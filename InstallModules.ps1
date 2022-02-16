# Microsoft Build Tools für C++
# must be installed prior to running this script
# https://visualstudio.microsoft.com/de/visual-cpp-build-tools/

Write-Output "Creating Python venv"
# Please specify the exact path to your Python executable here if 
# you have multiple versions installed, e.g. c:\Python39\python.exe
python -m venv .\PyAccEngineerEnv

Write-Output "Activating Python venv"
.\PyAccEngineerEnv\Scripts\activate

Write-Output "Installing required packages"
pip install -r requirement.txt

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
