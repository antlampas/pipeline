from multiprocessing import Process,Lock
from queue import Queue
from time import time,sleep
from oggetto import oggetto

ipc            = Queue()
lock_ipc       = Lock()
configurazione = []

o = oggetto(configurazione,ipc,lock_ipc)

o.start()
while True:
    comando = input("Invia comando: ")
    pacchetto_segnale = comando + ":" + str(time()) + ":" + __name__ + ":"
    ipc.put(pacchetto_segnale)
o.join()
