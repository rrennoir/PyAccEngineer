from SharedMemory.PyAccSharedMemory import *
import time
import math
import pyautogui
import pygame as pg


def set_tyre_pressure(current_pressure: float, target_pressure: float):

    while not math.isclose(current_pressure, target_pressure, rel_tol=1e-3):

        if current_pressure > target_pressure:
            pyautogui.press("left")
            current_pressure -= 0.1

        else:
            pyautogui.press("right")
            current_pressure += 0.1

        time.sleep(0.1)


def set_pressures(fl: float, fr: float, rl: float, rr: float, sm: ACC_map):

    # Reset MFD cursor to top
    pyautogui.press("p")

    for _ in range(7):
        pyautogui.press("down")
        time.sleep(0.1)

    print(sm.Graphics.mdf_tyre_pressure)

    pressure_fl = sm.Graphics.mdf_tyre_pressure.front_left
    set_tyre_pressure(pressure_fl, fl)
    pyautogui.press("down")
    time.sleep(0.1)
    
    pressure_fl = sm.Graphics.mdf_tyre_pressure.front_right
    set_tyre_pressure(pressure_fl, fr)
    pyautogui.press("down")
    time.sleep(0.1)
    
    pressure_fl = sm.Graphics.mdf_tyre_pressure.rear_left
    set_tyre_pressure(pressure_fl, rl)
    pyautogui.press("down")
    time.sleep(0.1)
    
    pressure_fl = sm.Graphics.mdf_tyre_pressure.rear_right
    set_tyre_pressure(pressure_fl, rr)
    pyautogui.press("down")
    time.sleep(0.1)


def set_fuel(fuel: int):

    # Reset MFD cursor to top
    pyautogui.press("p")

    for _ in range(2):
        pyautogui.press("down")
        time.sleep(0.1)
    
    for _ in range(fuel):
        pyautogui.press("right")
        time.sleep(0.1)


def main():

    asm = accSharedMemory()

    asm.start()

    sm = None
    while sm is None:
        sm = asm.get_data()

    asm.stop()


    time.sleep(3)
    print("starting")

    print("setting up fuel")
    set_fuel(10)

    print("setting up pressure")
    set_pressures(27.5, 27.5, 27.5, 27.5, sm)
    print("finish")


if __name__ == "__main__":
    main()