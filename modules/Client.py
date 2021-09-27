from __future__ import annotations

import struct

from twisted.internet import reactor, task
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ClientFactory, DatagramProtocol, Protocol
from twisted.python.failure import Failure

from modules.Common import (Credidentials, DataQueue, NetData, NetworkQueue,
                            PacketType)


class ClientInstance:

    def __init__(self, credis: Credidentials, queue: DataQueue) -> None:

        self.data_queue = queue

        self.udp_queue = DataQueue([], [])
        self.tcp_queue = DataQueue([], [])

        self.looping_call = task.LoopingCall(self.check_queue)
        self.looping_call.start(0.01)

        endpoint = TCP4ClientEndpoint(reactor, credis.ip, credis.tcp_port)
        endpoint.connect(TCP_Factory(credis, self.tcp_queue))

        reactor.listenUDP(0, UDPClient(credis.ip, credis.udp_port,
                                       self.udp_queue))

    def check_queue(self) -> None:

        for element in self.data_queue.q_in:

            if (element.data_type in (NetworkQueue.Telemetry,
                                      NetworkQueue.TelemetryRT)):

                self.udp_queue.q_in.append(element)

            else:
                self.tcp_queue.q_in.append(element)

        self.data_queue.q_in.clear()

        for element in self.udp_queue.q_out:
            self.data_queue.q_out.append(element)

        self.udp_queue.q_out.clear()

        for element in self.tcp_queue.q_out:
            self.data_queue.q_out.append(element)

        self.tcp_queue.q_out.clear()

    def close(self) -> None:

        self.looping_call.stop()
        self.data_queue.q_in.append(NetData(NetworkQueue.Close))


class TCP_Factory(ClientFactory):

    def __init__(self, credis: Credidentials, queue: DataQueue) -> None:

        self._name = credis.username
        self._driverID = credis.driverID
        self.data_queue = queue

    def buildProtocol(self, addr) -> TCP_Client:

        return TCP_Client(self._name, self._driverID, self.data_queue)


class TCP_Client(Protocol):

    def __init__(self, name: str, driverID: int, queue: DataQueue) -> None:

        self._name = name
        self._driverID = driverID
        self._data_queue = queue
        self._error = ""
        self.loop_call = task.LoopingCall(self.check_queue)
        self.loop_call.start(0.1)

    def check_queue(self) -> None:

        for element in self._data_queue.q_in:

            packet = element.data_type
            if packet == NetworkQueue.CarInfoData:
                self.transport.write(PacketType.SmData.to_bytes()
                                     + element.data)

            elif packet == NetworkQueue.StrategySet:
                self.transport.write(PacketType.Strategy.to_bytes()
                                     + element.data)

            elif packet == NetworkQueue.StrategyDone:
                print("client send strat ok")
                self.transport.write(PacketType.StrategyOK.to_bytes())

            elif packet == NetworkQueue.Close:
                self.close()

        self._data_queue.q_in.clear()

    def dataReceived(self, data: bytes):
        self._decode_packet(data)

    def connectionMade(self):

        buffer = []
        name_byte = self._name.encode("utf-8")
        name_lenght = struct.pack("!B", len(name_byte))

        buffer.append(PacketType.Connect.to_bytes())
        buffer.append(name_lenght)
        buffer.append(name_byte)
        buffer.append(struct.pack("!B", self._driverID))

        self.transport.write(b"".join(buffer))

    def connectionLost(self, reason: Failure):
        self._error = str(reason)
        print(self._error)

    def close(self):

        if self.transport is not None:
            print("CLIENT: Close transport")
            self.transport.loseConnection()
            self.loop_call.stop()
            self._data_queue.q_in.clear()

    def _decode_packet(self, data: bytes) -> None:

        packet = PacketType.from_bytes(data)
        data = data[1:]

        net_data = None
        if packet == PacketType.ConnectionReply:
            net_data = NetData(NetworkQueue.ConnectionReply, data)

        elif packet == PacketType.ServerData:
            net_data = NetData(NetworkQueue.ServerData, data)

        elif packet == PacketType.Strategy:
            net_data = NetData(NetworkQueue.Strategy, data)

        elif packet == PacketType.StrategyOK:
            print("receive strat ok client")
            net_data = NetData(NetworkQueue.StrategyDone, data)

        elif packet == PacketType.UpdateUsers:
            net_data = NetData(NetworkQueue.UpdateUsers, data)

        elif packet == PacketType.UDP_RENEW:
            print("UDP RENEW")

        else:
            print(f"Invalid packet type {data}")
            return

        self._data_queue.q_out.append(net_data)


class UDPClient(DatagramProtocol):

    def __init__(self, ip: str, port: int, queue: DataQueue) -> None:
        super().__init__()

        self.ip = ip
        self.port = port
        self.queue = queue
        self.loop_call = task.LoopingCall(self.check_queue)
        self.loop_call.start(0.01)

    def startProtocol(self) -> None:

        self.transport.connect(self.ip, self.port)
        self.transport.write(b"Hello UDP")

    def check_queue(self) -> None:

        for element in self.queue.q_in:

            if element.data_type == NetworkQueue.Telemetry:
                self.transport.write(PacketType.Telemetry.to_bytes()
                                     + element.data)

            elif element.data_type == NetworkQueue.TelemetryRT:
                self.transport.write(PacketType.TelemetryRT.to_bytes()
                                     + element.data)

        self.queue.q_in.clear()

    def datagramReceived(self, datagram: bytes, addr) -> None:
        self._decode_packet(datagram)

    def _decode_packet(self, data: bytes) -> None:

        packet = PacketType.from_bytes(data)

        if packet == PacketType.Telemetry:
            self.queue.q_out.append(NetData(NetworkQueue.Telemetry,
                                    data[1:]))

        elif packet == PacketType.TelemetryRT:
            self.queue.q_out.append(NetData(NetworkQueue.TelemetryRT,
                                    data[1:]))

    # Possibly invoked if there is no server listening
    def connectionRefused(self):
        print("No one listening")
