import subprocess
import sys
from pathlib import Path
import platformdirs
import shutil
import os

def anti_qsweepy_setup():
    """anti_qsweepy_setup setup script entry point"""
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

    module_pth = Path(os.path.dirname(os.path.realpath(__file__)))

    pth = platformdirs.user_documents_path()/"anti_qsweeepy_plotting_scripts"
    #if not pth.exists():
    #    pth.mkdir()
    # Copy plotting scripts into user dir
    shutil.copytree(module_pth.parent/'plotting_scripts', pth, dirs_exist_ok = True)