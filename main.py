from multiprocessing import Process,Lock,Queue
from time            import time,sleep
from oggetto         import oggetto

ipc            = Queue()
lock_ipc       = Lock()
configurazione = []

o = oggetto(configurazione,ipc,lock_ipc)

o.start()
while True:
    comando      = input("Invia comando: ")
    destinatario = input("A: ")
    pacchetto_segnale = comando + ":" + str(time()) + ":" + __name__ + ":" + destinatario
    with lock_ipc:
        ipc.put_nowait(pacchetto_segnale)
    sleep(0.001)
o.join()
