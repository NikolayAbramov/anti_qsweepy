from anti_qsweepy.drivers import *
from numpy import *
import time

def warmup_until(T):
	#Stop automation
	tc.instr.query('SET:SYS:DR:ACTN:STOP')
	#Stop turbo
	tc.instr.query('SET:DEV:TURB1:PUMP:SIG:STATE:OFF')
	#Stop forepump
	tc.instr.query('SET:DEV:FP:PUMP:SIG:STATE:OFF')
	#Stop compressor
	tc.instr.query('SET:DEV:COMP:PUMP:SIG:STATE:OFF')
	#Close all valves
	tc.instr.query('SET:DEV:V1:VALV:SIG:STATE:CLOSE')
	tc.instr.query('SET:DEV:V5:VALV:SIG:STATE:CLOSE')
	tc.instr.query('SET:DEV:V9:VALV:SIG:STATE:CLOSE')
	#Wait for turbo to slowdown
	tc.instr.query('READ:DEV:TURB1:PUMP:SIG:SPD')