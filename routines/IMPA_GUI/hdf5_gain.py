from tables import File, exceptions
import traceback
import numpy as np

db = lambda x: 20*np.log10(x)

class HDF5GainFile(File):
    def __init__(self, *args, **kwargs)->None:
        super().__init__( *args, **kwargs)
        self.n_records = 0
        while True:
            try:
                group = self.root['group_{:d}'.format(self.n_records)]
            except (exceptions.NoSuchNodeError, IndexError):
                break
            self.n_records += 1
        self.group_n = 0
        #GHz
        self.f_unit = 1e9
        self.i_unit = 1e-3
        self.Fs = 0
        self.Pp = 0
        self.Ib = 0
        self.Gsnr = 0
    
    def get_data(self) -> dict:
        try:
            group = self.root['group_{:d}'.format(self.group_n)]
            F = np.array(group.frequency)
            #S21_off = array( group.pump_off )
            S21_on = np.array(group.pump_on)
            S21_off_snr = np.array(group.snr_pump_off)
        except (exceptions.NoSuchNodeError, IndexError) as err:
            return {'Fs': None,
                    'Pp': None,
                    'Ib': None,
                    'Gsnr': None,
                    'frequency': None,
                    'gain': None,
                    'snr_gain': None,
                    'info': None,
                    'status': False,
                    'message': 'File is empty or has wrong structure! Node {0} is missing.'.format(err.args[0])}
        try:
            # New file format
            self.Fs = group.thumbnail[0]['Fs']
            self.Pp = group.thumbnail[0]['Pp']
            self.Ib = group.thumbnail[0]['I']
            self.Gsnr = group.thumbnail[0]['Gsnr']
        except (exceptions.NoSuchNodeError, IndexError):
            try:
                # Old file format
                self.Fs = self.root.thumbnail[self.group_n]['Fs']
                self.Pp = self.root.thumbnail[self.group_n]['Pp']
                self.Ib = self.root.thumbnail[self.group_n]['I']
                self.Gsnr = self.root.thumbnail[self.group_n]['Gsnr']
            except (exceptions.NoSuchNodeError, IndexError):
                # Plug with 0s if the thumbnail is finally broken
                self.Fs = 0
                self.Pp = 0
                self.Ib = 0
                self.Gsnr = 0

        info_string = ("{:d}:Fc={:.4f}GHz Pp={:.2f}dBm I={:.4f}mA".\
                        format(self.group_n,
                        self.Fs/self.f_unit,
                        self.Pp,
                        self.Ib/self.i_unit,
                        self.Gsnr))
        S21_off = np.mean(S21_off_snr, axis=0)
        snr_ref = abs(S21_off)/np.std(np.real(S21_off_snr), axis = 0)
        S21_on_snr = np.array(group.snr_pump_on)
        snr = abs(np.mean(S21_on_snr, axis=0))/np.std(np.real(S21_on_snr), axis = 0)
        F_snr = np.array(group.snr_frequency)
        snr_gain = snr/snr_ref
        gain = abs(S21_on/S21_off)
        return {'Fs': self.Fs/self.f_unit,
                'Pp': self.Pp,
                'Ib': self.Ib/self.i_unit,
                'Gsnr': self.Gsnr,
                'frequency': F_snr/self.f_unit,
                'gain': db(gain),
                'snr_gain': db(snr_gain),
                'info': info_string,
                'status': True,
                'message': 'Success!'}
        
    def forward(self) -> bool:
        if self.group_n < self.n_records-1:
            self.group_n += 1
            return True
        return False            

    def backward(self) -> bool:
        if self.group_n > 0:
            self.group_n -= 1
            return True
        return False
