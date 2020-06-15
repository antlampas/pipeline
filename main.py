from multiprocessing import Process,Lock
from queue import Queue
from time import time,sleep
from oggetto import oggetto

ipc            = Queue()
lock_ipc       = Lock()
configurazione = []

o = oggetto(configurazione,ipc,lock_ipc)
o.start()
o.join()
