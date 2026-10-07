import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_ROOT_NAME = "landaudit"


def _get_log_dir():
    """Папка logs/ поруч із проєктом (або поруч із exe після збірки PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _setup():
    root = logging.getLogger(_ROOT_NAME)
    if root.handlers:  # Streamlit перевиконує скрипт — не дублюємо обробники
        return
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(_get_log_dir(), "app.log"),
        maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)


def get_logger(name):
    _setup()
    return logging.getLogger(f"{_ROOT_NAME}.{name}")
