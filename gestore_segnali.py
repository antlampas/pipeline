"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

from multiprocessing import Process
from time            import sleep,time

import logging

ATTESA_CICLO_PRINCIPALE = 0.001

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
                 lock_segnali_uscita,
                 controlla_destinatario=True,
                 inoltra=False):
        """Inizializza

        Inizializza le code per la comunicazione
        """

        super().__init__()
        ################## Inizializzazione Gestore Segnali ####################
        # Coda per la comunicazione in entrata con i processi esterni
        self.coda_ipc_entrata     = coda_ipc_entrata
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
                                     "destinatario": ""
                                    }
        self.segnale_entrata      = {
                                     "segnale":      "",
                                     "mittente":     "",
                                     "destinatario": "",
                                     "timestamp":    0
                                    }

        self.controlla_destinatario = controlla_destinatario
        self.inoltra = inoltra
        ############### Fine Inizializzazione Gestore Segnali ##################
    def run(self):
        s = self.idle()
        return int(s)
    def idle(self):
        """Idle

        Una volta inizializzato, il Gestore Segnale entra nello stato di idle
        in attesa di essere avviato.
        """

        logging.info(type(self).__name__ + " " + self.padre + " " + "idle")
        segnale_spacchettato = []
        # Semplicemente due variabili per "facilitare" la gestione del segnale
        self.segnale_uscita["segnale"]      = \
        self.segnale_uscita["destinatario"] = ""

        with self.lock_ipc_uscita:
            self.ipc_uscita.put_nowait("idle:" + \
                                            str(time())  + ":" + \
                                            str(type(self).__name__) + ":")
        while True:
            # Ripulisci il Segnale Spacchettato e le variabili
            # d'appoggio
            segnale_spacchettato[:]             = ""
            self.segnale_uscita["segnale"]      = \
            self.segnale_uscita["destinatario"] = ""
            # Controlla se ci sono segnali in arrivo
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.empty():
                    segnale_spacchettato[:] = self.coda_segnali_uscita.get_nowait()
                    logging.info(segnale_spacchettato)
                    logging.info("Lunghezza: " + str(len(segnale_spacchettato)))
            if len(segnale_spacchettato) == 0:
                # Se non è arrivato nessun segnale, salta al prossimo ciclo
                sleep(ATTESA_CICLO_PRINCIPALE)
                continue
            if len(segnale_spacchettato) == 2:
                # Se il segnale è formato da due parti, allora a posto
                self.segnale_uscita["segnale"] = segnale_spacchettato[0]
                self.segnale_uscita["destinatario"] = segnale_spacchettato[1]
            else:
                # Altrimenti il segnale è mal formato. Scartalo e passa al
                # ciclo successivo
                continue
            # Se la "parte segnale" del segnale sia stata definita
            if self.segnale_uscita["segnale"] != "":
                # Se il segnale è indirizzato al Gestore Segnale
                if self.segnale_uscita["destinatario"] == \
                                                    type(self).__name__:
                    # Esegui il segnale se è tra i segnali che il
                    # Gestore Segnali può interpretare
                    if self.segnale_uscita["segnale"] in dir(self):
                        # Esegui l'operazione
                        s = getattr(self,self.segnale_uscita["segnale"])()
                        with self.lock_ipc_uscita:
                            self.ipc_uscita.put_nowait("terminato:" + \
                                                     str(time()) + \
                                                     ":" + \
                                                     type(self).__name__ + \
                                                     ":")
                        return int(s)
                    # Se il segnale è la richiesta di stop
                elif self.segnale_uscita["segnale"] == "stop":
                        with self.lock_ipc_uscita:
                            self.ipc_uscita.put_nowait("terminato:" + \
                                                       str(time()) + ":" + \
                                                       type(self).__name__ \
                                                       + ":")
                        return int(-1)
    def avvia(self):
        """Avvia

        Ciclo principale del Gestore Segnali, una volta avviato.
        Controlla continuamente la Coda IPC per i segnali in entrata e la Coda
        Segnali Uscita per i segnali pronti ad essere inviati
        """
        logging.info(type(self).__name__ + " " + self.padre + " " + "avviato")
        i = r = 0
        while True:
            # Controlla segnali in arrivo
            with self.lock_ipc_entrata:
                if not self.coda_ipc_entrata.empty():
                     r = self.ricevi_segnale()
            sleep(ATTESA_CICLO_PRINCIPALE)
            # Controlla segnali in entrata
            with self.lock_segnali_uscita:
                if not self.coda_segnali_uscita.empty():
                    i = self.invia_segnale()
            if (i == int(-1)) or (r == int(-1)):
                return int(-1)
            sleep(ATTESA_CICLO_PRINCIPALE)
    def invia_segnale(self):
        logging.info(self.padre + " Invia segnale")
        self.segnale_uscita["segnale"]      = \
        self.segnale_uscita["destinatario"] = \
        self.segnale_uscita["mittente"]     = ""
        pacchetto_segnale                   = ""
        segnale_spacchettato                = []
        # Preleva il segnale da inviare dalla Coda Segnali in Uscita
        segnale_spacchettato[:]          = self.coda_segnali_uscita.get_nowait()
        logging.info(segnale_spacchettato)
        # Controlla che il segnale sia ben formato
        if self.inoltra:
            if len(segnale_spacchettato) == 3:
                self.segnale_uscita["segnale"] = segnale_spacchettato[0]
                self.segnale_uscita["destinatario"] = segnale_spacchettato[1]
                self.segnale_uscita["mittente"] = segnale_spacchettato[2]
                if self.segnale_uscita["segnale"] == "" or \
                   self.segnale_uscita["destinatario"] == self.padre:
                    pacchetto_segnale       = ""
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
                else:
                    pacchetto_segnale = \
                     str(self.segnale_uscita["segnale"]) + ":" + \
                     str(time()) + ":" + \
                     str(self.segnale_uscita["mittente"]) + ":" + \
                     str(self.segnale_uscita["destinatario"])
                    logging.info(pacchetto_segnale)
                    self.ipc_uscita.put_nowait(pacchetto_segnale)
                    return 0
            else:
                self.segnale_uscita["segnale"] = \
                self.segnale_uscita["destinatario"] = \
                self.segnale_uscita["mittente"] = ""
                pacchetto_segnale = ""
                segnale_spacchettato[:] = []
                return 0
        else:
            if len(segnale_spacchettato) == 2:
                self.segnale_uscita["segnale"] = segnale_spacchettato[0]
                self.segnale_uscita["destinatario"] = segnale_spacchettato[1]
                if self.segnale_uscita["segnale"] == "" and \
                   self.segnale_uscita["destinatario"] == "":
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
                    pacchetto_segnale = \
                     str(self.segnale_uscita["segnale"]) + ":" + \
                     str(time()) + ":" + \
                     str(self.padre) + ":" + \
                     str(self.segnale_uscita["destinatario"])
                    logging.info(pacchetto_segnale)
                    self.ipc_uscita.put_nowait(pacchetto_segnale)
                    return 0
            else:
                self.segnale_uscita["segnale"] = \
                self.segnale_uscita["destinatario"] = \
                self.segnale_uscita["mittente"] = ""
                pacchetto_segnale = ""
                segnale_spacchettato[:] = []
                return 0
    def ricevi_segnale(self):
        logging.info(self.padre + " Ricevi segnale")

        pacchetto_segnale                    = ""
        segnale_spacchettato                 = []
        self.mittente                        = ""
        self.segnale_entrata["segnale"]      = ""
        self.segnale_entrata["mittente"]     = ""
        self.segnale_entrata["destinatario"] = ""
        self.segnale_entrata["timestamp"]    = 0

        # Inizia ricezione segnale
        pacchetto_segnale = self.coda_ipc_entrata.get_nowait()
        logging.info(self.padre)
        logging.info(pacchetto_segnale)
        segnale_spacchettato[:] = pacchetto_segnale.split(":")
        logging.info(self.padre)
        logging.info(segnale_spacchettato)
        if len(segnale_spacchettato) == 4:
            self.segnale_entrata["segnale"] = segnale_spacchettato[0]
            self.segnale_entrata["timestamp"] = segnale_spacchettato[1]
            self.segnale_entrata["mittente"] = segnale_spacchettato[2]
            self.segnale_entrata["destinatario"] = segnale_spacchettato[3]
            logging.info("Gestore Segnali " + self.padre)
            logging.info(self.segnale_entrata["segnale"])
            logging.info(self.segnale_entrata["mittente"])
            logging.info(self.segnale_entrata["destinatario"])
            logging.info(self.segnale_entrata["timestamp"])
        elif len(segnale_spacchettato) == 3:
            self.segnale_entrata["segnale"] = segnale_spacchettato[0]
            self.segnale_entrata["timestamp"] = segnale_spacchettato[1]
            self.segnale_entrata["mittente"] = segnale_spacchettato[2]
            logging.info("Gestore Segnali " + self.padre)
            logging.info(self.segnale_entrata["segnale"])
            logging.info(self.segnale_entrata["mittente"])
            logging.info(self.segnale_entrata["timestamp"])
        else:
            return 1

        if self.controlla_destinatario:
            if self.segnale_entrata["destinatario"] == self.padre or \
               self.segnale_entrata["destinatario"] == "":
                logging.info("Gestore Segnali " + self.padre)
                logging.info([self.segnale_entrata["segnale"],
                              self.segnale_entrata["mittente"],
                              self.segnale_entrata["destinatario"],
                              self.segnale_entrata["timestamp"]])
                if not self.coda_segnali_entrata.full():
                    self.coda_segnali_entrata.put_nowait(
                        [self.segnale_entrata["segnale"],
                         self.segnale_entrata["mittente"],
                         self.segnale_entrata["destinatario"],
                         self.segnale_entrata["timestamp"]])
                return 1
            else:
                return 0
        else:
            logging.info("Gestore Segnali " + self.padre)
            logging.info([self.segnale_entrata["segnale"],
                          self.segnale_entrata["mittente"],
                          self.segnale_entrata["destinatario"],
                          self.segnale_entrata["timestamp"]])
            if not self.coda_segnali_entrata.full():
                self.coda_segnali_entrata.put_nowait( \
                                           [self.segnale_entrata["segnale"],
                                           self.segnale_entrata["mittente"],
                                           self.segnale_entrata["destinatario"],
                                           self.segnale_entrata["timestamp"]])
                return 1
