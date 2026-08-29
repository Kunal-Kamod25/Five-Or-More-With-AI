import time
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    file_path = os.path.join(project_root, "data", "raw", "board_matrix_live.txt")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create the file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("Waiting for game to start...\n")

    print(f"Watching {file_path} for live game updates...")
    
    last_modified = 0
    last_content = ""
    
    try:
        while True:
            current_modified = os.path.getmtime(file_path)
            
            if current_modified != last_modified:
                last_modified = current_modified
                
                with open(file_path, "r") as f:
                    content = f.read()
                
                if content != last_content:
                    last_content = content
                    clear_console()
                    print("====================================")
                    print("LIVE 9x9 BOARD MATRIX (Five-or-More)")
                    print("====================================\n")
                    print(content)
                    print("\n(Run the game in another window using `cd game_engine/lines && cargo run`)")
            
            time.sleep(0.1) # Check every 100ms
            
    except KeyboardInterrupt:
        print("\nExiting Matrix Viewer.")

if __name__ == "__main__":
    main()
