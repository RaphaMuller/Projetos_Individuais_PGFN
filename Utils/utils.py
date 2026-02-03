import os
import time
import glob
import shutil
import logging
from Managers.autenticador import GoogleOAUTH
from Managers.controlador_Planilha import ControladorPlanilha
from Utils.secrets import Planilhas

class Utilitarios:

    @staticmethod
    def renomear_arquivo_mais_recente(
        novo_nome: str,
        extensao: str = "pdf",
        pasta_origem: str = os.path.expanduser("~/Downloads"),
        pasta_destino: str = "",
        esperar_download: bool = True,
        timeout: int = 10
    ) -> str | None:

        try:
            tempo_esperado = 0
            padrao_busca = os.path.join(pasta_origem, f"*.{extensao}")

            while esperar_download and tempo_esperado < timeout:
                arquivos = glob.glob(padrao_busca)
                if arquivos:
                    arquivo_recente = max(arquivos, key=os.path.getctime)
                    if not arquivo_recente.endswith(".crdownload"):
                        break
                time.sleep(1)
                tempo_esperado += 1
            else:
                raise TimeoutError(f"Nenhum arquivo '.{extensao}' pronto foi encontrado em '{pasta_origem}'.")

            # Adiciona extensão se necessário
            if not novo_nome.lower().endswith(f".{extensao.lower()}"):
                novo_nome += f".{extensao}"

            # Cria pasta destino se necessário
            if pasta_destino and not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino, exist_ok=True)

            destino_final = os.path.join(pasta_destino or pasta_origem, novo_nome)

            # Renomeia/move o arquivo
            shutil.move(arquivo_recente, destino_final)
            logging.info(f"Arquivo renomeado para: {destino_final}")
            return destino_final

        except Exception as e:
            logging.error(f"[ERRO] ao renomear arquivo: {str(e)}")
            return None

    @staticmethod
    def get_seletores(auth: GoogleOAUTH, planilha_nome_aba: str ):
            
        planilha_seletores = ControladorPlanilha(
            autenticador=auth,
            planilha_id=Planilhas.PLANILHA_SELETORES,
            planilha_nome= planilha_nome_aba
        )
        lista_seletores = planilha_seletores.read_to_json()
        seletores = {linha['SELETORES']: linha['ID'] for linha in lista_seletores}
        return seletores

    @staticmethod
    def get_processos(auth: GoogleOAUTH, planilha_nome_aba: str):
        processos_triagem = ControladorPlanilha(
            autenticador=auth,
            planilha_id=Planilhas.PLANILHA_PROCESSOS_TRIAGEM,
            planilha_nome= planilha_nome_aba
        )
        planilha_processos = processos_triagem.read_to_json()
        processos = [p['PROCESSOS'] for p in planilha_processos]
        return processos
    