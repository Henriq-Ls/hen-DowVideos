"""Interface principal para baixar mídia e gerar transcrições."""

from _CONFIGURA_ import (
    ALTURA_BOTAO,
    ALTURA_BOTAO_PRINCIPAL,
    ALTURA_CARD_OPERACAO,
    ALTURA_PROGRESSO,
    ALTURA_TRANSCRICAO,
    ESPACAMENTO_LAYOUT,
    ESTILO_BTN_CANCELAR,
    ESTILO_BTN_PRIMARIO,
    ESTILO_CABECALHO,
    ESTILO_CARTAO,
    ESTILO_PROGRESSBAR,
    ESTILO_STATUS,
    ESTILO_SUBCABECALHO,
    FORMATOS_AUDIO_DISPONIVEIS,
    FORMATOS_VIDEO_DISPONIVEIS,
    FORMATO_AUDIO_PADRAO,
    FORMATO_VIDEO_PADRAO,
    MARGEM_LAYOUT,
    PASTA_DOWNLOADS_PADRAO,
    ROTULO_QUALIDADE_AUTOMATICA,
    COR_ACENTO,
    COR_BG_CAMPO,
    COR_BORDA,
    COR_TEXTO_SECUNDARIO,
    TAMANHO_ICONE_ACAO,
    TAMANHO_ICONE_OPCAO,
)
from _LOGS_ import log
from _MIDIA_ import HistoricoMidia
from _APP_.dialog_busca import DialogBuscaVideos
from _THREADS_.tarefas_midia import TarefaMidia
from _ULTILIDADES_.icones import (
    ico_analisar,
    ico_audio,
    ico_buscar,
    ico_conteudo,
    ico_processar,
    ico_salvar,
    ico_transcricao,
    ico_video,
    icone,
)
from _ULTILIDADES_.loading_overlay import LoadingOverlay
from _ULTILIDADES_.popups import popup_aviso, popup_erro

from pathlib import Path
import json
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PainelPrincipal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._caminho_transcricao = ""
        self._caminho_conteudo = ""
        self._url_transcricao = ""
        self._titulo_transcricao = ""
        self._dialog_busca = None
        self._overlay = None
        self._montar_ui()

    @property
    def tarefa_ativa(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def _montar_ui(self):
        conteudo_painel = QWidget()
        layout = QVBoxLayout(conteudo_painel)
        layout.setContentsMargins(
            MARGEM_LAYOUT,
            MARGEM_LAYOUT,
            MARGEM_LAYOUT,
            MARGEM_LAYOUT,
        )
        layout.setSpacing(ESPACAMENTO_LAYOUT)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(conteudo_painel)
        layout_externo = QVBoxLayout(self)
        layout_externo.setContentsMargins(0, 0, 0, 0)
        layout_externo.addWidget(scroll)

        titulo = QLabel("HenDowVideos")
        titulo.setStyleSheet(ESTILO_CABECALHO)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Analise o link, escolha uma ou mais tarefas e inicie tudo em uma etapa."
        )
        subtitulo.setStyleSheet(ESTILO_SUBCABECALHO)
        layout.addWidget(subtitulo)

        grupo_fonte = QGroupBox("1. Link e pasta de saída")
        grupo_fonte.setStyleSheet(ESTILO_CARTAO)
        fonte_layout = QVBoxLayout(grupo_fonte)
        fonte_layout.setSpacing(ESPACAMENTO_LAYOUT)

        self.campo_url = QPlainTextEdit()
        self.campo_url.setPlaceholderText(
            "Cole um link ou vários links, um por linha. A análise detalhada "
            "é feita em um link por vez."
        )
        self.campo_url.setMinimumHeight(82)
        self.campo_url.setMaximumHeight(120)
        self.campo_url.setToolTip(
            "Links públicos de vídeo. Para processar vários, coloque um endereço "
            "em cada linha."
        )
        self.campo_url.textChanged.connect(self._ao_alterar_url)
        link_layout = QHBoxLayout()
        link_layout.addWidget(self.campo_url, 1)
        self.botao_verificar = QPushButton("Analisar link")
        self.botao_verificar.setIcon(ico_analisar())
        self.botao_verificar.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_verificar.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_verificar.setMinimumHeight(ALTURA_BOTAO_PRINCIPAL)
        self.botao_verificar.setMinimumWidth(170)
        self.botao_verificar.setToolTip(
            "Consulta título, canal, duração, formato e qualidades disponíveis. "
            "Use um link por vez."
        )
        self.botao_verificar.clicked.connect(self._verificar_link)
        link_layout.addWidget(self.botao_verificar)
        fonte_layout.addWidget(QLabel("Link(s) do vídeo"))
        fonte_layout.addLayout(link_layout)

        self.botao_busca = QPushButton(
            "Buscar vídeos por tema ou palavra-chave"
        )
        self.botao_busca.setIcon(ico_buscar())
        self.botao_busca.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_busca.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_busca.setMinimumHeight(ALTURA_BOTAO)
        self.botao_busca.setToolTip(
            "Abre a busca do YouTube para localizar vídeos e adicionar os links aqui."
        )
        self.botao_busca.clicked.connect(self._abrir_busca)
        fonte_layout.addWidget(self.botao_busca)

        destino_layout = QHBoxLayout()
        destino_layout.setSpacing(ESPACAMENTO_LAYOUT)
        self.campo_destino = QLineEdit(str(Path(PASTA_DOWNLOADS_PADRAO)))
        self.campo_destino.setPlaceholderText("Pasta onde os arquivos serão salvos")
        self.campo_destino.setToolTip(
            "Pasta de destino para mídia, transcrições e arquivos gerados."
        )
        self.botao_pasta = QPushButton("Escolher pasta")
        self.botao_pasta.setIcon(icone("fa5s.folder-open"))
        self.botao_pasta.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_pasta.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_pasta.setMinimumHeight(ALTURA_BOTAO)
        self.botao_pasta.setToolTip("Escolha a pasta onde os resultados serão salvos.")
        self.botao_pasta.clicked.connect(self._escolher_pasta)
        destino_layout.addWidget(self.campo_destino, 1)
        destino_layout.addWidget(self.botao_pasta)
        fonte_layout.addWidget(QLabel("Salvar os resultados em"))
        fonte_layout.addLayout(destino_layout)
        layout.addWidget(grupo_fonte)

        grupo_operacoes = QGroupBox("2. O que você quer fazer?")
        grupo_operacoes.setStyleSheet(ESTILO_CARTAO)
        operacoes_layout = QVBoxLayout(grupo_operacoes)
        operacoes_layout.setSpacing(ESPACAMENTO_LAYOUT)

        operacoes_layout.addWidget(QLabel(
            "Marque todas as tarefas que deseja combinar nesta execução."
        ))
        grade_opcoes = QGridLayout()
        grade_opcoes.setHorizontalSpacing(ESPACAMENTO_LAYOUT)
        grade_opcoes.setVerticalSpacing(ESPACAMENTO_LAYOUT)

        self.card_video, self.opcao_video = self._criar_card_opcao(
            ico_video(),
            "Baixar vídeo",
            "Salvar o vídeo com qualidade e formato escolhidos.",
            "Baixa o vídeo. A qualidade só pode ser preenchida depois de analisar "
            "um link.",
        )
        self.card_audio, self.opcao_audio = self._criar_card_opcao(
            ico_audio(),
            "Baixar áudio",
            "Extrair o som e salvar no formato escolhido.",
            "Extrai e salva o áudio. A conversão depende do FFmpeg instalado.",
        )
        self.card_transcricao, self.opcao_transcricao = self._criar_card_opcao(
            ico_transcricao(),
            "Criar transcrição",
            "Usar legendas disponíveis ou reconhecer a fala.",
            "Primeiro tenta encontrar legendas. Sem legendas, precisa de Whisper e "
            "FFmpeg; o modelo Whisper pode ser baixado na primeira utilização.",
        )
        self.card_conteudo, self.opcao_conteudo = self._criar_card_opcao(
            ico_conteudo(),
            "Gerar conteúdo",
            "Criar um texto estruturado a partir da transcrição.",
            "Precisa do Ollama aberto e do modelo configurado instalado. Se "
            "necessário, a transcrição é criada automaticamente.",
        )
        self._cards_opcao = (
            (self.card_video, self.opcao_video),
            (self.card_audio, self.opcao_audio),
            (self.card_transcricao, self.opcao_transcricao),
            (self.card_conteudo, self.opcao_conteudo),
        )
        grade_opcoes.addWidget(self.card_video, 0, 0)
        grade_opcoes.addWidget(self.card_audio, 0, 1)
        grade_opcoes.addWidget(self.card_transcricao, 1, 0)
        grade_opcoes.addWidget(self.card_conteudo, 1, 1)
        operacoes_layout.addLayout(grade_opcoes)

        self.painel_video = QGroupBox("Opções de vídeo")
        self.painel_video.setStyleSheet(ESTILO_CARTAO)
        painel_video_layout = QHBoxLayout(self.painel_video)
        painel_video_layout.addWidget(QLabel("Qualidade máxima"))
        self.seletor_qualidade = QComboBox()
        self.seletor_qualidade.addItem(ROTULO_QUALIDADE_AUTOMATICA, None)
        self.seletor_qualidade.setToolTip(
            "A lista de qualidades é carregada ao analisar um único link."
        )
        painel_video_layout.addWidget(self.seletor_qualidade, 1)
        painel_video_layout.addWidget(QLabel("Formato do arquivo"))
        self.seletor_formato_video = QComboBox()
        for formato in FORMATOS_VIDEO_DISPONIVEIS:
            self.seletor_formato_video.addItem(formato.upper(), formato)
        self.seletor_formato_video.setToolTip(
            "Escolha o contêiner do arquivo de vídeo. Nem toda troca de contêiner "
            "converte o codec original."
        )
        painel_video_layout.addWidget(self.seletor_formato_video, 1)
        operacoes_layout.addWidget(self.painel_video)

        self.painel_audio = QGroupBox("Opções de áudio")
        self.painel_audio.setStyleSheet(ESTILO_CARTAO)
        audio_layout = QHBoxLayout(self.painel_audio)
        audio_layout.addWidget(QLabel("Formato do arquivo"))
        self.seletor_formato_audio = QComboBox()
        for formato in FORMATOS_AUDIO_DISPONIVEIS:
            self.seletor_formato_audio.addItem(formato.upper(), formato)
        self.seletor_formato_audio.setToolTip(
            "Escolha o formato para salvar o áudio extraído."
        )
        audio_layout.addWidget(self.seletor_formato_audio, 1)
        operacoes_layout.addWidget(self.painel_audio)
        for opcao in (
            self.opcao_video,
            self.opcao_audio,
            self.opcao_transcricao,
            self.opcao_conteudo,
        ):
            opcao.toggled.connect(self._atualizar_selecao)
        self.opcao_video.setChecked(True)

        self.botao_processar = QPushButton("Iniciar processamento")
        self.botao_processar.setIcon(ico_processar())
        self.botao_processar.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_processar.setStyleSheet(ESTILO_BTN_PRIMARIO)
        self.botao_processar.setMinimumHeight(ALTURA_BOTAO_PRINCIPAL)
        self.botao_processar.setToolTip(
            "Executa todas as tarefas marcadas para os links informados."
        )
        self.botao_processar.clicked.connect(self._processar_selecao)
        operacoes_layout.addWidget(self.botao_processar)
        self._atualizar_selecao()
        layout.addWidget(grupo_operacoes)

        grupo_info = QGroupBox("Informações do link")
        grupo_info.setStyleSheet(ESTILO_CARTAO)
        info_layout = QVBoxLayout(grupo_info)
        self.rotulo_info = QLabel(
            "Cole um link e clique em “Analisar link” para consultar os detalhes."
        )
        self.rotulo_info.setWordWrap(True)
        self.rotulo_info.setMinimumHeight(42)
        self.rotulo_info.setToolTip(
            "Título, canal, duração, formato de origem e qualidades detectadas."
        )
        info_layout.addWidget(self.rotulo_info)
        layout.addWidget(grupo_info)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setMinimumHeight(ALTURA_PROGRESSO)
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setStyleSheet(ESTILO_PROGRESSBAR)
        layout.addWidget(self.barra_progresso)

        self.rotulo_status = QLabel("Pronto.")
        self.rotulo_status.setStyleSheet(ESTILO_STATUS)
        layout.addWidget(self.rotulo_status)

        self.abas_resultado = QTabWidget()
        self.abas_resultado.setMinimumHeight(ALTURA_TRANSCRICAO + 40)

        pagina_transcricao = QWidget()
        transcricao_layout = QVBoxLayout(pagina_transcricao)
        self.campo_transcricao = QTextEdit()
        self.campo_transcricao.setReadOnly(True)
        self.campo_transcricao.setPlaceholderText(
            "A transcrição gerada aparecerá aqui. Quando houver legendas, "
            "elas serão usadas primeiro; se não houver, será tentada a "
            "transcrição automática."
        )
        self.campo_transcricao.setMinimumHeight(ALTURA_TRANSCRICAO)
        transcricao_layout.addWidget(self.campo_transcricao)

        salvar_layout = QHBoxLayout()
        salvar_layout.addStretch(1)
        self.botao_salvar_transcricao = QPushButton("Salvar transcrição como…")
        self.botao_salvar_transcricao.setIcon(ico_salvar())
        self.botao_salvar_transcricao.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_salvar_transcricao.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_salvar_transcricao.setMinimumHeight(ALTURA_BOTAO)
        self.botao_salvar_transcricao.setToolTip(
            "Salva o texto da transcrição em um arquivo .txt."
        )
        self.botao_salvar_transcricao.setEnabled(False)
        self.botao_salvar_transcricao.clicked.connect(self._salvar_transcricao)
        salvar_layout.addWidget(self.botao_salvar_transcricao)
        transcricao_layout.addLayout(salvar_layout)
        self.abas_resultado.addTab(pagina_transcricao, "Transcrição")

        pagina_conteudo = QWidget()
        conteudo_layout = QVBoxLayout(pagina_conteudo)
        self.campo_conteudo = QPlainTextEdit()
        self.campo_conteudo.setReadOnly(True)
        self.campo_conteudo.setPlaceholderText(
            "O conteúdo estruturado gerado com Ollama aparecerá aqui."
        )
        conteudo_layout.addWidget(self.campo_conteudo)
        salvar_conteudo_layout = QHBoxLayout()
        salvar_conteudo_layout.addStretch(1)
        self.botao_salvar_conteudo = QPushButton("Salvar conteúdo como JSON…")
        self.botao_salvar_conteudo.setIcon(ico_salvar())
        self.botao_salvar_conteudo.setIconSize(QSize(TAMANHO_ICONE_ACAO, TAMANHO_ICONE_ACAO))
        self.botao_salvar_conteudo.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_salvar_conteudo.setMinimumHeight(ALTURA_BOTAO)
        self.botao_salvar_conteudo.setToolTip(
            "Salva o conteúdo estruturado em um arquivo .json."
        )
        self.botao_salvar_conteudo.setEnabled(False)
        self.botao_salvar_conteudo.clicked.connect(self._salvar_conteudo)
        salvar_conteudo_layout.addWidget(self.botao_salvar_conteudo)
        conteudo_layout.addLayout(salvar_conteudo_layout)
        self.abas_resultado.addTab(pagina_conteudo, "Conteúdo estruturado")

        pagina_historico = QWidget()
        historico_layout = QVBoxLayout(pagina_historico)
        historico_botoes = QHBoxLayout()
        self.botao_atualizar_historico = QPushButton("Atualizar histórico")
        self.botao_atualizar_historico.setIcon(icone("fa5s.sync-alt"))
        self.botao_atualizar_historico.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_atualizar_historico.setMinimumHeight(ALTURA_BOTAO)
        self.botao_atualizar_historico.setToolTip("Atualiza a lista de registros locais.")
        self.botao_atualizar_historico.clicked.connect(self._atualizar_historico)
        self.botao_usar_link_historico = QPushButton(
            "Adicionar link selecionado"
        )
        self.botao_usar_link_historico.setIcon(ico_analisar())
        self.botao_usar_link_historico.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_usar_link_historico.setMinimumHeight(ALTURA_BOTAO)
        self.botao_usar_link_historico.setToolTip(
            "Copia o link do registro selecionado para a área de entrada."
        )
        self.botao_usar_link_historico.clicked.connect(self._usar_link_historico)
        self.botao_abrir_historico = QPushButton("Abrir registro selecionado")
        self.botao_abrir_historico.setIcon(ico_buscar())
        self.botao_abrir_historico.setStyleSheet(ESTILO_BTN_CANCELAR)
        self.botao_abrir_historico.setMinimumHeight(ALTURA_BOTAO)
        self.botao_abrir_historico.setToolTip(
            "Carrega a transcrição ou o conteúdo salvo no histórico."
        )
        self.botao_abrir_historico.clicked.connect(self._abrir_registro_historico)
        historico_botoes.addWidget(self.botao_atualizar_historico)
        historico_botoes.addStretch(1)
        historico_botoes.addWidget(self.botao_usar_link_historico)
        historico_botoes.addWidget(self.botao_abrir_historico)
        historico_layout.addLayout(historico_botoes)
        self.lista_historico = QListWidget()
        self.lista_historico.itemDoubleClicked.connect(
            lambda _item: self._usar_link_historico()
        )
        historico_layout.addWidget(self.lista_historico)
        self.abas_resultado.addTab(pagina_historico, "Histórico local")
        layout.addWidget(self.abas_resultado, 1)
        self._atualizar_historico()

        log.ok("PainelPrincipal", "_montar_ui", "interface de mídia montada")

    def _criar_card_opcao(
        self,
        icone_opcao,
        titulo: str,
        descricao: str,
        dica: str,
    ) -> tuple[QGroupBox, QCheckBox]:
        card = QGroupBox()
        card.setMinimumHeight(ALTURA_CARD_OPERACAO)
        card.setToolTip(dica)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(ESPACAMENTO_LAYOUT)

        icone_label = QLabel()
        icone_label.setPixmap(
            icone_opcao.pixmap(
                QSize(TAMANHO_ICONE_OPCAO, TAMANHO_ICONE_OPCAO)
            )
        )
        icone_label.setToolTip(dica)
        card_layout.addWidget(icone_label, alignment=Qt.AlignmentFlag.AlignTop)

        textos = QVBoxLayout()
        opcao = QCheckBox(titulo)
        opcao.setToolTip(dica)
        textos.addWidget(opcao)
        explicacao = QLabel(descricao)
        explicacao.setWordWrap(True)
        explicacao.setStyleSheet(f"color: {COR_TEXTO_SECUNDARIO};")
        explicacao.setToolTip(dica)
        textos.addWidget(explicacao)
        card_layout.addLayout(textos, 1)
        return card, opcao

    def _atualizar_selecao(self, *_args):
        for card, opcao in getattr(self, "_cards_opcao", ()):
            borda = COR_ACENTO if opcao.isChecked() else COR_BORDA
            card.setStyleSheet(
                f"QGroupBox {{ background: {COR_BG_CAMPO}; border: 1px solid {borda}; "
                "border-radius: 8px; margin-top: 0px; padding: 4px; }"
            )
        self._atualizar_controles_formato()
        if hasattr(self, "botao_processar"):
            tem_selecao = any(
                opcao.isChecked()
                for opcao in (
                    self.opcao_video,
                    self.opcao_audio,
                    self.opcao_transcricao,
                    self.opcao_conteudo,
                )
            )
            self.botao_processar.setEnabled(tem_selecao and not self.tarefa_ativa)

    def _ao_alterar_url(self):
        if hasattr(self, "seletor_qualidade"):
            self._atualizar_qualidades([])
        if hasattr(self, "rotulo_info"):
            self.rotulo_info.setText(
                "O link mudou. Clique em “Analisar link” para atualizar as informações."
            )

    def _escolher_pasta(self):
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Escolher pasta de destino",
            self.campo_destino.text(),
        )
        if pasta:
            self.campo_destino.setText(pasta)

    def _abrir_busca(self):
        self._dialog_busca = DialogBuscaVideos(
            self._adicionar_links_busca,
            parent=self,
        )
        self._dialog_busca.exec()

    def _adicionar_links_busca(self, links: list[str]):
        atuais = self._ler_urls()
        combinados = list(dict.fromkeys([*atuais, *links]))
        self.campo_url.setPlainText("\n".join(combinados))
        self.abas_resultado.setCurrentIndex(0)

    def _atualizar_historico(self):
        self.lista_historico.clear()
        try:
            historico = HistoricoMidia()
            for registro in historico.listar():
                titulo = registro.get("titulo") or registro.get("url") or ""
                detalhes = " · ".join(
                    parte
                    for parte in (
                        registro.get("tipo", ""),
                        registro.get("formato", ""),
                        registro.get("atualizado_em", ""),
                    )
                    if parte
                )
                item = QListWidgetItem(
                    f"{titulo} — {registro.get('status', '')} · {detalhes}"
                )
                item.setData(Qt.ItemDataRole.UserRole, registro.get("url", ""))
                item.setToolTip(str(registro.get("url", "")))
                self.lista_historico.addItem(item)
        except Exception as exc:
            log.erro("PainelPrincipal", "_atualizar_historico", str(exc))
            if hasattr(self, "rotulo_status"):
                self.rotulo_status.setText(
                    f"Não foi possível carregar o histórico local: {exc}"
                )

    def _usar_link_historico(self):
        item = self.lista_historico.currentItem()
        if item is None:
            self.rotulo_status.setText("Selecione um item do histórico.")
            return
        url = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if url:
            self._adicionar_links_busca([url])
            self.rotulo_status.setText("Link do histórico adicionado à lista.")

    def _abrir_registro_historico(self):
        item = self.lista_historico.currentItem()
        if item is None:
            self.rotulo_status.setText("Selecione um item do histórico.")
            return
        url = str(item.data(Qt.ItemDataRole.UserRole) or "")
        try:
            registro = HistoricoMidia().obter(url)
        except Exception as exc:
            self.rotulo_status.setText(
                f"Não foi possível abrir o registro: {exc}"
            )
            return
        if not registro:
            self.rotulo_status.setText("O registro não foi encontrado.")
            return

        texto = str(registro.get("transcricao") or "")
        if texto:
            self.campo_transcricao.setPlainText(texto)
            self._caminho_transcricao = str(
                registro.get("caminho_transcricao") or ""
            )
            self._url_transcricao = url
            self._titulo_transcricao = str(registro.get("titulo") or "")
            self.botao_salvar_transcricao.setEnabled(True)
            self.abas_resultado.setCurrentIndex(0)

        conteudo = registro.get("conteudo")
        if conteudo:
            self._mostrar_conteudo(conteudo)
        elif not texto:
            self.rotulo_status.setText(
                "Este registro não contém transcrição nem conteúdo estruturado."
            )
            return

        self.rotulo_status.setText(
            f"Registro carregado: {registro.get('titulo') or url}"
        )

    def _verificar_link(self):
        urls = self._ler_urls()
        if not urls:
            self._iniciar_tarefa("informacoes", urls=urls)
            return
        if len(urls) > 1:
            popup_aviso(
                "Analise um link por vez",
                "Deixe apenas um link na caixa para consultar título, duração e "
                "qualidades disponíveis. O processamento ainda aceita vários links.",
                self,
            )
            return
        self._iniciar_tarefa("informacoes", urls=urls)

    def _processar_selecao(self):
        baixar_video = self.opcao_video.isChecked()
        baixar_audio = self.opcao_audio.isChecked()
        transcrever = self.opcao_transcricao.isChecked()
        gerar_conteudo = self.opcao_conteudo.isChecked()
        if not any((baixar_video, baixar_audio, transcrever, gerar_conteudo)):
            popup_aviso(
                "Escolha uma tarefa",
                "Marque ao menos uma opção antes de iniciar o processamento.",
                self,
            )
            return
        tipos_download = [
            nome
            for selecionado, nome in (
                (baixar_video, "video"),
                (baixar_audio, "audio"),
            )
            if selecionado
        ]
        self._iniciar_tarefa(
            "processamento",
            tipo="+".join(tipos_download) or "processamento",
            transcrever=transcrever,
            gerar_conteudo=gerar_conteudo,
            baixar_video=baixar_video,
            baixar_audio=baixar_audio,
        )

    def _ler_urls(self) -> list[str]:
        return list(dict.fromkeys(
            linha.strip()
            for linha in self.campo_url.toPlainText().splitlines()
            if linha.strip()
        ))

    def _atualizar_controles_formato(self, ocupado: bool | None = None):
        video_selecionado = self.opcao_video.isChecked()
        audio_selecionado = self.opcao_audio.isChecked()
        livre = not self.tarefa_ativa if ocupado is None else not ocupado
        self.painel_video.setVisible(video_selecionado)
        self.painel_audio.setVisible(audio_selecionado)
        self.seletor_qualidade.setEnabled(video_selecionado and livre)
        self.seletor_formato_video.setEnabled(video_selecionado and livre)
        self.seletor_formato_audio.setEnabled(audio_selecionado and livre)

    def _atualizar_qualidades(self, alturas: list[int]):
        selecionada = self.seletor_qualidade.currentData()
        self.seletor_qualidade.clear()
        self.seletor_qualidade.addItem(ROTULO_QUALIDADE_AUTOMATICA, None)
        for altura in alturas:
            self.seletor_qualidade.addItem(f"{altura}p", altura)
        indice = self.seletor_qualidade.findData(selecionada)
        self.seletor_qualidade.setCurrentIndex(max(0, indice))

    def _iniciar_tarefa(
        self,
        operacao: str,
        tipo: str = "video",
        transcrever: bool = False,
        gerar_conteudo: bool = False,
        baixar_video: bool = False,
        baixar_audio: bool = False,
        urls: list[str] | None = None,
        texto_transcricao: str = "",
        titulo_transcricao: str = "",
    ):
        urls = urls if urls is not None else self._ler_urls()
        if not urls:
            popup_aviso(
                "Falta o link",
                "Cole pelo menos um link de vídeo para continuar.",
                self,
            )
            self.campo_url.setFocus()
            return
        if operacao == "informacoes" and len(urls) > 1:
            popup_aviso(
                "Analise um link por vez",
                "Para consultar as qualidades disponíveis, deixe apenas um link.",
                self,
            )
            return

        destino = self.campo_destino.text().strip()
        if operacao != "informacoes" and not destino:
            popup_aviso(
                "Escolha a pasta de saída",
                "Selecione uma pasta onde os arquivos e resultados serão salvos.",
                self,
            )
            return
        if self.tarefa_ativa:
            return

        self._definir_ocupado(True)
        self.barra_progresso.setRange(0, 0)
        mensagens = {
            "informacoes": "Consultando informações do link…",
            "download": "Iniciando download…",
            "transcricao": "Preparando transcrição…",
            "conteudo": (
                "Preparando transcrição para gerar conteúdo…"
                if not texto_transcricao
                else "Gerando conteúdo estruturado…"
            ),
            "processamento": "Preparando as tarefas selecionadas…",
        }
        self.rotulo_status.setText(mensagens[operacao])

        self._worker = TarefaMidia(
            operacao=operacao,
            url=urls[0],
            urls=urls,
            destino=destino,
            tipo=tipo,
            transcrever_apos_download=transcrever,
            gerar_conteudo_apos_transcricao=gerar_conteudo,
            baixar_video=baixar_video,
            baixar_audio=baixar_audio,
            resolucao_max=(
                self.seletor_qualidade.currentData()
                if baixar_video or tipo == "video" else None
            ),
            formato_video=str(
                self.seletor_formato_video.currentData() or FORMATO_VIDEO_PADRAO
            ),
            formato_audio=str(
                self.seletor_formato_audio.currentData() or FORMATO_AUDIO_PADRAO
            ),
            texto_transcricao=texto_transcricao,
            titulo_transcricao=titulo_transcricao,
            parent=self,
        )
        self._overlay = LoadingOverlay(self.window(), mensagem=mensagens[operacao])
        self._overlay.show()
        self._worker.progresso.connect(self._ao_atualizar_progresso)
        self._worker.resultado.connect(self._ao_receber_resultado)
        self._worker.finished.connect(self._ao_terminar_thread)
        self._worker.start()

    def _definir_ocupado(self, ocupado: bool):
        self.campo_url.setEnabled(not ocupado)
        self.campo_destino.setEnabled(not ocupado)
        self.opcao_video.setEnabled(not ocupado)
        self.opcao_audio.setEnabled(not ocupado)
        self.opcao_transcricao.setEnabled(not ocupado)
        self.opcao_conteudo.setEnabled(not ocupado)
        self._atualizar_controles_formato(ocupado)
        self.botao_pasta.setEnabled(not ocupado)
        self.botao_busca.setEnabled(not ocupado)
        self.botao_verificar.setEnabled(not ocupado)
        self.botao_processar.setEnabled(
            not ocupado
            and any(
                opcao.isChecked()
                for opcao in (
                    self.opcao_video,
                    self.opcao_audio,
                    self.opcao_transcricao,
                    self.opcao_conteudo,
                )
            )
        )
        self.botao_salvar_transcricao.setEnabled(
            not ocupado
            and bool(
                self._caminho_transcricao
                or self.campo_transcricao.toPlainText().strip()
            )
        )
        self.botao_salvar_conteudo.setEnabled(
            not ocupado and bool(self.campo_conteudo.toPlainText().strip())
        )

    def _ao_atualizar_progresso(self, percentual: int, mensagem: str):
        self.rotulo_status.setText(mensagem)
        if self._overlay is not None:
            self._overlay.set_mensagem(mensagem)
        if percentual < 0:
            self.barra_progresso.setRange(0, 0)
            return
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(max(0, min(100, percentual)))

    def _ao_receber_resultado(self, resultado: object):
        if not isinstance(resultado, dict):
            self.rotulo_status.setText("A operação terminou com uma resposta inválida.")
            return

        operacao = resultado.get("operacao")
        if not resultado.get("ok"):
            erro = str(resultado.get("erro") or "Erro não identificado.")
            self.rotulo_status.setText(f"Não foi possível concluir: {erro}")
            if operacao == "informacoes":
                self.rotulo_info.setText(f"Não foi possível verificar o link.\n{erro}")
            self.barra_progresso.setRange(0, 100)
            self.barra_progresso.setValue(0)
            popup_erro("Não foi possível concluir", erro, self)
            return

        dados = resultado.get("dados") or {}
        if operacao == "informacoes":
            alturas = dados.get("available_heights") or []
            self._atualizar_qualidades(alturas)
            lista_qualidades = ", ".join(f"{altura}p" for altura in alturas)
            self.rotulo_info.setText(
                f"Título: {dados.get('title', 'Não informado')}\n"
                f"Canal: {dados.get('uploader', 'Não informado')}\n"
                f"Duração: {dados.get('duration', 'Não informada')}\n"
                f"Resolução: {dados.get('resolution', 'Não informada')}\n"
                f"Formato de origem: {dados.get('format', 'Não informado')}\n"
                f"Qualidades disponíveis: {lista_qualidades or 'não informadas'}"
            )
            self.rotulo_status.setText("Informações carregadas.")
        elif "items" in dados:
            itens = dados.get("items") or []
            sucessos = int(dados.get("success_count") or 0)
            falhas = int(dados.get("failure_count") or 0)
            linhas = []
            transcricoes = []
            conteudos = []
            for item in itens:
                endereco = str(item.get("url") or "")
                if item.get("ok"):
                    linhas.append(f"Concluído: {endereco}")
                else:
                    detalhe_erro = "; ".join(
                        str(erro) for erro in (item.get("erros") or [])
                    )
                    if item.get("transcricao_erro"):
                        detalhe_erro = "; ".join(
                            parte for parte in (
                                detalhe_erro,
                                f"Transcrição: {item['transcricao_erro']}",
                            ) if parte
                        )
                    if item.get("conteudo_erro"):
                        detalhe_erro = "; ".join(
                            parte for parte in (
                                detalhe_erro,
                                f"Conteúdo: {item['conteudo_erro']}",
                            ) if parte
                        )
                    linhas.append(
                        f"Falhou: {endereco} — "
                        f"{detalhe_erro or item.get('erro', 'erro desconhecido')}"
                    )
                transcricao = item.get("transcricao")
                if transcricao:
                    texto = str(transcricao.get("text") or "").strip()
                    if texto:
                        transcricoes.append(f"Link: {endereco}\n\n{texto}")
                conteudo = item.get("conteudo")
                if conteudo:
                    conteudos.append({
                        "url": endereco,
                        "conteudo": conteudo,
                    })
                if item.get("transcricao_erro"):
                    linhas.append(
                        f"Transcrição não concluída: {item['transcricao_erro']}"
                    )
                if item.get("conteudo_erro"):
                    linhas.append(
                        f"Conteúdo estruturado não gerado: {item['conteudo_erro']}"
                    )
                if item.get("historico_erro"):
                    linhas.append(
                        f"Histórico não salvo: {item['historico_erro']}"
                    )
            if transcricoes:
                self.campo_transcricao.setPlainText("\n\n---\n\n".join(transcricoes))
                self._caminho_transcricao = ""
                if len(itens) == 1:
                    item_transcricao = itens[0].get("transcricao") or {}
                    self._caminho_transcricao = str(
                        item_transcricao.get("path") or ""
                    )
                    self._url_transcricao = str(itens[0].get("url") or "")
                    self._titulo_transcricao = str(
                        item_transcricao.get("title") or ""
                    )
                else:
                    self._url_transcricao = ""
                    self._titulo_transcricao = ""
            if conteudos:
                self._mostrar_conteudo(conteudos[0]["conteudo"] if len(conteudos) == 1 else conteudos)
            self.rotulo_status.setText(
                (
                    f"Processamento concluído: {sucessos} sucesso(s), "
                    f"{falhas} falha(s). "
                    if len(itens) == 1
                    else f"Lote concluído: {sucessos} sucesso(s), {falhas} falha(s). "
                )
                + " ".join(linhas)
            )
            if falhas and not sucessos:
                popup_erro(
                    "Nenhum link foi concluído",
                    "Confira os detalhes no status da tela:\n\n"
                    + "\n".join(linhas),
                    self,
                )
            self.barra_progresso.setRange(0, 100)
            self.barra_progresso.setValue(100)
            self._atualizar_historico()
        elif operacao == "download":
            mensagem = str(dados.get("message") or "Download concluído.")
            transcricao = dados.get("transcricao")
            erro_transcricao = dados.get("transcricao_erro")
            if transcricao:
                texto = str(transcricao.get("text") or "")
                self.campo_transcricao.setPlainText(texto)
                self._caminho_transcricao = str(transcricao.get("path") or "")
                self._url_transcricao = self._ler_urls()[0]
                self._titulo_transcricao = str(transcricao.get("title") or "")
                mensagem += (
                    f" Transcrição criada por {transcricao.get('source', 'legenda')} "
                    f"e salva em {self._caminho_transcricao}."
                )
            elif erro_transcricao:
                mensagem += f" A transcrição não foi concluída: {erro_transcricao}"
            if dados.get("conteudo"):
                self._mostrar_conteudo(dados["conteudo"])
                mensagem += " Conteúdo estruturado pronto."
            if dados.get("conteudo_erro"):
                mensagem += (
                    " O conteúdo estruturado não foi gerado: "
                    f"{dados['conteudo_erro']}"
                )
            if dados.get("historico_erro"):
                mensagem += (
                    " O histórico local não foi salvo: "
                    f"{dados['historico_erro']}"
                )
            self.rotulo_status.setText(mensagem)
            self.barra_progresso.setRange(0, 100)
            self.barra_progresso.setValue(100)
            self._atualizar_historico()
        elif operacao == "transcricao":
            texto = str(dados.get("text") or "")
            self.campo_transcricao.setPlainText(texto)
            self._caminho_transcricao = str(dados.get("path") or "")
            self._url_transcricao = self._ler_urls()[0]
            self._titulo_transcricao = str(dados.get("title") or "")
            if dados.get("conteudo"):
                self._mostrar_conteudo(dados["conteudo"])
            origem = str(dados.get("source") or "transcrição")
            mensagem = (
                f"Transcrição gerada a partir de {origem} e salva em "
                f"{self._caminho_transcricao}"
            )
            if dados.get("conteudo_erro"):
                mensagem += (
                    ". Conteúdo estruturado não gerado: "
                    f"{dados['conteudo_erro']}"
                )
            if dados.get("historico_erro"):
                mensagem += (
                    ". Histórico local não salvo: "
                    f"{dados['historico_erro']}"
                )
            self.rotulo_status.setText(mensagem)
            self.barra_progresso.setRange(0, 100)
            self.barra_progresso.setValue(100)
            self._atualizar_historico()
        elif operacao == "conteudo":
            transcricao = dados.get("transcricao") or {}
            texto = str(transcricao.get("text") or "")
            if texto:
                self.campo_transcricao.setPlainText(texto)
                self._caminho_transcricao = str(transcricao.get("path") or "")
                self._url_transcricao = self._ler_urls()[0]
                self._titulo_transcricao = str(transcricao.get("title") or "")
            if dados.get("conteudo"):
                self._mostrar_conteudo(dados["conteudo"])
                mensagem = "Conteúdo estruturado gerado."
            else:
                mensagem = (
                    "A transcrição foi obtida, mas o conteúdo estruturado "
                    "não foi gerado: "
                    + str(dados.get("conteudo_erro") or "erro desconhecido")
                )
            if dados.get("historico_erro"):
                mensagem += (
                    " Histórico local não salvo: "
                    f"{dados['historico_erro']}"
                )
            self.rotulo_status.setText(mensagem)
            self.barra_progresso.setRange(0, 100)
            self.barra_progresso.setValue(100)
            self._atualizar_historico()

    def _mostrar_conteudo(self, conteudo):
        self.campo_conteudo.setPlainText(
            json.dumps(conteudo, ensure_ascii=False, indent=2)
        )
        self._caminho_conteudo = ""
        self.botao_salvar_conteudo.setEnabled(
            bool(self.campo_conteudo.toPlainText().strip())
        )
        self.abas_resultado.setCurrentIndex(1)

    def _ao_terminar_thread(self):
        thread = self.sender()
        if thread is self._worker:
            if self._overlay is not None:
                self._overlay.fechar()
                self._overlay.deleteLater()
                self._overlay = None
            self._worker = None
            self._definir_ocupado(False)
            thread.deleteLater()

    def _salvar_transcricao(self):
        texto = self.campo_transcricao.toPlainText().strip()
        if not texto:
            self.rotulo_status.setText("Não há transcrição para salvar.")
            return

        sugestao = self._caminho_transcricao or str(
            Path(self.campo_destino.text()) / "transcricao.txt"
        )
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar transcrição",
            sugestao,
            "Arquivo de texto (*.txt)",
        )
        if not caminho:
            return
        if Path(caminho).suffix.lower() != ".txt":
            caminho = f"{caminho}.txt"

        try:
            Path(caminho).write_text(texto + "\n", encoding="utf-8")
            self._caminho_transcricao = caminho
            self.rotulo_status.setText(f"Transcrição salva em {caminho}")
            log.ok("PainelPrincipal", "_salvar_transcricao", f"arquivo salvo: {caminho}")
        except OSError as exc:
            log.erro("PainelPrincipal", "_salvar_transcricao", str(exc))
            self.rotulo_status.setText(f"Não foi possível salvar a transcrição: {exc}")

    def _salvar_conteudo(self):
        texto = self.campo_conteudo.toPlainText().strip()
        if not texto:
            self.rotulo_status.setText("Não há conteúdo estruturado para salvar.")
            return

        sugestao = self._caminho_conteudo or str(
            Path(self.campo_destino.text()) / "conteudo_estruturado.json"
        )
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar conteúdo estruturado",
            sugestao,
            "Arquivo JSON (*.json)",
        )
        if not caminho:
            return
        if Path(caminho).suffix.lower() != ".json":
            caminho = f"{caminho}.json"

        try:
            conteudo = json.loads(texto)
            Path(caminho).write_text(
                json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._caminho_conteudo = caminho
            self.rotulo_status.setText(f"Conteúdo estruturado salvo em {caminho}")
            log.ok(
                "PainelPrincipal",
                "_salvar_conteudo",
                f"JSON salvo: {caminho}",
            )
        except (OSError, json.JSONDecodeError) as exc:
            log.erro("PainelPrincipal", "_salvar_conteudo", str(exc))
            self.rotulo_status.setText(
                f"Não foi possível salvar o conteúdo estruturado: {exc}"
            )
