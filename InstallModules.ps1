Write-Output "Create venv"
python -m venv .\PyAccEngineerEnv

Write-Output "Install required package"
PyAccEngineerEnv\Scripts\pip.exe install -r requirement.txt

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
