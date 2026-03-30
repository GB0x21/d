import logging
import sys


def setup_logger(level: str = "INFO") -> logging.Logger:
    root = logging.getLogger("pennybot")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not root.handlers:
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)

        file_handler = logging.FileHandler("pennybot.log")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)

    return root
