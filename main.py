# main.py — Ponto de entrada do projeto
"""
Responsabilidades ÚNICAS deste arquivo (nesta ordem):
  1. Garantir que o diretório do projeto está no sys.path
  2. Ativar faulthandler (captura crashes nativos C/Qt antes de qualquer import)
  3. Inicializar o logger → cria LOG_GERAL.log
  4. Inicializar appdata → cria estrutura de pastas do usuário
  5. Registrar crash handler global (sys.excepthook)
  6. Criar QApplication e exibir MainWindow
"""
import sys
import os
import traceback
import faulthandler

# ── Bootstrap: garante que o diretório do projeto está no path ────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

# ── faulthandler — captura segfaults e crashes nativos C/Qt ──────────────────
# DEVE ser ativado antes de qualquer import do PySide6
faulthandler.enable()

# ── Logger (cria LOG_GERAL.log da sessão) ─────────────────────────────────────
from _LOGS_ import log

# ── AppData (cria estrutura de pastas no computador do usuário) ───────────────
from _APPDATA_ import appdata
appdata.inicializar()

# ── Crash handler global ──────────────────────────────────────────────────────
def _excepthook(tipo, valor, tb):
    """Captura qualquer exceção não tratada e salva no log antes de exibir."""
    texto = "".join(traceback.format_exception(tipo, valor, tb))
    log.crash("main.py", "excepthook", texto)
    sys.__excepthook__(tipo, valor, tb)

sys.excepthook = _excepthook

from _CONFIGURA_ import (
    FONTE_NOME_UI, FONTE_TAMANHO_BASE,
    TITULO_APP, IMAGEM_ICO, ARQUIVO_LOCK_APP
)

# ── Single instance — impede abrir o app duas vezes ──────────────────────────
from PySide6.QtCore import QLockFile
import tempfile

_LOCK_PATH = os.path.join(tempfile.gettempdir(), ARQUIVO_LOCK_APP)
_lock_file = QLockFile(_LOCK_PATH)
_lock_file.setStaleLockTime(0)

if not _lock_file.tryLock(100):
    # Já existe uma instância rodando
    from PySide6.QtWidgets import QApplication, QMessageBox
    _app_tmp = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.warning(
        None,
        "Já está aberto",
        "O aplicativo já está em execução."
    )
    sys.exit(0)

# ── Imports Qt e módulos do projeto ───────────────────────────────────────────
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from _APP_.main_window import MainWindow


def _qt_msg_handler(mode, context, message):
    """Filtra e loga mensagens internas do Qt."""
    if "setPointSize" in message and "Point size <= 0" in message:
        return  # qtawesome usa pixelSize; pointSize retorna -1 por design
    if mode == QtMsgType.QtWarningMsg:
        log.aviso("Qt", "msg_handler", message)
    elif mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        log.erro("Qt", "msg_handler", message)


def main():
    log.info("main.py", "main", f"{TITULO_APP} iniciando...")

    qInstallMessageHandler(_qt_msg_handler)
    app = QApplication(sys.argv)

    if FONTE_TAMANHO_BASE and FONTE_TAMANHO_BASE > 0:
        app.setFont(QFont(FONTE_NOME_UI, FONTE_TAMANHO_BASE))

    if os.path.isfile(IMAGEM_ICO):
        app.setWindowIcon(QIcon(IMAGEM_ICO))
        log.ok("main.py", "main", f"Ícone carregado: {IMAGEM_ICO}")
    else:
        log.aviso("main.py", "main", f"icon.ico não encontrado: {IMAGEM_ICO}")

    log.ok("main.py", "main", "QApplication criada")
    win = MainWindow()
    win.show()
    log.ok("main.py", "main", "MainWindow exibida")

    code = app.exec()
    log.info("main.py", "main", f"App encerrada com código {code}")
    sys.exit(code)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        texto = traceback.format_exc()
        log.crash("main.py", "__main__", texto)
        sys.exit(1)
