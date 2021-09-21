import copy
import io
import pathlib
import tkinter
from dataclasses import astuple
from datetime import datetime
from tkinter import ttk
from typing import List

import matplotlib
import matplotlib.animation as animation
import win32clipboard
from matplotlib import pyplot, style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image

from modules.Common import avg, send_to_clipboard
from modules.Telemetry import Telemetry, TelemetryRT

# Use tkinter backend
matplotlib.use("TkAgg")

style.use("dark_background")


class TyreGraph(ttk.Frame):

    previous_laps = {}

    def __init__(self, root, config: dict) -> None:

        ttk.Frame.__init__(self, master=root)

        self.pressures_fl = []
        self.pressures_fr = []
        self.pressures_rl = []
        self.pressures_rr = []
        self.time_axis = []
        self.in_pit_lane = False

        self.current_lap = 0

        self.app_config = config

        self.fl_var = tkinter.StringVar(value="0.0")
        self.fr_var = tkinter.StringVar(value="0.0")
        self.rl_var = tkinter.StringVar(value="0.0")
        self.rr_var = tkinter.StringVar(value="0.0")

        self.p_lost_fl = tkinter.DoubleVar()
        self.p_lost_fr = tkinter.DoubleVar()
        self.p_lost_rl = tkinter.DoubleVar()
        self.p_lost_rr = tkinter.DoubleVar()

        self.figure = pyplot.figure(figsize=(8, 4), dpi=100)
        self.graph = self.figure.add_subplot(1, 1, 1)

        self.plot_line_fl,  = self.graph.plot(
            self.time_axis, self.pressures_fl,
            self.app_config["graph_colour"]["front_left"],
            label="Front left")

        self.plot_line_fr,  = self.graph.plot(
            self.time_axis, self.pressures_fr,
            self.app_config["graph_colour"]["front_right"],
            label="Front right")

        self.plot_line_rl,  = self.graph.plot(
            self.time_axis, self.pressures_rl,
            self.app_config["graph_colour"]["rear_left"],
            label="Rear left")

        self.plot_line_rr,  = self.graph.plot(
            self.time_axis, self.pressures_rr,
            self.app_config["graph_colour"]["rear_right"],
            label="Rear right")

        self.graph.set_title("Pressures over time")
        self.graph.set_xlabel("Time (Seconds)")
        self.graph.set_ylabel("Pressures (PSI)")
        self.graph.legend()
        self.graph.grid(color="#696969", linestyle='-', linewidth=1)

        self._build_UI()

    def update_data(self, telemetry: Telemetry) -> None:

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
                    "rear right": [],
                    "time": []
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

                for index, pressure in enumerate(self.time_axis):

                    if index % self.app_config["saved_graph_step"] == 0:
                        lap_pressure["time"].append(pressure)

                key_name = f"{telemetry.session}-Lap_{telemetry.lap}"
                TyreGraph.previous_laps[key_name] = lap_pressure

            self._reset_pressures()
            self.current_lap = telemetry.lap

        pressures = astuple(telemetry.tyre_pressure)

        if not self.in_pit_lane and avg(pressures) != 0:
            self._check_pressure_loss(pressures)

            self.pressures_fl.append(pressures[0])
            self.pressures_fr.append(pressures[1])
            self.pressures_rl.append(pressures[2])
            self.pressures_rr.append(pressures[3])

            self.time_axis.append(telemetry.lap_time / 1000)

        if self.in_pit_lane and not telemetry.in_pit_lane:
            self._reset_pressures()
            self._reset_pressure_loss()
            self.in_pit_lane = False

        elif telemetry.in_pit_lane:
            self.in_pit_lane = True

    def _check_pressure_loss(self, pressures: List[float]) -> None:

        if len(self.pressures_fl) == 0:
            return

        delta = 0.075

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

        if len(self.time_axis) != len(self.pressures_fl):
            print("update incomplet")
            return

        self.plot_line_fl.set_data(self.time_axis, self.pressures_fl)
        self.plot_line_fr.set_data(self.time_axis, self.pressures_fr)
        self.plot_line_rl.set_data(self.time_axis, self.pressures_rl)
        self.plot_line_rr.set_data(self.time_axis, self.pressures_rr)

        min_all = self._find_lowest_pressure()
        max_all = self._find_higest_pressure()

        self.graph.set_ylim(min_all - 0.2, max_all + 0.2)

        if len(self.time_axis) == 1:
            self.graph.set_xlim(0, 1)

        else:
            self.graph.set_xlim(0, self.time_axis[-1])

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
        self.time_axis.clear()

    def reset(self) -> None:

        self.current_lap = 0
        self._reset_pressures()

    def close(self) -> None:

        pyplot.close("all")
        self.destroy()

    def _build_UI(self) -> None:

        f_pressures = ttk.Frame(self, style="PressureInfo.TFrame")
        f_pressures.pack(side=tkinter.TOP)

        # Row Label
        title = ttk.Label(f_pressures, text="Last lap average", width=36)
        title.grid(row=1, column=0, padx=1, pady=1)

        title = ttk.Label(f_pressures,
                          text="Pressure lost on this tyre set (aprox)",
                          width=36)
        title.grid(row=2, column=0, padx=1, pady=1)

        # Colum Label
        l_front_left = ttk.Label(f_pressures, text="Front left", width=15,
                                 anchor=tkinter.CENTER)
        l_front_left.grid(row=0, column=1, padx=1, pady=1)

        l_front_right = ttk.Label(f_pressures, text="Front right", width=15,
                                  anchor=tkinter.CENTER)
        l_front_right.grid(row=0, column=2, padx=1, pady=1)

        l_rear_left = ttk.Label(f_pressures, text="Rear left", width=15,
                                anchor=tkinter.CENTER)
        l_rear_left.grid(row=0, column=3, padx=1, pady=1)

        l_rear_right = ttk.Label(f_pressures, text="Rear right", width=15,
                                 anchor=tkinter.CENTER)
        l_rear_right.grid(row=0, column=4, padx=1, pady=1)

        # Pressure avg values
        l_fl_var = ttk.Label(f_pressures, textvariable=self.fl_var,
                             width=15, anchor=tkinter.CENTER)
        l_fl_var.grid(row=1, column=1, padx=1)

        l_fr_var = ttk.Label(f_pressures, textvariable=self.fr_var,
                             width=15, anchor=tkinter.CENTER)
        l_fr_var.grid(row=1, column=2, padx=1)

        l_rl_var = ttk.Label(f_pressures,  textvariable=self.rl_var,
                             width=15, anchor=tkinter.CENTER)
        l_rl_var.grid(row=1, column=3, padx=1)

        l_rr_var = ttk.Label(f_pressures, textvariable=self.rr_var,
                             width=15, anchor=tkinter.CENTER)
        l_rr_var.grid(row=1, column=4, padx=1)

        # Pressure lost values
        l_lost_fl = ttk.Label(f_pressures, textvariable=self.p_lost_fl,
                              width=15, anchor=tkinter.CENTER)
        l_lost_fl.grid(row=2, column=1, padx=1, pady=1)

        l_lost_fr = ttk.Label(f_pressures, textvariable=self.p_lost_fr,
                              width=15, anchor=tkinter.CENTER)
        l_lost_fr.grid(row=2, column=2, pady=1)

        l_lost_rl = ttk.Label(f_pressures, textvariable=self.p_lost_rl,
                              width=15, anchor=tkinter.CENTER)
        l_lost_rl.grid(row=2, column=3, pady=1)

        l_lost_rr = ttk.Label(f_pressures, textvariable=self.p_lost_rr,
                              width=15, anchor=tkinter.CENTER)
        l_lost_rr.grid(row=2, column=4)

        canvas = FigureCanvasTkAgg(self.figure, self)
        canvas.get_tk_widget().pack(side=tkinter.BOTTOM)
        self.ani = animation.FuncAnimation(self.figure, self._animate,
                                           interval=500, blit=False)


class PrevLapsGraph(ttk.Frame):

    def __init__(self, root, config: dict) -> None:

        ttk.Frame.__init__(self, master=root)

        self.laps = copy.copy(TyreGraph.previous_laps)

        self.avg_fl = tkinter.DoubleVar()
        self.avg_fr = tkinter.DoubleVar()
        self.avg_rl = tkinter.DoubleVar()
        self.avg_rr = tkinter.DoubleVar()

        self.app_config = config

        self._update_list_id = None

        self.figure = pyplot.figure(figsize=(8, 4), dpi=100)
        self.graph = self.figure.add_subplot(1, 1, 1)

        f_lap_select = ttk.Frame(self)
        f_lap_select.grid_columnconfigure(index=2, minsize=250)
        f_lap_select.grid(row=0, column=0)

        l_lap = ttk.Label(f_lap_select, text="Lap", width=6)
        l_lap.grid(row=0, column=0)

        self.lap_selector = ttk.Combobox(f_lap_select, values=[""],
                                         state="readonly")
        self.lap_selector.bind("<<ComboboxSelected>>", self._plot)

        self.lap_selector.grid(row=0, column=1)

        self.b_save = ttk.Button(f_lap_select, text="Save graph as png",
                                 command=self._save_graph)
        self.b_save.grid(row=0, column=3)

        self.b_copy = ttk.Button(f_lap_select, text="Copy graph to clipboard",
                                 command=self._copy_graph)
        self.b_copy.grid(row=0, column=4)

        f_avg_pressure = ttk.Frame(self, style="PressureInfo.TFrame")
        f_avg_pressure.grid(row=1, column=0)

        # Row Label
        title = ttk.Label(f_avg_pressure, text="Last lap average", width=36)
        title.grid(row=1, column=0, padx=1, pady=1)

        # Colum Label
        l_front_left = ttk.Label(f_avg_pressure, text="Front left", width=15,
                                 anchor=tkinter.CENTER)
        l_front_left.grid(row=0, column=1, padx=1, pady=1)

        l_front_right = ttk.Label(f_avg_pressure, text="Front right", width=15,
                                  anchor=tkinter.CENTER)
        l_front_right.grid(row=0, column=2, padx=1, pady=1)

        l_rear_left = ttk.Label(f_avg_pressure, text="Rear left", width=15,
                                anchor=tkinter.CENTER)
        l_rear_left.grid(row=0, column=3, padx=1, pady=1)

        l_rear_right = ttk.Label(f_avg_pressure, text="Rear right", width=15,
                                 anchor=tkinter.CENTER)
        l_rear_right.grid(row=0, column=4, padx=1, pady=1)

        # Pressure avg values
        l_fl_var = ttk.Label(f_avg_pressure, textvariable=self.avg_fl,
                             width=15, anchor=tkinter.CENTER)
        l_fl_var.grid(row=1, column=1, padx=1)

        l_fr_var = ttk.Label(f_avg_pressure, textvariable=self.avg_fr,
                             width=15, anchor=tkinter.CENTER)
        l_fr_var.grid(row=1, column=2, padx=1)

        l_rl_var = ttk.Label(f_avg_pressure,  textvariable=self.avg_rl,
                             width=15, anchor=tkinter.CENTER)
        l_rl_var.grid(row=1, column=3, padx=1)

        l_rr_var = ttk.Label(f_avg_pressure, textvariable=self.avg_rr,
                             width=15, anchor=tkinter.CENTER)
        l_rr_var.grid(row=1, column=4, padx=1)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().grid(row=2, column=0)

        self.graph.set_title(f"Pressures over time for lap None")
        self.graph.set_xlabel("Time (Seconds)")
        self.graph.set_ylabel("Pressures (PSI)")
        self.graph.grid(color="#696969", linestyle='-', linewidth=1)

        self._update_list_id = self.after(
            self.app_config["live_graph_inverval"] * 1000, self._update_list)

    def _update_list(self) -> None:

        laps = TyreGraph.previous_laps

        if self.laps != laps:

            laps_key = list(laps.keys())

            for key in laps_key:
                if key not in self.lap_selector["values"]:
                    self.lap_selector["values"] = (
                        *self.lap_selector["values"], key)

            self.laps = copy.copy(laps)

        self._update_list_id = self.after(
            self.app_config["live_graph_inverval"] * 1000, self._update_list)

    def _plot(self, _) -> None:

        key = self.lap_selector.get()

        if key == "":
            return

        lap_data = self.laps[key]

        print(f"Ploting for {key}")

        self.graph.clear()

        self.graph.plot(lap_data["time"], lap_data["front left"],
                        self.app_config["graph_colour"]["front_left"],
                        label="Front left")
        self.graph.plot(lap_data["time"], lap_data["front right"],
                        self.app_config["graph_colour"]["front_right"],
                        label="Front right")
        self.graph.plot(lap_data["time"], lap_data["rear left"],
                        self.app_config["graph_colour"]["rear_left"],
                        label="Rear left")
        self.graph.plot(lap_data["time"], lap_data["rear right"],
                        self.app_config["graph_colour"]["rear_right"],
                        label="Rear right")

        min_all = self._find_lowest_pressure()
        max_all = self._find_higest_pressure()

        self.graph.set_ylim(min_all - 0.2, max_all + 0.2)

        if len(lap_data["time"]) == 1:
            self.graph.set_xlim(0, 1)

        else:
            self.graph.set_xlim(0, lap_data["time"][-1])

        self.graph.set_title(f"Pressures over time for {key}")
        self.graph.set_xlabel("Time (Seconds)")
        self.graph.set_ylabel("Pressures (PSI)")
        self.graph.legend()
        self.graph.grid(color="#696969", linestyle='-', linewidth=1)

        self.canvas.draw()

        self.avg_fl.set(f"{avg(lap_data['front left']):.1f}")
        self.avg_fr.set(f"{avg(lap_data['front right']):.1f}")
        self.avg_rl.set(f"{avg(lap_data['rear left']):.1f}")
        self.avg_rr.set(f"{avg(lap_data['rear right']):.1f}")

    def _save_graph(self) -> None:

        if self.lap_selector.get() == "":
            return

        name = self.lap_selector.get()
        time = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

        save_dir = pathlib.Path("./Pressure_Graph")
        save_dir.mkdir(parents=True, exist_ok=True)

        path = save_dir / f"{time}_{name}.png"

        self.figure.savefig(str(path))

    def _copy_graph(self) -> None:

        if self.lap_selector.get() == "":
            return

        # Save figure to in-memory buffer
        png_buffer = io.BytesIO()
        self.figure.savefig(png_buffer, format="png")
        png_buffer.seek(0)

        # Convert PNG image to BMP and save to in-memory buffer
        bmp_buffer = io.BytesIO()
        image = Image.open(png_buffer)
        image.convert("RGB").save(bmp_buffer, "BMP")

        # Get bytes and remove header
        final_data = bmp_buffer.getvalue()[14:]

        send_to_clipboard(win32clipboard.CF_DIB, final_data)

        png_buffer.close()
        bmp_buffer.close()

    def close(self) -> None:

        self.after_cancel(self._update_list_id)

    def _find_higest_pressure(self) -> None:

        key = self.lap_selector.get()

        fl_max = max(self.laps[key]["front left"])
        fr_max = max(self.laps[key]["front right"])
        rl_max = max(self.laps[key]["rear left"])
        rr_max = max(self.laps[key]["rear right"])

        max_font = max(fl_max, fr_max)
        max_rear = max(rl_max, rr_max)

        return max(max_font, max_rear)

    def _find_lowest_pressure(self) -> None:

        key = self.lap_selector.get()

        fl_min = min(self.laps[key]["front left"])
        fr_min = min(self.laps[key]["front right"])
        rl_min = min(self.laps[key]["rear left"])
        rr_min = min(self.laps[key]["rear right"])

        min_font = min(fl_min, fr_min)
        min_rear = min(rl_min, rr_min)

        return min(min_font, min_rear)
