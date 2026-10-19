"""Diálogo para configurar o modelo e o serviço Ollama."""

from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from _APPDATA_ import appdata
from _CONFIGURA_ import MODELO_OLLAMA_CONTEUDO, OLLAMA_API_URL


class DialogConfiguracoes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Ollama")
        self.setMinimumWidth(480)

        configuracoes = appdata.ler_config()
        modelo = configuracoes.get("modelo_ollama") or MODELO_OLLAMA_CONTEUDO
        endereco = configuracoes.get("ollama_api_url") or OLLAMA_API_URL

        explicacao = QLabel(
            "Escolha o modelo instalado no Ollama e o endereço da API que o app "
            "deve chamar. Esta tela não baixa nem move modelos."
        )
        explicacao.setWordWrap(True)

        formulario = QFormLayout()
        self.campo_modelo = QLineEdit(str(modelo))
        self.campo_modelo.setPlaceholderText("llama3.2")
        self.campo_modelo.setToolTip(
            "Nome exato do modelo no Ollama, por exemplo llama3.2 ou phi3:mini."
        )
        formulario.addRow("Modelo", self.campo_modelo)

        self.campo_endereco = QLineEdit(str(endereco))
        self.campo_endereco.setPlaceholderText(
            "http://127.0.0.1:11434/api/generate"
        )
        self.campo_endereco.setToolTip(
            "Endereço completo do endpoint de geração do Ollama."
        )
        formulario.addRow("Endereço do Ollama", self.campo_endereco)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(explicacao)
        layout.addLayout(formulario)
        layout.addWidget(botoes)

    def _salvar(self):
        modelo = self.campo_modelo.text().strip()
        endereco = self.campo_endereco.text().strip()
        if not modelo:
            QMessageBox.warning(
                self,
                "Modelo não informado",
                "Digite o nome de um modelo instalado no Ollama.",
            )
            self.campo_modelo.setFocus()
            return

        partes = urlparse(endereco)
        if (
            partes.scheme not in ("http", "https")
            or not partes.netloc
            or not partes.path.rstrip("/").endswith("/api/generate")
        ):
            QMessageBox.warning(
                self,
                "Endereço inválido",
                "Informe o endereço completo do endpoint de geração, por exemplo "
                "http://127.0.0.1:11434/api/generate.",
            )
            self.campo_endereco.setFocus()
            return

        configuracoes = appdata.ler_config()
        configuracoes.update({
            "modelo_ollama": modelo,
            "ollama_api_url": endereco,
        })
        appdata.salvar_config(configuracoes)
        salvo = appdata.ler_config()
        if (
            salvo.get("modelo_ollama") != modelo
            or salvo.get("ollama_api_url") != endereco
        ):
            QMessageBox.critical(
                self,
                "Falha ao salvar",
                "Não foi possível salvar as configurações do Ollama.",
            )
            return
        self.accept()
