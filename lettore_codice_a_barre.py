"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

from oggetto import oggetto
import logging
import evdev

from time            import sleep,time
from gpiozero        import LED,Button

ATTESA_CICLO_PRINCIPALE = 0.01

class lettore_codice_a_barre(oggetto):
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
        logging.info(type(self).__name__ + " inizializzazione")
        configurazione       = []
        lista_configurazione = []
        impostazioni         = []

        self.attiva_terminatore      = False
        self.attiva_limite_caratteri = False

        with open(file_configurazione) as f:
            configurazione = f.readlines()
        lista_configurazione[:] = [x.strip() for x in configurazione]
        # La lista delle impostazioni è una lista di liste, così da permettere
        # indici non unici
        for impostazione in lista_configurazione:
            nome,valore = impostazione.split(" ")
            impostazioni.append([nome,valore])

        with open(file_configurazione) as file_configurazione:
            for linea in file_configurazione:
                linea = linea.strip()
                opzione,valore = linea.split(" ")
                if opzione == "device":
                    self.device = evdev.InputDevice(valore)
                    self.device.grab()
                elif opzione == "pin_lettura":
                    self.leggi = LED(int(valore))
                    self.leggi.off()
                elif opzione == "terminatore":
                    self.attiva_terminatore = True
                    self.terminatore = valore
                elif opzione == "limite_caratteri":
                    self.attiva_limite_caratteri = True
                    self.limite_caratteri = int(valore)
                elif opzione == "richiesta_comando":
                    self.richiesta_comando = Button(int(valore))
        logging.info(type(self).__name__ + " inizializzato")
    def avvia(self):
        logging.info(type(self).__name__ + " avviato")
        with self.lock_segnali_uscita:
            if not self.coda_segnali_uscita.full():
                self.coda_segnali_uscita.put_nowait(["avviato",""])
        ##### Variabili d'appoggio #####
        # Segnale così com'è scritto nella coda segnali
        pacchetto_segnale_entrata = []
        # Segnale come deve essere scritto nella coda segnale
        pacchetto_segnale_uscita = []
        segnale                  = ""
        mittente                 = ""
        destinatario             = ""
        timestamp                = 0

        comando                  = ""
        while True:
            ########################## Loop principale #########################
            ################# Ripristina variabili d'appoggio ##################
            pacchetto_segnale_entrata[:] = []
            comando          = ""
            segnale          = ""
            destinatario     = ""
            mittente         = ""
            timestamp        = 0
            ############### Fine ripristino variabili d'appoggio ###############
            ########################## Ricevi segnale ##########################
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
            if len(pacchetto_segnale_entrata) == 4:
                logging.info(str(type(self).__name__) + " messaggio diretto ricevuto")
                segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
                pacchetto_segnale_entrata[:] = []
            elif len(pacchetto_segnale_entrata) == 3:
                logging.info(str(type(self).__name__) + " messaggio broadcast ricevuto")
                segnale,mittente,timestamp = pacchetto_segnale_entrata
                pacchetto_segnale_entrata[:] = []
            elif len(pacchetto_segnale_entrata) == 0:
                pass
            else:
                with self.lock_segnali_uscita:
                    if not self.coda_segnali_uscita.full():
                        self.coda_segnali_uscita.put_nowait( \
                                                         ["segnale mal formato",
                                                          ""])
                pacchetto_segnale_entrata[:] = []
                sleep(ATTESA_CICLO_PRINCIPALE)
                continue
            pacchetto_segnale_entrata[:] = []
            if segnale != "":
                logging.info(str(type(self).__name__) + " " + str(segnale) + " ricevuto")
            ######################## Fine ricevi segnale #######################
            ############# Se segnale ricevuto, gestisci il segnale #############
            if segnale == "stop": # Segnale ####################################
                with self.lock_segnali_uscita:
                    if not self.coda_segnali_uscita.full():
                        self.coda_segnali_uscita.put_nowait(["stop",
                                                             "gestore_segnali"])
                return int(-1)
            elif segnale == "cassa presente": # Segnale ########################
                with self.lock_segnali_uscita:
                    if not self.coda_segnali_uscita.full():
                        self.coda_segnali_uscita.put_nowait( \
                                                   ["pronto lettura codice",
                                                    "riconoscimento_cassa"])
                while True:
                    ################# Ripristina variabili d'appoggio ##########
                    pacchetto_segnale_entrata[:] = []
                    comando                      = ""
                    codice                       = ""
                    segnale                      = ""
                    destinatario                 = ""
                    mittente                     = ""
                    timestamp                    = 0
                    ############### Fine ripristino variabili d'appoggio #######
                    ########################## Ricevi segnale ##################
                    logging.info(str(type(self).__name__) + " in attesa di richiesta lettura codice")
                    with self.lock_segnali_entrata:
                        if not self.coda_segnali_entrata.empty():
                            pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
                    if len(pacchetto_segnale_entrata) == 4:
                        segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
                        pacchetto_segnale_entrata[:] = []
                    elif len(pacchetto_segnale_entrata) == 3:
                        segnale,mittente,timestamp = pacchetto_segnale_entrata
                        pacchetto_segnale_entrata[:] = []
                    elif len(pacchetto_segnale_entrata) == 0:
                        sleep(ATTESA_CICLO_PRINCIPALE)
                        continue
                    else:
                        with self.lock_segnali_uscita:
                            if not self.coda_segnali_uscita.full():
                                self.coda_segnali_uscita.put_nowait( \
                                                     ["segnale mal formato",""])
                        pacchetto_segnale_entrata[:] = []
                        sleep(ATTESA_CICLO_PRINCIPALE)
                        continue
                    ################## Gestisci il segnale #####################
                    logging.info(str(type(self).__name__) + " " + str(segnale) + " ricevuto")
                    if segnale == "leggi codice":
                        logging.info("Richiesta Lettura Codice")
                        while codice == "":
                            codice = self.leggi_codice_a_barre()
                        logging.info("Codice letto")
                        print(codice)
                        pacchetto_segnale_uscita[:] = [str(codice),
                                                       str(mittente)]
                        with self.lock_segnali_uscita:
                            if not self.coda_segnali_uscita.full():
                                self.coda_segnali_uscita.put_nowait( \
                                                   pacchetto_segnale_uscita)
                    elif segnale == "codice ricevuto":
                        logging.info(str(type(self).__name__) + " " + \
                                     segnale + \
                                     " ricevuto")
                        break
                    sleep(ATTESA_CICLO_PRINCIPALE)
            ####################### Fine Gestione segnale ######################
            ########### Leggi eventuale comando utente dallo scanner ###########
            if self.richiesta_comando.is_pressed:
                logging.info("In attesa del comando dal lettore codice a barre")
                comando_letto = self.leggi_codice_a_barre()
                logging.info(comando_letto)
                if comando_letto != "":
                    comando = comando_letto.lower()
                    if comando.find("aggiorna") == 0:
                        logging.info("Richiesta aggiornamento configurazione")
                        # Estrapola il nome dell'operazione da aggiornare
                        ignora,operazione = comando.split(" ")
                        print(comando)
                        # Richiedi la lista delle operazioni al Gestore Operazioni
                        pacchetto_segnale_uscita = ["lista_operazioni",
                                                    "gestore_pipeline"]
                        with self.lock_segnali_uscita:
                            if not self.coda_segnali_uscita.full():
                                self.coda_segnali_uscita.put_nowait( \
                                                       pacchetto_segnale_uscita)
                        lista_operazioni = []
                        while True:
                            pacchetto_segnale_entrata[:] = []
                            segnale            = ""
                            mittente           = ""
                            destinatario       = ""
                            timestamp          = 0
                            with self.lock_segnali_entrata:
                                if not self.coda_segnali_entrata.empty():
                                    pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
                                    print(pacchetto_segnale_entrata)
                            if len(pacchetto_segnale_entrata) == 4:
                                segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
                                pacchetto_segnale_entrata[:] = []
                            elif len(pacchetto_segnale_entrata) == 3:
                                segnale,mittente,destinatario,timestamp = \
                                                       pacchetto_segnale_entrata
                                pacchetto_segnale_entrata[:] = []
                            elif len(pacchetto_segnale_entrata) == 0:
                                pass
                            else:
                                with self.lock_segnali_uscita:
                                    if not self.coda_segnali_uscita.full():
                                        self.coda_segnali_uscita.put_nowait( \
                                                     ["segnale mal formato",""])
                                    sleep(0.001)
                                    if not self.coda_segnali_uscita.full():
                                        self.coda_segnali_uscita.put_nowait( \
                                                       pacchetto_segnale_uscita)
                                pacchetto_segnale_entrata[:] = []
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                            # Se il mittente è il gestore pipeline e il destinatario
                            # è il Lettore Codice a barre, allora il segnale è la
                            # lista delle operazioni
                            if mittente == "gestore_pipeline" and \
                               destinatario == str(type(self).__name__):
                                lista_operazioni[:] = segnale.split(",")
                                # Se l'operazione richiesta per l'aggiornamento è
                                # tra le operazioni caricate nella pipeline,
                                # aggiorna; altrimenti segnala che l'operazione non
                                # è valida
                                if operazione in lista_operazioni:
                                    logging.info("Aggiornando " + operazione)
                                    segnale_aggiornamento = \
                                                    ["aggiorna",str(operazione)]
                                    with self.lock_segnali_uscita:
                                        if not self.coda_segnali_uscita.full():
                                            self.coda_segnali_uscita.put_nowait( \
                                                          segnale_aggiornamento)
                                    break
                                    while True:
                                        with self.lock_segnali_entrata:
                                            if not self.coda_segnali_entrata.empty():
                                                pacchetto_segnale_entrata[:] = \
                                          self.coda_segnali_entrata.get_nowait()
                                        if len(pacchetto_segnale_entrata) == 4:
                                            segnale,
                                            mittente,
                                            destinatario,
                                            timestamp = pacchetto_segnale_entrata
                                            pacchetto_segnale_entrata[:] = []
                                        elif len(pacchetto_segnale_entrata) == 3:
                                            segnale,
                                            mittente,
                                            destinatario = pacchetto_segnale_entrata
                                            pacchetto_segnale_entrata[:] = []
                                        elif len(pacchetto_segnale_entrata) == 0:
                                            pass
                                        else:
                                            with self.lock_segnali_uscita:
                                                if not self.coda_segnali_uscita.full():
                                                    self.coda_segnali_uscita.put_nowait(["segnale mal formato",""])
                                            pacchetto_segnale_entrata[:] = []
                                            sleep(0.01)
                                            continue
                                        impostazione = self.leggi_codice_a_barre(0.1)
                                        if impostazione == "fine aggiornamento":
                                            with self.lock_segnali_uscita:
                                                if not self.coda_segnali_uscita.full():
                                                    self.coda_segnali_uscita.put_nowait([str(impostazione),str(mittente)])
                                            sleep(0.01)
                                            continue
                                        if segnale == "pronto":
                                            with self.lock_segnali_uscita:
                                                if not self.coda_segnali_uscita.full():
                                                    self.coda_segnali_uscita.put_nowait([str(impostazione),str(mittente)])
                                        elif segnale == "fine aggiornamento":
                                            with self.lock_segnali_uscita:
                                                if not self.coda_segnali_uscita.full():
                                                    self.coda_segnali_uscita.put_nowait(["ok",str(mittente)])
                                            break
                                        sleep(0.01)
                                else:
                                    with self.lock_segnali_uscita:
                                        if not self.coda_segnali_uscita.full():
                                            self.coda_segnali_uscita.put_nowait( \
                                           ["L'operazione richiesta non è presente",
                                            str(mittente)])
                                        sleep(0.01)
                                        if not self.coda_segnali_uscita.full():
                                            self.coda_segnali_uscita.put_nowait( \
                                                              ["fine aggiornamento",
                                                               str(mittente)])
                                    break
                    elif comando == "stop":
                        with self.lock_segnali_uscita:
                            if not self.coda_segnali_uscita.full():
                                self.coda_segnali_uscita.put_nowait(["stop",""])
                        sleep(0.01)
                        with self.lock_segnali_uscita:
                            if not self.coda_segnali_uscita.full():
                                self.coda_segnali_uscita.put_nowait(["stop",
                                                                 "gestore_segnali"])
                        return int(-1)
                    else:
                        logging.warn(comando + ": Comando non valido")
                    comando = ""
            sleep(ATTESA_CICLO_PRINCIPALE)
            ###################### Fine Loop Principale ########################
    def leggi_codice_a_barre(self,to=0):
        tempo_precedente = 0
        intervallo       = 0
        codice           = ""
        self.leggi.on()
        if to > 0:
            tempo_precedente = time()
        skip = 0
        ultimo_carattere = ''
        codice = ""
        codici_validi = {
                          0:   None,    1:  u'ESC',   2:  u'1',     3:  u'2',
                          4:   u'3',     5: u'4',     6:  u'5',     7:  u'6',
                          8:   u'7',     9: u'8',     10: u'9',     11: u'0',
                          12:  u'-',    13: u'=',     14: u'BKSP',  15: u'TAB',
                          16:  u'Q',    17: u'W',     18: u'E',     19: u'R',
                          20:  u'T',    21: u'Y',     22: u'U',     23: u'I',
                          24:  u'O',    25: u'P',     26: u'[',     27: u']',
                          28:  u'CRLF', 29: u'LCTRL', 30: u'A',     31: u'S',
                          32:  u'D',    33: u'F',     34: u'G',     35: u'H',
                          36:  u'J',    37: u'K',     38: u'L',     39: u';',
                          40:  u'"',    41: u'`',     42: u'LSHFT', 43: u'\\',
                          44:  u'Z',    45: u'X',     46: u'C',     47: u'V',
                          48:  u'B',    49: u'N',     50: u'M',     51: u',',
                          52:  u'.',    53: u'/',     54: u'RSHFT', 56: u'LALT',
                          57:  u' ',    100: u'RALT'
        }
        i = 0
        if to > 0:
            while True:
                event = self.device.read_one()
                if skip:
                    skip = 0
                    continue
                if event == None:
                    return ""
                elif event.type == evdev.ecodes.EV_KEY:
                    data = evdev.categorize(event)
                    if data.keystate == 1:
                        carattere = codici_validi.get(data.scancode) or u'NONE'
                        if carattere in codici_validi.values():
                            if carattere == 'LCTRL':
                                skip = 1
                                continue
                            codice += carattere
                            ultimo_carattere = carattere
                            i += 1
                if ultimo_carattere == str(self.terminatore):
                    codice = codice.replace("TAB","")
                    codice = codice.replace("CTAB","")
                    codice = codice.replace("ESC","")
                    codice = codice.replace("BKSP","")
                    codice = codice.replace("CRLF","")
                    codice = codice.replace("LSHFT","")
                    codice = codice.replace("RSHFT","")
                    codice = codice.replace("LALT","")
                    codice = codice.replace("RALT","")
                    codice = codice.replace("/","")
                    self.leggi.off()
                    return codice
                intervallo = time() - tempo_precedente
                if intervallo >= to:
                    self.leggi.off()
                    return ""
        else:
            for event in self.device.read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    data = evdev.categorize(event)
                    if data.keystate == 1:
                        carattere = codici_validi.get(data.scancode) or u'NONE'
                        if carattere in codici_validi.values():
                            if carattere == 'LCTRL':
                                skip = 1
                                continue
                            codice += carattere
                            ultimo_carattere = carattere
                            i += 1
                if (self.attiva_terminatore and \
                    ultimo_carattere == self.terminatore) \
                    or \
                    (self.attiva_limite_caratteri and \
                    i == (self.limite_caratteri)):
                    codice = codice.replace("TAB","")
                    codice = codice.replace("CTAB","")
                    codice = codice.replace("ESC","")
                    codice = codice.replace("BKSP","")
                    codice = codice.replace("CRLF","")
                    codice = codice.replace("LSHFT","")
                    codice = codice.replace("RSHFT","")
                    codice = codice.replace("LALT","")
                    codice = codice.replace("RALT","")
                    codice = codice.replace("/","")
                    self.leggi.off()
                    return codice
        self.leggi.off()
