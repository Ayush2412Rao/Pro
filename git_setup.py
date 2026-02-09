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
        if not os.path.exists(".git"):
            subprocess.check_call([git_cmd, "init"])
            
        subprocess.check_call([git_cmd, "config", "user.name", "Ayush2412Rao"])
        subprocess.check_call([git_cmd, "config", "user.email", "ayushrao786420@gmail.com"])
        subprocess.check_call([git_cmd, "add", "."])
        
        # Check if there are changes to commit
        status = subprocess.run([git_cmd, "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.check_call([git_cmd, "commit", "-m", "Initial commit"])
            print("Git repository initialized, configured, and committed.")
        else:
            print("Nothing to commit (repository already up to date locally).")

        print("\n--- Push to GitHub ---")
        print("To see this code on GitHub, you must create a repository there first.")
        print("1. Go to https://github.com/new")
        print("2. Create a repository (e.g., named 'Pro')")
        repo_url = input("3. Enter the HTTPS URL here (e.g., https://github.com/Ayush2412Rao/Pro.git): ").strip()
        
        if repo_url:
            subprocess.run([git_cmd, "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
            subprocess.check_call([git_cmd, "remote", "add", "origin", repo_url])
            subprocess.check_call([git_cmd, "branch", "-M", "main"])
            subprocess.check_call([git_cmd, "push", "-u", "origin", "main"])
            print("Successfully pushed to GitHub!")
            
    except subprocess.CalledProcessError as e:
        print(f"Error during git setup: {e}")

if __name__ == "__main__":
    main()