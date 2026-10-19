$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build aborted.' }
python -m PyInstaller --noconfirm --clean --windowed --onedir --name DeskOTP --collect-all keyring --collect-all cv2 --collect-all numpy launch.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
Write-Host 'Built: dist\DeskOTP\DeskOTP.exe'
