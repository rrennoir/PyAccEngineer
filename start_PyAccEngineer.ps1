Write-Host "Active venv"
.\PyAccEngineerEnv\Scripts\activate

Write-Host "Stating PyAccEngineer"
python .\main.py

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "Exit Python venv"
deactivate