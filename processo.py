from multiprocessing import Process

class processo(Process):
    def __init__(self,coda_ipc,lock_ipc):
        super(processo,self).__init__()
        self.coda_ipc = coda_ipc
        self.lock     = lock_ipc
    def idle(self):
        pass
    def avvia(self):
        pass
    def ferma(self):
        pass
    def termina(self):
        pass
    def sospendi(self):
        pass
    def uccidi(self):
        pass
