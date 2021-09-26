from __future__ import annotations
from modules.Common import PacketType

from typing import List
import struct

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import failure


class TCP_Server(Protocol):

    def connectionMade(self):

        print("new connection")
        self.transport.write("hello from server".encode("utf-8"))

    def dataReceived(self, data: bytes):

        print(f"Got data {data}")

        self.decode_data(data)

        self.transport.write(b"data ok")

    def decode_data(self, data: bytes) -> None:

        packet = PacketType.from_bytes(data)

        if packet == PacketType.Connect:

            lenght = data[1]
            name = data[2:lenght+2].decode("utf-8")
            driverID = struct.unpack("!B", data[lenght+2:lenght+3])[0]

            print(f"name: {name}, driverID: {driverID}")
            self.transport.write(PacketType.ConnectionReply.to_bytes() + struct.pack("!?", True))

        else:
            print(f"incorrect packet {packet}")

    def connectionLost(self, reason: failure.Failure = ...):
        print(reason)


class SeverInstace(ServerFactory):

    def __init__(self) -> None:
        self.users = []

    def buildProtocol(self, addr: IAddress):

        return TCP_Server()


if __name__ == "__main__":

    endpoint = TCP4ServerEndpoint(reactor, 4269)
    endpoint.listen(SeverInstace())
    reactor.run()
