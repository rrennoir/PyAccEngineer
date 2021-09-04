from __future__ import annotations

import ipaddress
import math
import multiprocessing
import queue
import socket
import struct
import threading
import time
import tkinter
from dataclasses import astuple, dataclass
from enum import Enum, auto
from functools import partial
from multiprocessing.connection import Connection
from tkinter import messagebox
from typing import ClassVar, Tuple, Union

import pyautogui
import win32com.client
import win32gui

from SharedMemory.PyAccSharedMemory import *


def clamp(number: Union[float, int],
          min_value: Union[float, int],
          max_value: Union[float, int]) -> Union[float, int]:

    if number > max_value:
        number = max_value

    elif number < min_value:
        number = min_value

    return number


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


def ACCWindowFinderCallback(hwnd: int, obj: list) -> bool:
    """
    Since win32gui.FindWindow(None, 'AC2') doesn't work since kunos
    are a bunch of pepega and the title is 'AC2   '
    """

    title: str = win32gui.GetWindowText(hwnd)
    if title.find("AC2") != -1:
        obj.append(hwnd)

    return True


def set_acc_forground() -> None:
    # List because I need to pass arg by reference and not value
    hwnd = []
    win32gui.EnumWindows(ACCWindowFinderCallback, hwnd)
    if len(hwnd) != 0:
        # Weird fix for SetForegroundWindow()
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        # ----------------------------
        win32gui.SetForegroundWindow(hwnd[0])


def set_tyre_pressure(current_pressure: float, target_pressure: float) -> None:

    while not math.isclose(current_pressure, target_pressure, rel_tol=1e-5):

        if current_pressure > target_pressure:
            pyautogui.press("left")
            current_pressure -= 0.1

        else:
            pyautogui.press("right")
            current_pressure += 0.1

        time.sleep(0.01)


def set_fuel(mfd_fuel: float, target_fuel: float) -> None:

    while not math.isclose(mfd_fuel, target_fuel, rel_tol=1e-5):
        if mfd_fuel > target_fuel:
            pyautogui.press("left")
            mfd_fuel -= 1

        else:
            pyautogui.press("right")
            mfd_fuel += 1

        time.sleep(0.01)


def set_tyre_set(mfd_tyre_set: int, target_tyre_set: int) -> None:

    while mfd_tyre_set != target_tyre_set:

        if mfd_tyre_set > target_tyre_set:
            pyautogui.press("left")
            mfd_tyre_set -= 1

        else:
            pyautogui.press("right")
            mfd_tyre_set += 1

        time.sleep(0.01)


def set_strategy(strategy: PitStop, sm: ACC_map, comm: Connection,
                 data_queue: queue.Queue) -> None:

    set_acc_forground()

    time.sleep(1)

    # Reset MFD cursor to top
    pyautogui.press("p")

    for _ in range(2):
        pyautogui.press("down")
        time.sleep(0.01)

    set_fuel(sm.Graphics.mfd_fuel_to_add, strategy.fuel)

    # check if tyre set is on wet, tyre set will be disable
    # so going down 5 times will be FR instead of FL
    # --------- start ---------------------
    for _ in range(5):
        pyautogui.press("down")
        time.sleep(0.01)

    old_fr = sm.Graphics.mfd_tyre_pressure.front_right
    pyautogui.press("left")

    time.sleep(0.1)
    comm.send("NEW_DATA")
    sm = data_queue.get()

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

    set_tyre_compound(strategy.tyre_compound)

    # pressure data might be invalide (pressing left when on
    # dry compound set pressure as currently used)
    time.sleep(0.1)
    comm.send("NEW_DATA")
    sm = data_queue.get()

    if strategy.tyre_compound == "Dry":
        pyautogui.press("up")
        time.sleep(0.01)

        mfd_tyre_set = sm.Graphics.mfd_tyre_set
        set_tyre_set(mfd_tyre_set, strategy.tyre_set)
        down = 3

    else:
        down = 2

    for _ in range(down):
        pyautogui.press("down")
        time.sleep(0.01)

    mfd_pressures = astuple(sm.Graphics.mfd_tyre_pressure)
    for tyre_index, tyre_pressure in enumerate(mfd_pressures):

        set_tyre_pressure(tyre_pressure, strategy.tyre_pressures[tyre_index])
        pyautogui.press("down")
        time.sleep(0.01)


def set_tyre_compound(compound: str):
    if compound == "Dry":
        pyautogui.press("left")

    elif compound == "Wet":
        pyautogui.press("right")

    time.sleep(0.01)


class ButtonPannel(tkinter.Frame):

    def __init__(self, root, var, command, step=[0.1, 0.5, 1.0]) -> None:

        tkinter.Frame.__init__(self, root)

        for index, element in enumerate(step):
            b_minus = tkinter.Button(
                self, text=str(-element), width=5,
                command=partial(command, -element))
            b_add = tkinter.Button(self, text=str(
                element), width=5, command=partial(command, element))
            b_minus.grid(row=0, column=2 - index, padx=2, pady=1)
            b_add.grid(row=0, column=4 + index, padx=2, pady=1)

        l_var = tkinter.Label(self, textvariable=var, width=10)
        l_var.grid(row=0, column=3)


def set_strat_proc(comm: Connection, data_queue: queue.Queue) -> None:

    message = ""
    while message != "STOP":

        message = comm.recv()

        if message == "SET_STRATEGY":
            strategy = data_queue.get()
            sm_data = data_queue.get()

            set_strategy(strategy, sm_data, comm, data_queue)

            comm.send("STRATEGY_DONE")


class ConnectionWindow(tkinter.Toplevel):

    def __init__(self, root: App, as_server: bool = False):
        tkinter.Toplevel.__init__(self, master=root)

        self.title("Connection window")
        self.main_app = root

        # Block other window
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.as_server = as_server

        self.f_connection_info = tkinter.Frame(
            self, bd=2, relief=tkinter.RIDGE)
        self.f_connection_info.grid()

        self.l_ip = tkinter.Label(self.f_connection_info, text="IP:",
                                  anchor=tkinter.E, width=10)
        self.l_ip.grid(row=0, column=0, padx=5, pady=2)

        self.l_username = tkinter.Label(self.f_connection_info,
                                        text="Username:",
                                        anchor=tkinter.E, width=10)
        self.l_username.grid(row=2, column=0, padx=5, pady=2)

        self.l_port = tkinter.Label(self.f_connection_info, text="Port:",
                                    anchor=tkinter.E, width=10)
        self.l_port.grid(row=1, column=0, padx=5, pady=2)

        self.e_ip = tkinter.Entry(self.f_connection_info, width=30)
        self.e_ip.grid(row=0, column=1, padx=5, pady=2)

        self.e_port = tkinter.Entry(self.f_connection_info, width=30)
        self.e_port.insert(tkinter.END, "4269")
        self.e_port.grid(row=1, column=1, padx=5, pady=2)

        self.e_username = tkinter.Entry(self.f_connection_info, width=30)
        self.e_username.insert(tkinter.END, "xXx_cringe_xXx")
        self.e_username.grid(row=2, column=1, padx=5, pady=2)

        self.b_connect = tkinter.Button(
            self, text="Connect", command=self.connect)
        self.b_connect.grid(row=1, padx=10, pady=5)

        if self.as_server:
            self.e_ip.insert(tkinter.END, "127.0.0.1")
            self.e_ip.config(state="disabled")
            self.e_port.config(state="disabled")

    def connect(self) -> None:

        self.b_connect.config(state="disabled")

        error_message = ""

        try:
            ipaddress.ip_address(self.e_ip.get())
            self.e_ip.config(background="White")

        except ValueError:
            self.e_ip.config(background="Red")
            error_message += "Invalide IP address\n"

        if self.e_port.get().isnumeric():
            self.e_port.config(background="White")

        else:
            self.e_port.config(background="Red")
            error_message += "Invalide port\n"

        if self.e_username.get() != "":
            self.e_username.config(background="White")

        else:
            self.e_username.config(background="Red")
            error_message += "Invalide username\n"

        if error_message == "":
            username = self.e_username.get()
            if self.as_server:
                self.main_app.as_server(username)
                self.destroy()
            else:
                ip = self.e_ip.get()
                port = int(self.e_port.get())
                connected, msg = self.main_app.connect_to_server(ip, port,
                                                                 username)

                if connected:
                    self.on_close()

                else:
                    messagebox.showerror("Error", msg)
                    self.b_connect.config(state="active")

        else:
            messagebox.showerror("Error", error_message)
            self.b_connect.config(state="active")

    def on_close(self) -> None:

        self.grab_release()
        self.destroy()


class UserUI(tkinter.Frame):

    def __init__(self, root):

        tkinter.Frame.__init__(self, master=root)
        self.user_list = []

        f_background = tkinter.Frame(self, background="Black")
        row_count = 0

        l_user = tkinter.Label(f_background, text="Users:", width=20)
        l_user.grid(row=row_count, column=0, padx=1, pady=1)
        row_count += 1

        self.user1 = tkinter.StringVar()
        l_user1_var = tkinter.Label(
            f_background, textvariable=self.user1, width=20)
        l_user1_var.grid(row=row_count, column=0, padx=1, pady=1)
        row_count += 1

        self.user2 = tkinter.StringVar()
        l_user2_var = tkinter.Label(
            f_background, textvariable=self.user2, width=20)
        l_user2_var.grid(row=row_count, column=0, padx=1, pady=1)
        row_count += 1

        self.user3 = tkinter.StringVar()
        l_user3_var = tkinter.Label(
            f_background, textvariable=self.user3, width=20)
        l_user3_var.grid(row=row_count, column=0, padx=1, pady=1)
        row_count += 1

        self.user4 = tkinter.StringVar()
        l_user4_var = tkinter.Label(
            f_background, textvariable=self.user4, width=20)
        l_user4_var.grid(row=row_count, column=0, padx=1, pady=1)

        f_background.pack()

    def add_user(self, name: str) -> None:

        if len(self.user_list) < 4 and name not in self.user_list:
            self.user_list.append(name)

            if self.user1.get() == "":
                self.user1.set(name)

            elif self.user2.get() == "":
                self.user2.set(name)

            elif self.user3.get() == "":
                self.user3.set(name)

            elif self.user4.get() == "":
                self.user4.set(name)

            else:
                print("UserUI: names full ?")
        else:
            print("UserUI: More than 4 users ?")

    def reset(self) -> None:

        self.user_list.clear()
        self.user1.set("")
        self.user2.set("")
        self.user3.set("")
        self.user4.set("")


class TyreInfo(tkinter.Frame):

    def __init__(self, root, name: str, on_the_right: bool = True):

        tkinter.Frame.__init__(self, master=root)

        self.tyre_pressure = tkinter.DoubleVar()
        self.tyre_temp = tkinter.DoubleVar()
        self.brake_temp = tkinter.DoubleVar()
        self.pad_wear = tkinter.DoubleVar()
        self.disc_wear = tkinter.DoubleVar()

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
        self.tyre = tkinter.Frame(self, background="Green")
        self.tyre.grid(row=row_count, rowspan=6, column=tyre_column)
        t = tkinter.Label(self.tyre, width=10)
        t.grid()

        l_tyre = tkinter.Label(
            self, text=name, width=label_width, anchor=txt_anchor)
        l_tyre.grid(row=row_count, column=label_column)
        row_count += 1

        l_tyre_pressure = tkinter.Label(self, text="Tyre pressure",
                                        width=label_width, anchor=txt_anchor)
        l_tyre_pressure_var = tkinter.Label(self,
                                            textvariable=self.tyre_pressure,
                                            width=var_width)
        l_tyre_pressure.grid(row=row_count, column=label_column)
        l_tyre_pressure_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_tyre_temp = tkinter.Label(self, text="Tyre temperature",
                                    width=label_width, anchor=txt_anchor)
        l_tyre_temp_var = tkinter.Label(self,
                                        textvariable=self.tyre_temp,
                                        width=var_width)
        l_tyre_temp.grid(row=row_count, column=label_column)
        l_tyre_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_brake_temp = tkinter.Label(self, text="Brake temperature",
                                     width=label_width, anchor=txt_anchor)
        l_brake_temp_var = tkinter.Label(self,
                                         textvariable=self.brake_temp,
                                         width=var_width)
        l_brake_temp.grid(row=row_count, column=label_column)
        l_brake_temp_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_pad_wear = tkinter.Label(self, text="Pad wear",
                                   width=label_width, anchor=txt_anchor)
        l_pad_wear_var = tkinter.Label(self,
                                       textvariable=self.pad_wear,
                                       width=var_width)
        l_pad_wear.grid(row=row_count, column=label_column)
        l_pad_wear_var.grid(row=row_count, column=var_column)
        row_count += 1

        l_disc_wear = tkinter.Label(self, text="Disc wear",
                                    width=label_width, anchor=txt_anchor)
        l_disc_wear_var = tkinter.Label(self,
                                        textvariable=self.disc_wear,
                                        width=var_width)
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

    def reset_value(self) -> None:

        self.tyre_pressure.set(0)
        self.tyre_temp.set(0)
        self.brake_temp.set(0)
        self.pad_wear.set(0)
        self.disc_wear.set(0)


@dataclass
class Telemetry:

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

        buffer = [
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

        raw_data = struct.unpack("!21f 3i", data)

        return Telemetry(
            raw_data[0],
            Wheels(*raw_data[1:5]),
            Wheels(*raw_data[5:9]),
            Wheels(*raw_data[9:13]),
            Wheels(*raw_data[13:17]),
            Wheels(*raw_data[17:21]),
            raw_data[21],
            raw_data[22],
            raw_data[23],
        )


class TelemetryUI(tkinter.Frame):

    def __init__(self, root):

        tkinter.Frame.__init__(self, master=root)

        self.telemetry: Optional[Telemetry] = None

        f_info = tkinter.Frame(self)
        f_info.grid(row=0, column=0)

        # Fuel
        self.fuel_var = tkinter.DoubleVar()
        l_fuel = tkinter.Label(f_info, text="Fuel: ")
        l_fuel_var = tkinter.Label(
            f_info, textvariable=self.fuel_var)
        l_fuel.pack(side=tkinter.LEFT)
        l_fuel_var.pack(side=tkinter.LEFT)

        # Lap time
        self.lap_time_var = tkinter.StringVar(value="00:00.000")
        l_lap_time = tkinter.Label(f_info, text="Lap time: ")
        l_lap_time_var = tkinter.Label(
            f_info, textvariable=self.lap_time_var)
        l_lap_time.pack(side=tkinter.LEFT)
        l_lap_time_var.pack(side=tkinter.LEFT)

        # best time
        self.best_time_var = tkinter.StringVar(value="00:00.000")
        l_best_time = tkinter.Label(f_info, text="Best time: ")
        l_best_time_var = tkinter.Label(
            f_info, textvariable=self.lap_time_var)
        l_best_time.pack(side=tkinter.LEFT)
        l_best_time_var.pack(side=tkinter.LEFT)

        # Previous time
        self.prev_time_var = tkinter.StringVar(value="00:00.000")
        l_prev_time = tkinter.Label(f_info, text="Previous time: ",)
        l_prev_time_var = tkinter.Label(
            f_info, textvariable=self.prev_time_var)
        l_prev_time.pack(side=tkinter.LEFT)
        l_prev_time_var.pack(side=tkinter.LEFT)

        tyre_frame = tkinter.Frame(self)
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


class StrategyUI(tkinter.Frame):

    def __init__(self, root):

        tkinter.Frame.__init__(self, master=root)

        self.asm = accSharedMemory()
        self.asm.start()

        self.server_data: CarInfo = None
        self.strategy = None
        self.strategy_ok = False

        self.child_com, self.parent_com = multiprocessing.Pipe()
        self.data_queue = multiprocessing.Queue()
        self.strategy_proc = multiprocessing.Process(
            target=set_strat_proc, args=(self.child_com, self.data_queue))
        self.strategy_proc.start()

        self.tyres = None
        self.mfd_fuel = 0
        self.mfd_tyre_set = 0
        self.max_static_fuel = 120

        f_settings = tkinter.Frame(self, bd=2, relief=tkinter.RIDGE)

        app_row = 0

        # Strategy Menu: Fuel Row
        self.fuel_text = tkinter.DoubleVar()
        l_fuel = tkinter.Label(f_settings, text="Fuel: ", width=15)
        l_fuel.grid(row=app_row, column=0)
        bp_fuel = ButtonPannel(f_settings, self.fuel_text,
                               self.change_fuel, [1, 5, 10])
        bp_fuel.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre set row
        self.tyre_set_text = tkinter.IntVar()
        l_tyre_set = tkinter.Label(f_settings, text="Tyre set: ", width=15)
        l_tyre_set.grid(row=app_row, column=0)
        bp_tyre_set = ButtonPannel(
            f_settings, self.tyre_set_text, self.change_tyre_set, [1])
        bp_tyre_set.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre compound
        f_tyre_compound = tkinter.Frame(f_settings)

        self.tyre_compound_text = tkinter.StringVar(value="Dry")
        l_tyre_set = tkinter.Label(
            f_settings, text="Tyre compound: ", width=15)
        l_tyre_set.grid(row=app_row, column=0)

        b_minus = tkinter.Button(
            f_tyre_compound, text="Dry", width=5, command=partial(
                self.change_tyre_compound, "Dry"))

        b_add = tkinter.Button(
            f_tyre_compound, text="Wet", width=5, command=partial(
                self.change_tyre_compound, "Wet"))

        b_minus.grid(row=0, column=2, padx=2, pady=1)
        b_add.grid(row=0, column=4, padx=2, pady=1)

        l_var = tkinter.Label(
            f_tyre_compound, textvariable=self.tyre_compound_text, width=10)
        l_var.grid(row=0, column=3)
        f_tyre_compound.grid(row=app_row, column=1)
        app_row += 1

        tyre_steps = [0.1, 0.5, 1.0]

        # Strategy menu: Front left tyre
        self.front_left_text = tkinter.DoubleVar()
        l_tyre_fl = tkinter.Label(f_settings, text="Front left: ", width=15)
        l_tyre_fl.grid(row=app_row, column=0)
        bp_tyre_fl = ButtonPannel(
            f_settings, self.front_left_text, self.change_pressure_fl,
            tyre_steps)
        bp_tyre_fl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Front right tyre
        self.front_right_text = tkinter.DoubleVar()
        l_tyre_fr = tkinter.Label(f_settings, text="Front right: ", width=15)
        l_tyre_fr.grid(row=app_row, column=0)
        bp_tyre_fr = ButtonPannel(
            f_settings, self.front_right_text, self.change_pressure_fr,
            tyre_steps)
        bp_tyre_fr.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear left tyre
        self.rear_left_text = tkinter.DoubleVar()
        l_tyre_rl = tkinter.Label(f_settings, text="Rear left: ", width=15)
        l_tyre_rl.grid(row=app_row, column=0)
        bp_tyre_rl = ButtonPannel(
            f_settings, self.rear_left_text, self.change_pressure_rl,
            tyre_steps)
        bp_tyre_rl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear right tyre
        self.rear_right_text = tkinter.DoubleVar()
        l_tyre_rr = tkinter.Label(f_settings, text="Rear right: ", width=15)
        l_tyre_rr.grid(row=app_row, column=0)
        bp_tyre_rr = ButtonPannel(
            f_settings, self.rear_right_text, self.change_pressure_rr,
            tyre_steps)
        bp_tyre_rr.grid(row=app_row, column=1)
        app_row += 1

        f_settings.grid(row=0, padx=2, pady=2)

        f_button_grid = tkinter.Frame(self, relief=tkinter.RIDGE, bd=2)
        f_button_grid.grid(row=1, pady=5)

        self.b_update_strat = tkinter.Button(
            f_button_grid, text="Update values",
            command=self.update_values)
        self.b_update_strat.pack(side=tkinter.LEFT, padx=83, pady=2)
        self.b_set_strat = tkinter.Button(
            f_button_grid, text="Set Strategy",
            command=self.set_strategy)
        self.b_set_strat.pack(side=tkinter.RIGHT, padx=83, pady=2)

        self.update_values()
        self.check_reply()

    def check_reply(self) -> None:

        if self.parent_com.poll():
            message = self.parent_com.recv()
            if message == "STRATEGY_DONE":
                self.strategy_ok = True

            elif message == "NEW_DATA":
                self.data_queue.put(self.asm.get_data())

        self.after(60, self.check_reply)

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

        self.parent_com.send("STOP")
        self.strategy_proc.join()
        self.asm.stop()

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
        self.parent_com.send("SET_STRATEGY")

    def change_pressure_fl(self, change) -> None:

        self.tyres[0] = clamp(self.tyres[0] + change, 20.3, 35.0)
        self.front_left_text.set(f"{self.tyres[0]:.1f}")

    def change_pressure_fr(self, change) -> None:

        self.tyres[1] = clamp(self.tyres[1] + change, 20.3, 35.0)
        self.front_right_text.set(f"{self.tyres[1]:.1f}")

    def change_pressure_rl(self, change) -> None:

        self.tyres[2] = clamp(self.tyres[2] + change, 20.3, 35.0)
        self.rear_left_text.set(f"{self.tyres[2]:.1f}")

    def change_pressure_rr(self, change) -> None:

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


class App(tkinter.Tk):

    def __init__(self) -> None:

        tkinter.Tk.__init__(self)
        self.title("PyAccEngineer")
        self.config(bg="Grey")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Networking
        self.server = None
        self.client = None
        self.client_queue_out = queue.Queue()
        self.client_queue_in = queue.Queue()

        self.connection_window = None

        self.menu_bar = tkinter.Menu(self)
        self.menu_bar.add_command(
            label="Connect", command=self.open_connection_window)
        self.menu_bar.add_command(
            label="As Server", command=partial(self.open_connection_window,
                                               True))
        self.menu_bar.add_command(
            label="Disconnect", command=self.disconnect, state="disabled")
        self.config(menu=self.menu_bar)

        self.strategy_ui = StrategyUI(self)
        self.strategy_ui.grid(row=0, column=0, padx=5, pady=5)

        self.telemetry_ui = TelemetryUI(self)
        self.telemetry_ui.grid(row=1, column=0)

        self.user_ui = UserUI(self)
        self.user_ui.grid(row=0, column=1)

        self.last_time = time.time()
        self.min_delta = 0.5

        self.client_loop()

        self.mainloop()

        self.strategy_ui.close()

    def client_loop(self) -> None:

        delta_time = time.time() - self.last_time

        if self.client is not None and self.client_queue_out.qsize() > 0:

            event_type = self.client_queue_out.get()

            if event_type == NetworkQueue.ServerData:

                server_data = CarInfo.from_bytes(self.client_queue_out.get())
                is_first_update = self.strategy_ui.server_data is None
                self.strategy_ui.server_data = server_data
                if is_first_update:

                    self.strategy_ui.update_values()

            elif event_type == NetworkQueue.Strategy:

                strategy = self.client_queue_out.get()
                asm_data = self.strategy_ui.asm.get_data()
                if asm_data is not None:

                    pit_stop = PitStop.from_bytes(strategy)
                    self.strategy_ui.apply_strategy(pit_stop)

            elif event_type == NetworkQueue.StrategyDone:

                self.strategy_ui.b_set_strat.config(state="active")
                self.strategy_ui.update_values()

            elif event_type == NetworkQueue.Telemetry:

                telemetry_bytes = self.client_queue_out.get()
                telemetry = Telemetry.from_bytes(telemetry_bytes)
                self.telemetry_ui.telemetry = telemetry
                self.telemetry_ui.update_values()

            elif event_type == NetworkQueue.UpdateUsers:

                user_update = self.client_queue_out.get()
                nb_users = user_update[0]
                self.user_ui.reset()

                index = 1
                for _ in range(nb_users):

                    name_lenght = user_update[index]
                    index += 1
                    name = struct.unpack(
                        f"!{name_lenght}s",
                        user_update[index:index+name_lenght])[0].decode(
                            "utf-8")
                    index += name_lenght
                    self.user_ui.add_user(name)

        asm_data = self.strategy_ui.asm.get_data()
        if (asm_data is not None and self.client is not None
                and delta_time > self.min_delta):

            self.last_time = time.time()

            mfd_pressure = asm_data.Graphics.mfd_tyre_pressure
            mfd_fuel = asm_data.Graphics.mfd_fuel_to_add
            max_fuel = asm_data.Static.max_fuel
            mfd_tyre_set = asm_data.Graphics.mfd_tyre_set
            infos = CarInfo(*astuple(mfd_pressure),
                            mfd_fuel, max_fuel,
                            mfd_tyre_set)

            self.client_queue_in.put(NetworkQueue.CarInfoData)
            self.client_queue_in.put(infos.to_bytes())

            # Telemetry
            telemetry_data = Telemetry(
                asm_data.Physics.fuel,
                asm_data.Physics.wheel_pressure,
                asm_data.Physics.tyre_core_temp,
                asm_data.Physics.brake_temp,
                asm_data.Physics.pad_life,
                asm_data.Physics.disc_life,
                asm_data.Graphics.current_time,
                asm_data.Graphics.best_time,
                asm_data.Graphics.last_time
            )
            self.client_queue_in.put(NetworkQueue.Telemetry)
            self.client_queue_in.put(telemetry_data.to_bytes())

        if self.strategy_ui.strategy is not None:

            strategy = self.strategy_ui.strategy
            self.strategy_ui.strategy = None
            self.client_queue_in.put(NetworkQueue.StrategySet)
            self.client_queue_in.put(strategy.to_bytes())

        if self.strategy_ui.strategy_ok:

            self.client_queue_in.put(NetworkQueue.StrategyDone)
            self.strategy_ui.strategy_ok = False

        self.after(10, self.client_loop)

    def open_connection_window(self, as_server: bool = False) -> None:

        self.connection_window = ConnectionWindow(self, as_server)

    def connect_to_server(self, ip, port: int,
                          username: str) -> Tuple(bool, str):

        self.client = ClientInstance(
            ip, port, username, self.client_queue_in, self.client_queue_out)

        succes, msg = self.client.connect()
        if succes:
            self.connected(True)

        else:
            self.client = None

        return (succes, msg)

    def as_server(self, name: str) -> None:

        self.server = ServerInstance()
        self.connect_to_server("127.0.0.1", 4269, name)
        self.connected(True)

    def connected(self, state: bool) -> None:

        if state:
            self.menu_bar.entryconfig("Disconnect", state="active")
            self.menu_bar.entryconfig("Connect", state="disabled")
            self.menu_bar.entryconfig("As Server", state="disabled")

        else:
            self.menu_bar.entryconfig("Disconnect", state="disabled")
            self.menu_bar.entryconfig("Connect", state="active")
            self.menu_bar.entryconfig("As Server", state="active")

    def disconnect(self) -> None:

        self.stop_networking()
        self.connected(False)

        self.strategy_ui.reset()
        self.user_ui.reset()

    def stop_networking(self) -> None:

        if self.client is not None:
            self.client.disconnect()

            # Create new empty queues
            self.client_queue_in = queue.Queue()
            self.client_queue_out = queue.Queue()
            self.client = None
            print("APP: Client stopped.")

        if self.server is not None:
            self.server.disconnect()
            self.server = None
            print("APP: Server stopped.")

    def on_close(self) -> None:

        self.disconnect()
        self.destroy()


class ClientInstance:

    def __init__(self, ip: str, port: int, username: str,
                 in_queue: queue.Queue, out_queue: queue.Queue) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_ip = ip
        self._server_port = port
        self._username = username
        self._listener_thread = None
        self._thread_event = None
        self._in_queue = in_queue
        self._out_queue = out_queue

    def connect(self) -> Tuple(bool, str):

        try:
            self._socket.settimeout(3)
            self._socket.connect((self._server_ip, self._server_port))
            self._socket.settimeout(0.1)
            print(f"CLIENT: Connected to {self._server_ip}")

        except socket.timeout as msg:
            print(f"CLIENT: Timeout while connecting to {self._server_ip}")
            return (False, msg)

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        try:
            name_lenght = len(self._username)
            name_byte = struct.pack(f"!B {name_lenght}s", name_lenght,
                                    self._username.encode("utf-8"))
            self._socket.send(PacketType.Connect.to_bytes() + name_byte)

        except ConnectionResetError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        except ConnectionRefusedError as msg:
            print(f"CLIENT: {msg}")
            return (False, msg)

        reply = self._socket.recv(64)
        packet_type = PacketType.from_bytes(reply)
        if packet_type == PacketType.ConnectionReply:

            succes = struct.unpack("!?", reply[1:])[0]

            if succes:
                self._thread_event = threading.Event()

                self._listener_thread = threading.Thread(
                    target=self._network_listener)
                self._listener_thread.start()

                return (True, "Connected")

            else:
                return (False, "Connection rejected")

        else:
            # TODO should I ?
            self._socket.shutdown(socket.SHUT_RDWR)
            return (False, "Connection refused")

    def disconnect(self) -> None:

        if self._thread_event is not None:
            self._thread_event.set()
            self._listener_thread.join()

    def _network_listener(self) -> None:

        data = None
        print("CLIENT: Listening for server packets")
        while not (self._thread_event.is_set() or data == b""):

            try:
                data = self._socket.recv(1024)

            except socket.timeout:
                data = None

            except ConnectionResetError:
                data = b""

            if data is not None and len(data) > 0:
                self._handle_data(data)

            self._check_app_state()

        if data == b"":
            print("CLIENT: Lost connection to server.")

        print("close socket")
        self._socket.close()
        print("client_listener STOPPED")

    def _handle_data(self, data: bytes) -> None:

        packet_type = PacketType.from_bytes(data)

        if packet_type == PacketType.ServerData:

            self._out_queue.put(NetworkQueue.ServerData)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.Strategy:

            self._out_queue.put(NetworkQueue.Strategy)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.StrategyOK:

            self._out_queue.put(NetworkQueue.StrategyDone)

        elif packet_type == PacketType.Telemetry:

            self._out_queue.put(NetworkQueue.Telemetry)
            self._out_queue.put(data[1:])

        elif packet_type == PacketType.UpdateUsers:

            self._out_queue.put(NetworkQueue.UpdateUsers)
            self._out_queue.put(data[1:])

    def _check_app_state(self) -> None:

        while self._in_queue.qsize() != 0:

            item_type = self._in_queue.get()

            if item_type == NetworkQueue.CarInfoData:

                info: bytes = self._in_queue.get()
                self._socket.send(PacketType.SmData.to_bytes() + info)

            elif item_type == NetworkQueue.StrategySet:

                strategy: bytes = self._in_queue.get()
                buffer = PacketType.Strategy.to_bytes() + strategy
                self._socket.send(buffer)

            elif item_type == NetworkQueue.StrategyDone:
                self._socket.send(PacketType.StrategyOK.to_bytes())

            elif item_type == NetworkQueue.Telemetry:

                telemetry = self._in_queue.get()
                self._socket.send(PacketType.Telemetry.to_bytes() + telemetry)


@dataclass
class ClientHandle:

    thread: threading.Thread
    rx_queue: queue.Queue
    tx_queue: queue.Queue
    addr: str
    username: str = ""


class ServerInstance:

    def __init__(self) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(0.05)
        self._server_thread = threading.Thread(target=self._server_listener)
        self._server_event = threading.Event()
        self.server_queue = queue.Queue()

        self.connection = None
        self._thread_pool: List[ClientHandle] = []
        self._users = []

        self._socket.bind(("", 4269))
        self._server_thread.start()

    def _server_listener(self) -> None:

        self._socket.listen()
        handler_event = threading.Event()
        dead_thread_timer = time.time()
        while not self._server_event.is_set():

            if len(self._thread_pool) < 4:
                try:
                    c_socket, addr = self._socket.accept()
                    print("SERVER: Accepting new connection")
                    self._new_connection(c_socket, addr, handler_event)

                except socket.timeout:
                    pass

                for client_thread in self._thread_pool:

                    if client_thread.rx_queue.qsize() > 0:

                        data = client_thread.rx_queue.get()
                        for thread in self._thread_pool:
                            thread.tx_queue.put(data)

            if time.time() - dead_thread_timer > 5:
                dead_thread_timer = time.time()
                for client_thread in reversed(self._thread_pool):
                    if not client_thread.thread.is_alive():
                        print("SERVER: Removing thread of client thread pool")
                        self._thread_pool.remove(client_thread)

                        for user in reversed(self._users):
                            if client_thread.username == user[0]:
                                self._users.remove(user)

                        self._update_user_connected()

        self._socket.close()
        handler_event.set()
        print("Closing threads")
        for client_thread in self._thread_pool:
            print(f"SERVER: Joining thread (server_listener) {client_thread}")
            client_thread.thread.join()
            self._thread_pool.remove(client_thread)

        print("server_listener STOPPED")

    def _new_connection(self, c_socket: socket.socket, addr,
                        event: threading.Event) -> None:

        try:
            data = c_socket.recv(1024)

        except socket.timeout:
            data = None

        except ConnectionResetError:
            data = b""

        packet_type = PacketType.from_bytes(data)
        if packet_type == PacketType.Connect:

            lenght = data[1]
            name = struct.unpack(f"!{lenght}s", data[2:])[0].decode("utf-8")

            packet_type = PacketType.ConnectionReply.to_bytes()
            if name not in [user[0] for user in self._users]:

                succes = struct.pack("!?", True)
                c_socket.send(packet_type + succes)

                rx_queue = queue.Queue()
                tx_queue = queue.Queue()
                thread = threading.Thread(target=self._client_handler,
                                          args=(c_socket, addr, event,
                                                rx_queue, tx_queue))

                new_client = ClientHandle(thread, rx_queue,
                                          tx_queue, addr, name)
                new_client.thread.start()

                self._users.append((name, addr))
                self._thread_pool.append(new_client)

                self._update_user_connected()

            else:
                succes = struct.pack("!?", False)
                c_socket.send(packet_type + succes)

    def _update_user_connected(self) -> None:

        if len(self._thread_pool) == 0:
            return

        buffer = []
        buffer.append(PacketType.UpdateUsers.to_bytes())
        buffer.append(struct.pack("!B", len(self._users)))

        for user in self._users:

            lenght = struct.pack("!B", len(user[0]))
            name = user[0].encode("utf-8")
            buffer.append(lenght + name)

        self._thread_pool[0].rx_queue.put(b"".join(buffer))

    def _client_handler(self, c_socket: socket.socket, addr,
                        event: threading.Event, rx_queue: queue.Queue,
                        tx_queue: queue.Queue) -> None:

        c_socket.settimeout(0.2)
        print(f"SERVER: Connected to {addr}")

        data = None
        while not (event.is_set() or data == b""):

            try:
                data = c_socket.recv(1024)

            except socket.timeout:
                data = None

            except ConnectionResetError:
                data = b""

            if data is not None and len(data) > 0:

                packet_type = PacketType.from_bytes(data)

                if packet_type == PacketType.Disconnect:
                    print(f"SERVER: Client {addr} disconnected")

                elif packet_type == PacketType.SmData:
                    if rx_queue.qsize() == 0:
                        rx_queue.put(data)

                elif packet_type == PacketType.Strategy:
                    rx_queue.put(data)

                elif packet_type == PacketType.StrategyOK:
                    rx_queue.put(data)

                elif packet_type == PacketType.Telemetry:
                    rx_queue.put(data)

                else:
                    print(f"Socket data {addr}: {data}")

            if tx_queue.qsize() > 0:
                net_data = tx_queue.get()

                packet_type = PacketType.from_bytes(net_data)
                if packet_type == PacketType.SmData:
                    buffer = PacketType.ServerData.to_bytes() + net_data[1:]
                    c_socket.send(buffer)

                elif packet_type == PacketType.Strategy:
                    c_socket.send(net_data)

                elif packet_type == PacketType.StrategyOK:
                    c_socket.send(net_data)

                elif packet_type == PacketType.Telemetry:
                    c_socket.send(net_data)

                elif packet_type == PacketType.UpdateUsers:
                    c_socket.send(net_data)

        if data == b"":
            print(f"SERVER: Lost connection with client {addr}")

        c_socket.close()
        print("SERVER: client_handler STOPPED")

    def disconnect(self) -> None:

        print("server disconnect")
        self._server_event.set()
        self._server_thread.join()


def main():

    App()


if __name__ == "__main__":

    main()
