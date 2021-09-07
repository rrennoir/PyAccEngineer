import queue
import socket
import struct
import threading
from typing import Tuple

from Common import NetworkQueue, PacketType


class ClientInstance:

    def __init__(self, ip: str, port: int, username: str,
                 in_queue: queue.Queue, out_queue: queue.Queue) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_ip = ip
        self._server_port = port
        self._username = username
        self._listener_thread = None
        self._thread_event = None
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._error = ""

    def connect(self) -> Tuple[bool, str]:

        try:
            self._socket.settimeout(3)
            self._socket.connect((self._server_ip, self._server_port))
            self._socket.settimeout(0.1)
            print(f"CLIENT: Connected to {self._server_ip}")

        except socket.timeout as msg:
            print(f"CLIENT: Timeout while connecting to {self._server_ip}")
            return (False, msg)

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        name_lenght = len(self._username)
        name_byte = struct.pack(f"!B {name_lenght}s", name_lenght,
                                self._username.encode("utf-8"))

        self._send_data(PacketType.Connect.to_bytes() + name_byte)

        reply = self._socket.recv(64)
        packet_type = PacketType.from_bytes(reply)
        if packet_type == PacketType.ConnectionReply:

            succes = struct.unpack("!?", reply[1:])[0]

            if succes:
                self._thread_event = threading.Event()

                self._listener_thread = threading.Thread(
                    target=self._network_listener)
                self._listener_thread.start()

                return (True, "Connected")

            else:
                return (False, "Connection rejected")

        else:
            # TODO should I ?
            self._socket.shutdown(socket.SHUT_RDWR)
            return (False, "Connection refused")

    def disconnect(self) -> None:

        if self._listener_thread.isAlive():

            self._send_data(PacketType.Disconnect.to_bytes())
            self._socket.shutdown(socket.SHUT_WR)

            data = None
            while data != b"":

                try:
                    data = self._socket.recv(1024)

                except socket.timeout:
                    print(f"CLIENT: {msg}")

                except ConnectionResetError as msg:
                    print(f"CLIENT: {msg}")

                except ConnectionRefusedError as msg:
                    print(f"CLIENT: {msg}")

        if self._thread_event is not None:
            self._thread_event.set()
            self._listener_thread.join()

    def _send_data(self, data: bytes) -> bool:

        try:
            self._socket.send(data)

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")
            self._error = msg
            return False

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")
            self._error = msg
            return False

    def _network_listener(self) -> None:

        data = None
        print("CLIENT: Listening for server packets")
        while not (self._thread_event.is_set() or data == b""):

            try:
                data = self._socket.recv(1024)

            except socket.timeout:
                data = None

            except ConnectionResetError:
                data = b""

            if data is not None and len(data) > 0:
                self._handle_data(data)

            self._check_app_state()

        if data == b"":
            print("CLIENT: Lost connection to server.")

        print("close socket")
        self._socket.close()
        self._thread_event.set()
        print("client_listener STOPPED")

    def _handle_data(self, data: bytes) -> None:

        packet_type = PacketType.from_bytes(data)

        if packet_type == PacketType.ServerData:

            self._out_queue.put(NetworkQueue.ServerData)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.Strategy:

            self._out_queue.put(NetworkQueue.Strategy)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.StrategyOK:

            self._out_queue.put(NetworkQueue.StrategyDone)

        elif packet_type == PacketType.Telemetry:

            self._out_queue.put(NetworkQueue.Telemetry)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.UpdateUsers:

            self._out_queue.put(NetworkQueue.UpdateUsers)
            self._out_queue.put(data[1:])

    def _check_app_state(self) -> None:

        while self._in_queue.qsize() != 0:

            item_type = self._in_queue.get()

            if item_type == NetworkQueue.CarInfoData:

                info: bytes = self._in_queue.get()
                self._socket.send(PacketType.SmData.to_bytes() + info)

            elif item_type == NetworkQueue.StrategySet:

                strategy: bytes = self._in_queue.get()
                buffer = PacketType.Strategy.to_bytes() + strategy
                self._socket.send(buffer)

            elif item_type == NetworkQueue.StrategyDone:
                self._socket.send(PacketType.StrategyOK.to_bytes())

            elif item_type == NetworkQueue.Telemetry:

                telemetry = self._in_queue.get()
                self._socket.send(PacketType.Telemetry.to_bytes() + telemetry)
