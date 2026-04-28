FLORA FOCUS - Windows Setup
===========================

STEP 1 - Install Python (only needed once ever)
  Go to https://python.org, click Download, run the installer.
  IMPORTANT: tick the box that says "Add Python to PATH" before clicking Install.


STEP 2 - Start Flora Focus
  Double-click:  launch_flora_focus_windows.bat

  The app now starts the backend automatically, so you only need one launch step.
  Your data is saved automatically in:  backend/flora_focus.db


NEXT TIME:
  Just double-click:  launch_flora_focus_windows.bat
  Python only needs installing once.


SOMETHING WENT WRONG?
---------------------
  "No module named kivy"
      Open Command Prompt and run:   venv\Scripts\python.exe -m pip install kivy[full]

  Black/blank window
      Open Command Prompt and run:   venv\Scripts\python.exe -m pip install --upgrade kivy[full]

  "Connection refused" when logging in
      Close the app and open launch_flora_focus_windows.bat again.

  My data is gone
      Do not delete the file:  backend/flora_focus.db
      That file contains all your accounts, tasks, and friends.
