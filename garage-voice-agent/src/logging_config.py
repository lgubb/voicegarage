import logging
import sys


def configure_logging(level: int = logging.INFO, log_detail: str = "normal") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    if log_detail != "debug":
        logging.getLogger("livekit.agents").setLevel(logging.INFO)
