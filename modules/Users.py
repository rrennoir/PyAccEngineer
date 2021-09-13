import tkinter
from collections import namedtuple


class UserUI(tkinter.Frame):

    def __init__(self, root, font):

        tkinter.Frame.__init__(self, master=root)
        self.user_list = []

        self.active_user = None
        self.font = font

        f_background = tkinter.Frame(self, background="Grey")
        column_count = 0

        l_user = tkinter.Label(f_background, text="Users:", width=10)
        l_user.config(font=self.font, bg="Black", fg="White")
        l_user.grid(row=0, column=column_count, padx=2, pady=1)
        column_count += 1

        user1 = tkinter.StringVar()
        l_user1 = tkinter.Label(f_background, textvariable=user1, width=24)
        l_user1.config(font=self.font, bg="Black", fg="White")
        l_user1.grid(row=0, column=column_count, padx=2, pady=1)
        column_count += 1

        user2 = tkinter.StringVar()
        l_user2 = tkinter.Label(f_background, textvariable=user2, width=24)
        l_user2.config(font=self.font, bg="Black", fg="White")
        l_user2.grid(row=0, column=column_count, padx=2, pady=1)
        column_count += 1

        user3 = tkinter.StringVar()
        l_user3 = tkinter.Label(f_background, textvariable=user3, width=24)
        l_user3.config(font=self.font, bg="Black", fg="White")
        l_user3.grid(row=0, column=column_count, padx=2, pady=1)
        column_count += 1

        user4 = tkinter.StringVar()
        l_user4 = tkinter.Label(f_background, textvariable=user4, width=24)
        l_user4.config(font=self.font, bg="Black", fg="White")
        l_user4.grid(row=0, column=column_count, padx=2, pady=1)

        UserBox = namedtuple("UserBox", ["var", "label"])

        self.user_vars = [
            UserBox(user1, l_user1),
            UserBox(user2, l_user2),
            UserBox(user3, l_user3),
            UserBox(user4, l_user4)
        ]

        f_background.pack()

    def add_user(self, name: str) -> None:

        if len(self.user_list) < 4 and name not in self.user_list:
            self.user_list.append(name)

            for user in self.user_vars:

                if user.var.get() == "":
                    user.var.set(name)
                    break

    def set_active(self, name: str) -> None:

        for user in self.user_vars:

            if user.var.get() == name:
                user.label.config(bg="Green")
                self.active_user = name

            else:
                user.label.config(bg="Black")

    def reset(self) -> None:

        self.user_list.clear()
        self.active_user = None
        for user in self.user_vars:
            user.var.set("")
            user.label.config(bg="Black")
