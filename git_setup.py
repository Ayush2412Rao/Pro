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

            # Pull remote changes (like a README) before pushing to avoid "fetch first" errors.
            print("\nAttempting to integrate remote changes (e.g., a README file)...")
            # We run this command allowing stdout to be displayed for interactivity (e.g., auth prompts),
            # but we capture stderr to check for specific, non-fatal errors.
            pull_process = subprocess.run(
                [git_cmd, "pull", "origin", "main", "--allow-unrelated-histories", "--no-edit"],
                stderr=subprocess.PIPE,
                text=True
            )

            # If pull failed, we inspect stderr to see if it's a recoverable situation.
            if pull_process.returncode != 0:
                # This error is expected if the remote repository is brand new and empty. We can ignore it.
                if "couldn't find remote ref" in pull_process.stderr:
                    print("Remote repository is empty, proceeding with initial push.")
                else:
                    # Any other error is unexpected and likely requires manual intervention.
                    print(f"\nError: Could not automatically pull from remote. Git says:\n---")
                    print(pull_process.stderr.strip())
                    print(f"---\nPlease resolve the issue manually and then push using: git push -u origin main")
                    return

            print("\nPushing to remote...")
            subprocess.check_call([git_cmd, "push", "-u", "origin", "main"])
            print("Successfully pushed to GitHub!")
            
    except subprocess.CalledProcessError as e:
        print(f"Error during git setup: {e}")

if __name__ == "__main__":
    main()