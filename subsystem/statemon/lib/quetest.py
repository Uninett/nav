import threading

class mytest:
    def __init__(self):
        self.hasFinished=threading.Event()

    def run(self):
        try:
            for i in ['foo', 'bar']:
                print i
        except:
            print 'noe trynet'

        self.hasFinished.set()

