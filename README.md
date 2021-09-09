# PyAccEngineer

## Requierement

* Need python 3.8 +
* pywin32 module
* PyAutoGUI module
* For users who are the server need port 4269 (or port you want) open (TCP), simple client have nothing to do with their ports

## Usage simply run the main.py in the cmd / powershell

```
python main.py
```
or run the powershell script

One user connect as server and the others connect to it

If the username chosen is the same as in acc ("name surname") then the user driving will be highlighted in green.

Update value will refresh the information on the strategy page to the lastest value in game (mfd page)
Set Strategy will send a command to the user who is currently driving and set the strategy accrodinly

done :D


## Warnings

* At least one pit strategy must be set or different from the default
* When the strategy setter is started the driving user shouldn't alt tab (duh)
* Tyre change must be on before the strategy setter is started
* The app can't change driver (yet, I hope)
* Doesn't support non ascii letter sry, well it does but name will be cut short :o
