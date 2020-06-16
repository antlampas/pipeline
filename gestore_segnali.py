# Formato segnale: segnale:timestamp:[estensioni]
# Estensioni: mittente:destinatario
# Formato segnale completo: segnale:timestamp:mittente:destinatario

from thread   import thread
from processo import processo
from time     import sleep

class gestore_segnali(processo):
    def __init__(self,configurazione,coda_ipc,lock_ipc,coda_segnali,lock_segnali):
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali = coda_segnali
        self.lock_segnali = lock_segnali
    def run(self):
        self.idle()
    def idle(self):
        pacchetto_segnale    = ""
        segnale_spacchettato = []
        segnale = timestamp = mittente = destinatario = ""
        print(type(self).__name__ + " " + "idle")
        while True:
            with self.lock_ipc:
                if not self.ipc.empty():
                    pacchetto_segnale = self.ipc.get()
            if pacchetto_segnale == "":
                continue
            segnale_spacchettato[:] = pacchetto_segnale.split(":")
            print(pacchetto_segnale)
            if len(segnale_spacchettato) == 4:
                print(4)
                print(segnale_spacchettato)
                segnale,timestamp,mittente,destinatario = zip(segnale_spacchettato)
            elif len(segnale_spacchettato) == 3:
                print(3)
                print(segnale_spacchettato)
                segnale,timestamp,mittente = zip(segnale_spacchettato)
            if segnale != "":
                print(segnale)
                print(timestamp)
                print(mittente)
                print(destinatario)
                if destinatario == str(type(self).__name__) or \
                   destinatario == "":
                    if segnale in vars():
                        vars()[segnale]
                        segnale_spacchettato[:] = []
                        segnale = timestamp = mittente = destinatario = ""
                    elif segnale == "stop":
                        break
            sleep(1)
    def avvia(self):
        print(type(self).__name__ + " " + "avviato")
        while True:
            with self.lock_ipc:
                if not self.coda_ipc.empty():
                    self.ricevi_segnale()
            with self.lock_segnali:
                if not self.coda_segnali.full():
                    self.invia_segnale()
            sleep(1)
    def invia_segnale(self):
        pacchetto_segnale    = self.coda_segnali.get()
        segnale_spacchettato = zip(pacchetto_segnale.split(":"))
        if len(segnale_spacchettato) == 2:
            segnale,destinatario = segnale_spacchettato
            if mittente != str(type(self).__name__):
                pacchetto_segnale = str(segnale)             + ":" + \
                                    str(time())              + ":" + \
                                    str(type(self).__name__) + ":" + \
                                    str(destinatario)
                with self.lock:
                    if not self.ipc.full():
                        self.coda_ipc.put(pacchetto_segnale)
                    return
            else:
                self.coda_segnali.put(pacchetto_segnale)
                return
        else:
            self.coda_segnali.put(pacchetto_segnale)
            return
    def ricevi_segnale(self):
        pacchetto_segnale       = self.coda_ipc.get()
        segnale_spacchettato[:] = pacchetto_segnale.split(":")
        if len(segnale_spacchettato)   == 4:
            segnale,timestamp,mittente,destinatario = segnale_spacchettato
        elif len(segnale_spacchettato) == 3:
            segnale,timestamp,mittente = segnale_spacchettato
        else:
            return
        if destinatario == str(type(self).__name__) or destinatario == "":
            pacchetto_segnale = segnale + ":" + timestamp + ":" + mittente
            with self.lock_segnali:
                self.coda_segnali.put(pacchetto_segnale)
            return
        else:
            self.coda_ipc.put(pacchetto_segnale)
            return
