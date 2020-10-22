"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

from multiprocessing  import Process,Lock,Queue
from time             import time,sleep
import logging
import sys
import readline

from gestore_pipeline import gestore_pipeline

##################################### DEBUG ####################################
def inOut(lock_ipc_entrata,ipc_entrata,lock_ipc_uscita,ipc_uscita):
    print("inOut")
    segnale_entrata = ""
    segnale_uscita = ""
    segnale_uscita_spacchettato = []

    while True:
        with lock_ipc_entrata:
            ipc_entrata.put_nowait(segnale_entrata)
        with lock_ipc_uscita:
            if not ipc_uscita.empty():
                while not ipc_uscita.empty():
                    segnale_uscita = ipc_uscita.get_nowait()
                    segnale_uscita_spacchettato[:] = segnale_uscita.split(":")
                    if segnale_uscita_spacchettato[0] == "stop":
                        break
                    print(segnale_uscita_spacchettato)
                if segnale_uscita_spacchettato[0] == "stop":
                    break
            sleep(0.01)
################################## FINE DEBUG ##################################

ipc_entrata                 = Queue()
lock_ipc_entrata            = Lock()
ipc_uscita                  = Queue()
lock_ipc_uscita             = Lock()
file_configurazione         = "pipeline.conf"
file_log                    = "pipeline.log"

segnale_entrata             = ""
segnale_uscita              = ""
segnale_uscita_spacchettato = []

logging.basicConfig(filename=file_log,level=logging.DEBUG)

######################## Codice Personale qui ##################################
p = gestore_pipeline(file_configurazione,
                     ipc_uscita,
                     lock_ipc_uscita,
                     ipc_entrata,
                     lock_ipc_entrata)
p.start()

print("In attesa di idle")
while True:
    pacchetto_segnale = ""
    segnale_entrata   = ""
    segnale = timestamp = mittente = destinatario = ""
    with lock_ipc_entrata:
        if not ipc_entrata.empty():
            pacchetto_segnale = ipc_entrata.get_nowait()
    if pacchetto_segnale != "":
        segnale_spacchettato = pacchetto_segnale.split(":")
        if len(segnale_spacchettato) == 4:
            segnale,timestamp,mittente,destinatario = segnale_spacchettato
            print("Pacchetto da 4")
            print(segnale_spacchettato)
            print(segnale)
            print(timestamp)
            print(mittente)
            print(destinatario)
            if segnale == "idle":
                pacchetto_segnale = "avvia:" + str(time()) + ":" + str(__name__) + ":"
                with lock_ipc_uscita:
                    ipc_uscita.put_nowait(pacchetto_segnale)
                break
            elif segnale == "avvia":
                break
        elif len(segnale_spacchettato) == 3:
            segnale,timestamp,mittente = segnale_spacchettato
            print("Pacchetto da 3")
            print(segnale_spacchettato)
            print(segnale)
            print(timestamp)
            print(mittente)
            print(destinatario)
            if segnale == "idle":
                with lock_ipc_uscita:
                    ipc_uscita.put_nowait("avvia:" + str(time()) + ":" + \
                                          str(__name__) + ":")
                break
            elif segnale == "avvia":
                break
    sleep(0.01)
print("Avviamento")
with lock_ipc_uscita:
    ipc_uscita.put_nowait("avvia:" + str(time()) + ":" + str(__name__) + ":")

while True:
    segnale_uscita_spacchettato[:] = []
    segnale_uscita  = input("Segnale: ")
    segnale_entrata = ""
    with lock_ipc_uscita:
        ipc_uscita.put_nowait(segnale)
    with lock_ipc_entrata:
        if not ipc_entrata.empty():
            segnale_entrata = ipc_entrata.get_nowait()
    if segnale_entrata != "":
        segnale_spacchettato = segnale_entrata.split(":")
        segnale,timestamp,mittente,destinatario = segnale_spacchettato
        print(segnale_entrata)
        print(segnale_spacchettato)
        print(segnale)
        print(timestamp)
        print(mittente)
        print(destinatario)

p.join()
