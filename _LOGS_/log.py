# _LOGS_/log.py
"""
Logger — Singleton de logging unificado do projeto.

Gera UM único arquivo: LOG_GERAL.log
  → recebe tudo em ordem cronológica: ok / info / aviso / erro / crash / fault
  → faulthandler (crash nativo C/Qt) também aponta para ele diretamente

Pasta: PASTA_APPDATA/logs/  (constante definida em _CONFIGURA_)

Regras obrigatórias:
  - Singleton — uma única instância durante toda a vida do processo
  - Recria o arquivo a cada sessão — não acumula entre execuções
  - Todo open/write dentro de try/except silencioso — JAMAIS trava a UI
  - Pasta criada automaticamente se não existir
"""
import os
import datetime
import faulthandler

from _CONFIGURA_ import PASTA_APPDATA, MODO_DEV


def _pasta_logs() -> str:
    pasta = os.path.join(PASTA_APPDATA, "logs")
    os.makedirs(pasta, exist_ok=True)
    return pasta


class Logger:
    """Singleton — única instância durante toda a vida do processo."""
    _inst: "Logger | None" = None

    @classmethod
    def instancia(cls) -> "Logger":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        self._pasta   = _pasta_logs()
        self._session = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Único arquivo de log — recriado a cada sessão
        self.caminho_geral = os.path.join(self._pasta, "LOG_GERAL.log")

        with open(self.caminho_geral, "w", encoding="utf-8") as f:
            f.write("")

        # Cabeçalho de sessão
        modo = "DEV" if MODO_DEV else "PROD"
        self._escrever(f"{'═' * 60}")
        self._escrever(f"  SESSÃO INICIADA: {self._session}  [MODO: {modo}]")
        self._escrever(f"{'═' * 60}")

        # faulthandler aponta direto para o LOG_GERAL
        # (crash nativo C/Qt escreve inline, mantendo ordem cronológica)
        try:
            self._arq_fault = open(self.caminho_geral, "a", encoding="utf-8")
            self._arq_fault.write(
                f"\n{'═' * 60}\n  FAULTHANDLER ATIVO\n{'═' * 60}\n"
            )
            self._arq_fault.flush()
            faulthandler.enable(file=self._arq_fault)
        except Exception:
            pass

    # ── API pública ──────────────────────────────────────────────────────────

    def ok(self, modulo: str, funcao: str, msg: str):
        """Operação completou com sucesso. Só registra em MODO_DEV."""
        if MODO_DEV:
            self._log("OK   ", modulo, funcao, msg)

    def info(self, modulo: str, funcao: str, msg: str):
        """Fluxo normal do código. Só registra em MODO_DEV."""
        if MODO_DEV:
            self._log("INFO ", modulo, funcao, msg)

    def aviso(self, modulo: str, funcao: str, msg: str):
        """Algo inesperado mas o app continua. Sempre registra."""
        self._log("AVISO", modulo, funcao, msg)

    def erro(self, modulo: str, funcao: str, msg: str):
        """Exceção capturada em try/except. Sempre registra."""
        self._log("ERRO ", modulo, funcao, msg)

    def crash(self, modulo: str, funcao: str, texto: str):
        """Exceção não tratada — chegou ao sys.excepthook."""
        self._secao("CRASH")
        self._escrever(f"[CRASH] [{modulo}.{funcao}]")
        self._escrever(texto.strip())
        self._fim_secao()

    def fault(self, texto: str):
        """Dump manual de faulthandler (crash nativo C/Qt)."""
        self._secao("FAULTHANDLER")
        self._escrever(texto.strip())
        self._fim_secao()

    @property
    def pasta(self) -> str:
        """Pasta onde fica o LOG_GERAL.log."""
        return self._pasta

    # ── Interno ──────────────────────────────────────────────────────────────

    def _log(self, nivel: str, modulo: str, funcao: str, msg: str):
        self._escrever(f"[{nivel}] [{modulo}.{funcao}] {msg}")

    def _secao(self, titulo: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        linha = f"\n[{ts}] {'═' * 20} {titulo} {'═' * 20}"
        try:
            with open(self.caminho_geral, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
        except Exception:
            pass

    def _fim_secao(self):
        try:
            with open(self.caminho_geral, "a", encoding="utf-8") as f:
                f.write(f"{'─' * 60}\n")
        except Exception:
            pass

    def _escrever(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            with open(self.caminho_geral, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass  # o logger jamais pode travar a UI


# Instância singleton exportada
log: Logger = Logger.instancia()
