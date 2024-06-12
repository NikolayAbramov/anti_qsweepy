from tables import File, exceptions
import traceback
import numpy as np

db = lambda x: 20*np.log10(x)


class HDF5GainFile(File):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.n_records = 0
        try:
            self.n_records = len(self.root.thumbnail)
        except (exceptions.NoSuchNodeError, IndexError):
            pass
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
            s21_on = np.array(self.root.s21_on)[self.group_n]
            s21_off_snr = np.array(self.root.s21_off_snr)[self.group_n]
            snr_gain = np.array(self.root.snr_gain)[self.group_n]
            snr_freq = np.array(self.root.snr_freq)[self.group_n]
            self.Fs = self.root.thumbnail[self.group_n]['Fs']
            self.Pp = self.root.thumbnail[self.group_n]['Pp']
            self.Ib = self.root.thumbnail[self.group_n]['I']
            self.Gsnr = self.root.thumbnail[self.group_n]['Gsnr']
        except (exceptions.NoSuchNodeError, IndexError) as err:
            # traceback.print_exc()
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

        info_string = ("{:d}:Fc={:.4f}GHz Pp={:.2f}dBm I={:.4f}mA".
                       format(self.group_n,
                              self.Fs/self.f_unit,
                              self.Pp,
                              self.Ib/self.i_unit,
                              self.Gsnr))

        gain = abs(s21_on/s21_off_snr)
        return {'Fs': self.Fs/self.f_unit,
                'Pp': self.Pp,
                'Ib': self.Ib/self.i_unit,
                'Gsnr': self.Gsnr,
                'frequency': snr_freq/self.f_unit,
                'gain': db(gain),
                'snr_gain': db(snr_gain),
                'info': info_string,
                'status': True,
                'message': 'Success!'}
        
    def forward(self) -> bool:
        if self.group_n < self.n_records-1:
            self.group_n += 1
            print('Forward', self.group_n, self.n_records)
            return True
        return False            

    def backward(self) -> bool:
        if self.group_n > 0:
            self.group_n -= 1
            return True
        return False
