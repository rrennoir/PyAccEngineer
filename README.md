# PyAccEngineer v1.5.5

# Table of Contents

1. [Install](#install)
2. [Usage](#usage)
3. [Usefull info](#warnings)
4. [Donate](#donation)

![the app](https://i.imgur.com/lCR0e42.png)

For more images [here](https://imgur.com/a/ZlYYni5)

## Install

- Need python 3.8 or 3.9 (**don't use 3.10 it has problem installing some modules**), preferred [anaconda](https://www.anaconda.com/products/individual) or [python](https://www.python.org/downloads/)
- Check to box while installing to ADD TO PATH
- Download the zip file in the [Release](https://github.com/rrennoir/PyAccEngineer/releases) or use git: `git clone https://github.com/rrennoir/PyAccEngineer.git --recursive`
- Install the modules required, use the `install_module.ps1` script or do a `pip install -r requirement.txt` in the terminal

**For sever host only**, client doesn't need to open anything on their router.
- Open a TCP and UDP port (4269 TCP and 4270 UDP are the default)

### Example of opening port for 4269 on both protocol (TCP and UDP)

![port_forwarding_example](https://user-images.githubusercontent.com/32205591/145807682-943e091b-3cd3-4818-b71d-825ce2d52b37.png)

## Usage

### Open the app

- Use the start_PyAccEngineer.ps1 script (right click on it then run with powershell)

or if you know what you are doing

- Open terminal
- Navigate to the PyAccEngineer folder
- Start venv (if used)
- `python main.py`

#### Possible problems

- If you get the error `python isn't recognized...` and python is installed, [check here to add it to the path](https://www.educative.io/edpresso/how-to-add-python-to-path-variable-in-windows)

### How to use it

- One user connect as server and the others connect to it
- [OPTIONAL] Chose the same username as in acc ("name surname") then so the user driving will be highlighted in green.
- `Update values` will refresh the information on the strategy page to the lastest value in game (mfd page)
- `Set Strategy` will send a command to the user who is currently driving and set the strategy accordingly

### Run the server as headless (dedicated server)

Simply run the Server.py, by default port is 4269 (TCP) and 4270 (UDP) use -u or --udp_port to change the UDP port and -t or --tcp_port to change the TCP port


```powershell
python headless_server.py -u 4270 --tcp_port 4269
```

To stop the server simply press ctrl C in the cmd / powershell / windows terminal

## **Warnings**

- **Tyre change must be on before the strategy setter is started**
- **At least one pit strategy must be set or different from the default**
- When the strategy setter is started the driving user shouldn't alt tab (duh)

## ***Will you controle my pc for other things ?***

No and if you don't trust me just read the code 😂

## Donation

If you have too much money you can donate [here](https://www.paypal.com/donate?hosted_button_id=H8LHDCTB7R2KC) 😊
(and now gop will stop asking for a donate link 🐒)
