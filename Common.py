from __future__ import annotations

import struct
from dataclasses import astuple, dataclass
from enum import Enum, auto
from typing import ClassVar, Tuple


class PacketType(Enum):

    Connect = auto()
    SmData = auto()
    ServerData = auto()
    Disconnect = auto()
    ConnectionReply = auto()
    Strategy = auto()
    StrategyOK = auto()
    Telemetry = auto()
    UpdateUsers = auto()

    def to_bytes(self) -> bytes:
        """
        Convert PacketType to bytes (unsigned char)
        """

        return struct.pack("!B", self.value)

    @classmethod
    def from_bytes(cls, data: bytes) -> PacketType:
        """
        Convert the first unsigned char of a bytes object into a PacketType
        """

        return PacketType(struct.unpack("!B", data[:1])[0])


class NetworkQueue(Enum):

    ServerData = auto()
    Strategy = auto()
    StrategyDone = auto()
    CarInfoData = auto()
    StrategySet = auto()
    Telemetry = auto()
    UpdateUsers = auto()


@dataclass
class CarInfo:

    front_left_pressure: float
    front_right_pressure: float
    rear_left_pressure: float
    rear_right_pressure: float
    fuel_to_add: float
    max_fuel: float
    tyre_set: int

    byte_format: ClassVar[str] = "!6f i"
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:

        return struct.pack(self.byte_format, *astuple(self))

    @classmethod
    def from_bytes(cls, data: bytes) -> CarInfo:

        return CarInfo(*struct.unpack(cls.byte_format, data[:cls.byte_size]))


@dataclass
class PitStop:

    fuel: float
    tyre_set: int
    tyre_compound: str
    tyre_pressures: Tuple[float]
    next_driver: int = 0
    brake_pad: int = 1
    repairs_bodywork: bool = True
    repairs_suspension: bool = True

    byte_format: ClassVar[str] = "!f i 3s 4f 2i 2?"
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:
        buffer = []
        buffer.append(struct.pack("!f", self.fuel))
        buffer.append(struct.pack("!i", self.tyre_set))
        buffer.append(struct.pack("!3s", self.tyre_compound.encode("utf-8")))
        buffer.append(struct.pack("!4f", *self.tyre_pressures))
        buffer.append(struct.pack("!i", self.next_driver))
        buffer.append(struct.pack("!i", self.brake_pad))
        buffer.append(struct.pack("!?", self.repairs_bodywork))
        buffer.append(struct.pack("!?", self.repairs_suspension))

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> PitStop:

        temp_data = struct.unpack(cls.byte_format, data[:cls.byte_size])

        pit_data = [
            temp_data[0],
            temp_data[1],
            temp_data[2].decode("utf-8"),
            tuple(temp_data[3:7]),
            temp_data[7],
            temp_data[8],
            temp_data[9],
            temp_data[10],
        ]

        return PitStop(*pit_data)
