from __future__ import annotations

import copy
import logging
import struct
import tkinter
from dataclasses import astuple, dataclass
from tkinter import ttk
from typing import ClassVar, List

from SharedMemory.PyAccSharedMemory import (ACC_RAIN_INTENSITY,
                                            ACC_SESSION_TYPE,
                                            ACC_TRACK_GRIP_STATUS, CarDamage,
                                            Wheels)

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

        label_width = 16
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

        self.front = tkinter.DoubleVar()
        self.left = tkinter.DoubleVar()
        self.right = tkinter.DoubleVar()
        self.rear = tkinter.DoubleVar()

        self.sus_fl = tkinter.DoubleVar()
        self.sus_fr = tkinter.DoubleVar()
        self.sus_rl = tkinter.DoubleVar()
        self.sus_rr = tkinter.DoubleVar()

        self.total_repair = tkinter.DoubleVar()

        self._build_bodywork_ui()

        f_total = ttk.Frame(self, style="TelemetryGrid.TFrame")
        f_total.pack(side=tkinter.LEFT)
        total_time = ttk.Label(f_total, text="Toal repair",
                               width=10, anchor=tkinter.CENTER)
        total_time.grid(row=0, column=0, padx=2, pady=(2, 1))

        total_time_var = ttk.Label(f_total, textvariable=self.total_repair,
                                   width=10, anchor=tkinter.CENTER)
        total_time_var.grid(row=1, column=0, padx=2, pady=(1, 2))

        self._build_suspension_ui()

    def _build_bodywork_ui(self) -> None:

        f_bodywork = ttk.Frame(self, style="TelemetryGrid.TFrame")
        f_bodywork.pack(side=tkinter.LEFT, padx=(0, 5))

        f_title = ttk.Frame(f_bodywork)
        f_title.grid(row=0, column=0, rowspan=2, padx=(2, 1))
        sub_widget_tile = ttk.Label(f_title, text="Bodywork\ndamage",
                                    width=10, anchor=tkinter.CENTER, )
        sub_widget_tile.pack()

        l_front = ttk.Label(f_bodywork, text="Front",
                            width=7, anchor=tkinter.CENTER)
        l_front.grid(row=0, column=1, padx=1, pady=(2, 1))
        l_front_var = ttk.Label(f_bodywork, textvariable=self.front, width=7,
                                anchor=tkinter.CENTER)
        l_front_var.grid(row=1, column=1, padx=1, pady=(1, 2))

        l_left = ttk.Label(f_bodywork, text="Left", width=7,
                           anchor=tkinter.CENTER)
        l_left.grid(row=0, column=2, padx=1, pady=(2, 1))
        l_left_var = ttk.Label(f_bodywork, textvariable=self.left, width=7,
                               anchor=tkinter.CENTER)
        l_left_var.grid(row=1, column=2, padx=1, pady=(1, 2))

        l_right = ttk.Label(f_bodywork, text="Right",
                            width=7, anchor=tkinter.CENTER)
        l_right.grid(row=0, column=3, padx=1, pady=(2, 1))
        l_right_var = ttk.Label(f_bodywork, textvariable=self.right, width=7,
                                anchor=tkinter.CENTER)
        l_right_var.grid(row=1, column=3, padx=1, pady=(1, 2))

        l_rear = ttk.Label(f_bodywork, text="Rear", width=7,
                           anchor=tkinter.CENTER)
        l_rear.grid(row=0, column=4, padx=1, pady=(2, 1))
        l_rear_var = ttk.Label(f_bodywork, textvariable=self.rear, width=7,
                               anchor=tkinter.CENTER)
        l_rear_var.grid(row=1, column=4, padx=(1, 2), pady=(1, 2))

    def _build_suspension_ui(self) -> None:

        f_suspension = ttk.Frame(self, style="TelemetryGrid.TFrame")
        f_suspension.pack(side=tkinter.LEFT, padx=(5, 0))

        sub_widget_tile = ttk.Label(f_suspension,
                                    text="Suspension\ndamage",
                                    anchor=tkinter.CENTER, width=10)
        sub_widget_tile.grid(row=0, column=4, rowspan=2, padx=(1, 2))

        l_front = ttk.Label(f_suspension, text="FL", width=7,
                            anchor=tkinter.CENTER)
        l_front.grid(row=0, column=0, padx=1, pady=(2, 1))
        l_front_var = ttk.Label(f_suspension, textvariable=self.sus_fl,
                                width=7, anchor=tkinter.CENTER)
        l_front_var.grid(row=1, column=0, padx=1, pady=(1, 2))

        l_left = ttk.Label(f_suspension, text="FR", width=7,
                           anchor=tkinter.CENTER)
        l_left.grid(row=0, column=1, padx=1, pady=(2, 1))
        l_left_var = ttk.Label(f_suspension, textvariable=self.sus_fr,
                               width=7, anchor=tkinter.CENTER)
        l_left_var.grid(row=1, column=1, padx=1, pady=(1, 2))

        l_right = ttk.Label(f_suspension, text="RL", width=7,
                            anchor=tkinter.CENTER)
        l_right.grid(row=0, column=2, padx=1, pady=(2, 1))
        l_right_var = ttk.Label(f_suspension, textvariable=self.sus_rl,
                                width=7, anchor=tkinter.CENTER)
        l_right_var.grid(row=1, column=2, padx=1, pady=(1, 2))

        l_rear = ttk.Label(f_suspension, text="RR", width=7,
                           anchor=tkinter.CENTER)
        l_rear.grid(row=0, column=3, padx=1, pady=(2, 1))
        l_rear_var = ttk.Label(f_suspension, textvariable=self.sus_rr,
                               width=7, anchor=tkinter.CENTER)
        l_rear_var.grid(row=1, column=3, padx=(1, 2), pady=(1, 2))

    def update_values(self, bodywork: CarDamage, suspension: Wheels) -> None:

        body_dmg_to_s_ratio = 0.282  # Kunos why >:o

        self.front.set(round(bodywork.front * body_dmg_to_s_ratio, 1))
        self.left.set(round(bodywork.left * body_dmg_to_s_ratio, 1))
        self.right.set(round(bodywork.right * body_dmg_to_s_ratio, 1))
        self.rear.set(round(bodywork.rear * body_dmg_to_s_ratio, 1))

        self.sus_fl.set(round(suspension.front_left * 30, 1))
        self.sus_fr.set(round(suspension.front_right * 30, 1))
        self.sus_rl.set(round(suspension.rear_left * 30, 1))
        self.sus_rr.set(round(suspension.rear_right * 30, 1))

        self.total_repair.set(round(self.front.get()
                                    + self.left.get()
                                    + self.right.get()
                                    + self.rear.get()
                                    + self.sus_fl.get()
                                    + self.sus_fr.get()
                                    + self.sus_rl.get()
                                    + self.sus_rr.get(), 1))


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
    suspension_damage: Wheels
    current_sector_index: int
    last_sector_time: int
    is_lap_valid: bool
    air_temp: float
    road_temp: float

    byte_size: ClassVar[int] = struct.calcsize("!B i 11f 3i 2? B i 12f ?"
                                               " f B 2B 5f B 4f 2i ? 2f")
    byte_format: ClassVar[str] = ("!B i 11f 3i 2? B i 12f ?"
                                  " f B 2B 5f B 4f 2i ? 2f")

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
            struct.pack("!B", self.condition.value),
            struct.pack("!4f", *astuple(self.suspension_damage)),
            struct.pack("!i", self.current_sector_index),
            struct.pack("!i", self.last_sector_time),
            struct.pack("!?", self.is_lap_valid),
            struct.pack("!f", self.air_temp),
            struct.pack("!f", self.road_temp),
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
            f"!{lenght}s i 11f 3i 2? B i 12f ? f B 2B 5f B 4f 2i ? 2f",
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
            ACC_RAIN_INTENSITY(rest[41]),
            Wheels(*rest[42:46]),
            rest[46],
            rest[47],
            rest[48],
            rest[49],
            rest[50],
        )


class TelemetryUI(ttk.Frame):

    def __init__(self, root):

        ttk.Frame.__init__(self, master=root)

        self.current_driver = None
        self.driver_swap = False

        self.session = tkinter.StringVar(value="Practice")
        self.time_left = tkinter.StringVar(value="00:00:00")
        self.lap_var = tkinter.IntVar()
        self.grip_status = tkinter.StringVar(value="Optimum")
        self.condition = tkinter.StringVar(value="Heavy rain")
        self.air_temp = tkinter.DoubleVar()
        self.road_temp = tkinter.DoubleVar()

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

        self._build_top_frame()

        f_middle = ttk.Frame(self)
        f_middle.pack()

        self._build_left_frame(f_middle)
        f_center = ttk.Frame(f_middle, style="TelemetryGrid.TFrame")
        f_center.pack(side=tkinter.LEFT)
        self._build_right_frame(f_middle)

        self.front_left = TyreInfo(f_center, "Front left", False)
        self.front_left.grid(row=0, column=0, padx=2, pady=2)

        self.front_right = TyreInfo(f_center, "Front right")
        self.front_right.grid(row=0, column=1, padx=2, pady=2)

        self.rear_left = TyreInfo(f_center, "Rear left", False)
        self.rear_left.grid(row=1, column=0, padx=2, pady=2)

        self.rear_right = TyreInfo(f_center, "Rear right")
        self.rear_right.grid(row=1, column=1, padx=2, pady=2)

        self._build_bottom_frame()

    def _build_top_frame(self) -> None:

        f_top = ttk.Frame(self, style="TelemetryGrid.TFrame")
        f_top.pack(pady=2)

        column_count = 0

        # Session name
        l_session = ttk.Label(f_top, text="Session", width=8,
                              anchor=tkinter.CENTER)
        l_session.grid(row=0, column=column_count, padx=(2, 1), pady=(2, 1))

        l_session_var = ttk.Label(f_top, textvariable=self.session,
                                  width=8, anchor=tkinter.CENTER)
        l_session_var.grid(row=1, column=column_count,
                           padx=(2, 1), pady=(1, 2))
        column_count += 1

        # Time left
        l_time_left = ttk.Label(f_top, text="Time left", width=8,
                                anchor=tkinter.CENTER)
        l_time_left.grid(row=0, column=column_count, padx=1, pady=(2, 1))

        l_time_left_var = ttk.Label(f_top, textvariable=self.time_left,
                                    width=8, anchor=tkinter.CENTER)
        l_time_left_var.grid(row=1, column=column_count, padx=1, pady=(1, 2))
        column_count += 1

        # Grip
        l_grip = ttk.Label(f_top, text="Grip status", width=10,
                           anchor=tkinter.CENTER)
        l_grip.grid(row=0, column=column_count, padx=1, pady=(2, 1))

        l_grip_var = ttk.Label(f_top, textvariable=self.grip_status,
                               width=10, anchor=tkinter.CENTER)
        l_grip_var.grid(row=1, column=column_count, padx=1, pady=(1, 2))
        column_count += 1

        # Condition
        l_condition = ttk.Label(f_top, text="Condition", width=10,
                                anchor=tkinter.CENTER)
        l_condition.grid(row=0, column=column_count, padx=1, pady=(2, 1))

        l_condition_var = ttk.Label(f_top, textvariable=self.condition,
                                    width=10, anchor=tkinter.CENTER)
        l_condition_var.grid(row=1, column=column_count, padx=1, pady=(1, 2))
        column_count += 1

        # Lap
        l_lap = ttk.Label(f_top, text="Lap", width=8, anchor=tkinter.CENTER)
        l_lap.grid(row=0, column=column_count, padx=1, pady=(2, 1))

        l_lap_var = ttk.Label(f_top, textvariable=self.lap_var,
                              width=8, anchor=tkinter.CENTER)
        l_lap_var.grid(row=1, column=column_count, padx=1, pady=(1, 2))
        column_count += 1

        # Air temp
        l_lap = ttk.Label(f_top, text="Air", width=8, anchor=tkinter.CENTER)
        l_lap.grid(row=0, column=column_count, padx=1, pady=(2, 1))

        l_lap_var = ttk.Label(f_top, textvariable=self.air_temp,
                              width=8, anchor=tkinter.CENTER)
        l_lap_var.grid(row=1, column=column_count, padx=1, pady=(1, 2))
        column_count += 1

        # Road temp
        l_lap = ttk.Label(f_top, text="Track", width=8, anchor=tkinter.CENTER)
        l_lap.grid(row=0, column=column_count, padx=(1, 2), pady=(2, 1))

        l_lap_var = ttk.Label(f_top, textvariable=self.road_temp,
                              width=8, anchor=tkinter.CENTER)
        l_lap_var.grid(row=1, column=column_count, padx=(1, 2), pady=(1, 2))

    def _build_bottom_frame(self) -> None:

        f_bottom = ttk.Frame(self)
        f_bottom.pack()

        self.damage_info = CarDamageInfo(f_bottom)
        self.damage_info.grid(pady=5)

    def _build_right_frame(self, center_frame: ttk.Frame) -> None:

        f_right = ttk.Frame(center_frame, style="TelemetryGrid.TFrame")
        f_right.pack(side=tkinter.RIGHT, padx=(10, 5))

        row_count = 0

        # Fuel
        l_fuel = ttk.Label(f_right, text="Fuel", width=8,
                           anchor=tkinter.CENTER)
        l_fuel.grid(row=row_count, column=0, padx=2, pady=(2, 0))
        row_count += 1

        l_fuel_var = ttk.Label(f_right, textvariable=self.fuel_var,
                               width=8, anchor=tkinter.CENTER)
        l_fuel_var.grid(row=row_count, column=0, padx=2, pady=(0, 1))
        row_count += 1

        # Fuel per lap
        l_fuel_per_lap = ttk.Label(f_right, text="Fuel/Lap", width=8,
                                   anchor=tkinter.CENTER)
        l_fuel_per_lap.grid(row=row_count, column=0, padx=2, pady=(1, 0))
        row_count += 1

        l_fuel_per_lap_var = ttk.Label(f_right,
                                       textvariable=self.fuel_per_lap_var,
                                       width=8, anchor=tkinter.CENTER)
        l_fuel_per_lap_var.grid(row=row_count, column=0, padx=2, pady=(0, 1))
        row_count += 1

        # Lap left
        l_fuel_lap_left = ttk.Label(f_right, text="Est. laps", width=8,
                                    anchor=tkinter.CENTER)
        l_fuel_lap_left.grid(row=row_count, column=0, padx=2, pady=(1, 0))
        row_count += 1

        l_fuel_lap_left_var = ttk.Label(f_right,
                                        textvariable=self.fuel_lap_left_var,
                                        width=8, anchor=tkinter.CENTER)
        l_fuel_lap_left_var.grid(row=row_count, column=0, padx=2, pady=(0, 1))
        row_count += 1

        # Time before brake fail
        l_pad_fail = ttk.Label(f_right, text="Brake life", width=8,
                               anchor=tkinter.CENTER)
        l_pad_fail.grid(row=row_count, column=0, padx=2, pady=(1, 0))
        row_count += 1

        l_pad_fal_var = ttk.Label(f_right, textvariable=self.time_pad_failure,
                                  width=8, anchor=tkinter.CENTER)
        l_pad_fal_var.grid(row=row_count, column=0, padx=2, pady=(0, 1))

    def _build_left_frame(self, center_frame: ttk.Frame) -> None:

        f_left = ttk.Frame(center_frame, style="TelemetryGrid.TFrame")
        f_left.pack(side=tkinter.LEFT, padx=(0, 5))

        row_count = 0

        # Lap time
        l_lap_time = ttk.Label(f_left, text="Lap time", width=12,
                               anchor=tkinter.CENTER)
        l_lap_time.grid(row=row_count, column=0, padx=2, pady=(2, 0))
        row_count += 1

        l_lap_time_var = ttk.Label(f_left, textvariable=self.lap_time_var,
                                   width=12, anchor=tkinter.CENTER)
        l_lap_time_var.grid(row=row_count, column=0, padx=2, pady=(0, 1))
        row_count += 1

        # best time
        l_best_time = ttk.Label(f_left, text="Best time", width=12,
                                anchor=tkinter.CENTER)
        l_best_time.grid(row=row_count, column=0, padx=1, pady=(1, 0))
        row_count += 1

        l_best_time_var = ttk.Label(f_left, textvariable=self.best_time_var,
                                    width=12, anchor=tkinter.CENTER)
        l_best_time_var.grid(row=row_count, column=0, padx=1, pady=(0, 1))
        row_count += 1

        # Previous time
        l_prev_time = ttk.Label(f_left, text="Previous time", width=12,
                                anchor=tkinter.CENTER)
        l_prev_time.grid(row=row_count, column=0, padx=1, pady=(1, 0))
        row_count += 1

        l_prev_time_var = ttk.Label(f_left, textvariable=self.prev_time_var,
                                    width=12, anchor=tkinter.CENTER)
        l_prev_time_var.grid(row=row_count, column=0, padx=1, pady=(0, 2))

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

        self.damage_info.update_values(telemetry.damage,
                                       telemetry.suspension_damage)

        if self.current_driver != telemetry.driver:

            self.current_driver = telemetry.driver
            self.driver_swap = True

        self.air_temp.set(round(telemetry.air_temp, 1))
        self.road_temp.set(round(telemetry.road_temp, 1))
