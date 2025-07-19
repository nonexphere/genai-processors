Página inicial
Gemini API
Modelos
Isso foi útil?

Envie comentáriosGeração de voz (conversão de texto em voz)

A API Gemini pode transformar a entrada de texto em áudio de um ou vários alto-falantes usando recursos nativos de geração de texto em fala (TTS). A geração de conversão de texto em voz (TTS) é controlável, o que significa que você pode usar a linguagem natural para estruturar interações e orientar o estilo, sotaque, ritmo e tom do áudio.

O recurso TTS é diferente da geração de fala fornecida pela API Live, que foi projetada para áudio interativo, não estruturado e entradas e saídas multimodais. Enquanto a API Live se destaca em contextos de conversação dinâmicos, a TTS pela API Gemini é personalizada para cenários que exigem recitação de texto exata com controle detalhado sobre estilo e som, como a geração de podcasts ou audiolivros.

Este guia mostra como gerar áudio de um ou vários alto-falantes a partir de texto.

Pré-lançamento :a conversão de texto em voz (TTS) nativa está em pré-lançamento.
Antes de começar
Use uma variante do modelo Gemini 2.5 com recursos nativos de conversão de texto em fala (TTS), conforme listado na seção Modelos compatíveis. Para resultados ideais, considere qual modelo se adapta melhor ao seu caso de uso específico.

Talvez seja útil testar os modelos de TTS do Gemini 2.5 no AI Studio antes de começar a criar.

Observação: os modelos de TTS aceitam entradas somente de texto e produzem saídas somente de áudio. Para conferir uma lista completa de restrições específicas para modelos de TTS, consulte a seção Limitações.
Conversão de texto em voz para um locutor
Para converter texto em áudio de alto-falante único, defina a modalidade de resposta como "audio" e transmita um objeto SpeechConfig com VoiceConfig definido. Você precisa escolher um nome de voz entre as vozes de saída pré-criadas.

Este exemplo salva o áudio de saída do modelo em um arquivo wave:

Python
JavaScript
REST

from google import genai
from google.genai import types
import wave

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client()

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents="Say cheerfully: Have a wonderful day!",
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
               voice_name='Kore',
            )
         )
      ),
   )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='out.wav'
wave_file(file_name, data) # Saves the file to current directory
Para mais exemplos de código, consulte o arquivo "TTS - Get Started" no repositório de livros de receitas:

Confira no GitHub

Conversão de texto em voz com vários alto-falantes
Para áudio com vários alto-falantes, você vai precisar de um objeto MultiSpeakerVoiceConfig com cada alto-falante (até dois) configurado como um SpeakerVoiceConfig. Você vai precisar definir cada speaker com os mesmos nomes usados no prompt:

Python
JavaScript
REST

from google import genai
from google.genai import types
import wave

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client()

prompt = """TTS the following conversation between Joe and Jane:
         Joe: How's it going today Jane?
         Jane: Not too bad, how about you?"""

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=prompt,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
               types.SpeakerVoiceConfig(
                  speaker='Joe',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                     )
                  )
               ),
               types.SpeakerVoiceConfig(
                  speaker='Jane',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                     )
                  )
               ),
            ]
         )
      )
   )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='out.wav'
wave_file(file_name, data) # Saves the file to current directory
Como controlar o estilo de fala com comandos
É possível controlar o estilo, o tom, o sotaque e o ritmo usando comandos em linguagem natural para TTS de um ou vários alto-falantes. Por exemplo, em um comando para um único alto-falante, você pode dizer:


Say in an spooky whisper:
"By the pricking of my thumbs...
Something wicked this way comes"
Em um comando com vários alto-falantes, forneça ao modelo o nome de cada alto-falante e a transcrição correspondente. Você também pode dar orientações para cada palestrante individualmente:


Make Speaker1 sound tired and bored, and Speaker2 sound excited and happy:

Speaker1: So... what's on the agenda today?
Speaker2: You're never going to guess!
Tente usar uma opção de voz que corresponda ao estilo ou emoção que você quer transmitir para enfatizar ainda mais. No comando anterior, por exemplo, a respiração de Enceladus pode enfatizar "cansado" e "entediado", enquanto o tom otimista de Puck pode complementar "animado" e "feliz".

Como gerar um comando para converter em áudio
Os modelos de TTS só geram áudio, mas você pode usar outros modelos para gerar uma transcrição primeiro e depois transmitir essa transcrição para o modelo de TTS para leitura em voz alta.

Python
JavaScript

from google import genai
from google.genai import types

client = genai.Client()

transcript = client.models.generate_content(
   model="gemini-2.0-flash",
   contents="""Generate a short transcript around 100 words that reads
            like it was clipped from a podcast by excited herpetologists.
            The hosts names are Dr. Anya and Liam.""").text

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=transcript,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
               types.SpeakerVoiceConfig(
                  speaker='Dr. Anya',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                     )
                  )
               ),
               types.SpeakerVoiceConfig(
                  speaker='Liam',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                     )
                  )
               ),
            ]
         )
      )
   )
)

# ...Code to stream or save the output
Opções de voz
Os modelos de TTS são compatíveis com as seguintes 30 opções de voz no campo voice_name:

Zephyr: Bright	Puck: Upbeat	Charon: informativo
Coreia: Firm	Fenrir: excitável	Leda -- Youthful
Orus: empresa	Aoede: Breezy	Callirrhoe: tranquila
Autonoe: Bright	Encélado: Breathy	Iapetus: Clear
Umbriel: tranquila	Algieba: Smooth	Despina: Smooth
Erinome: Clear	Algenib: Gravelly	Rasalgethi: informativo
Laomedeia: Upbeat	Achernar: suave	Alnilam: Firm
Schedar: par	Gacrux: Mature	Pulcherrima: Avançar
Achird: Friendly	Zubenelgenubi: Casual	Vindemiatrix: Gentle
Sadachbia: Lively	Sadaltager: conhecimento	Sulafat: quente
Você pode ouvir todas as opções de voz no AI Studio.

Idiomas aceitos
Os modelos de TTS detectam o idioma de entrada automaticamente. Elas oferecem suporte aos seguintes 24 idiomas:

Idioma	Código BCP-47	Idioma	Código BCP-47
Árabe (egípcio)	ar-EG	Alemão (Alemanha)	de-DE
Inglês (EUA)	en-US	Espanhol (EUA)	es-US
Francês (França)	fr-FR	Hindi (Índia)	hi-IN
Indonésio (Indonésia)	id-ID	Italiano (Itália)	it-IT
Japonês (Japão)	ja-JP	Coreano (Coreia)	ko-KR
Português (Brasil)	pt-BR	Russo (Rússia)	ru-RU
Holandês (Países Baixos)	nl-NL	Polonês (Polônia)	pl-PL
Tailandês (Tailândia)	th-TH	Turco (Turquia)	tr-TR
Vietnamita (Vietnã)	vi-VN	Romeno (Romênia)	ro-RO
Ucraniano (Ucrânia)	uk-UA	Bengali (Bangladesh)	bn-BD
Inglês (Índia)	Pacote en-IN e hi-IN	Marati (Índia)	mr-IN
Tâmil (Índia)	ta-IN	Telugo (Índia)	te-IN
Modelos compatíveis
Modelo	Apenas um locutor	Multialto-falante
TTS de pré-lançamento do Gemini 2.5 Flash	✔️	✔️
Gemini 2.5 Pro Preview TTS	✔️	✔️
Limitações
Os modelos TTS só podem receber entradas de texto e gerar saídas de áudio.
Uma sessão de TTS tem um limite de janela de contexto de 32 mil tokens.
Consulte a seção Idiomas para saber se o idioma é aceito.
A seguir
Teste o livro de receitas de geração de áudio.
A API Live do Gemini oferece opções de geração de áudio interligadas com outras modalidades.
Para trabalhar com entradas de áudio, acesse o guia Compreensão de áudio.
Isso foi útil?

Envie comentários
Exceto em caso de indicação contrária, o conteúdo desta página é licenciado de acordo com a Licença de atribuição 4.0 do Creative Comm