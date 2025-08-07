import time


class TemperatureControllerBaseClass():
    def temperature(self, chan):
        return 1.

    def wait_for_stable_T(self, chan, tolerance, hold_time, timeout=600., interval=2.):
        StartTime = time.time()
        RefTime = StartTime
        InTol = False
        Status = False
        T = self.temperature(chan)
        Tref = T
        while (1):
            T = self.temperature(chan)
            heat = self.heater_value(chan)
            Time = time.time()
            print(" Waiting for stable temperature, T={:.4f}K, heater {:f}%   ".format(T, heat), end="\r")
            if (T <= (Tref + tolerance)) and (T >= (Tref - tolerance)):
                if (Time - RefTime) >= hold_time:
                    Status = True
                    break
            else:
                RefTime = Time
                Tref = T
            if (Time - StartTime) >= timeout:
                print("Temperature controller warning: wait_for_stable_T Timeout expired")
                Status = False
                break
            time.sleep(interval)
        return T, Status
