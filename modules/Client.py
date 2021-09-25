import queue
import socket
import struct
import threading
import time
from typing import Tuple

from modules.Common import Credidentials, NetworkQueue, PacketType


class ClientInstance:

    def __init__(self, credis: Credidentials, in_queue: queue.Queue,
                 out_queue: queue.Queue) -> None:

        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._server_ip = credis.ip
        self._tcp_port = credis.tcp_port
        self._udp_port = credis.udp_port
        self._username = credis.username
        self._driverID = credis.driverID
        self._listener_thread = None
        self._thread_event = None
        self._in_queue = in_queue
        self._out_queue = out_queue

    def connect(self) -> Tuple[bool, str]:

        try:
            self._tcp_socket.settimeout(3)
            self._tcp_socket.connect((self._server_ip, self._tcp_port))
            self._udp_socket.bind(("", 0))
            self._udp_socket.settimeout(0.01)

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

        buffer = []
        name_byte = self._username.encode("utf-8")
        name_lenght = struct.pack("!B", len(name_byte))

        buffer.append(PacketType.Connect.to_bytes())
        buffer.append(name_lenght)
        buffer.append(name_byte)
        buffer.append(struct.pack("!i", self._driverID))

        self._send_tcp(b"".join(buffer))

        reply = self._tcp_socket.recv(256)
        self._tcp_socket.settimeout(0.01)
        packet_type = PacketType.from_bytes(reply)
        if packet_type == PacketType.ConnectionReply:

            succes = struct.unpack("!?", reply[1:])[0]

            if succes:
                self._thread_event = threading.Event()

                self._listener_thread = threading.Thread(
                    target=self._network_listener,
                    name="Client listener")
                self._listener_thread.start()

                buffer = [
                    PacketType.ConnectUDP.to_bytes(),
                    name_lenght,
                    name_byte
                ]

                self._send_udp(b"".join(buffer))

                return (True, "Connected")

            else:
                self._tcp_socket.close()
                self._udp_socket.close()
                return (False, "Connection rejected")

        else:
            # TODO should I ?
            self._tcp_socket.shutdown(socket.SHUT_RDWR)
            self._udp_socket.shutdown(socket.SHUT_RDWR)
            return (False, "Connection refused")

    def disconnect(self) -> None:

        if (self._listener_thread is not None
                and self._listener_thread.is_alive()):

            self._thread_event.set()
            self._listener_thread.join()

            self._send_tcp(PacketType.Disconnect.to_bytes())
            self._tcp_socket.shutdown(socket.SHUT_WR)

            data = None
            while data != b"":

                try:
                    data = self._tcp_socket.recv(256)

                except socket.timeout as msg:
                    print(f"CLIENT: {msg}")

                except ConnectionResetError as msg:
                    print(f"CLIENT: {msg}")

                except ConnectionRefusedError as msg:
                    print(f"CLIENT: {msg}")

        print("close socket")
        self._tcp_socket.close()
        self._udp_socket.close()

    def _send_tcp(self, data: bytes) -> None:

        try:
            self._tcp_socket.send(data)

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")

        except BrokenPipeError as msg:
            print(f"CLIENT: {msg}")

    def _send_udp(self, data: bytes) -> bool:

        try:
            self._udp_socket.sendto(data, (self._server_ip, self._udp_port))

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")

        except BrokenPipeError as msg:
            print(f"CLIENT: {msg}")

    def _network_listener(self) -> None:

        data = None
        udp_timer = time.time()
        print("CLIENT: Listening for server packets")
        while not (self._thread_event.is_set() or data == b""):

            try:
                udp_data, _ = self._udp_socket.recvfrom(256)

            except socket.timeout:
                udp_data = None

            except ConnectionResetError:
                udp_data = b""

            try:
                data = self._tcp_socket.recv(256)

            except socket.timeout:
                data = None

            except ConnectionResetError:
                data = b""

            self._check_app_state()
            if data is not None and len(data) > 0:
                self._handle_data(data)

            if udp_data is not None and len(udp_data) > 0:

                packet_type = PacketType.from_bytes(udp_data)

                if packet_type == PacketType.Telemetry:

                    self._out_queue.put(NetworkQueue.Telemetry)
                    self._out_queue.put(udp_data[1:])

                elif packet_type == PacketType.TelemetryRT:

                    self._out_queue.put(NetworkQueue.TelemetryRT)
                    self._out_queue.put(udp_data[1:])

            if time.time() - udp_timer > 1:

                self._send_udp(PacketType.UDP_OK.to_bytes())
                udp_timer = time.time()

        if data == b"":
            print("CLIENT: Lost connection to server.")

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

        elif packet_type == PacketType.UDP_RENEW:

            print("CLIENT: Got UDP renew request")
            self._udp_socket.close()
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_socket.bind(("", 0))
            self._udp_socket.settimeout(0.01)
            self._send_udp(PacketType.ConnectUDP.to_bytes())
            print("CLIENT: UDP connection restablished")

    def _check_app_state(self) -> None:

        while self._in_queue.qsize() != 0:

            item_type = self._in_queue.get()

            if item_type == NetworkQueue.CarInfoData:

                info: bytes = self._in_queue.get()
                self._send_tcp(PacketType.SmData.to_bytes() + info)

            elif item_type == NetworkQueue.StrategySet:

                strategy: bytes = self._in_queue.get()
                self._send_tcp(PacketType.Strategy.to_bytes() + strategy)

            elif item_type == NetworkQueue.StrategyDone:

                self._send_tcp(PacketType.StrategyOK.to_bytes())

            elif item_type == NetworkQueue.Telemetry:

                telemetry = self._in_queue.get()
                self._send_udp(PacketType.Telemetry.to_bytes() + telemetry)

            elif item_type == NetworkQueue.TelemetryRT:

                telemetry = self._in_queue.get()
                self._send_udp(PacketType.TelemetryRT.to_bytes() + telemetry)
