from __future__ import annotations

import struct
import tkinter
from tkinter import ttk
from dataclasses import astuple, dataclass
from typing import ClassVar, Optional

from SharedMemory.PyAccSharedMemory import Wheels, ACC_SESSION_TYPE

from modules.Common import rgbtohex, string_time_from_ms, convert_to_rgb


class TyreInfo(ttk.Frame):

    def __init__(self, root, name: str, on_the_right: bool = True):

        ttk.Frame.__init__(self, master=root)

        self.colours = [(32, 32, 255), (32, 255, 32), (255, 32, 32)]

        self.tyre_pressure = tkinter.DoubleVar()
        self.tyre_temp = tkinter.DoubleVar()
        self.brake_temp = tkinter.DoubleVar()
        self.pad_wear = tkinter.DoubleVar()
        self.disc_wear = tkinter.DoubleVar()

        label_width = 20
        var_width = 5
        if on_the_right:
            label_column = 2
            var_column = 1
            tyre_column = 0
            txt_anchor = tkinter.W
            brake_x = 0

        else:
            label_column = 0
            var_column = 1
            tyre_column = 2
            txt_anchor = tkinter.E
            brake_x = 35

        row_count = 0
        f_tyre = ttk.Frame(self)
        f_tyre.grid(row=row_count, rowspan=6, column=tyre_column)

        self.tyre_canvas = tkinter.Canvas(f_tyre, width=50, height=100)
        self.tyre_canvas.pack(padx=10)

        self.tyre_rect = self.tyre_canvas.create_rectangle(0, 0, 50, 100,
                                                           fill="Grey")

        self.brake_rect = self.tyre_canvas.create_rectangle(brake_x, 25,
                                                            brake_x + 15, 75,
                                                            fill="Grey")

        l_tyre = ttk.Label(self, text=name, width=label_width,
                           anchor=txt_anchor)
        l_tyre.grid(row=row_count, column=label_column)
        row_count += 1

        l_tyre_pressure = ttk.Label(self, text="Tyre pressure",
                                    width=label_width, anchor=txt_anchor)

        l_tyre_pressure_var = ttk.Label(self, textvariable=self.tyre_pressure,
                                        width=var_width, anchor=tkinter.CENTER)

        l_tyre_pressure.grid(row=row_count, column=label_column)
        l_tyre_pressure_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_tyre_temp = ttk.Label(self, text="Tyre temperature",
                                width=label_width, anchor=txt_anchor)
        l_tyre_temp_var = ttk.Label(self, textvariable=self.tyre_temp,
                                    width=var_width, anchor=tkinter.CENTER)
        l_tyre_temp.grid(row=row_count, column=label_column)
        l_tyre_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_brake_temp = ttk.Label(self, text="Brake temperature",
                                 width=label_width, anchor=txt_anchor)
        l_brake_temp_var = ttk.Label(self, textvariable=self.brake_temp,
                                     width=var_width, anchor=tkinter.CENTER)
        l_brake_temp.grid(row=row_count, column=label_column)
        l_brake_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_pad_wear = ttk.Label(self, text="Pad wear", width=label_width,
                               anchor=txt_anchor)
        l_pad_wear.grid(row=row_count, column=label_column)

        l_pad_wear_var = ttk.Label(self, textvariable=self.pad_wear,
                                   width=var_width, anchor=tkinter.CENTER)
        l_pad_wear_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_disc_wear = ttk.Label(self, text="Disc wear",
                                width=label_width, anchor=txt_anchor)
        l_disc_wear.grid(row=row_count, column=label_column)

        l_disc_wear_var = ttk.Label(self, textvariable=self.disc_wear,
                                    width=var_width, anchor=tkinter.CENTER)
        l_disc_wear_var.grid(row=row_count, column=var_column)

    def update_value(self, pad_wear: float, disc_wear: float) -> None:

        self.pad_wear.set(f"{pad_wear:.1f}")
        self.disc_wear.set(f"{disc_wear:.1f}")

    def update_rt_value(self, tyre_pressure: float,
                        tyre_temp: float, brake_temp: float) -> None:

        self.tyre_pressure.set(f"{tyre_pressure:.1f}")
        self.tyre_temp.set(f"{tyre_temp:.1f}")
        self.brake_temp.set(f"{brake_temp:.1f}")

        self.update_tyre_hud(tyre_pressure)
        self.update_brake_hud(brake_temp)

    def update_tyre_hud(self, pressure: float) -> None:

        if pressure > 29:
            colour = self.colours[2]

        elif pressure < 26:
            colour = self.colours[0]

        else:
            colour = convert_to_rgb(26, 29, pressure, self.colours)

        self.tyre_canvas.itemconfig(self.tyre_rect, fill=rgbtohex(*colour))

    def update_brake_hud(self, brake_temp: float) -> None:

        if brake_temp > 1000:
            colour = self.colours[2]

        elif brake_temp < 100:
            colour = self.colours[0]

        else:
            colour = convert_to_rgb(100, 1000, brake_temp, self.colours)

        self.tyre_canvas.itemconfig(self.brake_rect, fill=rgbtohex(*colour))

    def reset_value(self) -> None:

        self.tyre_pressure.set(0)
        self.tyre_temp.set(0)
        self.brake_temp.set(0)
        self.pad_wear.set(0)
        self.disc_wear.set(0)


@dataclass
class TelemetryRT:

    gas: float
    brake: float
    streering_angle: float
    gear: float
    speed: float

    byte_format: ClassVar[str] = "!5f"
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:

        buffer = [
            struct.pack("!f", self.gas),
            struct.pack("!f", self.brake),
            struct.pack("!f", self.streering_angle),
            struct.pack("!f", self.gear),
            struct.pack("!f", self.speed),
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> TelemetryRT:

        if len(data) > cls.byte_size:

            print(f"Telemetry: Warning got packet of {len(data)} bytes")
            data = data[:cls.byte_size]

        unpacked_data = struct.unpack(cls.byte_format, data)

        return TelemetryRT(*unpacked_data)


@dataclass
class Telemetry:

    driver: str
    lap: int
    fuel: float
    fuel_per_lap: float
    fuel_estimated_laps: float
    pad_wear: Wheels
    disc_wear: Wheels
    lap_time: int
    best_time: int
    previous_time: int
    in_pit: bool
    in_pit_lane: bool
    session: ACC_SESSION_TYPE
    driver_stint_time_left: int
    tyre_pressure: Wheels
    tyre_temp: Wheels
    brake_temp: Wheels
    has_wet_tyres: bool

    byte_size: ClassVar[int] = struct.calcsize("!B i 11f 3i 2? B i 12f B")
    byte_format: ClassVar[str] = "!B i 11f 3i 2? B i 12f B"

    def to_bytes(self) -> bytes:

        driver_lenght = len(self.driver)

        buffer = [
            struct.pack("!B", driver_lenght),
            self.driver.encode("utf-8"),
            struct.pack("!i", self.lap),
            struct.pack("!f", self.fuel),
            struct.pack("!f", self.fuel_per_lap),
            struct.pack("!f", self.fuel_estimated_laps),
            struct.pack("!4f", *astuple(self.pad_wear)),
            struct.pack("!4f", *astuple(self.disc_wear)),
            struct.pack("!i", self.lap_time),
            struct.pack("!i", self.best_time),
            struct.pack("!i", self.previous_time),
            struct.pack("!?", self.in_pit),
            struct.pack("!?", self.in_pit_lane),
            struct.pack("!B", self.session.value),
            struct.pack("!i", self.driver_stint_time_left),
            struct.pack("!4f", *astuple(self.tyre_pressure)),
            struct.pack("!4f", *astuple(self.tyre_temp)),
            struct.pack("!4f", *astuple(self.brake_temp)),
            struct.pack("!B", self.has_wet_tyres),
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> Telemetry:

        lenght = data[0]
        expected_packet_size = cls.byte_size + lenght

        if len(data) > expected_packet_size:
            psize = len(data)
            print(f"Telemetry: Warning got packet of {psize} bytes,"
                  f" expected {expected_packet_size}")
            data = data[:expected_packet_size + 1]

        raw_data = struct.unpack(f"!{lenght}s i 11f 3i 2? B i 12f B", data[1:])

        name = raw_data[0].decode("utf-8")
        rest = raw_data[1:]

        return Telemetry(
            name,
            rest[0],
            rest[1],
            rest[2],
            rest[3],
            Wheels(*rest[4:8]),
            Wheels(*rest[8:12]),
            rest[12],
            rest[13],
            rest[14],
            rest[15],
            rest[16],
            ACC_SESSION_TYPE(rest[17]),
            rest[18],
            Wheels(*rest[19:23]),
            Wheels(*rest[23:27]),
            Wheels(*rest[27:31]),
            rest[31],
        )


class TelemetryUI(ttk.Frame):

    def __init__(self, root):

        ttk.Frame.__init__(self, master=root)

        self.telemetry: Optional[Telemetry] = None
        self.telemetry_rt: Optional[TelemetryRT] = None

        self.current_driver = None
        self.driver_swap = False

        self.lap_time_var = tkinter.StringVar(value="00:00.000")
        self.best_time_var = tkinter.StringVar(value="00:00.000")
        self.prev_time_var = tkinter.StringVar(value="00:00.000")

        self.lap_var = tkinter.IntVar()
        self.fuel_var = tkinter.DoubleVar()
        self.fuel_per_lap_var = tkinter.DoubleVar()
        self.fuel_lap_left_var = tkinter.DoubleVar()

        self.gas = tkinter.DoubleVar()
        self.brake = tkinter.DoubleVar()
        self.steering = tkinter.DoubleVar()
        self.gear = tkinter.IntVar()
        self.speed = tkinter.DoubleVar()

        self._build_telemetry_ui()

        tyre_frame = ttk.Frame(self)
        tyre_frame.grid(row=2, column=0)

        self.front_left = TyreInfo(tyre_frame, "Front left", False)
        self.front_left.grid(row=0, column=0, padx=10, pady=10)

        self.front_right = TyreInfo(tyre_frame, "Front right")
        self.front_right.grid(row=0, column=1, padx=10, pady=10)

        self.rear_left = TyreInfo(tyre_frame, "Rear left", False)
        self.rear_left.grid(row=1, column=0, padx=10, pady=10)

        self.rear_right = TyreInfo(tyre_frame, "Rear right")
        self.rear_right.grid(row=1, column=1, padx=10, pady=10)

        f_driver_input = ttk.Frame(self)
        f_driver_input.grid(row=0, column=1, rowspan=3)

        self.c_gas = tkinter.Canvas(f_driver_input, width=20, height=100)
        self.c_gas.grid(row=0, column=0, padx=10)

        self.c_brake = tkinter.Canvas(f_driver_input, width=20, height=100)
        self.c_brake.grid(row=0, column=1, padx=10)

        self.c_steering = tkinter.Canvas(f_driver_input, width=100, height=20)
        self.c_steering.grid(row=1, column=0, padx=10, pady=10, columnspan=2)

        self.gas_rect = self.c_gas.create_rectangle(0, 0, 20, 100,
                                                    fill="Green")
        self.brake_rect = self.c_brake.create_rectangle(0, 0, 20, 100,
                                                        fill="Red")

        self.steering_rect = self.c_steering.create_rectangle(0, 0, 100, 20,
                                                              fill="Yellow")

        l_gear = ttk.Label(f_driver_input, text="Gear", width=7)
        l_gear.grid(row=2, column=0)

        gear_var = ttk.Label(f_driver_input, textvariable=self.gear, width=3)
        gear_var.grid(row=2, column=1)

        l_speed = ttk.Label(f_driver_input, text="Speed", width=7)
        l_speed.grid(row=3, column=0)

        speed_var = ttk.Label(f_driver_input, textvariable=self.speed, width=3)
        speed_var.grid(row=3, column=1)

    def _build_telemetry_ui(self) -> None:

        f_info = ttk.Frame(self)
        f_info.grid(row=0, column=0, padx=1, pady=1)

        f_info2 = ttk.Frame(self)
        f_info2.grid(row=1, column=0, padx=1, pady=1)

        # Lap time
        l_lap_time = ttk.Label(f_info, text="Lap time")
        l_lap_time.grid(row=0, column=0, padx=1, pady=1)

        l_lap_time_var = ttk.Label(f_info, textvariable=self.lap_time_var,
                                   width=10)
        l_lap_time_var.grid(row=0, column=1, padx=1, pady=1)

        # best time
        l_best_time = ttk.Label(f_info, text="Best time")
        l_best_time.grid(row=0, column=2, padx=1, pady=1)

        l_best_time_var = ttk.Label(f_info, textvariable=self.best_time_var,
                                    width=10)
        l_best_time_var.grid(row=0, column=3, padx=1, pady=1)

        # Previous time
        l_prev_time = ttk.Label(f_info, text="Previous time")
        l_prev_time.grid(row=0, column=4, padx=1, pady=1)

        l_prev_time_var = ttk.Label(f_info,
                                    textvariable=self.prev_time_var, width=10)
        l_prev_time_var.grid(row=0, column=5, padx=1, pady=1)

        # Lap
        l_lap = ttk.Label(f_info2, text="Lap")
        l_lap.grid(row=0, column=0, padx=1, pady=1)

        l_lap_var = ttk.Label(f_info2, textvariable=self.lap_var,
                              width=5)
        l_lap_var.grid(row=0, column=1, padx=1, pady=1)

        # Fuel
        l_fuel = ttk.Label(f_info2, text="Fuel")
        l_fuel.grid(row=0, column=2, padx=1, pady=1)

        l_fuel_var = ttk.Label(f_info2, textvariable=self.fuel_var,
                               width=5)
        l_fuel_var.grid(row=0, column=3, padx=1, pady=1)

        # Fuel per lap
        l_fuel_per_lap = ttk.Label(f_info2, text="Fuel per lap")
        l_fuel_per_lap.grid(row=0, column=4, padx=1, pady=1)

        l_fuel_per_lap_var = ttk.Label(f_info2,
                                       textvariable=self.fuel_per_lap_var,
                                       width=5,)
        l_fuel_per_lap_var.grid(row=0, column=5, padx=1, pady=1)

        # Lap left
        l_fuel_lap_left = ttk.Label(f_info2, text="Lap left with fuel")
        l_fuel_lap_left.grid(row=0, column=6, padx=1, pady=1)

        l_fuel_lap_left_var = ttk.Label(
            f_info2, textvariable=self.fuel_lap_left_var, width=5)
        l_fuel_lap_left_var.grid(row=0, column=7, padx=1, pady=1)

    def update_values(self) -> None:

        if self.telemetry is not None:

            pressure = astuple(self.telemetry.tyre_pressure)
            tyre_temp = astuple(self.telemetry.tyre_temp)
            brake_temp = astuple(self.telemetry.brake_temp)

            self.front_left.update_rt_value(pressure[0], tyre_temp[0],
                                            brake_temp[0])

            self.front_right.update_rt_value(pressure[1], tyre_temp[1],
                                             brake_temp[1])

            self.rear_left.update_rt_value(pressure[2], tyre_temp[2],
                                           brake_temp[2])

            self.rear_right.update_rt_value(pressure[3], tyre_temp[3],
                                            brake_temp[3])

            self.lap_var.set(self.telemetry.lap)
            self.fuel_var.set(f"{self.telemetry.fuel:.1f}")
            self.fuel_per_lap_var.set(f"{self.telemetry.fuel_per_lap:.2f}")
            self.fuel_lap_left_var.set(
                f"{self.telemetry.fuel_estimated_laps:.1f}")

            pad_wear = astuple(self.telemetry.pad_wear)
            disc_wear = astuple(self.telemetry.disc_wear)

            self.front_left.update_value(
                pad_wear[0], disc_wear[0], self.telemetry.has_wet_tyres)

            self.front_right.update_value(
                pad_wear[1], disc_wear[1], self.telemetry.has_wet_tyres)

            self.rear_left.update_value(
                pad_wear[2], disc_wear[2], self.telemetry.has_wet_tyres)

            self.rear_right.update_value(
                pad_wear[3],  disc_wear[3], self.telemetry.has_wet_tyres)

            self.lap_time_var.set(string_time_from_ms(self.telemetry.lap_time))
            self.best_time_var.set(
                string_time_from_ms(self.telemetry.best_time))
            self.prev_time_var.set(
                string_time_from_ms(self.telemetry.previous_time))

            if self.current_driver != self.telemetry.driver:

                self.current_driver = self.telemetry.driver
                self.driver_swap = True

    def update_values_rt(self) -> None:

        if self.telemetry_rt is not None:

            self.gas.set(self.telemetry_rt.gas)
            self.brake.set(self.telemetry_rt.brake)
            self.steering.set(self.telemetry_rt.streering_angle)
            self.gear.set(self.telemetry_rt.gear - 1)
            self.speed.set(f"{self.telemetry_rt.speed:.1f}")

            self.c_gas.coords(self.gas_rect, 0,
                              100 - self.gas.get() * 100,  20, 100)
            self.c_brake.coords(self.brake_rect, 0,
                                100 - self.brake.get() * 100,  20, 100)

            self.c_steering.coords(self.steering_rect,
                                   0, 0, (self.steering.get() + 1) * 50, 20)
