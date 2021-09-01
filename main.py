import ipaddress
import math
import socket
import struct
import time
import tkinter
from dataclasses import astuple, dataclass
from enum import Enum, auto
from functools import partial
from multiprocessing import Pipe, Process, Queue
from multiprocessing.connection import Connection
from threading import Event, Thread
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


class PacketType(Enum):

    Connect = 1
    SmData = 2
    ServerData = 3
    Disconnect = 4
    ConnectionAccepted = 5
    Strategy = 6
    StrategyOK = 7

    def to_bytes(self) -> bytes:
        """
        Convert PacketType to bytes (unsigned char)
        """

        return struct.pack("!B", self.value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Any:
        """
        Convert the first unsigned char of a bytes object into a PacketType
        """

        return PacketType(struct.unpack("!B", data[:1])[0])



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

    def to_bytes(self) -> bytes:
        buffer = []
        buffer.append(struct.pack("!f", self.fuel))
        buffer.append(struct.pack("!i", self.tyre_set))
        buffer.append(struct.pack(
            "!3s", bytearray(self.tyre_compound, "utf-8")))
        buffer.append(struct.pack("!4f", *self.tyre_pressures))
        buffer.append(struct.pack("!i", self.next_driver))
        buffer.append(struct.pack("!i", self.brake_pad))
        buffer.append(struct.pack("!?", self.repairs_bodywork))
        buffer.append(struct.pack("!?", self.repairs_suspension))

        return b"".join(buffer)


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

    while not math.isclose(current_pressure, target_pressure, rel_tol=1e-3):

        if current_pressure > target_pressure:
            pyautogui.press("left")
            current_pressure -= 0.1

        else:
            pyautogui.press("right")
            current_pressure += 0.1

        time.sleep(0.01)


def set_fuel(mfd_fuel: float, target_fuel: float) -> None:

    while not math.isclose(mfd_fuel, target_fuel, rel_tol=1e-3):
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
                 data_queue: Queue) -> None:

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
    wet_was_selected = not math.isclose(old_fr, new_fr, rel_tol=1e-2)

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

        l_var = tkinter.Label(self, textvariable=var, width=15)
        l_var.grid(row=0, column=3)


def set_strat_proc(comm: Connection, data_queue: Queue) -> None:

    message = ""
    while message != "STOP":

        message = comm.recv()

        if message == "SET_STRATEGY":
            strategy = data_queue.get()
            sm_data = data_queue.get()

            set_strategy(strategy, sm_data, comm, data_queue)

            comm.send("STRATEGY_DONE")


class ConnectionWindow(tkinter.Toplevel):

    def __init__(self, root):
        tkinter.Toplevel.__init__(self, master=root)

        self.title("Connection window")
        self.geometry("400x400")

        self.f_connection_info = tkinter.Frame(self)
        self.f_connection_info.grid()

        self.l_ip = tkinter.Label(self.f_connection_info, text="IP: ")
        self.l_ip.grid(row=0, column=0)

        self.l_port = tkinter.Label(self.f_connection_info, text="Port: ")
        self.l_port.grid(row=1, column=0)

        self.e_ip = tkinter.Entry(self.f_connection_info)
        self.e_ip.grid(row=0, column=1)

        self.e_port = tkinter.Entry(self.f_connection_info)
        self.e_port.grid(row=1, column=1)

        self.b_connect = tkinter.Button(
            self, text="Connect", command=self.connect)
        self.b_connect.grid(row=1)

    def connect(self) -> None:

        self.b_connect.config(state="disabled")

        try:
            ipaddress.ip_address(self.e_ip.get())
            self.e_ip.config(background="White")

            if self.e_port.get().isnumeric():
                self.e_port.config(background="White")
                port = int(self.e_port.get())

                if self.master.connect_to_server(self.e_ip.get(), port):
                    self.destroy()

                else:
                    self.b_connect.config(state="active")

            else:
                self.e_port.config(background="Red")

        except ValueError:
            self.e_ip.config(background="Red")


class StrategyUI(tkinter.Frame):

    def __init__(self, root):
        tkinter.Frame.__init__(self, master=root)

        self.asm = accSharedMemory()
        self.asm.start()

        self.server_data: CarInfo = None
        self.strategy = None
        self.strategy_ok = False

        self.child_com, self.parent_com = Pipe()
        self.data_queue = Queue()
        self.strategy_proc = Process(
            target=set_strat_proc, args=(self.child_com, self.data_queue))
        self.strategy_proc.start()

        self.tyres = None
        self.mfd_fuel = 0
        self.mfd_tyre_set = 0
        self.max_static_fuel = 120

        self.tyre_compound_text = tkinter.StringVar()

        self.update_values()

        f_settings = tkinter.Frame(self)

        app_row = 0

        # Strategy Menu: Fuel Row
        self.fuel_text = tkinter.DoubleVar()
        l_fuel = tkinter.Label(f_settings, text="Fuel: ", width=20)
        l_fuel.grid(row=app_row, column=0)
        bp_fuel = ButtonPannel(f_settings, self.fuel_text,
                               self.change_fuel, [1, 5, 10])
        bp_fuel.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre set row
        self.tyre_set_text = tkinter.IntVar()
        l_tyre_set = tkinter.Label(f_settings, text="Tyre set: ", width=20)
        l_tyre_set.grid(row=app_row, column=0)
        bp_tyre_set = ButtonPannel(
            f_settings, self.tyre_set_text, self.change_tyre_set, [1])
        bp_tyre_set.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Tyre compound
        f_tyre_compound = tkinter.Frame(f_settings)

        l_tyre_set = tkinter.Label(
            f_settings, text="Tyre compound: ", width=20)
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
            f_tyre_compound, textvariable=self.tyre_compound_text, width=15)
        l_var.grid(row=0, column=3)
        f_tyre_compound.grid(row=app_row, column=1)
        app_row += 1

        tyre_steps = [0.1, 0.5, 1.0]

        # Strategy menu: Front left tyre
        self.front_left_text = tkinter.DoubleVar()
        l_tyre_fl = tkinter.Label(f_settings, text="Front left: ", width=20)
        l_tyre_fl.grid(row=app_row, column=0)
        bp_tyre_fl = ButtonPannel(
            f_settings, self.front_left_text, self.change_pressure_fl,
            tyre_steps)
        bp_tyre_fl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Front right tyre
        self.front_right_text = tkinter.DoubleVar()
        l_tyre_fr = tkinter.Label(f_settings, text="Front right: ", width=20)
        l_tyre_fr.grid(row=app_row, column=0)
        bp_tyre_fr = ButtonPannel(
            f_settings, self.front_right_text, self.change_pressure_fr,
            tyre_steps)
        bp_tyre_fr.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear left tyre
        self.rear_left_text = tkinter.DoubleVar()
        l_tyre_rl = tkinter.Label(f_settings, text="Rear left: ", width=20)
        l_tyre_rl.grid(row=app_row, column=0)
        bp_tyre_rl = ButtonPannel(
            f_settings, self.rear_left_text, self.change_pressure_rl,
            tyre_steps)
        bp_tyre_rl.grid(row=app_row, column=1)
        app_row += 1

        # Strategy menu: Rear right tyre
        self.rear_right_text = tkinter.DoubleVar()
        l_tyre_rr = tkinter.Label(f_settings, text="Rear right: ", width=20)
        l_tyre_rr.grid(row=app_row, column=0)
        bp_tyre_rr = ButtonPannel(
            f_settings, self.rear_right_text, self.change_pressure_rr,
            tyre_steps)
        bp_tyre_rr.grid(row=app_row, column=1)
        app_row += 1

        f_settings.grid(row=0)

        f_button_grid = tkinter.Frame(self)
        f_button_grid.grid(row=1)
        self.bupdate_strat = tkinter.Button(
            f_button_grid, text="Update values", width=50,
            command=self.update_values)
        self.bupdate_strat.grid(row=0, column=0)
        self.bset_strat = tkinter.Button(
            f_button_grid, text="Set Strategy", width=50,
            command=self.set_strategy)
        self.bset_strat.grid(row=0, column=1)

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

        else:
            print("data is none")
            self.fuel_text.set(0)
            self.tyre_set_text.set(0)
            self.front_left_text.set(0)
            self.rear_left_text.set(0)
            self.rear_right_text.set(0)
            self.front_right_text.set(0)
            self.tyre_compound_text.set("Dry")

    def close(self) -> None:
        self.parent_com.send("STOP")
        self.strategy_proc.join()
        self.asm.stop()

    def set_strategy(self) -> None:

        self.strategy = PitStop(
            self.mfd_fuel, self.mfd_tyre_set, self.tyre_compound_text.get(),
            self.tyres)
        self.bset_strat.config(state="disabled")

    def is_strategy_applied(self, state: bool) -> None:

        if state:
            self.bset_strat.config(state="active")

        else:
            self.bset_strat.config(state="disabled")

    def apply_strategy(self, strat) -> None:
        self.data_queue.put(strat)
        self.data_queue.put(self.asm.get_data())
        self.parent_com.send("SET_STRATEGY")

    def change_pressure_fl(self, change) -> None:

        self.tyres[0] = clamp(self.tyres[0] + change, 20.3, 35.0)
        self.front_left_text.set(f"{self.tyres[0]:.1f}")

    def change_pressure_fr(self, change) -> None:
        self.tyres[1] += change

        self.tyres[1] = clamp(self.tyres[1] + change, 20.3, 35.0)
        self.front_right_text.set(f"{self.tyres[1]:.1f}")

    def change_pressure_rl(self, change) -> None:
        self.tyres[2] += change

        self.tyres[2] = clamp(self.tyres[2] + change, 20.3, 35.0)
        self.rear_left_text.set(f"{self.tyres[2]:.1f}")

    def change_pressure_rr(self, change) -> None:
        self.tyres[3] += change

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


class app(tkinter.Tk):

    def __init__(self) -> None:

        tkinter.Tk.__init__(self)
        self.title("PyAccEngineer")
        self.geometry("1280x720")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Networking
        self.server = None
        self.client = None
        self.client_queue_out = Queue()
        self.client_queue_in = Queue()

        self.connection_window = None

        self.menu_bar = tkinter.Menu(self)
        self.menu_bar.add_command(
            label="Connect", command=self.open_connection_window)
        self.menu_bar.add_command(label="As Server", command=self.as_server)
        self.menu_bar.add_command(
            label="Disconnect", command=self.disconnect, state="disabled")
        self.config(menu=self.menu_bar)

        self.strategy_ui = StrategyUI(self)
        self.strategy_ui.grid(row=0)

        self.client_loop()

        self.mainloop()

        self.strategy_ui.close()
        self.stop_networking()

    def client_loop(self) -> None:

        if self.client_queue_out.qsize() > 0:

            event_type = self.client_queue_out.get()

            if event_type == NetworkQueue.ServerData:
                server_data = self.client_queue_out.get()
                is_first_update = self.strategy_ui.server_data is None
                self.strategy_ui.server_data = server_data
                if is_first_update:
                    self.strategy_ui.update_values()

            elif event_type == NetworkQueue.Strategy:
                strategy = self.client_queue_out.get()

                asm_data = self.strategy_ui.asm.get_data()
                if asm_data is not None:
                    compound = strategy[3].decode("utf-8")
                    pit_stop = PitStop(
                        strategy[1], strategy[2], compound, strategy[4:8],
                        strategy[8], strategy[9], strategy[10], strategy[11])
                    self.strategy_ui.apply_strategy(pit_stop)

            elif event_type == NetworkQueue.StrategyDone:
                self.strategy_ui.bset_strat.config(state="active")
                self.strategy_ui.update_values()

            elif event_type == NetworkQueue.AsmRequest:

                infos = None
                asm_data = self.strategy_ui.asm.get_data()
                if asm_data is not None:

                    mfd_pressure = asm_data.Graphics.mfd_tyre_pressure
                    mfd_fuel = asm_data.Graphics.mfd_fuel_to_add
                    max_fuel = asm_data.Static.max_fuel
                    mfd_tyre_set = asm_data.Graphics.mfd_tyre_set
                    infos = CarInfo(*astuple(mfd_pressure),
                                    mfd_fuel, max_fuel, mfd_tyre_set)

                self.client_queue_in.put(infos)

            elif event_type == NetworkQueue.IsStrategyAsked:
                strategy = None
                if self.strategy_ui.strategy is not None:
                    strategy = self.strategy_ui.strategy
                    self.strategy_ui.strategy = None
                self.client_queue_in.put(strategy)

            elif event_type == NetworkQueue.IsStrategyDone:
                self.client_queue_in.put(self.strategy_ui.strategy_ok)
                self.strategy_ui.strategy_ok = False

        self.after(100, self.client_loop)

    def open_connection_window(self) -> None:

        self.connection_window = ConnectionWindow(self)
        self.menu_bar.entryconfig("Disconnect", state="active")
        self.menu_bar.entryconfig("Connect", state="disabled")

    def connect_to_server(self, ip, port) -> bool:

        self.client = ClientInstance(
            ip, port, self.client_queue_in, self.client_queue_out)
        return self.client.connect()

    def as_server(self) -> None:

        self.menu_bar.entryconfig("Disconnect", state="active")
        self.menu_bar.entryconfig("Connect", state="disabled")
        self.menu_bar.entryconfig("As Server", state="disabled")

        self.server = ServerInstance()
        self.connect_to_server("127.0.0.1", 4269)

    def disconnect(self) -> None:

        self.stop_networking()

        self.menu_bar.entryconfig("Disconnect", state="disabled")
        self.menu_bar.entryconfig("Connect", state="active")
        self.menu_bar.entryconfig("As Server", state="active")

    def stop_networking(self) -> None:

        if self.client is not None:
            self.client.disconnect()

            # Create new empty queues
            self.client_queue_in = Queue()
            self.client_queue_out = Queue()

        if self.server is not None:
            self.server.disconnect()

        print("APP: disconnect done")

    def on_close(self) -> None:

        self.disconnect()
        self.destroy()


class NetworkQueue(Enum):

    ServerData = auto()
    Strategy = auto()
    IsStrategyDone = auto()
    StrategyDone = auto()
    AsmRequest = auto()
    IsStrategyAsked = auto()


@dataclass
class CarInfo:

    front_left_pressure: float
    front_right_pressure: float
    rear_left_pressure: float
    rear_right_pressure: float
    fuel_to_add: float
    max_fuel: float
    tyre_set: int


class ClientInstance:

    def __init__(self, ip: str, port: int, in_queue: Queue,
                 out_queue: Queue) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_ip = ip
        self._server_port = port
        self._listener_thread = None
        self._thread_event = None
        self._in_queue = in_queue
        self._out_queue = out_queue

    def connect(self) -> bool:

        try:
            self._socket.settimeout(3)
            self._socket.connect((self._server_ip, self._server_port))
            self._socket.settimeout(0.1)
            print(f"CLIENT: Connected to {self._server_ip}")

        except socket.timeout:
            print(f"CLIENT: Timeout while connecting to {self._server_ip}")
            return False

        try:
            self._socket.send(PacketType.Connect.to_bytes())

        except ConnectionResetError:
            print(f"CLIENT: Connection reset error with {self._server_ip}")
            return False

        reply = self._socket.recv(64)
        print(f"CLIENT: Got {reply =}")
        packet_type = PacketType.from_bytes(reply)
        if packet_type == PacketType.ConnectionAccepted:

            print("CLIENT: connected")
            self._thread_event = Event()

            self._listener_thread = Thread(target=self._network_listener)
            self._listener_thread.start()

            return True

        else:
            # TODO should I ?
            self._socket.shutdown(socket.SHUT_RDWR)
            return False

    def disconnect(self) -> None:

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

            if not self._thread_event.is_set():
                self._check_app_state()

        if data == b"":
            print("CLIENT: Lost connection to server.")

        print("close socket")
        self._socket.close()
        print("client_listener STOPPED")

    def _handle_data(self, data: bytes) -> None:

        packet_type = PacketType.from_bytes(data)

        if packet_type == PacketType.ServerData:
            server_data = CarInfo(*(struct.unpack("!H6fi", data[:30])[1:]))

            self._out_queue.put(NetworkQueue.ServerData)
            self._out_queue.put(copy.copy(server_data))

        elif packet_type == PacketType.Strategy:
            self._out_queue.put(NetworkQueue.Strategy)
            self._out_queue.put(struct.unpack("!Hfi3s4fii??", data[:39]))

        elif packet_type == PacketType.StrategyOK:
            self._out_queue.put(NetworkQueue.StrategyDone)

    def _check_app_state(self) -> None:

        self._out_queue.put(NetworkQueue.AsmRequest)
        car_info: CarInfo = get_or_none(self._in_queue)
        if car_info is not None:
            buffer = struct.pack(
                "!H 6f i", PacketType.SmData.value, *astuple(car_info))
            self._socket.send(buffer)

        self._out_queue.put(NetworkQueue.IsStrategyAsked)
        strategy: PitStop = get_or_none(self._in_queue)
        if strategy is not None:
            packet_type = PacketType.Strategy
            buffer = struct.pack("!H", packet_type.value) + strategy.to_bytes()
            self._socket.send(buffer)

        self._out_queue.put(NetworkQueue.IsStrategyDone)
        strategy_ok = get_or_none(self._in_queue)
        if strategy_ok:
            packet_type = PacketType.StrategyOK
            buffer = struct.pack("!H", packet_type.value)
            self._socket.send(buffer)


def get_or_none(data_queue: Queue, timeout: float = 0.5) -> Any:

    try:
        return data_queue.get(timeout=timeout)

    except queue.Empty:
        return None


@dataclass
class ClientHandle:

    thread: Thread
    rx_queue: Queue
    tx_queue: Queue


class ServerInstance:

    def __init__(self) -> None:

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(0.2)
        self._server_thread = Thread(target=self._server_listener)
        self._server_event = Event()
        self.server_queue = queue.Queue()

        self.connection = None
        self._thread_pool: List[ClientHandle] = []

        self._socket.bind(("", 4269))
        self._server_thread.start()

    def _server_listener(self) -> None:

        self._socket.listen()
        handler_event = Event()
        dead_thread_timer = time.time()
        while not self._server_event.is_set():

            if len(self._thread_pool) < 4:
                try:
                    c_socket, addr = self._socket.accept()
                    print("SERVER: Accepting new connection")

                    rx_queue = Queue()
                    tx_queue = Queue()
                    thread = Thread(target=self._client_handler, args=(
                        c_socket, addr, handler_event, rx_queue, tx_queue))

                    new_client = ClientHandle(thread, rx_queue, tx_queue)
                    new_client.thread.start()

                    self._thread_pool.append(new_client)

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

        self._socket.close()
        handler_event.set()
        print("Closing threads")
        for client_thread in self._thread_pool:
            print(f"SERVER: Joining thread (server_listener) {client_thread}")
            client_thread.thread.join()

        print("server_listener STOPPED")

    def _client_handler(self, c_socket: socket.socket, addr, event: Event,
                        rx_queue: Queue, tx_queue: Queue) -> None:

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

                if packet_type == PacketType.Connect:
                    c_socket.send(PacketType.ConnectionAccepted.to_bytes())

                elif packet_type == PacketType.Disconnect:
                    print(f"SERVER: Client {addr} disconnected")

                elif packet_type == PacketType.SmData:
                    if rx_queue.qsize() == 0:
                        rx_queue.put(data)

                elif packet_type == PacketType.Strategy:
                    rx_queue.put(data)

                elif packet_type == PacketType.StrategyOK:
                    rx_queue.put(data)

                else:
                    print(f"Socket data {addr}: {data}")

            if tx_queue.qsize() > 0:
                net_data = tx_queue.get()

                packet_type = PacketType.from_bytes(net_data)
                if packet_type == PacketType.SmData:
                    buffer = PacketType.ServerData.to_bytes() + net_data[1:]
                    c_socket.send(buffer)

                if packet_type == PacketType.Strategy:
                    c_socket.send(net_data)

                if packet_type == PacketType.StrategyOK:
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

    app()


if __name__ == "__main__":

    main()
