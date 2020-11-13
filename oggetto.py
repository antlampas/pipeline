"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""
import logging

from multiprocessing import Process,Lock,Queue
from gestore_segnali import gestore_segnali

class oggetto(Process):
    """Oggetto

    Classe base per tutti gli oggetti del framework. Ha le caratterisiche di
    base per la gestione del processo associato ed imposta ed avvia il Gestore
    Segnali dell'oggetto
    """
    def __init__(self,
                 coda_ipc_entrata,
                 lock_ipc_entrata,
                 coda_ipc_uscita,
                 lock_ipc_uscita):
        #################### Inizializzazione oggetto ##########################
        super().__init__()
        self.impostazioni_in_aggiornamento = 0
        self.stato = "idle"
        # Coda in cui il Gestore Segali mette i segnali ricevuti
        self.coda_segnali_entrata = Queue()
        self.lock_segnali_entrata = Lock()
        # Coda in cui l'oggetto mette i segnali da inviare all'esterno. È presa
        # in carico dal Gestore Segnali
        self.coda_segnali_uscita  = Queue()
        self.lock_segnali_uscita  = Lock()
        ######### Impostazione ed inizializzazione del Gestore Segnali #########
        self.gestore_segnali      = gestore_segnali(type(self).__name__,
                                                    coda_ipc_entrata,
                                                    lock_ipc_entrata,
                                                    coda_ipc_uscita,
                                                    lock_ipc_uscita,
                                                    self.coda_segnali_entrata,
                                                    self.lock_segnali_entrata,
                                                    self.coda_segnali_uscita,
                                                    self.lock_segnali_uscita)
        self.gestore_segnali.start()
        logging.info(str(type(self).__name__) + ": avviando gestore segnali")
        with self.lock_segnali_uscita:
            self.coda_segnali_uscita.put_nowait(["avvia","gestore_segnali"])
        ################## Fine Inizializzazione oggetto #######################
    def run(self):
        """Punto d'entrata del processo/thread"""
        # Entra nello stato richiesto
        while True:
            s = getattr(self,self.stato)()
            if s != 0:
                break
        return int(s)
    def idle(self):
        """Stato Idle
        """
        pass
    def avvia(self):
        """Stato Avviato
        """
        pass
    def ferma(self):
        """Stato Fermato
        """
        pass
    def termina(self):
        """Stato Terminazione
        """
        pass
    def sospendi(self):
        """Stato Sospensione
        """
        pass
    def uccidi(self):
        """Stato Uccisione
        """
        pass
    def leggi_segnale(self,timeout=None):
        """Lettura del primo segnale in entrata
        """
        pacchetto_segnale = []
        segnale           = ""
        mittente          = ""
        destinatario      = ""
        timestamp         = 0
        with self.lock_timeout(self.lock_segnali_uscita,timeout) as acquisito:
            if acquisito:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale[:] = self.coda_segnali_entrata.get_nowait()
                else:
                    return ["Coda Segnali Entrata Vuota","","",""]
            else:
                return ["Acquisizione Lock Coda Entrata fallita","","",""]
        if len(pacchetto_segnale) == 4:
            segnale,mittente,destinatario,timestamp = pacchetto_segnale
        elif len(pacchetto_segnale) == 3:
            segnale,mittente,timestamp = pacchetto_segnale
        elif len(pacchetto_segnale) == 0:
            pass
        else:
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.full():
                    self.coda_segnali_uscita.put_nowait(["segnale mal formato",
                                                         ""])
        if segnale == "":
            return int(-4)
        elif segnale == "stop":
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.full():
                    self.coda_segnali_uscita.put_nowait(["stop",
                                                         "gestore_segnali"])
            return int(-1)
        else:
            return [segnale,mittente,destinatario,timestamp]
    def invia_segnale(self,segnale,timeout=None):
        """Lettura del segnale in uscita
        """
        stato = 0
        with self.lock_timeout(self.lock_segnali_uscita,timeout) as acquisito:
            if acquisito:
                if not self.coda_segnali_uscita.full():
                    self.coda_segnali_uscita.put_nowait(segnale)
                    stato = 1
                else:
                    stato = int(-1)
            else:
                stato = int(-2)
        return stato
    @contextmanager
    def lock_timeout(lock, timeout=1):
        """Implementazione del Lock con Timeout
        """
        result = lock.acquire(timeout=timeout)
        yield result
        if result:
            lock.release()
