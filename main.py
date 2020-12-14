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

ipc_entrata                 = Queue()
lock_ipc_entrata            = Lock()
ipc_uscita                  = Queue()
lock_ipc_uscita             = Lock()
file_configurazione         = "pipeline.conf"
file_log                    = "shotstation.log"

segnale_entrata             = ""
segnale_uscita              = ""
segnale_uscita_spacchettato = []

logging.basicConfig(filename=file_log,level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)
######################## Codice Personale qui ##################################
p = gestore_pipeline(file_configurazione,
                     ipc_uscita,
                     lock_ipc_uscita,
                     ipc_entrata,
                     lock_ipc_entrata)
p.start()
sleep(0.001)
with lock_ipc_uscita:
    ipc_uscita.put_nowait("avvia:" + \
                          str(time()) + ":" + \
                          str(__name__) + \
                          ":gestore_pipeline")
sleep(0.001)
p.join()
