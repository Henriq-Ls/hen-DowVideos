# _APPDATA_/__init__.py
"""
Ponto de entrada público do módulo AppData.

Uso:
    from _APPDATA_ import appdata

    appdata.inicializar()            # chamar UMA vez no main.py
    print(appdata.pasta_raiz)        # caminho da pasta do usuário
    cfg = appdata.ler_config()       # lê config.json
    appdata.salvar_config(cfg)       # salva config.json
"""

from _APPDATA_.gerenciador import GerenciadorAppData

appdata: GerenciadorAppData = GerenciadorAppData.instancia()

__all__ = ["GerenciadorAppData", "appdata"]
