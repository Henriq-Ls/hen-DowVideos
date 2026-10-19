"""Histórico local de links, downloads, transcrições e conteúdo gerado."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from _CONFIGURA_ import HISTORICO_ARQUIVO, HISTORICO_LIMITE_PADRAO
from _APPDATA_ import appdata


class HistoricoMidia:
    def __init__(self):
        appdata.inicializar()
        self.caminho = Path(appdata.pasta_raiz) / HISTORICO_ARQUIVO
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._criar_tabela()

    def _conectar(self):
        conexao = sqlite3.connect(self.caminho, timeout=10)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _criar_tabela(self):
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS midias (
                    url TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL DEFAULT '',
                    tipo TEXT NOT NULL DEFAULT '',
                    formato TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'concluido',
                    caminho TEXT NOT NULL DEFAULT '',
                    caminho_transcricao TEXT NOT NULL DEFAULT '',
                    transcricao TEXT NOT NULL DEFAULT '',
                    conteudo_json TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            colunas = {
                str(linha["name"])
                for linha in conexao.execute("PRAGMA table_info(midias)")
            }
            if "caminho_transcricao" not in colunas:
                conexao.execute(
                    "ALTER TABLE midias ADD COLUMN "
                    "caminho_transcricao TEXT NOT NULL DEFAULT ''"
                )

    def existe_url(self, url: str) -> bool:
        endereco = self.normalizar_url(url)
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT 1 FROM midias WHERE url = ? LIMIT 1",
                (endereco,),
            ).fetchone()
        return linha is not None

    @staticmethod
    def normalizar_url(url: str) -> str:
        endereco = (url or "").strip()
        partes = urlparse(endereco)
        host = partes.netloc.lower().removeprefix("www.")
        caminho = partes.path.rstrip("/")
        if host == "youtu.be" and caminho:
            video_id = caminho.lstrip("/").split("/")[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        if host.endswith("youtube.com"):
            parametros = parse_qs(partes.query)
            video_id = ""
            if caminho == "/watch":
                video_id = (parametros.get("v") or [""])[0]
            elif caminho.startswith(("/shorts/", "/embed/", "/live/")):
                video_id = caminho.split("/")[2]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        return endereco

    def salvar(
        self,
        url: str,
        titulo: str = "",
        tipo: str = "",
        formato: str = "",
        status: str = "concluido",
        caminho: str = "",
        caminho_transcricao: str = "",
        transcricao: str = "",
        conteudo: dict | list | None = None,
    ):
        endereco = self.normalizar_url(url)
        if not endereco:
            raise ValueError("Não é possível registrar uma mídia sem link.")

        agora = datetime.now().astimezone().isoformat(timespec="seconds")
        conteudo_json = (
            json.dumps(conteudo, ensure_ascii=False)
            if conteudo is not None
            else ""
        )
        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO midias (
                    url, titulo, tipo, formato, status, caminho,
                    caminho_transcricao, transcricao, conteudo_json,
                    criado_em, atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    titulo = CASE WHEN excluded.titulo = ''
                        THEN midias.titulo ELSE excluded.titulo END,
                    tipo = CASE WHEN excluded.tipo = ''
                        THEN midias.tipo ELSE excluded.tipo END,
                    formato = CASE WHEN excluded.formato = ''
                        THEN midias.formato ELSE excluded.formato END,
                    status = excluded.status,
                    caminho = CASE WHEN excluded.caminho = ''
                        THEN midias.caminho ELSE excluded.caminho END,
                    caminho_transcricao = CASE
                        WHEN excluded.caminho_transcricao = ''
                        THEN midias.caminho_transcricao
                        ELSE excluded.caminho_transcricao END,
                    transcricao = CASE WHEN excluded.transcricao = ''
                        THEN midias.transcricao ELSE excluded.transcricao END,
                    conteudo_json = CASE WHEN excluded.conteudo_json = ''
                        THEN midias.conteudo_json ELSE excluded.conteudo_json END,
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    endereco,
                    titulo or "",
                    tipo or "",
                    formato or "",
                    status or "concluido",
                    caminho or "",
                    caminho_transcricao or "",
                    transcricao or "",
                    conteudo_json,
                    agora,
                    agora,
                ),
            )

    def listar(self, limite: int = HISTORICO_LIMITE_PADRAO) -> list[dict]:
        quantidade = max(1, min(int(limite), 500))
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT url, titulo, tipo, formato, status, caminho,
                       atualizado_em
                FROM midias
                ORDER BY atualizado_em DESC
                LIMIT ?
                """,
                (quantidade,),
            ).fetchall()
        return [dict(linha) for linha in linhas]

    def obter(self, url: str) -> dict | None:
        endereco = self.normalizar_url(url)
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM midias WHERE url = ? LIMIT 1",
                (endereco,),
            ).fetchone()
        if linha is None:
            return None
        registro = dict(linha)
        try:
            registro["conteudo"] = (
                json.loads(registro.get("conteudo_json") or "")
                if registro.get("conteudo_json")
                else None
            )
        except json.JSONDecodeError:
            registro["conteudo"] = None
        return registro
