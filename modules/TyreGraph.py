import tkinter
import copy
from dataclasses import astuple
from typing import List

import matplotlib
import matplotlib.animation as animation
from matplotlib import pyplot, style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from modules.Common import avg
from modules.Telemetry import Telemetry

# Use tkinter backend
matplotlib.use("TkAgg")

style.use("dark_background")


class TyreGraph(tkinter.Frame):

    previous_laps = {}

    def __init__(self, root, font: tuple, config: dict) -> None:

        tkinter.Frame.__init__(self, master=root)

        self.pressures_fl = []
        self.pressures_fr = []
        self.pressures_rl = []
        self.pressures_rr = []
        self.data_point = []
        self.in_pit_lane = False

        self.current_lap = 0
        self.font = font

        self.app_config = config

        self.fl_var = tkinter.StringVar(value="0.0")
        self.fr_var = tkinter.StringVar(value="0.0")
        self.rl_var = tkinter.StringVar(value="0.0")
        self.rr_var = tkinter.StringVar(value="0.0")

        self.p_lost_fl = tkinter.DoubleVar()
        self.p_lost_fr = tkinter.DoubleVar()
        self.p_lost_rl = tkinter.DoubleVar()
        self.p_lost_rr = tkinter.DoubleVar()

        self.figure = pyplot.figure(figsize=(9, 5), dpi=100)
        self.graph = self.figure.add_subplot(1, 1, 1)

        self.plot_line_fl,  = self.graph.plot(
            self.data_point, self.pressures_fl,
            self.app_config["graph_colour"]["front_left"],
            label="Front left")

        self.plot_line_fr,  = self.graph.plot(
            self.data_point, self.pressures_fr,
            self.app_config["graph_colour"]["front_right"],
            label="Front right")

        self.plot_line_rl,  = self.graph.plot(
            self.data_point, self.pressures_rl,
            self.app_config["graph_colour"]["rear_left"],
            label="Rear left")

        self.plot_line_rr,  = self.graph.plot(
            self.data_point, self.pressures_rr,
            self.app_config["graph_colour"]["rear_right"],
            label="Rear right")

        self.graph.set_title("Pressures over time")
        self.graph.set_xlabel("Time (Seconds)")
        self.graph.set_ylabel("Pressures (PSI)")
        self.graph.legend()

        self._build_UI()

    def update_data(self, telemetry: Telemetry) -> None:

        pressures = astuple(telemetry.tyre_pressure)

        if telemetry.lap != self.current_lap:

            if len(self.pressures_fl) != 0:
                self.fl_var.set(f"{avg(self.pressures_fl):.2f}")
                self.fr_var.set(f"{avg(self.pressures_fr):.2f}")
                self.rl_var.set(f"{avg(self.pressures_rl):.2f}")
                self.rr_var.set(f"{avg(self.pressures_rr):.2f}")

                lap_pressure = {
                    "front left": [],
                    "front right": [],
                    "rear left": [],
                    "rear right": []
                }

                for index, pressure in enumerate(self.pressures_fl):

                    if index % self.app_config["saved_graph_step"] == 0:
                        lap_pressure["front left"].append(pressure)

                for index, pressure in enumerate(self.pressures_fr):

                    if index % self.app_config["saved_graph_step"] == 0:
                        lap_pressure["front right"].append(pressure)

                for index, pressure in enumerate(self.pressures_rl):

                    if index % self.app_config["saved_graph_step"] == 0:
                        lap_pressure["rear left"].append(pressure)

                for index, pressure in enumerate(self.pressures_rr):

                    if index % self.app_config["saved_graph_step"] == 0:
                        lap_pressure["rear right"].append(pressure)

                TyreGraph.previous_laps[str(telemetry.lap)] = lap_pressure

            self._reset_pressures()
            self.current_lap = telemetry.lap

        if self.in_pit_lane and not telemetry.in_pit_lane:
            self._reset_pressures()
            self._reset_pressure_loss()
            self.in_pit_lane = False

        if telemetry.in_pit_lane:
            self.in_pit_lane = True

        else:
            self._check_pressure_loss(pressures)

            self.pressures_fl.append(pressures[0])
            self.pressures_fr.append(pressures[1])
            self.pressures_rl.append(pressures[2])
            self.pressures_rr.append(pressures[3])

            self.data_point = [i / 2 for i in range(0, len(self.pressures_fl))]

    def _check_pressure_loss(self, pressures: List[float]) -> None:

        if len(self.pressures_fl) == 0:
            return

        delta = 0.05

        diff_lf = self.pressures_fl[-1] - pressures[0]
        if diff_lf > delta:
            self.p_lost_fl.set(f"{self.p_lost_fl.get() + diff_lf:.2f}")

        diff_lf = self.pressures_fr[-1] - pressures[1]
        if diff_lf > delta:
            self.p_lost_fr.set(f"{self.p_lost_fr.get() + diff_lf:.2f}")

        diff_lf = self.pressures_rl[-1] - pressures[2]
        if diff_lf > delta:
            self.p_lost_rl.set(f"{self.p_lost_rl.get() + diff_lf:.2f}")

        diff_lf = self.pressures_rr[-1] - pressures[3]
        if diff_lf > delta:
            self.p_lost_rr.set(f"{self.p_lost_rr.get() + diff_lf:.2f}")

    def _reset_pressure_loss(self) -> None:

        self.p_lost_fl.set(0)
        self.p_lost_fr.set(0)
        self.p_lost_rl.set(0)
        self.p_lost_rr.set(0)

    def _animate(self, i) -> None:

        if len(self.pressures_fl) == 0:
            return

        self.plot_line_fl.set_data(self.data_point, self.pressures_fl)
        self.plot_line_fr.set_data(self.data_point, self.pressures_fr)
        self.plot_line_rl.set_data(self.data_point, self.pressures_rl)
        self.plot_line_rr.set_data(self.data_point, self.pressures_rr)

        min_all = self._find_lowest_pressure()
        max_all = self._find_higest_pressure()

        self.graph.set_ylim(min_all - 0.2, max_all + 0.2)

        if len(self.data_point) == 1:
            self.graph.set_xlim(0, 1)

        else:
            self.graph.set_xlim(0, self.data_point[-1])

    def _find_higest_pressure(self) -> None:

        fl_max = max(self.pressures_fl)
        fr_max = max(self.pressures_fr)
        rl_max = max(self.pressures_rl)
        rr_max = max(self.pressures_rr)

        max_font = max(fl_max, fr_max)
        max_rear = max(rl_max, rr_max)

        return max(max_font, max_rear)

    def _find_lowest_pressure(self) -> None:

        fl_min = min(self.pressures_fl)
        fr_min = min(self.pressures_fr)
        rl_min = min(self.pressures_rl)
        rr_min = min(self.pressures_rr)

        min_font = min(fl_min, fr_min)
        min_rear = min(rl_min, rr_min)

        return min(min_font, min_rear)

    def _reset_pressures(self) -> None:

        self.pressures_fl.clear()
        self.pressures_fr.clear()
        self.pressures_rl.clear()
        self.pressures_rr.clear()
        self.data_point.clear()

    def reset(self) -> None:

        self.current_lap = 0
        self._reset_pressures()

    def close(self) -> None:

        pyplot.close("all")
        self.destroy()

    def _build_UI(self) -> None:

        f_pressures = tkinter.Frame(self, bg="Grey", pady=2)
        f_pressures.pack(side=tkinter.TOP)

        title = tkinter.Label(f_pressures, text="Last lap average",
                              bg="Black", fg="White", width=17)
        title.config(font=self.font)
        title.grid(row=0, column=0, padx=2)

        l_front_left = tkinter.Label(f_pressures, text="Front left",
                                     bg="Black", fg="White", width=12)
        l_front_left.config(font=self.font)
        l_front_left.grid(row=0, column=1, padx=2)

        l_front_left_var = tkinter.Label(f_pressures, textvariable=self.fl_var,
                                         width=9, bg="Black", fg="White")
        l_front_left_var.config(font=self.font)
        l_front_left_var.grid(row=0, column=2, padx=2)

        l_front_right = tkinter.Label(f_pressures, text="Front right",
                                      bg="Black", fg="White", width=12)
        l_front_right.config(font=self.font)
        l_front_right.grid(row=0, column=3, padx=2)

        l_front_right_var = tkinter.Label(f_pressures,
                                          textvariable=self.fr_var,
                                          width=9, bg="Black", fg="White")
        l_front_right_var.config(font=self.font)
        l_front_right_var.grid(row=0, column=4, padx=2)

        l_rear_left = tkinter.Label(f_pressures, text="Rear left",
                                    bg="Black", fg="White", width=12)
        l_rear_left.config(font=self.font)
        l_rear_left.grid(row=0, column=5, padx=2)

        l_rear_left_var = tkinter.Label(f_pressures,  textvariable=self.rl_var,
                                        width=9, bg="Black", fg="White")
        l_rear_left_var.config(font=self.font)
        l_rear_left_var.grid(row=0, column=6, padx=2)

        l_rear_right = tkinter.Label(f_pressures, text="Rear right",
                                     bg="Black", fg="White", width=12)
        l_rear_right.config(font=self.font)
        l_rear_right.grid(row=0, column=7, padx=2)

        l_rear_right_var = tkinter.Label(f_pressures, textvariable=self.rr_var,
                                         width=9, bg="Black", fg="White")
        l_rear_right_var.config(font=self.font)
        l_rear_right_var.grid(row=0, column=8, padx=2)

        title = tkinter.Label(f_pressures, text="Pressure lost (aprox)",
                              bg="Black", fg="White", width=17)
        title.config(font=self.font)
        title.grid(row=1, column=0, padx=2, pady=1)

        l_p_lost_fl = tkinter.Label(f_pressures, text="Front left",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_fl_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_fl,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_fl.grid(row=1, column=1)
        l_p_lost_fl_var.grid(row=1, column=2, padx=2, pady=1)

        l_p_lost_fr = tkinter.Label(f_pressures, text="Front right",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_fr_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_fr,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_fr.grid(row=1, column=3)
        l_p_lost_fr_var.grid(row=1, column=4, pady=1)

        l_p_lost_rl = tkinter.Label(f_pressures, text="Rear left",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_rl_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_rl,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_rl.grid(row=1, column=5)
        l_p_lost_rl_var.grid(row=1, column=6, pady=1)

        l_p_lost_rr = tkinter.Label(f_pressures, text="Rear right",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_rr_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_rr,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_rr.grid(row=1, column=7)
        l_p_lost_rr_var.grid(row=1, column=8, pady=1)

        canvas = FigureCanvasTkAgg(self.figure, self)
        canvas.get_tk_widget().pack(side=tkinter.BOTTOM)
        self.ani = animation.FuncAnimation(self.figure, self._animate,
                                           interval=500, blit=False)
