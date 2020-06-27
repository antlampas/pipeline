from multiprocessing import Process,Queue,Lock
from time            import time,sleep
from random          import uniform
from logging         import info
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
        lista_segnali        = []

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

        # Preleva le impostazioni del Gestore Pipeline. Le impostazioni sono:
        # -) Operazione: il nome dell'operazione da aggiungere alla pipeline
        # -) Segnale: un segnale che il Gestore Pipeline può inviare
        for impostazione in impostazioni:
            nome,valore = impostazione
            # Aggiungi il segnale alla lista dei segnali
            if nome == "segnale":
                lista_segnali.append(valore)
        for impostazione in impostazioni:
            nome,valore = impostazione
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
                                   self.lock_segnali_uscita_operazioni[valore])
                # Avvia il Gestore Segnali *associato* all'operazione
                self.gestore_segnali_operazioni[valore].start()
                # Inizializza l'operazione nella coda delle operazioni
                self.operazioni[valore] = globals()[valore](
                                       str(valore + ".conf"),
                                       self.ipc_uscita_operazioni[valore],
                                       self.lock_ipc_uscita_operazioni[valore],
                                       self.ipc_entrata_operazioni[valore],
                                       self.lock_ipc_entrata_operazioni[valore])
                # Manda il segnale di avvio all'operazione.
                # Lo manda due volte, perché il primo avvia il Gestore Segnali
                # dell'operazione, il secondo avvia l'operazione vera e propria
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
        # Avvia tutte le operazioni
        for nome,operazione in self.operazioni.items():
            operazione.start()
        self.stop = 0
        ################ Fine inizializza le impostazioni ######################
    def idle(self):
        info(type(self).__name__ + " idle")
        # Attendi il segnale di avvio
        while True:
            segnale = ""
            # Segnala all'esterno che sei in idle
            with self.lock_segnali_uscita:
                self.coda_segnali_uscita.put_nowait(["idle",""])
            ################# Ricevi messaggi dall'esterno #####################
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            # Se non hai ricevuto nessun segnale
            if segnale == "":
                # Non fare niente e comincia direttamente il prossimo ciclo
                sleep(uniform(0.001,0.200))
                continue
            # Se hai ricevuto il segnale di stop
            elif segnale == "stop":
                # Invia il segnale di stop anche al tuo Gestore Segnali
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["stop", \
                                                         "gestore_segnali"])
                # Termina segnalando l'uscita per segnale di stop
                return int(-1)
            else:
                # Se il segnale è tra i metodi riconosciuti dal Gestore Pipeline
                if segnale in dir(self):
                    #Esegui il segnale
                    getattr(self,segnale)()
            ############## Fine ricezione messaggi dall'esterno ################
    def avvia(self):
        info(type(self).__name__ + " avviato")
        while True:
            segnale = ""
            ################# Ricevi messaggi dall'esterno #####################
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    segnale = self.coda_segnali_entrata.get_nowait()
            # Se hai ricevuto il segnale di stop
            if segnale == "stop":
                # Invia il segnale di stop anche al tuo Gestore Segnali
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(
                                                     ["stop","gestore_segnali"])
                # Termina segnalando l'uscita per segnale di stop
                return int(-1)
            elif segnale != "":
                pass
            else:
                pass
            ############## Fine ricezione messaggi dall'esterno ################
            ########## Comunicazione con le operazioni della pipeline ##########
            # Per ogni operazione
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
                segnale_spacchettato = []
                # Leggi l'eventuale segnale in uscita dall'operazione
                with lock_entrata:
                    if not coda_segnali_entrata.empty():
                        segnale_spacchettato[:] = \
                                               coda_segnali_entrata.get_nowait()
                # Se il destinatario è il Gestore Pipeline
                if destinazione == type(self).__name__:
                    # Fa qualcosa
                    pass
                # Se il destinatario è una delle altre operazioni
                elif destinazione in self.operazioni:
                    # Inoltra il segnale a quella specifica operazione
                    with self.lock_segnali_uscita_operazioni[destinazione]:
                        self.coda_segnali_uscita_operazioni[destinazione].put_nowait([segnale,destinazione])
                # Se il destinatario è "broadcast"
                elif destinazione == "":
                    # Inoltra il segnale a tutte le altre operazioni
                    for operazione in self.operazioni:
                        if operazione == oggetto:
                            continue
                        else:
                            with self.lock_segnali_uscita_operazioni[operazione]:
                                self.coda_segnali_uscita_operazioni[operazione].put_nowait([segnale,destinazione])

            ############## Fine comunicazione con le operazioni ################
            sleep(0.01)
