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

    def __init__(self, root, font) -> None:

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

        title = tkinter.Label(f_pressures, text="Pressure lost (aprox)",
                              bg="Black", fg="White", width=17)
        title.config(font=self.font)
        title.grid(row=1, column=0, padx=2, pady=1)

        self.p_lost_fl = tkinter.DoubleVar()
        l_p_lost_fl = tkinter.Label(f_pressures, text="Front left",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_fl_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_fl,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_fl.grid(row=1, column=1)
        l_p_lost_fl_var.grid(row=1, column=2, padx=2, pady=1)

        self.p_lost_fr = tkinter.DoubleVar()
        l_p_lost_fr = tkinter.Label(f_pressures, text="Front right",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_fr_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_fr,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_fr.grid(row=1, column=3)
        l_p_lost_fr_var.grid(row=1, column=4, pady=1)

        self.p_lost_rl = tkinter.DoubleVar()
        l_p_lost_rl = tkinter.Label(f_pressures, text="Rear left",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_rl_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_rl,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_rl.grid(row=1, column=5)
        l_p_lost_rl_var.grid(row=1, column=6, pady=1)

        self.p_lost_rr = tkinter.DoubleVar()
        l_p_lost_rr = tkinter.Label(f_pressures, text="Rear right",
                                    bg="Black", fg="White", font=self.font,
                                    width=12)
        l_p_lost_rr_var = tkinter.Label(f_pressures,
                                        textvariable=self.p_lost_rr,
                                        bg="Black", fg="White", width=9,
                                        font=self.font)
        l_p_lost_rr.grid(row=1, column=7)
        l_p_lost_rr_var.grid(row=1, column=8, pady=1)

        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.pressure = self.figure.add_subplot(111)
        self._set_graph_info()

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.BOTTOM)

    def update_data(self, pressure: List[float], lap) -> None:

        if lap != self.current_lap:

            if len(self.pressures_fl) != 0:
                self.fl_var.set(f"{avg(self.pressures_fl):.2f}")
                self.fr_var.set(f"{avg(self.pressures_fr):.2f}")
                self.rl_var.set(f"{avg(self.pressures_rl):.2f}")
                self.rr_var.set(f"{avg(self.pressures_rr):.2f}")

            self._reset_data()
            self.current_lap = lap

        else:
            self._check_pressure_loss(pressure)

            self.pressures_fl.append(pressure[0])
            self.pressures_fr.append(pressure[1])
            self.pressures_rl.append(pressure[2])
            self.pressures_rr.append(pressure[3])

        self._draw_plot()

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

    def reset_pressure_loss(self) -> None:

        self.p_lost_fl.set(0)
        self.p_lost_fr.set(0)
        self.p_lost_rl.set(0)
        self.p_lost_rr.set(0)

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
