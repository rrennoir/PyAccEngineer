from __future__ import annotations

import logging
import struct
import time
from typing import List, Tuple

from twisted.internet import reactor, task
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import DatagramProtocol, Protocol, ServerFactory
from twisted.python.failure import Failure

from modules.Common import (DataQueue, NetData, NetworkQueue,
                            PacketType, PitStop)

server_log = logging.getLogger(__name__)


class TCP_Server(Protocol):

    def __init__(self, users: List[TCP_Server],
                 strategies: List[PitStop],
                 user_connected: List[Tuple[str, int]],
                 queue: DataQueue) -> None:

        super().__init__()
        self.queue = queue
        self.users = users
        self.users.append(self)
        self.user_connected: List[str, int] = user_connected

        self.user_change = False
        self._error = ""
        self.valid_user = False
        self.sent_strat_history = False
        self.timer = time.time()

        self.user: Tuple[str, int] = ()

        self.strategies: List[PitStop] = strategies

        self.loop_call = task.LoopingCall(self.server_loop)
        self.loop_call.start(0.1)

    def server_loop(self) -> None:

        if self.user_change:
            self.update_user_connected()
            self.user_change = False

        # why the fuck I'm not allowed to send 2 TCP packet 1ms apart?
        if (self.valid_user and not self.sent_strat_history
                and time.time() > self.timer + 0.5):

            self.sent_strat_history = True
            header = PacketType.StategyHistory.to_bytes()

            packet = struct.pack("!B", len(self.strategies))
            for strategy in self.strategies:
                packet += strategy.to_bytes()

            self.send_message(header + packet)

        for element in self.queue.q_in:

            if element.data_type == NetworkQueue.Close:
                self.close()
                self.queue.q_in.remove(element)
                break

    def connectionMade(self) -> None:
        server_log.info(f"New connection with {self.transport.getPeer()}")

    def dataReceived(self, data: bytes) -> None:

        byte_offset = 0
        while (len(data) != byte_offset):

            try:
                packet_size = struct.unpack("!H",
                                        data[byte_offset:byte_offset+2])[0]
                byte_offset += 2
                self.decode_data(data[byte_offset:byte_offset+packet_size])
                byte_offset += packet_size

            except struct.error as msg:
                server_log.warning(msg)

    def send_to_all_user(self, data: bytes) -> None:

        data_header = struct.pack("!H", len(data))
        message = data_header + data

        for user in self.users:
            user.transport.write(message)

    def send_message(self, data: bytes) -> None:

        data_header = struct.pack("!H", len(data))
        message = data_header + data
        self.transport.write(message)

    def decode_data(self, data: bytes) -> None:

        packet = PacketType.from_bytes(data)

        if packet == PacketType.Connect:

            lenght = data[1]
            name = data[2:lenght+2].decode("utf-8")
            driverID = data[lenght+2]

            server_log.info(f"New user info, name: {name},"
                            f" driverID: {driverID}")

            self.user = (name, driverID)
            succes = False
            if name in [user[0] for user in self.user_connected]:
                server_log.warning(f"User {name} is already used.")
                msg = "This username is already connected."

            elif driverID in [user[1] for user in self.user_connected]:
                server_log.warning(f"DriverID {driverID} is already used.")
                msg = f"The driver ID {driverID} is already used."

            else:
                server_log.info(f"Connection succes")
                self.user_connected.append(self.user)
                self.user_change = True
                self.valid_user = True
                succes = True
                msg = "Connection succes"

            header = PacketType.ConnectionReply.to_bytes()
            info = msg.encode("utf-8")
            packet = struct.pack("!?B", succes, len(info)) + info

            self.send_message(header + packet)

        elif packet == PacketType.SmData:

            header = PacketType.ServerData.to_bytes()
            self.send_to_all_user(header + data[1:])

        elif packet == PacketType.Strategy:

            self.strategies.append(PitStop.from_bytes(data[1:]))
            self.send_to_all_user(data)

        elif packet == PacketType.StrategyOK:
            self.send_to_all_user(data)

        elif packet == PacketType.TyreSets:
            server_log.info("Received Tyre sets data")
            self.send_to_all_user(data)

        else:
            server_log.warning(f"incorrect packet {packet}")

    def update_user_connected(self) -> None:

        buffer = []
        buffer.append(PacketType.UpdateUsers.to_bytes())
        buffer.append(struct.pack("!B", len(self.user_connected)))

        for user in self.user_connected:

            name = user[0].encode("utf-8")
            lenght = struct.pack("!B", len(name))
            driverID = struct.pack("!B", user[1])
            buffer.append(lenght + name + driverID)

        self.send_to_all_user(b"".join(buffer))
        server_log.info(f"Send user update {buffer}")

    def connectionLost(self, reason: Failure):

        self._error = str(reason)

        server_log.info(f"Lost connection with {self.transport.getPeer()}")

        if self.valid_user:
            self.user_connected.remove(self.user)
            self.user_change = True

    def close(self) -> None:

        if self.transport is not None:
            server_log.info("Close TCP SERVER")
            self.transport.loseConnection()
            self.loop_call.stop()


class TCP_Factory(ServerFactory):

    def __init__(self, queue: DataQueue) -> None:
        super().__init__()
        self._users: List[TCP_Server] = []
        self._strategies: List[PitStop] = []
        self.user_connected: List[Tuple[str, int]] = []
        self.queue = queue

    def buildProtocol(self, addr: IAddress):

        return TCP_Server(self._users, self._strategies,
                          self.user_connected, self.queue)


class UDP_Server(DatagramProtocol):

    def __init__(self, clients: List, queue: DataQueue) -> None:
        super().__init__()
        self.clients = clients
        self.queue = queue

        self.udp_imnotdead_timer = time.time()
        self.loop_call = task.LoopingCall(self.udp_server_loop)
        self.loop_call.start(0.01)

    def datagramReceived(self, datagram: bytes, addr):

        if addr not in self.clients:
            self.clients.append(addr)

        if datagram in (b"Hello UDP", b"I'm not a dead client"):
            return

        for client in self.clients:
            self.transport.write(datagram, client)

    def udp_server_loop(self) -> None:

        for element in self.queue.q_in:

            if element.data_type == NetworkQueue.Close:
                self.close()
                self.queue.q_in.remove(element)
                break

        if time.time() - self.udp_imnotdead_timer > 10:
            for client in self.clients:
                self.transport.write(b"I'm not a dead server", client)
            self.udp_imnotdead_timer = time.time()

    def close(self) -> None:
        server_log.info("Close UDP SERVER")
        self.transport.loseConnection()
        self.loop_call.stop()


class ServerInstance:

    def __init__(self, tcp_port: int, udp_port: int) -> None:

        self.udp_clients = []
        self.data_queue = DataQueue([], [])

        self.tcp_endpoint = TCP4ServerEndpoint(reactor, tcp_port)
        self.tcp_endpoint.listen(TCP_Factory(self.data_queue))
        reactor.listenUDP(udp_port, UDP_Server(self.udp_clients,
                                               self.data_queue))

    def close(self) -> None:
        self.data_queue.q_in.append(NetData(NetworkQueue.Close))
        self.data_queue.q_in.append(NetData(NetworkQueue.Close))
