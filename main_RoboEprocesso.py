import os
from datetime import datetime
from Managers.autenticador import GoogleOAUTH
from Managers.controlador_Planilha import ControladorPlanilha
from Managers.controlador_drive import ControladorDrive
from Managers.log_manager import Logger
from Utils.secrets import Planilhas
from Utils.secrets import Pastas
from Utils.user import User

# Gerar nome do log com data/hora
log_filename = f"LogRoboPDF_{datetime.now().strftime('%Y/%m/%d')}.log"
log = Logger(f"{log_filename}", name='Robo E-Processo').get_logger()

# Instâncias principais
auth = GoogleOAUTH()
drive = ControladorDrive(auth)
sheets = ControladorPlanilha(auth)

cargos_autorizados = ['Tecnico']

def mainRobo_PDF():

    log.debug('\nINICIANDO TELA DE MONITORAMENTO DO ROBO\n')
    log.info("\nIniciando execução do robô de renomeação e movimentação de PDFs\n")
    controleAdm()

    # Faz a leitura da planilha com os processos a serem renomeados e seus digitalizadores.
    planilha_processos = ControladorPlanilha(
        autenticador=auth,
        planilha_id=Planilhas.RENOMEAR_PROCESSOS,
        planilha_nome='Processos_Para_Renomear'
    )

    dados = planilha_processos.read_to_json()
    log.info(f'Total de processos encontrados: {len(dados)}')

    processos_conferidos = [
        (p['PROCESSOS CONFERIDOS'].strip(),
         p['QUEM DIGITALIZOU?'].strip())
        for p in dados
    ]

    log.info(f'\nProcessos a serem modificados: {processos_conferidos}\n')
    executar_fluxo_drive(processos_conferidos, drive)

    # Subir log para o Drive após execução
    drive.upload_arquivo(
        pasta_destino_id=Pastas.LOGS_ROBOS,
        caminho_arquivo=log_filename,
        nome_arquivo=os.path.basename(log_filename)
    )

def controleAdm():
    usuario = User(auth)
    if usuario.perfil not in cargos_autorizados:
        raise PermissionError(f'Acesso negado: Cargo {usuario.perfil} não tem permissão para executar essa automação')

    log.info(f'Acesso liberado para {usuario.perfil}, executando robô...')

# Pega os ID's das pastas dos digitalizadores
def get_pasta_id(digitalizador):
    digitalizadores = Pastas.PASTAS_DIGITALIZADORES
    digitalizador_normalizado = digitalizador.strip().lower()

    if digitalizador_normalizado in digitalizadores:
        id_pasta = digitalizadores[digitalizador_normalizado]
        log.info(f"ID da pasta do digitalizador '{digitalizador}' encontrado: {id_pasta}")
        return id_pasta
    else:
        log.warning(f"[AVISO] Digitalizador '{digitalizador}' não encontrado.")
        return None

def limpeza_processos(processos_com_erro):
    # Extrair listas de processos e digitalizadores
    lista_processos = [item['processo'] for item in processos_com_erro]
    lista_digitalizadores = [item['digitalizador'] for item in processos_com_erro]

    # Log dos erros encontrados
    if processos_com_erro:
        log.warning("⚠️ Processos com erro:\n")
        for p in processos_com_erro:
            log.warning(
                f"Processo Nº - {p['processo']} | "
                f"Digitalizador: {p['digitalizador']} | "
                f"Erro: {p['erro']}\n"
            )
        log.info(f'Processos com erro voltando para planilha.')
    else:
        log.info('Nenhum processo com erro. Limpando planilha...')

    # Configura planilha
    sheets.set_planilha_id(Planilhas.RENOMEAR_PROCESSOS)
    sheets.set_nome_planilha('Processos_Para_Renomear')

    # Usa batchUpdate genérico (já faz clear + insert em uma chamada)
    sheets.batch_update(
        nome_colunas=["PROCESSOS CONFERIDOS", "QUEM DIGITALIZOU?"],
        valores_por_coluna={
            "PROCESSOS CONFERIDOS": lista_processos,
            "QUEM DIGITALIZOU?": lista_digitalizadores
        },
        linha_inicial=2
        )

def executar_fluxo_drive(processos_conferidos, drive: ControladorDrive):
    processos_com_erro = []
    contador = 0
    try:
        # Lista todas as subpastas dentro da pasta EProcesso
        pastas_existentes = drive.listar_arquivos(Pastas.EProcesso)

        # Conta quantas pastas existem com o prefixo "Lote - "
        num_lotes = sum(
            1 for item in pastas_existentes
            if item.get('mimeType') == 'application/vnd.google-apps.folder' and item.get('name', '').startswith('Lote - ')
        )
        # Cria a nova pasta com o próximo número
        pasta_lote = f"Lote - {num_lotes + 1} - {datetime.now().strftime('%d-%m-%Y - %H:%M')}" 
        lote_id = drive.criar_pasta(pasta_lote, pasta_pai_id=Pastas.EProcesso)

        if lote_id:
            log.info(f"Pasta '{pasta_lote}' criada com sucesso! ID: {lote_id}")

    except FileNotFoundError:
        log.error(f'Não foi possivel criar a pasta {pasta_lote}')
        return

    for numero_processo, digitalizador in processos_conferidos:
        try:
            log.info(f"🔄 Iniciando fluxo para processo {numero_processo}\n")
            pasta_digitalizador_id = get_pasta_id(digitalizador)

            # Verifica se o digitalizador tem pasta cadastrada.
            if not pasta_digitalizador_id:
                msg = f'[AVISO] Processo: Nº - {numero_processo} sem ID de pasta de origem'
                log.error(f'\n{msg}\n')
                processos_com_erro.append({
                    'processo': numero_processo,
                    'digitalizador': digitalizador,
                    'erro': msg
                })
                continue

            # Verifica por nome se a pasta(numero_processo) existe dentro da pasta do digitalizador.
            pasta_origem = drive.buscar_pasta_por_nome(numero_processo, pasta_pai_id=pasta_digitalizador_id)
            if not pasta_origem:
                msg = f"[AVISO] Pasta do processo: Nº - {numero_processo} não encontrada."
                log.error(f"{msg}\n")
                processos_com_erro.append({
                    'processo': numero_processo,
                    'digitalizador': digitalizador,
                    'erro': msg
                })
                continue

            # Verifica se foi criado a pasta destino existe.
            pasta_destino_id = drive.criar_pasta(numero_processo, pasta_pai_id=lote_id)
            if not pasta_destino_id:
                msg = f"[AVISO] Não foi possível criar pasta de destino para o processo: Nº - {numero_processo}"
                log.error(f"{msg}\n")
                processos_com_erro.append({
                    'processo': numero_processo,
                    'digitalizador': digitalizador,
                    'erro': msg
                })
                continue
            
            # Verifica se existe algum arquivo dentro da pasta(numero_processo).
            arquivos = drive.listar_arquivos(pasta_origem['id'])
            if not arquivos:
                msg = f"[AVISO] Nenhum arquivo encontrado na pasta do processo: Nº - {numero_processo}"
                log.warning(f"{msg}\n")
                processos_com_erro.append({
                    'processo': numero_processo,
                    'digitalizador': digitalizador,
                    'erro': msg
                })
                continue

            # Para cada arquivo .pdf ou .tif com nome (numero_processo).
            # Copia para a pasta destino e renomeia.
            for arquivo in arquivos:
                try:
                    novo_arquivo_id = drive.copiar_arquivo(arquivo['id'], parents=[pasta_destino_id])

                    if arquivo['name'].strip() == f'{numero_processo}.pdf' or arquivo['name'].strip() == f'{numero_processo}.tif':
                        novo_nome = f'P{numero_processo}_V1_A0V0_T07-54-369-664_S00001_Livre.pdf'
                        drive.renomear_arquivo(novo_arquivo_id, novo_nome)

                except Exception as e:
                    msg = f"[ERRO] Falha ao copiar/renomear arquivo {arquivo['name']} do processo {numero_processo}"
                    log.error(f"{msg}\nErro: {str(e)}")
                    processos_com_erro.append({
                            'processo': numero_processo,
                            'digitalizador': digitalizador,
                            'erro': msg
                        })
                    continue

            log.info(f"[OK] Processo {numero_processo} copiado e arquivos renomeados.\n")
            contador += 1

        except Exception as e:
            msg = f"[ERRO] Erro inesperado ao processar o processo {numero_processo}"
            log.error(f"{msg}\nErro: {str(e)}")
            processos_com_erro.append({
                'processo': numero_processo,
                'digitalizador': digitalizador,
                'erro': msg
            })
            continue

    try:
        
        limpeza = limpeza_processos(processos_com_erro)    
        if limpeza:
            log.info(f"\nTotal de processos finalizados com sucesso: {contador} de {len(processos_conferidos)}")

    except Exception as e:
        log.error(f"[ERRO] Não foi possível finalizar a limpeza dos processos\nErro: {str(e)}")

if __name__ == "__main__":
    mainRobo_PDF()
