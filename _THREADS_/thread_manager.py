# _THREADS_/thread_manager.py
"""
ThreadManager — Gerenciador central de todas as threads do projeto.

Responsabilidades:
  - Manter registro de todas as threads ativas
  - Encerrar todas ordenadamente no shutdown (aboutToQuit)
  - Logar estado das threads: início, término, timeout

Uso:
    from _THREADS_ import thread_manager

    # Encerrar todas no shutdown (conectar ao aboutToQuit da QApplication):
    app.aboutToQuit.connect(thread_manager.encerrar_todas)

    # Verificar threads ainda rodando:
    ativas = thread_manager.listar_ativas()
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _THREADS_.thread_segura import ThreadSegura


def _log():
    from _LOGS_ import log as _l
    return _l


class ThreadManager:
    """Singleton — registro central de todas as threads ativas."""
    _inst: "ThreadManager | None" = None

    @classmethod
    def instancia(cls) -> "ThreadManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        # dict: nome_thread → instância ThreadSegura
        self._threads: dict[str, "ThreadSegura"] = {}

    # ── API pública ──────────────────────────────────────────────────────────

    def registrar(self, nome: str, thread: "ThreadSegura"):
        """
        Registra uma thread ativa.
        Chamado automaticamente pelo ThreadSegura.start().
        """
        if nome in self._threads:
            _log().aviso(
                "ThreadManager", "registrar",
                f"thread '{nome}' já registrada — sobrescrevendo"
            )
        self._threads[nome] = thread
        _log().info(
            "ThreadManager", "registrar",
            f"registrada: '{nome}' | ativas: {len(self._threads)}"
        )

    def remover(self, nome: str):
        """
        Remove uma thread do registro.
        Chamado automaticamente quando a thread emite finished.
        """
        if nome in self._threads:
            del self._threads[nome]
            _log().info(
                "ThreadManager", "remover",
                f"removida: '{nome}' | ativas: {len(self._threads)}"
            )

    def listar_ativas(self) -> list[str]:
        """Retorna lista dos nomes das threads ainda registradas."""
        return list(self._threads.keys())

    def encerrar_todas(self, timeout_ms: int = 3000):
        """
        Para todas as threads registradas ordenadamente.
        Chamado no aboutToQuit da QApplication.

        Para cada thread:
          1. Chama quit() (pede para o event loop da thread parar)
          2. Aguarda até timeout_ms milissegundos
          3. Se ainda rodando, força terminate() e loga como erro
        """
        if not self._threads:
            _log().info("ThreadManager", "encerrar_todas", "nenhuma thread ativa")
            return

        nomes = list(self._threads.keys())
        _log().info(
            "ThreadManager", "encerrar_todas",
            f"encerrando {len(nomes)} thread(s): {nomes}"
        )

        for nome, thread in list(self._threads.items()):
            try:
                if thread.isRunning():
                    thread.quit()
                    terminou = thread.wait(timeout_ms)
                    if terminou:
                        _log().ok(
                            "ThreadManager", "encerrar_todas",
                            f"'{nome}' encerrada normalmente"
                        )
                    else:
                        _log().erro(
                            "ThreadManager", "encerrar_todas",
                            f"'{nome}' não respondeu em {timeout_ms}ms — forçando terminate()"
                        )
                        thread.terminate()
                        thread.wait(1000)
            except Exception as e:
                _log().erro(
                    "ThreadManager", "encerrar_todas",
                    f"erro ao encerrar '{nome}': {e}"
                )

        restantes = [n for n, t in self._threads.items() if t.isRunning()]
        if restantes:
            _log().erro(
                "ThreadManager", "encerrar_todas",
                f"threads ainda rodando após shutdown: {restantes}"
            )
        else:
            _log().ok("ThreadManager", "encerrar_todas", "todas as threads encerradas")
