
from __future__ import annotations

import logging
import time
import tkinter
from tkinter import ttk

import matplotlib
import matplotlib.animation as animation
from matplotlib import pyplot, style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from modules.Telemetry import TelemetryRT

matplotlib.use("TkAgg")

style.use("dark_background")

log = logging.getLogger(__name__)


class InputGraph(ttk.Frame):

    def __init__(self, root) -> None:

        ttk.Frame.__init__(self, master=root)

        self.time_axis = []
        self.gas_data = []
        self.brake_data = []

        self.figure = pyplot.figure(figsize=(6.5, 4.5), dpi=100)
        self.figure.subplots_adjust(left=0.125,
                                    bottom=0.1,
                                    right=0.9,
                                    top=0.9,
                                    wspace=0.2,
                                    hspace=0.7)

        self.gas_graph = self.figure.add_subplot(2, 1, 1)
        self.brake_graph = self.figure.add_subplot(2, 1, 2)

        self.last_time = 0

        self.gas_line,  = self.gas_graph.plot(
            self.time_axis, self.gas_data,
            "#00FF00",
            label="Gas")

        self.brake_line,  = self.brake_graph.plot(
            self.time_axis, self.brake_data,
            "#FF0000",
            label="Brake")

        self.gas_graph.set_title("Throttle input over time")
        self.gas_graph.set_xlabel("Time (Seconds)")
        self.gas_graph.set_ylabel("Throttle (%)")
        self.gas_graph.set_xlim(0, 1)
        self.gas_graph.set_ylim(0, 100)

        self.brake_graph.set_title("Brake input over time")
        self.brake_graph.set_xlabel("Time (Seconds)")
        self.brake_graph.set_ylabel("Brake (%)")
        self.brake_graph.set_xlim(0, 1)
        self.brake_graph.set_ylim(0, 100)

        canvas = FigureCanvasTkAgg(self.figure, self)
        canvas.get_tk_widget().pack(side=tkinter.BOTTOM)
        self.ani = animation.FuncAnimation(self.figure, self._animate,
                                           interval=500, blit=False)

        self.ani.event_source.stop()

    def _animate(self, i) -> None:

        if len(self.time_axis) == 0:
            return

        self.gas_line.set_data(self.time_axis, self.gas_data)
        self.brake_line.set_data(self.time_axis, self.brake_data)

        if len(self.time_axis) < 2:
            self.gas_graph.set_xlim(0, 1)
            self.brake_graph.set_xlim(0, 1)

        else:
            self.gas_graph.set_xlim(0, self.time_axis[-1])
            self.brake_graph.set_xlim(0, self.time_axis[-1])

    def update_values(self, throttle: float, brake: float) -> None:

        self.gas_data.append(throttle * 100)
        self.brake_data.append(brake * 100)

        if self.last_time != 0:
            self.time_axis.append(time.time() - self.last_time)

        else:
            self.time_axis.append(0)
            self.last_time = time.time()

    def reset(self) -> None:

        self.time_axis.clear()
        self.gas_data.clear()
        self.brake_data.clear()
        self.last_time = 0

    def stop_animation(self) -> None:
        self.ani.event_source.stop()

    def start_animation(self) -> None:
        self.ani.event_source.start()


class DriverInputs(ttk.Frame):

    def __init__(self, root) -> None:

        ttk.Frame.__init__(self, master=root)

        self.input_graph = InputGraph(self)
        self.input_graph.grid(row=0, column=2, rowspan=6)

        self.lap = 0

        self._is_animating = False

        self.gas = tkinter.DoubleVar()
        self.brake = tkinter.DoubleVar()
        self.steering = tkinter.DoubleVar()
        self.gear = tkinter.IntVar()
        self.speed = tkinter.IntVar()

        l_gas = ttk.Label(self, text="Gas", anchor=tkinter.CENTER)
        l_gas.grid(row=0, column=0)
        l_brake = ttk.Label(self, text="Brake", anchor=tkinter.CENTER)
        l_brake.grid(row=0, column=1)

        self.c_gas = tkinter.Canvas(self, width=20, height=100)
        self.c_gas.grid(row=1, column=0, padx=10)

        self.c_brake = tkinter.Canvas(self, width=20, height=100)
        self.c_brake.grid(row=1, column=1, padx=10)

        l_steering = ttk.Label(self, text="Steering",
                               anchor=tkinter.CENTER)
        l_steering.grid(row=2, column=0, columnspan=2)

        self.c_steering = tkinter.Canvas(self, width=100, height=20)
        self.c_steering.grid(row=3, column=0, padx=10, pady=10, columnspan=2)

        self.gas_rect = self.c_gas.create_rectangle(0, 0, 20, 100,
                                                    fill="Green")
        self.brake_rect = self.c_brake.create_rectangle(0, 0, 20, 100,
                                                        fill="Red")

        self.steering_rect = self.c_steering.create_rectangle(0, 0, 100, 20,
                                                              fill="Yellow")

        l_gear = ttk.Label(self, text="Gear", width=7)
        l_gear.grid(row=4, column=0)

        gear_var = ttk.Label(self, textvariable=self.gear, width=5)
        gear_var.grid(row=4, column=1)

        l_speed = ttk.Label(self, text="Speed", width=7)
        l_speed.grid(row=5, column=0)

        speed_var = ttk.Label(self, textvariable=self.speed, width=5)
        speed_var.grid(row=5, column=1)

    def update_values(self, data: TelemetryRT) -> None:

        self.gas.set(data.gas)
        self.brake.set(data.brake)
        self.steering.set(data.streering_angle)
        self.gear.set(data.gear - 1)
        self.speed.set(int(data.speed))

        self.c_gas.coords(self.gas_rect, 0,
                          100 - self.gas.get() * 100, 20, 100)
        self.c_brake.coords(self.brake_rect, 0,
                            100 - self.brake.get() * 100, 20, 100)

        self.c_steering.coords(self.steering_rect,
                               0, 0, (self.steering.get() + 1) * 50, 20)

        self.input_graph.update_values(data.gas, data.brake)

    def update_lap(self, lap: int) -> None:

        if lap != self.lap:
            self.lap = lap
            self.input_graph.reset()

    def stop_animation(self) -> None:

        self.input_graph.stop_animation()
        self._is_animating = False

    def start_animation(self) -> None:

        self.input_graph.start_animation()
        self._is_animating = True

    @property
    def is_animating(self) -> bool:
        return self._is_animating
