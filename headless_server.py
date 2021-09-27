import getopt
import logging
import sys
from typing import List

from twisted.internet import reactor

from modules.Server import ServerInstance

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s.%(msecs)03d | %(name)s | %(message)s",
                    datefmt="%H:%M:%S")


def headless(argv: List[str]) -> None:
    """
    Ugly isn't it ?
    """

    try:
        opts, args = getopt.getopt(argv[1:], "hu:t:",
                                   ["help", "udp_port=", "tcp_port="])

    except getopt.GetoptError as err:

        print(err)
        sys.exit(2)

    tcp_port = 4269
    udp_port = 4270
    for opt, arg in opts:

        if opt in ("-h", "--help"):
            print(f"python {__file__} [-p <port> (default 4269)]")
            sys.exit()

        elif opt in ("-u", "--udp_port"):

            if arg.isnumeric():
                udp_port = int(arg)

            else:
                logging.warning(f"Invalide UDP port arg: {arg}")
                sys.exit(1)

        elif opt in ("-t", "--tcp_port"):

            if arg.isnumeric():
                tcp_port = int(arg)

            else:
                logging.warning(f"Invalide TCP port arg: {arg}")
                sys.exit(1)

    ServerInstance(tcp_port, udp_port)
    logging.info("Running as headless server"
                 f" with port TCP:{tcp_port} UDP:{udp_port}")

    reactor.run()

    logging.info("Exiting")


if __name__ == "__main__":

    headless(sys.argv)
