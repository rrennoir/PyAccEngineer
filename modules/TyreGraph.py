import tkinter
from typing import List

import matplotlib
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from modules.Common import avg

# Use tkinter backend
matplotlib.use("TkAgg")

style.use("dark_background")


class TyreGraph(tkinter.Frame):

    def __init__(self, root) -> None:

        tkinter.Frame.__init__(self, master=root)

        self.pressures_fl = []
        self.pressures_fr = []
        self.pressures_rl = []
        self.pressures_rr = []

        self.current_lap = 0
        self.font = ("Helvetica", 13)

        f_lap_avg = tkinter.Frame(self, bg="Grey", pady=2)
        f_lap_avg.pack(side=tkinter.TOP)

        title = tkinter.Label(f_lap_avg, text="Last lap average",
                              bg="Black", fg="White", width=17)
        title.config(font=self.font)
        title.grid(row=0, column=0, padx=2)

        l_front_left = tkinter.Label(f_lap_avg, text="Front left",
                                     bg="Black", fg="White", width=12)
        l_front_left.config(font=self.font)
        l_front_left.grid(row=0, column=1, padx=2)

        self.fl_var = tkinter.StringVar(value="0.0 PSI")
        l_front_left_var = tkinter.Label(f_lap_avg,  textvariable=self.fl_var,
                                         width=9, bg="Black", fg="White")
        l_front_left_var.config(font=self.font)
        l_front_left_var.grid(row=0, column=2, padx=2)

        l_front_right = tkinter.Label(f_lap_avg, text="Front right",
                                      bg="Black", fg="White", width=12)
        l_front_right.config(font=self.font)
        l_front_right.grid(row=0, column=3, padx=2)

        self.fr_var = tkinter.StringVar(value="0.0 PSI")
        l_front_right_var = tkinter.Label(f_lap_avg,  textvariable=self.fr_var,
                                          width=9, bg="Black", fg="White")
        l_front_right_var.config(font=self.font)
        l_front_right_var.grid(row=0, column=4, padx=2)

        l_rear_left = tkinter.Label(f_lap_avg, text="Rear left",
                                    bg="Black", fg="White", width=12)
        l_rear_left.config(font=self.font)
        l_rear_left.grid(row=0, column=5, padx=2)

        self.rl_var = tkinter.StringVar(value="0.0 PSI")
        l_rear_left_var = tkinter.Label(f_lap_avg,  textvariable=self.rl_var,
                                        width=9, bg="Black", fg="White")
        l_rear_left_var.config(font=self.font)
        l_rear_left_var.grid(row=0, column=6, padx=2)

        l_rear_right = tkinter.Label(f_lap_avg, text="Rear right",
                                     bg="Black", fg="White", width=12)
        l_rear_right.config(font=self.font)
        l_rear_right.grid(row=0, column=7, padx=2)

        self.rr_var = tkinter.StringVar(value="0.0 PSI")
        l_rear_right_var = tkinter.Label(f_lap_avg, textvariable=self.rr_var,
                                         width=9, bg="Black", fg="White")
        l_rear_right_var.config(font=self.font)
        l_rear_right_var.grid(row=0, column=8, padx=2)

        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.pressure = self.figure.add_subplot(111)
        self._set_graph_info()

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.BOTTOM)

    def update_data(self, pressure: List[float], lap) -> None:

        if lap != self.current_lap:

            if len(self.pressures_fl) != 0:
                self.fl_var.set(f"{avg(self.pressures_fl):.2f} PSI")
                self.fr_var.set(f"{avg(self.pressures_fr):.2f} PSI")
                self.rl_var.set(f"{avg(self.pressures_rl):.2f} PSI")
                self.rr_var.set(f"{avg(self.pressures_rr):.2f} PSI")

            self._reset_data()
            self.current_lap = lap

        else:
            self.pressures_fl.append(pressure[0])
            self.pressures_fr.append(pressure[1])
            self.pressures_rl.append(pressure[2])
            self.pressures_rr.append(pressure[3])

        self._draw_plot()

    def _draw_plot(self) -> None:

        self.pressure.clear()

        data_point = [i for i in range(len(self.pressures_fl))]

        self.pressure.plot(data_point, self.pressures_fl, label="Front left")
        self.pressure.plot(data_point, self.pressures_fr, label="Front right")
        self.pressure.plot(data_point, self.pressures_rl, label="Rear left")
        self.pressure.plot(data_point, self.pressures_rr, label="Rear right")

        self._set_graph_info()

        if len(self.pressures_fl) != 0:
            self.pressure.legend()

        self.canvas.draw()

    def _reset_data(self) -> None:

        self.pressures_fl.clear()
        self.pressures_fr.clear()
        self.pressures_rl.clear()
        self.pressures_rr.clear()

    def _set_graph_info(self) -> None:

        self.pressure.set_title("Pressures over time")
        self.pressure.set_xlabel("Time (Seconds)")
        self.pressure.set_ylabel("Pressures (PSI)")

    def reset(self) -> None:

        self.current_lap = 0
        self._reset_data()
        self._draw_plot()
