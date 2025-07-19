Get started with Live API

Pré-lançamento :a API Live está em fase de pré-lançamento.
A API Live permite interações de voz e vídeo em tempo real com baixa latência com o Gemini. Ele processa transmissões contínuas de áudio, vídeo ou texto para fornecer respostas faladas imediatas e semelhantes a humanos, criando uma experiência de conversa natural para seus usuários.

Visão geral da API Live

A API Live oferece um conjunto abrangente de recursos, como detecção de atividade de voz, uso de ferramentas e chamada de função, gerenciamento de sessão (para gerenciar conversas de longa duração) e tokens temporários (para autenticação segura do lado do cliente).

Nesta página, você encontra exemplos e amostras de código básicas.

Exemplos de aplicativos
Confira os exemplos de aplicativos a seguir que ilustram como usar a API Live para casos de uso completos:

App de inicialização de áudio ao vivo no AI Studio, usando bibliotecas JavaScript para se conectar à API Live e transmitir áudio bidirecional pelo microfone e alto-falantes.
Livro de receitas de Python da API Live usando Pyaudio, que se conecta à API Live.
Integrações com parceiros
Se você preferir um processo de desenvolvimento mais simples, use o Daily ou o LiveKit. São plataformas de parceiros terceirizados que já integraram a API Gemini Live ao protocolo WebRTC para agilizar o desenvolvimento de aplicativos de áudio e vídeo em tempo real.

Antes de começar a criar
Antes de começar a criar com a API Live, você precisa tomar duas decisões importantes: escolher um modelo e uma abordagem de implementação.

Escolher uma arquitetura de geração de áudio
Se você estiver criando um caso de uso baseado em áudio, a escolha do modelo vai determinar a arquitetura de geração de áudio usada para criar a resposta de áudio:

Áudio nativo:essa opção oferece a fala mais natural e realista e melhor desempenho multilíngue. Ele também ativa recursos avançados, como diálogo afetivo (com reconhecimento de emoções), áudio proativo (em que o modelo pode decidir ignorar ou responder a determinadas entradas) e "pensamento". O áudio nativo é compatível com os seguintes modelos de áudio nativo:
gemini-2.5-flash-preview-native-audio-dialog
gemini-2.5-flash-exp-native-audio-thinking-dialog
Áudio em meia cascata: essa opção usa uma arquitetura de modelo em cascata (entrada de áudio nativa e saída de texto em voz). Ele oferece melhor desempenho e confiabilidade em ambientes de produção, especialmente com o uso de ferramentas. O áudio em cascata parcial é compatível com os seguintes modelos:
gemini-live-2.5-flash-preview
gemini-2.0-flash-live-001
Escolher uma abordagem de implementação
Ao integrar com a API Live, você precisa escolher uma das seguintes abordagens de implementação:

De servidor para servidor: o back-end se conecta à API ativa usando WebSockets. Normalmente, o cliente envia dados de streaming (áudio, vídeo, texto) para o servidor, que os encaminha para a API Live.
Cliente-servidor: o código do front-end se conecta diretamente à API Live usando WebSockets para transmitir dados, ignorando o back-end.
Observação: geralmente, a conexão cliente-servidor oferece melhor desempenho para streaming de áudio e vídeo, já que dispensa a necessidade de enviar o stream para o back-end primeiro. A configuração também é mais fácil, já que você não precisa implementar um proxy que envia dados do cliente para o servidor e, em seguida, do servidor para a API. No entanto, para ambientes de produção, a fim de reduzir os riscos de segurança, recomendamos usar tokens temporários em vez de chaves de API padrão.
Primeiros passos
Este exemplo lê um arquivo WAV, o envia no formato correto e salva os dados recebidos como um arquivo WAV.

É possível enviar áudio convertendo-o em PCM de 16 bits, 16 kHz, formato mono, e receber áudio definindo AUDIO como modalidade de resposta. A saída usa uma taxa de amostragem de 24 kHz.

Python
JavaScript

# Test file: https://storage.googleapis.com/generativeai-downloads/data/16000.wav
# Install helpers for converting files: pip install librosa soundfile
import asyncio
import io
from pathlib import Path
import wave
from google import genai
from google.genai import types
import soundfile as sf
import librosa

client = genai.Client()

# Half cascade model:
# model = "gemini-live-2.5-flash-preview"

# Native audio output model:
model = "gemini-2.5-flash-preview-native-audio-dialog"

config = {
  "response_modalities": ["AUDIO"],
  "system_instruction": "You are a helpful assistant and answer in a friendly tone.",
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:

        buffer = io.BytesIO()
        y, sr = librosa.load("sample.wav", sr=16000)
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()

        # If already in correct format, you can use this:
        # audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)  # Output is 24kHz

        async for response in session.receive():
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())
A seguir
Leia o guia completo de recursos da API Live para conferir os principais recursos e configurações, incluindo a Detecção de atividade de voz e recursos de áudio nativos.
Leia o guia Uso de ferramentas para saber como integrar a API Live com ferramentas e chamadas de função.
Leia o guia Gerenciamento de sessões para gerenciar conversas de longa duração.
Leia o guia Tokens temporários para autenticação segura em aplicativos de cliente para servidor.
Para mais informações sobre a API WebSockets, consulte a referência da API WebSockets.


Página inicial
Gemini API
Modelos
Isso foi útil?

Envie comentáriosLive API capabilities guide

Prévia: a API Live está em prévia.
Este é um guia abrangente que aborda os recursos e as configurações disponíveis com a API Live. Consulte a página Começar a usar a API Live para ter uma visão geral e exemplos de código para casos de uso comuns.

Antes de começar
Conheça os conceitos básicos:se ainda não fez isso, leia primeiro a página Começar a usar a API Live . Assim, você vai conhecer os princípios fundamentais da API Live, como ela funciona e a distinção entre os diferentes modelos e os métodos de geração de áudio correspondentes (áudio nativo ou half-cascade).
Teste a API Live no AI Studio:pode ser útil testar a API Live no Google AI Studio antes de começar a criar. Para usar a API Live no Google AI Studio, selecione Transmissão.
Como estabelecer uma conexão
O exemplo a seguir mostra como criar uma conexão com uma chave de API:

Python
JavaScript

import asyncio
from google import genai

client = genai.Client()

model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        print("Session started")

if __name__ == "__main__":
    asyncio.run(main())
Observação: só é possível definir uma modalidade no campo response_modalities. Isso significa que você pode configurar o modelo para responder com texto ou áudio, mas não ambos na mesma sessão.
Modalidades de interação
As seções a seguir fornecem exemplos e contexto de suporte para as diferentes modalidades de entrada e saída disponíveis na API Live.

Envio e recebimento de texto
Saiba como enviar e receber texto:

Python
JavaScript

import asyncio
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello, how are you?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.text is not None:
                print(response.text, end="")

if __name__ == "__main__":
    asyncio.run(main())
Atualizações incrementais de conteúdo
Use atualizações incrementais para enviar entrada de texto, estabelecer ou restaurar o contexto da sessão. Para contextos curtos, você pode enviar interações de turno a turno para representar a sequência exata de eventos:

Python
JavaScript

turns = [
    {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
    {"role": "model", "parts": [{"text": "Paris"}]},
]

await session.send_client_content(turns=turns, turn_complete=False)

turns = [{"role": "user", "parts": [{"text": "What is the capital of Germany?"}]}]

await session.send_client_content(turns=turns, turn_complete=True)
Para contextos mais longos, é recomendável fornecer um único resumo da mensagem para liberar a janela de contexto para interações subsequentes. Consulte Retomada de sessão para outro método de carregar o contexto da sessão.

Envio e recebimento de áudio
O exemplo de áudio mais comum, áudio para áudio, é abordado no guia Começar.

Confira um exemplo de áudio para texto que lê um arquivo WAV, envia no formato correto e recebe a saída de texto:

Python
JavaScript

# Test file: https://storage.googleapis.com/generativeai-downloads/data/16000.wav
# Install helpers for converting files: pip install librosa soundfile
import asyncio
import io
from pathlib import Path
from google import genai
from google.genai import types
import soundfile as sf
import librosa

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:

        buffer = io.BytesIO()
        y, sr = librosa.load("sample.wav", sr=16000)
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()

        # If already in correct format, you can use this:
        # audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
E aqui está um exemplo de texto para áudio. Para receber áudio, defina AUDIO como modalidade de resposta. Este exemplo salva os dados recebidos como um arquivo WAV:

Python
JavaScript

import asyncio
import wave
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["AUDIO"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        message = "Hello how are you?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())
Formatos de áudio
Os dados de áudio na API Live são sempre brutos, little-endian, PCM de 16 bits. A saída de áudio sempre usa uma taxa de amostragem de 24 kHz. O áudio de entrada é nativamente de 16 kHz, mas a API Live faz uma nova amostragem, se necessário, para que qualquer taxa de amostragem possa ser enviada. Para transmitir a taxa de amostragem do áudio de entrada, defina o tipo MIME de cada Blob que contém áudio como um valor como audio/pcm;rate=16000.

Transcrições de áudio
É possível ativar a transcrição da saída de áudio do modelo enviando output_audio_transcription na configuração de configuração. O idioma da transcrição é inferido da resposta do modelo.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["AUDIO"],
        "output_audio_transcription": {}
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello? Gemini are you there?"

        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.server_content.model_turn:
                print("Model turn:", response.server_content.model_turn)
            if response.server_content.output_transcription:
                print("Transcript:", response.server_content.output_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())
É possível ativar a transcrição da entrada de áudio enviando input_audio_transcription na configuração de configuração.

Python
JavaScript

import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {
    "response_modalities": ["TEXT"],
    "input_audio_transcription": {},
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_data = Path("16000.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type='audio/pcm;rate=16000')
        )

        async for msg in session.receive():
            if msg.server_content.input_transcription:
                print('Transcript:', msg.server_content.input_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())
Fazer streaming de áudio e vídeo
Para ver um exemplo de como usar a API Live em um formato de streaming de áudio e vídeo, execute o arquivo "Live API - Get Started" no repositório de livros de receitas:

Conferir no Colab

Mudar a voz e o idioma
Cada modelo da API Live é compatível com um conjunto diferente de vozes. A meia cascata é compatível com Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus e Zephyr. O áudio nativo oferece suporte a uma lista muito mais longa (idêntica à lista de modelos de TTS). Você pode ouvir todas as vozes no AI Studio.

Para especificar uma voz, defina o nome dela no objeto speechConfig como parte da configuração da sessão:

Python
JavaScript

config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}
    },
}
Observação: se você estiver usando a API generateContent, o conjunto de vozes disponíveis será um pouco diferente. Consulte o guia de geração de áudio para conhecer as vozes de geração de áudio do generateContent.
A API Live é compatível com vários idiomas.

Para mudar o idioma, defina o código de idioma no objeto speechConfig como parte da configuração da sessão:

Python
JavaScript

config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "language_code": "de-DE"
    }
}
Observação: os modelos de saída de áudio nativa escolhem automaticamente o idioma adequado e não permitem definir explicitamente o código de idioma.
Recursos de áudio nativos
Os recursos a seguir estão disponíveis apenas com áudio nativo. Saiba mais sobre o áudio nativo em Escolher um modelo e geração de áudio.

Observação: no momento, os modelos de áudio nativos têm suporte limitado para uso de ferramentas. Consulte Visão geral das ferramentas aceitas para mais detalhes.
Como usar a saída de áudio nativa
Para usar a saída de áudio nativa, configure um dos modelos de áudio nativos e defina response_modalities como AUDIO.

Consulte Enviar e receber áudio para ver um exemplo completo.

Python
JavaScript

model = "gemini-2.5-flash-preview-native-audio-dialog"
config = types.LiveConnectConfig(response_modalities=["AUDIO"])

async with client.aio.live.connect(model=model, config=config) as session:
    # Send audio input and receive audio
Computação afetiva
Com esse recurso, o Gemini pode adaptar o estilo das respostas conforme a expressão e o tom da solicitação.

Para usar o diálogo afetivo, defina a versão da API como v1alpha e defina enable_affective_dialog como true na mensagem de configuração:

Python
JavaScript

client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    enable_affective_dialog=True
)
No momento, o diálogo afetivo só é compatível com os modelos nativos de saída de áudio.

Áudio proativo
Quando esse recurso está ativado, o Gemini pode decidir não responder proativamente se o conteúdo não for relevante.

Para usar, defina a versão da API como v1alpha, configure o campo proactivity na mensagem de configuração e defina proactive_audio como true:

Python
JavaScript

client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    proactivity={'proactive_audio': True}
)
No momento, o áudio proativo só é compatível com os modelos de saída de áudio nativos.

Saída de áudio nativa com pensamento
A saída de áudio nativa oferece suporte a capacidades de pensamento, disponíveis em um modelo separado gemini-2.5-flash-exp-native-audio-thinking-dialog.

Consulte Enviar e receber áudio para ver um exemplo completo.

Python
JavaScript

model = "gemini-2.5-flash-exp-native-audio-thinking-dialog"
config = types.LiveConnectConfig(response_modalities=["AUDIO"])

async with client.aio.live.connect(model=model, config=config) as session:
    # Send audio input and receive audio
Detecção de atividade de voz (VAD)
A detecção de atividade de voz (VAD, na sigla em inglês) permite que o modelo reconheça quando uma pessoa está falando. Isso é essencial para criar conversas naturais, já que permite que um usuário interrompa o modelo a qualquer momento.

Quando o VAD detecta uma interrupção, a geração em andamento é cancelada e descartada. Apenas as informações já enviadas ao cliente são mantidas no histórico da sessão. Em seguida, o servidor envia uma mensagem BidiGenerateContentServerContent para informar sobre a interrupção.

Em seguida, o servidor do Gemini descarta todas as chamadas de função pendentes e envia uma mensagem BidiGenerateContentServerContent com os IDs das chamadas canceladas.

Python
JavaScript

async for response in session.receive():
    if response.server_content.interrupted is True:
        # The generation was interrupted

        # If realtime playback is implemented in your application,
        # you should stop playing audio and clear queued playback here.
VAD automática
Por padrão, o modelo realiza automaticamente a VAD em um fluxo contínuo de entrada de áudio. A VAD pode ser configurada com o campo realtimeInputConfig.automaticActivityDetection da configuração de configuração.

Quando o fluxo de áudio é pausado por mais de um segundo (por exemplo, porque o usuário desativou o microfone), um evento audioStreamEnd precisa ser enviado para limpar o áudio em cache. O cliente pode retomar o envio de dados de áudio a qualquer momento.

Python
JavaScript

# example audio file to try:
# URL = "https://storage.googleapis.com/generativeai-downloads/data/hello_are_you_there.pcm"
# !wget -q $URL -O sample.pcm
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        # if stream gets paused, send:
        # await session.send_realtime_input(audio_stream_end=True)

        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
Com send_realtime_input, a API responde ao áudio automaticamente com base na VAD. Enquanto send_client_content adiciona mensagens ao contexto do modelo em ordem, send_realtime_input é otimizado para capacidade de resposta às custas da ordenação determinística.

Configuração automática de VAD
Para ter mais controle sobre a atividade de VAD, configure os seguintes parâmetros. Consulte a referência da API para mais informações.

Python
JavaScript

from google.genai import types

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False, # default
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 100,
        }
    }
}
Desativar a detecção automática de atividade de voz
Como alternativa, a VAD automática pode ser desativada definindo realtimeInputConfig.automaticActivityDetection.disabled como true na mensagem de configuração. Nessa configuração, o cliente é responsável por detectar a fala do usuário e enviar mensagens activityStart e activityEnd nos momentos adequados. Um audioStreamEnd não é enviado nessa configuração. Em vez disso, qualquer interrupção do stream é marcada por uma mensagem activityEnd.

Python
JavaScript

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
}

async with client.aio.live.connect(model=model, config=config) as session:
    # ...
    await session.send_realtime_input(activity_start=types.ActivityStart())
    await session.send_realtime_input(
        audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
    )
    await session.send_realtime_input(activity_end=types.ActivityEnd())
    # ...
Contagem de tokens
Você pode encontrar o número total de tokens consumidos no campo usageMetadata da mensagem retornada do servidor.

Python
JavaScript

async for message in session.receive():
    # The server will periodically send messages that include UsageMetadata.
    if message.usage_metadata:
        usage = message.usage_metadata
        print(
            f"Used {usage.total_token_count} tokens in total. Response token breakdown:"
        )
        for detail in usage.response_tokens_details:
            match detail:
                case types.ModalityTokenCount(modality=modality, token_count=count):
                    print(f"{modality}: {count}")
Resolução da mídia
É possível especificar a resolução da mídia de entrada definindo o campo mediaResolution como parte da configuração da sessão:

Python
JavaScript

from google.genai import types

config = {
    "response_modalities": ["AUDIO"],
    "media_resolution": types.MediaResolution.MEDIA_RESOLUTION_LOW,
}
Limitações
Considere as seguintes limitações da API Live ao planejar seu projeto.

Modalidades de resposta
Só é possível definir uma modalidade de resposta (TEXT ou AUDIO) por sessão na configuração da sessão. Definir os dois resulta em uma mensagem de erro de configuração. Isso significa que você pode configurar o modelo para responder com texto ou áudio, mas não ambos na mesma sessão.

Autenticação do cliente
Por padrão, a API Live só oferece autenticação de servidor para servidor. Se você estiver implementando seu aplicativo da API Live usando uma abordagem de cliente para servidor, use tokens efêmeros para reduzir os riscos de segurança.

Duração da sessão
As sessões somente de áudio têm duração máxima de 15 minutos, e as sessões de áudio e vídeo têm duração máxima de 2 minutos. No entanto, é possível configurar diferentes técnicas de gerenciamento de sessão para extensões ilimitadas na duração da sessão.

Janela de contexto
Uma sessão tem um limite de janela de contexto de:

128 mil tokens para modelos de saída de áudio nativa
32 mil tokens para outros modelos da API Live
Idiomas aceitos
A API Live é compatível com os seguintes idiomas.

Observação: os modelos de saída de áudio nativa escolhem automaticamente o idioma adequado e não permitem definir explicitamente o código de idioma.
Idioma	Código BCP-47	Idioma	Código BCP-47
Alemão (Alemanha)	de-DE	Inglês (Austrália)*	en-AU
Inglês (Reino Unido)*	en-GB	Inglês (Índia)	en-IN
Inglês (EUA)	en-US	Espanhol (EUA)	es-US
Francês (França)	fr-FR	Hindi (Índia)	hi-IN
Português (Brasil)	pt-BR	Árabe (genérico)	ar-XA
Espanhol (Espanha)*	es-ES	Francês (Canadá)*	fr-CA
Indonésio (Indonésia)	id-ID	Italiano (Itália)	it-IT
Japonês (Japão)	ja-JP	Turco (Turquia)	tr-TR
Vietnamita (Vietnã)	vi-VN	Bengali (Índia)	bn-IN
Gujarati (Índia)*	gu-IN	Canarês (Índia)*	kn-IN
Marati (Índia)	mr-IN	Malaiala (Índia)*	ml-IN
Tâmil (Índia)	ta-IN	Telugo (Índia)	te-IN
Holandês (Países Baixos)	nl-NL	Coreano (Coreia do Sul)	ko-KR
Chinês mandarim (China)*	cmn-CN	Polonês (Polônia)	pl-PL
Russo (Rússia)	ru-RU	Tailandês (Tailândia)	th-TH
Os idiomas marcados com um asterisco (*) não estão disponíveis para o áudio nativo.

A seguir
Leia os guias Uso de ferramentas e Gerenciamento de sessões para informações essenciais sobre o uso eficaz da API Live.
Teste a API Live no Google AI Studio.
Para mais informações sobre os modelos da API Live, consulte Gemini 2.0 Flash Live e Áudio nativo do Gemini 2.5 Flash na página "Modelos".
Confira mais exemplos no manual da API Live, no manual de ferramentas da API Live e no script de primeiros passos da API Live.



 Esta página foi traduzida pela API Cloud Translation.
Switch to English
Página inicial
Gemini API
Modelos
Isso foi útil?

Envie comentáriosTool use with Live API

O uso da ferramenta permite que a API Live vá além da conversa, permitindo que ela realize ações no mundo real e extraia o contexto externo, mantendo uma conexão em tempo real. É possível definir ferramentas como Chamada de função, Execução de código e Pesquisa Google com a API Live.

Visão geral das ferramentas compatíveis
Confira uma breve visão geral das ferramentas disponíveis para cada modelo:

Ferramenta	Modelos em cascata
gemini-live-2.5-flash-preview
gemini-2.0-flash-live-001	gemini-2.5-flash-preview-native-audio-dialog	gemini-2.5-flash-exp-native-audio-thinking-dialog
Pesquisa	Sim	Sim	Sim
Chamadas de função	Sim	Sim	Não
Execução de código	Sim	Não	Não
Contexto de URL	Sim	Não	Não
Chamadas de função
A API Live oferece suporte a chamadas de função, assim como solicitações normais de geração de conteúdo. A chamada de função permite que a API Live interaja com dados e programas externos, aumentando muito o que seus aplicativos podem realizar.

É possível definir declarações de função como parte da configuração da sessão. Depois de receber chamadas de ferramentas, o cliente precisa responder com uma lista de objetos FunctionResponse usando o método session.send_tool_response.

Consulte o tutorial de chamada de função para saber mais.

Observação: ao contrário da API generateContent, a API Live não oferece suporte ao processamento automático de respostas de ferramentas. Você precisa processar as respostas da ferramenta manualmente no código do cliente.
Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

# Simple function definitions
turn_on_the_lights = {"name": "turn_on_the_lights"}
turn_off_the_lights = {"name": "turn_off_the_lights"}

tools = [{"function_declarations": [turn_on_the_lights, turn_off_the_lights]}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Turn on the lights please"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)
            elif chunk.tool_call:
                function_responses = []
                for fc in chunk.tool_call.function_calls:
                    function_response = types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={ "result": "ok" } # simple, hard-coded function response
                    )
                    function_responses.append(function_response)

                await session.send_tool_response(function_responses=function_responses)

if __name__ == "__main__":
    asyncio.run(main())
Com um único comando, o modelo pode gerar várias chamadas de função e o código necessário para encadear as saídas. Esse código é executado em um ambiente de sandbox, gerando mensagens BidiGenerateContentToolCall subsequentes.

Chamada de função assíncrona
Observação: o método de chamada de função assíncrona só é aceito na geração de áudio half-cascade.
A chamada de função é executada sequencialmente por padrão, o que significa que a execução é pausada até que os resultados de cada chamada de função estejam disponíveis. Isso garante o processamento sequencial, o que significa que você não poderá continuar interagindo com o modelo enquanto as funções estiverem sendo executadas.

Se você não quiser bloquear a conversa, poderá pedir ao modelo para executar as funções de forma assíncrona. Para fazer isso, primeiro adicione um behavior às definições de função:

Python
JavaScript

  # Non-blocking function definitions
  turn_on_the_lights = {"name": "turn_on_the_lights", "behavior": "NON_BLOCKING"} # turn_on_the_lights will run asynchronously
  turn_off_the_lights = {"name": "turn_off_the_lights"} # turn_off_the_lights will still pause all interactions with the model
NON-BLOCKING garante que a função seja executada de forma assíncrona enquanto você pode continuar interagindo com o modelo.

Em seguida, é necessário informar ao modelo como se comportar quando ele receber o FunctionResponse usando o parâmetro scheduling. Ele pode:

Interromper o que está fazendo e informar a resposta recebida imediatamente (scheduling="INTERRUPT"),
Aguarde até que ele termine o que está fazendo (scheduling="WHEN_IDLE"),
Ou não faça nada e use esse conhecimento mais tarde na discussão (scheduling="SILENT")

Python
JavaScript

# for a non-blocking function definition, apply scheduling in the function response:
  function_response = types.FunctionResponse(
      id=fc.id,
      name=fc.name,
      response={
          "result": "ok",
          "scheduling": "INTERRUPT" # Can also be WHEN_IDLE or SILENT
      }
  )
Execução de código
É possível definir a execução do código como parte da configuração da sessão. Isso permite que a API Live gere e execute código Python e realize cálculos de forma dinâmica para melhorar seus resultados. Consulte o tutorial de execução de código para saber mais.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'code_execution': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Compute the largest prime palindrome under 100000."
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)

                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                      if part.executable_code is not None:
                        print(part.executable_code.code)

                      if part.code_execution_result is not None:
                        print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
Embasamento com a Pesquisa Google
É possível ativar o embasamento com a Pesquisa Google como parte da configuração da sessão. Isso aumenta a precisão da API Live e evita alucinações. Consulte o tutorial de embasamento para saber mais.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'google_search': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "When did the last Brazil vs. Argentina soccer match happen?"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)

                # The model might generate and execute Python code to use Search
                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                      if part.executable_code is not None:
                        print(part.executable_code.code)

                      if part.code_execution_result is not None:
                        print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
Combinar várias ferramentas
É possível combinar várias ferramentas na API Live, aumentando ainda mais os recursos do seu aplicativo:

Python
JavaScript

prompt = """
Hey, I need you to do three things for me.

1. Compute the largest prime palindrome under 100000.
2. Then use Google Search to look up information about the largest earthquake in California the week of Dec 5 2024?
3. Turn on the lights

Thanks!
"""

tools = [
    {"google_search": {}},
    {"code_execution": {}},
    {"function_declarations": [turn_on_the_lights, turn_off_the_lights]},
]

config = {"response_modalities": ["TEXT"], "tools": tools}

# ... remaining model call
A seguir
Confira mais exemplos de uso de ferramentas com a API Live no Livro de receitas de uso de ferramentas.
Confira a história completa sobre recursos e configurações no guia de recursos de API em tempo real.


Session management with Live API

Na API Live, uma sessão se refere a uma conexão persistente em que a entrada e a saída são transmitidas continuamente pela mesma conexão. Leia mais sobre como isso funciona. Esse design de sessão exclusivo permite baixa latência e oferece suporte a recursos exclusivos, mas também pode apresentar desafios, como limites de tempo de sessão e encerramento antecipado. Este guia aborda estratégias para superar os desafios de gerenciamento de sessões que podem surgir ao usar a API Live.

Tempo de vida da sessão
Sem compressão, as sessões somente de áudio são limitadas a 15 minutos, e as sessões de áudio e vídeo são limitadas a 2 minutos. Exceder esses limites encerra a sessão (e, portanto, a conexão), mas você pode usar a compressão da janela de contexto para estender as sessões por um período ilimitado.

A vida útil de uma conexão também é limitada a cerca de 10 minutos. Quando a conexão é encerrada, a sessão também é encerrada. Nesse caso, é possível configurar uma única sessão para permanecer ativa em várias conexões usando a retomada de sessão. Você também vai receber uma mensagem de saída antes que a conexão termine, permitindo que você realize outras ações.

Compactação da janela de contexto
Para permitir sessões mais longas e evitar o encerramento abrupto da conexão, ative a compressão da janela de contexto definindo o campo contextWindowCompression como parte da configuração da sessão.

Em ContextWindowCompressionConfig, é possível configurar um mecanismo de janela deslizante e o número de tokens que aciona a compactação.

Python
JavaScript

from google.genai import types

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    context_window_compression=(
        # Configures compression with default parameters.
        types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        )
    ),
)
Retomada da sessão
Para evitar o encerramento da sessão quando o servidor redefinir periodicamente a conexão WebSocket, configure o campo sessionResumption na configuração de configuração.

A transmissão dessa configuração faz com que o servidor envie mensagens SessionResumptionUpdate, que podem ser usadas para retomar a sessão transmitindo o último token de retomada como SessionResumptionConfig.handle da conexão subsequente.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

async def main():
    print(f"Connecting to the service with handle {previous_session_handle}...")
    async with client.aio.live.connect(
        model=model,
        config=types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            session_resumption=types.SessionResumptionConfig(
                # The handle of the session to resume is passed here,
                # or else None to start a new session.
                handle=previous_session_handle
            ),
        ),
    ) as session:
        while True:
            await session.send_client_content(
                turns=types.Content(
                    role="user", parts=[types.Part(text="Hello world!")]
                )
            )
            async for message in session.receive():
                # Periodically, the server will send update messages that may
                # contain a handle for the current state of the session.
                if message.session_resumption_update:
                    update = message.session_resumption_update
                    if update.resumable and update.new_handle:
                        # The handle should be retained and linked to the session.
                        return update.new_handle

                # For the purposes of this example, placeholder input is continually fed
                # to the model. In non-sample code, the model inputs would come from
                # the user.
                if message.server_content and message.server_content.turn_complete:
                    break

if __name__ == "__main__":
    asyncio.run(main())
Receber uma mensagem antes da desconexão da sessão
O servidor envia uma mensagem GoAway que sinaliza que a conexão atual será encerrada em breve. Essa mensagem inclui o timeLeft, que indica o tempo restante e permite que você tome outras medidas antes que a conexão seja encerrada como ABORTED.

Python
JavaScript

async for response in session.receive():
    if response.go_away is not None:
        # The connection will soon be terminated
        print(response.go_away.time_left)
Receber uma mensagem quando a geração for concluída
O servidor envia uma mensagem generationComplete que indica que o modelo terminou de gerar a resposta.

Python
JavaScript

async for response in session.receive():
    if response.server_content.generation_complete is True:
        # The generation is complete