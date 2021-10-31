Write-Output "Create venv"
python -m venv .\PyAccEngineerEnv

Write-Output "Activate venv"
.\PyAccEngineerEnv\Scripts\activate

Write-Output "Install required package"
pip install -r requirement.txt

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Output "Exit Python venv"
deactivate