import queue
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import List

from Common import PacketType


@dataclass
class ClientHandle:

    thread: threading.Thread
    rx_queue: queue.Queue
    tx_queue: queue.Queue
    addr: str
    username: str = ""


class ServerInstance:

    def __init__(self, port: int) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(0.05)
        self._server_thread = threading.Thread(target=self._server_listener)
        self._server_event = threading.Event()
        self.server_queue = queue.Queue()

        self.connection = None
        self._thread_pool: List[ClientHandle] = []
        self._users = []

        self._socket.bind(("", port))
        self._server_thread.start()

    def _server_listener(self) -> None:

        self._socket.listen()
        handler_event = threading.Event()
        dead_thread_timer = time.time()
        while not self._server_event.is_set():

            if len(self._thread_pool) < 4:
                try:
                    c_socket, addr = self._socket.accept()
                    print("SERVER: Accepting new connection")
                    self._new_connection(c_socket, addr, handler_event)

                except socket.timeout:
                    pass

                for client_thread in self._thread_pool:

                    if client_thread.rx_queue.qsize() > 0:

                        data = client_thread.rx_queue.get()
                        for thread in self._thread_pool:
                            thread.tx_queue.put(data)

            if time.time() - dead_thread_timer > 5:
                dead_thread_timer = time.time()
                for client_thread in reversed(self._thread_pool):
                    if not client_thread.thread.is_alive():
                        print("SERVER: Removing thread of client thread pool")
                        self._thread_pool.remove(client_thread)

                        for user in reversed(self._users):
                            if client_thread.username == user[0]:
                                self._users.remove(user)

                        self._update_user_connected()

        self._socket.close()
        handler_event.set()
        print("Closing threads")
        for client_thread in self._thread_pool:
            print(f"SERVER: Joining thread (server_listener) {client_thread}")
            client_thread.thread.join()
            self._thread_pool.remove(client_thread)

        print("server_listener STOPPED")

    def _new_connection(self, c_socket: socket.socket, addr,
                        event: threading.Event) -> None:

        try:
            data = c_socket.recv(1024)

        except socket.timeout:
            data = None

        except ConnectionResetError:
            data = b""

        packet_type = PacketType.from_bytes(data)
        if packet_type == PacketType.Connect:

            lenght = data[1]
            name = struct.unpack(f"!{lenght}s", data[2:])[0].decode("utf-8")

            packet_type = PacketType.ConnectionReply.to_bytes()
            if name not in [user[0] for user in self._users]:

                succes = struct.pack("!?", True)
                c_socket.send(packet_type + succes)

                rx_queue = queue.Queue()
                tx_queue = queue.Queue()
                thread = threading.Thread(target=self._client_handler,
                                          args=(c_socket, addr, event,
                                                rx_queue, tx_queue))

                new_client = ClientHandle(thread, rx_queue,
                                          tx_queue, addr, name)
                new_client.thread.start()

                self._users.append((name, addr))
                self._thread_pool.append(new_client)

                self._update_user_connected()

            else:
                succes = struct.pack("!?", False)
                c_socket.send(packet_type + succes)

    def _update_user_connected(self) -> None:

        if len(self._thread_pool) == 0:
            return

        buffer = []
        buffer.append(PacketType.UpdateUsers.to_bytes())
        buffer.append(struct.pack("!B", len(self._users)))

        for user in self._users:

            lenght = struct.pack("!B", len(user[0]))
            name = user[0].encode("utf-8")
            buffer.append(lenght + name)

        self._thread_pool[0].rx_queue.put(b"".join(buffer))

    def _client_handler(self, c_socket: socket.socket, addr,
                        event: threading.Event, rx_queue: queue.Queue,
                        tx_queue: queue.Queue) -> None:

        client_disconnect = False
        c_socket.settimeout(0.2)
        print(f"SERVER: Connected to {addr}")

        data = None
        while not (event.is_set() or data == b"" or client_disconnect):

            try:
                data = c_socket.recv(1024)

            except socket.timeout:
                data = None

            except ConnectionResetError:
                data = b""

            if data is not None and len(data) > 0:

                packet_type = PacketType.from_bytes(data)

                if packet_type == PacketType.Disconnect:
                    client_disconnect = True
                    print(f"SERVER: Client {addr} actively disconnected")

                elif packet_type == PacketType.SmData:
                    if rx_queue.qsize() == 0:
                        rx_queue.put(data)

                elif packet_type == PacketType.Strategy:
                    rx_queue.put(data)

                elif packet_type == PacketType.StrategyOK:
                    rx_queue.put(data)

                elif packet_type == PacketType.Telemetry:
                    rx_queue.put(data)

                else:
                    print(f"Socket data {addr}: {data}")

            if tx_queue.qsize() > 0:
                net_data = tx_queue.get()

                packet_type = PacketType.from_bytes(net_data)
                if packet_type == PacketType.SmData:
                    buffer = PacketType.ServerData.to_bytes() + net_data[1:]
                    c_socket.send(buffer)

                elif packet_type == PacketType.Strategy:
                    ServerInstance._send_data(c_socket, net_data)
                elif packet_type == PacketType.StrategyOK:
                    ServerInstance._send_data(c_socket, net_data)

                elif packet_type == PacketType.Telemetry:
                    ServerInstance._send_data(c_socket, net_data)

                elif packet_type == PacketType.UpdateUsers:
                    ServerInstance._send_data(c_socket, net_data)

        if data == b"":
            print(f"SERVER: Lost connection with client {addr}")

        c_socket.close()
        print("SERVER: client_handler STOPPED")

    @staticmethod
    def _send_data(c_socket: socket.socket, data: bytes) -> None:

        try:
            c_socket.send(data)

        except socket.timeout as msg:
            print(f"SERVER: {msg}")

        except ConnectionRefusedError as msg:
            print(f"SERVER: {msg}")

        except ConnectionResetError as msg:
            print(f"SERVER: {msg}")

    def disconnect(self) -> None:

        print("SERVER: Shutdown")

        self._server_event.set()
        self._server_thread.join()
