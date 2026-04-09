#!/usr/bin/env python3
"""Backward-compatible wrapper for the research slab generation script."""

import asyncio

from research.generate_slabs import main


if __name__ == "__main__":
    asyncio.run(main())
