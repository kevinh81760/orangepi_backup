import json
from pathlib import Path
from burger import Run
import pexpect
from time import sleep

def main():
    path = Path(__file__).parent.resolve()
    with open(Path(path, 'config.json'), 'r') as f:
        config = json.load(f)
        config["sqlite"]["file"] = Path(path, config["sqlite"]["file"])
        Run(config)

def is_synced_ntp():
    command_output, _ = pexpect.run("timedatectl", withexitstatus=True)
    for line in command_output.decode("unicode_escape").split("\n"):
        if "synchronized: yes" in line:
            return True
    return False

if __name__== "__main__":
    while not is_synced_ntp():
        sleep(1)
        pass
    main()
