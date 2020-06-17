#from threading import Lock
from multiprocessing import Lock,Queue
#from queue           import Queue
from processo        import processo
from gestore_segnali import gestore_segnali
from time            import sleep,time

class oggetto(processo):
    def __init__(self,configurazione,coda_ipc,lock_ipc):
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali_entrata = Queue()
        self.coda_segnali_uscita  = Queue()
        self.lock_segnali_entrata = Lock()
        self.lock_segnali_uscita  = Lock()
        self.ipc                  = coda_ipc
        self.lock_ipc             = lock_ipc
        self.gestore_segnali      = gestore_segnali(configurazione,
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
        # print(type(self).__name__ + " " + "idle")
        segnale = [] # [segnale , mittente]
        while True:
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            if segnale == "esci":
                uscita = ["stop","gestore_segnali"]
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(uscita)
                # with self.lock_ipc:
                #     pacchetto_segnale = "terminato:" + str(time()) + ":" + type(self).__name__ + ":"
                #     self.ipc.put_nowait(pacchetto_segnale)
                return int(-1)
            segnale = []
            sleep(0.01)
