from Managers.autenticador import GoogleOAUTH
from Utils.secrets import Planilhas
from Managers.controlador_Planilha import ControladorPlanilha

class User:
    def __init__(self, autenticador: GoogleOAUTH)-> None:
        self.autenticador = autenticador
        self.nome = None
        self.perfil = None
        self.email = None
        
        controlador_planilha = ControladorPlanilha(self.autenticador)
        self.email = self.autenticador.get_user_email()

        Administatrivo_sheet = Planilhas.ADM
        if Administatrivo_sheet is None:
            raise ValueError('Sem parametros para planilha de controle Administartivo')
        if self.email is None:
            raise ValueError('Email não consta na planilha do Administrativo')      
                # Acessa planilha
        controlador_planilha = ControladorPlanilha(
            autenticador=self.autenticador,
            planilha_id=Planilhas.ADM,
            planilha_nome="Administrativo"  
        )

        # Lê os dados da planilha
        dados_usuarios = controlador_planilha.read_to_json()

        # Busca o usuário na planilha
        for usuario in dados_usuarios:
            email_planilha = usuario.get("Email", "").strip().lower()
            cargo = usuario.get("Cargo", "").strip()
            nome = usuario.get("Nome", "").strip()

            if email_planilha == self.email.strip().lower():
                self.nome = nome
                self.perfil = cargo
            else:
                raise ValueError(f"Email '{self.email}' não consta na planilha do Administrativo")

