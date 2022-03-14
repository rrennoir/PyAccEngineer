# PyAccEngineer v1.5.9

- [PyAccEngineer v1.5.9](#pyaccengineer-v159)
  - [Download](#download)
  - [Prerequisit](#prerequisit)
  - [Installation](#installation)
    - [For server host (any driver, just one of them)](#for-server-host-any-driver-just-one-of-them)
  - [Open the app](#open-the-app)
  - [Possible problems](#possible-problems)
    - [Python isn't recognized](#python-isnt-recognized)
    - [Nobody is able to connect](#nobody-is-able-to-connect)
    - [Able to connect but no telemetry](#able-to-connect-but-no-telemetry)
  - [How to use it](#how-to-use-it)
    - [Run the server as headless (dedicated server)](#run-the-server-as-headless-dedicated-server)
  - [**Important note for using this**](#important-note-for-using-this)
  - [***Will you control my PC for other things ?***](#will-you-control-my-pc-for-other-things-)
  - [Donation](#donation)

![the app](https://i.imgur.com/lCR0e42.png)

For more images [here](https://imgur.com/a/ZlYYni5)


## Download

Download the zip file from the [Releases](https://github.com/rrennoir/PyAccEngineer/releases) page.

Or use git: `git clone https://github.com/rrennoir/PyAccEngineer.git --recursive`

## Prerequisit

To work the app need Python installed (for the user is enough, doesn't require admin access) and added to the path. 

**Don't use python 3.10 or greater as it has problem installing some modules**, use 3.8 or 3.9 instead.

Preferrably [anaconda](https://www.anaconda.com/products/individual), but the default python package work too [python](https://www.python.org/downloads/)

And **don't forget to add it to the PATH**, it's one of the step in the installer as shown in the screenshot I found on Google Image.

![Add python to path](https://i.stack.imgur.com/n5uHy.png)

## Installation

Install the required Python modules by running the `InstallModules.bat` (or `InstallModules.ps`). However .bat is recommended since it doesn't have the permission limitation by default

### For server host (any driver, just one of them)

Clients don't need to open anything on their router.
Host open TCP and UDP port (4269 for TCP **and** UDP are the default) for incoming connections as shown below

![port_forwarding_example](https://user-images.githubusercontent.com/32205591/145807682-943e091b-3cd3-4818-b71d-825ce2d52b37.png)

## Open the app

Use the StartApp.bat / StartApp.ps1 script 

## Possible problems

### Python isn't recognized

If you get the error `python isn't recognized...` and python is installed, [check here how to add it your PATH](https://www.educative.io/edpresso/how-to-add-python-to-path-variable-in-windows)

### Nobody is able to connect

If nobody can connect and the address / port are connect that mean the TCP port forwarding isn't setup correctly on the host router.

### Able to connect but no telemetry

If everyone can connect, but no telemetry is received to the clients that mean the UDP port forwarding isn't setup correctly on the host router.

## How to use it

- One user starts "As Server" and others connect to it
- Choose the same username as in ACC ("firstname surname"), so that the user driving can be recognized and will be highlighted in green.
- `Update values` will refresh the information on the strategy page to the lastest value in game (mfd page)
- `Set Strategy` will send a command to the user who is currently driving and set the strategy accordingly

### Run the server as headless (dedicated server)

Simply run the headless_server.py, default port is 4269 (TCP) and 4269 (UDP). Or use the command line switches -u or --udp_port to change the UDP port and -t or --tcp_port to change the TCP port. To change both port at the same time use -p or --port

```powershell
# sets both UDP/TCP ports to 4275
python headless_server.py -p 4275
```

```powershell
# sets ports for UDP to 4270 and TCP to 4269
python headless_server.py -u 4270 --tcp_port 4269
```

To stop the server simply press ctrl C in the cmd / powershell / Windows terminal

## **Important note for using this**

- **Tyre change must be on before the strategy setter is started**
- **At least one pit strategy must be set or different from the default** (just setting aggresive preset will work)
- When the strategy setter is started the driving user shouldn't alt tab (duh)

## ***Will you control my PC for other things ?***

No, and if you don't trust me just read the code 😂

The app basicaly has 2 channels, an udp channel sending ACC telemetry and another sending application info like users update, update state, the strategy state, tyre wear data, etc

No keycode are sent over the network, only the desired state of the pit strategy, so the app received it and generate the virtual keypress necessary to fulfill that state.

## Donation

If you have too much money you can donate [here](https://www.paypal.com/donate?hosted_button_id=H8LHDCTB7R2KC) 😊
(and now gop will stop asking for a donate link 🐒)
