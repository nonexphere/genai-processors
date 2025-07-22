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

"""Leonidas v2 CLI - Command Line Interface for the refactored agent

This CLI provides a simple way to run the new modular Leonidas v2 agent
with improved conversation flow and tool-based intelligence.

Usage:
    python leonidas/leonidas_cli.py --mode camera
    python leonidas/leonidas_cli.py --mode screen --debug
"""

import argparse
import asyncio
import os
import sys

from absl import logging
from genai_processors.core import text
import leonidas

def main():
    """Main CLI entry point."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Leonidas v2 - Modular Conversational AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Run in audio-only mode
  %(prog)s --video-mode camera        # Use camera input
  %(prog)s --video-mode screen        # Use screen capture
  %(prog)s --video-mode camera --debug # Enable debug logging
  
Requirements:
  - Set GOOGLE_API_KEY environment variable
  - Install: pip install genai-processors pyaudio
  - Use headphones to prevent audio feedback
        """
    )
    
    parser.add_argument(
        '--video-mode',
        type=str,
        choices=['camera', 'screen'],
        default=None,
        help='Enable video input mode: camera for webcam, screen for screen capture. Disabled by default.'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for troubleshooting'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='Google AI API key (overrides GOOGLE_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.set_verbosity(logging.DEBUG)
        print("Debug logging enabled")
    else:
        logging.set_verbosity(logging.INFO)
    
    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: Google AI API key not found!")
        print("   Set GOOGLE_API_KEY environment variable or use --api-key")
        print("   Get your key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    # Display startup information
    print("=" * 60)
    print("Leonidas v2 - Conversational AI Agent")
    print("=" * 60)
    print(f"Video Mode: {args.video_mode if args.video_mode else 'Disabled'}")
    print(f"Audio: Enabled (use headphones recommended)")
    print(f"Model: gemini-live-2.5-flash-preview")
    print(f"Language: Portuguese Brazilian")
    print(f"Architecture: Modular (InputManager → Orchestrator → OutputManager)")
    print("=" * 60)
    print("Tips:")
    print("   • Speak naturally - Leonidas will think before responding")
    print("   • The agent can change its own behavior based on context")
    print("   • Use Ctrl+C to exit gracefully")
    print("   • Check console for thinking process and state changes")
    print("=" * 60)
    
    try:
        # Run the agent
        print("Starting Leonidas v2...")
        asyncio.run(leonidas.run_leonidas(api_key, args.video_mode))
        
    except KeyboardInterrupt:
        print("\nLeonidas v2 shutdown requested by user")
        print("   Session ended gracefully")
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("   Install required packages: pip install genai-processors pyaudio")
        sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print("   Use --debug flag for detailed error information")
        sys.exit(1)


if __name__ == '__main__':
    main()
