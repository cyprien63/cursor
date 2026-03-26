import subprocess
import os

def update_repository():
    """Runs git pull to update the cursors from GitHub."""
    try:
        # Check if .git exists to ensure it's a repo
        if not os.path.exists(".git"):
            print("Not a git repository. Skipping update.")
            return False
        
        print("Checking for updates...")
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if "Already up to date" in result.stdout:
            print("No updates found.")
        else:
            print("Updates downloaded successfully.")
        return True
    except FileNotFoundError:
        print("Git not found. Please install git to enable auto-updates.")
        return False
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False
