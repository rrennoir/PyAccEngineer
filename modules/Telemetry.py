from __future__ import annotations

import logging
import struct
import tkinter
from dataclasses import astuple, dataclass
from tkinter import ttk
import copy
from typing import ClassVar, List

from SharedMemory.PyAccSharedMemory import (ACC_SESSION_TYPE,
                                            ACC_TRACK_GRIP_STATUS, Wheels,
                                            CarDamage, ACC_RAIN_INTENSITY)

from modules.Common import convert_to_rgb, rgbtohex, string_time_from_ms

log = logging.getLogger(__name__)


class TyreInfo(ttk.Frame):

    def __init__(self, root, name: str, on_the_right: bool = True):

        ttk.Frame.__init__(self, master=root)

        self.colours = [(32, 32, 255), (32, 255, 32), (255, 32, 32)]

        self.tyre_pressure = tkinter.DoubleVar()
        self.tyre_temp = tkinter.DoubleVar()
        self.brake_temp = tkinter.DoubleVar()
        self.pad_compound = tkinter.IntVar()
        self.pad_wear = tkinter.DoubleVar()
        self.disc_wear = tkinter.DoubleVar()

        self.has_wet = False

        self.name = name

        self.tyre_range = {
            "dry": {
                "pressure": [26, 29],
                "temperature": [50, 120]
            },
            "wet": {
                "pressure": [28, 32],
                "temperature": [20, 70]
            },
            "gt4": {
                "pressure": [25, 28],
                "temperatur": [40, 110]
            }
        }

        self.brake_range = {
            "front": [150, 850],
            "rear": [150, 750],
        }

        label_width = 20
        var_width = 5
        if on_the_right:
            label_column = 2
            var_column = 1
            tyre_column = 0
            txt_anchor = tkinter.W
            brake_x = 0
            core_x = 50

        else:
            label_column = 0
            var_column = 1
            tyre_column = 2
            txt_anchor = tkinter.E
            brake_x = 35
            core_x = 35

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
        self.core_rect = self.tyre_canvas.create_rectangle(core_x - 35, 35,
                                                           core_x, 65,
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

        l_pad_comp = ttk.Label(self, text="Pad compound", width=label_width,
                               anchor=txt_anchor)
        l_pad_comp.grid(row=row_count, column=label_column)

        l_pad_comp_var = ttk.Label(self, textvariable=self.pad_compound,
                                   width=var_width, anchor=tkinter.CENTER)
        l_pad_comp_var.grid(row=row_count, column=var_column)
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

    def update_value(self, pad_compound: int, pad_wear: float,
                     disc_wear: float, has_wet: bool, tyre_pressure: float,
                     tyre_temp: float, brake_temp: float) -> None:

        self.pad_compound.set(pad_compound + 1)
        self.pad_wear.set(round(pad_wear, 1))
        self.disc_wear.set(round(disc_wear, 1))
        self.has_wet = has_wet

        self.tyre_pressure.set(round(tyre_pressure, 1))
        self.tyre_temp.set(round(tyre_temp, 1))
        self.brake_temp.set(round(brake_temp, 1))

        self.update_tyre_hud(tyre_pressure, tyre_temp)
        self.update_brake_hud(brake_temp)

    def update_tyre_hud(self, pressure: float, temperature: float) -> None:

        pressure_range = self.tyre_range["dry"]["pressure"]
        temperature_range = self.tyre_range["dry"]["temperature"]
        if self.has_wet:
            pressure_range = self.tyre_range["wet"]["pressure"]
            temperature_range = self.tyre_range["wet"]["temperature"]

        if pressure > pressure_range[1]:
            colour = self.colours[2]

        elif pressure < pressure_range[0]:
            colour = self.colours[0]

        else:
            colour = convert_to_rgb(pressure_range[0], pressure_range[1],
                                    pressure, self.colours)

        self.tyre_canvas.itemconfig(self.tyre_rect, fill=rgbtohex(*colour))

        if temperature > temperature_range[1]:
            colour = self.colours[2]

        elif temperature < temperature_range[0]:
            colour = self.colours[0]

        else:
            colour = convert_to_rgb(temperature_range[0], temperature_range[1],
                                    temperature, self.colours)

        self.tyre_canvas.itemconfig(self.core_rect, fill=rgbtohex(*colour))

    def update_brake_hud(self, brake_temp: float) -> None:

        side = "front"
        if self.name.startswith("R"):
            side = "rear"

        if brake_temp > self.brake_range[side][1]:
            colour = self.colours[2]

        elif brake_temp < self.brake_range[side][0]:
            colour = self.colours[0]

        else:
            colour = convert_to_rgb(self.brake_range[side][0],
                                    self.brake_range[side][1], brake_temp,
                                    self.colours)

        self.tyre_canvas.itemconfig(self.brake_rect, fill=rgbtohex(*colour))

    def reset_value(self) -> None:

        self.tyre_pressure.set(0)
        self.tyre_temp.set(0)
        self.brake_temp.set(0)
        self.pad_wear.set(0)
        self.disc_wear.set(0)


class CarDamageInfo(ttk.Frame):

    def __init__(self, root):
        ttk.Frame.__init__(self, master=root)

        self.front_dmg = tkinter.DoubleVar()
        self.left_dmg = tkinter.DoubleVar()
        self.right_dmg = tkinter.DoubleVar()
        self.rear_dmg = tkinter.DoubleVar()

        row_counter = 0

        widget_tile = ttk.Label(self, text="Car Damage")
        widget_tile.grid(row=row_counter, column=0, columnspan=2)
        row_counter += 1

        l_front = ttk.Label(self, text="Front", width=7, anchor=tkinter.E)
        l_front.grid(row=row_counter, column=0)
        l_front_var = ttk.Label(self, textvariable=self.front_dmg, width=5,
                                anchor=tkinter.CENTER)
        l_front_var.grid(row=row_counter, column=1)
        row_counter += 1

        l_left = ttk.Label(self, text="Left", width=7, anchor=tkinter.E)
        l_left.grid(row=row_counter, column=0)
        l_left_var = ttk.Label(self, textvariable=self.left_dmg, width=5,
                               anchor=tkinter.CENTER)
        l_left_var.grid(row=row_counter, column=1)
        row_counter += 1

        l_right = ttk.Label(self, text="Right", width=7, anchor=tkinter.E)
        l_right.grid(row=row_counter, column=0)
        l_right_var = ttk.Label(self, textvariable=self.right_dmg, width=5,
                                anchor=tkinter.CENTER)
        l_right_var.grid(row=row_counter, column=1)
        row_counter += 1

        l_rear = ttk.Label(self, text="Rear", width=7, anchor=tkinter.E)
        l_rear.grid(row=row_counter, column=0)
        l_rear_var = ttk.Label(self, textvariable=self.rear_dmg, width=5,
                               anchor=tkinter.CENTER)
        l_rear_var.grid(row=row_counter, column=1)

    def update_values(self, car_damage: CarDamage) -> None:

        self.front_dmg.set(round(car_damage.front, 1))
        self.left_dmg.set(round(car_damage.left, 1))
        self.right_dmg.set(round(car_damage.right, 1))
        self.rear_dmg.set(round(car_damage.rear, 1))


@dataclass
class TelemetryRT:

    gas: float
    brake: float
    streering_angle: float
    gear: int
    speed: float

    byte_format: ClassVar[str] = "!3f i f"
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:

        return struct.pack(self.byte_format, *astuple(self))

    @classmethod
    def from_bytes(cls, data: bytes) -> TelemetryRT:

        if len(data) > cls.byte_size:

            log.warning(f"Telemetry: Warning got packet of {len(data)} bytes")
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
    session_left: float
    grip: ACC_TRACK_GRIP_STATUS
    front_pad: int
    rear_pad: int
    damage: CarDamage
    condition: ACC_RAIN_INTENSITY

    byte_size: ClassVar[int] = struct.calcsize(
        "!B i 11f 3i 2? B i 12f ? f B 2B 5f B")
    byte_format: ClassVar[str] = "!B i 11f 3i 2? B i 12f ? f B 2B 5f B"

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
            struct.pack("!?", self.has_wet_tyres),
            struct.pack("!f", self.session_left),
            struct.pack("!B", self.grip.value),
            struct.pack("!B", self.front_pad),
            struct.pack("!B", self.rear_pad),
            struct.pack("!5f", *astuple(self.damage)),
            struct.pack("!B", self.condition.value)
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> Telemetry:

        lenght = data[0]
        expected_packet_size = cls.byte_size + lenght

        if len(data) > expected_packet_size:
            psize = len(data)
            log.warning(f"Got packet of {psize} bytes,"
                        f" expected {expected_packet_size}")
            data = data[:expected_packet_size + 1]

        raw_data = struct.unpack(
            f"!{lenght}s i 11f 3i 2? B i 12f ? f B 2B 5f B",
            data[1:])

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
            rest[32],
            ACC_TRACK_GRIP_STATUS(rest[33]),
            rest[34],
            rest[35],
            CarDamage(*rest[36:41]),
            ACC_RAIN_INTENSITY(rest[41])
        )


class TelemetryUI(ttk.Frame):

    def __init__(self, root):

        ttk.Frame.__init__(self, master=root)

        self.current_driver = None
        self.driver_swap = False

        self.session = tkinter.StringVar()
        self.time_left = tkinter.StringVar(value="00:00:00")
        self.lap_var = tkinter.IntVar()
        self.grip_status = tkinter.StringVar()
        self.condition = tkinter.StringVar()

        self.lap_time_var = tkinter.StringVar(value="00:00.000")
        self.best_time_var = tkinter.StringVar(value="00:00.000")
        self.prev_time_var = tkinter.StringVar(value="00:00.000")

        self.fuel_var = tkinter.DoubleVar()
        self.fuel_per_lap_var = tkinter.DoubleVar()
        self.fuel_lap_left_var = tkinter.DoubleVar()

        self.time_pad_failure = tkinter.StringVar(value="00:00:00")
        self.prev_pad_life: List[int] = []
        self.prev_time_left: int = 0
        self.lap = 0

        self._build_telemetry_ui()

        tyre_frame = ttk.Frame(self)
        tyre_frame.grid(row=4, column=0)

        self.front_left = TyreInfo(tyre_frame, "Front left", False)
        self.front_left.grid(row=0, column=0, padx=10, pady=10)

        self.front_right = TyreInfo(tyre_frame, "Front right")
        self.front_right.grid(row=0, column=1, padx=10, pady=10)

        self.rear_left = TyreInfo(tyre_frame, "Rear left", False)
        self.rear_left.grid(row=1, column=0, padx=10, pady=10)

        self.rear_right = TyreInfo(tyre_frame, "Rear right")
        self.rear_right.grid(row=1, column=1, padx=10, pady=10)

        f_side_info = ttk.Frame(self)
        f_side_info.grid(row=0, column=1, rowspan=6)

        self.damage_info = CarDamageInfo(f_side_info)
        self.damage_info.grid(row=0, column=0, pady=5)

    def _build_telemetry_ui(self) -> None:

        f_main_info = ttk.Frame(self)
        f_main_info.grid(row=0, column=0)

        f_info = ttk.Frame(self)
        f_info.grid(row=1, column=0, padx=1, pady=1)

        f_info2 = ttk.Frame(self)
        f_info2.grid(row=2, column=0, padx=1, pady=1)

        f_info3 = ttk.Frame(self)
        f_info3.grid(row=3, column=0, padx=1, pady=1)

        column_count = 0

        # Session name
        l_session = ttk.Label(f_main_info, text="Session")
        l_session.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_session_var = ttk.Label(f_main_info, textvariable=self.session,
                                  width=8)
        l_session_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Time left
        l_time_left = ttk.Label(f_main_info, text="Time left")
        l_time_left.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_time_left_var = ttk.Label(f_main_info, textvariable=self.time_left,
                                    width=7)
        l_time_left_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Grip
        l_grip = ttk.Label(f_main_info, text="Grip status")
        l_grip.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_grip_var = ttk.Label(f_main_info, textvariable=self.grip_status,
                               width=10)
        l_grip_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Condition
        l_condition = ttk.Label(f_main_info, text="Condition")
        l_condition.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_condition_var = ttk.Label(f_main_info, textvariable=self.condition,
                                    width=10)
        l_condition_var.grid(row=0, column=column_count, padx=1, pady=1)

        column_count = 0

        # Lap time
        l_lap_time = ttk.Label(f_info, text="Lap time")
        l_lap_time.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_lap_time_var = ttk.Label(f_info, textvariable=self.lap_time_var,
                                   width=10)
        l_lap_time_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # best time
        l_best_time = ttk.Label(f_info, text="Best time")
        l_best_time.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_best_time_var = ttk.Label(f_info, textvariable=self.best_time_var,
                                    width=10)
        l_best_time_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Previous time
        l_prev_time = ttk.Label(f_info, text="Previous time")
        l_prev_time.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_prev_time_var = ttk.Label(f_info,
                                    textvariable=self.prev_time_var, width=10)
        l_prev_time_var.grid(row=0, column=column_count, padx=1, pady=1)

        column_count = 0

        # Lap
        l_lap = ttk.Label(f_info2, text="Lap")
        l_lap.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_lap_var = ttk.Label(f_info2, textvariable=self.lap_var,
                              width=4)
        l_lap_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Fuel
        l_fuel = ttk.Label(f_info2, text="Fuel")
        l_fuel.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_fuel_var = ttk.Label(f_info2, textvariable=self.fuel_var,
                               width=5)
        l_fuel_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Fuel per lap
        l_fuel_per_lap = ttk.Label(f_info2, text="Fuel per lap")
        l_fuel_per_lap.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_fuel_per_lap_var = ttk.Label(f_info2,
                                       textvariable=self.fuel_per_lap_var,
                                       width=5,)
        l_fuel_per_lap_var.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        # Lap left
        l_fuel_lap_left = ttk.Label(f_info2, text="Lap left with fuel")
        l_fuel_lap_left.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        l_fuel_lap_left_var = ttk.Label(
            f_info2, textvariable=self.fuel_lap_left_var, width=5)
        l_fuel_lap_left_var.grid(row=0, column=column_count, padx=1, pady=1)

        l_pad_fail = ttk.Label(f_info3, text="Time before brake failure")
        l_pad_fail.grid(row=0, column=0)

        l_pad_fal_var = ttk.Label(f_info3, textvariable=self.time_pad_failure)
        l_pad_fal_var.grid(row=0, column=1)

    def update_values(self, telemetry: Telemetry) -> None:

        pressure = astuple(telemetry.tyre_pressure)
        tyre_temp = astuple(telemetry.tyre_temp)
        brake_temp = astuple(telemetry.brake_temp)

        self.grip_status.set(telemetry.grip)

        self.time_left.set(string_time_from_ms(int(telemetry.session_left),
                                               hours=True)[:-4])
        self.session.set(telemetry.session)
        self.condition.set(telemetry.condition)
        self.lap_var.set(telemetry.lap)
        self.fuel_var.set(round(telemetry.fuel, 1))
        self.fuel_per_lap_var.set(round(telemetry.fuel_per_lap, 1))
        self.fuel_lap_left_var.set(round(telemetry.fuel_estimated_laps, 1))

        front_pad = telemetry.front_pad
        rear_pad = telemetry.rear_pad
        pad_wear = astuple(telemetry.pad_wear)
        disc_wear = astuple(telemetry.disc_wear)

        if self.lap != telemetry.lap and telemetry.session_left != -1:
            self.lap = telemetry.lap
            if len(self.prev_pad_life) != 0 and self.prev_time_left != 0:

                time_delta = self.prev_time_left - telemetry.session_left
                time_left = []
                for pad, prev_pad in zip(pad_wear, self.prev_pad_life):

                    lap_wear = prev_pad - pad
                    pad_left = pad - 12.5
                    lap_left = pad_left / lap_wear
                    time_left.append(int(lap_left * time_delta))

                time_for_fail = min(time_left)
                self.time_pad_failure.set(string_time_from_ms(time_for_fail,
                                                              True)[:-4])

            self.prev_time_left = int(telemetry.session_left)
            self.prev_pad_life = copy.copy(pad_wear)

        self.front_left.update_value(front_pad, pad_wear[0], disc_wear[0],
                                     telemetry.has_wet_tyres, pressure[0],
                                     tyre_temp[0], brake_temp[0])

        self.front_right.update_value(front_pad, pad_wear[1], disc_wear[1],
                                      telemetry.has_wet_tyres, pressure[1],
                                      tyre_temp[1], brake_temp[1])

        self.rear_left.update_value(rear_pad, pad_wear[2], disc_wear[2],
                                    telemetry.has_wet_tyres, pressure[2],
                                    tyre_temp[2], brake_temp[2])

        self.rear_right.update_value(rear_pad, pad_wear[3], disc_wear[3],
                                     telemetry.has_wet_tyres, pressure[3],
                                     tyre_temp[3],  brake_temp[3])

        self.lap_time_var.set(string_time_from_ms(telemetry.lap_time))
        self.best_time_var.set(string_time_from_ms(telemetry.best_time))
        self.prev_time_var.set(string_time_from_ms(telemetry.previous_time))

        self.damage_info.update_values(telemetry.damage)

        if self.current_driver != telemetry.driver:

            self.current_driver = telemetry.driver
            self.driver_swap = True
