class cycler:
    def __init__(self, state1, state2):
        self.state1 = state1
        self.state2 = state2
        self.current = state1

    def __str__(self):
        if self.current == self.state1:
            self.current = self.state2
        else:
            self.current = self.state1
        return self.current

    def getcurrent(self):
        return self.current
