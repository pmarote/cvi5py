import PySimpleGUI as sg
import os
import traceback

from pycvi.Config import Config
from pycvi.CviPr import CviPr
from pycvi.Actions import Actions
import pycvi.conv
import pycvi.pancho
import pycvi.audit

config = Config()
cviPr = CviPr(config)
actions = Actions(config, cviPr)
osf_list, osf_selecionada = actions.get_osfs()

sg.theme('SystemDefaultForReal')
# ------ Menu Definition ------ #
menu_def = [['&Arquivo', ['&Open     Ctrl-O', 'Jupyter Notebook ou cmd',
                          '&Fontes', '&Resultados', '&Trab_Excel', '---',
                          'Abre &Excel', 'Abre &Html', '---', 'E&xit']],
            ['&Edit',
                ['&Paste', ['Special', 'Normal', ],
                 'Undo', '---', 'Propriedades']],
            ['&Conv', ['01 &Converter', '02 &XML', '03 &EFD', '04 CAT&42']],
            ['&Pancho', ['&Cadesp', '&PGSF', '&Sem Papel']],
            ['Au&ditSafic',
                ['00 Pesquisa Livre',
                 '01 Audit Resumo', '02 Audit Conciliação',
                 '03 Audit DocAtribs', '04 Audits do Safic',
                 '05 Audit Cadesp', '06 Audit Tabelas Cv',
                 '11 Dados das NFes', '15 MDFs CTEs NFes',
                 '21 Dados das EFDs', '22 DGCAs Simplificados',
                 '35 Scanc', '95 Específico',
                 'DFe']],
            ['&Utilitários',
                ['S&qliteMan', 'Sqlite&Bro', '&Notepad++', '&Sublime',
                 '---', 'Dados de &Inicialização', 'Backup CVI',
                 'Sql Genérico']],
            ['&Ajuda', '&Sobre...'], ]
# ------ Buttons ------ #
buttons = [sg.Button('DFe'), sg.Button('Resultados'), sg.Button('Abre Excel'),
           sg.Button('Abre Html'), sg.Button('Propriedades')]


def main_window(menu_def, buttons, osf_list, osf_selecionada):
    # ------ GUI Defintion ------ #
    layout = [
        [sg.Menu(menu_def, tearoff=False, pad=(200, 1))],
        [sg.Combo(osf_list, osf_selecionada,
                  s=(100, 22), key='-COMBO-', enable_events=True)],
        [sg.Output(size=(100, 28))],
        buttons,
    ]
    window = sg.Window(f"{config.PROJECT_NAME} {config.PROJECT_VERSION}",
                       layout, icon='.\\core\\pn_i32.ico',
                       default_element_size=(12, 1),
                       default_button_element_size=(12, 1), finalize=True)
    # Event loop
    try:
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Exit'):
                break
            print(event, values)
            # ------ Process menu choices ------ #
            if event == '-COMBO-':
                actions.combo_action(values['-COMBO-'])
            if event == 'Open     Ctrl-O':
                actions.open_action()
            elif event == 'Jupyter Notebook ou cmd':
                actions.startfile_action('cvi5py_cmd.bat')
            elif event == 'Fontes':
                actions.startfile_action('', config.CVI_SOURCE)
            elif event == 'Resultados':
                path_selection = os.path.join(config.CVI_RESULT, values['-COMBO-'][18:32],
                                              values['-COMBO-'][:11])
                actions.startfile_action('', os.path.realpath(path_selection))
            elif event == 'Trab_Excel':
                actions.startfile_action('TrabPaulo.xlsm', config.CVI_RES)
            elif event == 'Abre Excel':
                actions.open_excel_html_action(window, 'txt')
            elif event == 'Abre Html':
                actions.open_excel_html_action(window, 'html')
            elif event == 'Propriedades':
                actions.properties_action()
            elif event == '01 Converter':
                pycvi.conv.conv_action(window, values['-COMBO-'])
            elif event == 'Cadesp':
                pycvi.pancho.cadesp_action(window, values['-COMBO-'])
            elif event == 'PGSF':
                pycvi.pancho.pgsf_action(window, values['-COMBO-'])
            elif event == 'Sem Papel':
                pycvi.pancho.sempapel_action(window, values['-COMBO-'])
            elif event == '00 Pesquisa Livre':
                pycvi.audit._00_action(window, values['-COMBO-'])
            elif event == '02 Audit Conciliação':
                pycvi.audit._02_action(window, values['-COMBO-'])
            elif event == '03 Audit DocAtribs':
                pycvi.audit._03_action(window, values['-COMBO-'])
            elif event == '21 Dados das EFDs':
                pycvi.audit._21_action(window, values['-COMBO-'])
            elif event == '35 Scanc':
                pycvi.audit._35_action(window, values['-COMBO-'])
            elif event == '95 Específico':
                pycvi.audit._95_action(window, values['-COMBO-'])
            elif event == 'DFe':
                pycvi.audit._90_action(window, values['-COMBO-'])
            elif event == 'SqliteMan':
                actions.startfile_action(r'Sqliteman-1.2.2\sqliteman.exe')
            elif event == 'SqliteBro':
                actions.startfile_action('sqlite_bro.exe')
            elif event == 'Notepad++':
                actions.startfile_action(r'npp.8.3.3.portable.x64\notepad++.exe')
            elif event == 'Sublime':
                actions.startfile_action('cvi5py_sublime.bat')
            elif event == 'Dados de Inicialização':
                actions.init_data_action()
            elif event == 'Backup CVI':
                actions.backup_cvi_action(window)
            elif event == 'Sql Genérico':
                actions.sqlToData_generic_action(window)
            elif event == 'Sobre...':
                actions.about_action(window)
        window.close()
    except Exception as e:
        traceback.print_exc()
        sg.popup_error_with_traceback(f'Erro no menu...', e)


main_window(menu_def, buttons, osf_list, osf_selecionada)
