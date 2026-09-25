;     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

; Nuitka generated NSIS script for Windows installer creation.
; Generated from 'NsisTemplate.nsi', changes will be lost.

Unicode true

@MULTIUSER_HEADER@

!include "MUI2.nsh"

Name "@PRODUCT_NAME@"
OutFile "@OUTPUT_FILENAME@"

@REQUEST_EXECUTION_LEVEL@

@INSTALLDIR_CFG@

; Installer executable version information.
VIProductVersion "@PRODUCT_VERSION_4@"
VIAddVersionKey "ProductName" "@PRODUCT_NAME@"
VIAddVersionKey "CompanyName" "@COMPANY_NAME@"
VIAddVersionKey "FileDescription" "@FILE_DESCRIPTION@"
VIAddVersionKey "FileVersion" "@PRODUCT_VERSION@"
VIAddVersionKey "ProductVersion" "@PRODUCT_VERSION@"
VIAddVersionKey "LegalCopyright" "@LEGAL_COPYRIGHT@"

!define MUI_ABORTWARNING
@MUI_ICON_DEFINE@

!insertmacro MUI_PAGE_WELCOME
@LICENSE_PAGE@
@MULTIUSER_PAGE@
@COMPONENTS_PAGE@
@DIRECTORY_PAGE@
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "!@PRODUCT_NAME@" section_program
  SectionIn RO

  @SHELL_VAR_SETUP@

  SetOutPath "$INSTDIR"

  ; Payload of the installer as compiled by Nuitka.
  @PAYLOAD_COMMANDS@

  ; Remember the installation directory for upgrades.
  WriteRegStr SHCTX "@INSTALL_REG_KEY@" "InstallDir" "$INSTDIR"

  ; Create the uninstaller and register it, so uninstallation and upgrades
  ; work through the standard Windows mechanisms.
  WriteUninstaller "$INSTDIR\uninstall.exe"

  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "DisplayName" "@PRODUCT_NAME@"
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "DisplayVersion" "@PRODUCT_VERSION@"
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "Publisher" "@COMPANY_NAME@"
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "DisplayIcon" "$\"$INSTDIR\@MAIN_BINARY@$\""
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "InstallLocation" "$INSTDIR"
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  WriteRegStr SHCTX "@UNINSTALL_REG_KEY@" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
  WriteRegDWORD SHCTX "@UNINSTALL_REG_KEY@" "NoModify" 1
  WriteRegDWORD SHCTX "@UNINSTALL_REG_KEY@" "NoRepair" 1
SectionEnd

@SHORTCUT_SECTIONS@

Section "Uninstall"
  @SHELL_VAR_SETUP@

  ; Remove the shortcuts if they were created.
  Delete "$DESKTOP\@PRODUCT_NAME@.lnk"
  Delete "$SMPROGRAMS\@PRODUCT_NAME@.lnk"

  ; Remove installed files and the uninstaller itself.
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR"

  DeleteRegKey SHCTX "@UNINSTALL_REG_KEY@"
  DeleteRegKey SHCTX "@INSTALL_REG_KEY@"
SectionEnd

;     Part of "Nuitka", an optimizing Python compiler that is compatible and
;     integrates with CPython, but also works on its own.
;
;     Licensed under the GNU Affero General Public License, Version 3 (the "License");
;     you may not use this file except in compliance with the License.
;     You may obtain a copy of the License at
;
;        https://www.gnu.org/licenses/agpl-3.0.txt
;
;     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
;     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
;
;     Unless required by applicable law or agreed to in writing, software
;     distributed under the License is distributed on an "AS IS" BASIS,
;     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
;     See the License for the specific language governing permissions and
;     limitations under the License.
