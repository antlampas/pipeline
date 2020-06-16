# Formato segnale: segnale:timestamp:[estensioni]
# Estensioni: mittente:destinatario
# Formato segnale completo: segnale:timestamp:mittente:destinatario

from thread   import thread
from processo import processo
from time     import sleep

class gestore_segnali(processo):
    """Gestore Segnali

    È progettato per essere posto come componente di un processo.
    È il componente addetto alla gestione delle comunicazioni del processo
    padre con altri processi.
    """
    def __init__(self,configurazione,padre,coda_ipc,lock_ipc,coda_segnali,lock_segnali):
        ################## Inizializzazione Gestore Segnali ####################
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali = coda_segnali
        self.lock_segnali = lock_segnali
        self.padre        = str(padre)
        ############### Fine Inizializzazione Gestore Segnali ##################
    def run(self):
        self.idle()
    def idle(self):
        pacchetto_segnale    = ""
        segnale_spacchettato = []
        segnale = timestamp = mittente = destinatario = ""
        # print(type(self).__name__ + " " + "idle")
        while True:
            with self.lock_ipc:
                if not self.ipc.empty():
                    pacchetto_segnale = self.ipc.get_nowait()
            if pacchetto_segnale == "":
                sleep(0.001)
                continue
            else:
                segnale_spacchettato[:] = pacchetto_segnale.split(":")
                print(pacchetto_segnale)
                print(segnale_spacchettato)
                if len(segnale_spacchettato) == 4:
                    segnale,timestamp,mittente,destinatario = \
                                                       zip(segnale_spacchettato)
                    segnale      = segnale[0]
                    timestamp    = timestamp[0]
                    mittente     = mittente[0]
                    destinatario = destinatario[0]
                elif len(segnale_spacchettato) == 3:
                    segnale,timestamp,mittente = zip(segnale_spacchettato)
                    segnale   = segnale[0]
                    timestamp = timestamp[0]
                    mittente  = mittente[0]
                if segnale != "":
                    if destinatario == self.padre or destinatario == "":
                        if segnale in dir(self) and \
                                                callable(getattr(self,segnale)):
                            getattr(self,segnale)()
                            segnale_spacchettato[:] = []
                            segnale = timestamp = mittente = destinatario = ""
                        elif segnale == "stop":
                            with self.lock_segnali:
                                self.coda_segnali.put_nowait(segnale_spacchettato)
                            break
                segnale                 = ""
                timestamp               = ""
                mittente                = ""
                destinatario            = ""
                pacchetto_segnale       = ""
                segnale_spacchettato[:] = []
    def avvia(self):
        print(type(self).__name__ + " " + "avviato")
        stop = 0
        while True:
            if not stop:
                with self.lock_ipc:
                    if not self.ipc.empty():
                        self.ricevi_segnale()
                with self.lock_segnali:
                    if not self.coda_segnali.empty():
                        self.invia_segnale()
                    if not self.coda_segnali.empty():
                        s = self.coda_segnali.get_nowait()
                        if s != ['','']:
                            self.coda_segnali.put_nowait(s)
                            s = []
                        else:
                            stop = 1
            else:
                break
            sleep(0.001)
    def invia_segnale(self):
        print(type(self).__name__ + " " + "invia segnale")
        segnale_spacchettato = self.coda_segnali.get_nowait()
        print(segnale_spacchettato)
        if len(segnale_spacchettato) == 2:
            segnale,destinatario = zip(segnale_spacchettato)
            if destinatario != padre and destinatario != "":
                pacchetto_segnale = str(segnale)      + ":" + \
                                    str(time())       + ":" + \
                                    padre             + ":" + \
                                    str(destinatario)
                with self.lock:
                    if not self.ipc.full():
                        self.ipc.put_nowait(pacchetto_segnale)
                    return
            elif destinatario == type(self).__name__ and \
                 destinatario != ""                  and \
                 segnale == "stop":
                self.coda_segnali.put_nowait(['',''])
            else:
                self.coda_segnali.put_nowait(segnale_spacchettato)
                return
        elif len(segnale_spacchettato) < 2:
            segnale_spacchettato[:] = []
            return
        else:
            self.coda_segnali.put_nowait(segnale_spacchettato)
            return
    def ricevi_segnale(self):
        print(type(self).__name__ + " " + "ricevi segnale")
        pacchetto_segnale       = self.ipc.get_nowait()
        segnale_spacchettato = pacchetto_segnale.split(":")
        print(pacchetto_segnale)
        print(segnale_spacchettato)
        if len(segnale_spacchettato)   == 4:
            segnale,timestamp,mittente,destinatario = segnale_spacchettato
        elif len(segnale_spacchettato) == 3:
            segnale,timestamp,mittente = segnale_spacchettato
        else:
            return
        if destinatario == self.padre or destinatario == "":
            pacchetto_segnale = segnale + ":" + timestamp + ":" + mittente
            with self.lock_segnali:
                self.coda_segnali.put_nowait(segnale_spacchettato)
                segnale_spacchettato[:] = []
            return
        else:
            self.ipc.put_nowait(pacchetto_segnale)
            pacchetto_segnale = ""
            return
