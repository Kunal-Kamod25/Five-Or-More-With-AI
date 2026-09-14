@echo off
echo ========================================================
echo       Starting Tic-Tac-Toe Game with RL AI & GUI
echo ========================================================
echo.

:: Try to activate conda environment if available
call conda activate five-or-more-ai 2>nul

:: 1. Launch the Tkinter Graphical User Interface (GUI)
echo [1/2] Launching Tic-Tac-Toe Graphical User Interface (UI)...
start "Tic-Tac-Toe GUI" python TicTacToe\ui.py

:: 2. Launch the Console / Terminal interactive game concurrently
echo [2/2] Launching Tic-Tac-Toe Console Version...
start "Tic-Tac-Toe Console Game" cmd /k "python TicTacToe\game.py"

echo.
echo ========================================================
echo   Both GUI and Console versions are running!
echo ========================================================
echo Close this window or press any key to exit launcher.
pause >nul
