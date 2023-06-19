import os
import sqlite3
import PySimpleGUI as sg


class ConvHelpers:
    def __init__(self, result_dir, db3_name):
        self.dir = result_dir
        self.name = db3_name

    def connect(self):
        self.conn = sqlite3.connect(os.path.join(self.dir, self.name))
        self.cursor = self.conn.cursor()

    def exec(self, sql: str):
        self.cursor.execute(sql)
        self.conn.commit()

    def insert(self, tablename, fields):
        placeholders = ', '.join('?' for _ in fields)
        sql = f"INSERT INTO {tablename} VALUES ({placeholders})"
        self.cursor.execute(sql, fields)

    def insert_into_table_from_txt(self, txt_file, tablename, cabec=True):
        try:
            with open(txt_file, 'r', encoding='utf-8') as file:
                pass
                lines = file.readlines()
        except Exception as e:
            print(f"Erro ao abrir ou ler o arquivo {txt_file}.", e)
            return
        for key, value in enumerate(lines):
            if cabec:
                cabec = False
            else:
                fields = value.strip().split('\t')
                self.insert(tablename, fields)
        self.conn.commit()

    @staticmethod
    def dtaSPED(data):
        # Transforma data do formato SPED ( DDMMAAAA ) para AAAA-MM-DD
        return data[4:8] + '-' + data[2:4] + '-' + data[0:2]

    @staticmethod
    def get_zip_file(window):
        layout = [
            [sg.Text("Seleção do Arquivo .zip para Converter"),
             sg.Input(key='-FILEPATH-', enable_events=True),
             sg.FileBrowse(key='-BROWSE-', file_types=(("Zip Files", "*.zip"),))],
            [sg.Button("OK"), sg.Button("Cancel")]
        ]
        file_window = sg.Window('Conversão - Selecione o arquivo .zip', layout, modal=True)
        while True:
            event, values = file_window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                file_window.close()
                window.reappear()
                return None
            elif event == 'OK':
                file_window.close()
                window.reappear()
                return values['-FILEPATH-']

    @staticmethod
    def listdir(start_dir='.', exclui_xml=False):
        files = []
        if os.path.isdir(start_dir):
            with os.scandir(start_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        if exclui_xml and entry.name.endswith('.xml'):
                            continue
                        files.append(entry.path)
                    elif entry.is_dir():
                        files += ConvHelpers.listdir(entry.path, exclui_xml)
        else:
            print(f"##ERROR... {start_dir} is not a directory")
        return files

    @staticmethod
    def verifica_arquivo(nome_diretorio, nome_arquivo):
        # Lista todos os arquivos no diretório
        arquivos = os.listdir(nome_diretorio)
        # Filtra a lista para incluir apenas arquivos .db3
        arquivos_db3 = [arquivo for arquivo in arquivos if arquivo.endswith('.db3')]
        # Extrai os nomes dos arquivos, sem a extensão
        nomes_arquivos = [os.path.splitext(arquivo)[0] for arquivo in arquivos_db3]
        # Verifica se o nome_arquivo está na lista de nomes_arquivos
        if nome_arquivo in nomes_arquivos:
            return True
        else:
            return False
