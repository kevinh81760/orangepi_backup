import json
import subprocess
from pathlib import Path
from burger import Run
from time import sleep

def main():
    path = Path(__file__).parent.resolve()
    with open(Path(path, 'config.json'), 'r') as f:
        config = json.load(f)
        config["sqlite"]["file"] = Path(path, config["sqlite"]["file"])
        Run(config)

def is_synced_ntp():
    try:
        result = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip().lower() == "yes"
    except (subprocess.SubprocessError, OSError):
        return False

if __name__== "__main__":
    while not is_synced_ntp():
        sleep(1)
    main()
