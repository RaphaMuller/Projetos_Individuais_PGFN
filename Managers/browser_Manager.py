from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time
import logging

class BrowserManager:
    def __init__(self, headless=False, timeout=10):
        self.timeout = timeout
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.actions = ActionChains(self.driver)

    def _init_driver(self, headless):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options)
    
    def navegar_para_url(self, url: str):
        try:
            self.driver.get(url)
            logging.info(f"Navegação iniciada: {url}")
        except Exception as e:
            msg = (
                f"[ERRO] ao navegar para a URL.\n"
                f"URL: {url}\n"
                f"Erro: {str(e)}"
            )
            logging.error(msg)
            raise type(e)(msg)

    def click(self, seletor: str, by=By.XPATH):
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, seletor)))
            element.click()
        except Exception as e:
            msg = (
                f"[ERRO] ao clicar no elemento.\n"
                f"URL: {self.driver.current_url}\n"
                f"Seletor: {seletor}\n"
                f"Erro: {str(e)}"
            )
            logging.error(msg)
            raise type(e)(msg)

    def write(self, seletor: str, valor: str, by=By.XPATH):
            try:
                element =WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, seletor))
                )
                element.click()
                element.clear()
                element.send_keys(valor)
            except Exception as e:
                msg = (
                    f"[ERRO] ao preencher o campo.\n"
                    f"URL: {self.driver.current_url}\n"
                    f"Seletor: {seletor}\n"
                    f"Erro: {str(e)}"
                )
                logging.error(msg)
                raise type(e)(msg)
            
    def get_text(self, seletor: str, by=By.XPATH):
        try:
            element = self.wait.until(EC.presence_of_element_located((by, seletor)))
            text = element.text
            return text
        except Exception as e:
            msg = (
                f"[ERRO] ao obter texto do seletor.\n"
                f"URL: {self.driver.current_url}\n"
                f"Seletor: {seletor}\n"
                f"Erro: {str(e)}"
            )
            logging.error(msg)
            return ""
            
    def wait_for_element(self, seletor: str, by=By.XPATH, timeout= 5) -> bool:
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, seletor))
            )
            if element:
                return True
        except Exception:
            return False

    def scroll_to_element(self, seletor: str, by=By.XPATH):
        try:
            element = self.wait.until(EC.presence_of_element_located((by, seletor)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

        except Exception as e:
            msg = (
                f"[ERRO] ao centralizar elemento.\n"
                f"URL: {self.driver.current_url}\n"
                f"Seletor: {seletor}\n"
                f"Erro: {str(e)}"
            )
            logging.error(msg)
            raise type(e)(msg)
        
    def await_to_next_url(self, url: str, time_to_wait: float = 10):
        try:
            WebDriverWait(self.driver, time_to_wait).until(EC.url_contains(url))
            return True
        
        except Exception as e:
            msg = (
                f"[ERRO] ao esperar pela URL.\n"
                f"URL esperada: {url}\n"
                f"URL atual: {self.driver.current_url}\n"
                f"Erro: {str(e)}"
            )
            logging.error(msg)
            raise TimeoutError(msg)
        
    def hover_and_click(self, caminho_menus: list[str], tempo_entre_passos=0.5):
        """
        caminho_menus: lista com os textos dos itens do menu em ordem hierárquica.
        Exemplo: ["Processo", "Juntar", "Desapensar"]
        """
        try:
            actions = ActionChains(self.driver)

            for idx, texto in enumerate(caminho_menus):
                # Seleciona o item pelo texto
                xpath = f"//td[contains(@class,'ThemeOffice') and normalize-space(text())='{texto}']"
                elemento = self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))

                # Faz o hover para abrir o submenu
                actions.move_to_element(elemento).perform()
                time.sleep(tempo_entre_passos)  # tempo para submenu abrir

            # Depois do último, clica
            elemento.click()
            return True

        except TimeoutException:
            logging.error(f"Elemento '{caminho_menus}' não encontrado ou não ficou visível.")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao navegar no menu: {str(e)}")
            return False
            
    def fechar_navegador(self):
        try:
            self.driver.quit()
            logging.info("Navegador fechado com sucesso.")
        except Exception as e:
            msg = f"[ERRO] ao fechar navegador: {str(e)}"
            logging.error(msg)