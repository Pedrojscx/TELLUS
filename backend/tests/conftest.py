from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def dir_referencias() -> Path:
    return RAIZ / "referencias" / "localizacao"
