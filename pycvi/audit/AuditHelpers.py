import PySimpleGUI as sg
import os
import traceback

from pycvi.CviDb import CviDb
from pycvi.CviSqlToData import CviSqlToData


class AuditHelpers:
    """Helpers diversos para as auditorias
    """

    def __init__(self, config):
        self.config = config

    def values_to_osf_cnpj(self, values: str):
        osf = values[:11]
        cnpj = values[18:32]
        return osf, cnpj

    def audits_action(self, osf: str, cnpj: str):
        db_dir = os.path.join(self.config.CVI_VAR, 'result', cnpj)
        cvidb = CviDb(db_dir, f'cv_{osf}.db3')
        try:
            cvidb.opendb()
        except Exception as e:
            print(f"Erro ao abrir o banco de dados {db_dir}\\cv_{osf}.db3", e)
            return False
        try:
            cvidb.attachdb(db_dir, f'osf{osf}.db3')
            return cvidb
        except Exception as e:
            print(f"Erro com attach no banco de dados {db_dir}\\osf{osf}.db3",
                  e)
            return False

    def get_sql_input(self, window, fileName, queryTitle, sql):
        layout = [
            [sg.Text("Nome do Arquivo"),
             sg.Input(default_text=fileName, key='-FILENAME-', size=(120, 1))],
            [sg.Text("Título do Relatório"),
             sg.Input(default_text=queryTitle, key='-TITLE-', size=(120, 1))],
            [sg.Text("SQL"),
             sg.Multiline(default_text=sql, key='-SQL-', size=(130, 20))],
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
                return values['-FILENAME-'], values['-TITLE-'], values['-SQL-']

    def sqlToData_run_aux(self, window, cv_db, sql: str,
                          fileName: str, queryTitle=''):
        if window is not False:
            # ou seja, se window = False, não abre janela de confirmação do SQL
            # window.disappear()
            sql_input = self.get_sql_input(window, fileName, queryTitle, sql)
            if sql_input is None:
                print("Relatório cancelado pelo usuário")
                return False
            sql = sql_input[2]
            fileName = sql_input[0]
            queryTitle = sql_input[1]

        cvi_sys_data = self.config.load_cvi_sys_data()
        sqlToData = CviSqlToData(cvi_sys_data['toDataType'],
                                 cvi_sys_data['maxCells'],
                                 cvi_sys_data['showSql'])
        print(sql)
        try:
            sqlToData.run(cv_db, sql, fileName, queryTitle)
            print(f"Do sql acima, o arquivo {fileName} foi gerado com sucesso")
            return True
        except Exception as e:
            print(f"Do sql acima, {fileName} ##NÃO## foi gerado "
                  + "em razão do seguinte erro:", e, "\n")
            traceback.print_exc()
            return False

    def createTableFromSql(self, window, cv_db, table: str, sql: str):
        sqldrop = f'''
DROP TABLE IF EXISTS {table}
'''
        cv_db.exec_commit(sqldrop)
        print(f"Dropped table (if exists) {table}")
        window.refresh()
        sqlcreate = f'''
CREATE TABLE {table} AS
{sql}
'''
        cv_db.exec_commit(sqlcreate)
        print(f"Created table {table} from sql {sql}")
        window.refresh()

    def df_style(self, styler):
        '''Estilo numérico para o Jupyter Notebook
        '''
        styler.format(lambda v: f'{v:,.2f}'.replace(".", "#").
                      replace(",", ".").replace("#", ",") if not isinstance(v, str) else v)
        styler.applymap(lambda v: 'color:red;' if not isinstance(v, str) and v < 0 else None)
        styler.applymap(lambda v: 'opacity: 70%;'
                        if not isinstance(v, str) and abs(v) < 10000 else None)
        return styler
