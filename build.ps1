# AI Reader Build Script (Simplified)
# Step 1: Bundling
Write-Host "🔄 Activating Stable Python 3.11 Environment (venv_311)..." -ForegroundColor Cyan
& .\venv_311\Scripts\Activate.ps1
& ".\venv_311\Scripts\python.exe" -m PyInstaller AIReader.spec --noconfirm
# Step 2: Models
mkdir -Force "dist\AI Reader\models"
copy "models\kokoro-v1.0.onnx" "dist\AI Reader\models\" -Force
copy "models\voices-v1.0.bin" "dist\AI Reader\models\" -Force
# Step 3: Support Data (Absolute Final ESpeak Fix)
If (Test-Path "dist\AI Reader\_internal\espeak") { Remove-Item "dist\AI Reader\_internal\espeak" -Recurse -Force }
mkdir -Force "dist\AI Reader\_internal\espeak"
Copy-Item -Path "venv_311\Lib\site-packages\espeakng_loader\*" -Destination "dist\AI Reader\_internal\espeak" -Recurse -Force

# Step 4: Installer
$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "installer.iss"
