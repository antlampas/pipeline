"""
Autore: Francesco Antonetti Lamorgese Passeri

This work is licensed under the Creative Commons Attribution 4.0 International
License. To view a copy of this license, visit
http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""

from multiprocessing import Process

class processo(Process):
    """Interfaccia Processo

    Interfaccia per quando si deve creare un Processo
    """
    def __init__(self,coda_ipc,lock_ipc):
        super().__init__()
    def idle(self):
        pass
    def avvia(self):
        pass
    def ferma(self):
        pass
    def termina(self):
        pass
    def sospendi(self):
        pass
    def uccidi(self):
        pass
