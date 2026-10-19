# _CONFIGURA_/__init__.py
"""
Fonte única de verdade para TODOS os valores fixos do projeto.
Nenhum outro arquivo pode ter cores, atalhos, tamanhos ou qualquer
valor fixo — tudo vem daqui.

SEÇÕES:
    APPDATA
    APLICAÇÃO
    FONTES
    JANELA PRINCIPAL
    ATALHOS
    CORES — paleta base
    CORES — UI escuro
    ESTILOS QSS prontos
"""

import os

# ══════════════════════════════════════════════════════════════════════════════
# MODO DE EXECUÇÃO
# ══════════════════════════════════════════════════════════════════════════════
# True  → desenvolvimento: log em nível DEBUG, erros detalhados
# False → produção: log em nível ERROR apenas, sem stack traces no terminal
MODO_DEV = True

# ══════════════════════════════════════════════════════════════════════════════
# APPDATA — pasta do usuário no sistema operacional
# ══════════════════════════════════════════════════════════════════════════════
# Windows: %APPDATA%\hen-dowvideos
# Linux/Mac: ~/hen-dowvideos
NOME_APP_SISTEMA = "hen-dowvideos"
PASTA_APPDATA = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    NOME_APP_SISTEMA
)

# ══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
VERSAO_APP  = "v0.1.0"
TITULO_APP  = "hen-DowVideos"
ARQUIVO_LOCK_APP = f"{NOME_APP_SISTEMA}.lock"
PASTA_DOWNLOADS_PADRAO = os.path.join(os.path.expanduser("~"), "Downloads")
TEMA_QT     = "Fusion"             # tema base do Qt

# Caminhos absolutos — independentes do CWD de execução
_PROJETO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_DIR = os.path.join(_PROJETO_DIR, "FFMPEG")
FFMPEG_SEARCH_DIRS = (
    os.path.join(FFMPEG_DIR, "FFmpeg"),
    os.path.join(_PROJETO_DIR, "FFmpeg"),
    FFMPEG_DIR,
)
FFMPEG_RELATIVE_DIRS = ("bin", "")
FFMPEG_EXECUTABLES = ("ffmpeg.exe", "ffmpeg")
IMAGEM_ICO   = os.path.join(_PROJETO_DIR, "IMAGENS", "icon.ico")
LOGO_MARCA   = os.path.join(_PROJETO_DIR, "IMAGENS", "logo_nome.png")
LOGO_SIMB    = os.path.join(_PROJETO_DIR, "IMAGENS", "logo.png")

# ══════════════════════════════════════════════════════════════════════════════
# FONTES
# ══════════════════════════════════════════════════════════════════════════════
FONTE_NOME_UI       = "Segoe UI"
FONTE_TAMANHO_BASE  = 10     # pontos — fonte padrão da QApplication

FONTE_TAMANHO_TITULO  = 13   # px (CSS/QSS)
FONTE_TAMANHO_INFO    = 12
FONTE_TAMANHO_LABEL   = 11
FONTE_TAMANHO_DETALHE = 10
FONTE_TAMANHO_SUTIL   = 9

# ══════════════════════════════════════════════════════════════════════════════
# JANELA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
LARGURA_PADRAO = 1280
ALTURA_PADRAO  = 800
LARGURA_MIN    = 1024
ALTURA_MIN     = 600
MARGEM_LAYOUT = 24
ESPACAMENTO_LAYOUT = 12
ALTURA_BOTAO = 40
ALTURA_PROGRESSO = 18
ALTURA_TRANSCRICAO = 180
ALTURA_BOTAO_PRINCIPAL = 52
ALTURA_CARD_OPERACAO = 92
TAMANHO_ICONE_ACAO = 22
TAMANHO_ICONE_OPCAO = 28

# ══════════════════════════════════════════════════════════════════════════════
# ATALHOS
# ══════════════════════════════════════════════════════════════════════════════
ATALHO_SAIR           = "Alt+F4"
ATALHO_SALVAR         = "Ctrl+S"
ATALHO_ABRIR          = "Ctrl+O"
ATALHO_NOVO           = "Ctrl+N"
# Adicione atalhos específicos do projeto abaixo

# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD E TRANSCRIÇÃO
# ══════════════════════════════════════════════════════════════════════════════
FORMATO_VIDEO_PADRAO = "mp4"
FORMATO_AUDIO_PADRAO = "mp3"
QUALIDADE_AUDIO_KBPS = "192"
FORMATOS_VIDEO_DISPONIVEIS = ("mp4", "mkv", "mov", "avi", "flv", "wmv", "webm")
FORMATOS_AUDIO_DISPONIVEIS = ("mp3", "m4a", "wav", "flac", "opus")
ROTULO_QUALIDADE_AUTOMATICA = "Melhor disponível"
IDIOMAS_LEGENDA = ("pt", "pt-BR", "en", "en-US")
IDIOMA_TRANSCRICAO = "pt"
MODELO_WHISPER = "base"
OLLAMA_API_URL = os.environ.get(
    "HEN_DOWVIDEOS_OLLAMA_API_URL",
    "http://127.0.0.1:11434/api/generate",
)
MODELO_OLLAMA_CONTEUDO = os.environ.get(
    "HEN_DOWVIDEOS_MODELO_OLLAMA",
    "llama3.2",
)
OLLAMA_TIMEOUT_SEGUNDOS = 300
OLLAMA_TAMANHO_MAX_TRANSCRICAO = 24000
OLLAMA_TAMANHO_CONTEXTO = 8192
BUSCA_MAX_RESULTADOS_PADRAO = 20
BUSCA_MAX_RESULTADOS = 50
BUSCA_VISUALIZACOES_MAX = 2_000_000_000
BUSCA_DURACAO_MAXIMA_MINUTOS = 1440
BUSCA_DIAS_MAXIMO = 3650
HISTORICO_LIMITE_PADRAO = 100
HISTORICO_ARQUIVO = "historico_midias.sqlite3"

# ══════════════════════════════════════════════════════════════════════════════
# CORES — paleta base (nomes semânticos)
# ══════════════════════════════════════════════════════════════════════════════
PRETO          = "#020202"
PRETO_FOSCO    = "#070706"
CINZA_ESCURO   = "#0F1210"
BRANCO         = "#EDEEF0"
AMARELO        = "#FFC107"
AMBAR          = "#E0A800"
VERDE          = "#4ec994"
TURQUESA       = "#00C2A8"
AZUL_CLARO     = "#2196F3"
AZUL           = "#0057FF"
AZUL_ESCURO    = "#1FB8D0"
CORAL          = "#FF6B6B"
VERMELHO       = "#A10510"
LARANJA_ESCURO = "#9E3B02"

# ══════════════════════════════════════════════════════════════════════════════
# CORES — UI escuro (usadas nos estilos QSS abaixo)
# ══════════════════════════════════════════════════════════════════════════════
COR_BG_APP           = "#1a1a1a"   # fundo principal
COR_BG_SECUNDARIO    = "#0d1f25"   # menubar, toolbar, status bar
COR_BG_TERCIARIO     = "#2a2a2a"   # menus, inputs, cards
COR_BG_CAMPO         = "#1e1e1e"   # dialogs, list widgets
COR_BG_ESCURO        = "#222222"   # scrollbars, fundos muito escuros
COR_BORDA            = "#333333"   # bordas gerais
COR_BORDA_CLARA      = "#444444"   # bordas de inputs, handles
COR_TEXTO            = "#dddddd"   # texto principal
COR_TEXTO_SECUNDARIO = "#aaaaaa"   # labels secundários
COR_TEXTO_SUTIL      = "#777777"   # placeholders
COR_TEXTO_INATIVO    = "#666666"   # botões desabilitados
COR_ACENTO           = "#3a7bd5"   # cor de destaque principal
COR_ACENTO_HOVER     = "#2f6bc4"
COR_ACENTO_ATIVO     = "#3a5a8a"   # seleção / checked
COR_ACENTO_BORDA     = "#5a8aba"   # borda do item ativo
COR_SUCESSO          = "#22aa77"
COR_SUCESSO_HOVER    = "#22cc99"
COR_PERIGO           = "#a10510"

# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS QSS — prontos para uso direto
# ══════════════════════════════════════════════════════════════════════════════

ESTILO_ESCURO_GLOBAL = f"""
QMainWindow, QWidget {{
    background: {COR_BG_APP};
    color: {COR_TEXTO};
    font-family: "{FONTE_NOME_UI}", Arial, sans-serif;
    font-size: {FONTE_TAMANHO_LABEL}px;
}}
QSplitter::handle {{ background: {COR_BORDA}; }}
QMenuBar {{
    background: {COR_BG_SECUNDARIO};
    color: {COR_TEXTO};
    border-bottom: 1px solid {COR_BORDA};
}}
QMenuBar::item:selected {{ background: {COR_ACENTO}; }}
QMenu {{
    background: {COR_BG_TERCIARIO};
    color: {COR_TEXTO};
    border: 1px solid {COR_BORDA_CLARA};
}}
QMenu::item:selected {{ background: {COR_ACENTO}; }}
QToolBar {{
    background: {COR_BG_SECUNDARIO};
    border-bottom: 1px solid {COR_BORDA};
    spacing: 4px;
    padding: 2px;
}}
QToolButton {{
    background: transparent;
    color: {COR_TEXTO};
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
}}
QToolButton:hover   {{ background: #3a3a3a; }}
QToolButton:pressed {{ background: {COR_BG_TERCIARIO}; }}
QStatusBar {{
    background: {COR_BG_SECUNDARIO};
    color: {COR_TEXTO_SECUNDARIO};
    border-top: 1px solid {COR_BORDA};
    font-size: {FONTE_TAMANHO_DETALHE}px;
}}
QLineEdit, QComboBox, QTextEdit {{
    background: {COR_BG_TERCIARIO};
    color: {COR_TEXTO};
    border: 1px solid {COR_BORDA_CLARA};
    border-radius: 4px;
    padding: 6px;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {COR_ACENTO_BORDA};
}}
QScrollBar:vertical {{
    background: {COR_BG_ESCURO}; width: 10px; border: none;
}}
QScrollBar::handle:vertical {{
    background: {COR_BORDA_CLARA}; border-radius: 5px; min-height: 20px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {COR_BG_ESCURO}; height: 10px; border: none;
}}
QScrollBar::handle:horizontal {{
    background: {COR_BORDA_CLARA}; border-radius: 5px; min-width: 20px;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{ width: 0; }}
"""

ESTILO_DIALOGO_ESCURO = f"""
QDialog    {{ background: {COR_BG_CAMPO}; color: {COR_TEXTO}; }}
QLabel     {{ color: {COR_TEXTO_SECUNDARIO}; }}
QGroupBox  {{
    color: #bbbbbb;
    border: 1px solid {COR_BORDA};
    border-radius: 4px;
    margin-top: 8px;
    font-size: {FONTE_TAMANHO_LABEL}px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}
QComboBox, QSpinBox, QLineEdit, QDoubleSpinBox {{
    background: {COR_BG_TERCIARIO};
    color: {COR_TEXTO};
    border: 1px solid {COR_BORDA_CLARA};
    border-radius: 3px;
    padding: 3px;
}}
"""

ESTILO_BTN_PRIMARIO = f"""
QPushButton {{
    background: {COR_ACENTO};
    color: #ffffff;
    border: none;
    padding: 8px 20px;
    border-radius: 4px;
    font-size: {FONTE_TAMANHO_INFO}px;
    font-weight: bold;
}}
QPushButton:hover    {{ background: {COR_ACENTO_HOVER}; }}
QPushButton:disabled {{ background: {COR_BG_TERCIARIO}; color: {COR_TEXTO_INATIVO}; }}
"""

ESTILO_BTN_CANCELAR = f"""
QPushButton {{
    background: {COR_BORDA_CLARA};
    color: {COR_TEXTO_SECUNDARIO};
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}}
QPushButton:hover {{ background: {COR_TEXTO_SUTIL}; }}
"""

ESTILO_CARTAO = f"""
QGroupBox {{
    background: {COR_BG_CAMPO};
    border: 1px solid {COR_BORDA};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COR_TEXTO_SECUNDARIO};
    font-size: {FONTE_TAMANHO_INFO}px;
    font-weight: bold;
}}
"""

ESTILO_CABECALHO = f"""
color: {COR_TEXTO};
font-size: {FONTE_TAMANHO_TITULO + 3}px;
font-weight: bold;
"""

ESTILO_SUBCABECALHO = f"""
color: {COR_TEXTO_SECUNDARIO};
font-size: {FONTE_TAMANHO_LABEL}px;
"""

ESTILO_STATUS = f"""
color: {COR_TEXTO_SECUNDARIO};
font-size: {FONTE_TAMANHO_DETALHE}px;
"""

ESTILO_LIST_WIDGET = f"""
QListWidget {{
    background: {COR_BG_APP};
    border: none;
    color: {COR_TEXTO};
}}
QListWidget::item {{ padding: 4px; border-bottom: 1px solid {COR_BORDA}; }}
QListWidget::item:selected {{ background: {COR_ACENTO_ATIVO}; }}
QListWidget::item:hover    {{ background: {COR_BG_TERCIARIO}; }}
"""

ESTILO_PROGRESSBAR = f"""
QProgressBar {{
    background: {COR_BG_TERCIARIO};
    border: 1px solid {COR_BORDA_CLARA};
    border-radius: 3px;
}}
QProgressBar::chunk {{
    background: {COR_ACENTO};
    border-radius: 2px;
}}
"""
