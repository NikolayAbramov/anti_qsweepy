from numpy import *
from numpy.typing import ArrayLike
import anti_qsweepy.routines.differential_evolution as di


class OperationPoint():
    def __init__(self, Fs=0., Fp=0., Pp=0., I=0., G=0., Gsnr=0.):
        self.I = I
        self.Fs = Fs
        self.Pp = Pp
        self.Fp = Fp
        self.G = G
        self.Gsnr = Gsnr

    def __str__(self):
        return ("""Fs = {:.6e} Hz
Fp = {:.6e} Hz
Pp = {:.3f} dBm
I = {:.6e} A
G = {:.2f} dB
Gsnr = {:.2f} dB""".format(self.Fs, self.Fp, self.Pp, self.I, self.G, self.Gsnr))

    def file_str(self):
        return "{:.6e}\t{:.6e}\t{:.2f}\t{:e}\t{:.2f}\t{:.2f}".format(self.Fs, self.Fp, self.Pp, self.I, self.G,
                                                                     self.Gsnr)

    def file_str_header(self):
        return "#Fs,Hz\t\tFp,Hz\t\tPp,dBm\tI,A\t\tG,dB\tGsnr,dB"


class TuningTable():
    def __init__(self, points=[]):
        self.i = 0
        self.points = points

    def __len__(self):
        return len(self.points)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self.points):
            i = self.i
            self.i += 1
            return self.points[i]
        else:
            self.i = 0
            raise StopIteration

    def __getitem__(self, i):
        return self.points[i]

    def __setitem__(self, i, val):
        self.points[i] = val

    def add_point(self, op):
        self.points += [op, ]

    def dump(self, path):
        file = open(path, 'w+')
        file.write(self.points[0].file_str_header() + '\n')
        for op in self.points:
            file.write(op.file_str() + '\n')
        file.close()

    def load(self, path):
        data = loadtxt(path)
        self.points = []
        if len(shape(data)) < 2:
            op = OperationPoint(Fs=data[0], Fp=data[1], Pp=data[2], I=data[3], G=data[4], Gsnr=data[5])
            self.add_point(op)
        else:
            for row in data:
                op = OperationPoint(Fs=row[0], Fp=row[1], Pp=row[2], I=row[3], G=row[4], Gsnr=row[5])
                self.add_point(op)


# Tuner for wideband IMPA based on differetial evalution algorithm.
# Works for both wide and narrow band modes. For narrow band modes central point weight is more important.
# It's batter to set target bw closer to expected. It can be wider, but not much.
class IMPATuner():
    def __init__(self, vna=None, pump=None, bias=None):
        self.vna = vna
        self.pump = pump
        self.bias = bias
        self.bias_range = [0, 1e-3]
        self.pump_range = [-5., 2.]
        self.target_freq = 6.5e9
        self.target_freq_span = 0.
        self.target_gain = 20  # dB
        self.target_bw = 600e6
        self.w_cent = 0.5  # Central point weight. Forces gain to be close to the target at central frequency.
        self.Ps = -30
        self.bw = 5e3
        self.points = 350
        self.detuning = 2e6
        self.ref = None
        self.snr_ref = None
        self.res = None
        self.n = 10
        self.di_solver: di.DifferentialEvolutionSolver | None = None
        self._abort = False

    def abort(self) -> None:
        """Thread abort."""
        self._abort = True

    def _check_abort_flag(self) -> None:
        """Rises AbortException handled by differential evolution algorithm  if abort()
        method was previously called."""
        if self._abort:
            self._abort = False
            raise di.AbortException

    def _measure_ref(self):
        self.bias.output(False)
        self.pump.output(False)
        self.vna.soft_trig_arm()
        self.ref = self.vna.read_data()
        # print("Reference level: {:f}db".format(db_ref))
        f_cent, span = self.vna.freq_center_span()
        self.vna.sweep_type('cw')
        self.vna.freq_cw(f_cent + self.detuning)
        noise_ref = self.vna.read_data()
        self.snr_ref = abs(mean(noise_ref)) / std(real(noise_ref))
        self.vna.sweep_type('lin')
        self.pump.output('on')
        self.vna.soft_trig_abort()

    def _measure_snr_gain(self, f_cent):
        # f_cent,span = self.vna.freq_center_span()
        self.vna.sweep_type('cw')
        self.vna.freq_cw(f_cent)
        data = self.vna.read_data()
        snr = abs(mean(data)) / std(real(data))
        snr_gain = snr / self.snr_ref
        self.vna.sweep_type('lin')
        return snr_gain

    def _func_min(self, x: ndarray) -> float:
        """Cost function for differential evolution minimizer.

        Arguments:
            x : array_like The parameters vector, x[0] - bias value ,x[1] - pump amplitude
        Returns:
            float cost function value
        """
        self.pump.power(x[1])
        self.bias.setpoint(x[0])
        if len(x) > 2:
            self.pump.freq(2 * x[2])
            self.vna.freq_center_span((x[2], self.target_bw))
        target_gain = 10 ** (self.target_gain / 20)
        gain = abs(self.vna.read_data() / self.ref)
        gain_diff = gain - target_gain
        f_cent, span = self.vna.freq_center_span()
        snr_gain = self._measure_snr_gain(f_cent + self.detuning)
        c_point = gain_diff[int(len(gain_diff) / 2)]
        cent = 0
        if c_point > 0:
            cent = (self.w_cent * c_point) ** 2
        # return mean(diff**2) + self.w_cent*diff[int(len(diff)/2)]**2 - snr_gain**2
        # return mean(gain_diff**2) + cent - snr_gain**2
        return mean(gain_diff ** 2) + cent + (snr_gain - target_gain) ** 2

    '''
    def _func_min(self,x):
        #x[0] - bias
        #x[1] - pump
        self.pump.power(x[1])
        self.pump.freq(2*x[2])
        self.bias.setpoint(x[0])
        self.vna.freq_center_span((x[2], self.target_bw))
        data = zeros((self.n,self.points))
        for i in range(self.n):
            data[i] = abs(self.vna.read_data())
        snr = mean(mean(data,axis=0)/std(data,axis = 0)/self.snr_ref)
        return 	-snr
    '''

    def _func_min_vect(self, x: ndarray) -> ndarray | float:
        """A vectorized version of the cost function that should be
        passed to the differential evolution optimizer."""
        self._check_abort_flag()
        if len(shape(x)) == 2:
            res = zeros(shape(x)[0])
            for i, val in enumerate(x):
                self._check_abort_flag()
                res[i] = self._func_min(val)
            return res
        elif len(shape(x)) == 1:
            return self._func_min(x)
        else:
            raise ValueError('Invalid argument shape!')

    def find_gain(self, popsize=50,
                  minpopsize=5,
                  tol=0.06,
                  std_tol=1,
                  maxiter=20,
                  **kwargs):
        """Gain optimization."""

        # Setup instruments
        self.bias.setpoint(0.)
        self.vna.sweep_type('lin')
        self.vna.num_of_points(self.points)
        self.vna.freq_center_span((self.target_freq, self.target_bw))
        self.vna.bandwidth(self.bw)
        self.vna.power(self.Ps)
        self.vna.output(True)
        # Measure zero gain reference
        self._measure_ref()
        # print("Reference level: {:f}db".format(mean(self.ref)))
        self.pump.output(True)
        self.bias.output(True)
        self.pump.freq(self.target_freq * 2)
        # Optimize gain
        self.vna.soft_trig_arm()
        if self.target_freq_span == 0:
            ranges = [self.bias_range, self.pump_range]
        else:
            ranges = [self.bias_range, self.pump_range,
                      (self.target_freq - self.target_freq_span / 2, self.target_freq + self.target_freq_span / 2)]
        self.di_solver = di.DifferentialEvolutionSolver(self._func_min_vect,
                                                        ranges,
                                                        tol=tol,
                                                        # std_tol = std_tol,
                                                        std_conv=std_tol,
                                                        popsize=popsize,
                                                        minpopsize=minpopsize,
                                                        maxiter_conv=maxiter,
                                                        polish=False,
                                                        **kwargs)
        self.res = self.di_solver.solve()

        if len(self.res['x']) > 2:
            op = OperationPoint(G=self.target_gain, Pp=self.res['x'][1], I=self.res['x'][0], Fp=self.res['x'][2] * 2,
                                Fs=self.res['x'][2])
        else:
            op = OperationPoint(G=self.target_gain, Pp=self.res['x'][1], I=self.res['x'][0], Fp=self.target_freq * 2,
                                Fs=self.target_freq)
        self.set_op(op)
        f_cent, span = self.vna.freq_center_span()
        op.Gsnr = 20. * log10(self._measure_snr_gain(f_cent + self.detuning))
        self.vna.soft_trig_abort()
        return op, self.res.success

    # Setup instrument accoding to the operation point
    def set_op(self, op):
        self.bias.setpoint(op.I)
        self.pump.freq(op.Fp)
        self.pump.power(op.Pp)
        self.vna.sweep_type('lin')
        span = self.vna.freq_center_span()[1]
        self.vna.freq_center_span((op.Fs, span))

    def vna_snapshot(self, op, span=None, N=None, Ps=None, bw=None):
        if span is None:
            span = self.target_bw * 2
        if N is None:
            N = self.points * 2
        if Ps is None:
            Ps = self.Ps
        self.bias.setpoint(op.I)
        self.bias.output(1)

        self.pump.power(op.Pp)
        self.pump.output(1)
        self.pump.freq(op.Fp)

        self.vna.num_of_points(N)
        self.vna.power(Ps)
        self.vna.sweep_type('lin')
        self.vna.freq_center_span((op.Fp / 2, span))
        if bw is None:
            self.vna.bandwidth(self.bw / 10)
        else:
            self.vna.bandwidth(bw)
        self.vna.soft_trig_arm()
        S21on = self.vna.read_data()
        self.pump.output(False)
        S21off = self.vna.read_data()
        Fpoints = self.vna.freq_points()
        self.vna.soft_trig_abort()
        return S21on, S21off, Fpoints

    def snr_snapshot(self, op, span=None, N=None, Ps=None, bw=None, Nmeas=100):
        if span is None:
            span = self.target_bw * 2
        if N is None:
            N = self.points * 2
        if Ps is None:
            Ps = self.Ps
        self.bias.setpoint(op.I)
        self.bias.output(1)

        self.pump.output(0)
        self.pump.power(op.Pp)
        self.pump.freq(op.Fp)

        self.vna.num_of_points(N)
        self.vna.power(Ps)
        self.vna.sweep_type('lin')
        self.vna.freq_center_span((op.Fp / 2, span))
        if bw is None:
            self.vna.bandwidth(self.bw)
        else:
            self.vna.bandwidth(bw)

        self.vna.soft_trig_arm()
        S21off = zeros((Nmeas, N), dtype=complex)
        S21on = zeros((Nmeas, N), dtype=complex)
        for i in range(Nmeas):
            S21off[i] = self.vna.read_data()

        self.pump.output(1)
        for i in range(Nmeas):
            S21on[i] = self.vna.read_data()

        Fpoints = self.vna.freq_points()
        self.vna.soft_trig_abort()

        return S21on, S21off, Fpoints
