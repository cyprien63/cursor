import os
import sys
import json

# Add the project directory to sys.path
sys.path.append(r"c:\Users\Cyprien\Desktop\code\git\cursor")

import cursor_logic

def run_tests():
    results = {}
    
    themes = {
        "flames": r"c:\Users\Cyprien\Desktop\code\git\cursor\curseur\flames",
        "never-lost-rainbow": r"c:\Users\Cyprien\Desktop\code\git\cursor\curseur\never-lost-rainbow"
    }
    
    for theme_name, theme_path in themes.items():
        if not os.path.exists(theme_path):
            continue
        
        theme_results = []
        files = sorted([f for f in os.listdir(theme_path) if f.endswith((".cur", ".ani"))])
        for f in files:
            role = cursor_logic.get_role_from_filename(f, theme=theme_name)
            theme_results.append({"file": f, "role": role})
        results[theme_name] = theme_results
    
    with open("mapping_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
