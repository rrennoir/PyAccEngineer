from __future__ import annotations

import ipaddress
import json
import queue
import struct
import time
from pathlib import Path
import tkinter
from dataclasses import astuple
from functools import partial
from tkinter import messagebox, ttk
from typing import Tuple

from modules.Client import ClientInstance
from modules.Common import CarInfo, NetworkQueue, PitStop, Credidentials
from modules.Server import ServerInstance
from modules.Strategy import StrategyUI
from modules.Telemetry import Telemetry, TelemetryUI
from modules.TyreGraph import PrevLapsGraph, TyreGraph
from modules.Users import UserUI

_VERSION_ = "1.4.0"


class ConnectionWindow(tkinter.Toplevel):

    def __init__(self, root: App, as_server: bool = False):
        tkinter.Toplevel.__init__(self, master=root)

        self.title("Connection window")
        self.main_app = root
        self.connection_path = "./Config/connection.json"

        self.credidentials = None
        key_check = ("ip", "tcp_port", "udp_port", "username",
                     "driverID")

        if Path(self.connection_path).is_file():
            fp = open(self.connection_path, "r")

            try:
                self.credidentials = json.load(fp)

                if (type(self.credidentials) is not dict or
                        tuple(self.credidentials.keys()) != key_check):

                    print(f"Invalid connection.json file")
                    self.credidentials = None

            except json.JSONDecodeError as msg:
                self.credidentials = None
                print(f"JSON Error: {msg}")

            fp.close()

        else:
            print(f"{self.connection_path} not found")
            self.credidentials = None

        # Block other window as long as this one is open
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.as_server = as_server

        self.f_connection_info = tkinter.Frame(
            self, bd=2, relief=tkinter.RIDGE)
        self.f_connection_info.grid()

        self.l_ip = tkinter.Label(self.f_connection_info, text="IP",
                                  anchor=tkinter.E, width=10)
        self.l_ip.grid(row=0, column=0, padx=5, pady=2)

        self.l_tcp_port = tkinter.Label(self.f_connection_info,
                                        text="TCP port", anchor=tkinter.E,
                                        width=10)
        self.l_tcp_port.grid(row=1, column=0, padx=5, pady=2)

        self.l_udp_port = tkinter.Label(self.f_connection_info,
                                        text="UDP port", anchor=tkinter.E,
                                        width=10)
        self.l_udp_port.grid(row=2, column=0, padx=5, pady=2)

        self.l_username = tkinter.Label(self.f_connection_info,
                                        text="Username",
                                        anchor=tkinter.E, width=10)
        self.l_username.grid(row=3, column=0, padx=5, pady=2)

        self.l_driverID = tkinter.Label(self.f_connection_info,
                                        text="Driver ID",
                                        anchor=tkinter.E, width=10)
        self.l_driverID.grid(row=4, column=0, padx=5, pady=2)

        self.e_ip = tkinter.Entry(self.f_connection_info, width=30)
        self.e_ip.grid(row=0, column=1, padx=5, pady=2)

        self.e_tcp_port = tkinter.Entry(self.f_connection_info, width=30)
        self.e_tcp_port.grid(row=1, column=1, padx=5, pady=2)

        self.e_udp_port = tkinter.Entry(self.f_connection_info, width=30)
        self.e_udp_port.grid(row=2, column=1, padx=5, pady=2)

        self.e_username = tkinter.Entry(self.f_connection_info, width=30)
        self.e_username.grid(row=3, column=1, padx=5, pady=2)

        self.e_driverID = tkinter.Entry(self.f_connection_info, width=30)
        self.e_driverID.grid(row=4, column=1, padx=5, pady=2)

        self.b_connect = tkinter.Button(self, text="Connect",
                                        command=self.connect)
        self.b_connect.grid(row=1, padx=10, pady=5)

        if self.credidentials is not None:

            if not self.as_server:
                self.e_ip.insert(tkinter.END, self.credidentials["ip"])

            self.e_tcp_port.insert(tkinter.END, self.credidentials["tcp_port"])
            self.e_udp_port.insert(tkinter.END, self.credidentials["udp_port"])
            self.e_username.insert(tkinter.END, self.credidentials["username"])
            self.e_driverID.insert(tkinter.END, self.credidentials["driverID"])

        else:
            self.e_tcp_port.insert(tkinter.END, "4269")
            self.e_udp_port.insert(tkinter.END, "4270")

        if self.as_server:
            self.e_ip.insert(tkinter.END, "127.0.0.1")
            self.e_ip.config(state="disabled")

    def connect(self) -> None:

        self.b_connect.config(state="disabled")

        error_message = ""

        try:
            ipaddress.ip_address(self.e_ip.get())
            self.e_ip.config(background="White")

        except ValueError:
            self.e_ip.config(background="Red")
            error_message += "Invalide IP address\n"

        if self.e_tcp_port.get().isnumeric():
            self.e_tcp_port.config(background="White")

        else:
            self.e_tcp_port.config(background="Red")
            error_message += "Invalide TCP port\n"

        if self.e_udp_port.get().isnumeric():
            self.e_udp_port.config(background="White")

        else:
            self.e_udp_port.config(background="Red")
            error_message += "Invalide UDP port\n"

        if self.e_username.get() != "":
            self.e_username.config(background="White")

        else:
            self.e_username.config(background="Red")
            error_message += "Invalide username\n"

        driverID = self.e_driverID.get()
        if driverID != "" and driverID.isnumeric():
            self.e_driverID.config(background="White")

        else:
            self.e_driverID.config(background="Red")
            error_message += "Invalide driver ID\n"

        if error_message == "":

            credits = Credidentials(
                ip=self.e_ip.get(),
                tcp_port=int(self.e_tcp_port.get()),
                udp_port=int(self.e_udp_port.get()),
                username=self.e_username.get(),
                driverID=int(self.e_driverID.get())
            )

            if self.as_server:

                connected, msg = self.main_app.as_server(credits)

                if connected:
                    self.save_credidentials(credits)
                    self.on_close()

                else:
                    messagebox.showerror("Error", msg)
                    self.b_connect.config(state="active")

            else:
                connected, msg = self.main_app.connect_to_server(credits)

                if connected:
                    self.save_credidentials(credits)
                    self.on_close()

                else:
                    messagebox.showerror("Error", msg)
                    self.b_connect.config(state="active")

        else:
            messagebox.showerror("Error", error_message)
            self.b_connect.config(state="active")

    def save_credidentials(self, credits: Credidentials) -> None:

        with open(self.connection_path, "w") as fp:

            connection = {
                "ip": credits.ip,
                "tcp_port": credits.tcp_port,
                "udp_port": credits.udp_port,
                "username": credits.username,
                "driverID": credits.driverID
            }
            json.dump(connection, fp)

    def on_close(self) -> None:

        self.grab_release()
        self.destroy()


class App(tkinter.Tk):

    def __init__(self) -> None:

        tkinter.Tk.__init__(self)

        try:
            with open("./Config/gui.json", "r") as fp:

                self.gui_config = json.load(fp)

        except FileNotFoundError:
            print("APP: './Config/gui.json' not found.")
            return

        self.font = (self.gui_config["font"], self.gui_config["font_size"])
        self.iconbitmap("./Assets/Icon/techSupport.ico")

        app_style = ttk.Style(self)
        app_style.configure('.',
                            font=self.font,
                            background=self.gui_config["background_colour"],
                            foreground=self.gui_config["foreground_colour"])

        app_style.configure('TNotebook.Tab', foreground="#000000")
        app_style.configure('TButton', foreground="#000000")
        app_style.configure('TCombobox', foreground="#000000")

        app_style.configure("ActiveDriver.TLabel",
                            background=self.gui_config["active_driver_colour"])

        app_style.configure("Users.TFrame", background="#000000")
        app_style.configure("PressureInfo.TFrame", background="#000000")

        self.title(f"PyAccEngineer {_VERSION_}")
        self.config(bg="Grey")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.c_loop_id = None

        # Networking
        self.server = None
        self.client = None
        self.client_queue_out = queue.Queue()
        self.client_queue_in = queue.Queue()

        self.connection_window = None

        self.menu_bar = tkinter.Menu(self)
        self.menu_bar.add_command(label="Connect",
                                  command=self.open_connection_window,
                                  font=self.font)

        self.menu_bar.add_command(label="As Server",
                                  command=partial(self.open_connection_window,
                                                  True),  font=self.font)
        self.menu_bar.add_command(label="Disconnect",
                                  command=self.disconnect, state="disabled",
                                  font=self.font)

        self.config(menu=self.menu_bar)

        tab_control = ttk.Notebook(self)
        tab_control.grid(row=0, column=0, pady=3)

        self.user_ui = UserUI(self)
        self.user_ui.grid(row=1, column=0)

        # Center StrategyUI in the notebook frame
        f_strategy_ui = ttk.Frame(tab_control)
        f_strategy_ui.pack(fill=tkinter.BOTH, expand=1)
        self.strategy_ui = StrategyUI(f_strategy_ui, self.gui_config)
        self.strategy_ui.place(anchor=tkinter.CENTER, in_=f_strategy_ui,
                               relx=.5, rely=.5)

        # Center TelemetryUI in the notebook frame
        f_telemetry_ui = ttk.Frame(tab_control)
        f_telemetry_ui.pack(fill=tkinter.BOTH, expand=1)
        self.telemetry_ui = TelemetryUI(f_telemetry_ui)
        self.telemetry_ui.place(anchor=tkinter.CENTER, in_=f_telemetry_ui,
                                relx=.5, rely=.5)

        self.tyre_graph = TyreGraph(tab_control, self.gui_config)
        self.tyre_graph.pack(fill=tkinter.BOTH, expand=1)

        self.prev_lap_graph = PrevLapsGraph(tab_control, self.gui_config)
        self.prev_lap_graph.pack(fill=tkinter.BOTH, expand=1)

        tab_control.add(f_strategy_ui, text="Strategy")
        tab_control.add(f_telemetry_ui, text="Telemetry")
        tab_control.add(self.tyre_graph, text="Pressures")
        tab_control.add(self.prev_lap_graph, text="Previous Laps")

        self.last_time = time.time()
        self.min_delta = 0.1

        self.client_loop()

        self.eval('tk::PlaceWindow . center')
        self.mainloop()

        print("APP: Main UI shutdown")

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

                self.tyre_graph.update_data(telemetry)

            elif event_type == NetworkQueue.UpdateUsers:

                user_update = self.client_queue_out.get()
                nb_users = user_update[0]
                self.user_ui.reset()
                self.strategy_ui.reset_drivers()

                index = 1
                for _ in range(nb_users):

                    lenght = user_update[index]
                    index += 1
                    name = user_update[index:index+lenght].decode("utf-8")
                    index += lenght
                    driverID = struct.unpack("!i",
                                             user_update[index:index+4])[0]

                    index += 4
                    self.user_ui.add_user(name, driverID)
                    self.strategy_ui.add_driver(name, driverID)

        if self.telemetry_ui.driver_swap or self.user_ui.active_user is None:

            if self.telemetry_ui.current_driver is not None:
                self.user_ui.set_active(self.telemetry_ui.current_driver)
                self.telemetry_ui.driver_swap = False
                self.strategy_ui.set_driver(self.telemetry_ui.current_driver)

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
            name = asm_data.Static.player_name.split("\x00")[0]
            surname = asm_data.Static.player_surname.split("\x00")[0]
            driver = f"{name} {surname}"

            telemetry_data = Telemetry(
                driver,
                asm_data.Graphics.completed_lap,
                asm_data.Physics.fuel,
                asm_data.Graphics.fuel_per_lap,
                asm_data.Graphics.fuel_estimated_laps,
                asm_data.Physics.wheel_pressure,
                asm_data.Physics.tyre_core_temp,
                asm_data.Physics.brake_temp,
                asm_data.Physics.pad_life,
                asm_data.Physics.disc_life,
                asm_data.Graphics.current_time,
                asm_data.Graphics.best_time,
                asm_data.Graphics.last_time,
                asm_data.Graphics.is_in_pit,
                asm_data.Graphics.is_in_pit_lane,
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

        self.c_loop_id = self.after(10, self.client_loop)

    def open_connection_window(self, as_server: bool = False) -> None:

        self.connection_window = ConnectionWindow(self, as_server)

    def connect_to_server(self, credits: Credidentials) -> Tuple[bool, str]:

        self.client = ClientInstance(credits, self.client_queue_in,
                                     self.client_queue_out)

        succes, msg = self.client.connect()
        if succes:
            self.connected(True)

        else:
            self.client = None

        return (succes, msg)

    def as_server(self, credis: Credidentials) -> Tuple[bool, str]:

        self.server = ServerInstance(credis.tcp_port, credis.udp_port)

        if self.server.error is None:
            succes, msg = self.connect_to_server(credis)

            if succes:
                self.connected(True)

            return succes, msg

        else:
            error = self.server.error
            self.server = None

            return False, error

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
        self.tyre_graph.reset()

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

        self.after_cancel(self.c_loop_id)
        self.strategy_ui.close()
        self.tyre_graph.close()
        self.prev_lap_graph.close()

        self.disconnect()

        self.destroy()


def main():

    App()


if __name__ == "__main__":

    main()
