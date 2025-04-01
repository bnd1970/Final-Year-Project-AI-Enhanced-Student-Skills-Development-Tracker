# main ui
import os
import sys
import subprocess
from pathlib import Path

INPUT_DIR = Path("input_form")
OUTPUT_DIR = Path("output_form")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files(directory, extension=".xlsx"):
    return sorted([
        f.name for f in directory.glob(f"*{extension}") 
        if f.is_file() and not f.name.startswith('~$')  # Added filter condition
    ])

def select_file(files, prompt):
    print(prompt)
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    while True:
        try:
            choice = int(input("Enter selection number: "))
            return files[choice-1]
        except (ValueError, IndexError):
            print("Invalid input, please select again")

def preprocess_module():
    clear_screen()
    print("=== Preprocessing Module ===")
    
    input_files = list_files(INPUT_DIR)
    if not input_files:
        input("Input directory is empty, press Enter to return...")
        return
    
    selected = select_file(input_files, "Please select the raw file to process:")
    output_name = input("Enter output filename (without extension): ").strip() + ".xlsx"
    
    cmd = [
        sys.executable, "preprocess_form.py",
        str(INPUT_DIR/selected),
        str(OUTPUT_DIR/output_name)
    ]
    subprocess.run(cmd)
    input("\nProcessing complete, press Enter to return to main menu...")

def analysis_module():
    clear_screen()
    print("=== Analysis Module ===")
    
    output_files = list_files(OUTPUT_DIR)
    if not output_files:
        input("Output directory is empty, press Enter to return...")
        return
    
    selected = select_file(output_files, "Please select the file to analyze:")
    
    cmd = [
        sys.executable, "analysis_form.py",
        "--input", str(OUTPUT_DIR/selected)
    ]
    subprocess.run(cmd)
    input("\nAnalysis complete, press Enter to return to main menu...")

def main_menu():
    while True:
        clear_screen()
        print("=== Team Collaboration Analysis System ===")
        print("1. Preprocess chat files")
        print("2. Analyze collaboration capability")
        print("3. Exit system")
        
        choice = input("Please select an option: ")
        if choice == "1":
            preprocess_module()
        elif choice == "2":
            analysis_module()
        elif choice == "3":
            print("Thank you for using, goodbye!")
            break
        else:
            input("Invalid selection, press Enter to continue...")

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    main_menu()