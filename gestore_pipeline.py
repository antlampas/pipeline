from multiprocessing      import Process,Queue,Lock
from time                 import time,sleep
from random               import uniform

#Framework
from oggetto              import oggetto
from gestore_segnali      import gestore_segnali

# Operazioni
from attesa_cassa         import attesa_cassa
from riconoscimento_cassa import riconoscimento_cassa
from acquisizione_foto    import acquisizione_foto
from invia_foto           import invia_foto

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
    def avvia(self):
        print(type(self).__name__ + " avviato")
        while True:
            segnale = ""
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
            for (oggetto,lock_entrata),         \
                (oggetto,lock_uscita),          \
                (oggetto,coda_segnali_entrata), \
                (oggetto,coda_segnali_uscita)   \
                in                              \
                zip(self.lock_segnali_entrata_operazioni.items(), \
                self.lock_segnali_uscita_operazioni.items(),      \
                self.coda_segnali_entrata_operazioni.items(),     \
                self.coda_segnali_uscita_operazioni.items()):
                segnale = ""
                with lock_entrata:
                    if not coda_segnali_entrata.empty():
                        segnale = coda_segnali_entrata.get_nowait()
                if segnale == "esci":
                    uscita = ["stop","gestore_segnali"]
                    with lock_uscita:
                        coda_segnali_uscita.put_nowait(uscita)
                    return int(-1)
                elif segnale == "avvia":
                    with lock_uscita:
                        coda_segnali_uscita.put_nowait(
                                                  [str(type(self).__name__),""])
                elif segnale != "":
                    pass
            sleep(0.001)
