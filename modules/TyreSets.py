from __future__ import annotations

import json
import pathlib
import struct
import time
import tkinter
from dataclasses import dataclass
from tkinter import ttk
from typing import ClassVar, List

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

DUMP_FILE = "swap_dump_carjson.json"
DIMP_FOLDER = "Documents/Assetto Corsa Competizione/Debug"


class TyreSets(ttk.Frame):

    def __init__(self, root, config: dict) -> None:

        ttk.Frame.__init__(self, master=root)

        self.path = pathlib.Path("./test")
        # self.path = pathlib.Path(
        #     "C:/Users/ryanr/Documents/Assetto Corsa Competizione/Debug")

        self.updated = False
        self.tyres_data: List[TyresSetData] = []
        self._read_dump_file(self.path / DUMP_FILE)

        self.no_spam_timer = 0

        self.tyreFL_O = tkinter.DoubleVar()
        self.tyreFL_M = tkinter.DoubleVar()
        self.tyreFL_I = tkinter.DoubleVar()
        self.tyreFL_grain = tkinter.DoubleVar()
        self.tyreFL_blister = tkinter.DoubleVar()
        self.tyreFL_flatspot = tkinter.DoubleVar()
        self.tyreFL_marble = tkinter.DoubleVar()

        self.tyreFR_I = tkinter.DoubleVar()
        self.tyreFR_M = tkinter.DoubleVar()
        self.tyreFR_O = tkinter.DoubleVar()
        self.tyreFR_grain = tkinter.DoubleVar()
        self.tyreFR_blister = tkinter.DoubleVar()
        self.tyreFR_flatspot = tkinter.DoubleVar()
        self.tyreFR_marble = tkinter.DoubleVar()

        self.tyreRL_O = tkinter.DoubleVar()
        self.tyreRL_M = tkinter.DoubleVar()
        self.tyreRL_I = tkinter.DoubleVar()
        self.tyreRL_grain = tkinter.DoubleVar()
        self.tyreRL_blister = tkinter.DoubleVar()
        self.tyreRL_flatspot = tkinter.DoubleVar()
        self.tyreRL_marble = tkinter.DoubleVar()

        self.tyreRR_I = tkinter.DoubleVar()
        self.tyreRR_M = tkinter.DoubleVar()
        self.tyreRR_O = tkinter.DoubleVar()
        self.tyreRR_grain = tkinter.DoubleVar()
        self.tyreRR_blister = tkinter.DoubleVar()
        self.tyreRR_flatspot = tkinter.DoubleVar()
        self.tyreRR_marble = tkinter.DoubleVar()

        self._build_UI()

        self.fs_event_handler = FileSystemEventHandler()
        self.fs_event_handler.on_modified = self._file_modified

        self.observer = Observer()
        self.observer.schedule(self.fs_event_handler,
                               self.path, recursive=False)

        self.observer.start()

    def _build_UI(self) -> None:

        tyre_set_l = ttk.Label(self, text="Tyre set: ")
        tyre_set_l.grid(row=0, column=0)

        self.tyre_set_cb = ttk.Combobox(self, values=[i for i in range(1, 51)],
                                        state="readonly")
        self.tyre_set_cb.grid(row=0, column=1)
        self.tyre_set_cb.bind("<<ComboboxSelected>>", self._show_tyre_set_info)

        tyreFL_f = ttk.Frame(self, padding=10)
        tyreFL_f.grid(row=1, column=0)
        tyreFL_l = ttk.Label(tyreFL_f, text="Front left")
        tyreFL_l.grid(row=0, column=1, columnspan=3)

        tyreFL_I = ttk.Label(tyreFL_f, text="I")
        tyreFL_I.grid(row=1, column=3)
        tyreFL_M = ttk.Label(tyreFL_f, text="M")
        tyreFL_M.grid(row=1, column=2)
        tyreFL_O = ttk.Label(tyreFL_f, text="O")
        tyreFL_O.grid(row=1, column=1)

        tyreFL_tread_l = ttk.Label(tyreFL_f, text="Tread (mm)")
        tyreFL_tread_l.grid(row=2, column=0)

        tyreFL_I_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_I)
        tyreFL_I_l.grid(row=2, column=1)
        tyreFL_M_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_M)
        tyreFL_M_l.grid(row=2, column=2)
        tyreFL_O_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_O)
        tyreFL_O_l.grid(row=2, column=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Grain (%)")
        tyreFL_grain.grid(row=3, column=0)

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_grain)
        tyreFL_grain_l.grid(row=3, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Blister (%)")
        tyreFL_grain.grid(row=4, column=0)

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_blister)
        tyreFL_grain_l.grid(row=4, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="FlatSpot (%)")
        tyreFL_grain.grid(row=5, column=0)

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_flatspot)
        tyreFL_grain_l.grid(row=5, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Marble (%)")
        tyreFL_grain.grid(row=6, column=0)

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_marble)
        tyreFL_grain_l.grid(row=6, column=1, columnspan=3)

        tyreFR_f = ttk.Frame(self, padding=10)
        tyreFR_f.grid(row=1, column=1)
        tyreFR_l = ttk.Label(tyreFR_f, text="Front right")
        tyreFR_l.grid(row=0, column=0, columnspan=3)

        tyreFR_I = ttk.Label(tyreFR_f, text="I")
        tyreFR_I.grid(row=1, column=0)
        tyreFR_M = ttk.Label(tyreFR_f, text="M")
        tyreFR_M.grid(row=1, column=1)
        tyreFR_O = ttk.Label(tyreFR_f, text="O")
        tyreFR_O.grid(row=1, column=2)

        tyreFR_tread_l = ttk.Label(tyreFR_f, text="Tread (mm)")
        tyreFR_tread_l.grid(row=2, column=4)

        tyreFR_I_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_I)
        tyreFR_I_l.grid(row=2, column=2)
        tyreFR_M_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_M)
        tyreFR_M_l.grid(row=2, column=1)
        tyreFR_O_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_O)
        tyreFR_O_l.grid(row=2, column=0)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Grain (%)")
        tyreFR_grain.grid(row=3, column=4)

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_grain)
        tyreFR_grain_l.grid(row=3, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Blister (%)")
        tyreFR_grain.grid(row=4, column=4)

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_blister)
        tyreFR_grain_l.grid(row=4, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="FlatSpot (%)")
        tyreFR_grain.grid(row=5, column=4)

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_flatspot)
        tyreFR_grain_l.grid(row=5, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Marble (%)")
        tyreFR_grain.grid(row=6, column=4)

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_marble)
        tyreFR_grain_l.grid(row=6, column=0, columnspan=3)

        tyreRL_f = ttk.Frame(self, padding=10)
        tyreRL_f.grid(row=2, column=0)
        tyreRL_l = ttk.Label(tyreRL_f, text="Rear left")
        tyreRL_l.grid(row=0, column=1, columnspan=3)

        tyreRL_I = ttk.Label(tyreRL_f, text="I")
        tyreRL_I.grid(row=1, column=3)
        tyreRL_M = ttk.Label(tyreRL_f, text="M")
        tyreRL_M.grid(row=1, column=2)
        tyreRL_O = ttk.Label(tyreRL_f, text="O")
        tyreRL_O.grid(row=1, column=1)

        tyreRL_tread_l = ttk.Label(tyreRL_f, text="Tread (mm)")
        tyreRL_tread_l.grid(row=2, column=0)

        tyreRL_I_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_I)
        tyreRL_I_l.grid(row=2, column=1)
        tyreRL_M_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_M)
        tyreRL_M_l.grid(row=2, column=2)
        tyreRL_O_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_O)
        tyreRL_O_l.grid(row=2, column=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Grain (%)")
        tyreRL_grain.grid(row=3, column=0)

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_grain)
        tyreRL_grain_l.grid(row=3, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Blister (%)")
        tyreRL_grain.grid(row=4, column=0)

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_blister)
        tyreRL_grain_l.grid(row=4, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="FlatSpot (%)")
        tyreRL_grain.grid(row=5, column=0)

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_flatspot)
        tyreRL_grain_l.grid(row=5, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Marble (%)")
        tyreRL_grain.grid(row=6, column=0)

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_marble)
        tyreRL_grain_l.grid(row=6, column=1, columnspan=3)

        tyreRR_f = ttk.Frame(self, padding=10)
        tyreRR_f.grid(row=2, column=1)
        tyreRR_l = ttk.Label(tyreRR_f, text="Rear right")
        tyreRR_l.grid(row=0, column=0, columnspan=3)

        tyreRR_I = ttk.Label(tyreRR_f, text="I")
        tyreRR_I.grid(row=1, column=0)
        tyreRR_M = ttk.Label(tyreRR_f, text="M")
        tyreRR_M.grid(row=1, column=1)
        tyreRR_O = ttk.Label(tyreRR_f, text="O")
        tyreRR_O.grid(row=1, column=2)

        tyreRR_tread_l = ttk.Label(tyreRR_f, text="Tread (mm)")
        tyreRR_tread_l.grid(row=2, column=4)

        tyreRR_I_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_I)
        tyreRR_I_l.grid(row=2, column=2)
        tyreRR_M_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_M)
        tyreRR_M_l.grid(row=2, column=1)
        tyreRR_O_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_O)
        tyreRR_O_l.grid(row=2, column=0)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Grain (%)")
        tyreRR_grain.grid(row=3, column=4)

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_grain)
        tyreRR_grain_l.grid(row=3, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Blister (%)")
        tyreRR_grain.grid(row=4, column=4)

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_blister)
        tyreRR_grain_l.grid(row=4, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="FlatSpot (%)")
        tyreRR_grain.grid(row=5, column=4)

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_flatspot)
        tyreRR_grain_l.grid(row=5, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Marble (%)")
        tyreRR_grain.grid(row=6, column=4)

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_marble)
        tyreRR_grain_l.grid(row=6, column=0, columnspan=3)

    def _show_tyre_set_info(self, event) -> None:

        selected_item = self.tyre_set_cb.current()

        tyre_data = self.tyres_data[selected_item]

        self.tyreFL_O.set(round(tyre_data.FL.treadIMO[2], 2))
        self.tyreFL_M.set(round(tyre_data.FL.treadIMO[1], 2))
        self.tyreFL_I.set(round(tyre_data.FL.treadIMO[0], 2))
        self.tyreFL_grain.set(round(tyre_data.FL.grain, 2))
        self.tyreFL_blister.set(round(tyre_data.FL.blister, 2))
        self.tyreFL_flatspot.set(round(tyre_data.FL.flatspot, 2))
        self.tyreFL_marble.set(round(tyre_data.FL.marble, 2))

        self.tyreFR_O.set(round(tyre_data.FR.treadIMO[2], 2))
        self.tyreFR_M.set(round(tyre_data.FR.treadIMO[1], 2))
        self.tyreFR_I.set(round(tyre_data.FR.treadIMO[0], 2))
        self.tyreFR_grain.set(round(tyre_data.FR.grain, 2))
        self.tyreFR_blister.set(round(tyre_data.FR.blister, 2))
        self.tyreFR_flatspot.set(round(tyre_data.FR.flatspot, 2))
        self.tyreFR_marble.set(round(tyre_data.FR.marble, 2))

        self.tyreRL_O.set(round(tyre_data.RL.treadIMO[2], 2))
        self.tyreRL_M.set(round(tyre_data.RL.treadIMO[1], 2))
        self.tyreRL_I.set(round(tyre_data.RL.treadIMO[0], 2))
        self.tyreRL_grain.set(round(tyre_data.RL.grain, 2))
        self.tyreRL_blister.set(round(tyre_data.RL.blister, 2))
        self.tyreRL_flatspot.set(round(tyre_data.RL.flatspot, 2))
        self.tyreRL_marble.set(round(tyre_data.RL.marble, 2))

        self.tyreRR_O.set(round(tyre_data.RR.treadIMO[2], 2))
        self.tyreRR_M.set(round(tyre_data.RR.treadIMO[1], 2))
        self.tyreRR_I.set(round(tyre_data.RR.treadIMO[0], 2))
        self.tyreRR_grain.set(round(tyre_data.RR.grain, 2))
        self.tyreRR_blister.set(round(tyre_data.RR.blister, 2))
        self.tyreRR_flatspot.set(round(tyre_data.RR.flatspot, 2))
        self.tyreRR_marble.set(round(tyre_data.RR.marble, 2))

    def _file_modified(self, event: FileModifiedEvent) -> None:

        print(f"file {event.src_path} modified")

        if (event.src_path.split("\\")[-1] == DUMP_FILE
                and self.no_spam_timer + 1 < time.time()):
            self.no_spam_timer = time.time()

            self._read_dump_file(event.src_path)
            self.updated = True

    def _read_dump_file(self, path: str) -> None:

        self.tyres_data.clear()
        tyre_set_data = None

        try:
            with open(path) as fp:
                tyre_set_data = json.load(fp)

        except FileExistsError as msg:
            return

        for tyre_set in tyre_set_data["tyreSets"]:

            tyre_set_temp = []
            for index, tyre in enumerate(tyre_set["wearStatus"]):

                if index % 2 == 0:
                    wear = tyre["treadMM"]

                else:
                    wear = list(reversed(tyre["treadMM"]))

                tyre_set_temp.append(TyreSetData(wear, tyre["grain"],
                                                 tyre["blister"],
                                                 tyre["marblesLevel"],
                                                 tyre["flatSpot"]))

            self.tyres_data.append(TyresSetData(*tyre_set_temp))

    def close(self) -> None:

        self.observer.stop()
        self.observer.join()


@dataclass
class TyreSetData:

    treadIMO: List[float]
    grain: float
    blister: float
    marble: float
    flatspot: float

    byte_format: ClassVar[str] = ("! 3f 4f")
    byte_size: ClassVar[int] = struct.calcsize(byte_format)

    def to_bytes(self) -> bytes:

        buffer = [
            struct.pack("!3f", *self.treadIMO),
            struct.pack("!f", self.grain),
            struct.pack("!f", self.blister),
            struct.pack("!f", self.marble),
            struct.pack("!f", self.flatspot),
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> TyreSetData:

        raw_data = struct.unpack(cls.byte_format, data)

        return TyreSetData(
            raw_data[0:3],
            raw_data[3],
            raw_data[4],
            raw_data[5],
            raw_data[6],
        )


@dataclass
class TyresSetData:

    FL: TyreSetData
    FR: TyreSetData
    RL: TyreSetData
    RR: TyreSetData

    def to_bytes(self) -> bytes:

        buffer = [
            self.FL.to_bytes(),
            self.FR.to_bytes(),
            self.RL.to_bytes(),
            self.RR.to_bytes(),
        ]

        return b"".join(buffer)

    @classmethod
    def from_bytes(cls, data: bytes) -> TyresSetData:

        temp = []
        byte_index = 0
        for _ in range(4):

            temp.append(TyreSetData.from_bytes(
                data[byte_index:byte_index+TyreSetData.byte_size]))

            byte_index += TyreSetData.byte_size

        return TyresSetData(*temp)
