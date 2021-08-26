from multiprocessing import Pipe, Process, Queue
from multiprocessing.connection import Connection
from dataclasses import dataclass, astuple

from SharedMemory.PyAccSharedMemory import *
import time
import math
import pyautogui
import tkinter
from typing import Optional, Tuple
from functools import partial

import win32gui
import win32com.client


def ACCWindowFinderCallback(hwnd: int, obj) -> bool:
    """Since win32gui.FindWindow(None, 'AC2') doesn't work since kunos are a bunch of pepega and the title is 'AC2   '... """
    
    title = win32gui.GetWindowText(hwnd)
    if title.find("AC2") != -1:
        obj.append(hwnd)

    return True

@dataclass
class PitStop:

    fuel: float
    tyre_set: Optional[int]
    tyre_compound: str
    tyre_pressures: Optional[Tuple[float]]
    next_driver: int = 0
    brake_pad: int = 1
    repairs_bodywork: bool = True
    repairs_suspension: bool = True


def set_acc_forground() -> None:
    hwnd = []
    win32gui.EnumWindows(ACCWindowFinderCallback, hwnd)
    if len(hwnd) != 0:
        # Weird fix for SetForegroundWindow()
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        # ----------------------------
        win32gui.SetForegroundWindow(hwnd[0])


def set_tyre_pressure(current_pressure: float, target_pressure: float)-> None:

    while not math.isclose(current_pressure, target_pressure, rel_tol=1e-3):

        if current_pressure > target_pressure:
            pyautogui.press("left")
            current_pressure -= 0.1

        else:
            pyautogui.press("right")
            current_pressure += 0.1

        time.sleep(0.01)


def set_fuel(mfd_fuel: float, target_fuel: float)-> None:

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


def set_strategy(strategy: PitStop, sm: ACC_map, comm: Connection, data_queue: Queue) -> None:

    set_acc_forground()

    time.sleep(1)

    # Reset MFD cursor to top
    pyautogui.press("p")

    for _ in range(2):
        pyautogui.press("down")
        time.sleep(0.01)

    mfd_fuel = sm.Graphics.mfd_fuel_to_add
    set_fuel(mfd_fuel, strategy.fuel)

    # check if tyre set is on wet, tyre set will be disable
    # so going down 5 times will be FR instead of FL
    # --------- start ---------------------
    for _ in range(5):
        pyautogui.press("down")
        time.sleep(0.01)

    old_fr = sm.Graphics.mfd_tyre_pressure.front_right
    pyautogui.press("left")

    comm.send("NEW_DATA")
    sm = data_queue.get() 

    wet_was_selected = False
    if old_fr != sm.Graphics.mfd_tyre_pressure.front_right:
        wet_was_selected = True
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

    # pressure data might be invalide (pressing left when on dry compound set pressure as currently used)
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
    print(mfd_pressures)

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
            b_minus = tkinter.Button(self, text=str(-element), width=5, command=partial(command, -element))
            b_add = tkinter.Button(self, text=str(element), width=5, command=partial(command, element))
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

        self.b_connect = tkinter.Button(self, text="Connect", command=self.connect)
        self.b_connect.grid(row=1)


    def connect(self) -> None:

        print(f"{self.e_ip.get() = }")
        print(f"{self.e_port.get() = }")

        # TODO really connect to something


class StrategyUI(tkinter.Frame):

    def __init__(self, root):
        tkinter.Frame.__init__(self, master=root)

        self.asm = accSharedMemory()
        self.asm.start()

        self.sm_data = self.asm.get_data()
        while self.sm_data is None:
            self.sm_data = self.asm.get_data()

        self.child_com, self.parent_com = Pipe()
        self.data_queue = Queue()
        self.strategy_proc = Process(target=set_strat_proc, args=(self.child_com, self.data_queue))
        self.strategy_proc.start()

        self.tyres = None
        self.mfd_fuel = 0
        self.mfd_tyre_set = 0

        self.fuel_text = tkinter.DoubleVar()
        self.tyre_set_text = tkinter.IntVar()
        self.front_left_text = tkinter.DoubleVar()
        self.front_right_text = tkinter.DoubleVar()
        self.rear_left_text = tkinter.DoubleVar()
        self.rear_right_text = tkinter.DoubleVar()
        self.tyre_compound_text = tkinter.StringVar()

        self.update_values()
    
        f_settings = tkinter.Frame(self)

        app_row = 0
        l_fuel = tkinter.Label(f_settings, text="Fuel: ", width=20)
        l_fuel.grid(row=app_row, column=0)
        bp_fuel = ButtonPannel(f_settings, self.fuel_text, self.change_fuel, [1, 5, 10])
        bp_fuel.grid(row=app_row, column=1)
        app_row += 1

        l_tyre_set = tkinter.Label(f_settings, text="Tyre set: ", width=20)
        l_tyre_set.grid(row=app_row, column=0)
        bp_tyre_set = ButtonPannel(f_settings, self.tyre_set_text, self.change_tyre_set, [1])
        bp_tyre_set.grid(row=app_row, column=1)
        app_row += 1

        l_tyre_set = tkinter.Label(f_settings, text="Tyre compound: ", width=20)
        l_tyre_set.grid(row=app_row, column=0)

        f_tyre_compound = tkinter.Frame(f_settings)
        b_minus = tkinter.Button(f_tyre_compound, text="Dry", width=5, command=partial(self.change_tyre_compound, "Dry"))
        b_add = tkinter.Button(f_tyre_compound, text="Wet", width=5, command=partial(self.change_tyre_compound, "Wet"))
        b_minus.grid(row=0, column=2, padx=2, pady=1)
        b_add.grid(row=0, column=4, padx=2, pady=1)

        l_var = tkinter.Label(f_tyre_compound, textvariable=self.tyre_compound_text, width=15)
        l_var.grid(row=0, column=3)
        f_tyre_compound.grid(row=app_row, column=1)
        app_row += 1

        l_tyre_fl = tkinter.Label(f_settings, text="Front left: ", width=20)
        l_tyre_fl.grid(row=app_row, column=0)
        bp_tyre_fl = ButtonPannel(f_settings, self.front_left_text, self.change_pressure_fl, [0.1, 0.5, 1.0])
        bp_tyre_fl.grid(row=app_row, column=1)
        app_row += 1

        l_tyre_fr = tkinter.Label(f_settings, text="Front right: ", width=20)
        l_tyre_fr.grid(row=app_row, column=0)
        bp_tyre_fr = ButtonPannel(f_settings, self.front_right_text, self.change_pressure_fr, [0.1, 0.5, 1.0])
        bp_tyre_fr.grid(row=app_row, column=1)
        app_row += 1
        
        l_tyre_rl = tkinter.Label(f_settings, text="Rear left: ", width=20)
        l_tyre_rl.grid(row=app_row, column=0)
        bp_tyre_rl = ButtonPannel(f_settings, self.rear_left_text, self.change_pressure_rl, [0.1, 0.5, 1.0])
        bp_tyre_rl.grid(row=app_row, column=1)
        app_row += 1
    
        l_tyre_rr = tkinter.Label(f_settings, text="Rear right: ", width=20)
        l_tyre_rr.grid(row=app_row, column=0)
        bp_tyre_rr = ButtonPannel(f_settings, self.rear_right_text, self.change_pressure_rr, [0.1, 0.5, 1.0])
        bp_tyre_rr.grid(row=app_row, column=1)
        app_row += 1

        f_settings.grid(row=0)

        self.bset_strat = tkinter.Button(self, text="Set Strategy", width=100, command=self.set_strategy)
        self.bset_strat.grid(row=1)

        self.check_reply()


    def check_reply(self) -> None:

        if self.parent_com.poll():
            message = self.parent_com.recv()
            if message == "STRATEGY_DONE":
                self.bset_strat.config(state="active")
                self.update_values()

            elif message == "NEW_DATA":
                self.data_queue.put(self.asm.get_data())


        self.after(60, self.check_reply)

    def update_values(self) -> None:
        self.sm_data = self.asm.get_data()

        self.tyres = self.sm_data.Graphics.mfd_tyre_pressure
        self.mfd_fuel = self.sm_data.Graphics.mfd_fuel_to_add
        self.mfd_tyre_set = self.sm_data.Graphics.mfd_tyre_set

        self.fuel_text.set(f"{self.mfd_fuel:.1f}")
        self.tyre_set_text.set(self.mfd_tyre_set + 1)
        self.front_left_text.set(f"{self.tyres.front_left:.1f}")
        self.rear_left_text.set(f"{self.tyres.rear_left:.1f}")
        self.rear_right_text.set(f"{self.tyres.rear_right:.1f}")
        self.front_right_text.set(f"{self.tyres.front_right:.1f}")

        if self.tyre_compound_text.get() == "":
            self.tyre_compound_text.set("Dry")

    def close(self) -> None:
        self.parent_com.send("STOP")
        self.strategy_proc.join()
        self.asm.stop()

    def set_strategy(self) -> None:

        strat = PitStop(self.mfd_fuel, self.mfd_tyre_set, self.tyre_compound_text.get(), astuple(self.tyres))
        self.data_queue.put(strat)
        self.data_queue.put(self.asm.get_data())
        self.parent_com.send("SET_STRATEGY")
        self.bset_strat.config(state="disabled")

    def change_pressure_fl(self, change) -> None:

        self.tyres.front_left += change

        if self.tyres.front_left > 35.0:
            self.tyres.front_left = 35.0

        elif self.tyres.front_left < 20.3:
            self.tyres.front_left = 20.3
    
        self.front_left_text.set(f"{self.tyres.front_left:.1f}")

    def change_pressure_fr(self, change) -> None:
        self.tyres.front_right += change

        if self.tyres.front_right > 35.0:
            self.tyres.front_right = 35.0

        elif self.tyres.front_right < 20.3:
            self.tyres.front_right = 20.3
    
        self.front_right_text.set(f"{self.tyres.front_right:.1f}")
    
    def change_pressure_rl(self, change) -> None:
        self.tyres.rear_left += change

        if self.tyres.rear_left > 35.0:
            self.tyres.rear_left = 35.0

        elif self.tyres.rear_left < 20.3:
            self.tyres.rear_left = 20.3
        
        self.rear_left_text.set(f"{self.tyres.rear_left:.1f}")
    
    def change_pressure_rr(self, change) -> None:
        self.tyres.rear_right += change

        if self.tyres.rear_right > 35.0:
            self.tyres.rear_right = 35.0

        elif self.tyres.rear_right < 20.3:
            self.tyres.rear_right = 20.3

        self.rear_right_text.set(f"{self.tyres.rear_right:.1f}")

    def change_fuel(self, change) -> None:

        self.mfd_fuel += change
        if self.mfd_fuel < 0:
            self.mfd_fuel = 0

        elif self.mfd_fuel > self.sm_data.Static.max_fuel:
            self.mfd_fuel = self.sm_data.Static.max_fuel

        self.fuel_text.set(f"{self.mfd_fuel:.1f}")
    
    def change_tyre_set(self, change: int) -> None:

        self.mfd_tyre_set += change
        if self.mfd_tyre_set < 0:
            self.mfd_tyre_set = 0

        elif self.mfd_tyre_set > 49:
            self.mfd_tyre_set = 49

        self.tyre_set_text.set(self.mfd_tyre_set + 1)

    def change_tyre_compound(self, compound: str) -> None:
        self.tyre_compound_text.set(compound)

class app(tkinter.Tk):

    def __init__(self) -> None:

        tkinter.Tk.__init__(self)
        self.title("PyAccEngineer")

        self.connection_window = None

        self.menu_bar = tkinter.Menu(self)
        self.menu_bar.add_command(label="Connect", command=self.open_connection_window)
        self.menu_bar.add_command(label="As Server", command=self.as_server)
        self.menu_bar.add_command(label="Disconnect", command=self.disconnect, state="disabled")
        self.config(menu=self.menu_bar)

        self.strategy_ui = StrategyUI(self)
        self.strategy_ui.grid(row=0)

        self.mainloop()
        self.strategy_ui.close()        
        
    def open_connection_window(self) -> None:
        self.connection_window = ConnectionWindow(self)
        self.menu_bar.entryconfig("Disconnect", state="active")
        self.menu_bar.entryconfig("Connect", state="disabled")
    
    def as_server(self) -> None:
        # TODO
        pass

    def disconnect(self) -> None:
        # TODO do disconnect stuff
        self.menu_bar.entryconfig("Disconnect", state="disabled")
        self.menu_bar.entryconfig("Connect", state="active")


def main():
    app()


if __name__ == "__main__":
    main()
