"""Operações de metadados, download de mídia e transcrição."""

from _CONFIGURA_ import (
    FFMPEG_EXECUTABLES,
    FFMPEG_RELATIVE_DIRS,
    FFMPEG_SEARCH_DIRS,
    BUSCA_MAX_RESULTADOS,
    FORMATOS_AUDIO_DISPONIVEIS,
    OLLAMA_TAMANHO_CONTEXTO,
    OLLAMA_TAMANHO_MAX_TRANSCRICAO,
    OLLAMA_TIMEOUT_SEGUNDOS,
    MODELO_OLLAMA_CONTEUDO,
    OLLAMA_API_URL,
    FORMATO_AUDIO_PADRAO,
    FORMATO_VIDEO_PADRAO,
    FORMATOS_VIDEO_DISPONIVEIS,
    IDIOMA_TRANSCRICAO,
    IDIOMAS_LEGENDA,
    MODELO_WHISPER,
    QUALIDADE_AUDIO_KBPS,
)
from _LOGS_ import log
from _APPDATA_ import appdata

import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Callable
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AtualizacaoProgresso = Callable[[int, str], None]


class ServicoMidia:
    """Implementa as operações de mídia usadas pela interface."""

    @staticmethod
    def _importar_yt_dlp():
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError(
                "A dependência yt-dlp não está instalada. "
                "Instale as dependências listadas em requirements.txt."
            ) from exc
        return yt_dlp

    @staticmethod
    def _validar_url(url: str) -> str:
        endereco = (url or "").strip()
        if not endereco.startswith(("https://", "http://")):
            raise ValueError("Informe um endereço de vídeo iniciado por http:// ou https://.")
        return endereco

    @staticmethod
    def _localizar_ffmpeg() -> Path:
        tentativas = []
        for raiz in FFMPEG_SEARCH_DIRS:
            for diretorio in FFMPEG_RELATIVE_DIRS:
                pasta = Path(raiz) / diretorio if diretorio else Path(raiz)
                for executavel in FFMPEG_EXECUTABLES:
                    caminho = pasta / executavel
                    tentativas.append(str(caminho))
                    if caminho.is_file():
                        return caminho

        executavel_sistema = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if executavel_sistema:
            return Path(executavel_sistema)
        tentativas.append("PATH do sistema: ffmpeg")

        raise RuntimeError(
            "FFmpeg não foi encontrado. Caminhos verificados: "
            + "; ".join(tentativas)
        )

    @staticmethod
    def _notificar(
        callback: AtualizacaoProgresso | None,
        percentual: int,
        mensagem: str,
    ) -> None:
        if callback is not None:
            callback(percentual, mensagem)

    @staticmethod
    def _hook_progresso(
        callback: AtualizacaoProgresso | None,
    ) -> Callable[[dict], None]:
        def atualizar(dados: dict) -> None:
            situacao = dados.get("status")
            if situacao == "downloading":
                percentual = -1
                texto_percentual = str(dados.get("_percent_str", "")).replace("%", "").strip()
                try:
                    percentual = max(0, min(100, round(float(texto_percentual))))
                except (TypeError, ValueError):
                    total = dados.get("total_bytes") or dados.get("total_bytes_estimate")
                    baixado = dados.get("downloaded_bytes")
                    if total and baixado is not None:
                        percentual = max(0, min(100, round(baixado * 100 / total)))
                mensagem = "Baixando mídia"
                if percentual >= 0:
                    mensagem = f"Baixando mídia — {percentual}%"
                ServicoMidia._notificar(callback, percentual, mensagem)
            elif situacao == "finished":
                ServicoMidia._notificar(callback, 100, "Finalizando arquivo…")

        return atualizar

    @staticmethod
    def _formatar_duracao(duracao: int | float | None) -> str:
        if not duracao:
            return "Não informada"
        segundos = int(duracao)
        horas, restante = divmod(segundos, 3600)
        minutos, segundos = divmod(restante, 60)
        if horas:
            return f"{horas}:{minutos:02d}:{segundos:02d}"
        return f"{minutos}:{segundos:02d}"

    def obter_informacoes(self, url: str) -> dict:
        endereco = self._validar_url(url)
        yt_dlp = self._importar_yt_dlp()
        opcoes = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(endereco, download=False)

        if not info:
            raise RuntimeError("Não foi possível obter informações desse endereço.")
        if info.get("_type") == "playlist":
            raise RuntimeError("Por enquanto, informe o link de um vídeo individual.")

        altura = info.get("height")
        resolucao = f"{altura}p" if altura else "Não informada"
        fps = info.get("fps")
        if fps:
            resolucao = f"{resolucao} · {fps} fps"
        alturas_disponiveis = sorted({
            int(formato["height"])
            for formato in (info.get("formats") or [])
            if formato.get("height")
            and formato.get("vcodec") not in (None, "none")
        }, reverse=True)

        return {
            "id": str(info.get("id") or ""),
            "title": str(info.get("title") or "Vídeo sem título"),
            "uploader": str(info.get("uploader") or info.get("channel") or "Canal não informado"),
            "duration": self._formatar_duracao(info.get("duration")),
            "resolution": resolucao,
            "format": str(info.get("ext") or "Não informado").upper(),
            "available_heights": alturas_disponiveis,
        }

    def pesquisar_videos(
        self,
        consulta: str,
        max_resultados: int = 10,
        visualizacoes_minimas: int = 0,
        duracao_minima_segundos: int = 0,
        duracao_maxima_segundos: int = 0,
        dias_atras: int = 0,
    ) -> list[dict]:
        termo = (consulta or "").strip()
        if not termo:
            raise ValueError("Digite um tema ou palavra-chave para pesquisar.")
        if not 1 <= int(max_resultados) <= BUSCA_MAX_RESULTADOS:
            raise ValueError("A quantidade de resultados deve ficar entre 1 e 50.")
        if visualizacoes_minimas < 0 or duracao_minima_segundos < 0:
            raise ValueError("Os filtros numéricos não podem ser negativos.")
        if duracao_maxima_segundos and duracao_maxima_segundos < duracao_minima_segundos:
            raise ValueError("A duração máxima precisa ser maior que a mínima.")

        yt_dlp = self._importar_yt_dlp()
        opcoes = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            dados = ydl.extract_info(
                f"ytsearch{int(max_resultados)}:{termo}",
                download=False,
            )

        if not dados:
            return []

        data_limite = (
            (date.today() - timedelta(days=int(dias_atras))).strftime("%Y%m%d")
            if dias_atras > 0
            else ""
        )
        encontrados = []
        for entrada in dados.get("entries") or []:
            if not entrada or not entrada.get("id"):
                continue
            visualizacoes = int(entrada.get("view_count") or 0)
            duracao = int(entrada.get("duration") or 0)
            data_envio = str(entrada.get("upload_date") or "")
            if visualizacoes < visualizacoes_minimas:
                continue
            if duracao < duracao_minima_segundos:
                continue
            if duracao_maxima_segundos and duracao > duracao_maxima_segundos:
                continue
            if data_limite and data_envio and data_envio < data_limite:
                continue

            titulo = str(entrada.get("title") or "Vídeo sem título")
            encontrados.append({
                "id": str(entrada["id"]),
                "title": titulo,
                "url": str(
                    entrada.get("webpage_url")
                    or f"https://www.youtube.com/watch?v={entrada['id']}"
                ),
                "uploader": str(
                    entrada.get("uploader") or entrada.get("channel") or ""
                ),
                "views": visualizacoes,
                "duration_seconds": duracao,
                "duration": self._formatar_duracao(duracao),
                "upload_date": data_envio,
            })
        return encontrados

    def baixar_midia(
        self,
        url: str,
        destino: str | Path,
        tipo: str,
        progresso: AtualizacaoProgresso | None = None,
        resolucao_max: int | None = None,
        formato_video: str = FORMATO_VIDEO_PADRAO,
        formato_audio: str = FORMATO_AUDIO_PADRAO,
    ) -> dict:
        endereco = self._validar_url(url)
        if tipo not in ("video", "audio"):
            raise ValueError("Escolha vídeo ou áudio para o download.")
        if tipo == "video" and formato_video not in FORMATOS_VIDEO_DISPONIVEIS:
            raise ValueError("Formato de vídeo não disponível.")
        if tipo == "audio" and formato_audio not in FORMATOS_AUDIO_DISPONIVEIS:
            raise ValueError("Formato de áudio não disponível.")
        if resolucao_max is not None and int(resolucao_max) < 1:
            raise ValueError("A resolução máxima precisa ser positiva.")

        yt_dlp = self._importar_yt_dlp()
        ffmpeg = self._localizar_ffmpeg()
        pasta_saida = Path(destino).expanduser()
        pasta_saida.mkdir(parents=True, exist_ok=True)
        opcoes = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "outtmpl": str(pasta_saida / "%(title).180B [%(id)s].%(ext)s"),
            "progress_hooks": [self._hook_progresso(progresso)],
            "ffmpeg_location": str(ffmpeg),
        }

        if tipo == "video":
            seletor = "bestvideo+bestaudio/best"
            if resolucao_max is not None:
                altura_maxima = int(resolucao_max)
                seletor = (
                    f"bestvideo[height<={altura_maxima}]+bestaudio/"
                    f"best[height<={altura_maxima}]/best"
                )
            opcoes.update({
                "format": seletor,
            })
            if formato_video == "avi":
                opcoes["merge_output_format"] = "mp4"
                opcoes["postprocessors"] = [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "avi",
                }]
            else:
                opcoes["merge_output_format"] = formato_video
        else:
            opcoes.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": formato_audio,
                    "preferredquality": QUALIDADE_AUDIO_KBPS,
                }],
            })

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            resultado = ydl.download([endereco])
        if resultado:
            raise RuntimeError("O yt-dlp não conseguiu concluir o download.")

        log.ok("ServicoMidia", "baixar_midia", f"download concluído em {pasta_saida}")
        return {
            "folder": str(pasta_saida),
            "type": tipo,
            "format": formato_video if tipo == "video" else formato_audio,
            "resolution": resolucao_max or "Melhor disponível",
        }

    @staticmethod
    def _ler_legenda_vtt(caminho: Path) -> str:
        conteudo = caminho.read_text(encoding="utf-8-sig", errors="replace")
        linhas = []
        anterior = None

        for linha in conteudo.splitlines():
            texto = linha.strip()
            if (
                not texto
                or texto.startswith(("WEBVTT", "NOTE", "STYLE", "REGION"))
                or "-->" in texto
                or re.fullmatch(r"\d+", texto)
            ):
                continue

            texto = re.sub(r"<[^>]*>", "", texto)
            texto = html.unescape(texto)
            texto = re.sub(r"\s+", " ", texto).strip()
            if texto and texto != anterior:
                linhas.append(texto)
                anterior = texto

        return " ".join(linhas).strip()

    @staticmethod
    def _nome_seguro(texto: str, limite: int = 90) -> str:
        nome = re.sub(r"[^\w.-]+", "_", texto, flags=re.UNICODE).strip("._")
        nome = nome[:limite].rstrip("._")
        return nome or "video"

    def _obter_legenda(self, url: str, pasta_temporaria: Path) -> str:
        yt_dlp = self._importar_yt_dlp()
        opcoes = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(IDIOMAS_LEGENDA),
            "subtitlesformat": "vtt/best",
            "outtmpl": str(pasta_temporaria / "%(title).160B [%(id)s].%(ext)s"),
        }

        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                ydl.download([url])
        except Exception as exc:
            log.aviso("ServicoMidia", "_obter_legenda", f"legenda indisponível: {exc}")
            return ""

        arquivos = list(pasta_temporaria.rglob("*.vtt"))
        arquivos.extend(pasta_temporaria.rglob("*.srt"))
        if not arquivos:
            return ""

        def prioridade(caminho: Path) -> int:
            nome = caminho.name.lower()
            for indice, idioma in enumerate(IDIOMAS_LEGENDA):
                if idioma.lower() in nome:
                    return indice
            return len(IDIOMAS_LEGENDA)

        for arquivo in sorted(arquivos, key=prioridade):
            texto = self._ler_legenda_vtt(arquivo)
            if texto:
                return texto
        return ""

    def _transcrever_audio(
        self,
        url: str,
        pasta_temporaria: Path,
        progresso: AtualizacaoProgresso | None,
    ) -> str:
        yt_dlp = self._importar_yt_dlp()
        ffmpeg = self._localizar_ffmpeg()
        pasta_ffmpeg = str(ffmpeg.parent)
        caminhos_path = os.environ.get("PATH", "").split(os.pathsep)
        if pasta_ffmpeg not in caminhos_path:
            os.environ["PATH"] = os.pathsep.join(
                [pasta_ffmpeg, *caminhos_path]
            )
        self._notificar(progresso, -1, "Baixando áudio para transcrição…")
        opcoes = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "outtmpl": str(pasta_temporaria / "audio.%(ext)s"),
            "progress_hooks": [self._hook_progresso(progresso)],
            "ffmpeg_location": str(ffmpeg),
        }

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            resultado = ydl.download([url])
        if resultado:
            raise RuntimeError("Não foi possível baixar o áudio para transcrição.")

        candidatos = [
            arquivo for arquivo in pasta_temporaria.glob("audio.*")
            if arquivo.is_file() and not arquivo.name.endswith((".part", ".json"))
        ]
        if not candidatos:
            raise RuntimeError("O áudio foi baixado, mas o arquivo não foi localizado.")

        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError(
                "A transcrição automática precisa de openai-whisper. "
                "Instale as dependências listadas em requirements.txt."
            ) from exc

        appdata.inicializar()
        self._notificar(progresso, -1, "Carregando o modelo de transcrição…")
        modelo = whisper.load_model(MODELO_WHISPER, download_root=appdata.pasta_cache)
        self._notificar(progresso, -1, "Transcrevendo áudio…")
        resultado_transcricao = modelo.transcribe(
            str(candidatos[0]),
            language=IDIOMA_TRANSCRICAO,
            fp16=False,
        )
        return str(resultado_transcricao.get("text") or "").strip()

    def criar_transcricao(
        self,
        url: str,
        destino: str | Path,
        progresso: AtualizacaoProgresso | None = None,
    ) -> dict:
        endereco = self._validar_url(url)
        metadados = self.obter_informacoes(endereco)
        pasta_saida = Path(destino).expanduser()
        pasta_saida.mkdir(parents=True, exist_ok=True)
        self._notificar(progresso, -1, "Procurando legendas disponíveis…")

        with tempfile.TemporaryDirectory(prefix="hen_dowvideos_") as temporario:
            pasta_temporaria = Path(temporario)
            transcricao = self._obter_legenda(endereco, pasta_temporaria)
            origem = "legenda"
            if not transcricao:
                transcricao = self._transcrever_audio(
                    endereco,
                    pasta_temporaria,
                    progresso,
                )
                origem = "Whisper"

        if not transcricao:
            raise RuntimeError("Não foi encontrada legenda nem fala reconhecível para transcrever.")

        nome = self._nome_seguro(metadados["title"])
        identificador = self._nome_seguro(metadados["id"], limite=40)
        arquivo = pasta_saida / f"{nome}-{identificador}-transcricao.txt"
        arquivo.write_text(transcricao + "\n", encoding="utf-8")
        self._notificar(progresso, 100, "Transcrição pronta.")
        log.ok("ServicoMidia", "criar_transcricao", f"transcrição salva em {arquivo}")
        return {
            "text": transcricao,
            "path": str(arquivo),
            "source": origem,
            "title": metadados["title"],
        }

    @staticmethod
    def gerar_conteudo_estruturado(
        texto: str,
        titulo: str = "",
        url: str = "",
    ) -> dict:
        """Gera conteúdo editorial estruturado usando o Ollama local."""
        transcricao = (texto or "").strip()
        if not transcricao:
            raise ValueError("É necessária uma transcrição para gerar o conteúdo.")
        if len(transcricao) > OLLAMA_TAMANHO_MAX_TRANSCRICAO:
            raise ValueError(
                "A transcrição é longa demais para uma única geração local. "
                "Use uma transcrição menor ou divida o conteúdo."
            )

        campos = {
            "seo_title": "string",
            "main_title": "string",
            "meta_description": "string",
            "introduction": "string",
            "context_title": "string",
            "context_paragraph": "string",
            "details_title": "string",
            "details_paragraph": "string",
            "summary_title": "string",
            "summary_paragraph": "string",
            "list_title": "string",
            "key_points": ["string"],
            "faq_title": "string",
            "faq": [{"question": "string", "answer": "string"}],
            "video_section_title": "string",
            "image_alt": "string",
            "keywords": ["string"],
        }
        esquema = {
            "type": "object",
            "properties": {
                "seo_title": {"type": "string"},
                "main_title": {"type": "string"},
                "meta_description": {"type": "string"},
                "introduction": {"type": "string"},
                "context_title": {"type": "string"},
                "context_paragraph": {"type": "string"},
                "details_title": {"type": "string"},
                "details_paragraph": {"type": "string"},
                "summary_title": {"type": "string"},
                "summary_paragraph": {"type": "string"},
                "list_title": {"type": "string"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "faq_title": {"type": "string"},
                "faq": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"},
                        },
                        "required": ["question", "answer"],
                        "additionalProperties": False,
                    },
                },
                "video_section_title": {"type": "string"},
                "image_alt": {"type": "string"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": list(campos),
            "additionalProperties": False,
        }
        prompt = (
            "Crie conteúdo editorial estruturado a partir da transcrição abaixo. "
            "Responda somente com um objeto JSON válido, sem markdown ou texto "
            "antes/depois. Use exatamente estas chaves e tipos; o formato é "
            "validado pela aplicação:\n"
            f"{json.dumps(campos, ensure_ascii=False)}\n"
            "Escreva em português brasileiro. Seja claro, informativo e adequado "
            "para SEO. Não invente fatos, nomes, datas, números ou conclusões que "
            "não estejam apoiados pela transcrição; se faltarem informações, "
            "mantenha o texto mais curto e fiel à fonte. Não repita o mesmo "
            "conteúdo entre seções. Gere de 5 a 8 pontos em key_points, de 3 a 5 "
            "perguntas e respostas em faq, de 5 a 10 palavras-chave e mantenha "
            "seo_title com no máximo 60 caracteres.\n\n"
            f"Título original: {titulo or 'Não informado'}\n"
            f"Link de origem: {url or 'Não informado'}\n\n"
            "Transcrição:\n"
            f"{transcricao}"
        )
        payload = json.dumps(
            {
                "model": MODELO_OLLAMA_CONTEUDO,
                "prompt": prompt,
                "stream": False,
                "format": esquema,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": OLLAMA_TAMANHO_CONTEXTO,
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        requisicao = Request(
            OLLAMA_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(
                requisicao,
                timeout=OLLAMA_TIMEOUT_SEGUNDOS,
            ) as resposta_http:
                resposta_api = json.loads(resposta_http.read().decode("utf-8"))
        except HTTPError as exc:
            detalhe = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                "O Ollama recusou a geração. Confirme se o modelo "
                f"'{MODELO_OLLAMA_CONTEUDO}' está instalado. {detalhe}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                "Não foi possível conectar ao Ollama local. Abra o Ollama e "
                f"confirme se o modelo '{MODELO_OLLAMA_CONTEUDO}' está instalado."
            ) from exc
        except (TimeoutError, OSError) as exc:
            raise RuntimeError(
                "A geração local não respondeu a tempo. Verifique se o Ollama "
                "está funcionando."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("O Ollama retornou uma resposta inválida.") from exc

        if not isinstance(resposta_api, dict):
            raise RuntimeError("O Ollama retornou uma resposta inválida.")
        conteudo_bruto = str(resposta_api.get("response") or "").strip()
        conteudo_bruto = re.sub(
            r"^\s*```(?:json)?\s*|\s*```\s*$",
            "",
            conteudo_bruto,
            flags=re.IGNORECASE,
        ).strip()
        try:
            conteudo = json.loads(conteudo_bruto)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "O Ollama não retornou o conteúdo no formato JSON esperado."
            ) from exc

        if not isinstance(conteudo, dict):
            raise RuntimeError("O conteúdo gerado não é um objeto JSON.")
        faltando = [chave for chave in campos if chave not in conteudo]
        if faltando:
            raise RuntimeError(
                "O conteúdo gerado veio incompleto. Campos ausentes: "
                + ", ".join(faltando)
            )
        for chave in ("key_points", "keywords"):
            if not isinstance(conteudo[chave], list) or not all(
                isinstance(item, str) for item in conteudo[chave]
            ):
                raise RuntimeError(
                    f"O campo '{chave}' não veio como uma lista de textos."
                )
        if not isinstance(conteudo["faq"], list) or not all(
            isinstance(item, dict)
            and isinstance(item.get("question"), str)
            and isinstance(item.get("answer"), str)
            for item in conteudo["faq"]
        ):
            raise RuntimeError("O campo 'faq' não veio no formato esperado.")

        return conteudo
