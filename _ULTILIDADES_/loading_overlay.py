# _ULTILIDADES_/loading_overlay.py
"""
LoadingOverlay — overlay modal animado para operações demoradas.

Bloqueia TODOS os cliques na janela enquanto estiver visível (ApplicationModal).
Sem botões. Fecha apenas programaticamente via fechar().
Cores puxadas de _CONFIGURA_ — nunca hardcoded aqui.

────────────────────────────────────────────────────────────────────────────
USO BÁSICO
────────────────────────────────────────────────────────────────────────────

    from _ULTILIDADES_.loading_overlay import LoadingOverlay
    from PySide6.QtWidgets import QApplication

    overlay = LoadingOverlay(self, mensagem="Abrindo projeto...")
    overlay.show()
    QApplication.processEvents()   # garante 1 frame renderizado antes de travar

    try:
        self._fazer_trabalho_pesado()
    finally:
        overlay.fechar()

────────────────────────────────────────────────────────────────────────────
ATUALIZAR MENSAGEM EM TEMPO DE EXECUÇÃO
────────────────────────────────────────────────────────────────────────────

    overlay.set_mensagem("Restaurando sessão...")

────────────────────────────────────────────────────────────────────────────
INTEGRAÇÃO COM ThreadSegura (fechar ao sinal de conclusão)
────────────────────────────────────────────────────────────────────────────

    overlay = LoadingOverlay(self, mensagem="Carregando...")
    overlay.show()
    thread.concluido.connect(overlay.fechar)
    thread.start()

────────────────────────────────────────────────────────────────────────────
REGRAS DE THREAD — NÃO VIOLE
────────────────────────────────────────────────────────────────────────────
• show() e fechar() devem ser chamados na MAIN THREAD.
• fechar() pode ser conectado a Signal de QThread via connect() — o Qt
  despacha automaticamente para a main thread (conexão cross-thread).
• NÃO conecte finished de uma ThreadSegura a fechar() diretamente se o
  objeto da thread e o overlay tiverem o mesmo parent — use um lambda ou
  slot intermediário para evitar ordem de destruição ambígua.
• Se a thread que dispara fechar() puder ser destruída antes do dispatch,
  use Qt.QueuedConnection explicitamente:
      thread.concluido.connect(overlay.fechar, Qt.QueuedConnection)
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget

from _CONFIGURA_ import (
    COR_ACENTO,
    COR_BG_CAMPO,
    COR_BORDA,
    COR_TEXTO_SECUNDARIO,
    ESTILO_PROGRESSBAR,
    FONTE_TAMANHO_LABEL,
)


# ─────────────────────────────────────────────────────────────────────────────
# Spinner
# ─────────────────────────────────────────────────────────────────────────────

class _Spinner(QWidget):
    """
    Spinner de traços radiais animado via QPainter + QTimer.
    Sem GIF, sem dependência externa além de PySide6.
    """

    _N_TRACOS  = 10    # número de traços radiais
    _R_EXT     = 20    # raio externo em px
    _R_INT     = 11    # raio interno em px
    _ESPESSURA = 3     # largura do traço em px
    _INTERVALO = 70    # ms por frame (~14 fps)

    def __init__(self, cor: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cor   = QColor(cor)
        self._passo = 0
        lado = (self._R_EXT + 3) * 2
        self.setFixedSize(lado, lado)

        self._timer = QTimer(self)
        self._timer.setInterval(self._INTERVALO)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def parar(self) -> None:
        """Para a animação — chame antes de destruir o widget."""
        self._timer.stop()

    def ativar(self) -> None:
        """Reativa a animação quando a tarefa não fornece percentual."""
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self) -> None:
        self._passo = (self._passo + 1) % self._N_TRACOS
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width()  / 2.0
        cy = self.height() / 2.0
        ang_passo = (2.0 * math.pi) / self._N_TRACOS

        for i in range(self._N_TRACOS):
            # Cabeçote = passo atual (mais opaco); cauda fica mais transparente
            distancia = (i - self._passo) % self._N_TRACOS
            alpha = int(255 * (1.0 - distancia / self._N_TRACOS))
            alpha = max(20, alpha)  # mínimo para a cauda não sumir

            cor = QColor(self._cor)
            cor.setAlpha(alpha)

            pen = QPen(cor, self._ESPESSURA)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)

            ang   = i * ang_passo
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            p.drawLine(
                int(cx + self._R_INT * cos_a),
                int(cy + self._R_INT * sin_a),
                int(cx + self._R_EXT * cos_a),
                int(cy + self._R_EXT * sin_a),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Overlay principal
# ─────────────────────────────────────────────────────────────────────────────

class LoadingOverlay(QDialog):
    """
    Overlay modal sem botões para operações demoradas.

    Bloqueia toda interação com a aplicação enquanto estiver visível.
    Fecha SOMENTE via fechar() — o usuário não consegue fechar manualmente.

    Parâmetros
    ----------
    parent      : QWidget pai (normalmente MainWindow / self)
    mensagem    : texto exibido abaixo do spinner
    cor_spinner : cor do spinner (padrão: COR_ACENTO do _CONFIGURA_)
    cor_fundo   : cor de fundo do painel (padrão: COR_BG_CAMPO do _CONFIGURA_)
    cor_texto   : cor do texto (padrão: COR_TEXTO_SECUNDARIO do _CONFIGURA_)
    """

    def __init__(
        self,
        parent: QWidget,
        mensagem: str = "Aguarde...",
        cor_spinner: str = COR_ACENTO,
        cor_fundo: str   = COR_BG_CAMPO,
        cor_texto: str   = COR_TEXTO_SECUNDARIO,
    ) -> None:
        super().__init__(parent)

        self._cor_fundo = cor_fundo
        self._cor_borda = COR_BORDA
        self._fechado   = False

        # ── flags da janela ───────────────────────────────────────────────
        # ApplicationModal: bloqueia TODA a aplicação (não só o parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # Impede Alt+F4 / Esc fecharem o overlay acidentalmente
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        # ── layout ────────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(36, 28, 36, 28)

        self._spinner = _Spinner(cor_spinner, self)
        layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self._barra_progresso = QProgressBar(self)
        self._barra_progresso.setRange(0, 100)
        self._barra_progresso.setValue(0)
        self._barra_progresso.setMinimumHeight(16)
        self._barra_progresso.setStyleSheet(ESTILO_PROGRESSBAR)
        self._barra_progresso.hide()
        layout.addWidget(self._barra_progresso)

        self._label = QLabel(mensagem, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            f"color: {cor_texto}; "
            f"font-size: {FONTE_TAMANHO_LABEL}px; "
            f"background: transparent;"
        )
        layout.addWidget(self._label)

        self.setFixedSize(260, 160)

    # ── API pública ───────────────────────────────────────────────────────

    def set_mensagem(self, texto: str) -> None:
        """Atualiza o texto em tempo de execução. Thread-safe via sinal Qt."""
        self._label.setText(texto)

    def set_progresso(self, percentual: int) -> None:
        """Mostra barra quando há percentual; spinner quando a etapa é indeterminada."""
        if percentual < 0:
            self._barra_progresso.hide()
            self._spinner.show()
            self._spinner.ativar()
            return

        self._spinner.parar()
        self._spinner.hide()
        self._barra_progresso.setValue(max(0, min(100, percentual)))
        self._barra_progresso.show()

    def fechar(self) -> None:
        """
        Fecha o overlay e reativa a janela pai.

        Pode ser chamado diretamente ou conectado a um Signal de QThread.
        Idempotente — chamadas repetidas são ignoradas.
        """
        if self._fechado:
            return
        self._fechado = True
        self._spinner.parar()
        self.accept()

    # ── eventos ───────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        """Engole Esc e Enter para não fechar o overlay acidentalmente."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        """Impede fechamento via Alt+F4 ou clique no X."""
        if not self._fechado:
            event.ignore()
            return
        super().closeEvent(event)

    def showEvent(self, event) -> None:
        """Centraliza sobre o parent ao exibir."""
        if self.parent() and hasattr(self.parent(), "frameGeometry"):
            geo = self.parent().frameGeometry()
            self.move(
                geo.center().x() - self.width()  // 2,
                geo.center().y() - self.height() // 2,
            )
        super().showEvent(event)

    def paintEvent(self, event) -> None:
        """Desenha o fundo arredondado (necessário com WA_TranslucentBackground)."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(self._cor_fundo))
        pen = QPen(QColor(self._cor_borda))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRoundedRect(
            QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 10, 10
        )
