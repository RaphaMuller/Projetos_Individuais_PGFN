from Managers.autenticador import GoogleOAUTH
from Managers.controlador_Planilha import ControladorPlanilha
from Managers.controlador_drive import ControladorDrive
from Utils.secrets import Planilhas
from Utils.secrets import Info_login
from Utils.user import User
from Managers.browser_Manager import BrowserManager
from Utils.secrets import Pastas
from datetime import datetime
from Utils.utils import Utilitarios
import os
import logging

# Geração do nome do arquivo de log com data/hora
log_filename = f"log_robo_sida_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log"

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler() 
    ]
)

# Instâncias principais
auth = GoogleOAUTH()
drive = ControladorDrive(auth)
sheets = ControladorPlanilha(auth)
driver = BrowserManager()

cargos_autorizados = ['Tecnico']

def mainSida():

    try:
        logging.info("Iniciando verificação de usuário")
        controleAdm()

        logging.info("Lendo seletores da planilha")
        seletores_sida = Utilitarios.get_seletores(auth,'SELETORES(SIDA)')
        
        logging.info("Lendo processos da planilha de triagem")
        processos = Utilitarios.get_processos(auth, 'Triagem')

        fazerLogin(driver, seletores_sida)

        logging.info("Consultando processos...\n")
        resultado_consulta = consultarProcessos(driver, processos, seletores_sida)

    # Seta planilha Triagem e prepara as situações do processo para update na planilha.
        lista_status = [item['status'] for item in resultado_consulta]
        logging.info("Subindo resultado para o Drive")

        sheets.set_planilha_id(Planilhas.PLANILHA_PROCESSOS_TRIAGEM)
        sheets.set_nome_planilha('Triagem')

        sheets.update_valores_em_coluna(
            valores=lista_status,
            nome_coluna_update='STATUS(SIDA)'
        )
        
    finally:
        logging.info("Finalizando e fechando o navegador")
        driver.fechar_navegador()

    # Subir log para o Drive após execução
        drive.upload_arquivo(
            pasta_destino_id=Pastas.LOGS_ROBOS,
            caminho_arquivo=log_filename,
            nome_arquivo=os.path.basename(log_filename)
        )
    # Subir Relatorios de processos EXTINTOS para o drive
    pasta_local = os.path.expanduser("~/Documents/PDFs_SIDA")

    if not os.path.exists(pasta_local):
        logging.warning(f"Pasta local '{pasta_local}' não encontrada. Nenhum arquivo será enviado.")

    else:
        for nome_arquivo in os.listdir(pasta_local):
            caminho_arquivo = os.path.join(pasta_local, nome_arquivo)

            if os.path.isfile(caminho_arquivo):
                drive.upload_arquivo(
                    pasta_destino_id=Pastas.PROCESSOS_EXTINTOS_SIDA,
                    caminho_arquivo=caminho_arquivo,
                    nome_arquivo=nome_arquivo
                )

#Faz verificação de cadastra na planilha de controle
def controleAdm():
    usuario = User(auth)

    if usuario.perfil not in cargos_autorizados:
        logging.error(f"Acesso negado: cargo '{usuario.perfil}' sem permissão")
        raise PermissionError(f'Acesso negado:\n O cargo {usuario.perfil} não tem permissão para executar essa automação')
    logging.info(f'Acesso liberado para {usuario.perfil}, executando robô...\n')

#Faz login no SIDA
def fazerLogin(driver: BrowserManager, seletores_sida: dict):
    try:
        logging.info("Abrindo página de login")
        driver.navegar_para_url('https://sida.pgfn.fazenda/sida/#/sida/login')

        driver.write(seletores_sida['CPF'], Info_login.login['LOGIN'])
        driver.write(seletores_sida['LOGIN'], Info_login.login['PASSWORD'])
        driver.click(seletores_sida['BUTTON_LOGIN'])

        next_page = driver.await_to_next_url(url='https://sida.pgfn.fazenda/sida/#/sida/consulta/busca', time_to_wait=20)
        if next_page:
            logging.info("Login feito com sucesso!\n")
    except Exception as e:
        logging.error(f"Erro na tentativa de fazer login: {e}")

# Consulta processos da planilha triagem a partir de 3 verificações
def consultarProcessos(driver: BrowserManager, processos, seletores_sida: dict):
    resultados = []

    for numero_processo in processos:
        try:
            logging.info(f'Iniciando consulta do processo Nº - {numero_processo}')
            try:
                driver.click(seletores_sida['SELETOR_PROCESSO_ADM'])
                driver.write(seletores_sida['SELETOR_NUM_PROCESSO'], numero_processo)
                driver.click(seletores_sida['BUTTON_SEARCH'])
                logging.info(f'Processo Nº - {numero_processo} pesquisado com sucesso')
            except Exception as e:
                logging.error(f'Erro ao tentar escrever número do processo na barra de pesquisa: {e}')
                return

            resultado_cadastro = verificarProcessoNaoCadastrado(driver, numero_processo, seletores_sida)
            if resultado_cadastro:
                resultados.append(resultado_cadastro)
                continue

            resultado_inscricao = consultarInscricoes(driver, numero_processo, seletores_sida)
            if resultado_inscricao:
                resultados.append(resultado_inscricao)
                continue

            resultado_consulta_rapida = consultaRapida(driver, numero_processo, seletores_sida)
            if resultado_consulta_rapida is not None:
                logging.info('Consulta rápida finalizada\n')
                resultados.append(resultado_consulta_rapida)

        except Exception as e:
            logging.error(f'Erro durante a consulta do processo Nº - {numero_processo}: {e}')
            continue
        
    return resultados

# Verificação 1, se estiver cadastrado e com apenas uma inscrição, pega o status(situação)
def consultaRapida(driver: BrowserManager, numero_processo, seletores_sida: dict):
    try:
        situacao = driver.get_text(seletores_sida['SITUACAO'])

        dados = {
                'processo': numero_processo,
                'status': situacao
            }
        logging.info(f'Processo Nº - {numero_processo} está {situacao}')

        #Se extinto, tenta baixar Relatorio
        baixar_pdf_se_extinto(driver, seletores_sida, numero_processo, situacao)
        button_visivel = driver.wait_for_element(seletores_sida['BUTTON_VOLTAR'])
        if button_visivel:
            driver.click(seletores_sida['BUTTON_VOLTAR'])

        return dados

    except Exception as e:
        logging.warning(f"[ERRO] Falha ao consultar situação do processo {numero_processo}: {e}")
        return None
    
# Verificação 2, se estiver cadastrado e tiver muitas incrisções, retorna "Muitas inscrisções"
def consultarInscricoes(driver: BrowserManager, numero_processo, seletores_sida: dict):
    try:
        inscricoes = driver.wait_for_element(seletores_sida['ALERT_INSCRICOES'], timeout=2)
        if inscricoes:
            logging.info(f'Processo Nº - {numero_processo} com múltiplas inscrições.')
            dados = {
                'processo': numero_processo,
                'status': 'Várias inscrições'
            }
            driver.click(seletores_sida['BUTTON_VOLTAR_INSC'])
            return dados
        
    except Exception:
        logging.info(f'Processo Nº - {numero_processo} possui apenas uma inscrição.')
        return None

# Verificação 3, se não estiver cadastrado, retorna sem cadastro.
def verificarProcessoNaoCadastrado(driver: BrowserManager, numero_processo, seletores_sida: dict):
    try:
        processo_nao_cadastrado = driver.wait_for_element(seletores_sida['ALERT_PROCESSO_NAO_CADASTRADO'], timeout= 2)
        if processo_nao_cadastrado:
            logging.info(f'Processo Nº - {numero_processo} não tem cadastro no SIDA')
            return {
                'numeroProcesso': numero_processo,
                'status': 'Sem cadastro no SIDA'
            }
    except Exception:
        logging.info(f'Processo Nº - {numero_processo} possui cadastro no SIDA!')
        return None

# Compelemento para consulta rapida.
# Caso o processo esteja extinto, baixa o relatorio completo e envia para uma pasta no drive.
def baixar_pdf_se_extinto(driver: BrowserManager, seletores_sida: dict, numero_processo: str, situacao: str) -> bool:
    palavras_chave = ['EXTINTA', 'EXTINTO']

    if any(palavra in situacao.upper() for palavra in palavras_chave):
        try:
            if driver.wait_for_element(seletores_sida['IMPRIMIR_EXTINTO']):
                driver.click(seletores_sida['IMPRIMIR_EXTINTO'])

            if driver.wait_for_element(seletores_sida['CONFIRMA_IMPRESSAO']):
                driver.click(seletores_sida['CONFIRMA_IMPRESSAO'])

            pasta_destino = os.path.join(os.path.expanduser("~/Documents"), "PDFs_SIDA")

            Utilitarios.renomear_arquivo_mais_recente(
                novo_nome=f'{numero_processo}_EXTINTO',
                extensao="pdf",
                pasta_destino=pasta_destino
            )
            logging.info(f"PDF baixado e renomeado para processo {numero_processo}")
            return True
        except Exception as e:
            logging.error(f"Erro ao tentar baixar PDF para {numero_processo}: {e}")
            return False
    return False

if __name__ == '__main__':
    mainSida()
