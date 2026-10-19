# _THREADS_/__init__.py
"""
Gerenciamento central de threads do projeto.

Uso:
    from _THREADS_ import thread_manager
    from _THREADS_.thread_segura import ThreadSegura

    # Criar uma thread:
    class MinhaThread(ThreadSegura):
        def run(self):
            pass   # lógica aqui

    t = MinhaThread(nome="minha_thread")
    t.start()  # registra automaticamente no thread_manager

    # Encerrar todas (chamado no shutdown):
    thread_manager.encerrar_todas()
"""

from _THREADS_.thread_manager import ThreadManager
from _THREADS_.thread_segura import ThreadSegura

thread_manager: ThreadManager = ThreadManager.instancia()

__all__ = ["ThreadManager", "ThreadSegura", "thread_manager"]
