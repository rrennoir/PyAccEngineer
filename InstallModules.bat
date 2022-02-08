@echo off
start /wait python -m venv .\PyAccEngineerEnv

PyAccEngineerEnv\Scripts\pip.exe install -r requirement.txt

pause
