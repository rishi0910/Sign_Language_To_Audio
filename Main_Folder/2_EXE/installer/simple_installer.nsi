; SignBridge Pro NSIS Installer Script
; Requires NSIS 3.x: https://nsis.sourceforge.io/

!define APP_NAME    "SignBridge Pro"
!define APP_VERSION "2.0.0"
!define APP_EXE     "SignBridgePro.exe"
!define INSTALL_DIR "$PROGRAMFILES\SignBridge Pro"

Name        "${APP_NAME} ${APP_VERSION}"
OutFile     "..\dist\SignBridgePro_Setup_v${APP_VERSION}.exe"
InstallDir  "${INSTALL_DIR}"
RequestExecutionLevel admin

; Pages
Page directory
Page instfiles

; Install section
Section "Install"
    SetOutPath "$INSTDIR"
    File /r "..\dist\SignBridgePro\*.*"

    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

    ; Create start menu entry
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"   "$INSTDIR\Uninstall.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstall section
Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
