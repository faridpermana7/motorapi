from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class DailyFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        directory: str,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        backupCount: int = 0,
        encoding: str = "utf-8",
    ):
        log_directory = Path(__file__).resolve().parent.parent / directory
        log_directory.mkdir(parents=True, exist_ok=True)
        super().__init__(
            log_directory / filename,
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding,
        )
