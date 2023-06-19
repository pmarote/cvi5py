import PySimpleGUI as sg
import os
import subprocess
import traceback
import time

# import pycvi
from pycvi.CviSqlToData import CviSqlToData
from pycvi.CviDb import CviDb


class Actions:
    """Actions diversas do pysimplegui do cvi5

    Estão aqui apenas por questão de organização do código de cvi5.py
    """

    def __init__(self, config, cviPr):
        self.config = config
        self.cvi_sys_data = self.config.load_cvi_sys_data()
        self.cviPr = cviPr

    def get_osfs(self):
        osf_list = []
        osf_selecionada = ''
        for osf in self.cviPr.getOsfList():
            item_value = f"{osf['osf']} CNPJ: {osf['cnpj']} "\
                         + f"IE: {osf['ie']}  {osf['razao']}"
            if (self.cvi_sys_data['osf_atual'] == osf['osf']
                    and self.cvi_sys_data['cnpj_atual'] == osf['cnpj']):
                osf_selecionada = item_value
            osf_list.append(item_value)
        return osf_list, osf_selecionada

    def combo_action(self, combo_value):
        self.cvi_sys_data = self.config.load_cvi_sys_data()
        self.cvi_sys_data['osf_atual'] = combo_value[:11]
        self.cvi_sys_data['cnpj_atual'] = combo_value[18:32]
        self.config.save_cvi_sys_data(self.cvi_sys_data)
        print("cvi_sys_data=", self.cvi_sys_data)

    def open_action(self):
        filename = sg.popup_get_file('file to open', no_window=True)
        print("##TODO## Opção ainda não implementada")
        print(filename)

    def startfile_action(self, filename, dirname=''):
        # #### SERÁ QUE ASSIM ABAIXO VAI SEM OS SETS DAQUI? ##
        # cmd start cmd /C sqlite_bro
        dirname = self.config.CVI_USR if dirname == '' else dirname
        os.startfile(os.path.realpath(os.path.join(dirname, filename)))
        print(f"Aberto {filename} - verifique se está em segundo plano.")

    def combo_popup(self, window, optionsList):
        layout = [
            [sg.Text("Lista dos arquivos mais recentes gerados:")],
            [sg.Combo(optionsList, default_value=optionsList[0],
                      size=(100, 1), key='-COMBO-')],
            [sg.Button("OK"), sg.Button("Cancel")]
        ]
        combo_window = sg.Window('Selecione um arquivo para abrir',
                                 layout, modal=True)
        while True:
            event, values = combo_window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                combo_window.close()
                # window.reappear()
                return None
            elif event == 'OK':
                combo_window.close()
                # window.reappear()
                return values['-COMBO-']

    def open_excel_html_action(self, window, fileType):
        if fileType not in ('txt', 'html'):
            print("#ERRO#... fileType deve ser 'txt' ou 'html'")
            return
        file_dict = {}
        self.cviPr.recursiveFilemtime(self.config.CVI_VAR, file_dict, fileType)
        # Ordenar o dicionário pela valor em ordem decrescente
        file_sort = dict(sorted(file_dict.items(),
                                key=lambda item: item[1], reverse=True))
        # Pegar apenas os primeiros 20 itens do dicionário
        file_top = dict(list(file_sort.items())[:20])
        file_selection = self.combo_popup(window, list(file_top.keys()))
        if file_selection is None:
            print("Seleção cancelada pelo usuário")
        else:
            if fileType == 'html':
                os.startfile(os.path.realpath(file_selection))
                print(f"Aberto {file_selection} - "
                      + "verifique se está em segundo plano")
            else:
                print("\n#AGUARDE# a abertura do Excel...")
                window.refresh()
                self.cviPr.abreExcelCom(file_selection)
                print(f"Aberto {file_selection} em Excel - "
                      + "verifique se está em segundo plano")

    def properties_action(self):
        self.cvi_sys_data = self.config.load_cvi_sys_data()
        print(self.cvi_sys_data)
        # definir qual opção do radio button será o padrão
        default_html = True \
            if self.cvi_sys_data['toDataType'] == 'html' else False
        default_txt = True \
            if self.cvi_sys_data['toDataType'] == 'txt' else False
        default_html = True \
            if self.cvi_sys_data['toDataType'] == 'html' else False
        default_txt = True \
            if self.cvi_sys_data['toDataType'] == 'txt' else False

        layout = [
            [sg.Text('Saída de Relatório: '),
             sg.Radio('html', "RADIO1", default=default_html),
             sg.Radio('txt', "RADIO1", default=default_txt)],
            [sg.Text('Número máximo de células: '),
             sg.Input(default_text=self.cvi_sys_data['maxCells'],
                      key='-MAXCELLS-', size=(5, 1),
                      enable_events=True, tooltip='Digite um número inteiro')],
            [sg.Checkbox('Mostrar SQL ao gerar arquivo html:',
                         default=self.cvi_sys_data['showSql'],
                         key='-SHOWSQL-')],
            [sg.OK()]
        ]
        window = sg.Window('Propriedades', layout, modal=True)
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                print("Não foi apertado ok, então as "
                      + "opções se mantiveram originalmente")
                print(self.cvi_sys_data)
                break
            if event == 'OK':
                # Validar a entrada de maxCells
                if not values['-MAXCELLS-'].isdigit():
                    sg.popup('Erro', 'Por favor, digite um número '
                             + 'inteiro para maxCells')
                    continue
                self.cvi_sys_data['toDataType'] = \
                    'html' if values[0] is True else 'txt'
                self.cvi_sys_data['maxCells'] = int(values['-MAXCELLS-'])
                self.cvi_sys_data['showSql'] = values['-SHOWSQL-']
                self.config.save_cvi_sys_data(self.cvi_sys_data)
                print(self.cvi_sys_data)
                window.close()
                break

    def init_data_action(self):
        print("Dados de Inicialização - ",
              "# VERIFIQUE SE OS SETTINGS ESTÃO PERFEITOS !#")
        self.config.printSettings()
        print("cvi_sys_data=", self.cvi_sys_data)

    def backup_cvi_action(self, window):
        self.startfile_action('cvi5py_back.bat')
        back_dir = os.path.join(os.path.dirname(self.config.CVI_USR), 'back')
        print(f"Em tese foi feito o backup cvi em {back_dir}. Aguarde...")
        window.refresh()
        time.sleep(2)  # Pausa a execução por 2 segundos
        print(f"Aguardei 2 segundos. Será que já acabou? "
              + "Os arquivos *.7z nessa pasta são:")
        # criar uma lista vazia para armazenar os caminhos dos arquivos
        file_list = []
        for root, dirs, files in os.walk(back_dir):
            for file in files:
                if file.endswith(".7z"):
                    # adicionar à lista
                    file_list.append(os.path.join(root, file))
        file_list.sort()
        for file in file_list:
            print(file)

    def get_sqlToData_generic(self, window, dbName, fileName, queryTitle, sql):
        layout = [
            [sg.Text("Localização do Banco de Dados"),
             sg.Input(default_text=dbName, key='-DBNAME-', size=(120, 1))],
            [sg.Text("Nome do Arquivo"),
             sg.Input(default_text=fileName, key='-FILENAME-', size=(120, 1))],
            [sg.Text("Título do Relatório"),
             sg.Input(default_text=queryTitle, key='-TITLE-', size=(120, 1))],
            [sg.Text("SQL"), sg.Multiline(default_text=sql, key='-SQL-',
                                          size=(130, 20))],
            [sg.Button("OK"), sg.Button("Cancel")]
        ]
        input_window = sg.Window('Confirme ou altere os dados do SQL',
                                 layout, modal=True)
        while True:
            event, values = input_window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                input_window.close()
                return None
            elif event == 'OK':
                input_window.close()
                return values['-DBNAME-'], values['-FILENAME-'],\
                    values['-TITLE-'], values['-SQL-']

    def sqlToData_generic_action(self, window):
        file_dict = {}
        self.cviPr.recursiveFilemtime(self.config.CVI_VAR, file_dict, 'db')
        self.cviPr.recursiveFilemtime(self.config.CVI_VAR, file_dict, 'db3')
        # Ordenar o dicionário pela valor em ordem decrescente
        file_sort = dict(sorted(file_dict.items(),
                                key=lambda item: item[1], reverse=True))
        # Pegar apenas os primeiros 20 itens do dicionário
        file_top = dict(list(file_sort.items())[:20])
        file_selection = self.combo_popup(window, list(file_top.keys()))
        if file_selection is None:
            print("Seleção cancelada pelo usuário")
            return False
        exe_path = os.path.join(self.config.CVI_USR,
                                'Sqliteman-1.2.2', 'sqliteman.exe')
        subprocess.Popen([exe_path] + [file_selection])
        dbName = file_selection
        fileName = os.path.join(self.config.CVI_VAR, 'Sql_Generico_py')
        queryTitle = 'sem titulo'
        sql = 'SELECT 1;'
        sql_input = self.get_sqlToData_generic(window, dbName, fileName,
                                               queryTitle, sql)
        if sql_input is None:
            print("Relatório cancelado pelo usuário")
            return False
        dbName, fileName, queryTitle, sql = sql_input
        cvidb = CviDb(os.path.dirname(dbName), os.path.basename(dbName))
        try:
            cvidb.opendb()
        except Exception as e:
            print(f"Erro ao abrir o banco de dados {dbName}", e)
            return False
        print(sql)
        sqlToData = CviSqlToData(self.cvi_sys_data['toDataType'],
                                 self.cvi_sys_data['maxCells'],
                                 self.cvi_sys_data['showSql'])
        try:
            sqlToData.run(cvidb, sql, fileName, queryTitle)
            print(f"Do sql acima, o arquivo "
                  + f"{fileName}.{self.cvi_sys_data['toDataType']} "
                  + "foi gerado com sucesso\n")
            return True
        except Exception as e:
            print(f"Do sql acima, o arquivo "
                  + f"{fileName}.{self.cvi_sys_data['toDataType']} "
                  + "##NÃO## foi gerado em razão do seguinte erro:", e, "\n")
            traceback.print_exc()
            return False
    #    try:
    #        sqlToData.run(cv_db, sql, fileName, queryTitle)
    #        print(sql_input[2])
    #        print(f"Do sql acima, o arquivo {sql_input[0]} foi gerado com sucesso")
    #        return True
    #    except Exception as e:
    #        # This will print the error message to the sg.Output element
    #        print(e)
    #        traceback.print_exc()
    #        return False

    def about_action(self, window):
        window.disappear()
        sg.popup('não mande email para: paulomarote@hotmail.com',
                 'Origem: Grupo de Estudos NFe/SPED - DRT/13 - Guarulhos',
                 'Autor: AFRE Paulo Marote\n',
                 f'PySimpleGUI Version {sg.version}', grab_anywhere=True)
        window.reappear()
