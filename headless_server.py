import getopt
import sys
import time

from typing import List

from modules.Server import ServerInstance


def headless(argv: List[str]) -> None:

    """
    Ugly isn't it ?
    """

    try:
        opts, args = getopt.getopt(argv[1:], "hp:", ["help", "port="])

    except getopt.GetoptError as err:

        print(err)
        sys.exit(2)

    port = 4269
    for opt, arg in opts:

        if opt in ("-h", "--help"):
            print("Server.py [-p <port> (default 4269)]")
            sys.exit()

        elif opt in ("-p", "--port"):

            if arg.isnumeric():
                port = int(arg)

            else:
                print(f"Invalide port arg: {arg}")
                sys.exit(1)

    server = ServerInstance(port)
    print("SERVER: Running as headless server")

    Running = True
    while Running:

        try:
            time.sleep(1)

        except KeyboardInterrupt:
            Running = False

    server.disconnect()
    print("SERVER: exiting")


if __name__ == "__main__":

    headless(sys.argv)
