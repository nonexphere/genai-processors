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
"""Small utils for helping with processors."""

import asyncio
from collections.abc import AsyncIterable, AsyncIterator, Iterable
from typing import Generic, TypeVar

_T = TypeVar('_T')

# TODO(kpsawhney): merge with streams.py and make streams.py generic.


async def stream_content(
    content: Iterable[_T],
    with_delay_sec: float | None = None,
    delay_first: bool = False,
    delay_end: bool = True,
) -> AsyncIterable[_T]:
  """Converts non-async content into an AsyncIterable.

  Args:
    content: the items to yield. The state of the iterator provided by `content`
      is undefined post-invocation and should not be relied on.
    with_delay_sec: If set, asyncio.sleep() is called with this value between
      yielding parts, and optionally also before and after.
    delay_first: If set to True, a delay is added before the first part.
    delay_end: Unless set to False, a delay is added between the last part and
      stopping the returned AsyncIterator.

  Yields:
    an item in `content` (unchanged).
  """
  # Getting the next value from content must not block. For this reason
  # this function doesn't work for generators.
  delay_next = with_delay_sec is not None and delay_first
  for c in content:
    if delay_next:
      await asyncio.sleep(with_delay_sec)
    else:
      delay_next = with_delay_sec is not None  # From the 2nd iteration onwards.
    yield c
  if with_delay_sec is not None and delay_end:
    await asyncio.sleep(with_delay_sec)


async def gather_stream(content: AsyncIterable[_T]) -> list[_T]:
  """Gathers an AsyncIterable into a list of items."""
  return [c async for c in content]


async def aenumerate(
    aiterable: AsyncIterable[_T],
) -> AsyncIterable[tuple[int, _T]]:
  """Enumerate an async iterable."""
  i = 0
  async for x in aiterable:
    yield (i, x)
    i += 1


async def enqueue(
    content: AsyncIterable[_T], queue: asyncio.Queue[_T | None]
) -> None:
  """Enqueues all content into a queue.

  When the queue is unbounded, this function will not block. When the queue is
  bounded, this function will block until the queue has space.

  Args:
    content: The content to enqueue.
    queue: The queue to enqueue to.
  """
  try:
    async for part in content:
      await queue.put(part)
  finally:
    await queue.put(None)


async def dequeue(queue: asyncio.Queue[_T | None]) -> AsyncIterable[_T]:
  while (part := await queue.get()) is not None:
    queue.task_done()
    yield part
  queue.task_done()


class PeekableAsyncIterator(Generic[_T], AsyncIterator[_T]):
  """An async iterator that allows peeking at the next item."""

  def __init__(self, delegate: AsyncIterator[_T]):
    self.delegate = delegate
    self.peeked = False
    self.peeked_item: _T | None = None

  async def peek(self) -> _T | None:
    """Peeks at the next item without advancing the iterator.

    Returns:
      The next item, or None if the iterator is exhausted.
    """
    if not self.peeked:
      try:
        self.peeked_item = await self.delegate.__anext__()
        self.peeked = True
      except StopAsyncIteration:
        return None
    return self.peeked_item

  async def __anext__(self) -> _T:
    if self.peeked:
      self.peeked = False
      return self.peeked_item
    return await self.delegate.__anext__()

  def __aiter__(self) -> AsyncIterator[_T]:
    return self
