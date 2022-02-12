# PyAccEngineer v1.5.9

# Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Useful info](#warnings)
4. [Donate](#donation)

![the app](https://i.imgur.com/lCR0e42.png)

For more images [here](https://imgur.com/a/ZlYYni5)

## Installation

- Need Python 3.8 or 3.9 (**don't use 3.10 it has problem installing some modules**), preferred [anaconda](https://www.anaconda.com/products/individual) or [python](https://www.python.org/downloads/)
- Check the box **ADD TO PATH** while installing Python
- Download the zip file from the [Release](https://github.com/rrennoir/PyAccEngineer/releases) page or use git: `git clone https://github.com/rrennoir/PyAccEngineer.git --recursive`
- Install the modules required, using the `InstallModule.bat` script or the ps1, bat is recommended since it doesn't have the limitation by default

**For server host only**, client doesn't need to open anything on their router.
- Open TCP and UDP port (4269 for TCP and UDP are the default) for incoming connections

### Example of opening port for 4269 on both protocol (TCP and UDP)

![port_forwarding_example](https://user-images.githubusercontent.com/32205591/145807682-943e091b-3cd3-4818-b71d-825ce2d52b37.png)

## Usage

### Open the app

- Use the StartApp.bat / StartApp.ps1 script 

#### Possible problems

- If you get the error `python isn't recognized...` and python is installed, [check here to add it to the path](https://www.educative.io/edpresso/how-to-add-python-to-path-variable-in-windows)

### How to use it

- One user starts "As Server" and others connect to it
- [OPTIONAL] Choose the same username as in ACC ("name surname"), so that the user driving can be recognized and will be highlighted in green.
- `Update values` will refresh the information on the strategy page to the lastest value in game (mfd page)
- `Set Strategy` will send a command to the user who is currently driving and set the strategy accordingly

### Run the server as headless (dedicated server)

Simply run the headless_server.py, by default port is 4269 (TCP) and 4269 (UDP) use -u or --udp_port to change the UDP port and -t or --tcp_port to change the TCP port. To change both port at the same time use -p or --port

```powershell
python headless_server.py -p 4275
```

```powershell
python headless_server.py -u 4270 --tcp_port 4269
```

To stop the server simply press ctrl C in the cmd / powershell / windows terminal

## **Warnings**

- **Tyre change must be on before the strategy setter is started**
- **At least one pit strategy must be set or different from the default**
- When the strategy setter is started the driving user shouldn't alt tab (duh)

## ***Will you controle my PC for other things ?***

No and if you don't trust me just read the code 😂

## Donation

If you have too much money you can donate [here](https://www.paypal.com/donate?hosted_button_id=H8LHDCTB7R2KC) 😊
(and now gop will stop asking for a donate link 🐒)
