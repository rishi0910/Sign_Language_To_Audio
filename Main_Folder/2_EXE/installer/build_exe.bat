@echo off
REM ══════════════════════════════════════════════
REM  SignBridge Pro — Build EXE
REM  Run from: 2_EXE_App/
REM ══════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════╗
echo  ║   SignBridge Pro — Build     ║
echo  ╚══════════════════════════════╝
echo.

REM Step 1 — generate dummy model if real one missing
if not exist "model\sign_model.h5" (
    echo [1/4] Generating dummy model for testing...
    python tests\mock_model.py
) else (
    echo [1/4] Model files found — skipping dummy generation.
)

REM Step 2 — install dependencies
echo [2/4] Installing dependencies...
pip install -r requirements.txt --quiet

REM Step 3 — clean previous build
echo [3/4] Cleaning previous build...
if exist "build\SignBridgePro" rmdir /s /q "build\SignBridgePro"
if exist "dist\SignBridgePro"  rmdir /s /q "dist\SignBridgePro"

REM Step 4 — build
echo [4/4] Building EXE with PyInstaller...
pyinstaller installer\SignBridgePro.spec --distpath dist --workpath build\work

echo.
echo  ✅ Build complete!
echo  Output: dist\SignBridgePro\SignBridgePro.exe
echo.
pause
