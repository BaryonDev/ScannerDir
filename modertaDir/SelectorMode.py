import subprocess
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\033[95m")  # Light Magenta color
    print("╔═══════════════════════════════════════════╗")
    print("║                 IATA.SC                   ║")
    print("╚═══════════════════════════════════════════╝")
    print("\033[0m")  # Reset color

def print_menu():
    print("\033[94m")  # Light Blue color
    print("╔═══════════════════════════════════════════╗")
    print("║               Main Menu                   ║")
    print("╠═══════════════════════════════════════════╣")
    print("║ 1. Scan 200K Dir                          ║")
    print("║ 2. Scan 1.2M Dir                          ║")
    print("║ 3. Scan Admin Path Only                   ║")
    print("║ 4. Run suki.py                            ║")
    print("║ 5. Exit                                   ║")
    print("╚═══════════════════════════════════════════╝")
    print("\033[0m")  # Reset color

def run_file(file_name):
    try:
        subprocess.run(["python", file_name], check=True)
    except subprocess.CalledProcessError:
        print(f"\033[91mAn error occurred while running {file_name}\033[0m")
    except FileNotFoundError:
        print(f"\033[91mFile {file_name} not found\033[0m")

def main():
    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input("\033[93mEnter your choice (1-5): \033[0m")

        if choice == '1':
            run_file("200k.py")
        elif choice == '2':
            run_file("1200k.py")
        elif choice == '3':
            run_file("adminPath.py")
        elif choice == '4':
            run_file("suki.py")
        elif choice == '5':
            print("\033[92mThank you for using IATA.SC. Goodbye!\033[0m")
            break
        else:
            print("\033[91mInvalid choice. Please enter a number between 1 and 5.\033[0m")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()