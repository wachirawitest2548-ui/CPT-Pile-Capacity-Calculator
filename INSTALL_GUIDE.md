# Windows Installer Pack

Put these files in the root of your GitHub repository:

- `requirements.txt`
- `installer.iss`
- `.github/workflows/build-windows-installer.yml`

Your repository must also contain:

- `main.py`
- `layer_gui.py`
- `layer_formulas.py`
- `PTTEP_Logo.svg.png`

## Build from a Mac

1. Commit and push all files to the `main` branch.
2. Open the repository on GitHub.
3. Select **Actions**.
4. Select **Build Windows Installer**.
5. Choose **Run workflow**, or wait for the automatic run after pushing.
6. Open the completed workflow run.
7. Download the artifact named:
   `Interactive-Axial-Pile-Capacity-Calculator-Setup`
8. Extract the downloaded ZIP.
9. Give users:
   `Interactive_Axial_Pile_Capacity_Calculator_Setup.exe`

## What Windows users do

1. Double-click the Setup file.
2. Continue through the installation wizard.
3. Optionally select the desktop shortcut.
4. Click Install.
5. Click Finish.

The installer also creates a Start Menu shortcut and an uninstaller.

## Important

Unsigned Windows applications can trigger Microsoft Defender SmartScreen.
The user may need to select **More info** and **Run anyway**.
For company-wide distribution, request code signing and IT approval.
