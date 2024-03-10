from tables import File, exceptions
import numpy as np
import scipy.signal as ss
import traceback

db = lambda x: 20*np.log10(x)

class HDF5BiasSweepFile(File):
    def __init__(self, *args, **kwargs)->None:
        super().__init__( *args, **kwargs)
        self.savgol_filt_wind = 51
        self.savgol_filt_order = 3
        #Frequency unit is GHz
        self.f_unit = 1e9
        #Current unit is mA
        self.i_unit = 1e-3
        #Time unit is ns
        self.t_unit = 1e-9
        
    def get_data(self)->dict:
        try:
            data_2d = np.array( self.root.data )
            c_coord = np.array( self.root.column_coordinate )
            r_coord = np.array( self.root.row_coordinate )
        except exceptions.NoSuchNodeError as err:
            traceback.print_exc()
            return {'frequency':None, 
                'current':None,
                'delay':None,
                'status':False,
                'message':'Wrong file structure!'}
        else:   
            data_2d_norm = data_2d/data_2d[0]
            uPh = np.unwrap(np.angle(data_2d))
            uPh_filt = ss.savgol_filter(uPh, self.savgol_filt_wind, self.savgol_filt_order)
            delay = -np.diff(uPh_filt)/((c_coord[1]-c_coord[0])*2.*np.pi)
        return {'frequency':c_coord[:-1]/self.f_unit, 
                'current':r_coord/self.i_unit,
                'delay':(delay/self.t_unit).T,
                'status':True,
                'message': 'Success!'}