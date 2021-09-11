from __future__ import annotations

import struct
import tkinter
from dataclasses import astuple, dataclass
from typing import List, Optional

from SharedMemory.PyAccSharedMemory import Wheels


def rgbtohex(r: int, g: int, b: int) -> str:
    "Convert RGB values to hex"

    return f'#{r:02x}{g:02x}{b:02x}'


def string_time_from_ms(time_in_ms: int) -> str:

    # if no time time_in_ms is equal to the maximum value of a 32bit int
    if time_in_ms == 2147483647:
        # simply return 00:00.000
        time_in_ms = 0

    minute = time_in_ms // 60_000
    second = (time_in_ms % 60_000) // 1000
    millisecond = (time_in_ms % 60_000) % 1000

    if minute < 10:
        minute_str = f"0{minute}"

    else:
        minute_str = str(minute)

    if second < 10:
        second_str = f"0{second}"

    else:
        second_str = str(second)

    if millisecond < 100:
        millisecond_str = f"0{millisecond}"

    elif millisecond < 10:
        millisecond_str = f"00{millisecond}"

    else:
        millisecond_str = str(millisecond)

    return f"{minute_str}:{second_str}.{millisecond_str}"


class TyreInfo(tkinter.Frame):

    def __init__(self, root, name: str, on_the_right: bool = True):

        tkinter.Frame.__init__(self, master=root, background="Black")

        self.pressure_table = {
            "Dry": {
                "high": {
                    "low": 28.1,
                    "low_mid": 28.3,
                    "high_mid": 28.7,
                    "high": 29.9
                },
                "mid": {
                    "low": 27.1,
                    "low_mid": 27.3,
                    "high_mid": 27.7,
                    "high": 27.9
                },
                "low": {
                    "low": 26.1,
                    "low_mid": 26.3,
                    "high_mid": 26.7,
                    "high": 26.9
                }
            },
            "Wet": {
                "high": {
                    "low": 30.8,
                    "low_mid": 31.0,
                    "high_mid": 31.5,
                    "high": 31.7
                },
                "mid": {
                    "low": 29.7,
                    "low_mid": 29.5,
                    "high_mid": 30.5,
                    "high": 30.7
                },
                "low": {
                    "low": 28.5,
                    "low_mid": 28.7,
                    "high_mid": 29.0,
                    "high": 29.2
                }
            }
        }

        self.tyre_pressure = tkinter.DoubleVar()
        self.tyre_temp = tkinter.DoubleVar()
        self.brake_temp = tkinter.DoubleVar()
        self.pad_wear = tkinter.DoubleVar()
        self.disc_wear = tkinter.DoubleVar()

        self.tyre_band: List[tkinter.Label] = []

        label_width = 15
        var_width = 5
        if on_the_right:
            label_column = 2
            var_column = 1
            tyre_column = 0
            txt_anchor = tkinter.W

        else:
            label_column = 0
            var_column = 1
            tyre_column = 2
            txt_anchor = tkinter.E

        row_count = 0
        self.tyre = tkinter.Frame(self, background="Black")
        self.tyre.grid(row=row_count, rowspan=6, column=tyre_column)
        for band_row in range(6):
            temp = tkinter.Label(self.tyre, width=10, background="Green")
            temp.grid(row=band_row, column=0)
            self.tyre_band.append(temp)

        l_tyre = tkinter.Label(self, text=name, width=label_width,
                               anchor=txt_anchor, bg="Black", fg="White")
        l_tyre.grid(row=row_count, column=label_column)
        row_count += 1

        l_tyre_pressure = tkinter.Label(self, text="Tyre pressure",
                                        width=label_width, anchor=txt_anchor,
                                        bg="Black", fg="White")

        l_tyre_pressure_var = tkinter.Label(self,
                                            textvariable=self.tyre_pressure,
                                            width=var_width,
                                            bg="Black", fg="White")

        l_tyre_pressure.grid(row=row_count, column=label_column)
        l_tyre_pressure_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_tyre_temp = tkinter.Label(self, text="Tyre temperature",
                                    width=label_width, anchor=txt_anchor,
                                    bg="Black", fg="White")
        l_tyre_temp_var = tkinter.Label(self,
                                        textvariable=self.tyre_temp,
                                        width=var_width,
                                        bg="Black", fg="White")
        l_tyre_temp.grid(row=row_count, column=label_column)
        l_tyre_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_brake_temp = tkinter.Label(self, text="Brake temperature",
                                     width=label_width, anchor=txt_anchor,
                                     bg="Black", fg="White")
        l_brake_temp_var = tkinter.Label(self,
                                         textvariable=self.brake_temp,
                                         width=var_width,
                                         bg="Black", fg="White")
        l_brake_temp.grid(row=row_count, column=label_column)
        l_brake_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_pad_wear = tkinter.Label(self, text="Pad wear",
                                   width=label_width, anchor=txt_anchor,
                                   bg="Black", fg="White")
        l_pad_wear_var = tkinter.Label(self,
                                       textvariable=self.pad_wear,
                                       width=var_width, bg="Black", fg="White")
        l_pad_wear.grid(row=row_count, column=label_column)
        l_pad_wear_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_disc_wear = tkinter.Label(self, text="Disc wear",
                                    width=label_width, anchor=txt_anchor,
                                    bg="Black", fg="White")
        l_disc_wear_var = tkinter.Label(self,
                                        textvariable=self.disc_wear,
                                        width=var_width, bg="Black",
                                        fg="White")
        l_disc_wear.grid(row=row_count, column=label_column)
        l_disc_wear_var.grid(row=row_count, column=var_column)

    def update_value(self, pressure: float, tyre_temp: float,
                     brake_temp: float, pad_wear: float,
                     disc_wear: float) -> None:

        self.tyre_pressure.set(f"{pressure:.1f}")
        self.tyre_temp.set(f"{tyre_temp:.1f}")
        self.brake_temp.set(f"{brake_temp:.1f}")
        self.pad_wear.set(f"{pad_wear:.1f}")
        self.disc_wear.set(f"{disc_wear:.1f}")

        self.update_tyre_hud(pressure)

    def update_tyre_hud(self, pressure: float) -> None:

        pressure_table = self.pressure_table["Dry"]
        mid_table = pressure_table["mid"]
        high_table = pressure_table["high"]
        low_table = pressure_table["low"]

        color = "Grey"
        for band in self.tyre_band:

            if mid_table["low"] < pressure < mid_table["high"]:

                if mid_table["high_mid"] < pressure:
                    color = rgbtohex(128, 255, 0)

                elif mid_table["low_mid"] < pressure < mid_table["high_mid"]:
                    color = rgbtohex(0, 255, 0)

                else:
                    color = rgbtohex(0, 255, 128)

            elif mid_table["high"] < pressure:

                if high_table["high_mid"] < pressure:
                    color = rgbtohex(255, 0, 0)

                elif high_table["low_mid"] < pressure < high_table["high_mid"]:
                    color = rgbtohex(255, 128, 0)

                elif pressure < high_table["low_mid"]:
                    color = rgbtohex(255, 255, 0)

            elif pressure < mid_table["low"]:

                if low_table["high_mid"] < pressure:
                    color = rgbtohex(0, 255, 255)

                elif low_table["low_mid"] < pressure < low_table["high_mid"]:
                    color = rgbtohex(0, 128, 255)

                elif pressure < low_table["low_mid"]:
                    color = rgbtohex(0, 0, 255)

            band.config(bg=color)

    def reset_value(self) -> None:

        self.tyre_pressure.set(0)
        self.tyre_temp.set(0)
        self.brake_temp.set(0)
        self.pad_wear.set(0)
        self.disc_wear.set(0)


@dataclass
class Telemetry:

    driver: str
    lap: int
    fuel: float
    tyre_pressure: Wheels
    tyre_temp: Wheels
    brake_temp: Wheels
    pad_wear: Wheels
    disc_wear: Wheels
    lap_time: int
    best_time: int
    previous_time: int

    def to_bytes(self) -> bytes:

        driver_lenght = len(self.driver)

        buffer = [
            struct.pack("!B", driver_lenght),
            struct.pack(f"!{driver_lenght}s", self.driver.encode("utf-8")),
            struct.pack("!i", self.lap),
            struct.pack("!f", self.fuel),
            struct.pack("!4f", *astuple(self.tyre_pressure)),
            struct.pack("!4f", *astuple(self.tyre_temp)),
            struct.pack("!4f", *astuple(self.brake_temp)),
            struct.pack("!4f", *astuple(self.pad_wear)),
            struct.pack("!4f", *astuple(self.disc_wear)),
            struct.pack("!i", self.lap_time),
            struct.pack("!i", self.best_time),
            struct.pack("!i", self.previous_time),
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> Telemetry:

        lenght = data[0]

        if len(data[1:]) > 112:
            psize = len(data[1:])
            print(f"Telemetry: Warning got packet of {psize} bytes")
            data = data[:113]

        raw_data = struct.unpack(f"!{lenght}s i 21f 3i", data[1:])

        name = raw_data[0].decode("utf-8")
        rest = raw_data[1:]

        return Telemetry(
            name,
            rest[0],
            rest[1],
            Wheels(*rest[2:6]),
            Wheels(*rest[6:10]),
            Wheels(*rest[10:14]),
            Wheels(*rest[14:18]),
            Wheels(*rest[18:22]),
            rest[22],
            rest[23],
            rest[24],
        )


class TelemetryUI(tkinter.Frame):

    def __init__(self, root):

        tkinter.Frame.__init__(self, master=root, background="Black")

        self.telemetry: Optional[Telemetry] = None

        f_info = tkinter.Frame(self, bg="Black")
        f_info.grid(row=0, column=0)

        self.current_driver = None
        self.driver_swap = False

        # Fuel
        self.fuel_var = tkinter.DoubleVar()
        l_fuel = tkinter.Label(f_info, text="Fuel: ", bg="Black", fg="White")
        l_fuel_var = tkinter.Label(f_info, textvariable=self.fuel_var,
                                   bg="Black", fg="White")
        l_fuel.pack(side=tkinter.LEFT)
        l_fuel_var.pack(side=tkinter.LEFT)

        # Lap time
        self.lap_time_var = tkinter.StringVar(value="00:00.000")
        l_lap_time = tkinter.Label(f_info, text="Lap time: ",
                                   bg="Black", fg="White")
        l_lap_time_var = tkinter.Label(f_info, textvariable=self.lap_time_var,
                                       bg="Black", fg="White")
        l_lap_time.pack(side=tkinter.LEFT)
        l_lap_time_var.pack(side=tkinter.LEFT)

        # best time
        self.best_time_var = tkinter.StringVar(value="00:00.000")
        l_best_time = tkinter.Label(f_info, text="Best time: ",
                                    bg="Black", fg="White")
        l_best_time_var = tkinter.Label(f_info,
                                        textvariable=self.best_time_var,
                                        bg="Black", fg="White")
        l_best_time.pack(side=tkinter.LEFT)
        l_best_time_var.pack(side=tkinter.LEFT)

        # Previous time
        self.prev_time_var = tkinter.StringVar(value="00:00.000")
        l_prev_time = tkinter.Label(f_info, text="Previous time: ",
                                    bg="Black", fg="White")
        l_prev_time_var = tkinter.Label(f_info,
                                        textvariable=self.prev_time_var,
                                        bg="Black", fg="White")
        l_prev_time.pack(side=tkinter.LEFT)
        l_prev_time_var.pack(side=tkinter.LEFT)

        tyre_frame = tkinter.Frame(self, bg="Black")
        tyre_frame.grid(row=1, column=0)

        self.front_left = TyreInfo(tyre_frame, "FL", False)
        self.front_left.grid(row=0, column=0, padx=10, pady=10)

        self.front_right = TyreInfo(tyre_frame, "FR")
        self.front_right.grid(row=0, column=1, padx=10, pady=10)

        self.rear_left = TyreInfo(tyre_frame, "RL", False)
        self.rear_left.grid(row=1, column=0, padx=10, pady=10)

        self.rear_right = TyreInfo(tyre_frame, "RR")
        self.rear_right.grid(row=1, column=1, padx=10, pady=10)

    def update_values(self) -> None:

        if self.telemetry is not None:

            self.fuel_var.set(f"{self.telemetry.fuel:.1f}")

            pressure = astuple(self.telemetry.tyre_pressure)
            tyre_temp = astuple(self.telemetry.tyre_temp)
            brake_temp = astuple(self.telemetry.brake_temp)
            pad_wear = astuple(self.telemetry.pad_wear)
            disc_wear = astuple(self.telemetry.disc_wear)

            self.front_left.update_value(pressure[0], tyre_temp[0],
                                         brake_temp[0], pad_wear[0],
                                         disc_wear[0])

            self.front_right.update_value(pressure[1], tyre_temp[1],
                                          brake_temp[1], pad_wear[1],
                                          disc_wear[1])

            self.rear_left.update_value(pressure[2], tyre_temp[2],
                                        brake_temp[2], pad_wear[2],
                                        disc_wear[2])

            self.rear_right.update_value(pressure[3], tyre_temp[3],
                                         brake_temp[3], pad_wear[3],
                                         disc_wear[3])

            self.lap_time_var.set(string_time_from_ms(self.telemetry.lap_time))
            self.best_time_var.set(
                string_time_from_ms(self.telemetry.best_time))
            self.prev_time_var.set(
                string_time_from_ms(self.telemetry.previous_time))

            if self.current_driver != self.telemetry.driver:

                self.current_driver = self.telemetry.driver
                self.driver_swap = True
