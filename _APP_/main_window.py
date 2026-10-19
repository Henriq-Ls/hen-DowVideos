# _APP_/main_window.py
"""
MainWindow — Janela principal do projeto.

Responsabilidades:
  - Aplicar tema e estilo global (de _CONFIGURA_)
  - Restaurar e salvar geometria/estado via appdata
  - Conectar shutdown ao thread_manager
  - Montar a estrutura de painéis e widgets

Expanda este arquivo conforme o projeto crescer.
Painéis grandes devem ir para subpastas dentro de _APP_/.
"""

from PySide6.QtWidgets import QDialog, QMainWindow, QToolButton
from PySide6.QtGui import QAction
from PySide6.QtCore import QByteArray, Qt

from _CONFIGURA_ import (
    TITULO_APP, VERSAO_APP,
    LARGURA_PADRAO, ALTURA_PADRAO,
    LARGURA_MIN, ALTURA_MIN,
    IMAGEM_ICO,
    ESTILO_ESCURO_GLOBAL,
    ATALHO_SAIR,
)
from _LOGS_ import log
from _APPDATA_ import appdata
from _THREADS_ import thread_manager
from _ULTILIDADES_.icones import ico_config


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("MainWindow", "__init__", "inicializando janela principal...")

        self._configurar_janela()
        self._aplicar_estilo()
        self._montar_ui()
        self._restaurar_sessao()
        self._conectar_shutdown()

        log.ok("MainWindow", "__init__", "janela principal pronta")

    # ── Configuração ─────────────────────────────────────────────────────────

    def _configurar_janela(self):
        self.setWindowTitle(f"{TITULO_APP} {VERSAO_APP}")
        self.setMinimumSize(LARGURA_MIN, ALTURA_MIN)
        self.resize(LARGURA_PADRAO, ALTURA_PADRAO)

        # Ícone da janela
        import os
        if os.path.isfile(IMAGEM_ICO):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(IMAGEM_ICO))

    def _aplicar_estilo(self):
        self.setStyleSheet(ESTILO_ESCURO_GLOBAL)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _montar_ui(self):
        from _APP_.painel_principal import PainelPrincipal

        self._painel = PainelPrincipal(self)
        self.setCentralWidget(self._painel)
        self._montar_menus()

        # Barra de status
        self.statusBar().showMessage("Pronto")

        log.ok("MainWindow", "_montar_ui", "UI montada")

    def _montar_menus(self):
        menu_arquivo = self.menuBar().addMenu("&Arquivo")
        acao_sair = QAction("Sair", self)
        acao_sair.setShortcut(ATALHO_SAIR)
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

        acao_configuracoes = QAction(
            ico_config(),
            "Configurações do Ollama",
            self,
        )
        acao_configuracoes.triggered.connect(self._abrir_configuracoes)
        menu_arquivo.addSeparator()
        menu_arquivo.addAction(acao_configuracoes)

        self.botao_configuracoes = QToolButton(self.menuBar())
        self.botao_configuracoes.setIcon(ico_config())
        self.botao_configuracoes.setText("Configurações")
        self.botao_configuracoes.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.botao_configuracoes.setAutoRaise(True)
        self.botao_configuracoes.setToolTip(
            "Escolher o modelo e o endereço do serviço Ollama."
        )
        self.botao_configuracoes.clicked.connect(self._abrir_configuracoes)
        self.menuBar().setCornerWidget(
            self.botao_configuracoes,
            Qt.Corner.TopRightCorner,
        )

    def _abrir_configuracoes(self):
        from _APP_.dialog_configuracoes import DialogConfiguracoes

        if DialogConfiguracoes(self).exec() == QDialog.DialogCode.Accepted:
            self.statusBar().showMessage(
                "Configurações do Ollama salvas.",
                5000,
            )

    # ── Sessão ───────────────────────────────────────────────────────────────

    def _restaurar_sessao(self):
        """Restaura geometria e estado salvos na sessão anterior."""
        sessao = appdata.ler_sessao()
        try:
            if "geometria" in sessao:
                self.restoreGeometry(QByteArray.fromBase64(
                    sessao["geometria"].encode()
                ))
            if "estado" in sessao:
                self.restoreState(QByteArray.fromBase64(
                    sessao["estado"].encode()
                ))
            log.ok("MainWindow", "_restaurar_sessao", "sessão restaurada")
        except Exception as e:
            log.aviso("MainWindow", "_restaurar_sessao", f"falha ao restaurar sessão: {e}")

    def _salvar_sessao(self):
        """Salva geometria e estado atual para a próxima sessão."""
        try:
            sessao = {
                "geometria": self.saveGeometry().toBase64().data().decode(),
                "estado":    self.saveState().toBase64().data().decode(),
            }
            appdata.salvar_sessao(sessao)
        except Exception as e:
            log.erro("MainWindow", "_salvar_sessao", f"falha ao salvar sessão: {e}")

    # ── Shutdown ─────────────────────────────────────────────────────────────

    def _conectar_shutdown(self):
        """Conecta encerramento ordenado ao sinal aboutToQuit."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._ao_encerrar)

    def _ao_encerrar(self):
        log.info("MainWindow", "_ao_encerrar", "encerrando aplicação...")
        thread_manager.encerrar_todas()
        log.info("MainWindow", "_ao_encerrar", "shutdown concluído")

    def closeEvent(self, event):
        log.info("MainWindow", "closeEvent", "janela fechando...")
        if getattr(self, "_painel", None) and self._painel.tarefa_ativa:
            self.statusBar().showMessage(
                "Aguarde a operação atual terminar antes de fechar."
            )
            event.ignore()
            return
        self._salvar_sessao()
        super().closeEvent(event)
