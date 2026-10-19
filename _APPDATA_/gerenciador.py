# _APPDATA_/gerenciador.py
"""
GerenciadorAppData — Singleton Facade do AppData

Ponto ÚNICO de acesso a tudo que vive em PASTA_APPDATA (definida em _CONFIGURA_).
Nenhum módulo deve montar caminhos de AppData na mão — todos consultam esta classe.

Uso:
    from _APPDATA_ import appdata
    appdata.inicializar()
    print(appdata.pasta_raiz)
"""

import os
import json
import datetime


# Import tardio para evitar dependência circular na inicialização
def _log():
    from _LOGS_ import log as _l
    return _l


class GerenciadorAppData:
    """Singleton — instância única durante toda a vida do processo."""
    _inst: "GerenciadorAppData | None" = None

    @classmethod
    def instancia(cls) -> "GerenciadorAppData":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        from _CONFIGURA_ import PASTA_APPDATA
        self._raiz = PASTA_APPDATA
        self._inicializado = False

    # ── Inicialização ────────────────────────────────────────────────────────

    def inicializar(self):
        """
        Garante toda a estrutura de pastas e arquivos padrão.
        Deve ser chamado UMA vez no startup, antes de qualquer acesso.
        """
        if self._inicializado:
            return

        os.makedirs(self._raiz,          exist_ok=True)
        os.makedirs(self.pasta_logs,     exist_ok=True)
        os.makedirs(self.pasta_config,   exist_ok=True)
        os.makedirs(self.pasta_cache,    exist_ok=True)
        os.makedirs(self.pasta_projetos, exist_ok=True)

        self._garantir_config_padrao()
        self._inicializado = True
        _log().ok("AppData", "inicializar", f"pasta_raiz={self._raiz}")

    # ── Caminhos canônicos ────────────────────────────────────────────────────
    # Sempre use estas properties — nunca monte caminhos na mão fora daqui

    @property
    def pasta_raiz(self) -> str:
        return self._raiz

    @property
    def pasta_logs(self) -> str:
        return os.path.join(self._raiz, "logs")

    @property
    def pasta_config(self) -> str:
        return os.path.join(self._raiz, "config")

    @property
    def pasta_cache(self) -> str:
        return os.path.join(self._raiz, "cache")

    @property
    def pasta_projetos(self) -> str:
        return os.path.join(self._raiz, "projetos")

    @property
    def arq_config(self) -> str:
        return os.path.join(self.pasta_config, "config.json")

    @property
    def arq_sessao(self) -> str:
        return os.path.join(self.pasta_config, "sessao.json")

    # ── Config ────────────────────────────────────────────────────────────────

    def ler_config(self) -> dict:
        """Lê config.json. Retorna {} em caso de falha."""
        try:
            with open(self.arq_config, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _log().aviso("AppData", "ler_config", f"falha ao ler config.json: {e}")
            return {}

    def salvar_config(self, dados: dict):
        """Salva dict no config.json."""
        try:
            with open(self.arq_config, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            _log().erro("AppData", "salvar_config", f"falha ao salvar config.json: {e}")

    def restaurar_padrao(self):
        """Apaga config.json e recria com valores padrão de fábrica."""
        if os.path.exists(self.arq_config):
            os.remove(self.arq_config)
        self._garantir_config_padrao()
        _log().ok("AppData", "restaurar_padrao", "config restaurado ao padrão")

    # ── Sessão (geometria, estado da janela) ──────────────────────────────────

    def ler_sessao(self) -> dict:
        """Lê sessao.json. Retorna {} em caso de falha."""
        try:
            with open(self.arq_sessao, "r", encoding="utf-8") as f:
                dados = json.load(f)
            _log().ok("AppData", "ler_sessao", f"sessão restaurada: {list(dados.keys())}")
            return dados
        except Exception:
            _log().info("AppData", "ler_sessao", "sessao.json ausente — usando padrão")
            return {}

    def salvar_sessao(self, dados: dict):
        """Persiste dados de sessão em sessao.json."""
        try:
            with open(self.arq_sessao, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            _log().ok("AppData", "salvar_sessao", f"sessão salva: {list(dados.keys())}")
        except Exception as e:
            _log().erro("AppData", "salvar_sessao", f"falha ao salvar sessao.json: {e}")

    # ── Internos ──────────────────────────────────────────────────────────────

    def _garantir_config_padrao(self):
        if not os.path.exists(self.arq_config):
            from _CONFIGURA_ import VERSAO_APP, TEMA_QT
            padrao = {
                "tema":    TEMA_QT,
                "versao":  VERSAO_APP,
                "criado":  datetime.datetime.now().isoformat(),
            }
            self.salvar_config(padrao)
