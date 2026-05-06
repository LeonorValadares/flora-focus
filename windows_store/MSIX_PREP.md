Flora Focus - Microsoft Store / MSIX Preparation
================================================

Current state
-------------
- Desktop app works as a portable folder.
- Public backend is live on Render.
- Production database is live on Supabase Postgres.
- Windows icon assets already exist:
  - FloraFocus_icon.jpeg
  - FloraFocus.png
  - FloraFocus.ico
- A real Windows executable now builds successfully:
  - windows_store/dist/FloraFocus/FloraFocus.exe
- The executable launch is verified with a bounded local startup test.

What is still missing
---------------------
The app still needs to be wrapped into a signed MSIX package with Store metadata.

That means:
- package identity
- publisher details
- versioning
- Store-ready icons and metadata
- local MSIX install/uninstall validation

Recommended Windows Store route
-------------------------------
1. Rebuild the executable with windows_store/build_windows_exe.ps1 when needed.
2. Package windows_store/dist/FloraFocus/FloraFocus.exe into MSIX.
3. Validate the MSIX locally.
4. Reserve the app name in Partner Center.
5. Submit the MSIX package to the Microsoft Store.

Recommended tooling
-------------------
- Microsoft Store / Partner Center account
- MSIX Packaging Tool
- Windows App Certification Kit

Official references
-------------------
- MSIX overview:
  https://learn.microsoft.com/en-us/windows/msix/overview
- Windows packaging overview:
  https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/packaging/
- Packaging model decision guide:
  https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/choose-packaging-model
- Microsoft Store Win32 distribution options:
  https://learn.microsoft.com/en-us/windows/apps/distribute-through-store/how-to-distribute-your-win32-app-through-microsoft-store
- MSIX Packaging Tool:
  https://learn.microsoft.com/en-us/windows/msix/packaging-tool/tool-overview
- Create an MSIX package from an existing desktop installer or manual install:
  https://learn.microsoft.com/en-us/windows/msix/packaging-tool/create-app-package

Best packaging choice for this project
--------------------------------------
Target: full MSIX package for Store submission.

Reason:
- Microsoft Store distribution is the cleanest fix for SmartScreen reputation issues.
- Store-delivered apps are re-signed by Microsoft.
- MSIX gives cleaner install/uninstall/update behavior than the current zip folder.

Practical route from where the project is today
-----------------------------------------------
Phase A - Package for Store
- Feed the executable into MSIX packaging.
- Add package identity, version, publisher, icons, and metadata.

Phase B - Submit
- Run Store validation.
- Upload to Partner Center.

What I recommend next
---------------------
The next concrete engineering task is:

- create the first local MSIX package from FloraFocus.exe

That is the point where Store-specific blockers become concrete instead of theoretical.
