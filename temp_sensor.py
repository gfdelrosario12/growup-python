import os, glob, time

class DS18B20:
    def __init__(self, pin):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        base_dir = '/sys/bus/w1/devices/'
        self.device_folder = glob.glob(base_dir + '28*')[0]
        self.device_file = self.device_folder + '/w1_slave'

    def read_temp(self):
        with open(self.device_file, 'r') as f:
            lines = f.readlines()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
        equals_pos = lines[1].find('t=')
        temp_c = float(lines[1][equals_pos+2:]) / 1000.0
        return temp_c
