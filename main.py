from multiprocessing import Process,Lock,Queue
from time            import time,sleep
from oggetto         import oggetto

ipc            = Queue()
lock_ipc       = Lock()
file_configurazione = "pipeline.conf"
configurazione = []
with open(file_configurazione) as f:
    configurazione = f.readlines()

configurazione = [x.strip() for x in configurazione]

######################## Codice Personale qui ##################################
