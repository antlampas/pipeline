from multiprocessing      import Process,Queue,Lock
from time                 import time,sleep

from oggetto              import oggetto
from gestore_segnali      import gestore_segnali

class gestore_pipeline(oggetto):
    def __init__(self,file_configurazione,coda_ipc,lock_ipc):
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
        super().__init__(impostazioni,coda_ipc,lock_ipc)

        self.operazioni                      = {}
        self.ipc_operazioni                  = {}
        self.lock_ipc_operazioni             = {}
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
                self.ipc_operazioni[valore]                  = Queue()
                self.lock_ipc_operazioni[valore]             = Lock()
                self.coda_segnali_entrata_operazioni[valore] = Queue()
                self.lock_segnali_entrata_operazioni[valore] = Lock()
                self.coda_segnali_uscita_operazioni[valore]  = Queue()
                self.lock_segnali_uscita_operazioni[valore]  = Lock()
                self.gestore_segnali_operazioni[valore]      = gestore_segnali(
                                   lista_segnali,
                                   type(self).__name__,
                                   coda_ipc,
                                   lock_ipc,
                                   self.coda_segnali_entrata_operazioni[valore],
                                   self.lock_segnali_entrata_operazioni[valore],
                                   self.coda_segnali_uscita_operazioni[valore],
                                   self.lock_segnali_uscita_operazioni[valore])
                self.gestore_segnali_operazioni[valore].start()
                self.operazioni[valore] = globals()[valore](
                                               str(valore + ".conf"),
                                               self.ipc_operazioni[valore],
                                               self.lock_ipc_operazioni[valore])
                with self.lock_ipc_operazioni[valore]:
                    self.ipc_operazioni[valore].put("avvia:"+str(time())+":"+type(self).__name__+":")
        for nome,operazione in self.operazioni.items():
            operazione.start()
    def idle(self):
        while True:
            for (oggetto,lock_entrata),         \
                (oggetto,lock_uscita),          \
                (oggetto,coda_segnali_entrata), \
                (oggetto,coda_segnali_uscita)   \
                in                              \
                zip(self.lock_segnali_entrata_operazioni.items(), \
                self.lock_segnali_uscita_operazioni.items(),  \
                self.coda_segnali_entrata_operazioni.items(), \
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
                if segnale == "avvia":
                    for lock,ipc in self.lock_ipc,self.ipc:
                        with lock:
                            ipc.put_nowait("avvia:"+str(time()) + ":" + \
                                                       str(type(self).__name__))
            sleep(0.01)
    def avvia(self):
        while True:
            segnale = ""
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            if segnale == "stop":
                uscita = ["stop","gestore_segnali"]
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(uscita)
                return int(-1)
            else:
                pass
