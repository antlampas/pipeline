#from threading import Lock
from multiprocessing import Lock
from queue           import Queue
from processo        import processo
from gestore_segnali import gestore_segnali

class oggetto(processo):
    def __init__(self,configurazione,coda_ipc,lock_ipc):
        super(oggetto, self).__init__(coda_ipc,lock_ipc)
        self.ipc             = coda_ipc
        self.lock_ipc        = lock_ipc
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
                print(self.coda_segnali.get())
            sleep(0.001)
