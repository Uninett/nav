import sys
import time

ROTATION=r"/-\|"
class RotaterPlugin:
    def __init__(self, rotdelay=0.1):
        self.rotation = -1
        self.rotatedelay = rotdelay
    def rotate(self, noDelay=None):
        if self.rotation > -1:
            sys.stdout.write("\010")
        self.rotation = (self.rotation + 1) % len(ROTATION)
        sys.stdout.write(ROTATION[self.rotation])
        sys.stdout.flush()
        if(not noDelay):
            time.sleep(self.rotatedelay)
    def write(self, *msg):
        if self.rotation > -1:
            sys.stdout.write("\010")
        print ('%s '*len(msg) % msg)[:-1]
        sys.stdout.write(" ")


def __test():
    import random
    foo = RotaterPlugin()
    messages = ['Calculation gravitation...',
                'Getting nuclear blast ratio...',
                ]
    try:
        while 1:
            if random.random() > 0.9:
                foo.write(random.choice(messages))
            foo.rotate()
    except:
        sys.exit(0)

if __name__ == '__main__':
    __test()

            
