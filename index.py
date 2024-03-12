import subprocess

def run_script(script_name):
    subprocess.run(['python3', script_name])

if __name__ == '__main__':
    run_script('scripts/importSprints.py')
    run_script('scripts/importTimeLogs.py')
