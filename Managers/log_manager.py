import logging
import sys
import time
from pathlib import Path 

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",   # Azul
        "INFO": "\033[37m",    # Branco
        "WARNING": "\033[93m", # Amarelo
        "ERROR": "\033[91m",   # Vermelho
        "CRITICAL": "\033[95m" # Roxo
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        log_message = super().format(record)
        return f"{log_color}{log_message}{self.RESET}"

class Logger:
    def __init__(self, log_filename, name="AppLogger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Cria os diretórios necessários
        log_path = Path(log_filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Evita adicionar handlers duplicados
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_filename, mode="w", encoding="utf-8")
            console_handler = logging.StreamHandler(sys.stdout)

            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            color_formatter = ColorFormatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            file_handler.setFormatter(formatter)
            console_handler.setFormatter(color_formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
    
    def write_logger(self, filename, text_box):
        self.logger.debug("=== INICIANDO MONITORAMENTO EM TEMPO REAL ===")
        self.logger.debug("(Aguardando novas entradas...)")
    
        # Agora monitora novas entradas
        with open(filename, "r", encoding="utf-8") as f:
            # Vai para o final do arquivo
            f.seek(0, 2)
            
            while True:
                line = f.readline().rstrip()
                if line:
                    text_box.after(0, lambda txt=line: self._insert_line(text_box, txt))
                else:
                    self.logger.info(line.rstrip())
                    time.sleep(0.2)