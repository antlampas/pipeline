# Formato segnale: segnale:timestamp:[estensioni]
# Estensioni: mittente:destinatario
# Formato segnale completo: segnale:timestamp:mittente:destinatario
from multiprocessing import Process
# from Threading       import Thread
from time            import sleep,time
from random          import uniform

# from thread          import thread
# from processo        import processo

class gestore_segnali(Process):
    """Gestore Segnali

    È progettato per essere posto come componente di un processo.
    È il componente addetto alla gestione delle comunicazioni del processo
    padre con altri processi.
    """

    def __init__(self,
                 padre,
                 coda_ipc_entrata,
                 lock_ipc_entrata,
                 coda_ipc_uscita,
                 lock_ipc_uscita,
                 coda_segnali_entrata,
                 lock_segnali_entrata,
                 coda_segnali_uscita,
                 lock_segnali_uscita):
        super().__init__()
        ################## Inizializzazione Gestore Segnali ####################
        self.ipc_entrata          = coda_ipc_entrata
        self.lock_ipc_entrata     = lock_ipc_entrata
        self.ipc_uscita           = coda_ipc_uscita
        self.lock_ipc_uscita      = lock_ipc_uscita
        self.coda_segnali_entrata = coda_segnali_entrata
        self.lock_segnali_entrata = lock_segnali_entrata
        self.coda_segnali_uscita  = coda_segnali_uscita
        self.lock_segnali_uscita  = lock_segnali_uscita
        self.padre                = str(padre)
        self.stop                 = 0
        ############### Fine Inizializzazione Gestore Segnali ##################
    def run(self):
        self.idle()
        if self.stop:
            return int(-1)
    def idle(self):
        if self.padre == "gestore_pipeline":
            print(type(self).__name__ + " " + self.padre + " " + "idle")
        pacchetto_segnale    = ""
        segnale_spacchettato = []
        segnale = timestamp = mittente = destinatario = ""
        while True:
            if not self.stop:
                with self.lock_ipc_entrata:
                    if not self.ipc_entrata.empty():
                        pacchetto_segnale = self.ipc_entrata.get_nowait()
                if pacchetto_segnale == "":
                    sleep(0.001)
                    continue
                else:
                    segnale_spacchettato[:] = pacchetto_segnale.split(":")
                    if len(segnale_spacchettato) == 4:
                        segnale,timestamp,mittente,destinatario = segnale_spacchettato
                    elif len(segnale_spacchettato) == 3:
                        segnale,timestamp,mittente = segnale_spacchettato
                    else:
                        continue
                    if segnale != "":
                        if destinatario == type(self).__name__ or destinatario == "":

                            if segnale in dir(self):
                                getattr(self,segnale)()
                                segnale_spacchettato[:] = []
                                segnale = timestamp = mittente = destinatario = ""
                            elif segnale == "stop":
                                self.stop = int(1)
                                break
                    segnale                 = ""
                    timestamp               = ""
                    mittente                = ""
                    destinatario            = ""
                    pacchetto_segnale       = ""
                    segnale_spacchettato[:] = []
            else:
                break
        with self.lock_ipc_uscita:
            pacchetto_segnale = "terminato:" + str(time()) + ":" + type(self).__name__ + ":"
            self.ipc_uscita.put_nowait(pacchetto_segnale)
    def avvia(self):
        print(type(self).__name__ + " " + self.padre + " " + "avviato")
        i = r = 0
        while True:
            with self.lock_ipc_entrata:
                if not self.ipc_entrata.empty():
                    r = self.ricevi_segnale()
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.empty():
                    i = self.invia_segnale()
            if i == int(-1):
                self.stop = 1
                break
            sleep(0.001)
        if self.stop:
            return int(-1)
    def invia_segnale(self):
        # print("Invia segnale")
        pacchetto_segnale = segnale = destinatario = ""
        segnale_spacchettato    = []
        segnale_spacchettato[:] = self.coda_segnali_uscita.get_nowait()
        if segnale_spacchettato:
            if len(segnale_spacchettato) == 2:
                segnale,destinatario = segnale_spacchettato
                if segnale == "" and destinatario == "":
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
                    with self.lock_ipc_uscita:
                        if not self.ipc_uscita.full():
                            self.ipc_uscita.put_nowait(pacchetto_segnale)
                    return 0
            else:
                segnale_spacchettato[:] = []
                return 0
    def ricevi_segnale(self):
        # print("Ricevi segnale")
        pacchetto_segnale = segnale = timestamp = mittente = destinatario = ""
        segnale_spacchettato    = []
        pacchetto_segnale       = self.ipc_entrata.get_nowait()
        segnale_spacchettato[:] = pacchetto_segnale.split(":")
        if segnale_spacchettato:
            if   len(segnale_spacchettato) == 4:
                segnale,timestamp,mittente,destinatario = segnale_spacchettato
            elif len(segnale_spacchettato) == 3:
                segnale,timestamp,mittente              = segnale_spacchettato
            else:
                return 1
            if destinatario == self.padre or destinatario == "":
                with self.lock_segnali_entrata:
                    if not self.coda_segnali_entrata.full():
                        self.coda_segnali_entrata.put_nowait(segnale)
                return 1
            else:
                return 0
class gestore_pipeline(oggetto):
    def __init__(self,
                 file_configurazione,
                 coda_ipc_entrata,
                 lock_ipc_entrata,
                 coda_ipc_uscita,
                 lock_ipc_uscita):
        super().__init__(coda_ipc_entrata,
                         lock_ipc_entrata,
                         coda_ipc_uscita,
                         lock_ipc_uscita)
        configurazione       = []
        lista_configurazione = []
        impostazioni         = []
        lista_segnali        = []

        with open(file_configurazione) as f:
            configurazione = f.readlines()
        lista_configurazione[:] = [x.strip() for x in configurazione]

        for impostazione in lista_configurazione:
            nome,valore = impostazione.split(" ")
            impostazioni.append([nome,valore])

        self.operazioni                      = {}
        self.ipc_entrata_operazioni          = {}
        self.lock_ipc_entrata_operazioni     = {}
        self.ipc_uscita_operazioni           = {}
        self.lock_ipc_uscita_operazioni      = {}
        self.coda_segnali_entrata_operazioni = {}
        self.coda_segnali_uscita_operazioni  = {}
        self.lock_segnali_entrata_operazioni = {}
        self.lock_segnali_uscita_operazioni  = {}
        self.gestore_segnali_operazioni      = {}

        for impostazione in impostazioni:
            nome,valore = impostazione
            if nome == "segnale":
                lista_segnali.append(valore)
        for impostazione in impostazioni:
            nome,valore = impostazione
            if nome == "operazione":
                self.ipc_entrata_operazioni[valore]          = Queue()
                self.lock_ipc_entrata_operazioni[valore]     = Lock()
                self.ipc_uscita_operazioni[valore]           = Queue()
                self.lock_ipc_uscita_operazioni[valore]      = Lock()
                self.coda_segnali_entrata_operazioni[valore] = Queue()
                self.lock_segnali_entrata_operazioni[valore] = Lock()
                self.coda_segnali_uscita_operazioni[valore]  = Queue()
                self.lock_segnali_uscita_operazioni[valore]  = Lock()
                self.gestore_segnali_operazioni[valore]      = gestore_segnali(
                                   type(self).__name__,
                                   self.ipc_entrata_operazioni[valore],
                                   self.lock_ipc_entrata_operazioni[valore],
                                   self.ipc_uscita_operazioni[valore],
                                   self.lock_ipc_uscita_operazioni[valore],
                                   self.coda_segnali_entrata_operazioni[valore],
                                   self.lock_segnali_entrata_operazioni[valore],
                                   self.coda_segnali_uscita_operazioni[valore],
                                   self.lock_segnali_uscita_operazioni[valore])
                self.gestore_segnali_operazioni[valore].start()
                self.operazioni[valore] = globals()[valore](
                                       str(valore + ".conf"),
                                       self.ipc_uscita_operazioni[valore],
                                       self.lock_ipc_uscita_operazioni[valore],
                                       self.ipc_entrata_operazioni[valore],
                                       self.lock_ipc_entrata_operazioni[valore])
                with self.lock_ipc_uscita_operazioni[valore]:
                    self.ipc_uscita_operazioni[valore].put_nowait("avvia:"  +  \
                                                           str(time()) + ":" + \
                                                           type(self).__name__ \
                                                           + ":")
                with self.lock_ipc_uscita_operazioni[valore]:
                    self.ipc_uscita_operazioni[valore].put_nowait("avvia:"  +  \
                                                           str(time()) + ":" + \
                                                           type(self).__name__ \
                                                           + ":" + valore)
        for nome,operazione in self.operazioni.items():
            operazione.start()
    def idle(self):
        print(type(self).__name__ + " idle")
        segnale_idle = ["idle",""]
        while True:
            segnale = ""
            with self.lock_segnali_uscita:
                self.coda_segnali_uscita.put_nowait(segnale_idle)
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()


            if segnale == "":
                sleep(uniform(0.001,0.200))
                continue
            elif segnale == "stop":
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["stop", \
                                                         "gestore_segnali"])
                return int(-1)
            else:
                if segnale in dir(self):
                    getattr(self,segnale)()
            sleep(uniform(0.001,0.200))
    def avvia(self):
        print(type(self).__name__ + " avviato")
        while True:
            segnale = ""
            ################# Ricevi messaggi dall'esterno #####################
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            if segnale == "stop":
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(
                                                     ["stop","gestore_segnali"])
                return int(-1)
            elif segnale != "":
                pass
            else:
                pass
            ############## Fine ricezione messaggi dall'esterno ################
            ########## Comunicazione con le operazioni della pipeline ##########
            for (oggetto,lock_entrata),                           \
                (oggetto,lock_uscita),                            \
                (oggetto,coda_segnali_entrata),                   \
                (oggetto,coda_segnali_uscita)                     \
                in                                                \
                zip(self.lock_segnali_entrata_operazioni.items(), \
                self.lock_segnali_uscita_operazioni.items(),      \
                self.coda_segnali_entrata_operazioni.items(),     \
                self.coda_segnali_uscita_operazioni.items()):
                segnale = destinazione = ""
                # print(type(self).__name__ + ": Controllando " + oggetto)
                with lock_uscita:
                    if not coda_segnali_entrata.empty():
                        segnale = coda_segnali_entrata.get_nowait()
                if segnale:
                    # print(type(self).__name__ + ": " + segnale)
                    if segnale != "":
                        if destinazione == type(self).__name__:
                            # print(type(self).__name__ + ": " + segnale)
                            # print(type(self).__name__ + ": " + destinazione)
                            pass
                        elif destinazione in self.operazioni:
                            # print(type(self).__name__ + ": " + segnale)
                            # print(type(self).__name__ + ": " + destinazione)
                            with self.lock_segnali_uscita_operazioni[destinazione]:
                                self.coda_segnali_uscita_operazioni[destinazione].put_nowait([segnale,destinazione])
                        elif destinazione == "":
                            # print(type(self).__name__ + ": " + segnale)
                            # print(type(self).__name__ + ": " + destinazione)
                            for operazione in self.operazioni:
                                if operazione == oggetto:
                                    continue
                                else:
                                    with self.lock_segnali_uscita_operazioni[operazione]:
                                        self.coda_segnali_uscita_operazioni[operazione].put_nowait([segnale,destinazione])

            ############## Fine comunicazione con le operazioni ################
            sleep(0.01)
