"""Central logging configuration with timestamps and module namespaces."""

import logging
import sys

def configure_bot_logging(log_level: str = "INFO", log_file: str = "trading_bot.log") -> None:
    # DEFECT 6: Missing line number and timestamp in log formatter complicates audit tracing
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)
