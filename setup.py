import sys
from cx_Freeze import setup, Executable

build_exe_options = {"packages": ["os"], 'include_files':['Config/','modules/','SharedMemory/','Assets/','headless_server.py']}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

#setup
setup(
    name = "PyAccEngineer",
    version = "1.4_beta",
    description = "Acc pit Engineer",
    author = "Ryan Rennoir",
    options = {"build_exe": build_exe_options},
    executables = [Executable("main.py", base=base, icon="Assets/Icon/techSupport.ico", targetName="PyAccEngineer")]
)