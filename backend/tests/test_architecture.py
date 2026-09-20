"""Guards the MVP's core architectural rule: yfinance stays isolated."""

from pathlib import Path

APP_ROOT = Path(__file__).parents[1] / "app"
ALLOWED_YFINANCE_FILE = APP_ROOT / "providers" / "yfinance_provider.py"


def test_only_yfinance_provider_imports_yfinance():
    offenders = []
    for path in APP_ROOT.rglob("*.py"):
        if path == ALLOWED_YFINANCE_FILE:
            continue
        text = path.read_text()
        if "import yfinance" in text or "from yfinance" in text:
            offenders.append(str(path))

    assert offenders == []
