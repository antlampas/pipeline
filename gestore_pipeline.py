"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

import logging
from multiprocessing import Queue,Lock
from time            import time,sleep

#Framework
from oggetto         import oggetto
from gestore_segnali import gestore_segnali


class gestore_pipeline(oggetto):
    """Gestore Pipeline

    Gestisce la coda delle operazioni che il programma deve eseguire.
    Fa da arbitro nelle comunicazioni tra le operazioni e tra le operazioni e
    il Gestore Pipeline (sé stesso) ed orchestra le operazioni.
    Si assicura che le operazioni vengano eseguite nell'ordine stabilito
    """
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
        ##### Inizializzazione comune a tutti gli oggetti del framework ########
        ##################### Lettura delle impostazioni #######################
        configurazione       = []
        lista_configurazione = []
        impostazioni         = []

        # Leggi le impostazioni dal file configurazione e mettile in una lista
        with open(file_configurazione) as f:
            configurazione = f.readlines()
        lista_configurazione[:] = [x.strip() for x in configurazione]
        # La lista delle impostazioni è una lista di liste, così da permettere
        # indici non unici
        for impostazione in lista_configurazione:
            nome,valore = impostazione.split(" ")
            impostazioni.append([nome,valore])
        ################# Fine lettura delle impostazioni ######################
        #### Fine inizializzazione comune a tutti gli oggetti del framework ####

        ################### Inizializza le impostazioni ########################

        # TODO: controlla le impostazioni già scritte e inizializza le
        #       impostazioni mancanti
        self.lista_segnali                   = []
        # Dizionario con le operazioni da eseguire nell'ordine di esecuzione
        self.operazioni                      = {} # "nome": operazione
        # Dizionario con le code per le comunicazioni tra il Gestore Pipeline e
        # le operazioni. Le code sono unidirezionali: qui ci sono i messaggi che
        # devono essere mandati alle operazioni.
        # Usato *solo* dai Gestori Segnali per le comunicazioni oggetto-oggetto
        # (Gestore Segnali - Gestore Segnali)
        self.ipc_entrata_operazioni          = {} # "nome operazione": coda
        # Dizionario con i lock per le code IPC in entrata
        self.lock_ipc_entrata_operazioni     = {} # "nome operazione": coda
        # Dizionario con le code per le comunicazioni tra il Gestore Pipeline e
        # le operazioni. Le code sono unidirezionali: qui ci sono i messaggi
        # ricevuti dalle operazioni.
        # Usato *solo* dai Gestori Segnali per le comunicazioni oggetto-oggetto
        # (Gestore Segnali - Gestore Segnali)
        self.ipc_uscita_operazioni           = {}
        # Dizionario con i lock per le code IPC in uscita
        self.lock_ipc_uscita_operazioni      = {}
        # Dizionario con le code per i segnali ricevuti dalle operazioni. Il
        # Gestore Pipeline legge i segnali delle operazioni da qui
        self.coda_segnali_entrata_operazioni = {}
        # dizionario con i lock per le code in uscita
        self.lock_segnali_uscita_operazioni  = {}
        # Dizionario con le code per i segnali da inviare alle operazioni. Il
        # Gestore Pipeline scrive i segnali per le operazioni da qui
        self.coda_segnali_uscita_operazioni  = {}
        # Dizionario con i lock per le code in entrata
        self.lock_segnali_entrata_operazioni = {}
        # Dizionario con i gestori segnali associati alle singole operazioni.
        # Per ogni operazione della pipeline, il Gestore Pipeline si crea un
        # Gestore Segnali per la comunicazione con quella operazione
        self.gestore_segnali_operazioni      = {}
        # Segnale in entrata dall'esterno dell'applicazione (dalla coda IPC)

        # Preleva le impostazioni del Gestore Pipeline. Le impostazioni sono:
        # -) Operazione: il nome dell'operazione da aggiungere alla pipeline
        # -) Segnale: un segnale che il Gestore Pipeline può inviare
        for impostazione in impostazioni:
            nome,valore = impostazione
            # Aggiungi il segnale alla lista dei segnali
            if nome == "segnale":
                self.lista_segnali.append(valore)
            # Aggiungi l'operazione alla pipeline
            if nome == "operazione":
                # Inizializza le code e i lock *associati* all'operazione nel
                # Gestore Pipeline
                self.ipc_entrata_operazioni[valore]          = Queue()
                self.lock_ipc_entrata_operazioni[valore]     = Lock()
                self.ipc_uscita_operazioni[valore]           = Queue()
                self.lock_ipc_uscita_operazioni[valore]      = Lock()
                self.coda_segnali_entrata_operazioni[valore] = Queue()
                self.lock_segnali_entrata_operazioni[valore] = Lock()
                self.coda_segnali_uscita_operazioni[valore]  = Queue()
                self.lock_segnali_uscita_operazioni[valore]  = Lock()
                # Inizializza il Gestore Segnali *associato* all'operazione
                self.gestore_segnali_operazioni[valore]      = gestore_segnali(
                                   type(self).__name__,
                                   self.ipc_entrata_operazioni[valore],
                                   self.lock_ipc_entrata_operazioni[valore],
                                   self.ipc_uscita_operazioni[valore],
                                   self.lock_ipc_uscita_operazioni[valore],
                                   self.coda_segnali_entrata_operazioni[valore],
                                   self.lock_segnali_entrata_operazioni[valore],
                                   self.coda_segnali_uscita_operazioni[valore],
                                   self.lock_segnali_uscita_operazioni[valore],
                                   controlla_destinatario=False,
                                   inoltra=True)
                # Avvia il Gestore Segnali *associato* all'operazione
                self.gestore_segnali_operazioni[valore].start()
                sleep(0.01)
                with self.lock_segnali_uscita_operazioni[valore]:
                    if not self.coda_segnali_uscita_operazioni[valore].full():
                        self.coda_segnali_uscita_operazioni[valore].put_nowait(["avvia","gestore_segnali"])
                # Inizializza l'operazione nella coda delle operazioni
                self.operazioni[valore] = globals()[valore](
                                       str(valore + ".conf"),
                                       self.ipc_uscita_operazioni[valore],
                                       self.lock_ipc_uscita_operazioni[valore],
                                       self.ipc_entrata_operazioni[valore],
                                       self.lock_ipc_entrata_operazioni[valore])
                sleep(0.1)
        # Avvia tutte le operazioni
        for nome,operazione in self.operazioni.items():
            operazione.start()
        ################ Fine inizializza le impostazioni ######################
    def idle(self):
        logging.info(type(self).__name__ + " idle")

        pacchetto_segnale_entrata = []
        segnale                   = ""
        mittente                  = ""
        destinatario              = ""
        timestamp                 = 0

        # Segnala all'esterno che sei in idle
        with self.lock_segnali_uscita:
            if not self.coda_segnali_uscita.full():
                self.coda_segnali_uscita.put_nowait(["idle",""])
        # Attendi il segnale di avvio
        while True:
            pacchetto_segnale_entrata[:] = []
            segnale                      = ""
            mittente                     = ""
            destinatario                 = ""
            timestamp                    = 0

            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
            if len(pacchetto_segnale_entrata) == 4:
                segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
            elif len(pacchetto_segnale_entrata) == 3:
                segnale,mittente,timestamp = pacchetto_segnale_entrata
            elif len(pacchetto_segnale_entrata) == 0:
                pass
            else:
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["segnale mal formato",
                                                         ""])
                sleep(0.1)
                logging.info("Gestore Pipeline: Segnale mal formato")
                pacchetto_segnale_entrata[:] = []
                continue
            logging.info(type(self).__name__)
            logging.info(pacchetto_segnale_entrata)
            logging.info(segnale)
            pacchetto_segnale_entrata[:] = []
            if segnale == "":
                sleep(0.01)
                continue
            # Se hai ricevuto il segnale di stop
            elif segnale == "stop":
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["terminato",""])
                    # Invia il segnale di stop anche al tuo Gestore Segnali
                    self.coda_segnali_uscita.put_nowait(["stop",
                                                         "gestore_segnali"])
                    # Termina segnalando l'uscita per segnale di stop
                return int(-1)
            else:
                # Se il segnale è tra i metodi riconosciuti dal Gestore Pipeline
                if segnale in dir(self):
                    #Esegui il segnale
                    s = getattr(self,segnale)()
                    return int(s)
                else:
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait( \
                                                          ["Segnale non valido",
                                                           ""])
                    sleep(0.01)
            ############## Fine ricezione messaggi dall'esterno ################
    def avvia(self):
        logging.info(type(self).__name__ + " avviato")

        pacchetto_segnale_entrata = []
        segnale                   = ""
        mittente                  = ""
        destinatario              = ""
        timestamp                 = 0
        richiesta_stop            = False

        # Segnala all'esterno che sei avviato
        with self.lock_segnali_uscita:
            if not self.coda_segnali_uscita.full():
                self.coda_segnali_uscita.put_nowait(["avviato",""])

        for nome,operazione in self.operazioni.items():
            # Manda il segnale di avvio all'operazione.
            with self.lock_ipc_uscita_operazioni[nome]:
                self.ipc_uscita_operazioni[nome].put_nowait("avvia:"  + \
                                                           str(time()) + ":" + \
                                                           type(self).__name__ \
                                                           + ":" + nome)
        while True:
            pacchetto_segnale_entrata[:] = []
            segnale                      = ""
            mittente                     = ""
            destinatario                 = ""
            timestamp                    = 0

            if richiesta_stop:
                for operazione in self.operazioni:
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["terminando: " + \
                                                             str(operazione),
                                                             ""])
                    with self.lock_segnali_uscita_operazioni[operazione]:
                        self.coda_segnali_uscita_operazioni[operazione].put_nowait(["stop",
                                                                                    operazione])
                    with self.lock_segnali_uscita_operazioni[operazione]:
                        self.coda_segnali_uscita_operazioni[operazione].put_nowait(["stop","gestore_segnali"])
                    #self.operazioni[operazione].join()
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait([str(operazione) + \
                                                             " terminata",""])
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["stop",
                                                         "gestore_segnali"])
                return int(-1)

            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
            logging.debug("IPC")
            logging.debug(pacchetto_segnale_entrata)
            if len(pacchetto_segnale_entrata) == 4:
                segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
                pacchetto_segnale_entrata[:] = []
            elif len(pacchetto_segnale_entrata) == 3:
                segnale,mittente,timestamp = pacchetto_segnale_entrata
                pacchetto_segnale_entrata[:] = []
            elif len(pacchetto_segnale_entrata) == 0:
                pass
            else:
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["segnale mal formato",
                                                         ""])
                logging.info("Gestore Pipeline: Segnale mal formato")
                pacchetto_segnale_entrata[:] = []
                sleep(0.1)
                continue

            # Se hai ricevuto il segnale di stop
            if segnale == "stop":
                # Invia il segnale di stop anche al tuo Gestore Segnali
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait( \
                                                        ["terminando: " + \
                                                            type(self).__name__,
                                                         ""])
                richiesta_stop = True

            ############## Fine ricezione messaggi dall'esterno ################
            ########## Comunicazione con le operazioni della pipeline ##########
            # Per ogni operazione
            for (ogg,lock_entrata),                               \
                (ogg,coda_segnali_entrata),                       \
                (ogg,lock_uscita),                                \
                (ogg,coda_segnali_uscita)                         \
                in                                                \
                zip(self.lock_segnali_entrata_operazioni.items(), \
                self.coda_segnali_entrata_operazioni.items(),     \
                self.lock_segnali_uscita_operazioni.items(),      \
                self.coda_segnali_uscita_operazioni.items()):
                #TODO: CONTROLLA DA QUI
                pacchetto_segnale_entrata[:] = []
                segnale                   = ""
                mittente                  = ""
                destinatario              = ""
                timestamp                 = 0
                logging.debug(id(coda_segnali_entrata))
                # Leggi l'eventuale segnale dall'operazione
                with lock_entrata:
                    if not coda_segnali_entrata.empty():
                        pacchetto_segnale_entrata[:] = \
                         coda_segnali_entrata.get_nowait()
                logging.debug(ogg)
                logging.debug(pacchetto_segnale_entrata)
                if len(pacchetto_segnale_entrata) == 4:
                    segnale,mittente,destinatario,timestamp = \
                                                   pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 3:
                    segnale,mittente,timestamp = pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 0:
                    sleep(0.01)
                    continue
                else:
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait( \
                                                 ["segnale mal formato",""])
                    with lock_uscita:
                        coda_segnali_uscita.put_nowait(["segnale mal formato",
                                                        ""])
                    logging.info("Gestore Pipeline: Segnale mal formato")
                    pacchetto_segnale_entrata[:] = []
                    sleep(0.01)
                    continue
                logging.debug("Gestore Pipeline " + \
                              segnale       + " " + \
                              mittente      + " " + \
                              destinatario  + " " + \
                              str(timestamp))
                sleep(0.001)
                # Se il destinatario è il Gestore Pipeline
                if str(destinatario) == type(self).__name__:
                    if segnale == "stop":
                        richiesta_stop = True
                        break
                    elif segnale == "lista_segnali":
                        ops = ""
                        prima_operazione = 1
                        for op in self.operazioni:
                            if prima_operazione == 1:
                                ops = str(op)
                                prima_operazione = 0
                            else:
                                ops = ops + "," + str(op)
                        with self.lock_segnali_uscita_operazioni[ogg]:
                            self.coda_segnali_uscita_operazioni[ogg].put_nowait([ops,destinatario,mittente])
                # Se il destinatario è una delle altre operazioni
                elif str(destinatario) in self.operazioni:
                    # Inoltra il segnale a quella specifica operazione
                    with self.lock_segnali_uscita_operazioni[str(destinatario)]:
                        self.coda_segnali_uscita_operazioni[str(destinatario)].put_nowait([segnale,destinatario,mittente])
                # Se il destinatario è "broadcast"
                elif str(destinatario) == "":
                    # Inoltra il segnale a tutte le altre operazioni
                    for operazione in self.operazioni:
                        if operazione == ogg:
                            continue
                        else:
                            with self.lock_segnali_uscita_operazioni[str(operazione)]:
                                self.coda_segnali_uscita_operazioni[str(operazione)].put_nowait([segnale,destinatario,mittente])
                        sleep(0.01)
                    if segnale == "stop":
                        richiesta_stop = True
            ############## Fine comunicazione con le operazioni ################
            sleep(0.01)
