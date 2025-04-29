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
"""Utilities for managing part streams."""

import asyncio
from collections.abc import AsyncIterable, Iterable
import copy

from . import content_api
from . import context
from . import utils


def split(
    content: AsyncIterable[content_api.ProcessorPart],
    *,
    n: int = 2,
    with_copy: bool = False,
) -> tuple[AsyncIterable[content_api.ProcessorPart], ...]:
  """Split a part stream into `n` identical part streams.

  Recommended to be used with processor.context to ensure error propagation.

  Args:
    content: content to be split
    n: number of streams to return
    with_copy: whether to copy the content parts or not. It is recommended to
      copy the content parts when side effects between streams can happen. This
      is the case when one processor changes a part in place (e.g. update its
      metadata). As this can be expensive if the content parts are large and the
      number of streams is high, the default is to not copy. Consider setting
      this to True if there is a change that a part can be modified in place.

  Returns:
    n streams of content.

  Raises:
    ValueError if n=0
  """
  if n == 0:
    raise ValueError('Cannot split a stream in n=0 streams.')
  if n == 1:
    return (content,)
  queues = [asyncio.Queue() for _ in range(n)]

  async def enqueue() -> None:
    async for part in content:
      for queue in queues:
        if with_copy:
          queue.put_nowait(copy.deepcopy(part))
        else:
          queue.put_nowait(part)
    for queue in queues:
      queue.put_nowait(None)

  async def dequeue(
      queue: asyncio.Queue[content_api.ProcessorPart],
  ) -> AsyncIterable[content_api.ProcessorPart]:
    while (part := await queue.get()) is not None:
      yield part

  context.create_task(enqueue())

  return tuple(dequeue(queue) for queue in queues)


async def concat(
    *contents: AsyncIterable[content_api.ProcessorPart],
) -> AsyncIterable[content_api.ProcessorPart]:
  """Concatenate multiple part streams into one.

  The streams are looped over concurrently before being assembled into a single
  output stream.

  Args:
    *contents: each stream to concat as a separate argument.

  Yields:
    The concatenation of all streams.
  """
  output_queues = [asyncio.Queue() for _ in contents]

  async def _stream_outputs(
      idx: int,
  ):
    async for c in contents[idx]:
      output_queues[idx].put_nowait(c)
    # Adds None to indicate end of output.
    output_queues[idx].put_nowait(None)

  tasks = []
  for idx, _ in enumerate(contents):
    tasks.append(context.create_task(_stream_outputs(idx)))

  for q in output_queues:
    while (part := await q.get()) is not None:
      q.task_done()
      yield part


async def merge(
    streams: Iterable[AsyncIterable[content_api.ProcessorPart]],
    *,
    queue_maxsize: int = 0,
    stop_on_first: bool = False,
) -> AsyncIterable[content_api.ProcessorPart]:
  """Merges multiple streams of ProcessorParts into one.

  The order is defined by the asyncio loop and will likely be determined by the
  time when the parts are available.

  If a stream is cancelled, the overall merge will be cancelled and all other
  streams will be cancelled as well.

  Args:
    streams: The input streams to merge. These streams cannot be iterated over
      outside of this call. If you need to consume them outside of this call,
      use `streams.split()` to copy the stream first.
    queue_maxsize: The maximum number of items to buffer in an internal queue
      for each input stream. Set to 0 to use an unbounded queue.
    stop_on_first: If True, stop merging streams as soon as one of them is
      empty.

  Yields:
    a item from one of the input streams. The order in which the items are
    yielded is random and interleaved (likely order of generation). This means
    the order of the items within one stream is preserved but not across
    streams.
  """
  out = asyncio.Queue(maxsize=queue_maxsize)
  active_streams = 0

  async with asyncio.TaskGroup() as tg:
    running_tasks = []
    for s in streams:
      active_streams += 1
      running_tasks.append(tg.create_task(utils.enqueue(s, out)))

    while active_streams:
      part = await out.get()
      out.task_done()
      if part is None:
        active_streams -= 1
        if stop_on_first:
          break
        continue
      yield part
    for t in running_tasks:
      t.cancel()
