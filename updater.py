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

def push_theme(theme_path):
    """Adds, commits and pushes the specified theme to GitHub."""
    try:
        if not os.path.exists(".git"):
            return False, "Not a git repository."
        
        theme_name = os.path.basename(theme_path)
        
        # 1. Git Add
        subprocess.run(["git", "add", theme_path], check=True, capture_output=True)
        
        # 2. Git Commit
        commit_msg = f"Update cursor theme: {theme_name}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        
        # 3. Git Push
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
            
        return True, "Successfully pushed to GitHub."
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else str(e)
        if "nothing to commit" in err_msg:
            return True, "Already up to date on GitHub."
        return False, err_msg
    except Exception as e:
        return False, str(e)

def get_staged_themes(cursor_dir):
    """Returns a list of folders in cursor_dir that are new or modified in Git."""
    try:
        result = subprocess.run(["git", "status", "--short", cursor_dir], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        lines = result.stdout.splitlines()
        staged = set()
        for line in lines:
            # Line format: 'XY path/' or 'XY path/file'
            parts = line.split(maxsplit=1)
            if len(parts) < 2: continue
            
            rel_path = parts[1].strip()
            # Normalize path and extract the first folder name after cursor_dir
            rel_path = rel_path.replace("\\", "/")
            if rel_path.startswith(cursor_dir + "/"):
                theme_name = rel_path[len(cursor_dir)+1:].split("/")[0]
                staged.add(theme_name)
            elif rel_path.startswith(cursor_dir):
                # it might be the dir itself
                theme_name = rel_path.split("/")[-1]
                if theme_name != cursor_dir:
                    staged.add(theme_name)
                    
        return sorted(list(staged))
    except:
        return []

def get_online_themes(cursor_dir):
    """Returns a list of folders in cursor_dir that are already tracked by Git."""
    try:
        # git ls-files shows all tracked files. We filter for the base directories.
        result = subprocess.run(["git", "ls-files", cursor_dir], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        lines = result.stdout.splitlines()
        tracked = set()
        for line in lines:
            line = line.replace("\\", "/")
            if line.startswith(cursor_dir + "/"):
                theme_name = line[len(cursor_dir)+1:].split("/")[0]
                tracked.add(theme_name)
                
        return sorted(list(tracked))
    except:
        return []

def delete_remote_theme(theme_path):
    """Removes a theme folder locally and from the GitHub repository."""
    try:
        if not os.path.exists(".git"):
            return False, "Not a git repository."
            
        theme_name = os.path.basename(theme_path)
        
        # 1. Git remove (does local and staging)
        subprocess.run(["git", "rm", "-rf", theme_path], check=True, capture_output=True)
        
        # 2. Commit deletion
        subprocess.run(["git", "commit", "-m", f"Delete theme: {theme_name}"], check=True, capture_output=True)
        
        # 3. Push deletion
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
            
        return True, f"Successfully deleted '{theme_name}' from GitHub."
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode() if e.stderr else str(e)
    except Exception as e:
        return False, str(e)

def push_all(message="Communal update"):
    """Adds everything, commits and pushes to GitHub."""
    try:
        if not os.path.exists(".git"):
            return False, "Not a git repository."
        
        # 1. Git Add All
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # 2. Git Commit
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        
        # 3. Git Push
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
            
        return True, "Successfully pushed all changes to GitHub."
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else str(e)
        if "nothing to commit" in err_msg:
            return True, "Nothing new to push."
        return False, err_msg
    except Exception as e:
        return False, str(e)
