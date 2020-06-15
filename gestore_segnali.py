# Formato segnale: segnale:timestamp:[estensioni]
# Estensioni: mittente:destinatario
# Formato segnale completo: segnale:timestamp:mittente:destinatario

from thread import thread
from time   import sleep

class gestore_segnali(thread):
    def __init__(self,configurazione,coda_ipc,lock_ipc,coda_segnali,lock_segnali):
        super(gestore_segnali,self).__init__(coda_ipc,lock_ipc)
        self.ipc          = coda_ipc
        slef.lock_ipc     = lock_ipc
        self.coda_segnali = coda_segnali
        self.lock_segnali = lock_segnali
    def run(self):
        self.idle()
    def idle(self):
        pacchetto_segnale = ""
        while True:
            sleep(0.001)
            with self.lock_ipc:
                if not self.ipc.empty():
                    pacchetto_segnale = self.ipc.get()
            segnale,timestamp,mittente,destinatario = zip(pacchetto_segnale)
            if destinatario == str(type(self).__name__) or destinatario == "":
                if segnale in vars():
                    vars()[segnale]
                elif segnale == "stop":
                    break
    def avvia(self):
        sleep(0.001)
        while True:
            with self.lock_ipc:
                if not self.coda_ipc.empty():
                    self.ricevi_segnale()
            with self.lock_segnali:
                if not self.coda_segnali.empty():
                    self.invia_segnale()
    def invia_segnale(self):
        pacchetto_segnale    = self.coda_segnali.get()
        segnale_spacchettato = zip(pacchetto_segnale.split(":"))
        if len(segnale_spacchettato) > 2:
            segnale,destinatario = segnale_spacchettato
            if mittente != str(type(self).__name__):
                pacchetto_segnale = str(segnale)             + ":" + \
                                    str(time())              + ":" + \
                                    str(type(self).__name__) + ":" + \
                                    str(destinatario)
                with self.lock:
                    if not self.ipc.full():
                        self.coda_ipc.put(pacchetto_segnale)
            else:
                self.coda_segnali.put(pacchetto_segnale)
        else:
            self.coda_segnali.put(pacchetto_segnale)
    def ricevi_segnale(self):
        pacchetto_segnale = self.coda_ipc.get()
        segnale,timestamp,mittente,destinatario =
                                               zip(pacchetto_segnale.split(":"))
        if destinatario == str(type(self).__name__) or destinatario == "":
            pacchetto_segnale = segnale + ":" + timestamp + ":" + mittente
            with self.lock_segnali:
                self.coda_segnali.put(pacchetto_segnale)
        else:
            self.coda_ipc.put(pacchetto_segnale)
