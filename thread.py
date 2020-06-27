from threading import Thread,Lock

class thread(Thread):
    """Interfaccia Thread

    Interfaccia per quando si deve creare un thread
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
