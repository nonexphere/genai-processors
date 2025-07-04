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

"""Command line interface for PDF processor.

Usage:
  python3 pdf_cli.py <pdf_file>

Requires a PDF file to be passed as argument.

This will print the parts extracted by pdf.PDFExtract to stdout.
"""
import argparse
import asyncio
import time

from genai_processors import content_api
from genai_processors.core import pdf


async def run_pdf(content: bytes, filename: str) -> None:
  """Extracts PDF content."""
  p = pdf.PDFExtract()
  metadata = {'original_file_name': filename}
  async for part in p(
      content_api.ProcessorPart(
          content, mimetype=pdf.PDF_MIMETYPE, metadata=metadata
      )
  ):
    print(f'{time.perf_counter()} - {part}')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('pdf_file')
  args = parser.parse_args()
  pdf_file = args.pdf_file
  with open(pdf_file, 'rb') as f:
    pdf_bytes = f.read()
    print(
        f'{time.perf_counter()} - PDF Processor start extracting PDF:'
        f' {pdf_file}'
    )
    asyncio.run(run_pdf(content=pdf_bytes, filename=pdf_file))
