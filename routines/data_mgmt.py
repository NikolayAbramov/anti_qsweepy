import os
import shutil
import datetime
import pathlib
import tables

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

def extendable_2d(path, data_descr = "Complex S-parameter", column_descr = "Frequency, Hz", row_descr = "Power, dBm"):	
	#Create HDF5 data file
	f = tables.open_file(path+'\\data.h5', mode='w')
	f.close()
	f = tables.open_file(path+'\\data.h5', mode='a')
	d_atom = tables.ComplexAtom(itemsize = 16 )
	rc_atom = tables.Float64Atom() #coordinates dtype
	d_array = f.create_earray(f.root, 'data', d_atom, (0, len(Fna)), "Complex S-parameter")
	f.create_array(f.root, 'column_coordinate', Fna, "Frequency, Hz")
	r_array = f.create_earray(f.root, 'row_coordinate', rc_atom, (0,), "Power, dBm")
	return f, d_array, r_array	

def spawn_plotting_script(dest,name):
	module_dir = os.path.dirname(os.path.abspath(__file__))
	source_dir = os.path.split(module_dir)[0]+"\\plotting_scripts"
	shutil.copyfile(source_dir+"\\"+name+'.py', dest+"\\"+name+'.py')
	shutil.copyfile(source_dir+"\\plot.bat", dest+"\\plot.bat")
	bat = open(dest+"\\plot.bat", 'a')
	bat.write(' '+name+'.py')
	bat.close()