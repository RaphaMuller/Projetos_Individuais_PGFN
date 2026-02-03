from googleapiclient.errors import HttpError
from Managers.autenticador import GoogleOAUTH
import logging

class ControladorPlanilha:
    def __init__(self, autenticador: GoogleOAUTH, planilha_id = '_', planilha_nome = '_'):
        self.planilha_id = planilha_id
        self.planilha_nome = planilha_nome
        self.aunteticador_planilhas = autenticador.get_oauth2_sheets()

    def set_planilha_id(self, new_id: str):
        self.planilha_id = new_id

    def set_nome_planilha(self, new_name: str):
        self.planilha_nome = new_name

    def get_nome_planilha(self):
        try:
            response = (
                self.aunteticador_planilhas
                .get(planilha_id = self.planilha_id)
                .execute()
                )
            
            planilhas = response.get("planilhas", [])

            for planilha in planilhas:
                properties = planilha.get("properties", {})
                title = properties.get("title", "")
                planilha_id = properties.get("planilhaId", 0)
                if title == self.planilha_nome:
                    return planilha_id
                raise ValueError(f"[ERRO] Aba '{self.planilha_nome}'\
                                 não encontrada na planilha: '{self.planilha_id}'")
        except HttpError as error:
            raise ValueError(f'[ERRO] na tentativa de encontrar ID da planilha: {error}') from error
        
    def read_to_json(self):
        if self.planilha_id == '_' or self.planilha_nome == '_':
            raise ValueError('[ERRO] na referência de valores para Id da planilha e Nome da planilha')

        for _ in range(3):
            try:
                result = (
                    self.aunteticador_planilhas
                    .spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=self.planilha_id,
                        range=self.planilha_nome
                    )
                    .execute()
                )

                values = result.get("values", [])
                if not values:
                    return []

                header = values[0]
                dados = values[1:]

                result_json = []
                for row in dados:
                    while len(row) < len(header):
                        row.append("")
                    result_json.append(dict(zip(header, row)))

                return result_json

            except HttpError as error:
                print(f"Tentativa falhou: {error}")
        raise ValueError("[ERRO] ao ler os dados da planilha após 3 tentativas")

  
    
    def clear_columns(self, letra_colunas: list[str], linha_inicial = 2, linha_final=None):
        if self.planilha_id == '_' or self.planilha_nome == '_':
            raise ValueError('[ERRO] ID ou nome da planilha não definidos corretamente.')
            
        try: 

            for coluna in letra_colunas:
                range_coluna = f'{self.planilha_nome}!{coluna}{linha_inicial}:{coluna}{linha_final or ""}'

                logging.info(f'Limpando coluna: {coluna}')

                request = (self.aunteticador_planilhas
                        .spreadsheets()
                        .values()
                        .clear(
                            spreadsheetId=self.planilha_id, 
                            range=range_coluna
                ))
                request.execute()
                logging.info(f'Colunas: {letra_colunas} limpa com sucesso.')
            return True

        except Exception as e:
            logging.error(f'[ERRO] ao tentar fazer a limpeza das coluna: {letra_colunas}: {e}')
            return False

    def find_columns(self, nome_colunas: list[str]):
        if self.planilha_id == '_' or self.planilha_nome == '_':
            raise ValueError('[ERRO] ID ou nome da planilha não definidos corretamente.')
        
        try:
            valores = self.aunteticador_planilhas.spreadsheets().values().get(
                spreadsheetId=self.planilha_id,
                range='A1:1',
                valueRenderOption='FORMULA'
            ).execute().get('values', [])

            if not valores or not valores[0]:
                raise ValueError('[ERRO] Cabeçalho da planilha vazio ou não encontrado')
            
            header = valores[0]

            if isinstance(nome_colunas, str):
                nome_colunas = [nome_colunas]

            result = []
            for nome in nome_colunas:
                if nome not in header:
                    raise ValueError(f"[ERRO] Nome: {nome} não encontrado no cabeçalho: {header}")
                
                indice = header.index(nome)
                letra_coluna = chr(ord('A') + indice)  
                result.append(letra_coluna)

            #Retorna o valor em list das colunas selecionadas ou coluna selecionada    
            logging.info(f'Colunas: {nome_colunas} encontradas')
            return result
        
        except Exception as e:
            raise RuntimeError(f"[ERRO] ao buscar coluna: {str(e)}")
        
    def batch_update(self, nome_colunas: list[str], valores_por_coluna: dict[str, list[str]], linha_inicial=2):
        """
        Atualiza em lote as colunas especificadas de uma planilha do Google Sheets.
        
        Args:
            nome_colunas: Lista com os nomes das colunas a serem atualizadas
            valores_por_coluna: Dicionário onde as chaves são nomes de colunas e os valores são listas de valores
            linha_inicial: Linha onde começar a atualização (padrão é 2)
        """
        if self.planilha_id == '_' or self.planilha_nome == '_':
            raise ValueError('[ERRO] ID ou nome da planilha não definidos corretamente.')
        
        # Encontrar as colunas
        colunas = self.find_columns(nome_colunas)
        if not colunas:
            error_msg = f'[ERRO] Não foi possível encontrar as colunas: {nome_colunas}'
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Limpar as colunas
        clear_ranges = [f"{self.planilha_nome}!{col}{linha_inicial}:{col}" for col in colunas]
        logging.info(f'Limpando as colunas: {nome_colunas}')

        # Tentar limpar as colunas (até 3 tentativas)
        for i in range(3):
            try:
                clear_request = self.autenticador_planilhas.spreadsheets().values().batchClear(
                    spreadsheetId=self.planilha_id,
                    body={"ranges": clear_ranges}
                )
                clear_request.execute()
                logging.info('Limpeza das colunas concluída.')
                break
            except HttpError as error:
                logging.error(f'[ERRO] Não foi possível limpar as colunas (tentativa {i+1}/3): {error}')
                if i == 2:  # Última tentativa
                    raise

        # Verificar se há valores para adicionar
        if not valores_por_coluna:
            logging.info('Sem valores para adicionar nas colunas... Pulando etapa de update.')
            return  # Retorna em vez de levantar exceção

        # Preparar dados para atualização
        dados = []
        for nome, col in zip(nome_colunas, colunas):
            valores = valores_por_coluna.get(nome, [])
            if valores:  # Verifica se a lista não está vazia
                dados.append({
                    "range": f'{self.planilha_nome}!{col}{linha_inicial}:{col}{linha_inicial + len(valores) - 1}',
                    "values": [[v] for v in valores if v]
                })

        # Executar atualização
        try:
            update_request = self.autenticador_planilhas.spreadsheets().values().batchUpdate(
                spreadsheetId=self.planilha_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": dados
                }
            )
            resultado = update_request.execute()
            logging.info(f'Valores adicionados à planilha: {self.planilha_id}')
            return resultado
            
        except HttpError as error:
            logging.error(f'[ERRO] Falha ao atualizar planilha: {error}')
            raise