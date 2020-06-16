from multiprocessing import Process,Lock,Queue
from time            import time,sleep
from oggetto         import oggetto

ipc            = Queue()
lock_ipc       = Lock()
configurazione = []

o = oggetto(configurazione,ipc,lock_ipc)

o.start()
while True:
    comando = input("Invia comando: ")
    pacchetto_segnale = comando + ":" + str(time()) + ":" + __name__ + ":"
    # print(pacchetto_segnale)
    # print(type(pacchetto_segnale))
    with lock_ipc:
        ipc.put_nowait(pacchetto_segnale)
    sleep(1)
o.join()
