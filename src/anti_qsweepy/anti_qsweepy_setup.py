import subprocess
import sys
from pathlib import Path
import platformdirs
import shutil
import os
from ruamel.yaml import YAML

from . import global_defs

def anti_qsweepy_setup():
    """anti_qsweepy_setup setup script"""

    # Detect virtual environment
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

    # Set environmental variable to enable simultaneous access to HDF5 data files
    subprocess.run("setx HDF5_USE_FILE_LOCKING \"FALSE\"")

    # Copy plotting scripts into user dir
    module_pth = Path(os.path.dirname(os.path.realpath(__file__)))
    user_plotting_scripts_pth = platformdirs.user_documents_path()/global_defs.project_name/global_defs.user_plotting_scripts_dir_name
    #if not pth.exists():
    #    pth.mkdir()
    shutil.copytree(module_pth/'plotting_scripts', user_plotting_scripts_pth, dirs_exist_ok = True)

    # Save configuration data
    app_data_pth = platformdirs.user_data_path(global_defs.project_name, appauthor = False)
    if not app_data_pth.exists():
        app_data_pth.mkdir(parents=True)

    app_data = {'user_plotting_scripts_pth':str(user_plotting_scripts_pth)}
    yaml = YAML()
    yaml.default_flow_style = False
    with open(app_data_pth/global_defs.app_conf_file_name, 'w') as f:
        yaml.dump(app_data, f)