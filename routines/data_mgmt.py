import os
import shutil
import datetime
import pathlib

def default_save_path(root, time=True, name=None):

	now = datetime.datetime.now()
	day_folder_name = now.strftime('%Y-%m-%d')
	time_folder_name = now.strftime('%H-%M-%S')
	
	if time and name:
		path = '{0}/{1}/{2}-{3}'.format(root, day_folder_name, time_folder_name, name)
	elif time:
		path = '{0}/{1}/{2}'.format(root, day_folder_name, time_folder_name)
	elif name:
		path = '{0}/{1}/{2}'.format(root, day_folder_name, name)
	else:
		path = '{0}/{1}'.format(root, day_folder_name)
		
	pathlib.Path(path).mkdir(parents=True, exist_ok=True) 
	return path

def spawn_plotting_script(dest,name):
	module_dir = os.path.dirname(os.path.abspath(__file__))
	source_dir = os.path.split(module_dir)[0]+"\\plotting_scripts"
	shutil.copyfile(source_dir+"\\"+name+'.py', dest+"\\"+name+'.py')
	shutil.copyfile(source_dir+"\\plot.bat", dest+"\\plot.bat")
	bat = open(dest+"\\plot.bat", 'a')
	bat.write(' '+name+'.py')
	bat.close()