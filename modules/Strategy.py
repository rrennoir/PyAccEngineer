import math
import multiprocessing
import queue
import time
import tkinter
from dataclasses import astuple
from functools import partial
from typing import Union

import pyautogui
import win32com
import win32com.client
import win32gui

from modules.Common import CarInfo, PitStop
from SharedMemory.PyAccSharedMemory import ACC_map, accSharedMemory


def clamp(number: Union[float, int],
          min_value: Union[float, int],
          max_value: Union[float, int]) -> Union[float, int]:

    if number > max_value:
        number = max_value

    elif number < min_value:
        number = min_value

    return number


def ACCWindowFinderCallback(hwnd: int, obj) -> bool:
    """
    Since win32gui.FindWindow(None, 'AC2') doesn't work since kunos
    are a bunch of pepega and the title is 'AC2   '
    """

    title: str = win32gui.GetWindowText(hwnd)
    if title.find("AC2") != -1:
        obj.hwnd = hwnd

    return True


class ButtonPannel(tkinter.Frame):

    def __init__(self, root, var, command, step=[0.1, 0.5, 1.0],
                 font=("Helvetica", 13)) -> None:

        tkinter.Frame.__init__(self, root, background="Black")

        for index, element in enumerate(step):
            b_minus = tkinter.Button(
                self, text=str(-element), width=5,
                command=partial(command, -element),
                bg="Black", fg="White", font=font, bd=5)

            b_add = tkinter.Button(
                self, text=str(element), width=5,
                command=partial(command, element),
                bg="Black", fg="White", font=font, bd=5)

            b_minus.grid(row=0, column=2 - index, padx=4, pady=2)
            b_add.grid(row=0, column=4 + index, padx=4, pady=2)

        l_var = tkinter.Label(self, textvariable=var, width=10,
                              bg="Black", fg="White", font=font)
        l_var.grid(row=0, column=3)


class StrategyUI(tkinter.Frame):

    def __init__(self, root, font):

        tkinter.Frame.__init__(self, master=root, background="Black")

        self.asm = accSharedMemory(refresh=60)
        self.asm.start()

        self.check_reply_id = None

        self.server_data: CarInfo = None
        self.strategy = None
        self.strategy_ok = False

        self.font = font
        self.big_font = (font[0], font[1] + 5)

        self.data_queue = multiprocessing.Queue()
        self.strat_setter = StrategySetter(self.data_queue)

        self.tyres = None
        self.mfd_fuel = 0
        self.mfd_tyre_set = 0
        self.max_static_fuel = 120

        f_settings = tkinter.Frame(self, bd=2, relief=tkinter.RIDGE,
                                   padx=10, pady=10, bg="Black")

        app_row = 0

        # Strategy Menu: Fuel Row
        self.fuel_text = tkinter.DoubleVar()
        l_fuel = tkinter.Label(f_settings, text="Fuel: ", width=15,
                               bg="Black", fg="White", font=self.font)
        l_fuel.grid(row=app_row, column=0)
        bp_fuel = ButtonPannel(f_settings, self.fuel_text,
                               self.change_fuel, [1, 5, 10])
        bp_fuel.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre set row
        self.tyre_set_text = tkinter.IntVar(value=1)
        l_tyre_set = tkinter.Label(f_settings, text="Tyre set: ",
                                   width=15, bg="Black", fg="White",
                                   font=self.font)
        l_tyre_set.grid(row=app_row, column=0)
        bp_tyre_set = ButtonPannel(
            f_settings, self.tyre_set_text, self.change_tyre_set, [1])
        bp_tyre_set.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre compound
        f_tyre_compound = tkinter.Frame(f_settings, bg="Black")

        self.tyre_compound_text = tkinter.StringVar(value="Dry")
        l_tyre_set = tkinter.Label(f_settings, text="Tyre compound: ",
                                   width=15, bg="Black", fg="White",
                                   font=self.font)
        l_tyre_set.grid(row=app_row, column=0)

        b_minus = tkinter.Button(f_tyre_compound, text="Dry", width=5,
                                 command=partial(
                                     self.change_tyre_compound, "Dry"),
                                 bg="Black", fg="White", font=self.font, bd=5)

        b_add = tkinter.Button(f_tyre_compound, text="Wet",
                               width=5, command=partial(
                                   self.change_tyre_compound, "Wet"),
                               bg="Black", fg="White", font=self.font, bd=5)

        b_minus.grid(row=0, column=2, padx=4, pady=2)
        b_add.grid(row=0, column=4, padx=4, pady=2)

        l_var = tkinter.Label(f_tyre_compound,
                              textvariable=self.tyre_compound_text,
                              width=10, bg="Black", fg="White", font=self.font)
        l_var.grid(row=0, column=3)
        f_tyre_compound.grid(row=app_row, column=1)
        app_row += 1

        tyre_steps = [0.1, 0.5, 1.0]

        # Strategy menu: Front left tyre
        self.front_left_text = tkinter.DoubleVar()
        l_tyre_fl = tkinter.Label(f_settings, text="Front left: ",
                                  width=15, bg="Black", fg="White",
                                  font=self.font)
        l_tyre_fl.grid(row=app_row, column=0)
        bp_tyre_fl = ButtonPannel(
            f_settings, self.front_left_text, self.change_pressure_fl,
            tyre_steps)
        bp_tyre_fl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Front right tyre
        self.front_right_text = tkinter.DoubleVar()
        l_tyre_fr = tkinter.Label(f_settings, text="Front right: ",
                                  width=15, bg="Black", fg="White",
                                  font=self.font)
        l_tyre_fr.grid(row=app_row, column=0)
        bp_tyre_fr = ButtonPannel(
            f_settings, self.front_right_text, self.change_pressure_fr,
            tyre_steps)
        bp_tyre_fr.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear left tyre
        self.rear_left_text = tkinter.DoubleVar()
        l_tyre_rl = tkinter.Label(f_settings, text="Rear left: ",
                                  width=15, bg="Black", fg="White",
                                  font=self.font)
        l_tyre_rl.grid(row=app_row, column=0)
        bp_tyre_rl = ButtonPannel(
            f_settings, self.rear_left_text, self.change_pressure_rl,
            tyre_steps)
        bp_tyre_rl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear right tyre
        self.rear_right_text = tkinter.DoubleVar()
        l_tyre_rr = tkinter.Label(f_settings, text="Rear right: ",
                                  width=15, bg="Black", fg="White",
                                  font=self.font)
        l_tyre_rr.grid(row=app_row, column=0)
        bp_tyre_rr = ButtonPannel(f_settings, self.rear_right_text,
                                  self.change_pressure_rr, tyre_steps)
        bp_tyre_rr.grid(row=app_row, column=1)
        app_row += 1

        f_settings.grid(row=0, padx=2, pady=2)

        f_button_grid = tkinter.Frame(
            self, relief=tkinter.RIDGE, bg="Black")
        f_button_grid.grid(row=1, pady=5)

        self.b_update_strat = tkinter.Button(
            f_button_grid, text="Update values",
            command=self.update_values, bg="Black",
            fg="White", font=self.big_font)

        self.b_update_strat.pack(side=tkinter.LEFT, padx=5, pady=2)

        self.b_set_strat = tkinter.Button(
            f_button_grid, text="Set Strategy",
            command=self.set_strategy, bg="Black",
            fg="White", font=self.big_font)

        self.b_set_strat.pack(side=tkinter.RIGHT, padx=5, pady=2)

        self.update_values()
        self.check_reply()

    def check_reply(self) -> None:

        if self.strat_setter.is_strat_applied():
            self.strategy_ok = True

        elif self.strat_setter.data_requested():
            self.data_queue.put(self.asm.get_data())

        self.check_reply_id = self.after(60, self.check_reply)

    def update_values(self) -> None:

        if self.server_data is not None:

            self.tyres = list(astuple(self.server_data)[:4])
            self.mfd_fuel = self.server_data.fuel_to_add
            self.mfd_tyre_set = self.server_data.tyre_set
            self.max_static_fuel = self.server_data.max_fuel

            self.fuel_text.set(f"{self.mfd_fuel:.1f}")
            self.tyre_set_text.set(self.mfd_tyre_set + 1)
            self.front_left_text.set(f"{self.tyres[0]:.1f}")
            self.front_right_text.set(f"{self.tyres[1]:.1f}")
            self.rear_left_text.set(f"{self.tyres[2]:.1f}")
            self.rear_right_text.set(f"{self.tyres[3]:.1f}")

            if self.tyre_compound_text.get() == "":
                self.tyre_compound_text.set("Dry")

    def close(self) -> None:

        self.strat_setter.stop()
        self.asm.stop()
        self.after_cancel(self.check_reply_id)

    def set_strategy(self) -> None:

        self.strategy = PitStop(
            self.mfd_fuel, self.mfd_tyre_set, self.tyre_compound_text.get(),
            self.tyres)
        self.b_set_strat.config(state="disabled")

    def is_strategy_applied(self, state: bool) -> None:

        if state:
            self.b_set_strat.config(state="active")

        else:
            self.b_set_strat.config(state="disabled")

    def apply_strategy(self, strat: PitStop) -> None:

        self.data_queue.put(strat)
        self.data_queue.put(self.asm.get_data())
        self.strat_setter.start()

    def change_pressure_fl(self, change) -> None:

        if self.tyres is None:
            return

        self.tyres[0] = clamp(self.tyres[0] + change, 20.3, 35.0)
        self.front_left_text.set(f"{self.tyres[0]:.1f}")

    def change_pressure_fr(self, change) -> None:

        if self.tyres is None:
            return

        self.tyres[1] = clamp(self.tyres[1] + change, 20.3, 35.0)
        self.front_right_text.set(f"{self.tyres[1]:.1f}")

    def change_pressure_rl(self, change) -> None:

        if self.tyres is None:
            return

        self.tyres[2] = clamp(self.tyres[2] + change, 20.3, 35.0)
        self.rear_left_text.set(f"{self.tyres[2]:.1f}")

    def change_pressure_rr(self, change) -> None:

        if self.tyres is None:
            return

        self.tyres[3] = clamp(self.tyres[3] + change, 20.3, 35.0)
        self.rear_right_text.set(f"{self.tyres[3]:.1f}")

    def change_fuel(self, change) -> None:

        self.mfd_fuel = clamp(self.mfd_fuel + change, 0, self.max_static_fuel)
        self.fuel_text.set(f"{self.mfd_fuel:.1f}")

    def change_tyre_set(self, change: int) -> None:

        self.mfd_tyre_set = clamp(self.mfd_tyre_set + change, 0, 49)
        self.tyre_set_text.set(self.mfd_tyre_set + 1)

    def change_tyre_compound(self, compound: str) -> None:

        self.tyre_compound_text.set(compound)

    def reset(self) -> None:

        self.b_set_strat.config(state="active")
        self.b_update_strat.config(state="active")


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

        print(f"Requested strategy: {strategy}")

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

    @staticmethod
    def set_tyre_compound(compound: str):

        if compound == "Dry":
            pyautogui.press("left")

        elif compound == "Wet":
            pyautogui.press("right")

        time.sleep(0.01)
