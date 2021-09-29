import logging
import math
import multiprocessing
import queue
import time
import tkinter
from dataclasses import astuple
from datetime import datetime
from functools import partial
from tkinter import ttk
from typing import Optional, Union

import pyautogui
import win32com
import win32com.client
import win32gui
from SharedMemory.PyAccSharedMemory import ACC_map, accSharedMemory
from modules.Telemetry import Telemetry
from modules.Common import string_time_from_ms

from modules.Common import CarInfo, PitStop

log = logging.getLogger(__name__)


def clamp(number: Union[float, int],
          min_value: Union[float, int],
          max_value: Union[float, int]) -> Union[float, int]:

    if number > max_value:
        number = max_value

    elif number < min_value:
        number = min_value

    return number


def time_str_to_ms(time: str) -> Optional[int]:

    if type(time) != str:
        return None

    try:
        minutes, second_and_ms = time.split(":")
        second, ms = second_and_ms.split(".")

        total_ms = int(minutes) * 60_000
        total_ms += int(second) * 1000
        total_ms += int(ms)

    except TypeError:
        print("type error")
        return None

    return total_ms


def ACCWindowFinderCallback(hwnd: int, obj) -> bool:
    """
    Since win32gui.FindWindow(None, 'AC2') doesn't work since kunos
    are a bunch of pepega and the title is 'AC2   '
    """

    title: str = win32gui.GetWindowText(hwnd)
    if title.find("AC2") != -1:
        obj.hwnd = hwnd

    return True


class FuelCalculator(ttk.Frame):

    def __init__(self, root):

        ttk.Frame.__init__(self, root)

        self.fuel_lp = tkinter.DoubleVar()
        self.duration = tkinter.IntVar()
        self.lap_time = tkinter.StringVar(value="00:00.000")
        self.fuel_calc = tkinter.IntVar()
        self.margin = tkinter.IntVar()
        self.override = tkinter.BooleanVar(value=False)

        self.current_lap = -1

        l_fuel_pl = ttk.Label(self, text="Fuel per lap")
        l_fuel_pl.grid(row=0, column=0)

        self.e_fuel_pl = ttk.Entry(self, state="disabled",
                                   textvariable=self.fuel_lp)
        self.e_fuel_pl.grid(row=1, column=0)

        l_lap_time = ttk.Label(self, text="lap time")
        l_lap_time.grid(row=0, column=1)

        self.e_lap_time = ttk.Entry(self, state="disabled",
                                    textvariable=self.lap_time)
        self.e_lap_time.grid(row=1, column=1)

        l_duration = ttk.Label(self, text="Duration")
        l_duration.grid(row=0, column=2)

        self.e_duration = ttk.Entry(self, state="disabled",
                                    textvariable=self.duration)
        self.e_duration.grid(row=1, column=2)

        l_fuel_need = ttk.Label(self, text="Fuel needed")
        l_fuel_need.grid(row=0, column=5)

        l_fuel_cal = ttk.Label(self, textvariable=self.fuel_calc)
        l_fuel_cal.grid(row=1, column=5)

        l_margin = ttk.Label(self, text="Spare laps")
        l_margin.grid(row=0, column=3)

        self.e_margin = ttk.Entry(self, textvariable=self.margin)
        self.e_margin.grid(row=1, column=3)

        cb_override = ttk.Checkbutton(self, text="Override",
                                      variable=self.override,
                                      command=self._override_change)
        cb_override.grid(row=2, column=0)

        self.b_compute = ttk.Button(self, text="Calculate",
                                    command=self._compute_fuel,
                                    state="disabled")
        self.b_compute.grid(row=1, column=4)

    def _compute_fuel(self) -> None:

        fuel_pl = self.fuel_lp.get()
        lap_time = self.lap_time.get()
        duration = self.duration.get()
        margin = self.margin.get()

        lap_time_ms = time_str_to_ms(lap_time)
        if lap_time_ms is None or lap_time_ms == 0:
            log.error("Invalid lap time for fuel calculation")
            return

        duration_ms = duration * 60_000
        laps = math.ceil(duration_ms / lap_time_ms) + margin
        fuel = math.ceil(laps * fuel_pl)

        self.fuel_calc.set(fuel)

    def _override_change(self) -> None:

        if self.override.get():
            state = "normal"

        else:
            state = "disabled"

        self.e_fuel_pl.config(state=state)
        self.e_lap_time.config(state=state)
        self.e_duration.config(state=state)
        self.b_compute.config(state=state)

    def update_values(self, telemetry: Telemetry) -> None:

        if telemetry.lap == self.current_lap:
            return

        if self.override.get():
            return

        self.current_lap = telemetry.lap

        self.fuel_lp.set(telemetry.fuel_per_lap)
        self.lap_time.set(string_time_from_ms(telemetry.previous_time))
        self.duration.set(telemetry.session_left / 60_000)

        self._compute_fuel()


class ButtonPannel(ttk.Frame):

    def __init__(self, root, var, callback, steps=[0.1, 0.5, 1.0]) -> None:

        ttk.Frame.__init__(self, root)

        for index, step in enumerate(steps):

            b_minus = ttk.Button(self, text=str(-step), width=5,
                                 command=partial(callback, -step))

            b_add = ttk.Button(self, text=str(step), width=5,
                               command=partial(callback, step))

            b_minus.grid(row=0, column=2 - index, padx=4, pady=2)
            b_add.grid(row=0, column=4 + index, padx=4, pady=2)

        l_var = ttk.Label(self, textvariable=var, width=10,
                          anchor=tkinter.CENTER)
        l_var.grid(row=0, column=3, padx=4, pady=2)


class StrategyUI(tkinter.Frame):

    def __init__(self, root, config: dict):

        ttk.Frame.__init__(self, master=root)

        self.asm = accSharedMemory()

        self.check_reply_id = None

        self.is_connected = False
        self.is_driver_active = False

        self.server_data: CarInfo = None
        self.strategy = None
        self.strategy_ok = False

        self.app_config = config

        self.data_queue = multiprocessing.Queue()
        self.strat_setter = StrategySetter(self.data_queue)

        self.max_static_fuel = 120

        self.driver_set = False
        self.current_driver = ""
        self.driver_list = []

        self.strategies = {}

        self.fuel_text = tkinter.DoubleVar()
        self.tyre_set_text = tkinter.IntVar(value=1)
        self.tyre_compound_text = tkinter.StringVar(value="Dry")

        self.front_left_text = tkinter.DoubleVar()
        self.front_right_text = tkinter.DoubleVar()
        self.rear_left_text = tkinter.DoubleVar()
        self.rear_right_text = tkinter.DoubleVar()

        self.driver_var = tkinter.StringVar(value="FirstName LastName")

        self.old_fuel = tkinter.DoubleVar()
        self.old_tyre_set = tkinter.IntVar(value=1)
        self.old_tyre_compound = tkinter.StringVar(value="Dry")

        self.old_front_left = tkinter.DoubleVar()
        self.old_front_right = tkinter.DoubleVar()
        self.old_rear_left = tkinter.DoubleVar()
        self.old_rear_right = tkinter.DoubleVar()

        self._build_ui()

        f_button_grid = ttk.Frame(self)
        f_button_grid.grid(row=1, pady=5)

        self.b_update_strat = ttk.Button(f_button_grid, text="Update values",
                                         command=self.update_values)

        self.b_update_strat.pack(side=tkinter.LEFT, padx=5, pady=2)

        self.b_set_strat = ttk.Button(f_button_grid, text="Set Strategy",
                                      command=self.set_strategy)

        self.b_set_strat.pack(side=tkinter.RIGHT, padx=5, pady=2)

        f_previous_strat = ttk.Frame(self)
        f_previous_strat.grid(row=0, rowspan=2, column=1, padx=5)

        l_title = ttk.Label(f_previous_strat, text="Strategy history")
        l_title.grid(row=0, column=0, columnspan=2)

        self.cb_strat = ttk.Combobox(f_previous_strat, values=[""],
                                     state="readonly")
        self.cb_strat.bind("<<ComboboxSelected>>", self._show_old_strat)
        self.cb_strat.grid(row=1, column=0, columnspan=2, padx=4, pady=2)

        # Old fuel
        l_fuel = ttk.Label(f_previous_strat, text="Fuel",
                           anchor=tkinter.E, width=10)
        l_fuel.grid(row=2, column=0, padx=4, pady=2)

        l_fuel_var = ttk.Label(f_previous_strat, width=5,
                               anchor=tkinter.CENTER,
                               textvariable=self.old_fuel)
        l_fuel_var.grid(row=2, column=1, padx=4, pady=2)

        # Old Tyre set
        l_tyre_set = ttk.Label(f_previous_strat, text="Tyre set",
                               anchor=tkinter.E, width=10)
        l_tyre_set.grid(row=3, column=0, padx=4, pady=2)

        l_tyre_set_var = ttk.Label(f_previous_strat, width=5,
                                   anchor=tkinter.CENTER,
                                   textvariable=self.old_tyre_set)
        l_tyre_set_var.grid(row=3, column=1, padx=4, pady=2)

        # Old compound
        l_compound = ttk.Label(f_previous_strat, text="Compound",
                               anchor=tkinter.E, width=10)
        l_compound.grid(row=4, column=0, padx=4, pady=2)

        l_compound_var = ttk.Label(f_previous_strat, width=5,
                                   anchor=tkinter.CENTER,
                                   textvariable=self.old_tyre_compound)
        l_compound_var.grid(row=4, column=1, padx=4, pady=2)

        # Old front left
        l_pressure_fl = ttk.Label(f_previous_strat, text="Front left",
                                  anchor=tkinter.E, width=10)
        l_pressure_fl.grid(row=5, column=0, padx=4, pady=2)

        l_pressure_fl_var = ttk.Label(f_previous_strat, width=5,
                                      anchor=tkinter.CENTER,
                                      textvariable=self.old_front_left)
        l_pressure_fl_var.grid(row=5, column=1, padx=4, pady=2)

        # Old front right
        l_pressure_fr = ttk.Label(f_previous_strat, text="Front right",
                                  anchor=tkinter.E, width=10)
        l_pressure_fr.grid(row=6, column=0, padx=4, pady=2)

        l_pressure_fr_var = ttk.Label(f_previous_strat, width=5,
                                      anchor=tkinter.CENTER,
                                      textvariable=self.old_front_right)
        l_pressure_fr_var.grid(row=6, column=1, padx=4, pady=2)

        # Old rear left
        l_pressure_rl = ttk.Label(f_previous_strat, text="Rear left",
                                  anchor=tkinter.E, width=10)
        l_pressure_rl.grid(row=7, column=0, padx=4, pady=2)

        l_pressure_rl_var = ttk.Label(f_previous_strat, width=5,
                                      anchor=tkinter.CENTER,
                                      textvariable=self.old_rear_left)
        l_pressure_rl_var.grid(row=7, column=1, padx=4, pady=2)

        # Old rear right
        l_pressure_rr = ttk.Label(f_previous_strat, text="Rear right",
                                  anchor=tkinter.E, width=10)
        l_pressure_rr.grid(row=8, column=0, padx=4, pady=2)

        l_pressure_rr_var = ttk.Label(f_previous_strat, width=5,
                                      anchor=tkinter.CENTER,
                                      textvariable=self.old_rear_right)
        l_pressure_rr_var.grid(row=8, column=1, padx=4, pady=2)

        b_copy = ttk.Button(f_previous_strat, text="Copy",
                            command=self._copy_strat)

        b_copy.grid(row=10, column=0, columnspan=2, padx=4, pady=5)

        self.f_fuel_cal = FuelCalculator(self)
        self.f_fuel_cal.grid(row=2, column=0, columnspan=2)

        self.update_values()
        self.check_reply()

    def _copy_strat(self) -> None:

        if self.cb_strat.get() == "":
            log.warning("No strategy selected")
            return

        self.fuel_text.set(self.old_fuel.get())
        self.tyre_set_text.set(self.old_tyre_set.get())
        self.tyre_compound_text.set(self.old_tyre_compound.get())
        self.front_left_text.set(f"{self.old_front_left.get():.1f}")
        self.front_right_text.set(f"{self.old_front_right.get():.1f}")
        self.rear_left_text.set(f"{self.old_rear_left.get():.1f}")
        self.rear_right_text.set(f"{self.old_rear_right.get():.1f}")

    def _show_old_strat(self, _) -> None:

        if self.cb_strat.get() == "":
            log.warning("No strategy selected")
            return

        selected_strat = self.cb_strat.get()

        if selected_strat not in self.strategies:
            log.warning(f"{selected_strat} not in strategies")
            return

        strategy: PitStop = self.strategies[selected_strat]

        self.old_fuel.set(strategy.fuel)
        self.old_tyre_set.set(strategy.tyre_set + 1)
        self.old_tyre_compound.set(strategy.tyre_compound)
        self.old_front_left.set(f"{strategy.tyre_pressures[0]:.1f}")
        self.old_front_right.set(f"{strategy.tyre_pressures[1]:.1f}")
        self.old_rear_left.set(f"{strategy.tyre_pressures[2]:.1f}")
        self.old_rear_right.set(f"{strategy.tyre_pressures[3]:.1f}")

    def _build_ui(self) -> None:

        f_settings = ttk.Frame(self)

        app_row = 0

        # Strategy Menu: Fuel Row

        l_fuel = ttk.Label(f_settings, text="Fuel", width=13,
                           anchor=tkinter.E)
        l_fuel.grid(row=app_row, column=0, padx=10)

        bp_fuel = ButtonPannel(f_settings, self.fuel_text,
                               self.change_fuel, [1, 5, 10])
        bp_fuel.grid(row=app_row, column=1)

        app_row += 1

        # Strategy menu: Tyre set
        l_tyre_set = ttk.Label(f_settings, text="Tyre set", width=13,
                               anchor=tkinter.E)
        l_tyre_set.grid(row=app_row, column=0, padx=10)

        bp_tyre_set = ButtonPannel(f_settings, self.tyre_set_text,
                                   self.change_tyre_set, [1])
        bp_tyre_set.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre compound
        f_tyre_compound = ttk.Frame(f_settings)

        l_tyre_set = ttk.Label(f_settings, text="Tyre compound", width=13,
                               anchor=tkinter.E)
        l_tyre_set.grid(row=app_row, column=0, padx=10)

        b_minus = ttk.Button(f_tyre_compound, text="Dry", width=5,
                             command=lambda: self.change_tyre_compound("Dry"))
        b_minus.grid(row=0, column=2, padx=4, pady=2)

        b_add = ttk.Button(f_tyre_compound, text="Wet", width=5,
                           command=lambda: self.change_tyre_compound("Wet"))
        b_add.grid(row=0, column=4, padx=4, pady=2)

        l_var = ttk.Label(f_tyre_compound,
                          textvariable=self.tyre_compound_text, width=10,
                          anchor=tkinter.CENTER)
        l_var.grid(row=0, column=3, padx=4, pady=2)

        f_tyre_compound.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Front left tyre
        l_tyre_fl = ttk.Label(f_settings, text="Front left", width=13,
                              anchor=tkinter.E)
        l_tyre_fl.grid(row=app_row, column=0, padx=10)
        bp_tyre_fl = ButtonPannel(f_settings, self.front_left_text,
                                  self.change_pressure_fl)
        bp_tyre_fl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Front right tyre
        l_tyre_fr = ttk.Label(f_settings, text="Front right", width=13,
                              anchor=tkinter.E)
        l_tyre_fr.grid(row=app_row, column=0, padx=10)

        bp_tyre_fr = ButtonPannel(f_settings, self.front_right_text,
                                  self.change_pressure_fr,)
        bp_tyre_fr.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear left tyre
        l_tyre_rl = ttk.Label(f_settings, text="Rear left", width=13,
                              anchor=tkinter.E)
        l_tyre_rl.grid(row=app_row, column=0, padx=10)

        bp_tyre_rl = ButtonPannel(f_settings, self.rear_left_text,
                                  self.change_pressure_rl)
        bp_tyre_rl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear right tyre
        l_tyre_rr = ttk.Label(f_settings, text="Rear right", width=13,
                              anchor=tkinter.E)
        l_tyre_rr.grid(row=app_row, column=0, padx=10)

        bp_tyre_rr = ButtonPannel(f_settings, self.rear_right_text,
                                  self.change_pressure_rr)
        bp_tyre_rr.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Driver selector
        f_drivers = ttk.Frame(f_settings)
        f_drivers.grid(row=app_row, column=1)

        l_driver = ttk.Label(f_settings, text="Driver", width=13,
                             anchor=tkinter.E)
        l_driver.grid(row=app_row, column=0, padx=10)

        b_driver_m = ttk.Button(f_drivers, text="Previous", width=10,
                                command=self._prev_driver)
        b_driver_m.grid(row=0, column=0, padx=4, pady=2)

        l_driver_var = ttk.Label(f_drivers, textvariable=self.driver_var,
                                 width=20, anchor=tkinter.CENTER)
        l_driver_var.grid(row=0, column=1, padx=4, pady=2)

        b_driver_p = ttk.Button(f_drivers, text="Next", width=10,
                                command=self._next_driver)
        b_driver_p.grid(row=0, column=2, padx=4, pady=2)

        f_settings.grid(row=0, padx=2, pady=2)

    def add_driver(self, driver: str, driverID: int) -> None:

        self.driver_list.append((driver, driverID))

    def set_driver(self, driver: str) -> None:

        self.current_driver = driver
        self.driver_set = False
        self.driver_var.set(driver)

    def reset_drivers(self) -> None:

        self.driver_list.clear()

    def _next_driver(self) -> None:

        if len(self.driver_list) < 2:
            log.warning("no more than 2 driver connected")
            return

        driver_ids = []
        current_id = None

        # find current driver id
        set_driver = self.driver_var.get()
        log.info(f"Current: {set_driver}")
        for driver in self.driver_list:

            if driver[0] == set_driver:
                current_id = driver[1]

            else:
                driver_ids.append(driver[1])

        if current_id is None:
            log.warning(f"Driver {set_driver} not in driver list")
            return

        # Find next driver in the list
        driver_ids.sort()
        next_driver_id = None
        for id in driver_ids:

            if current_id < id:
                next_driver_id = id
                break

        if next_driver_id is None:
            log.warning(f"No next driver found")
            return

        # Find name of next driver id
        for driver in self.driver_list:

            if driver[1] == next_driver_id:
                next_driver = driver[0]
                break

        self.driver_var.set(next_driver)

    def _prev_driver(self) -> None:

        if len(self.driver_list) < 2:
            log.warning("no more than 2 driver connected")
            return

        driver_ids = []
        current_id = None

        # find current driver id
        set_driver = self.driver_var.get()
        log.info(f"Current: {set_driver}")
        for driver in self.driver_list:

            if driver[0] == set_driver:
                current_id = driver[1]

            else:
                driver_ids.append(driver[1])

        if current_id is None:
            log.warning(f"Driver {set_driver} not in driver list")
            return

        # Find next driver in the list
        driver_ids.sort()
        previous_driver_id = None
        for id in driver_ids:

            if current_id > id:
                previous_driver_id = id
                break

        if previous_driver_id is None:
            log.warning(f"No previous driver found")
            return

        # Find name of next driver id
        for driver in self.driver_list:

            if driver[1] == previous_driver_id:
                previous_driver = driver[0]
                break

        self.driver_var.set(previous_driver)

    def check_reply(self) -> None:

        if self.strat_setter.is_strat_applied():
            self.strategy_ok = True

        elif self.strat_setter.data_requested():
            self.data_queue.put(self.asm.get_shared_memory_data())

        self.check_reply_id = self.after(60, self.check_reply)

    def updae_telemetry_data(self, telemetry: Telemetry) -> None:

        self.f_fuel_cal.update_values(telemetry)

    def update_values(self) -> None:

        if self.server_data is not None:

            tyres = astuple(self.server_data)[:4]
            mfd_tyre_set = self.server_data.tyre_set
            mfd_fuel = self.server_data.fuel_to_add

            self.max_static_fuel = self.server_data.max_fuel

            self.fuel_text.set(f"{mfd_fuel:.1f}")
            self.tyre_set_text.set(mfd_tyre_set + 1)
            self.front_left_text.set(f"{tyres[0]:.1f}")
            self.front_right_text.set(f"{tyres[1]:.1f}")
            self.rear_left_text.set(f"{tyres[2]:.1f}")
            self.rear_right_text.set(f"{tyres[3]:.1f}")

            if self.tyre_compound_text.get() == "":
                self.tyre_compound_text.set("Dry")

    def close(self) -> None:

        self.strat_setter.stop()
        self.asm.close()
        self.after_cancel(self.check_reply_id)

    def set_strategy(self) -> None:

        if not self.is_connected:
            log.warning("Not connected")
            return

        elif not self.is_driver_active:
            log.warning("No driver active")
            return

        selected_driver = self.driver_var.get()

        if selected_driver != self.current_driver:

            current_id = 0
            selected_id = 0
            for driver in self.driver_list:

                if driver[0] == self.current_driver:
                    current_id = driver[1]

                if driver[0] == selected_driver:
                    selected_id = driver[1]

            driver_offset = selected_id - current_id
            self.current_driver = selected_driver

        else:
            driver_offset = 0

        strat = PitStop(self.fuel_text.get(),
                        self.tyre_set_text.get() - 1,
                        self.tyre_compound_text.get(),
                        (
            self.front_left_text.get(),
            self.front_right_text.get(),
            self.rear_left_text.get(),
            self.rear_right_text.get()
        ),
            driver_offset)

        time_key = datetime.now().strftime("%H:%M.%S_%d_%m_%Y")
        self.strategies[time_key] = strat
        self.cb_strat["value"] = (*self.cb_strat["value"], time_key)

        self.strategy = strat
        self.b_set_strat.config(state="disabled")

    def is_strategy_applied(self, state: bool) -> None:

        if state:
            self.b_set_strat.config(state="active")

        else:
            self.b_set_strat.config(state="disabled")

    def apply_strategy(self, strat: PitStop) -> None:

        self.data_queue.put(strat)
        self.data_queue.put(self.asm.get_shared_memory_data())
        self.strat_setter.start()

    def change_pressure_fl(self, change) -> None:

        temp = clamp(self.front_left_text.get() + change, 20.3, 35.0)
        self.front_left_text.set(f"{temp:.1f}")

    def change_pressure_fr(self, change) -> None:

        temp = clamp(self.front_right_text.get() + change, 20.3, 35.0)
        self.front_right_text.set(f"{temp:.1f}")

    def change_pressure_rl(self, change) -> None:

        temp = clamp(self.rear_left_text.get() + change, 20.3, 35.0)
        self.rear_left_text.set(f"{temp:.1f}")

    def change_pressure_rr(self, change) -> None:

        temp = clamp(self.rear_right_text.get() + change, 20.3, 35.0)
        self.rear_right_text.set(f"{temp:.1f}")

    def change_fuel(self, change) -> None:

        temp = clamp(self.fuel_text.get() + change, 0, self.max_static_fuel)
        self.fuel_text.set(f"{temp:.1f}")

    def change_tyre_set(self, change: int) -> None:

        self.mfd_tyre_set = clamp(self.tyre_set_text.get() + change, 0, 49)
        self.tyre_set_text.set(self.mfd_tyre_set)

    def change_tyre_compound(self, compound: str) -> None:

        self.tyre_compound_text.set(compound)

    def reset(self) -> None:

        self.b_set_strat.config(state="active")
        self.b_update_strat.config(state="active")
        self.team_size = None


class StrategySetter:

    def __init__(self, data_queue: queue.Queue):

        self.child_com, self.parent_com = multiprocessing.Pipe()
        self.data_queue = data_queue
        self.hwnd = None
        self.messages = []
        self.setter = multiprocessing.Process(target=self.setter_loop)
        self.setter.start()

    def start(self) -> None:

        self.parent_com.send("SET_STRATEGY")

    def stop(self) -> None:

        self.parent_com.send("STOP")
        self.setter.join()

    def setter_loop(self) -> None:

        message = ""
        while message != "STOP":

            message = self.child_com.recv()

            if message == "SET_STRATEGY":
                strategy = self.data_queue.get()
                sm_data = self.data_queue.get()

                self.set_strategy(strategy, sm_data)

                self.child_com.send("STRATEGY_DONE")

    def _get_message(self) -> None:

        if self.parent_com.poll():
            self.messages.append(self.parent_com.recv())

    def is_strat_applied(self) -> bool:

        self._get_message()

        if "STRATEGY_DONE" in self.messages:
            self.messages.remove("STRATEGY_DONE")
            return True

        return False

    def data_requested(self) -> bool:

        self._get_message()

        if "NEW_DATA" in self.messages:
            self.messages.remove("NEW_DATA")
            return True

        return False

    def set_acc_forground(self) -> None:
        # List because I need to pass arg by reference and not value

        win32gui.EnumWindows(ACCWindowFinderCallback, self)
        if self.hwnd is not None:

            # Weird fix for SetForegroundWindow()
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')

            win32gui.SetForegroundWindow(self.hwnd)

    @staticmethod
    def set_tyre_pressure(current: float, target: float) -> None:

        # Fail safe incase of floating point weirdness
        i = 0
        max_iteration = abs((current - target) * 10) + 1

        while (not math.isclose(current, target, rel_tol=1e-5)
               and i < max_iteration):

            if current > target:
                pyautogui.press("left")
                current -= 0.1

            else:
                pyautogui.press("right")
                current += 0.1

            time.sleep(0.01)
            i += 1

    @staticmethod
    def set_fuel(current: float, target: float) -> None:

        while not math.isclose(current, target, rel_tol=1e-5):
            if current > target:
                pyautogui.press("left")
                current -= 1

            else:
                pyautogui.press("right")
                current += 1

            time.sleep(0.01)

    @staticmethod
    def set_tyre_set(current: int, target: int) -> None:

        while current != target:

            if current > target:
                pyautogui.press("left")
                current -= 1

            else:
                pyautogui.press("right")
                current += 1

            time.sleep(0.01)

    def set_strategy(self, strategy: PitStop, sm: ACC_map) -> None:

        log.info(f"Requested strategy: {strategy}")

        self.set_acc_forground()

        time.sleep(1)

        # Reset MFD cursor to top
        pyautogui.press("p")

        for _ in range(2):
            pyautogui.press("down")
            time.sleep(0.01)

        StrategySetter.set_fuel(sm.Graphics.mfd_fuel_to_add, strategy.fuel)

        # check if tyre set is on wet, tyre set will be disable
        # so going down 5 times will be FR instead of FL
        # --------- start ---------------------
        for _ in range(5):
            pyautogui.press("down")
            time.sleep(0.01)

        old_fr = sm.Graphics.mfd_tyre_pressure.front_right
        pyautogui.press("left")

        time.sleep(0.1)
        self.child_com.send("NEW_DATA")
        sm = self.data_queue.get()

        new_fr = sm.Graphics.mfd_tyre_pressure.front_right
        wet_was_selected = not math.isclose(old_fr, new_fr, rel_tol=1e-5)

        pyautogui.press("right")
        time.sleep(0.01)

        # Goind back to fuel selection
        for _ in range(5):
            pyautogui.press("up")
            time.sleep(0.01)

        # ---------end of wanky trick----------------------

        if wet_was_selected:
            step_for_compound = 2
        else:
            step_for_compound = 3

        for _ in range(step_for_compound):
            pyautogui.press("down")
            time.sleep(0.01)

        StrategySetter.set_tyre_compound(strategy.tyre_compound)

        # pressure data might be invalide (pressing left when on
        # dry compound set pressure as currently used)
        time.sleep(0.1)
        self.child_com.send("NEW_DATA")
        sm = self.data_queue.get()

        if strategy.tyre_compound == "Dry":
            pyautogui.press("up")
            time.sleep(0.01)

            mfd_tyre_set = sm.Graphics.mfd_tyre_set
            self.set_tyre_set(mfd_tyre_set, strategy.tyre_set)
            down = 3

        else:
            down = 2

        for _ in range(down):
            pyautogui.press("down")
            time.sleep(0.01)

        mfd_pressures = astuple(sm.Graphics.mfd_tyre_pressure)
        for tyre_index, tyre_pressure in enumerate(mfd_pressures):

            self.set_tyre_pressure(tyre_pressure,
                                   strategy.tyre_pressures[tyre_index])
            pyautogui.press("down")
            time.sleep(0.01)

        pyautogui.press("down")
        time.sleep(0.01)

        for _ in range(abs(strategy.driver_offset)):

            if strategy.driver_offset < 0:
                pyautogui.press("left")

            else:
                pyautogui.press("right")

            time.sleep(0.01)

    @staticmethod
    def set_tyre_compound(compound: str):

        if compound == "Dry":
            pyautogui.press("left")

        elif compound == "Wet":
            pyautogui.press("right")

        time.sleep(0.01)
