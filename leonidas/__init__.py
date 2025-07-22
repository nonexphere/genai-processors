# Copyright 2025 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Leonidas v2 - Modular Conversational AI Agent Package."""

from .leonidas import (
    InputManager,
    OutputManager,
    LeonidasOrchestrator,
    setup_logging,
    run_leonidas,
    LEONIDAS_TOOLS,
    LEONIDAS_SYSTEM_PROMPT,
)

from .memory_system import (
    LeonidasMemorySystem,
    MemoryInputProcessor,
    SessionHistoryProcessor,
    ContextLoadProcessor,
    SummaryGenerationProcessor,
    PersistentMemoryProcessor,
    InitialContextProcessor,
    ContextualGreetingProcessor,
)

__version__ = "2.0.0"
__all__ = [
    "InputManager",
    "OutputManager", 
    "LeonidasOrchestrator",
    "setup_logging",
    "run_leonidas",
    "LEONIDAS_TOOLS",
    "LEONIDAS_SYSTEM_PROMPT",
    "LeonidasMemorySystem",
    "MemoryInputProcessor",
    "SessionHistoryProcessor",
    "ContextLoadProcessor",
    "SummaryGenerationProcessor",
    "PersistentMemoryProcessor",
    "InitialContextProcessor",
    "ContextualGreetingProcessor",
]