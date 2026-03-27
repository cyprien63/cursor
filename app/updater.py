import subprocess
import os
import sys
import urllib.request
import zipfile
import shutil

def is_git_installed():
    """Checks if git is installed by running git --version."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def upgrade_pip():
    """Upgrades pip using python -m pip install --upgrade pip."""
    try:
        # User specifically asked for python.exe
        subprocess.run(["python.exe", "-m", "pip", "install", "--upgrade", "pip"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Fallback to 'python' if python.exe fails
        try:
            subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], capture_output=True, check=True)
            return True
        except:
            return False

def update_repository():
    """Runs git pull to update the cursors from GitHub."""
    try:
        # Check if .git exists to ensure it's a repo
        if not os.path.exists(".git"):
            print("Not a git repository. Skipping update.")
            return False
        
        print("Checking for updates...")
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        
        def has_active_themes():
            if not os.path.exists("curseur"): return False
            return any(os.path.isdir(os.path.join("curseur", d)) and not d.startswith(".") for d in os.listdir("curseur"))

        # Security: ensure files are actually there even if 'up to date'
        if not has_active_themes():
            print("Packs manquants localement, restauration forcée via Git...")
            subprocess.run(["git", "checkout", "HEAD", "--", "curseur"], capture_output=True)
        
        if "Already up to date" in result.stdout:
            print("No updates found.")
        else:
            print("Updates downloaded successfully.")
            
        return has_active_themes()
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

def get_staged_themes():
    """Returns a list of folders in curseur/ that are new or modified in Git."""
    try:
        # Assumes project root
        result = subprocess.run(["git", "status", "--short", "curseur"], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        lines = result.stdout.splitlines()
        staged = set()
        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) < 2: continue
            
            rel_path = parts[1].strip().replace("\\", "/")
            if rel_path.startswith("curseur/"):
                theme_name = rel_path[len("curseur")+1:].split("/")[0]
                if theme_name and theme_name != "curseur":
                    staged.add(theme_name)
                staged.add(theme_name)
            elif rel_path.startswith(cursor_dir):
                # it might be the dir itself
                theme_name = rel_path.split("/")[-1]
                if theme_name != cursor_dir:
                    staged.add(theme_name)
                    
        return sorted(list(staged))
    except:
        return []

def get_online_themes():
    """Returns a list of folders in curseur/ that are already tracked by Git."""
    try:
        # We always expect to be at the project root for Git commands
        result = subprocess.run(["git", "ls-files", "curseur"], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        lines = result.stdout.splitlines()
        tracked = set()
        for line in lines:
            line = line.replace("\\", "/")
            if line.startswith("curseur/"):
                theme_name = line[len("curseur")+1:].split("/")[0]
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
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        
        # 2. Git Commit
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True, text=True)
        
        # 3. Git Push
        result = subprocess.run(["git", "push", "origin", "HEAD"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Push failed: {result.stderr}"
            
        return True, "Successfully pushed all changes to GitHub."
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr if e.stderr else str(e)
        if "nothing to commit" in err_msg.lower():
            res = subprocess.run(["git", "push", "origin", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0: return True, "Pushed existing changes."
            return True, "Nothing new to push."
        return False, f"Git error: {err_msg}"
    except Exception as e:
        return False, str(e)

def download_zip_from_github(repo_url, target_dir):
    """
    Downloads the repository as a ZIP from GitHub and extracts it to target_dir.
    Tries both 'main' and 'master' branches. Uses PowerShell as fallback for download.
    """
    base_url = repo_url.replace('.git', '').rstrip('/')
    branches = ["main", "master"]
    zip_path = os.path.abspath("temp_repo.zip")
    extract_to = os.path.abspath("temp_extract")
    
    last_error = ""
    
    for branch in branches:
        zip_url = f"{base_url}/archive/refs/heads/{branch}.zip"
        try:
            print(f"Trying download from {zip_url}...")
            
            # Attempt 1: urllib
            download_success = False
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(zip_url, zip_path)
                download_success = True
            except Exception as e:
                print(f"urllib failed: {e}")
                # Attempt 2: PowerShell
                try:
                    cmd = ["powershell", "-Command", f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('{zip_url}', '{zip_path}')"]
                    subprocess.run(cmd, check=True, capture_output=True)
                    download_success = True
                    print("PowerShell download success.")
                except Exception as ps_e:
                    print(f"PowerShell failed: {ps_e}")
                    last_error = str(ps_e)
            
            if not download_success:
                continue

            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
                
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                
            # Deep search for 'curseur' folder
            source_cursor_dir = None
            for root, dirs, files in os.walk(extract_to):
                if "curseur" in dirs:
                    source_cursor_dir = os.path.join(root, "curseur")
                    break
            
            if not source_cursor_dir:
                # If no 'curseur' folder, use the root of the first subfolder
                subfolders = [f for f in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, f))]
                if subfolders:
                    source_cursor_dir = os.path.join(extract_to, subfolders[0])
                else:
                    source_cursor_dir = extract_to

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            # Copy contents
            count = 0
            for item in os.listdir(source_cursor_dir):
                # Avoid copying system/dev files if we are at the root
                if item.lower() in [".git", ".github", "venv", ".idea", "__pycache__", "build", "dist", "app", "main.py"]: 
                    continue
                
                s = os.path.join(source_cursor_dir, item)
                d = os.path.join(target_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                    count += 1
                elif item.endswith((".cur", ".ani")):
                    shutil.copy2(s, d)
                    count += 1
            
            # Cleanup
            if os.path.exists(zip_path): os.remove(zip_path)
            if os.path.exists(extract_to): shutil.rmtree(extract_to)
            
            if count == 0:
                last_error = "Aucun pack trouvé dans le téléchargement."
                continue
                
            return True, f"Téléchargement réussi ({count} packs trouvés)."
            
        except Exception as e:
            last_error = str(e)
            if os.path.exists(zip_path): os.remove(zip_path)
            continue
            
    return False, f"Erreur de téléchargement : {last_error}"

def get_latest_version(repo_url):
    """Checks the remote version.txt on GitHub."""
    try:
        raw_url = f"{repo_url.replace('github.com', 'raw.githubusercontent.com').replace('.git', '')}/main/version.txt"
        with urllib.request.urlopen(raw_url) as response:
            return response.read().decode().strip()
    except:
        return None

def apply_app_update(repo_url):
    """Downloads the new EXE and replaces the current one using a batch script."""
    # We target the main CursorStudio.exe in the repo
    raw_base = repo_url.replace('github.com', 'raw.githubusercontent.com').replace('.git', '')
    exe_url = f"{raw_base}/main/dist/CursorStudio.exe" # For testing, we assume user keeps it in dist/ or root
    
    # Fallback: check if they have it at the root
    new_exe = "CursorStudio_new.exe"
    current_exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.join(os.getcwd(), "main.py")
    current_exe_name = os.path.basename(current_exe_path)
    
    try:
        print(f"Downloading update from {exe_url}...")
        urllib.request.urlretrieve(exe_url, new_exe)
        
        # Create update script
        batch_path = os.path.join(os.path.dirname(current_exe_path), "update_app.bat")
        with open(batch_path, "w") as f:
            f.write(f'''@echo off
echo Finalisation de la mise a jour...
timeout /t 2 /nobreak > nul
del "{current_exe_name}"
ren "{new_exe}" "{current_exe_name}"
start "" "{current_exe_name}"
del "%~f0"
''')
        
        # Launch update script
        subprocess.Popen([batch_path], shell=True, cwd=os.path.dirname(current_exe_path))
        return True, "Mise à jour téléchargée. L'application va redémarrer."
    except Exception as e:
        # Try alternate URL (root of repo)
        try:
             exe_url_alt = f"{raw_base}/main/CursorStudio.exe"
             urllib.request.urlretrieve(exe_url_alt, new_exe)
             # (Same batch creation logic)
             batch_path = os.path.join(os.path.dirname(current_exe_path), "update_app.bat")
             with open(batch_path, "w") as f:
                f.write(f'''@echo off
echo Finalisation de la mise a jour...
timeout /t 2 /nobreak > nul
del "{current_exe_name}"
ren "{new_exe}" "{current_exe_name}"
start "" "{current_exe_name}"
del "%~f0"
''')
             subprocess.Popen([batch_path], shell=True, cwd=os.path.dirname(current_exe_path))
             return True, "Mise à jour téléchargée. Redémarrage..."
        except:
             return False, f"Erreur lors du téléchargement de l'EXE : {e}"
