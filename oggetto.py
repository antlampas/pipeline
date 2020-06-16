#from threading import Lock
from multiprocessing import Lock
from queue           import Queue
from processo        import processo
from gestore_segnali import gestore_segnali
from time            import sleep

class oggetto(processo):
    def __init__(self,configurazione,coda_ipc,lock_ipc):
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali    = Queue()
        self.lock_segnali    = Lock()
        self.gestore_segnali = gestore_segnali(configurazione,
                                               coda_ipc,
                                               lock_ipc,
                                               self.coda_segnali,
                                               self.lock_segnali)
        self.gestore_segnali.start()
    def run(self):
        self.idle()
    def idle(self):
        print(type(self).__name__ + " " + "idle")
        while True:
            with self.lock_segnali:
                if not self.coda_segnali.empty():
                    print(self.coda_segnali.get())
            sleep(1)
