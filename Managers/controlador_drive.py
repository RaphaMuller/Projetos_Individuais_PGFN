from Managers.autenticador import GoogleOAUTH
from googleapiclient.http import MediaFileUpload
import logging

class ControladorDrive:
    def __init__(self, autenticador = GoogleOAUTH):
        self.drive = autenticador.get_oauth2_drive()

    def buscar_arquivo_por_nome(self, nome_arquivo: str, pasta_id: str = None) -> dict:
        """Busca um arquivo por nome e opcionalmente por pasta"""
        if not nome_arquivo:
            raise ValueError("É necessario fornecer o nome do arquivo para realizar a busca.")

        query = f"name = '{nome_arquivo}' and trashed = false"

        if pasta_id:
            query += f"and '{pasta_id}' in parents"

        try:
            resultados = self.drive.files().list(
                q = query,
                spaces = "drive",
                fields= "files(id, name, mimeType, parents)",
                pageSize = 1,
                ).execute()

            arquivos = resultados.get("files", [])
            return arquivos[0] if arquivos else None
        except Exception as e:
            print(f"Erro ao buscar arquivo: {e}")
            return None

    def mover_arquivo_para_pasta(self, arquivo_id: str, pasta_destino_id: str):
        """Move o arquivo para uma nova pasta, removendo os pais antigos"""
        try:
            file = self.drive.files().get(fileId=arquivo_id, fields='parents').execute()
            pais_atuais = ",".join(file.get('parents', []))

            self.drive.files().update(
                fileId = arquivo_id,
                addParents = pasta_destino_id,
                removeParents = pais_atuais,
                fields = 'id, parents'
            ).execute()

            print(f"Arquivo {arquivo_id} movido para a pasata {pasta_destino_id}")
            return True
        except Exception as e:
            print(f"Erro ao mover arquivo: {e}")
            return False

    def renomear_arquivo(self, arquivo_id: str, novo_nome: str):
        """Renomeia um arquivo no Drive"""
        try:
            file = self.drive.files().get(fileId = arquivo_id, fields='name').execute()
            nome_antigo = file['name']

            self.drive.files().update(
                fileId = arquivo_id,
                body = {'name': novo_nome},
                fields = 'id, name'
            ).execute()

            logging.info(f'Arquivo {nome_antigo} foi renomeado com sucesso para {novo_nome}')
            return True
        except Exception as e:
            logging.error(f'Arquivo {nome_antigo} não foi encontrado e renomeado:', str(e))
            return False

    def buscar_pasta_por_nome(self, nome_pasta: str, pasta_pai_id: str= None) -> dict:
        """Busca uma pasta pelo nome no Drive (globalmente, sem limitar por pasta pai)."""
        query = f"name = '{nome_pasta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

        if pasta_pai_id:
            query += f" and '{pasta_pai_id}' in parents"

        try:
            resultados = self.drive.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, mimeType, parents)"
            ).execute()

            pastas = resultados.get("files", [])
            return pastas[0] if pastas else None

        except Exception as e:
            logging.error(f"Erro ao buscar pasta: {e}")
            return None

    def criar_pasta(self, nome: str, pasta_pai_id: str = None) -> str:
        
        """Cria uma pasta com nome definido e opcional pasta pai"""
        file_metadata = {
            'name': nome,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if pasta_pai_id:
            file_metadata['parents'] = [pasta_pai_id]

        try:
            file = self.drive.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return file['id']

        except Exception as e:
            logging.error(f'Ocorreu um erro ao tentar criar a pasta: {e}')
            return None

    def copiar_arquivo(self, arquivo_id: str, novo_nome: str = None, parents: list = None) -> str:
        """
        Copia um arquivo no Google Drive e opcionalmente define o novo nome e a pasta de destino.
        Retorna o ID do novo arquivo copiado.
        """
        try:
            body = {}
            if novo_nome:
                body['name'] = novo_nome
            if parents:
                body['parents'] = parents

            arquivo_copiado = self.drive.files().copy(
                fileId=arquivo_id,
                body=body
            ).execute()

            novo_id = arquivo_copiado.get('id')
            logging.info(f"Arquivo copiado com sucesso. Novo ID: {novo_id}\n")
            return novo_id

        except Exception as e:
            logging.error(f"Falha ao copiar arquivo {arquivo_id}: {e}")
            return None
        
    def listar_arquivos(self, pasta_id: str)-> list:
        """
        Lista todos os arquivos dentro de uma pasta no Google Drive.
        """
        try:
            arquivos = []
            page_token = None

            while True:
                resposta = self.drive.files().list(
                    q=f"'{pasta_id}' in parents and trashed = false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType)',
                    pageToken=page_token
                ).execute()

                arquivos.extend(resposta.get('files', []))
                page_token = resposta.get('nextPageToken', None)

                if not page_token:
                    break

            return arquivos

        except Exception as e:
            logging.error(f"[ERRO] Falha ao listar arquivos da pasta {pasta_id}: {e}")
            return []

    def upload_arquivo(self, caminho_arquivo: str, nome_arquivo: str, pasta_destino_id: str) -> str:
        """Faz upload de um arquivo para o Google Drive dentro da pasta indicada e retorna o ID do arquivo."""
        try:
            logging.info(f"Iniciando upload do arquivo '{caminho_arquivo}' para a pasta '{pasta_destino_id}' no Drive.\n")
            
            file_metadata = {
                'name': nome_arquivo,
                'parents': [pasta_destino_id]
            }
            media = MediaFileUpload(caminho_arquivo, resumable=True)
            
            arquivo = self.drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            arquivo_id = arquivo.get('id')
            logging.info(f"Upload concluído com sucesso. ID do arquivo no Drive: {arquivo_id}\n")

            return arquivo_id

        except Exception as e:
            logging.error(f"Erro ao fazer upload do arquivo '{nome_arquivo}':\n {e}", exc_info=True)
            raise