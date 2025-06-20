# Built-in Processors (`genai_processors.core`) 🧩

The library includes several pre-built processors:

*   **`genai_model.GenaiModel`**: Facilitates standard, turn-based interactions
    with Google's GenAI models (e.g., Gemini).
*   **`live_model.LiveProcessor`**: Enables real-time, streaming interactions
    with Google's GenAI Live API.
*   **`event_detection.EventDetection`**: Uses a GenAI model to detect specific
    events within a continuous stream of images (like video).
*   **`rate_limit_audio.RateLimitAudio`**: Splits and rate-limits audio streams
    to ensure natural playback speed, crucial for streaming audio output.
*   **`text.MatchProcessor`**: Finds and extracts a regex pattern within the
    input stream.
*   **`timestamp.Timestamp`**: Adds `ProcessorPart` objects containing
    timestamps to a stream, commonly used with image or video frames.
*   **`audio_io.PyAudioIn` / `audio_io.PyAudioOut`**: For capturing audio from a
    microphone (`PyAudioIn`) and playing audio to speakers (`PyAudioOut`) using
    PyAudio.
*   **`video.VideoIn`**: Generates a stream of image `ProcessorPart` objects
    from a camera or screen capture source.
*   **`preamble.Preamble` / `preamble.Suffix`**: Adds fixed content to the
    beginning (`Preamble`) or end (`Suffix`) of a full content stream.
*   **`drive.Docs` / `drive.Sheets` / `drive.Slides`**: Downloads Google
    Docs / Sheets / Slides, which can be passed to a `GenaiModel` for grounding.
