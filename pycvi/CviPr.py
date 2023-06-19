import os
import sqlite3
import fnmatch
import win32com.client as win32

from pycpfcnpj import cnpj


class CviPr:
    def __init__(self, config):
        self.config = config

    def getOsfList(self):
        # print("Lista de Auditorias:")
        osfList = []
        for dirname in os.listdir(self.config.CVI_RESULT):
            if os.path.isdir(os.path.join(self.config.CVI_RESULT, dirname))\
               and cnpj.validate(dirname):
                # encontrou uma pasta com CNPJ... procura agora um sqlite3 de osg
                for filename in os.listdir(os.path.join(self.config.CVI_RESULT, dirname)):
                    if filename[0:3].lower() == 'osf' and filename[-4:].lower() == '.db3':
                        osf = filename[:-4]
                        osf = osf[3:]
                        con = sqlite3.connect(os.path.join(
                            self.config.CVI_RESULT, dirname, filename))
                        cur = con.cursor()
                        sql = f"SELECT razao, cnpj, ie FROM _dbo_auditoria WHERE numOsf = '{osf}';"
                        for row in cur.execute(sql):
                            # print(f"CNPJ: {dirname} OSF: {osf} IE: {row[2]}  {row[0]}")
                            # prever erro (não abri nenhuma linha)
                            # h_wecho("OSF: {$osf} -> Não consegui abrir o arquivo {$key}...\
                            #           Erro: " . $db->lastErrorMsg() . "\n");
                            osfList.append({'osf': osf, 'cnpj': dirname,
                                            'ie': row[2], 'razao': row[0]})
                        con.close
        return osfList

    def getDatabasesOsfSqlite(self, osf, cnpj):
        print("OSF:", osf, "CNPJ:", cnpj)
        cv_db = os.path.join(self.config.CVI_RESULT, cnpj,
                             'cv_' + osf + '.db3')
        if (not os.path.isfile(cv_db)):
            print(f"Arquivo {cv_db} não localizado")
            return False
        osfdb = os.path.join(self.config.CVI_RESULT, cnpj,
                             'osf' + osf + '.db3')
        if (not os.path.isfile(osfdb)):
            print(f"Arquivo {osfdb} não localizado")
            return False
        con = sqlite3.connect(cv_db)
        cur = con.cursor()
        print(f"CONNECT '{cv_db}' AS " + 'cv_' + osf)
        sql = f"ATTACH '{osfdb}' AS " + 'osf' + osf
        print(sql)
        cur.execute(sql)
        # ##TODO## Detectar se seu pau no Attach
        return cur

    def recursiveFilemtime(self, path, file_dict, file_type='txt'):
        '''
        # Criando um dicionário vazio para armazenar os tempos de modificação dos arquivos
        file_dict = {}
        # Definindo o tipo de arquivo que estamos procurando
        file_type = 'txt'
        # Definindo o diretório inicial que queremos verificar
        initial_path = '/caminho/para/o/diretorio'
        # Chamando a função recursive_file_mtime
        cviPr.recursiveFilemtime(initial_path, file_dict, file_type)
        # Imprimindo o dicionário para ver os tempos de modificação dos arquivos
        import time
        for key, value in file_dict.items():
            print(f'File: {key}, Modification time: {time.ctime(value)}')
        '''
        if os.path.isfile(path):
            if fnmatch.fnmatch(path, '*.{}'.format(file_type)):
                file_dict[path.replace("/", "\\")] = os.path.getmtime(path)
            return
        elif os.path.isdir(path):
            for filename in os.listdir(path):
                self.recursiveFilemtime(os.path.join(path, filename), file_dict, file_type)
            return

    def abreExcelCom(self, fileName):
        # Open up Excel and make it visible
        try:
            excel = win32.gencache.EnsureDispatch('Excel.Application')
        except Exception as e:
            print(f"Não consegui abrir o excel. O erro foi:", e)
            print(f"Para corrigir, normalmente basta deletar a pasta "
                  + f'temporária {os.getenv("LOCALAPPDATA")}\\Temp\\gen_py')
            return
        excel.Visible = True
        # Open up the file
        # wb_data = excel.Workbooks.Open(fileName)
        excel.Workbooks.OpenText(fileName, 65001, 1, 1, 2, 0,
                                 1, 0, 0, 0, 0)
# http://msdn.microsoft.com/en-us/library/aa195814(v=office.11).aspx
# 2 -> Origin        xlWindows = 2 ou codepage 65001 utf8
# 1 -> StartRow      default value = 1
# 1 -> DataType      xlDelimited = 1     xlFixedWidth = 2
# 2 -> TextQualifier xlTextQualifierNone = -4142
#                    xlTextQualifierSingleQuote = 2
#                    xlTextQualifierDoubleQuote = 1
# 0 -> ConsecutiveDelimiter  True to have consecutive delimiters
#      considered one delimiter. The default is False
# 1 -> Tab           1 = True
# 0 -> Semicolon     0 = False
# 0 -> Comma         0 = False
# 0 -> Space         0 = False
# 0 -> Other         0 = False
        # opções de formatação padrão
        excel.ActiveSheet.PageSetup.PaperSize = 9  # xlPaperA4
        # define margens em (0.3, 0.3, 0.3, 0.3);
        excel.ActiveSheet.PageSetup.LeftMargin = \
            excel.Application.InchesToPoints(0.3)
        excel.ActiveSheet.PageSetup.RightMargin = \
            excel.Application.InchesToPoints(0.3)
        excel.ActiveSheet.PageSetup.HeaderMargin = \
            excel.Application.InchesToPoints(0.3)
        excel.ActiveSheet.PageSetup.FooterMargin = \
            excel.Application.InchesToPoints(0.3)
        # excel_imprime_linhas_grade($logico)
        excel.ActiveSheet.PageSetup.PrintGridlines = True
        # excel_zoom($zoom) (Zoom na impressão)
        excel.ActiveSheet.PageSetup.Zoom = 75
        # excel_zoom_visualizacao(porcentagem)
        excel.ActiveWindow.Zoom = 80

        r = excel.ActiveSheet.Range("1:1").Rows
        r.Cells.HorizontalAlignment = -4108  # xlCenter
        r.Cells.VerticalAlignment = -4108  # xlCenter
        r.Cells.WrapText = True  # Quebra Texto Automaticamente
        r.Cells.Font.Bold = True
        r.Cells.Font.Size = 12
        r.Cells.Interior.ColorIndex = 15
        r.AutoFilter(Field=1)
        excel.ActiveWindow.SplitColumn = 0
        excel.ActiveWindow.SplitRow = 1
        excel.ActiveWindow.FreezePanes = True
