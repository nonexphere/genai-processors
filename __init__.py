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

"""Google DeepMind genai processors library."""

__version__ = '1.0.0'

from . import content_api
from . import context
from . import debug
from . import map_processor
from . import mime_types
from . import processor
from . import streams

# Aliases
ProcessorPart = content_api.ProcessorPart
ProcessorContent = content_api.ProcessorContent
ProcessorPartTypes = content_api.ProcessorPartTypes
ProcessorContentTypes = content_api.ProcessorContentTypes
Processor = processor.Processor
PartProcessor = processor.PartProcessor
ProcessorFn = processor.ProcessorFn
PartProcessorWithMatchFn = processor.PartProcessorWithMatchFn

apply_sync = processor.apply_sync
apply_async = processor.apply_async
chain = processor.chain
parallel = processor.parallel
parallel_concat = processor.parallel_concat
create_filter = processor.create_filter
part_processor_function = processor.part_processor_function

stream_content = streams.stream_content
gather_stream = streams.gather_stream
