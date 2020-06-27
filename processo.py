from multiprocessing import Process

class processo(Process):
    """Interfaccia Processo

    Interfaccia per quando si deve creare un Processo
    """
    def __init__(self,coda_ipc,lock_ipc):
        super().__init__()
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
