from multiprocessing  import Process,Lock,Queue
from time             import time,sleep
from random           import uniform
from oggetto          import oggetto
from gestore_pipeline import gestore_pipeline

ipc_entrata      = Queue()
lock_ipc_entrata = Lock()
ipc_uscita       = Queue()
lock_ipc_uscita  = Lock()
file_configurazione = "pipeline.conf"

######################## Codice Personale qui ##################################
p = gestore_pipeline(file_configurazione,
                     ipc_uscita,
                     lock_ipc_uscita,
                     ipc_entrata,
                     lock_ipc_entrata)
p.start()

with lock_ipc_uscita:
    ipc_uscita.put_nowait("avvia:" + str(time()) + ":" + str(__name__) + ":")

while True:
    pacchetto_segnale = ""
    with lock_ipc_entrata:
        if not ipc_entrata.empty():
            pacchetto_segnale = ipc_entrata.get_nowait()
    if pacchetto_segnale != "":
        segnale_spacchettato = pacchetto_segnale.split(":")
        if len(segnale_spacchettato) == 4:
            segnale,timestamp,mittente,destinatario = segnale_spacchettato
            if segnale == "idle":
                pacchetto_segnale = "avvia:" + str(time()) + ":" + str(__name__) + ":"
                with lock_ipc_uscita:
                    ipc_uscita.put_nowait(pacchetto_segnale)
                break
        elif len(segnale_spacchettato) == 3:
            segnale,timestamp,mittente = segnale_spacchettato
            if segnale == "idle":
                with lock_ipc:
                    ipc.put_nowait("avvia:" + str(time()) + ":" + str(__name__) + ":")
                break
    sleep(uniform(0.001,0.200))
print("Avviamento")
with lock_ipc_uscita:
    ipc_uscita.put_nowait("avvia:" + str(time()) + ":" + str(__name__) + ":")

p.join()
