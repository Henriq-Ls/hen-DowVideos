# _LOGS_/__init__.py
"""
Ponto de entrada público do módulo de logging.

Uso em qualquer script do projeto:
    from _LOGS_ import log

    log.ok   ("modulo", "funcao", "operação concluída")
    log.info ("modulo", "funcao", "mensagem informativa")
    log.aviso("modulo", "funcao", "atenção aqui")
    log.erro ("modulo", "funcao", "algo deu errado")
    log.crash("modulo", "funcao", "traceback completo")
    log.fault("dump bruto do faulthandler")
"""

from _LOGS_.log import log

__all__ = ["log"]
