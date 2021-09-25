import queue
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import List, Tuple

from modules.Common import PacketType


@dataclass
class ClientHandle:

    thread: threading.Thread
    rx_queue: queue.Queue
    tx_queue: queue.Queue
    addr: tuple
    username: str
    udp_addr: tuple = ()


class ServerInstance:

    def __init__(self, tcp_port: int, udp_port: int) -> None:

        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.settimeout(0.01)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.settimeout(0.01)
        self._server_thread = threading.Thread(target=self._server_listener,
                                               name="Server listener")
        self._udp_thread = threading.Thread(target=self._udp_listener,
                                            name="UDP listener")
        self._server_event = threading.Event()
        self.udp_queue = queue.Queue()

        self.connection = None
        self._thread_pool: List[ClientHandle] = []
        self._users = []
        self.error = None
        self._udp_connections: List[List[Tuple[str, int], float]] = []

        try:
            self._tcp_socket.bind(("", tcp_port))
            self._udp_socket.bind(("", udp_port))

        except OSError as msg:
            self.error = msg
            print(f"SERVER: {msg}")
            return

        self._server_thread.start()
        self._udp_thread.start()

    def _udp_listener(self) -> None:

        print("SERVER: UDP listener started")
        while not self._server_event.is_set():
            udp_data, udp_addr = self._get_udp_data()

            if udp_data is None or len(udp_data) == 0:
                continue

            packet = PacketType.from_bytes(udp_data)
            if packet == PacketType.ConnectUDP:
                print("SERVER: Received Connection UDP packet")

                for connection in reversed(self._udp_connections):

                    if connection[0][0] == udp_addr[0]:
                        self._udp_connections.remove(connection)

                self._udp_connections.append([udp_addr, time.time()])
                print(f"SERVER: UDP connections: {self._udp_connections}")

            elif packet in (PacketType.Telemetry, PacketType.TelemetryRT):
                self._udp_send_all(udp_data)

            elif packet == PacketType.UDP_OK:

                for connection in self._udp_connections:

                    if connection[0] == udp_addr:
                        connection[1] = time.time()

            else:
                print(f"SERVER: Received incorrect packet {udp_data}")

            now = time.time()
            for connection in reversed(self._udp_connections):

                if now - connection[1] > 1.5:

                    print(f"connection with {connection[0]} timed out")
                    self.udp_queue.put(connection[0][0])
                    self._udp_connections.remove(connection)

        self._udp_socket.close()
        print("SERVER: UDP listener close")

    def _udp_send_all(self, data: bytes) -> None:

        for connection in self._udp_connections:
            self._send_udp(data, connection[0])

    def _server_listener(self) -> None:

        self._tcp_socket.listen()
        handler_event = threading.Event()
        dead_thread_timer = time.time()
        while not self._server_event.is_set():

            if len(self._thread_pool) < 5:
                try:
                    c_socket, addr = self._tcp_socket.accept()
                    print("SERVER: Accepting new connection")
                    self._new_connection(c_socket, addr, handler_event)

                except socket.timeout:
                    pass

                for client_thread in self._thread_pool:

                    if client_thread.rx_queue.qsize() > 0:

                        if client_thread.rx_queue.qsize() > 20:
                            print("Server running late !")

                        data = client_thread.rx_queue.get()
                        for thread in self._thread_pool:
                            thread.tx_queue.put(data)

            if self.udp_queue.qsize() > 0:

                ip = self.udp_queue.get()
                for client in self._thread_pool:
                    if client.addr[0] == ip:
                        client.tx_queue.put(PacketType.UDP_RENEW.to_bytes())

            if time.time() - dead_thread_timer > 2:
                dead_thread_timer = time.time()
                for client_thread in reversed(self._thread_pool):
                    if not client_thread.thread.is_alive():
                        print("SERVER: Removing thread of client thread pool")
                        self._thread_pool.remove(client_thread)

                        for user in reversed(self._users):
                            if client_thread.username == user[0]:
                                self._users.remove(user)

                        self._update_user_connected()

        self._tcp_socket.close()
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
            data = c_socket.recv(256)

        except socket.timeout:
            data = None

        except ConnectionResetError:
            data = b""

        packet_type = PacketType.from_bytes(data)
        if packet_type == PacketType.Connect:

            lenght = data[1]
            name = data[2:lenght+2].decode("utf-8")
            driverID = struct.unpack("!i", data[lenght+2:lenght+6])[0]

            packet_type = PacketType.ConnectionReply.to_bytes()
            if name not in [user[0] for user in self._users]:

                succes = struct.pack("!?", True)
                c_socket.send(packet_type + succes)

                rx_queue = queue.Queue()
                tx_queue = queue.Queue()
                thread = threading.Thread(target=self._client_handler,
                                          args=(c_socket, addr, event,
                                                rx_queue, tx_queue),
                                          name=f"{name} client handler")

                new_client = ClientHandle(thread, rx_queue,
                                          tx_queue, addr, name)
                new_client.thread.start()

                self._users.append((name, addr, driverID))
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

            name = user[0].encode("utf-8")
            lenght = struct.pack("!B", len(name))
            driverID = struct.pack("!i", user[2])
            buffer.append(lenght + name + driverID)

        self._thread_pool[0].rx_queue.put(b"".join(buffer))

    def _get_udp_data(self) -> Tuple[bytes, Tuple[str, int]]:

        try:
            data, addr = self._udp_socket.recvfrom(1024)

        except socket.timeout:
            data = None
            addr = ()

        except ConnectionResetError:
            data = b""
            addr = ()

        return data, addr

    def _client_handler(self, c_socket: socket.socket, addr,
                        event: threading.Event, rx_queue: queue.Queue,
                        tx_queue: queue.Queue) -> None:

        client_disconnect = False
        c_socket.settimeout(0.01)
        print(f"SERVER: Connected to {addr}")

        data = None
        while not (event.is_set() or data == b"" or client_disconnect):

            try:
                data = c_socket.recv(256)

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

                else:
                    print(f"Socket data {addr}: {data}")

            if tx_queue.qsize() > 0:
                net_data = tx_queue.get()

                if tx_queue.qsize() > 10:
                    print("tx_queue is late")

                packet_type = PacketType.from_bytes(net_data)
                if packet_type == PacketType.SmData:
                    buffer = PacketType.ServerData.to_bytes() + net_data[1:]
                    c_socket.send(buffer)

                elif packet_type == PacketType.Strategy:
                    ServerInstance._send_data(c_socket, net_data)

                elif packet_type == PacketType.StrategyOK:
                    ServerInstance._send_data(c_socket, net_data)

                elif packet_type == PacketType.UpdateUsers:
                    ServerInstance._send_data(c_socket, net_data)

                elif packet_type == PacketType.UDP_RENEW:
                    ServerInstance._send_data(c_socket, net_data)

        if data == b"":
            print(f"SERVER: Lost connection with client {addr}")

        c_socket.close()
        print("SERVER: client_handler STOPPED")

    def _send_udp(self, data: bytes, addr: tuple) -> None:

        try:
            self._udp_socket.sendto(data, addr)

        except ConnectionResetError as msg:
            print(f"SERVER: {msg}")

        except ConnectionRefusedError as msg:
            print(f"SERVER: {msg}")

        except ConnectionResetError as msg:
            print(f"SERVER: {msg}")

        except BrokenPipeError as msg:
            print(f"SERVER: {msg}")

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

        except BrokenPipeError as msg:
            print(f"SERVER: {msg}")

    def disconnect(self) -> None:

        print("SERVER: Shutdown")

        self._server_event.set()
        self._server_thread.join()
