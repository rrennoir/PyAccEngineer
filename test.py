from __future__ import annotations

import struct

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ClientFactory, DatagramProtocol, Protocol
from twisted.protocols.basic import LineReceiver

from modules.Common import PacketType


class ClientInstance(ClientFactory):

    def buildProtocol(self, addr) -> TCP_Client:

        return TCP_Client()


class TCP_Client(Protocol):

    def dataReceived(self, data: bytes):
        print(data)

    def connectionMade(self):

        buffer = []
        name_byte = "Ryan Rennoir".encode("utf-8")
        name_lenght = struct.pack("!B", len(name_byte))

        buffer.append(PacketType.Connect.to_bytes())
        buffer.append(name_lenght)
        buffer.append(name_byte)
        buffer.append(struct.pack("!B", 1))

        self.transport.write(b"".join(buffer))


# class UDPClient(DatagramProtocol):

#     def startProtocol(self, host_ip: str, host_port: int) -> None:

#         self.transport.connect(host_ip, host_port)
#         self.transport.write(PacketType.UDP_OK.to_bytes())

#     def datagramReceived(self, datagram: bytes, addr) -> None:
#         print(f"received {datagram} from {addr}")

#     # Possibly invoked if there is no server listening
#     def connectionRefused(self):
#         print("No one listening")

if __name__ == "__main__":

    endpoint = TCP4ClientEndpoint(reactor, "localhost", 4269)
    t = ClientInstance()
    endpoint.connect(t)
    reactor.run()
