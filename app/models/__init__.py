"""Model wrappers.

Each module here loads one model lazily (only when first used) and caches it.
Heavy imports (torch, transformers, faster_whisper) live inside the functions,
not at module top level, so the web app and the test suite can import these
modules without pulling in the multi-gigabyte ML stack.
"""
