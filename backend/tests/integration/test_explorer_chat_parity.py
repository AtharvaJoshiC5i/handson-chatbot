"""Explorer parity tests — disabled after simplified chat scope."""

import pytest

pytestmark = pytest.mark.skip(
    reason="Database explorer and granular list intents were removed.",
)
