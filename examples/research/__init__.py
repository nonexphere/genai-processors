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


"""Research agent example, using Processors library.

This agent takes user content as input, generates a set of topics based on
that content, researches each topic, and then synthesizes the research into a
final output.

The agent is composed of three main processors:
  - TopicGenerator: Generates `Topics` based on the user content.
  - TopicResearcher: Researches each `Topic`.
  - TopicVerbalizer: Converts a `Topic` ProcessorPart to a human-readable
  string.
  - The output of this flow is then passed to a GenAI model, which synthesizes
  the research into a final output.

The agent orchestrates these processors, passing the output of one to the
input of the next.
"""

import re

from . import agent
from . import interfaces
from .processors import topic_generator
from .processors import topic_researcher

ResearchAgent = agent.ResearchAgent
Config = interfaces.Config

TopicGenerator = topic_generator.TopicGenerator
TopicResearcher = topic_researcher.TopicResearcher

Topic = interfaces.Topic
