#from threading import Lock
from multiprocessing import Lock,Queue
#from queue           import Queue
from processo        import processo
from gestore_segnali import gestore_segnali
from time            import sleep,time

class oggetto(processo):
    def __init__(self,lista_segnali,coda_ipc,lock_ipc):
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali_entrata = Queue()
        self.coda_segnali_uscita  = Queue()
        self.lock_segnali_entrata = Lock()
        self.lock_segnali_uscita  = Lock()
        self.gestore_segnali      = gestore_segnali(lista_segnali,
                                                    type(self).__name__,
                                                    coda_ipc,
                                                    lock_ipc,
                                                    self.coda_segnali_entrata,
                                                    self.lock_segnali_entrata,
                                                    self.coda_segnali_uscita,
                                                    self.lock_segnali_uscita)
        self.gestore_segnali.start()
    def run(self):
        self.idle()
    def idle(self):
        segnale= ""
        while True:
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            if segnale == "esci":
                uscita = ["stop","gestore_segnali"]
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(uscita)
                return int(-1)
            elif segnale in dir(self) and callable(getattr(self,segnale)):
                q = getattr(self,segnale)()
            sleep(0.01)
