import sys
import time

ROTATION=r"/-\|"
class RotaterPlugin:
    def __init__(self, rotdelay=0.1):
        self.rotation = -1
        self.rotatedelay = rotdelay
    def rotate(self, noDelay=None):
        self.rotation = (self.rotation + 1) % len(ROTATION)
        sys.stdout.write("\010" + ROTATION[self.rotation])
        sys.stdout.flush()
        if(not noDelay):
            time.sleep(self.rotatedelay)
    def write(self, *msg):
        if self.rotation > -1:
            sys.stdout.write("\010")
        print ('%s '*len(msg) % msg)[:-1]
        sys.stdout.write(" ")

