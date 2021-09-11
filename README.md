# PyAccEngineer v1.2

![app](https://i.imgur.com/CKuR1CS.png)


## Requirements

- Need python 3.8+ (download at [python.org](https://www.python.org/downloads/) or [anaconda.com](https://www.anaconda.com/products/individual))
- pywin32 module
- PyAutoGUI module
- matplotlib module
- Server need open a TCP port (4269 is the default)

## Download

### With git

`git clone https://github.com/rrennoir/PyAccEngineer.git --recursive`

### Basic download

 Go to [Release](https://github.com/rrennoir/PyAccEngineer/releases) and download the latest PyAccEngineer.zip file :)

## Usage

### The Gui

Simply run the main.py in the cmd / powershell

```
python main.py
```

* One user connect as server and the others connect to it

* If the username chosen is the same as in acc ("name surname") then the user driving will be highlighted in green.
* `Update values` will refresh the information on the strategy page to the lastest value in game (mfd page)
* `Set Strategy` will send a command to the user who is currently driving and set the strategy accordingly


### Run the server as headless

Simply run the Server.py, by default port is 4269 use -p or --port to change it

```
python headless_server.py -p 4269
```

To stop the server simply press ctrl C in the terminal

## Warnings

* At least one pit strategy must be set or different from the default
* When the strategy setter is started the driving user shouldn't alt tab (duh)
* Tyre change must be on before the strategy setter is started
* The app can't change driver (yet, I hope)

## ***Will you controle my pc for other things ?***

No and if you don't trust me just read the code 😂
