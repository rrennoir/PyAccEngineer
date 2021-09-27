# PyAccEngineer v1.5

![app](https://i.imgur.com/7g7SAvD.png)

For more images [here](https://imgur.com/a/EwZwhOD)

## Requirements

- Need python 3.8+ (download at [python.org](https://www.python.org/downloads/) or [anaconda.com](https://www.anaconda.com/products/individual))
- pywin32 module
- PyAutoGUI module
- matplotlib module
- Twisted and service-identity modules
- Server need open a TCP and UDP port (4269 TCP and 4270 UDP are the default)

## Download

### With git

`git clone https://github.com/rrennoir/PyAccEngineer.git --recursive`

### Basic download

 Go to [Release](https://github.com/rrennoir/PyAccEngineer/releases) and download the latest PyAccEngineer.zip file :)

## Usage

### Open the app

- Open Command Prompt / Powershell / Windows Terminal
- Navigate to the PyAccEngineer folder
- Type `python main.py`
- There you go PyAccEngineer is running

![The lazy way](https://i.imgur.com/LTrFK2S.gif)

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
python headless_server.py -u 4270 -tcp_port 4269
```

To stop the server simply press ctrl C in the cmd / powershell / windows terminal

## **Warnings**

- **Tyre change must be on before the strategy setter is started**
- **At least one pit strategy must be set or different from the default**
- When the strategy setter is started the driving user shouldn't alt tab (duh)

## ***Will you controle my pc for other things ?***

No and if you don't trust me just read the code 😂
