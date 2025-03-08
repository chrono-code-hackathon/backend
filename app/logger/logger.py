import logging
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

class CustomFormatter(logging.Formatter):

    grey = Style.DIM + Fore.WHITE
    green = Fore.GREEN
    yellow = Fore.YELLOW
    red = Fore.RED
    bold_red = Back.RED + Fore.WHITE
    reset = Style.RESET_ALL
    format_str = '%(asctime)s - %(name)s - %(levelprefix)s%(message)s'

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def __init__(self):
        super().__init__(fmt=self.format_str, datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        record.levelprefix = f'{record.levelname}: '
        return formatter.format(record)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Add formatter to ch
ch.setFormatter(CustomFormatter())

# Add ch to logger
logger.addHandler(ch)
