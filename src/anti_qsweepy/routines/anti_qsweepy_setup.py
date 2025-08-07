import subprocess
import sys
from pathlib import Path

def anti_qsweepy_setup():
    """anti_qsweepy_setup script setup script entry point"""
    cmd = ""
    pth = Path(sys.prefix)
    env_name = pth.name
    if sys.prefix != sys.base_prefix:
        # It's either venv or virtualenv
        cmd = sys.prefix + r"\Scripts\activate.bat"
    elif "conda" in sys.prefix.lower():
        # It's Conda environment
        cmd = 'conda activate '+env_name
    else:
        # Not in a virtual environment
        pass
    cmd = '"'+cmd+'"'
    # Setup virtual environment activation cmd to run plotting scripts
    subprocess.run('setx ANTI_QSWEEPY_VENV_CMD ' + cmd)