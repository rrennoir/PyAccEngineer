from __future__ import annotations

import ipaddress
import json
import logging
import sys
import time
import tkinter
from dataclasses import astuple
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional, Tuple

from twisted.internet import reactor, task, tksupport

from modules.Client import ClientInstance
from modules.Common import (CarInfo, Credidentials, DataQueue, NetData,
                            NetworkQueue, PitStop)
from modules.DriverInputs import DriverInputs
from modules.Server import ServerInstance
from modules.Strategy import StrategyUI
from modules.Telemetry import Telemetry, TelemetryRT, TelemetryUI
from modules.TyreGraph import PrevLapsGraph, TyreGraph
from modules.Users import UserUI

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s.%(msecs)03d | %(name)s | %(message)s",
                    datefmt="%H:%M:%S")


_VERSION_ = "1.5.4"


class ConnectionPage(ttk.Frame):

    def __init__(self, app: App, root):
        ttk.Frame.__init__(self, master=root)

        self.main_app = app
        self.connection_path = "./Config/connection.json"

        self.is_connected = None
        self.connection_msg = ""
        self.credis = None
        self.is_connected_loop = task.LoopingCall(self.check_connection)

        self.credidentials = None
        key_check = ("saved_ip", "tcp_port", "udp_port", "username",
                     "driverID")

        logging.info(f"Loading {self.connection_path}")
        if Path(self.connection_path).is_file():
            fp = open(self.connection_path, "r")

            try:
                self.credidentials = json.load(fp)

                if (type(self.credidentials) is not dict or
                        tuple(self.credidentials.keys()) != key_check):

                    logging.info(f"Invalid connection.json file")
                    self.credidentials = None

            except json.JSONDecodeError as msg:
                self.credidentials = None
                logging.info(f"JSON Error: {msg}")

            fp.close()

        else:
            logging.info(f"{self.connection_path} not found")
            self.credidentials = None

        self.as_server = False

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

        if self.credidentials is None:
            self.cb_ip = ttk.Combobox(self.f_connection_info, width=30,
                                      values=[])

        else:
            self.cb_ip = ttk.Combobox(self.f_connection_info, width=30,
                                      values=self.credidentials["saved_ip"])
        self.cb_ip.grid(row=0, column=1, padx=5, pady=2)

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

            self.e_tcp_port.insert(tkinter.END, self.credidentials["tcp_port"])
            self.e_udp_port.insert(tkinter.END, self.credidentials["udp_port"])
            self.e_username.insert(tkinter.END, self.credidentials["username"])
            self.e_driverID.insert(tkinter.END, self.credidentials["driverID"])

        else:
            self.e_tcp_port.insert(tkinter.END, "4269")
            self.e_udp_port.insert(tkinter.END, "4270")

        logging.info("Displaying connection window")

    def set_as_server(self) -> None:

        self.cb_ip.set("127.0.0.1")
        self.cb_ip["state"] = "disabled"
        self.as_server = True

    def set_as_client(self) -> None:

        self.cb_ip.set("")
        self.cb_ip["state"] = "normal"
        self.as_server = False

    def connect(self) -> None:

        logging.info("Connect button pressed")

        self.b_connect.config(state="disabled")

        error_message = ""

        try:
            ipaddress.ip_address(self.cb_ip.get())

        except ValueError:
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

            logging.info("No error in the credidentials")

            self.credits = Credidentials(
                ip=self.cb_ip.get(),
                tcp_port=int(self.e_tcp_port.get()),
                udp_port=int(self.e_udp_port.get()),
                username=self.e_username.get(),
                driverID=int(self.e_driverID.get())
            )

            if self.as_server:
                self.main_app.as_server(self.credits)

            else:
                self.main_app.connect_to_server(self.credits)

            self.is_connected_loop.start(0.1)
            logging.info("Waiting for connection confirmation")

        else:
            logging.info(f"Error: {error_message}")
            messagebox.showerror("Error", error_message)
            self.b_connect.config(state="normal")

    def check_connection(self) -> None:

        if self.is_connected is None:
            return

        if self.is_connected:
            logging.info("Connected")
            self.save_credidentials(self.credits)

        else:
            logging.info("Connection failed")
            messagebox.showerror("Error", self.connection_msg)

        self.b_connect.config(state="normal")
        self.is_connected = None
        self.is_connected_loop.stop()

    def connected(self, succes: bool, error: str) -> None:

        self.is_connected = succes
        self.connection_msg = error

    def save_credidentials(self, credits: Credidentials) -> None:

        logging.info("Saving credidentials")

        if self.credidentials is None:
            saved_ip = [self.cb_ip.get()]

        elif credits.ip not in self.credidentials["saved_ip"]:

            saved_ip = [self.cb_ip.get(), *self.credidentials["saved_ip"]]

            if len(saved_ip) > 5:
                self.credidentials["saved_ip"].pop()

        else:
            saved_ip = self.credidentials["saved_ip"]

        with open(self.connection_path, "w") as fp:

            connection = {
                "saved_ip": saved_ip,
                "tcp_port": credits.tcp_port,
                "udp_port": credits.udp_port,
                "username": credits.username,
                "driverID": credits.driverID,
            }
            json.dump(connection, fp, indent=4)


class App(tkinter.Tk):

    def __init__(self) -> None:

        tkinter.Tk.__init__(self)

        tksupport.install(self)

        self.geometry("830x580+0+0")

        try:
            with open("./Config/gui.json", "r") as fp:

                self.gui_config = json.load(fp)

        except FileNotFoundError:
            print("APP: './Config/gui.json' not found.")
            return

        self.font = (self.gui_config["font"], self.gui_config["font_size"])

        if self.gui_config["icon"]:
            self.iconbitmap(self.gui_config["icon_path"])

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
        app_style.configure("TelemetryGrid.TFrame", background="#000000")
        app_style.configure("PressureInfo.TFrame", background="#000000")
        app_style.configure("TEntry", foreground="#000000")

        self.title(f"PyAccEngineer {_VERSION_}")
        self.config(bg="Grey")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Networking
        self.is_connected = False
        self.client: Optional[ClientInstance] = None
        self.server: Optional[ServerInstance] = None
        self.net_queue = DataQueue([], [])

        self.menu_bar = tkinter.Menu(self)
        self.menu_bar.add_command(label="Connect",
                                  command=self.show_connection_page,
                                  font=self.font)

        self.menu_bar.add_command(label="As Server",
                                  command=lambda: self.show_connection_page(
                                      True), font=self.font)
        self.menu_bar.add_command(label="Disconnect",
                                  command=self.disconnect, state="disabled",
                                  font=self.font)

        self.config(menu=self.menu_bar)

        self.main_canvas = tkinter.Canvas(self)
        self.main_frame = ttk.Frame(self)

        self.hsb = ttk.Scrollbar(self)
        self.vsb = ttk.Scrollbar(self)

        self.main_canvas.config(xscrollcommand=self.hsb.set,
                                yscrollcommand=self.vsb.set,
                                highlightthickness=0)

        self.hsb.config(orient=tkinter.HORIZONTAL,
                        command=self.main_canvas.xview)
        self.vsb.config(orient=tkinter.VERTICAL,
                        command=self.main_canvas.yview)

        self.hsb.pack(fill=tkinter.X, side=tkinter.BOTTOM,
                      expand=tkinter.FALSE)
        self.vsb.pack(fill=tkinter.Y, side=tkinter.RIGHT,
                      expand=tkinter.FALSE)

        self.main_canvas.pack(fill=tkinter.BOTH, side=tkinter.LEFT,
                              expand=tkinter.TRUE)

        self.main_canvas.create_window(0, 0, window=self.main_frame,
                                       anchor=tkinter.NW)

        self.user_ui = UserUI(self.main_frame)
        self.user_ui.grid(row=1, column=0)

        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.grid(row=0, column=0, pady=3)

        self.f_connection_ui = ttk.Frame(self.tab_control)
        self.f_connection_ui.pack(fill=tkinter.BOTH, expand=1)
        self.connection_page = ConnectionPage(self, self.f_connection_ui)
        self.connection_page.place(anchor=tkinter.CENTER,
                                   in_=self.f_connection_ui,
                                   relx=.5, rely=.5)

        # Center StrategyUI in the notebook frame
        f_strategy_ui = ttk.Frame(self.tab_control)
        f_strategy_ui.pack(fill=tkinter.BOTH, expand=1)
        self.strategy_ui = StrategyUI(f_strategy_ui, self.gui_config)
        self.strategy_ui.place(anchor=tkinter.CENTER, in_=f_strategy_ui,
                               relx=.5, rely=.5)

        self.telemetry_ui = TelemetryUI(self.tab_control)
        self.telemetry_ui.pack(fill=tkinter.BOTH, side=tkinter.LEFT,
                               expand=tkinter.TRUE)

        self.driver_inputs = DriverInputs(self.tab_control)
        self.driver_inputs.pack(fill=tkinter.BOTH, side=tkinter.LEFT,
                                expand=tkinter.TRUE)

        self.tyre_graph = TyreGraph(self.tab_control, self.gui_config)
        self.tyre_graph.pack(fill=tkinter.BOTH, expand=1)

        self.prev_lap_graph = PrevLapsGraph(self.tab_control, self.gui_config)
        self.prev_lap_graph.pack(fill=tkinter.BOTH, expand=1)

        self.tab_control.add(self.f_connection_ui, text="Connection")
        self.tab_control.add(f_strategy_ui, text="Strategy")
        self.tab_control.add(self.telemetry_ui, text="Telemetry")
        self.tab_control.add(self.driver_inputs, text="Driver Inputs")
        self.tab_control.add(self.tyre_graph, text="Pressures")
        self.tab_control.add(self.prev_lap_graph, text="Previous Laps")

        self.tab_control.hide(0)

        self.last_time = time.time()
        self.rt_last_time = time.time()
        self.rt_min_delta = self.gui_config["driver_input_speed"]
        self.min_delta = 0.5
        self.last_telemetry = time.time()
        self.telemetry_timeout = 2

        logging.info("Main UI created.")

        self.client_loopCall = task.LoopingCall(self.client_loop)
        self.client_loopCall.start(0.01)

        self.eval('tk::PlaceWindow . center')
        self.updateScrollRegion()

    def updateScrollRegion(self):

        self.main_canvas.update_idletasks()
        self.main_canvas.config(scrollregion=self.main_frame.bbox())

    def client_loop(self) -> None:

        selected_tab_name = self.tab_control.tab(self.tab_control.select(),
                                                 "text")
        if selected_tab_name == "Driver Inputs":
            if not self.driver_inputs.is_animating:
                self.driver_inputs.start_animation()

        else:
            if self.driver_inputs.is_animating:
                self.driver_inputs.stop_animation()

        if selected_tab_name == "Pressures":
            if not self.tyre_graph.is_animating:
                self.tyre_graph.start_animation()

        else:
            if self.tyre_graph.is_animating:
                self.tyre_graph.stop_animation()

        for element in self.net_queue.q_out:

            if element.data_type == NetworkQueue.ConnectionReply:

                logging.info("Received Connection reply for server")

                succes = bool(element.data[0])
                msg_lenght = element.data[1]
                msg = element.data[2:2 + msg_lenght]

                self.connection_page.connected(succes, msg)
                self.mb_connected(succes)
                self.is_connected = succes
                if not succes:
                    self.client.close()

            elif element.data_type == NetworkQueue.ServerData:

                server_data = CarInfo.from_bytes(element.data)
                is_first_update = self.strategy_ui.server_data is None
                self.strategy_ui.server_data = server_data

                if is_first_update:
                    self.strategy_ui.update_values()

            elif element.data_type == NetworkQueue.Strategy:

                logging.info("Received: Strategy")
                self.strategy_ui.b_set_strat.config(state="disabled")
                asm_data = self.strategy_ui.asm.read_shared_memory()
                if asm_data is not None:

                    pit_stop = PitStop.from_bytes(element.data)
                    self.strategy_ui.apply_strategy(pit_stop)

            elif element.data_type == NetworkQueue.StrategyDone:

                logging.info("Received: Strategy Done")

                self.strategy_ui.b_set_strat.config(state="normal")
                self.strategy_ui.update_values()

            elif element.data_type == NetworkQueue.Telemetry:

                telemetry = Telemetry.from_bytes(element.data)
                self.telemetry_ui.update_values(telemetry)
                self.tyre_graph.update_data(telemetry)
                self.strategy_ui.updade_telemetry_data(telemetry)

                self.driver_inputs.update_lap(telemetry.lap)

                if not self.strategy_ui.is_driver_active:
                    self.strategy_ui.is_driver_active = True
                    self.user_ui.set_active(telemetry.driver)

                self.last_telemetry = time.time()

            elif element.data_type == NetworkQueue.TelemetryRT:

                telemetry = TelemetryRT.from_bytes(element.data)
                self.driver_inputs.update_values(telemetry)

            elif element.data_type == NetworkQueue.UpdateUsers:

                logging.info("Received user update")

                user_update = element.data
                nb_users = user_update[0]
                self.user_ui.reset()
                self.strategy_ui.reset_drivers()

                index = 1
                for _ in range(nb_users):

                    lenght = user_update[index]
                    index += 1
                    name = user_update[index:index+lenght].decode("utf-8")
                    index += lenght
                    driverID = user_update[index]
                    index += 1

                    self.user_ui.add_user(name, driverID)
                    self.strategy_ui.add_driver(name, driverID)

        self.net_queue.q_out.clear()

        if not self.is_connected:
            return

        if not self.strategy_ui.is_connected:
            self.strategy_ui.is_connected = True

        if self.telemetry_ui.driver_swap or self.user_ui.active_user is None:

            if self.telemetry_ui.current_driver is not None:
                self.user_ui.set_active(self.telemetry_ui.current_driver)
                self.telemetry_ui.driver_swap = False
                self.strategy_ui.set_driver(self.telemetry_ui.current_driver)

        rt_delta_time = time.time() - self.rt_last_time
        delta_time = time.time() - self.last_time

        if (self.strategy_ui.is_driver_active and
                time.time() > self.last_telemetry + self.telemetry_timeout):

            logging.info("Telemetry timeout, not received "
                         f"telemetry for {self.telemetry_timeout}s")
            self.strategy_ui.is_driver_active = False
            self.user_ui.remove_active()
            self.telemetry_ui.current_driver = None

        asm_data = self.strategy_ui.asm.read_shared_memory()
        if asm_data is not None:

            if self.rt_min_delta < rt_delta_time:

                self.rt_last_time = time.time()

                telemetry_rt = TelemetryRT(
                    asm_data.Physics.gas,
                    asm_data.Physics.brake,
                    asm_data.Physics.steer_angle,
                    asm_data.Physics.gear,
                    asm_data.Physics.speed_kmh
                )

                self.net_queue.q_in.append(NetData(NetworkQueue.TelemetryRT,
                                           telemetry_rt.to_bytes()))

            if self.min_delta < delta_time:

                self.last_time = time.time()

                infos = CarInfo(
                    *astuple(asm_data.Graphics.mfd_tyre_pressure),
                    asm_data.Graphics.mfd_fuel_to_add,
                    asm_data.Static.max_fuel,
                    asm_data.Graphics.mfd_tyre_set)

                self.net_queue.q_in.append(NetData(NetworkQueue.CarInfoData,
                                           infos.to_bytes()))

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
                    asm_data.Physics.pad_life,
                    asm_data.Physics.disc_life,
                    asm_data.Graphics.current_time,
                    asm_data.Graphics.best_time,
                    asm_data.Graphics.last_time,
                    asm_data.Graphics.is_in_pit,
                    asm_data.Graphics.is_in_pit_lane,
                    asm_data.Graphics.session_type,
                    asm_data.Graphics.driver_stint_time_left,
                    asm_data.Physics.wheel_pressure,
                    asm_data.Physics.tyre_core_temp,
                    asm_data.Physics.brake_temp,
                    asm_data.Graphics.rain_tyres,
                    asm_data.Graphics.session_time_left,
                    asm_data.Graphics.track_grip_status,
                    asm_data.Physics.front_brake_compound,
                    asm_data.Physics.rear_brake_compound,
                    asm_data.Physics.car_damage,
                    asm_data.Graphics.rain_intensity,
                    asm_data.Physics.suspension_damage,
                    asm_data.Graphics.current_sector_index,
                    asm_data.Graphics.last_sector_time,
                    asm_data.Graphics.is_valid_lap,
                    asm_data.Physics.air_temp,
                    asm_data.Physics.road_temp,
                    asm_data.Graphics.wind_speed,
                    asm_data.Graphics.driver_stint_total_time_left,
                )

                self.net_queue.q_in.append(NetData(NetworkQueue.Telemetry,
                                           telemetry_data.to_bytes()))

        if self.strategy_ui.strategy is not None:

            logging.info("Sending strategy")
            strategy = self.strategy_ui.strategy
            self.strategy_ui.strategy = None
            self.net_queue.q_in.append(NetData(NetworkQueue.StrategySet,
                                               strategy.to_bytes()))

        if self.strategy_ui.strategy_ok:

            logging.info("Send strategy Done")
            self.net_queue.q_in.append(NetData(NetworkQueue.StrategyDone))
            self.strategy_ui.strategy_ok = False

    def show_connection_page(self, as_server: bool = False) -> None:

        logging.info("Show connection page")

        self.tab_control.add(self.f_connection_ui, text="Connection")
        self.tab_control.select(0)
        if as_server:
            self.connection_page.set_as_server()

        else:
            self.connection_page.set_as_client()

    def connect_to_server(self, credits: Credidentials) -> None:

        logging.info("Creating a ClientInstance connecting"
                     f" to {credits.ip}:{credits.tcp_port}")
        self.client = ClientInstance(credits, self.net_queue)

    def as_server(self, credis: Credidentials) -> Tuple[bool, str]:

        logging.info("Creating a ServerInstance")
        self.server = ServerInstance(credis.tcp_port, credis.udp_port)

        self.connect_to_server(credis)

    def mb_connected(self, state: bool) -> None:

        if state:
            self.menu_bar.entryconfig("Disconnect", state="active")
            self.menu_bar.entryconfig("Connect", state="disabled")
            self.menu_bar.entryconfig("As Server", state="disabled")
            self.tab_control.hide(0)

        else:
            self.menu_bar.entryconfig("Disconnect", state="disabled")
            self.menu_bar.entryconfig("Connect", state="active")
            self.menu_bar.entryconfig("As Server", state="active")

    def disconnect(self) -> None:

        logging.info("Disconnecting")

        self.stop_networking()
        self.mb_connected(False)

        self.strategy_ui.reset()
        self.user_ui.reset()
        self.tyre_graph.reset()

    def stop_networking(self) -> None:

        if self.is_connected:

            self.client.close()
            self.is_connected = False
            logging.info("Client stopped.")

        if self.server is not None:

            self.server.close()
            self.server = None
            logging.info("Server stopped.")

    def on_close(self) -> None:

        logging.info("Closing the app")

        self.strategy_ui.close()
        self.tyre_graph.close()
        self.prev_lap_graph.close()

        self.disconnect()

        self.client_loopCall.stop()

        tksupport.uninstall()

        reactor.stop()

        self.destroy()
        logging.info("App closed")


def create_gui() -> None:
    App()


def main():

    reactor.callLater(0, create_gui)
    reactor.run()


if __name__ == "__main__":

    main()
