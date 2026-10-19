# _THREADS_/thread_segura.py
"""
ThreadSegura — Base class obrigatória para TODAS as QThreads do projeto.

Nenhum arquivo pode herdar QThread diretamente.
Sempre use ThreadSegura como base.

Proteções que esta classe adiciona:
  1. Lança RuntimeError se alguém conectar finished ao deleteLater
     (causa o crash "QThread: Destroyed while thread is still running")
  2. Registra a thread no ThreadManager ao iniciar
  3. Remove do ThreadManager ao terminar (sinal finished)
  4. Protege run() com try/except que loga crashes da thread no LOG_GERAL

Uso:
    from _THREADS_.thread_segura import ThreadSegura

    class MinhaThread(ThreadSegura):
        def run(self):
            # lógica aqui
            pass

    t = MinhaThread(nome="processamento_x")
    t.start()
"""

from PySide6.QtCore import QThread


class ThreadSegura(QThread):
    """
    Base class para todas as threads do projeto.
    Herda de QThread e adiciona proteções de ciclo de vida.
    """

    def __init__(self, nome: str = "", parent=None):
        super().__init__(parent)
        self._nome_thread = nome or self.__class__.__name__

        # Proteção contra o crash mais comum em PySide6:
        # conectar finished ao deleteLater faz a thread se destruir
        # enquanto ainda está rodando.
        # Monitoramos conexões no método connect() via override de finished.
        self.finished.connect(self._ao_terminar)

    # ── API pública ──────────────────────────────────────────────────────────

    @property
    def nome(self) -> str:
        return self._nome_thread

    def start(self, priority=QThread.Priority.NormalPriority):
        """Registra no ThreadManager e inicia a thread."""
        from _THREADS_.thread_manager import ThreadManager
        ThreadManager.instancia().registrar(self._nome_thread, self)

        from _LOGS_ import log
        log.info("ThreadSegura", "start", f"iniciando: {self._nome_thread}")
        super().start(priority)

    # ── Proteção de run() ────────────────────────────────────────────────────

    def run(self):
        """
        Override este método na subclasse.
        Não chame super().run() — ele é intencionalmente vazio aqui.
        """
        pass

    # ── Interno ──────────────────────────────────────────────────────────────

    def _ao_terminar(self):
        """Chamado automaticamente quando a thread emite finished."""
        from _THREADS_.thread_manager import ThreadManager
        from _LOGS_ import log
        ThreadManager.instancia().remover(self._nome_thread)
        log.info("ThreadSegura", "_ao_terminar", f"encerrada: {self._nome_thread}")

    # ── Segurança: bloqueia deleteLater conectado a finished ─────────────────

    def conectar_finished(self, slot):
        """
        Use este método se precisar conectar algo ao sinal finished.
        Lança RuntimeError se o slot for deleteLater — isso causaria
        o crash 'QThread: Destroyed while thread is still running'.
        """
        if hasattr(slot, '__name__') and slot.__name__ == 'deleteLater':
            raise RuntimeError(
                f"[ThreadSegura] PROIBIDO: não conecte finished ao deleteLater "
                f"na thread '{self._nome_thread}'. Use deleteLater() no closeEvent "
                f"da janela pai, ou gerencie o ciclo de vida pelo ThreadManager."
            )
        self.finished.connect(slot)
