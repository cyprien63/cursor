import os
import sys

# Add the project directory to sys.path
sys.path.append(r"c:\Users\Cyprien\Desktop\code\git\cursor")

import cursor_logic

def test_flames_mapping():
    print("MAPPING TEST: flames")
    flames_dir = r"c:\Users\Cyprien\Desktop\code\git\cursor\curseur\flames"
    if not os.path.exists(flames_dir):
        print("ERROR: flames dir not found")
        return

    files = sorted([f for f in os.listdir(flames_dir) if f.endswith((".cur", ".ani"))])
    for f in files:
        role = cursor_logic.get_role_from_filename(f, theme="flames")
        print(f"FILE: [{f}] ROLE: [{role}]")

def test_rainbow_mapping():
    print("\nMAPPING TEST: never-lost-rainbow")
    rainbow_dir = r"c:\Users\Cyprien\Desktop\code\git\cursor\curseur\never-lost-rainbow"
    if not os.path.exists(rainbow_dir):
        print("ERROR: rainbow dir not found")
        return

    files = sorted([f for f in os.listdir(rainbow_dir) if f.endswith((".cur", ".ani"))])
    for f in files:
        role = cursor_logic.get_role_from_filename(f, theme="never-lost-rainbow")
        print(f"FILE: [{f}] ROLE: [{role}]")

if __name__ == "__main__":
    test_flames_mapping()
    test_rainbow_mapping()
