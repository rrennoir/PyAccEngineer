import tkinter
from tkinter import ttk
from collections import namedtuple


class UserUI(ttk.Frame):

    def __init__(self, root):

        ttk.Frame.__init__(self, master=root)
        self.user_list = []

        self.active_user = None

        f_background = ttk.Frame(self, style="Users.TFrame")
        column_count = 0

        l_user = ttk.Label(f_background, text="Users:", width=5)
        l_user.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        user1 = tkinter.StringVar()
        l_user1 = ttk.Label(f_background, textvariable=user1, width=18,
                            anchor=tkinter.CENTER)
        l_user1.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        user2 = tkinter.StringVar()
        l_user2 = ttk.Label(f_background, textvariable=user2, width=18,
                            anchor=tkinter.CENTER)
        l_user2.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        user3 = tkinter.StringVar()
        l_user3 = ttk.Label(f_background, textvariable=user3, width=18,
                            anchor=tkinter.CENTER)
        l_user3.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        user4 = tkinter.StringVar()
        l_user4 = ttk.Label(f_background, textvariable=user4, width=18,
                            anchor=tkinter.CENTER)
        l_user4.grid(row=0, column=column_count, padx=1, pady=1)
        column_count += 1

        user5 = tkinter.StringVar()
        l_user5 = ttk.Label(f_background, textvariable=user5, width=18,
                            anchor=tkinter.CENTER)
        l_user5.grid(row=0, column=column_count, padx=1, pady=1)

        UserBox = namedtuple("UserBox", ["var", "label"])

        self.user_vars = [
            UserBox(user1, l_user1),
            UserBox(user2, l_user2),
            UserBox(user3, l_user3),
            UserBox(user4, l_user4),
            UserBox(user5, l_user5),
        ]

        f_background.pack()

    def add_user(self, name: str, driverID: int) -> None:

        if len(self.user_list) < 4 and name not in self.user_list:
            self.user_list.append(name)

            for user in self.user_vars:

                if user.var.get() == "":
                    user.var.set(f"{name} ({driverID})")
                    break

    def set_active(self, name: str) -> None:

        for user in self.user_vars:

            if user.var.get()[:-4] == name:
                user.label.configure(style="ActiveDriver.TLabel")
                self.active_user = name

            else:
                user.label.configure(style="TLabel")

    def reset(self) -> None:

        self.user_list.clear()
        self.active_user = None
        for user in self.user_vars:
            user.var.set("")
            user.label.configure(style="TLabel")
