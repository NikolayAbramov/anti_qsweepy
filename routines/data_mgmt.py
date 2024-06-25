import os
import shutil
import datetime
import pathlib
import tables
import re

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

def extendable_2d(path, column_coordinate, dtype = complex,
				  data_descr = "Complex S-parameter",
				  column_descr = "Frequency, Hz",
				  row_descr = "Power, dBm"):
	# Create HDF5 data file
	f = tables.open_file(path+'\\data.h5', mode='w')
	f.close()
	f = tables.open_file(path+'\\data.h5', mode='a')
	d_atom = tables.ComplexAtom(itemsize = 16 )
	rc_atom = tables.Float64Atom() #coordinates dtype
	if dtype is complex:
		d_array = f.create_earray(f.root, 'data', d_atom, (0, len(column_coordinate)), "Data")
	elif dtype is float:
		d_array = f.create_earray(f.root, 'data', rc_atom, (0, len(column_coordinate)), "Data")
	else:
		raise TypeError
	f.create_array(f.root, 'column_coordinate', column_coordinate, "Frequency, Hz")
	r_array = f.create_earray(f.root, 'row_coordinate', rc_atom, (0,), "Power, dBm")
	f.flush()
	return f, d_array, r_array	

def data_file(path):	
	#Create HDF5 data file
	f = tables.open_file(path+'\\data.h5', mode='w')
	f.close()
	f = tables.open_file(path+'\\data.h5', mode='a')
	return f

def spawn_plotting_script(dest,name, py = True):
	module_dir = os.path.dirname(os.path.abspath(__file__))
	source_dir = os.path.split(module_dir)[0]+"\\plotting_scripts"
	script_name = os.path.split(name)[-1]
	if py:
		shutil.copyfile(source_dir+"\\"+name+'.py', dest+"\\"+script_name+'.py')
		shutil.copyfile(source_dir+"\\plot.bat", dest+"\\plot.bat")
		bat = open(dest+"\\plot.bat", 'a')
		bat.write(' '+script_name+'.py')
		bat.close()
	else:
		shutil.copyfile(source_dir+"\\"+name, dest+"\\"+name)
		
def add_vna_description(file, segment_table, parameter_val = None):
	if parameter_val is not None:
		class Parameter(tables.IsDescription):
			parameter_name = tables.StringCol(16)   # 16-character String
			parameter = tables.Float64Col()

		parameter = file.create_table(file.root, 'parameter', Parameter, "parameter").row
		parameter['parameter_name'] = ' '
		parameter['parameter'] = parameter_val
		parameter.append()

	class SegmentTable(tables.IsDescription):
		start = tables.Float64Col()
		stop = tables.Float64Col()
		points = tables.Float64Col()
		power = tables.Float64Col()
		bandwidth = tables.Float64Col()

	s_table = file.create_table(file.root, 'segment_table', SegmentTable, "segment_table").row
	for item in segment_table:
		s_table['start'] = item['start']
		s_table['stop'] = item['stop']
		s_table['points'] = item['points']
		s_table['power'] = item['power']
		s_table['bandwidth'] = item['bandwidth']
		s_table.append()
        
def add_sa_description(file: tables.File, metadata: dict) -> None:
    """Add spectrum analyzer metadata table to the HDF5 file"""
    class SAMetadata(tables.IsDescription):
        rbw = tables.Float64Col()
        vbw = tables.Float64Col()
        
    s_table = file.create_table(file.root, 'metadata', SAMetadata, "metadata").row
    s_table['rbw'] = metadata['rbw']
    s_table['vbw'] = metadata['vbw']
    s_table.append()
    

def impa_tuning_results(f_points:int, save_path:str):
	"""Creates HDF5 file to store IMPA tuning results"""
	class Thumbnail(tables.IsDescription):
		Fp = tables.Float64Col()
		Fs = tables.Float64Col()
		G = tables.Float64Col()
		Pp = tables.Float64Col()
		I = tables.Float64Col()
		Gsnr = tables.Float64Col()

	hdf5_title = 'JPA tuning table'
	f = tables.open_file(save_path + '\\data.h5', mode='w', title=hdf5_title)
	thumbnail = f.create_table(f.root, 'thumbnail', Thumbnail, "thumbnail").row
	complex_atom = tables.ComplexAtom(itemsize=16)
	float_atom = tables.Float64Atom()
	s21_on = f.create_earray(f.root, 's21_on', complex_atom, (0, f_points * 2), "S21-on")
	s21_off = f.create_earray(f.root, 's21_off', complex_atom, (0, f_points * 2), "S21-off")
	s21_on_snr = f.create_earray(f.root, 's21_on_snr', complex_atom, (0, f_points * 2),
								 "mean(S21-on-snr)")
	s21_off_snr = f.create_earray(f.root, 's21_off_snr', complex_atom, (0, f_points * 2),
								  "mean(S21-off-snr)")
	s21_freq = f.create_earray(f.root, 's21_frequency', float_atom, (0, f_points * 2), "S21 frequency")
	snr_gain = f.create_earray(f.root, 'snr_gain', float_atom, (0, f_points * 2), "SNR gain")
	snr_freq = f.create_earray(f.root, 'snr_freq', float_atom, (0, f_points * 2), "SNR frequency")
	return {'thumbnail': thumbnail,
			's21_on': s21_on,
			's21_off': s21_off,
			's21_on_snr': s21_on_snr,
			's21_off_snr': s21_off_snr,
			's21_freq': s21_freq,
			'snr_gain': snr_gain,
			'snr_freq': snr_freq,
			'file': f}