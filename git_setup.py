import subprocess
import os

def find_git():
    # Check if git is in PATH
    try:
        subprocess.check_call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "git"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Common Windows paths
    common_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe"),
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def main():
    # Ensure we are in the directory where the script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Initializing git repository in {os.getcwd()}...")
    
    git_cmd = find_git()
    
    if not git_cmd:
        print("Error: Git not found on your system.")
        print("Please install Git for Windows from: https://git-scm.com/download/win")
        print("After installing, restart your terminal and run this script again.")
        return

    try:
        subprocess.check_call([git_cmd, "init"])
        subprocess.check_call([git_cmd, "config", "user.name", "Ayush2412Rao"])
        subprocess.check_call([git_cmd, "config", "user.email", "ayushrao786420@gmail.com"])
        subprocess.check_call([git_cmd, "add", "."])
        subprocess.check_call([git_cmd, "commit", "-m", "Initial commit"])
        print("Git repository initialized, configured, and committed.")
    except subprocess.CalledProcessError as e:
        print(f"Error during git setup: {e}")

if __name__ == "__main__":
    main()