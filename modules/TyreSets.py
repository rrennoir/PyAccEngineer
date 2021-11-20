from __future__ import annotations

import json
import os
import pathlib
import struct
import logging
import time
import tkinter
from dataclasses import dataclass
from tkinter import ttk
from typing import ClassVar, List
from idlelib.tooltip import Hovertip

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

DUMP_FILE = "swap_dump_carjson.json"
DUMP_FOLDER = os.path.expanduser(
    "~/Documents/Assetto Corsa Competizione/Debug")

logger = logging.getLogger(__name__)


class TyreSets(ttk.Frame):

    def __init__(self, root, config: dict) -> None:

        ttk.Frame.__init__(self, master=root, style="TelemetryGrid.TFrame")

        self.path = pathlib.Path(DUMP_FOLDER)

        self.path.mkdir(parents=True, exist_ok=True)

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

        selector_f = ttk.Frame(self, padding=(180, 0))
        selector_f.grid(row=0, column=0, columnspan=2)

        tyre_set_l = ttk.Label(selector_f, text="Tyre set: ", width=10,
                               anchor=tkinter.E)
        tyre_set_l.grid(row=0, column=0)

        self.tyre_set_cb = ttk.Combobox(selector_f,
                                        values=[i for i in range(1, 51)],
                                        state="readonly", width=10)
        self.tyre_set_cb.grid(row=0, column=1)
        self.tyre_set_cb.bind("<<ComboboxSelected>>", self._show_tyre_set_info)

        tyreFL_f = ttk.Frame(self, padding=10)
        tyreFL_f.grid(row=1, column=0, padx=2, pady=2)
        tyreFL_l = ttk.Label(tyreFL_f, text="Front left", width=16,
                             anchor=tkinter.CENTER)
        tyreFL_l.grid(row=0, column=1, columnspan=3)

        tyreFL_I = ttk.Label(tyreFL_f, text="I", width=5,
                             anchor=tkinter.CENTER)
        tyreFL_I.grid(row=1, column=3)
        tyreFL_M = ttk.Label(tyreFL_f, text="M", width=5,
                             anchor=tkinter.CENTER)
        tyreFL_M.grid(row=1, column=2)
        tyreFL_O = ttk.Label(tyreFL_f, text="O", width=5,
                             anchor=tkinter.CENTER)
        tyreFL_O.grid(row=1, column=1)

        tyreFL_tread_l = ttk.Label(tyreFL_f, text="Tread (mm)", width=12,
                                   anchor=tkinter.E)
        tyreFL_tread_l.grid(row=2, column=0, padx=(0, 10))

        tyreFL_I_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_I,
                               width=5, anchor=tkinter.CENTER)
        tyreFL_I_l.grid(row=2, column=1)
        tyreFL_M_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_M,
                               width=5, anchor=tkinter.CENTER)
        tyreFL_M_l.grid(row=2, column=2)
        tyreFL_O_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_O,
                               width=5, anchor=tkinter.CENTER)
        tyreFL_O_l.grid(row=2, column=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Grain (%)", width=12,
                                 anchor=tkinter.E)
        tyreFL_grain.grid(row=3, column=0, padx=(0, 10))

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_grain,
                                   width=16, anchor=tkinter.CENTER)
        tyreFL_grain_l.grid(row=3, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Blister (%)", width=12,
                                 anchor=tkinter.E)
        tyreFL_grain.grid(row=4, column=0, padx=(0, 10))

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_blister,
                                   width=16, anchor=tkinter.CENTER)
        tyreFL_grain_l.grid(row=4, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="FlatSpot (%)", width=12,
                                 anchor=tkinter.E)
        tyreFL_grain.grid(row=5, column=0, padx=(0, 10))

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_flatspot,
                                   width=16, anchor=tkinter.CENTER)
        tyreFL_grain_l.grid(row=5, column=1, columnspan=3)

        tyreFL_grain = ttk.Label(tyreFL_f, text="Marble (%)", width=12,
                                 anchor=tkinter.E)
        tyreFL_grain.grid(row=6, column=0, padx=(0, 10))

        tyreFL_grain_l = ttk.Label(tyreFL_f, textvariable=self.tyreFL_marble,
                                   width=16, anchor=tkinter.CENTER)
        tyreFL_grain_l.grid(row=6, column=1, columnspan=3)

        tyreFR_f = ttk.Frame(self, padding=10)
        tyreFR_f.grid(row=1, column=1, padx=2, pady=2)
        tyreFR_l = ttk.Label(tyreFR_f, text="Front right", width=16,
                             anchor=tkinter.CENTER)
        tyreFR_l.grid(row=0, column=0, columnspan=3)

        tyreFR_I = ttk.Label(tyreFR_f, text="I", width=5,
                             anchor=tkinter.CENTER)
        tyreFR_I.grid(row=1, column=0)
        tyreFR_M = ttk.Label(tyreFR_f, text="M", width=5,
                             anchor=tkinter.CENTER)
        tyreFR_M.grid(row=1, column=1)
        tyreFR_O = ttk.Label(tyreFR_f, text="O", width=5,
                             anchor=tkinter.CENTER)
        tyreFR_O.grid(row=1, column=2)

        tyreFR_tread_l = ttk.Label(tyreFR_f, text="Tread (mm)", width=12,
                                   anchor=tkinter.W)
        tyreFR_tread_l.grid(row=2, column=4, padx=(10, 0))

        tyreFR_I_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_I, width=5,
                               anchor=tkinter.CENTER)
        tyreFR_I_l.grid(row=2, column=2)
        tyreFR_M_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_M, width=5,
                               anchor=tkinter.CENTER)
        tyreFR_M_l.grid(row=2, column=1)
        tyreFR_O_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_O, width=5,
                               anchor=tkinter.CENTER)
        tyreFR_O_l.grid(row=2, column=0)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Grain (%)", width=12,
                                 anchor=tkinter.W)
        tyreFR_grain.grid(row=3, column=4, padx=(10, 0))

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_grain,
                                   width=16, anchor=tkinter.CENTER)
        tyreFR_grain_l.grid(row=3, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Blister (%)", width=12,
                                 anchor=tkinter.W)
        tyreFR_grain.grid(row=4, column=4, padx=(10, 0))

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_blister,
                                   width=16, anchor=tkinter.CENTER)
        tyreFR_grain_l.grid(row=4, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="FlatSpot (%)", width=12,
                                 anchor=tkinter.W)
        tyreFR_grain.grid(row=5, column=4, padx=(10, 0))

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_flatspot,
                                   width=16, anchor=tkinter.CENTER)
        tyreFR_grain_l.grid(row=5, column=0, columnspan=3)

        tyreFR_grain = ttk.Label(tyreFR_f, text="Marble (%)", width=12,
                                 anchor=tkinter.W)
        tyreFR_grain.grid(row=6, column=4, padx=(10, 0))

        tyreFR_grain_l = ttk.Label(tyreFR_f, textvariable=self.tyreFR_marble,
                                   width=16, anchor=tkinter.CENTER)
        tyreFR_grain_l.grid(row=6, column=0, columnspan=3)

        tyreRL_f = ttk.Frame(self, padding=10)
        tyreRL_f.grid(row=2, column=0, padx=2, pady=2)
        tyreRL_l = ttk.Label(tyreRL_f, text="Rear left", width=16,
                             anchor=tkinter.CENTER)
        tyreRL_l.grid(row=0, column=1, columnspan=3)

        tyreRL_I = ttk.Label(tyreRL_f, text="I", width=5,
                             anchor=tkinter.CENTER)
        tyreRL_I.grid(row=1, column=3)
        tyreRL_M = ttk.Label(tyreRL_f, text="M", width=5,
                             anchor=tkinter.CENTER)
        tyreRL_M.grid(row=1, column=2)
        tyreRL_O = ttk.Label(tyreRL_f, text="O", width=5,
                             anchor=tkinter.CENTER)
        tyreRL_O.grid(row=1, column=1)

        tyreRL_tread_l = ttk.Label(tyreRL_f, text="Tread (mm)", width=12,
                                   anchor=tkinter.E)
        tyreRL_tread_l.grid(row=2, column=0, padx=(0, 10))

        tyreRL_I_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_I, width=5,
                               anchor=tkinter.CENTER)
        tyreRL_I_l.grid(row=2, column=1)
        tyreRL_M_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_M, width=5,
                               anchor=tkinter.CENTER)
        tyreRL_M_l.grid(row=2, column=2)
        tyreRL_O_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_O, width=5,
                               anchor=tkinter.CENTER)
        tyreRL_O_l.grid(row=2, column=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Grain (%)", width=12,
                                 anchor=tkinter.E)
        tyreRL_grain.grid(row=3, column=0, padx=(0, 10))

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_grain,
                                   width=16, anchor=tkinter.CENTER)
        tyreRL_grain_l.grid(row=3, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Blister (%)", width=12,
                                 anchor=tkinter.E)
        tyreRL_grain.grid(row=4, column=0, padx=(0, 10))

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_blister,
                                   width=16, anchor=tkinter.CENTER)
        tyreRL_grain_l.grid(row=4, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="FlatSpot (%)", width=12,
                                 anchor=tkinter.E)
        tyreRL_grain.grid(row=5, column=0, padx=(0, 10))

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_flatspot,
                                   width=16, anchor=tkinter.CENTER)
        tyreRL_grain_l.grid(row=5, column=1, columnspan=3)

        tyreRL_grain = ttk.Label(tyreRL_f, text="Marble (%)", width=12,
                                 anchor=tkinter.E)
        tyreRL_grain.grid(row=6, column=0, padx=(0, 10))

        tyreRL_grain_l = ttk.Label(tyreRL_f, textvariable=self.tyreRL_marble,
                                   width=16, anchor=tkinter.CENTER)
        tyreRL_grain_l.grid(row=6, column=1, columnspan=3)

        tyreRR_f = ttk.Frame(self, padding=10)
        tyreRR_f.grid(row=2, column=1, padx=2, pady=2)
        tyreRR_l = ttk.Label(tyreRR_f, text="Rear right", width=16,
                             anchor=tkinter.CENTER)
        tyreRR_l.grid(row=0, column=0, columnspan=3)

        tyreRR_I = ttk.Label(tyreRR_f, text="I", width=5,
                             anchor=tkinter.CENTER)
        tyreRR_I.grid(row=1, column=0)
        tyreRR_M = ttk.Label(tyreRR_f, text="M", width=5,
                             anchor=tkinter.CENTER)
        tyreRR_M.grid(row=1, column=1)
        tyreRR_O = ttk.Label(tyreRR_f, text="O", width=5,
                             anchor=tkinter.CENTER)
        tyreRR_O.grid(row=1, column=2)

        tyreRR_tread_l = ttk.Label(tyreRR_f, text="Tread (mm)", width=12,
                                   anchor=tkinter.W)
        tyreRR_tread_l.grid(row=2, column=4, padx=(10, 0))

        tyreRR_I_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_I, width=5,
                               anchor=tkinter.CENTER)
        tyreRR_I_l.grid(row=2, column=2)
        tyreRR_M_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_M, width=5,
                               anchor=tkinter.CENTER)
        tyreRR_M_l.grid(row=2, column=1)
        tyreRR_O_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_O, width=5,
                               anchor=tkinter.CENTER)
        tyreRR_O_l.grid(row=2, column=0)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Grain (%)", width=12,
                                 anchor=tkinter.W)
        tyreRR_grain.grid(row=3, column=4, padx=(10, 0))

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_grain,
                                   width=16, anchor=tkinter.CENTER)
        tyreRR_grain_l.grid(row=3, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Blister (%)", width=12,
                                 anchor=tkinter.W)
        tyreRR_grain.grid(row=4, column=4, padx=(10, 0))

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_blister,
                                   width=16, anchor=tkinter.CENTER)
        tyreRR_grain_l.grid(row=4, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="FlatSpot (%)", width=12,
                                 anchor=tkinter.W)
        tyreRR_grain.grid(row=5, column=4, padx=(10, 0))

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_flatspot,
                                   width=16, anchor=tkinter.CENTER)
        tyreRR_grain_l.grid(row=5, column=0, columnspan=3)

        tyreRR_grain = ttk.Label(tyreRR_f, text="Marble (%)", width=12,
                                 anchor=tkinter.W)
        tyreRR_grain.grid(row=6, column=4, padx=(10, 0))

        tyreRR_grain_l = ttk.Label(tyreRR_f, textvariable=self.tyreRR_marble,
                                   width=16, anchor=tkinter.CENTER)
        tyreRR_grain_l.grid(row=6, column=0, columnspan=3)

        what_f = ttk.Frame(self, padding=(220, 0))
        what_f.grid(row=3, column=0, columnspan=2)

        what_l = ttk.Label(what_f, text="What is this ?",
                           anchor=tkinter.CENTER)
        what_l.pack()
        Hovertip(what_f, "After a driver swap acc dump information about"
                 " the tyre wear, this read it and display the information",
                 10)

    def _show_tyre_set_info(self, event) -> None:

        if len(self.tyres_data) == 0:
            return

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

        if (event.src_path.split("\\")[-1] == DUMP_FILE
                and self.no_spam_timer + 1 < time.time()):

            logger.info(f"file {event.src_path} modified")
            self.no_spam_timer = time.time()
            self._read_dump_file(event.src_path)
            self.updated = True

    def _read_dump_file(self, path: str) -> None:

        self.tyres_data.clear()
        tyre_set_data = None

        try:
            with open(path) as fp:
                tyre_set_data = json.load(fp)

        except FileNotFoundError as msg:
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

        if (self.observer.is_alive()):
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

    byte_size: ClassVar[int] = TyreSetData.byte_size * 4

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
