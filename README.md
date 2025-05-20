# GenAI Processors Library 📚

**Build Modular, Asynchronous, and Composable AI Pipelines for Generative AI.**

GenAI Processors is a lightweight Python library that enables efficient,
parallel content processing.

At the core of the GenAI Processors library lies the concept of a `Processor`. A
`Processor` encapsulates a unit of work with a simple API: it takes a stream of
`ProcessorPart`s as input and returns a stream of `ProcessorPart`s (or
compatible types) as output.

```python
async def call(
  content: AsyncIterable[ProcessorPart]
) -> AsyncIterable[ProcessorPartTypes]
```

By processing diverse input modalities in a bidirectional streaming fashion,
Processors are helpful for streamlining agent development, particularly for
building agents using the
[Gemini Live API](https://ai.google.dev/gemini-api/docs/live).

The concept of `Processor` provides a common abstraction for Gemini model calls
and increasingly complex behaviors built around them, accommodating both
turn-based interactions and live streaming.

The GenAI Processors library offers an easy and intuitive way to create and
combine these processors and arranges for their async execution in the most
efficient way.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<!-- Add badges for PyPI version once available -->

## ✨ Key Features

*   **Modular**: Breaks down complex tasks into reusable `Processor` and
    `PartProcessor` units, which are easily chained (`+`) or parallelized (`//`)
    to create sophisticated data flows and agentic behaviors.
*   **Integrated with GenAI API**: Includes ready-to-use processors like
    `GenaiModel` for turn-based API calls and `LiveProcessor` for real-time
    streaming interactions.
*   **Extensible**: Lets you create custom processors by inheriting from base
    classes or using simple function decorators.
*   **Rich Content Handling**:
    *   `ProcessorPart`: A wrapper around `genai.types.Part` enriched with
        metadata like MIME type, role, and custom attributes.
    *   Supports various content types (text, images, audio, custom JSON).
*   **Asynchronous & Concurrent**: Built on Python's familiar `asyncio`
    framework to orchestrate concurrent tasks (including network I/O and
    communication with compute-heavy subthreads).
*   **Stream Management**: Has utilities for splitting, concatenating, and
    merging asynchronous streams of `ProcessorPart`s.

## 📦 Installation

The GenAI Processors library requires Python 3.10+.

Install it with:

```bash
pip install genai-processors
```

## 🚀 Getting Started

Check the following colabs to get familiar with GenAI processors (we recommend
following them in order):

*   [Content API Colab](https://colab.research.google.com/github/google/genai-processors/blob/main/notebooks/content_api_intro.ipynb) -
    explains the basics of `ProcessorPart`, `ProcessorContent`, and how to
    create them.
*   [Processor Intro Colab](https://colab.research.google.com/github/google/genai-processors/blob/main/notebooks/processor_intro.ipynb) -
    an introduction to the core concepts of GenAI Processors.
*   [Create Your Own Processor](https://colab.research.google.com/github/google/genai-processors/blob/main/notebooks/create_your_own_processor.ipynb) -
    a walkthrough of the typical steps to create a `Processor` or a
    `PartProcessor`.
*   [Work with the Live API](https://colab.research.google.com/github/google/genai-processors/blob/main/notebooks/live_processor_intro.ipynb) -
    a couple of examples of real-time processors built from the Gemini Live API
    using the `LiveProcessor` class.

## 📖 Examples

Explore the [examples/](examples/) directory for practical demonstrations:

*   [Research Agent Example](examples/research/README.md) - a research agent
    built with Processors, comprising 3 sub-processors, chaining, creating
    `ProcessorPart`s, etc.
*   [Live Commentary Example](examples/live/README.md) - a description of a live
    commentary agent built with the Gemini Live API, composed of two agents: one
    for event detection and one for managing the conversation.

## 🧩 Built-in Processors

The [core/](core/) directory contains a set of basic processors that you can
leverage in your own applications. It includes the generic building blocks
needed for most real-time applications and will evolve over time to include more
core components.

Community contributions expanding the set of built-in processors are located
under [contrib/](contrib/) - see the section below on how to add code to the
GenAI Processor library.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines on how to contribute to this project.

## 📜 License

This project is licensed under the Apache License, Version 2.0. See the
[LICENSE](LICENSE) file for details.
