@echo off
REM Save the current directory
set "CURRENT_DIR=%CD%"

REM Create virtual environment
set VENV_NAME=venv
python -m venv %VENV_NAME%

REM Activate the virtual environment
call %VENV_NAME%\Scripts\activate

REM Install dependencies
pip install -r %CURRENT_DIR%\requirements.txt

REM Create launch.bat
(
  echo @echo off
  echo call %VENV_NAME%\Scripts\activate
  echo python run.py
) > %CURRENT_DIR%\launch.bat

REM Deactivate the virtual environment
deactivate