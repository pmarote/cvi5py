import os
import sys
import json
from win32 import win32api

from pycvi.CviDb import CviDb


class Config:
    """Configurações diversas.

    Esta é a primeira classe carregada.
    Define especialmente os diretórios de trabalho e cria se não existir.
    Carrega  e salva também cvi_sys_data, que são basicamente as opções gravadas do sistema
    """

    def __init__(self):
        self.PROJECT_NAME: str = "CVI"       # padrão do docs(Swagger UI) e ReDoc
        self.PROJECT_VERSION: str = "5.1.2306"    # padrão do docs(Swagger UI) e ReDoc
        self.CVI_USR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__)))), 'usr')
        self.CVI_RES = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__)))), 'res')
        self.CVI_VAR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__)))), 'var')
        Config.create_dir_if_not_exists(self.CVI_VAR)
        Config.create_dir_if_not_exists(os.path.join(self.CVI_VAR, 'log'))
        Config.create_dir_if_not_exists(os.path.join(self.CVI_VAR, 'tmp'))
        self.CVI_SOURCE = os.path.join(self.CVI_VAR, 'source')
        Config.create_dir_if_not_exists(self.CVI_SOURCE)
        self.CVI_RESULT = os.path.join(self.CVI_VAR, 'result')
        Config.create_dir_if_not_exists(self.CVI_RESULT)
        self.CURRENT_PID = os.getpid()
        self.CVI_SYS_DATA_FILENAME = os.path.join(self.CVI_VAR, 'cvi_sys.json')
        # if not exists cvi_sys_data_filename, instantiate an empty dict and create it
        if (not os.path.isfile(self.CVI_SYS_DATA_FILENAME)):
            print(f"Arquivo {self.CVI_SYS_DATA_FILENAME} inexistente... "
                  + "Criando arquivo json inicial")
            cvi_sys_data = {}
            # add members/options
            cvi_sys_data['osf_atual'] = ''
            cvi_sys_data['cnpj_atual'] = ''
            cvi_sys_data['toDataType'] = 'html'
            cvi_sys_data['maxCells'] = 1000
            cvi_sys_data['showSql'] = True
            self.save_cvi_sys_data(cvi_sys_data)
        # if not exists cvi_sys.db, instantiate it
        if not os.path.isfile(os.path.join(self.CVI_VAR, 'cvi_sys.db')):
            print(f"Banco de dados {os.path.join(self.CVI_VAR), 'cvi_sys.db'} inexistente..."
                  + "Criando banco de dados inicial")
            cvidb_sys = CviDb(os.path.join(self.CVI_VAR), 'cvi_sys.db')
            try:
                cvidb_sys.createdb()
            except Exception as e:
                print(f"Erro fatal na criação do banco de dados "
                      + f"{os.path.join(self.CVI_VAR), 'cvi_sys.db'}.", e)
                return False
            cvidb_sys.exec_commit('''
CREATE TABLE cnpj_list
    (cnpj INT PRIMARY KEY, ie TEXT, razsoc TEXT);
''')
            cvidb_sys.exec_commit('''
CREATE TABLE pgsf_list
    (id INT PRIMARY KEY, osf TEXT, data TEXT, origem TEXT, forma_acionamento TEXT,
        razao_social TEXT, ie TEXT, responsavel TEXT, situacao TEXT);
''')
            cvidb_sys.exec_commit('''
CREATE TABLE sempapel_list
    (codigo TEXT PRIMARY KEY, descr TEXT, compl TEXT, interes TEXT, CNPJ TEXT, IE TEXT);
''')
            cvidb_sys.exec_commit('''
    CREATE TABLE aiim_tit
        (numero INT PRIMARY KEY, nro_comp TEXT, drt TEXT, autuado TEXT, advogado TEXT);
    ''')
            cvidb_sys.exec_commit('''
    CREATE TABLE aiim_tit_mov
        (numero, item, data TEXT, descri TEXT, PRIMARY KEY (numero, item));
    ''')
            cvidb_sys.exec_commit('''
    CREATE TABLE incons
        (origem, codigo, linha);
    ''')
            print("Banco de Dados criado com sucesso")

    def printSettings(self, full=True):
        drive_letter = self.CVI_RES[0:2]
        if full is True:
            print(f'vol_info: {drive_letter} =',
                  win32api.GetVolumeInformation(f'{drive_letter}\\')[0])
            print('sys.version: ', sys.version)
            print('sys.platform: ', sys.platform)
            print('os.name: ', os.name)
            print('sys.path: ', sys.path)
            print('os.getenv("HOME"):', os.getenv("HOME"))
            print('os.getenv("JUPYTER_CONFIG_DIR"):', os.getenv("JUPYTER_CONFIG_DIR"))
            print('os.getenv("JUPYTER_DATA_DIR"):', os.getenv("JUPYTER_DATA_DIR"))
            print('os.getenv("LOCALAPPDATA"):', os.getenv("LOCALAPPDATA"))
            print('os.getenv("PYTHON"):', os.getenv("PYTHON"))
            print('os.getenv("WINPYDIR"):', os.getenv("WINPYDIR"))
            print('os.getenv("USERDNSDOMAIN"):', os.getenv("USERDNSDOMAIN"))
        print('os.getenv("HTTP_PROXY"):', os.getenv("HTTP_PROXY"))
        # print('sys.modules.keys(): ', sys.modules.keys())
        for setting in dir(self):
            if setting.isupper():
                print(f'{setting} = {getattr(self, setting)}')

    def load_cvi_sys_data(self):
        try:
            with open(self.CVI_SYS_DATA_FILENAME, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Erro ao abrir ou ler o arquivo {self.CVI_SYS_DATA_FILENAME}.", e)
            return False

    def save_cvi_sys_data(self, cvi_sys_data):
        try:
            with open(self.CVI_SYS_DATA_FILENAME, 'w') as file:
                json.dump(cvi_sys_data, file)
        except Exception as e:
            print(f"Erro ao salvar o arquivo {self.CVI_SYS_DATA_FILENAME}.", e)
            return False

    @staticmethod
    def create_dir_if_not_exists(ordnerpfad):
        """Método estático
        """
        if not os.path.exists(ordnerpfad):
            os.makedirs(ordnerpfad)
