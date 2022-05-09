"""
This module contains shared fixtures, steps, and hooks.
"""

import pytest
import asyncio


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()