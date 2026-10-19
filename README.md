# hen-DowVideos

Aplicativo desktop em Python e PySide6 para analisar links de mídia, baixar vídeo
ou áudio, criar transcrições e gerar conteúdo estruturado localmente.

## O que o aplicativo faz

- Analisa um link e mostra título, canal, duração, formato de origem e qualidades
  disponíveis.
- Baixa vídeo ou áudio de links reconhecidos pelo
  [yt-dlp](https://github.com/yt-dlp/yt-dlp), inclusive Shorts quando acessíveis.
- Permite combinar tarefas: baixar vídeo, baixar áudio, criar transcrição e gerar
  conteúdo estruturado.
- Por padrão, organiza os resultados em uma subpasta por vídeo; essa opção pode ser
  desmarcada para salvar tudo diretamente na pasta escolhida.
- Pesquisa vídeos do YouTube por tema ou palavra-chave, com filtros de duração,
  visualizações e data de publicação.
- Tenta usar legendas existentes antes de recorrer à transcrição local com Whisper.
- Gera conteúdo editorial estruturado em JSON usando o Ollama instalado na máquina.
- Mantém um histórico local dos links e resultados processados.

O processamento acontece em segundo plano para manter a interface responsiva.

## Requisitos

Ambiente documentado para instalação:

- Windows 64 bits
- Python 3.13.1
- FFmpeg instalado separadamente ou disponível no `PATH`

Dependências Python — também listadas em `requirements.txt`:

- PySide6
- qtawesome
- yt-dlp
- openai-whisper

O PyTorch é instalado como dependência do Whisper. FFmpeg e Ollama **não** são
instalados pelo `pip`.

## Instalação no Windows

Abra o PowerShell na pasta do projeto:

```powershell
py -3.13.1 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente virtual, permita scripts locais
para o seu usuário e tente novamente:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### FFmpeg

Instale o FFmpeg separadamente. O aplicativo procura primeiro nestas pastas:

```text
FFMPEG/FFmpeg/bin/ffmpeg.exe
FFMPEG/bin/ffmpeg.exe
FFMPEG/ffmpeg.exe
```

Também pode usar um executável `ffmpeg` disponível no `PATH`. Os binários do
FFmpeg não fazem parte deste repositório e a pasta `FFMPEG/` está excluída do Git.

### Ollama (opcional)

O Ollama só é necessário para gerar conteúdo estruturado. Instale e abra o Ollama
e baixe o modelo padrão:

```powershell
ollama pull llama3.2
```

O aplicativo usa por padrão o serviço local em
`http://127.0.0.1:11434/api/generate`. Para usar outro modelo ou endereço, defina
as variáveis de ambiente antes de iniciar:

```powershell
$env:HEN_DOWVIDEOS_MODELO_OLLAMA = "nome-do-modelo"
$env:HEN_DOWVIDEOS_OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
```

## Iniciar

Com o ambiente virtual ativado, execute:

```powershell
python main.py
```

## Uso básico

1. Cole um link — ou vários, um por linha.
2. Para consultar título, duração e qualidades, deixe apenas um link e clique em
   **Analisar link**.
3. Marque uma ou mais tarefas. As opções de formato e qualidade aparecem conforme
   as tarefas escolhidas.
4. Escolha a pasta de saída e mantenha marcada **Organizar os arquivos de cada vídeo
   em uma subpasta** para separar os resultados por vídeo. Desmarque para usar uma
   única pasta.
5. Clique em **Iniciar processamento**. O resumo final informa o que concluiu, o que
   ficou parcial e onde os arquivos foram salvos.
6. Consulte as abas de transcrição, conteúdo estruturado e histórico.

A pesquisa do YouTube pode ser aberta pela própria tela. Os resultados escolhidos
na busca são adicionados à lista de links.

## Formatos disponíveis

- **Vídeo:** MP4, MKV, MOV, AVI, FLV, WMV e WEBM.
- **Áudio:** MP3, M4A, WAV, FLAC e OPUS.

A qualidade de vídeo pode ser escolhida depois de analisar um link. A seleção do
formato e a compatibilidade final também dependem dos codecs de origem e do FFmpeg;
nem toda troca de contêiner significa que o vídeo será recodificado. Confirme a
reprodução no aparelho de destino.

## Transcrição e conteúdo estruturado

O processo de transcrição tenta obter legendas disponíveis. Se não encontrar
legendas, baixa o áudio e usa Whisper localmente. Na primeira utilização, o modelo
Whisper pode ser baixado automaticamente e ocupar espaço em disco.

Para gerar conteúdo estruturado, o aplicativo precisa do Ollama aberto e do modelo
configurado instalado. O conteúdo é gerado a partir da transcrição e pode ser salvo
como JSON. Transcrições muito longas podem exceder o limite de geração configurado.

O histórico e o cache local são armazenados na pasta de dados do usuário. No Windows,
o diretório padrão do aplicativo é `%APPDATA%\hen-dowvideos`.

## Limitações e uso responsável

- O suporte depende dos extratores disponíveis no yt-dlp e do acesso permitido pelo
  site de origem. Nem todo link será compatível.
- Alguns sites podem exigir autenticação, bloquear o acesso ou não fornecer mídia.
- O aplicativo não importa cookies do navegador, não contorna DRM e não encerra
  processos do navegador.
- Use a ferramenta somente com conteúdo que você tenha autorização para baixar e
  respeitando os direitos autorais e os termos do serviço de origem.

## Estrutura do projeto

```text
_APP_/          Interface PySide6, janela de busca e painel principal
_APPDATA_/      Pastas locais, configurações e cache
_CONFIGURA_/    Configurações, formatos e estilos
_LOGS_/         Registro da aplicação
_MIDIA_/        Metadados, downloads, transcrição e histórico SQLite
_THREADS_/      Tarefas em segundo plano e gerenciamento de threads
_ULTILIDADES_/  Ícones, pop-ups e indicador de carregamento
nucleo/         Documentação de desenvolvimento
main.py         Inicialização do aplicativo
requirements.txt
```

## Estado e licença

O projeto está em desenvolvimento e depende de serviços e binários externos. A
execução completa deve ser validada no computador de destino com as dependências,
o FFmpeg e, quando necessário, o Ollama instalados.

Não há um arquivo de licença identificado neste repositório. Defina uma licença
antes de autorizar formalmente o uso, a distribuição ou contribuições de terceiros.
