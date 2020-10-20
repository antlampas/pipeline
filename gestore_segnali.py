"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

from multiprocessing import Process
# from Threading       import Thread
from time            import sleep,time
from logging         import info

class gestore_segnali(Process):
    """Gestore Segnali

    È progettato per essere posto come componente di un processo.
    È il componente addetto alla gestione delle comunicazioni del processo
    padre con altri processi.

    Formato segnale: segnale:timestamp:[estensioni]
    Estensioni implementate: mittente:destinatario
    Formato segnale completo: segnale:timestamp:mittente:destinatario

    Fondamentalmente fa da "cuscinetto" tra il canale di comunicazione tra gli
    altri oggetti e l'oggetto stesso. La struttura di base è: canale di
    comunicazione con l'esterno (la coda IPC in entrata ed IPC in uscita) e il
    canale di comunicazione interno, tra l'oggetto e il Gestore Segnali (le code
    Segnali in Entrata e Segnali in Uscita). Se c'è un segnale in arrivo
    nella coda IPC in Entrata, il Gestore Segnali fa i vari controlli e lo mette
    nella coda in entrata per l'oggetto. Se c'è un segnale nella Coda Segnali in
    Uscita, il Gestore Segnali fa i vari controlli e lo mette nella coda IPC in
    uscita.
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
        """Inizializza

        Inizializza le code per la comunicazione
        """

        super().__init__()
        ################## Inizializzazione Gestore Segnali ####################
        # Coda per la comunicazione in entrata con i processi esterni
        self.ipc_entrata          = coda_ipc_entrata
        self.lock_ipc_entrata     = lock_ipc_entrata
        # Coda per la comunicazione in uscita con i processi esterni
        self.ipc_uscita           = coda_ipc_uscita
        self.lock_ipc_uscita      = lock_ipc_uscita
        # Coda per i segnali ricevuti. Comunicazione con il processo padre
        self.coda_segnali_entrata = coda_segnali_entrata
        self.lock_segnali_entrata = lock_segnali_entrata
        # Coda per i segnali da inviare. Comunicatione con il padre
        self.coda_segnali_uscita  = coda_segnali_uscita
        self.lock_segnali_uscita  = lock_segnali_uscita
        # Nome dell'oggetto padre
        self.padre                = str(padre)
        self.segnale_uscita       = {
                                     "segnale":      "",
                                     "mittente":     "",
                                     "destinatario": "",
                                     "timestamp":    0
                                    }
        self.segnale_entrata      = {
                                     "segnale":      "",
                                     "mittente":     "",
                                     "destinatario": "",
                                     "timestamp":    0
                                    }
        # Flag per la richiesta di stop
        self.stop                 = 0
        ############### Fine Inizializzazione Gestore Segnali ##################
    def run(self):
        self.idle()
        if self.stop:
            return int(-1)
    def idle(self):
        """Idle

        Una volta inizializzato, il Gestore Segnale entra nello stato di idle
        in attesa di essere avviato.
        """

        info(type(self).__name__ + " " + self.padre + " " + "idle")
        # Stringa che rappresenta il segnale, nella forma
        # Segnale:timestamp:mittente:destinatario
        pacchetto_segnale    = ""
        # Il segnale spacchettato altro non è che una lista nella forma
        # [segnale,timestamp,mittente,destinatario]. Il segnale spacchettato è
        # ciò che viene scambiato tra il Gestore Segnale e l'oggetto di cui fa
        # parte
        segnale_spacchettato = []
        # Semplicemente quattro variabili per "facilitare" la gestione del
        # segnale
        self.segnale_entrata["segnale"]      = \
        self.segnale_entrata["mittente"]     = \
        self.segnale_entrata["destinatario"] = ""
        self.segnale_entrata["timestamp"]    = 0
        while True:
            # Se l'operatore non ha richiesto lo stop
            if not self.stop:
                # Controlla se ci sono segnali in arrivo
                with self.lock_ipc_entrata:
                    if not self.ipc_entrata.empty():
                        pacchetto_segnale = self.ipc_entrata.get_nowait()
                # Se non è arrivato nessun segnale, salta al prossimo ciclo
                if pacchetto_segnale == "":
                    sleep(0.001)
                    continue
                # Se c'è un qualche segnale in arrivo
                else:
                    # Spacchetta segnale
                    segnale_spacchettato[:] = pacchetto_segnale.split(":")
                    # Se il segnale è formato da 4 parti, vuol dire che è stato
                    # dìspecificato un destinatario.
                    if len(segnale_spacchettato) == 4:
                        self.segnale_entrata["segnale"],
                        self.segnale_entrata["timestamp"],
                        self.segnale_entrata["mittente"],
                        self.segnale_entrata["destinatario"] = \
                        segnale_spacchettato
                    # Se il segnale è formato da 3 parti, vuol dir che non è
                    # stato specificato nessun destinatario (segnale in
                    # broadcast)
                    elif len(segnale_spacchettato) == 3:
                        self.segnale_entrata["segnale"],
                        self.segnale_entrata["timestamp"],
                        self.segnale_entrata["mittente"] = \
                        segnale_spacchettato
                    # Altrimenti il segnale è mal formato. Scartalo e passa al
                    # ciclo successivo
                    else:
                        continue
                    # Se la "parte segnale" del segnale sia stata definita
                    if self.segnale_entrata["segnale"] != "":
                        # Se il segnale è indirizzato al Gestore Segnale
                        if self.segnale_entrata["destinatario"] \
                                          == type(self).__name__ \
                           or self.segnale_entrata["destinatario"] == "":
                            # Esegui il segnale se è tra i segnali che il
                            # Gestore Segnali può interpretare
                            if self.segnale_entrata["segnale"] in dir(self):
                                # Esegui l'operazione
                                getattr(self,self.segnale_entrata["segnale"])()
                                # Ripulisci il Segnale Spacchettato e le
                                # variabili d'appoggio
                                segnale_spacchettato[:]              = []
                                self.segnale_entrata["segnale"]      = \
                                self.segnale_entrata["mittente"]     = \
                                self.segnale_entrata["destinatario"] = ""
                                self.segnale_entrata["timestamp"]    = 0
                            # Se il segnale è la richiesta di stop
                            elif self.segnale_entrata["segnale"] == "stop":
                                # Imposta il flag di stop ed esci dal ciclo
                                self.stop = int(1)
                                break
                    # Ripulisci il Segnale Spacchettato e le variabili
                    # d'appoggio
                    pacchetto_segnale                    = ""
                    segnale_spacchettato[:]              = []
                    self.segnale_entrata["segnale"]      = ""
                    self.segnale_entrata["timestamp"]    = 0
                    self.segnale_entrata["mittente"]     = ""
                    self.segnale_entrata["destinatario"] = ""

            # Se l'operatore ha richiesto lo stop, esci dal ciclo
            else:
                break
        # Una volta terminato il Gestore Segnali, segnalalo all'ambiante ed esci
        with self.lock_ipc_uscita:
            self.ipc_uscita.put_nowait("terminato:" + str(time()) + ":" + \
                                                      type(self).__name__ + ":")
    def avvia(self):
        """Avvia

        Ciclo principale del Gestore Segnali, una volta avviato.
        Controlla continuamente la Coda IPC per i segnali in entrata e la Coda
        Segnali Uscita per i segnali pronti ad essere inviati
        """
        info(type(self).__name__ + " " + self.padre + " " + "avviato")
        #i = r = 0
        i = 0
        while True:
            # Controlla segnali in arrivo
            with self.lock_ipc_entrata:
                if not self.ipc_entrata.empty():
                    #r = self.ricevi_segnale()
                    self.ricevi_segnale()
            # Controlla segnali in entrata
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.empty():
                    i = self.invia_segnale()
            # -1 significa "Richiesta di stop", quindi imposta il flag di stop
            # ed esci dal ciclo
            if i == int(-1):
                self.stop = 1
                break
            sleep(0.001)
        if self.stop:
            return int(-1)
    def invia_segnale(self):
        info(self.padre + " Invia segnale")
        pacchetto_segnale = segnale = destinatario = ""
        segnale_spacchettato = []
        # Preleva il segnale da inviare dalla Coda Segnali in Uscita
        segnale_spacchettato[:] = self.coda_segnali_uscita.get_nowait()
        # Controlla che il segnale sia ben formato
        if segnale_spacchettato:
            if len(segnale_spacchettato) == 2:
                self.segnale_uscita["segnale"],
                self.segnale_uscita["destinatario"] = segnale_spacchettato
                if segnale == "" and destinatario == "":
                    segnale_spacchettato[:] = []
                    return 1
                elif self.segnale_uscita["destinatario"] == \
                     str(type(self).__name__):
                    if self.segnale_uscita["segnale"] == "stop":
                        return int(-1)
                    else:
                        pacchetto_segnale       = ""
                        segnale_spacchettato[:] = []
                        return 1
                elif self.segnale_uscita["destinatario"] == self.padre:
                    pacchetto_segnale       = ""
                    segnale_spacchettato[:] = []
                    return 1
                else:
                    pacchetto_segnale = str(self.segnale_uscita["segnale"]) \
                     + ":" + str(time()) + ":" + self.padre + ":" + \
                     str(destinatario)
                    with self.lock_ipc_uscita:
                        if not self.ipc_uscita.full():
                            self.ipc_uscita.put_nowait(pacchetto_segnale)
                    return 0
            else:
                segnale_spacchettato[:] = []
                return 0
    def ricevi_segnale(self):
        info(self.padre + " Ricevi segnale")
        pacchetto_segnale = \
            self.segnale_entrata["segnale"] = \
            self.segnale_entrata["timestamp"] = \
            self.segnale_entrata["mittente"] = \
            self.segnale_entrata["destinatario"]
        segnale_spacchettato = []
        with self.lock_ipc_entrata:
            pacchetto_segnale = self.ipc_entrata.get_nowait()
        segnale_spacchettato[:] = pacchetto_segnale.split(":")
        if segnale_spacchettato:
            if len(segnale_spacchettato) == 4:
                self.segnale_entrata["segnale"],   \
                 self.segnale_entrata["timestamp"], \
                 self.segnale_entrata["mittente"],  \
                 self.segnale_entrata["destinatario"] = segnale_spacchettato
            elif len(segnale_spacchettato) == 3:
                self.segnale_entrata["segnale"],   \
                 self.segnale_entrata["timestamp"], \
                 self.segnale_entrata["mittente"] = segnale_spacchettato
            else:
                return 1
            if self.segnale_entrata["destinatario"] == self.padre or \
               self.segnale_entrata["destinatario"] == "":
                with self.lock_segnali_entrata:
                    if not self.coda_segnali_entrata.full():
                        self.coda_segnali_entrata.put_nowait(
                            [self.segnale_entrata["segnale"],
                             self.segnale_entrata["mittente"],
                             self.segnale_entrata["destinatario"],
                             self.segnale_entrata["timestamp"]])
                return 1
            else:
                return 0
