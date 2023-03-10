Write-Host "Starting PyAccEngineer"
env\Scripts\python.exe .\main.py

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
