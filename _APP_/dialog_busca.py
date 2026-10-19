"""Janela de busca de vídeos do YouTube por tema ou palavra-chave."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from _LOGS_ import log
from _CONFIGURA_ import (
    BUSCA_DIAS_MAXIMO,
    BUSCA_DURACAO_MAXIMA_MINUTOS,
    BUSCA_MAX_RESULTADOS,
    BUSCA_MAX_RESULTADOS_PADRAO,
    BUSCA_VISUALIZACOES_MAX,
)
from _MIDIA_ import HistoricoMidia
from _THREADS_.tarefas_midia import TarefaMidia


class DialogBuscaVideos(QDialog):
    def __init__(self, ao_adicionar, parent=None):
        super().__init__(parent)
        self._ao_adicionar = ao_adicionar
        self._worker = None
        self.setWindowTitle("Buscar vídeos no YouTube")
        self.resize(780, 560)
        self._montar_ui()

    def _montar_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Pesquise por tema ou palavras-chave. Os resultados vêm do YouTube."
        ))

        consulta_layout = QHBoxLayout()
        self.campo_consulta = QLineEdit()
        self.campo_consulta.setPlaceholderText("Ex.: notícias de tecnologia")
        self.botao_buscar = QPushButton("Buscar")
        self.botao_buscar.clicked.connect(self._buscar)
        self.campo_consulta.returnPressed.connect(self._buscar)
        consulta_layout.addWidget(self.campo_consulta, 1)
        consulta_layout.addWidget(self.botao_buscar)
        layout.addLayout(consulta_layout)

        filtros_layout = QHBoxLayout()
        self.spin_resultados = QSpinBox()
        self.spin_resultados.setRange(1, BUSCA_MAX_RESULTADOS)
        self.spin_resultados.setValue(BUSCA_MAX_RESULTADOS_PADRAO)
        self.spin_resultados.setPrefix("Até ")
        self.spin_resultados.setSuffix(" resultados")
        self.spin_visualizacoes = QSpinBox()
        self.spin_visualizacoes.setRange(0, BUSCA_VISUALIZACOES_MAX)
        self.spin_visualizacoes.setPrefix("Mín. visualizações: ")
        self.spin_duracao_minima = QSpinBox()
        self.spin_duracao_minima.setRange(0, BUSCA_DURACAO_MAXIMA_MINUTOS)
        self.spin_duracao_minima.setPrefix("Duração mín. (min): ")
        self.spin_duracao_maxima = QSpinBox()
        self.spin_duracao_maxima.setRange(0, BUSCA_DURACAO_MAXIMA_MINUTOS)
        self.spin_duracao_maxima.setPrefix("Duração máx. (min): ")
        self.spin_dias = QSpinBox()
        self.spin_dias.setRange(0, BUSCA_DIAS_MAXIMO)
        self.spin_dias.setPrefix("Enviados nos últimos (dias): ")
        self.spin_dias.setSpecialValueText("Qualquer data")
        for controle in (
            self.spin_resultados,
            self.spin_visualizacoes,
            self.spin_duracao_minima,
            self.spin_duracao_maxima,
            self.spin_dias,
        ):
            filtros_layout.addWidget(controle)
        layout.addLayout(filtros_layout)

        self.lista_resultados = QListWidget()
        self.lista_resultados.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        layout.addWidget(self.lista_resultados, 1)

        self.rotulo_status = QLabel("Pronto.")
        layout.addWidget(self.rotulo_status)

        botoes_layout = QHBoxLayout()
        self.botao_adicionar_selecionados = QPushButton(
            "Adicionar selecionados aos links"
        )
        self.botao_adicionar_todos = QPushButton("Adicionar todos os resultados")
        self.botao_fechar = QPushButton("Fechar")
        self.botao_adicionar_selecionados.clicked.connect(
            self._adicionar_selecionados
        )
        self.botao_adicionar_todos.clicked.connect(self._adicionar_todos)
        self.botao_fechar.clicked.connect(self.reject)
        botoes_layout.addWidget(self.botao_adicionar_selecionados)
        botoes_layout.addWidget(self.botao_adicionar_todos)
        botoes_layout.addStretch(1)
        botoes_layout.addWidget(self.botao_fechar)
        layout.addLayout(botoes_layout)

    def _buscar(self):
        consulta = self.campo_consulta.text().strip()
        if not consulta:
            self.rotulo_status.setText("Digite um tema ou palavra-chave.")
            self.campo_consulta.setFocus()
            return
        if self._worker is not None and self._worker.isRunning():
            return

        duracao_minima = self.spin_duracao_minima.value()
        duracao_maxima = self.spin_duracao_maxima.value()
        if duracao_maxima and duracao_maxima < duracao_minima:
            self.rotulo_status.setText(
                "A duração máxima precisa ser igual ou maior que a mínima."
            )
            return

        self.lista_resultados.clear()
        self._definir_ocupado(True)
        self.rotulo_status.setText("Pesquisando no YouTube…")
        self._worker = TarefaMidia(
            operacao="pesquisa",
            url="",
            urls=[],
            consulta=consulta,
            max_resultados=self.spin_resultados.value(),
            visualizacoes_minimas=self.spin_visualizacoes.value(),
            duracao_minima_segundos=duracao_minima * 60,
            duracao_maxima_segundos=duracao_maxima * 60,
            dias_atras=self.spin_dias.value(),
            parent=self,
        )
        self._worker.resultado.connect(self._ao_receber_resultado)
        self._worker.finished.connect(self._ao_terminar_busca)
        self._worker.start()

    def _ao_receber_resultado(self, resultado):
        if not isinstance(resultado, dict) or not resultado.get("ok"):
            erro = (
                resultado.get("erro", "Não foi possível concluir a pesquisa.")
                if isinstance(resultado, dict)
                else "A pesquisa retornou uma resposta inválida."
            )
            self.rotulo_status.setText(str(erro))
            return

        videos = (resultado.get("dados") or {}).get("items") or []
        try:
            historico = HistoricoMidia()
        except Exception as exc:
            log.aviso(
                "DialogBuscaVideos",
                "_ao_receber_resultado",
                f"não foi possível abrir o histórico: {exc}",
            )
            historico = None
        for video in videos:
            url = str(video.get("url") or "")
            if not url:
                continue
            try:
                ja_processado = historico.existe_url(url) if historico else False
            except Exception as exc:
                log.aviso(
                    "DialogBuscaVideos",
                    "_ao_receber_resultado",
                    f"não foi possível consultar o histórico: {exc}",
                )
                ja_processado = False
            duracao = str(video.get("duration") or "duração desconhecida")
            visualizacoes = int(video.get("views") or 0)
            linha = (
                f"{video.get('title', 'Vídeo sem título')} · {duracao} · "
                f"{visualizacoes:,} visualizações"
            )
            if ja_processado:
                linha += " · já processado"
            item = QListWidgetItem(linha)
            item.setData(Qt.ItemDataRole.UserRole, url)
            item.setToolTip(url)
            self.lista_resultados.addItem(item)

        quantidade = len(videos)
        self.rotulo_status.setText(
            f"{quantidade} resultado(s). Selecione os que quer adicionar aos links."
        )

    def _ao_terminar_busca(self):
        worker = self.sender()
        if worker is self._worker:
            self._worker = None
            self._definir_ocupado(False)
            worker.deleteLater()

    def _definir_ocupado(self, ocupado: bool):
        self.campo_consulta.setEnabled(not ocupado)
        self.botao_buscar.setEnabled(not ocupado)
        for controle in (
            self.spin_resultados,
            self.spin_visualizacoes,
            self.spin_duracao_minima,
            self.spin_duracao_maxima,
            self.spin_dias,
        ):
            controle.setEnabled(not ocupado)

    def _adicionar_urls(self, urls: list[str]):
        urls_validos = list(dict.fromkeys(url for url in urls if url))
        if not urls_validos:
            self.rotulo_status.setText("Selecione pelo menos um resultado.")
            return
        self._ao_adicionar(urls_validos)
        self.rotulo_status.setText(
            f"{len(urls_validos)} link(s) adicionado(s) à lista principal."
        )

    def _adicionar_selecionados(self):
        urls = [
            str(item.data(Qt.ItemDataRole.UserRole) or "")
            for item in self.lista_resultados.selectedItems()
        ]
        self._adicionar_urls(urls)

    def _adicionar_todos(self):
        urls = [
            str(self.lista_resultados.item(indice).data(Qt.ItemDataRole.UserRole) or "")
            for indice in range(self.lista_resultados.count())
        ]
        self._adicionar_urls(urls)

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self.rotulo_status.setText("Aguarde a pesquisa terminar antes de fechar.")
            event.ignore()
            return
        event.accept()

    def reject(self):
        if self._worker is not None and self._worker.isRunning():
            self.rotulo_status.setText("Aguarde a pesquisa terminar antes de fechar.")
            return
        super().reject()
