@echo off
REM Build the NSIS installer (requires NSIS installed)
echo Building NSIS installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer\simple_installer.nsi
echo Done! Installer at: dist\SignBridgePro_Setup_v2.0.0.exe
pause
