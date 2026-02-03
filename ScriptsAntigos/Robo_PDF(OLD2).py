import os
import shutil
import pandas as pd 
import time

# Utiliza os números dos processos da planilha para localizar e manusear os processos
tabela = pd.read_excel('Processos_conferidos.xlsx')
print(tabela)

df = pd.DataFrame(tabela)

contador = 0
processos_com_erro = []
for numero_processo, nome in zip(df['Processos conferidos'], df['Quem digitalizou']):
    print(f'Processo conferido: {numero_processo}.\nQuem digitalizou: {nome}.')

    caminho_origem = f"L:\Administrativo\Arquivo Físico\Digitalização do Arquivo Físico\Processos Digitalizados\{nome}\{numero_processo}"
    caminho_destino = f"L:\Administrativo\Arquivo Físico\Digitalização do Arquivo Físico\Processos Digitalizados\Raphael Muller\E-Processo\{numero_processo}"

    try:
        # Copia a pasta original com os PDF's e transfere para a pasta destino
        time.sleep(1)
        shutil.copytree(caminho_origem, caminho_destino)

        # Verifica se a pasta foi criada
        if os.path.exists(caminho_destino):
                print('Copia feita com sucesso!')
        else:
                print('Erro, a pasta não foi copiada com sucesso!')
                processos_com_erro.append(numero_processo)
                continue

        # Novo caminho(Nome do processo)

        pdf_Comum = f'{caminho_destino}\{numero_processo}.pdf'
        pdf_Renomeado = f'{caminho_destino}\P{numero_processo}_V1_A0V0_T07-54-369-664_S00001_Livre.pdf'

        # Verifica se o arquivo original existe
        if os.path.exists(pdf_Comum):
                print(f'Arquivo foi encontrado!')
        else: 
                print(f' O arquivo {pdf_Comum}, não foi encontrado!')
                processos_com_erro.append(numero_processo)
                continue

        # Renomeia o Pdf original
        os.rename(pdf_Comum, pdf_Renomeado)

        # Verifica se o processo foi renomeado
        if os.path.exists(pdf_Renomeado):
                contador += 1
                print(f'O arquivo foi renomeado com sucesso para: \P{numero_processo}_V1_A0V0_T07-54-369-664_S00001_Livre.pdf')
        else:
                print(' FALHA AO Renomear processo!')
                processos_com_erro.append(numero_processo)
                continue
    
    except Exception as e:
         print(f'Erro: {e}') 
         
print(f'\nTotal de processos renomeados com sucesso: {contador} de {len(df)}')  

# Verifica se tem algum processo que retornou erro durante a execução
if processos_com_erro:
       print('\n Processos com erro: ')
       for processo in processos_com_erro:
              print(f'- Processo Nº{processo}')
else:
       print(f'\nTodos os processos foram copiados para pasta "L:\Administrativo\Arquivo Físico\Digitalização do Arquivo Físico\Processos Digitalizados\Raphael Muller\E-Processo"')

input("\nPressione ENTER para fechar...")

