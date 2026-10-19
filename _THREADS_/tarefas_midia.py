"""Tarefas de mídia em segundo plano com sinais para a interface."""

from _CONFIGURA_ import (
    FORMATO_AUDIO_PADRAO,
    FORMATO_VIDEO_PADRAO,
)
from _LOGS_ import log
from _THREADS_.thread_segura import ThreadSegura
from _MIDIA_ import HistoricoMidia, ServicoMidia

from PySide6.QtCore import Signal
import uuid


class TarefaMidia(ThreadSegura):
    progresso = Signal(int, str)
    resultado = Signal(object)

    def __init__(
        self,
        operacao: str,
        url: str,
        destino: str = "",
        tipo: str = "video",
        transcrever_apos_download: bool = False,
        baixar_video: bool = False,
        baixar_audio: bool = False,
        criar_srt: bool = False,
        urls: list[str] | None = None,
        resolucao_max: int | None = None,
        formato_video: str = FORMATO_VIDEO_PADRAO,
        formato_audio: str = FORMATO_AUDIO_PADRAO,
        gerar_conteudo_apos_transcricao: bool = False,
        texto_transcricao: str = "",
        titulo_transcricao: str = "",
        consulta: str = "",
        max_resultados: int = 10,
        visualizacoes_minimas: int = 0,
        duracao_minima_segundos: int = 0,
        duracao_maxima_segundos: int = 0,
        dias_atras: int = 0,
        parent=None,
        organizar_por_video: bool = True,
    ):
        super().__init__(nome=f"midia_{uuid.uuid4().hex}", parent=parent)
        self.operacao = operacao
        self.url = url
        self.urls = urls or ([url] if url else [])
        self.destino = destino
        self.tipo = tipo
        self.transcrever_apos_download = transcrever_apos_download
        self.baixar_video = baixar_video
        self.baixar_audio = baixar_audio
        self.criar_srt = criar_srt
        self.resolucao_max = resolucao_max
        self.formato_video = formato_video
        self.formato_audio = formato_audio
        self.gerar_conteudo_apos_transcricao = gerar_conteudo_apos_transcricao
        self.texto_transcricao = texto_transcricao
        self.titulo_transcricao = titulo_transcricao
        self.consulta = consulta
        self.max_resultados = max_resultados
        self.visualizacoes_minimas = visualizacoes_minimas
        self.duracao_minima_segundos = duracao_minima_segundos
        self.duracao_maxima_segundos = duracao_maxima_segundos
        self.dias_atras = dias_atras
        self.organizar_por_video = organizar_por_video

    def _progresso_lote(self, indice: int, total: int):
        def atualizar(percentual: int, mensagem: str):
            if percentual < 0:
                self.progresso.emit(-1, f"Link {indice}/{total}: {mensagem}")
                return
            geral = round(((indice - 1) * 100 + percentual) / total)
            self.progresso.emit(geral, f"Link {indice}/{total}: {mensagem}")
        return atualizar

    def _salvar_historico(self, url: str, dados: dict) -> str:
        resultado = dados if isinstance(dados, dict) else {}
        pacote_download = resultado.get("dados") or {}
        if not pacote_download and "folder" in resultado:
            pacote_download = resultado
        transcricao = resultado.get("transcricao")
        if not transcricao and isinstance(pacote_download, dict):
            if "text" in pacote_download:
                transcricao = pacote_download
        if not transcricao and "text" in resultado:
            transcricao = resultado
        transcricao = transcricao if isinstance(transcricao, dict) else {}
        pacote_download = (
            pacote_download if isinstance(pacote_download, dict) else {}
        )
        tipo = (
            self.tipo
            if self.operacao in ("download", "processamento")
            else self.operacao
        )
        if pacote_download.get("format"):
            formato = pacote_download["format"]
        elif self.operacao == "processamento":
            formato = (
                self.formato_video
                if self.baixar_video
                else self.formato_audio if self.baixar_audio else ""
            )
        else:
            formato = (
                self.formato_video if self.tipo == "video" else self.formato_audio
            )
        try:
            HistoricoMidia().salvar(
                url=url,
                titulo=str(
                    transcricao.get("title")
                    or resultado.get("title")
                    or self.titulo_transcricao
                    or ""
                ),
                tipo=tipo,
                formato=str(formato or ""),
                status=(
                    "parcial"
                    if (
                        resultado.get("erros")
                        or resultado.get("conteudo_erro")
                        or resultado.get("transcricao_erro")
                    )
                    else "concluido"
                ),
                caminho=str(
                    pacote_download.get("folder")
                    or transcricao.get("path")
                    or transcricao.get("srt_path")
                    or ""
                ),
                caminho_transcricao=str(transcricao.get("path") or ""),
                transcricao=str(transcricao.get("text") or ""),
                conteudo=resultado.get("conteudo"),
            )
            return ""
        except Exception as exc:
            log.erro("TarefaMidia", "_salvar_historico", str(exc))
            return str(exc)

    def _destino_para_url(
        self,
        servico: ServicoMidia,
        url: str,
        precisa_arquivo: bool = True,
    ) -> str:
        if self.organizar_por_video and precisa_arquivo:
            return servico.preparar_pasta_video(url, self.destino)
        return self.destino

    def _executar_lote(self, servico: ServicoMidia) -> dict:
        resultados = []
        total = len(self.urls)

        for indice, url in enumerate(self.urls, start=1):
            progresso = self._progresso_lote(indice, total)
            item = {"url": url, "ok": False}
            try:
                precisa_arquivo = (
                    self.operacao in ("download", "transcricao")
                    or self.criar_srt
                    or (
                        self.operacao == "processamento"
                        and (
                            self.baixar_video
                            or self.baixar_audio
                            or self.transcrever_apos_download
                            or self.gerar_conteudo_apos_transcricao
                            or self.criar_srt
                        )
                    )
                    or (
                        self.operacao == "conteudo"
                        and not self.texto_transcricao.strip()
                    )
                )
                destino_item = self._destino_para_url(
                    servico,
                    url,
                    precisa_arquivo,
                )
                if self.operacao == "download":
                    item["dados"] = servico.baixar_midia(
                        url,
                        destino_item,
                        self.tipo,
                        progresso,
                        self.resolucao_max,
                        self.formato_video,
                        self.formato_audio,
                    )
                    item["ok"] = True
                    if (
                        self.transcrever_apos_download
                        or self.gerar_conteudo_apos_transcricao
                        or self.criar_srt
                    ):
                        try:
                            item["transcricao"] = servico.criar_transcricao(
                                url,
                                destino_item,
                                progresso,
                                criar_srt=self.criar_srt,
                                salvar_txt=(
                                    self.transcrever_apos_download
                                    or self.gerar_conteudo_apos_transcricao
                                ),
                            )
                        except Exception as exc:
                            item["transcricao_erro"] = str(exc)
                    if (
                        self.gerar_conteudo_apos_transcricao
                        and item.get("transcricao")
                    ):
                        try:
                            transcricao = item["transcricao"]
                            item["conteudo"] = servico.gerar_conteudo_estruturado(
                                transcricao["text"],
                                transcricao.get("title", ""),
                                url,
                            )
                        except Exception as exc:
                            item["conteudo_erro"] = str(exc)
                elif self.operacao == "processamento":
                    item["downloads"] = []
                    if self.baixar_video:
                        self.progresso.emit(-1, "Baixando vídeo…")
                        try:
                            item["downloads"].append(
                                servico.baixar_midia(
                                    url,
                                    destino_item,
                                    "video",
                                    progresso,
                                    self.resolucao_max,
                                    self.formato_video,
                                    self.formato_audio,
                                )
                            )
                        except Exception as exc:
                            item.setdefault("erros", []).append(
                                f"Vídeo: {exc}"
                            )
                    if self.baixar_audio:
                        self.progresso.emit(-1, "Baixando áudio…")
                        try:
                            item["downloads"].append(
                                servico.baixar_midia(
                                    url,
                                    destino_item,
                                    "audio",
                                    progresso,
                                    None,
                                    self.formato_video,
                                    self.formato_audio,
                                )
                            )
                        except Exception as exc:
                            item.setdefault("erros", []).append(
                                f"Áudio: {exc}"
                            )

                    if (
                        self.transcrever_apos_download
                        or self.gerar_conteudo_apos_transcricao
                        or self.criar_srt
                    ):
                        try:
                            item["transcricao"] = servico.criar_transcricao(
                                url,
                                destino_item,
                                progresso,
                                criar_srt=self.criar_srt,
                                salvar_txt=(
                                    self.transcrever_apos_download
                                    or self.gerar_conteudo_apos_transcricao
                                ),
                            )
                        except Exception as exc:
                            item["transcricao_erro"] = str(exc)
                    if (
                        self.gerar_conteudo_apos_transcricao
                        and item.get("transcricao")
                    ):
                        try:
                            transcricao = item["transcricao"]
                            item["conteudo"] = servico.gerar_conteudo_estruturado(
                                transcricao["text"],
                                transcricao.get("title", ""),
                                url,
                            )
                        except Exception as exc:
                            item["conteudo_erro"] = str(exc)

                    if item["downloads"]:
                        item["dados"] = item["downloads"][0]
                    elif item.get("transcricao"):
                        item["dados"] = item["transcricao"]
                    item["ok"] = not any(
                        (
                            item.get("erros"),
                            item.get("transcricao_erro"),
                            item.get("conteudo_erro"),
                        )
                    )
                elif self.operacao in ("transcricao", "conteudo"):
                    item["transcricao"] = servico.criar_transcricao(
                        url,
                        destino_item,
                        progresso,
                        criar_srt=self.criar_srt,
                    )
                    item["dados"] = item["transcricao"]
                    item["ok"] = True
                    if (
                        self.operacao == "conteudo"
                        or self.gerar_conteudo_apos_transcricao
                    ):
                        try:
                            transcricao = item["transcricao"]
                            item["conteudo"] = servico.gerar_conteudo_estruturado(
                                transcricao["text"],
                                transcricao.get("title", ""),
                                url,
                            )
                        except Exception as exc:
                            item["conteudo_erro"] = str(exc)
                            if self.operacao == "conteudo":
                                item["ok"] = False
                else:
                    raise ValueError("Operação de mídia desconhecida.")
            except Exception as exc:
                if self.operacao == "conteudo" and item.get("transcricao"):
                    item["conteudo_erro"] = str(exc)
                    item["ok"] = False
                else:
                    item["erro"] = str(exc)
            tem_erro = any(
                item.get(chave)
                for chave in (
                    "erro",
                    "erros",
                    "transcricao_erro",
                    "conteudo_erro",
                )
            )
            if tem_erro:
                item["ok"] = False
            tem_saida = bool(
                item.get("downloads")
                or item.get("transcricao")
                or item.get("conteudo")
            )
            item["parcial"] = bool(not item["ok"] and tem_saida)
            if (
                item.get("ok")
                or item.get("transcricao")
                or item.get("downloads")
            ):
                erro_historico = self._salvar_historico(url, item)
                if erro_historico:
                    item["historico_erro"] = erro_historico
            resultados.append(item)
            progresso(100, "Concluído.")

        return {
            "items": resultados,
            "success_count": sum(1 for item in resultados if item["ok"]),
            "partial_count": sum(
                1 for item in resultados if item.get("parcial")
            ),
            "failure_count": sum(
                1
                for item in resultados
                if not item["ok"] and not item.get("parcial")
            ),
        }

    def run(self):
        servico = ServicoMidia()
        try:
            if self.operacao == "pesquisa":
                dados = {
                    "items": servico.pesquisar_videos(
                        self.consulta,
                        max_resultados=self.max_resultados,
                        visualizacoes_minimas=self.visualizacoes_minimas,
                        duracao_minima_segundos=self.duracao_minima_segundos,
                        duracao_maxima_segundos=self.duracao_maxima_segundos,
                        dias_atras=self.dias_atras,
                    )
                }
            elif self.operacao == "informacoes":
                if len(self.urls) != 1:
                    raise ValueError("Verifique um link por vez.")
                dados = servico.obter_informacoes(self.url)
            elif len(self.urls) > 1 or self.operacao == "processamento":
                dados = self._executar_lote(servico)
            elif self.operacao == "download":
                destino_item = self._destino_para_url(servico, self.urls[0])
                dados = servico.baixar_midia(
                    self.urls[0],
                    destino_item,
                    self.tipo,
                    self.progresso.emit,
                    self.resolucao_max,
                    self.formato_video,
                    self.formato_audio,
                )
                formato = (
                    self.formato_video
                    if self.tipo == "video"
                    else self.formato_audio
                )
                dados["message"] = f"Download de {formato.upper()} concluído em {dados['folder']}."
                if (
                    self.transcrever_apos_download
                    or self.gerar_conteudo_apos_transcricao
                    or self.criar_srt
                ):
                    self.progresso.emit(-1, "Download concluído; criando a transcrição…")
                    try:
                        dados["transcricao"] = servico.criar_transcricao(
                            self.urls[0],
                            destino_item,
                            self.progresso.emit,
                            criar_srt=self.criar_srt,
                            salvar_txt=(
                                self.transcrever_apos_download
                                or self.gerar_conteudo_apos_transcricao
                            ),
                        )
                    except Exception as exc:
                        dados["transcricao_erro"] = str(exc)
                if (
                    self.gerar_conteudo_apos_transcricao
                    and dados.get("transcricao")
                ):
                    self.progresso.emit(-1, "Gerando conteúdo estruturado com Ollama…")
                    try:
                        transcricao = dados["transcricao"]
                        dados["conteudo"] = servico.gerar_conteudo_estruturado(
                            transcricao["text"],
                            transcricao.get("title", ""),
                            self.urls[0],
                        )
                    except Exception as exc:
                        dados["conteudo_erro"] = str(exc)
            elif self.operacao == "transcricao":
                destino_item = self._destino_para_url(servico, self.urls[0])
                dados = servico.criar_transcricao(
                    self.urls[0],
                    destino_item,
                    self.progresso.emit,
                    criar_srt=self.criar_srt,
                )
                if self.gerar_conteudo_apos_transcricao:
                    self.progresso.emit(-1, "Gerando conteúdo estruturado com Ollama…")
                    try:
                        dados["conteudo"] = servico.gerar_conteudo_estruturado(
                            dados["text"],
                            dados.get("title", ""),
                            self.urls[0],
                        )
                    except Exception as exc:
                        dados["conteudo_erro"] = str(exc)
            elif self.operacao == "conteudo":
                if self.texto_transcricao.strip():
                    transcricao = {
                        "text": self.texto_transcricao.strip(),
                        "title": self.titulo_transcricao,
                        "source": "transcrição já carregada",
                    }
                else:
                    transcricao = servico.criar_transcricao(
                        self.urls[0],
                        self._destino_para_url(servico, self.urls[0]),
                        self.progresso.emit,
                    )
                dados = {"transcricao": transcricao}
                self.progresso.emit(-1, "Gerando conteúdo estruturado com Ollama…")
                try:
                    dados["conteudo"] = servico.gerar_conteudo_estruturado(
                        transcricao["text"],
                        transcricao.get("title", ""),
                        self.urls[0],
                    )
                except Exception as exc:
                    dados["conteudo_erro"] = str(exc)
            else:
                raise ValueError("Operação de mídia desconhecida.")

            if self.operacao in (
                "download",
                "transcricao",
                "conteudo",
                "processamento",
            ) and "items" not in dados:
                erro_historico = self._salvar_historico(self.urls[0], dados)
                if erro_historico:
                    dados["historico_erro"] = erro_historico

            self.resultado.emit({
                "ok": True,
                "operacao": self.operacao,
                "dados": dados,
            })
        except Exception as exc:
            log.erro("TarefaMidia", "run", f"{self.operacao}: {exc}")
            self.resultado.emit({
                "ok": False,
                "operacao": self.operacao,
                "erro": str(exc),
            })
