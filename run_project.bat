@echo off
echo Starting Five-or-More Game and Matrix Viewer...

:: Open a new terminal window for the Matrix Viewer
:: We use 'call conda activate' to ensure the environment is loaded correctly in the new window
start "Matrix Viewer" cmd /k "call conda activate five-or-more-ai & python src\utils\matrix_viewer.py"

:: Run the Rust game in the current terminal window
echo Starting Rust Game Engine...
cd game_engine\lines
cargo run

pause
