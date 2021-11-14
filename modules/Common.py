from __future__ import annotations

import logging
import struct
import sys
import os
from dataclasses import astuple, dataclass
from enum import Enum, auto
from typing import ClassVar, List, Tuple, Union

log = logging.getLogger(__name__)

if os.name == "nt":
    import win32clipboard

    def send_to_clipboard(clip_type, data):

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(clip_type, data)

        except TypeError as msg:
            log.info(msg)

        finally:
            win32clipboard.CloseClipboard()


EPSILON = sys.float_info.epsilon  # Smallest possible difference.


def convert_to_rgb(minval, maxval, val, colours):

    # "colours" is a series of RGB colors delineating a series of
    # adjacent linear color gradients between each pair.
    # Determine where the given value falls proportionality within
    # the range from minval->maxval and scale that fractional value
    # by the total number in the "colors" pallette.
    i_f = float(val-minval) / float(maxval-minval) * (len(colours)-1)

    # Determine the lower index of the pair of color indices this
    # value corresponds and its fractional distance between the lower
    # and the upper colors.
    i, f = int(i_f // 1), i_f % 1  # Split into whole & fractional parts.

    # Does it fall exactly on one of the color points?
    if f < EPSILON:
        return colours[i]

    # Otherwise return a color within the range between them.
    else:
        (r1, g1, b1), (r2, g2, b2) = colours[i], colours[i+1]
        return int(r1 + f*(r2-r1)), int(g1 + f*(g2-g1)), int(b1 + f*(b2-b1))


def rgbtohex(r: int, g: int, b: int) -> str:
    "Convert RGB values to hex"

    return f'#{r:02x}{g:02x}{b:02x}'


def avg(value: Union[List, Tuple]) -> Union[float, int]:

    return sum(value) / len(value)


def string_time_from_ms(time_in_ms: int, hours: bool = False) -> str:
    """
    Convert timestamp in millisecond in a string with the format mm:ss.xxx
    If hours is true the format will be hh:mm:ss.xx
    """

    # if no time time_in_ms is equal to the maximum value of a 32bit int
    if time_in_ms == 2147483647 or time_in_ms == 65_535_000:
        # simply return 00:00.000
        time_in_ms = 0

    elif time_in_ms < 0:
        time_in_ms = 0

    if hours:
        hour = time_in_ms // 3_600_000
        minute = (time_in_ms % 3_600_000) // 60_000
        second = ((time_in_ms % 3_600_000) % 60_000) // 1_000
        millisecond = (((time_in_ms % 3_600_000) % 60_000) % 1_000)

    else:
        hour = 0
        minute = time_in_ms // 60_000
        second = (time_in_ms % 60_000) // 1_000
        millisecond = (time_in_ms % 60_000) % 1_000

    if hour < 10:
        hour_str = f"0{hour}"

    else:
        hour_str = str(hour)

    if minute < 10:
        minute_str = f"0{minute}"

    else:
        minute_str = str(minute)

    if second < 10:
        second_str = f"0{second}"

    else:
        second_str = str(second)

    if 10 < millisecond < 100:
        millisecond_str = f"0{millisecond}"

    elif millisecond < 10:
        millisecond_str = f"00{millisecond}"

    else:
        millisecond_str = str(millisecond)

    if hours:
        return f"{hour_str}:{minute_str}:{second_str}.{millisecond_str}"

    else:
        return f"{minute_str}:{second_str}.{millisecond_str}"


@dataclass
class Credidentials:

    ip: str
    tcp_port: int
    udp_port: int
    username: str
    driverID: int


class PacketType(Enum):

    Connect = 1
    SmData = 2
    ServerData = 3
    Disconnect = 4
    ConnectionReply = 5
    Strategy = 6
    StrategyOK = 7
    Telemetry = 8
    UpdateUsers = 9
    ConnectUDP = 10
    TelemetryRT = 11
    UDP_OK = 12
    UDP_RENEW = 13
    StategyHistory = 14
    Unkown = -1

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

        try:
            packet = PacketType(struct.unpack("!B", data[:1])[0])

        except ValueError as msg:

            log.info(f"PacketType: {msg}")
            packet = PacketType.Unkown

        return packet


class NetworkQueue(Enum):

    ServerData = auto()
    Strategy = auto()
    StrategyDone = auto()
    StategyHistory = auto()
    CarInfoData = auto()
    StrategySet = auto()
    Telemetry = auto()
    TelemetryRT = auto()
    UpdateUsers = auto()
    ConnectionReply = auto()
    Close = auto()


@dataclass
class DataQueue:

    q_in: List[NetData]
    q_out: List[NetData]


@dataclass
class NetData:

    data_type: NetworkQueue
    data: bytes = b""


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

    timestamp: str
    fuel: float
    tyre_set: int
    tyre_compound: str
    tyre_pressures: Tuple[float]
    driver_offset: int = 0
    brake_pad: int = 1
    repairs_bodywork: bool = True
    repairs_suspension: bool = True

    byte_format: ClassVar[str] = "! 8s f i 3s 4f 2i 2?"
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:
        buffer = []
        buffer.append(struct.pack("!8s", self.timestamp.encode("utf-8")))
        buffer.append(struct.pack("!f", self.fuel))
        buffer.append(struct.pack("!i", self.tyre_set))
        buffer.append(struct.pack("!3s", self.tyre_compound.encode("utf-8")))
        buffer.append(struct.pack("!4f", *self.tyre_pressures))
        buffer.append(struct.pack("!i", self.driver_offset))
        buffer.append(struct.pack("!i", self.brake_pad))
        buffer.append(struct.pack("!?", self.repairs_bodywork))
        buffer.append(struct.pack("!?", self.repairs_suspension))

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> PitStop:

        temp_data = struct.unpack(cls.byte_format, data[:cls.byte_size])

        pit_data = [
            temp_data[0].decode("utf-8"),
            temp_data[1],
            temp_data[2],
            temp_data[3].decode("utf-8"),
            tuple(temp_data[4:8]),
            temp_data[8],
            temp_data[9],
            temp_data[10],
            temp_data[11],
        ]

        return PitStop(*pit_data)
