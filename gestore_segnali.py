# Formato segnale: segnale:timestamp:[estensioni]
# Estensioni: mittente:destinatario
# Formato segnale completo: segnale:timestamp:mittente:destinatario

from thread   import thread
from processo import processo
from time     import sleep,time

class gestore_segnali(processo):
    """Gestore Segnali

    È progettato per essere posto come componente di un processo.
    È il componente addetto alla gestione delle comunicazioni del processo
    padre con altri processi.
    """
    def __init__(self,configurazione,padre,coda_ipc,lock_ipc,coda_segnali_entrata,lock_segnali_entrata,coda_segnali_uscita,lock_segnali_uscita):
        ################## Inizializzazione Gestore Segnali ####################
        super().__init__(coda_ipc,lock_ipc)
        self.coda_segnali_entrata = coda_segnali_entrata
        self.lock_segnali_entrata = lock_segnali_entrata
        self.coda_segnali_uscita  = coda_segnali_uscita
        self.lock_segnali_uscita  = lock_segnali_uscita
        self.padre                = str(padre)
        self.stop                 = 0
        ############### Fine Inizializzazione Gestore Segnali ##################
    def run(self):
        while True:
            self.idle()
            if self.stop: return int(-1)
    def idle(self):
        pacchetto_segnale    = ""
        segnale_spacchettato = []
        segnale = timestamp = mittente = destinatario = ""
        #print(type(self).__name__ + " " + "idle")
        while True:
            if not self.stop:
                with self.lock_ipc:
                    if not self.ipc.empty():
                        pacchetto_segnale = self.ipc.get_nowait()
                if pacchetto_segnale == "":
                    sleep(0.001)
                    continue
                else:
                    segnale_spacchettato[:] = pacchetto_segnale.split(":")
                    if len(segnale_spacchettato) == 4:
                        segnale,timestamp,mittente,destinatario = segnale_spacchettato
                    elif len(segnale_spacchettato) == 3:
                        segnale,timestamp,mittente = segnale_spacchettato
                    if segnale != "":
                        if destinatario == self.padre or destinatario == "":
                            if segnale in dir(self) and \
                                                    callable(getattr(self,segnale)):
                                q = getattr(self,segnale)()
                                segnale_spacchettato[:] = []
                                segnale = timestamp = mittente = destinatario = ""
                            elif segnale == "stop":
                                with self.lock_segnali_entrata:
                                    self.coda_segnali_entrata.put_nowait(segnale_spacchettato)
                                break
                    segnale                 = ""
                    timestamp               = ""
                    mittente                = ""
                    destinatario            = ""
                    pacchetto_segnale       = ""
                    segnale_spacchettato[:] = []
            else:
                break
    def avvia(self):
        #print(type(self).__name__ + " " + "avviato")
        i = r = 0
        while True:
            with self.lock_ipc:
                if not self.ipc.empty():
                    r = self.ricevi_segnale()
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.empty():
                    i = self.invia_segnale()
            if i == int(-1):
                self.stop = 1
            sleep(0.001)
        if self.stop:
            return int(-1)
    def invia_segnale(self):
        #print(type(self).__name__ + " " + "invia segnale")
        pacchetto_segnale = ""
        segnale           = ""
        destinatario      = ""
        segnale_spacchettato = self.coda_segnali_uscita.get_nowait()
        if len(segnale_spacchettato) == 2:
            segnale,destinatario = segnale_spacchettato
            if segnale_spacchettato == ['','']:
                segnale                 = ""
                destinatario            = ""
                segnale_spacchettato[:] = []
                return 1
            elif destinatario == str(type(self).__name__):
                if segnale == "stop":
                    return int(-1)
                else:
                    pacchetto_segnale       = ""
                    segnale_spacchettato[:] = []
                    return 1
            elif destinatario == self.padre:
                pacchetto_segnale       = ""
                segnale_spacchettato[:] = []
                return 1
            else:
                pacchetto_segnale = str(segnale)      + ":" + \
                                    str(time())       + ":" + \
                                    self.padre        + ":" + \
                                    str(destinatario)
                with self.lock_ipc:
                    if not self.ipc.full():
                        self.ipc.put_nowait(pacchetto_segnale)
                return 0
        else:
            segnale_spacchettato[:] = []
            return 0
    def ricevi_segnale(self):
        #print(type(self).__name__ + " " + "ricevi segnale")
        pacchetto_segnale = segnale = timestamp = mittente = destinatario = ""
        segnale_spacchettato    = []
        pacchetto_segnale       = self.ipc.get_nowait()
        segnale_spacchettato[:] = pacchetto_segnale.split(":")
        if   len(segnale_spacchettato) == 4:
            segnale,timestamp,mittente,destinatario = segnale_spacchettato
        elif len(segnale_spacchettato) == 3:
            segnale,timestamp,mittente              = segnale_spacchettato
        else:
            return 1
        if destinatario == self.padre or destinatario == "":
            with self.lock_segnali_entrata:
                self.coda_segnali_entrata.put_nowait(segnale)
            return 1
        else:
            self.ipc.put_nowait(pacchetto_segnale)
            return 0
