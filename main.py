from multiprocessing import Process,Lock,Queue
from time            import time,sleep
from oggetto         import oggetto

ipc            = Queue()
lock_ipc       = Lock()
configurazione = []
termina        = 0
o = oggetto(configurazione,ipc,lock_ipc)

o.start()
while True:
    termina           = 0
    comando           = input("Invia comando: ")
    destinatario      = input("A: ")
    pacchetto_segnale = comando + ":" + str(time()) + ":" + __name__ + ":" + destinatario
    with lock_ipc:
        ipc.put_nowait(pacchetto_segnale)
        pacchetto_segnale = ""
    with lock_ipc:
        if not ipc.empty():
            pacchetto_segnale    = ipc.get_nowait()
            segnale_spacchettato = pacchetto_segnale.split(":")
            print(segnale_spacchettato[0])
            if segnale_spacchettato[0] == "terminato":
                termina = 1
            else:
                ipc.put_nowait(pacchetto_segnale)
                pacchetto_segnale       = ""
                segnale_spacchettato[:] = []
    if termina:
        break
    sleep(0.001)
o.join()
