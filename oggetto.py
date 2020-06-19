from multiprocessing import Process,Lock,Queue
from gestore_segnali import gestore_segnali
from time            import sleep,time

class oggetto(Process):
    def __init__(self,
                 coda_ipc_entrata,
                 lock_ipc_entrata,
                 coda_ipc_uscita,
                 lock_ipc_uscita):
        super().__init__()
        self.coda_segnali_entrata = Queue()
        self.lock_segnali_entrata = Lock()
        self.coda_segnali_uscita  = Queue()
        self.lock_segnali_uscita  = Lock()
        self.gestore_segnali      = gestore_segnali(type(self).__name__,
                                                    coda_ipc_entrata,
                                                    lock_ipc_entrata,
                                                    coda_ipc_uscita,
                                                    lock_ipc_uscita,
                                                    self.coda_segnali_entrata,
                                                    self.lock_segnali_entrata,
                                                    self.coda_segnali_uscita,
                                                    self.lock_segnali_uscita)
        self.gestore_segnali.start()
        with lock_ipc_uscita:
            coda_ipc_uscita.put_nowait("avvia:" + str(time()) + ":" + \
                                                      type(self).__name__ + ":")
    def run(self):
        self.idle()
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
