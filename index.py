import subprocess
from pathlib import Path
import shutil
import time

def run_script(script_name, folder_name):
    folder_path = Path(f'data/{folder_name}')
    if folder_path.exists() and folder_path.is_dir():
        subprocess.run(['python3', script_name])
        shutil.rmtree(folder_path)
    else:
        print(f"Folder {folder_path} does not exist.")

if __name__ == '__main__':
    while True:
        run_script('scripts/importSprints.py', 'sprint_data')
        
        run_script('scripts/importTimeLogs.py', 'timelogs_data')
        
        time.sleep(60)