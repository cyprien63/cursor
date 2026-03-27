import sys
import os

# Ensure the 'app' directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.gui import CursorApp
except ImportError as e:
    print(f"Error: Could not load the application. {e}")
    sys.exit(1)

if __name__ == "__main__":
    # Launch the application
    app = CursorApp()
    app.mainloop()
