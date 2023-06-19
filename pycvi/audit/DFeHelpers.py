import PySimpleGUI as sg
import os
import traceback

from pycvi.CviDb import CviDb
from pycvi.CviSqlToData import CviSqlToData


class DFeHelpers:
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
            print(f"Erro com attach no banco de dados {db_dir}\\osf{osf}.db3", e)
            return False

    def get_keys_input(self, window, dirName):
        layout = [
            [sg.Text("Diretorio para Gravação"),
             sg.Input(default_text=dirName, key='-DIRNAME-', size=(120, 1))],
            [sg.Text("Chaves"), sg.Multiline(key='-KEYS-', size=(130, 20))],
            [sg.Button("OK"), sg.Button("Cancel")]
        ]
        input_window = sg.Window('Digite a(s) chave(s) de acesso da(s) DFe(s)', layout, modal=True)
        while True:
            event, values = input_window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                input_window.close()
                return None
            elif event == 'OK':
                input_window.close()
                return values['-DIRNAME-'], values['-KEYS-']

    def DfeNFe_aux(self, window, cv_db, fileName: str, sqlToData, sql: str, queryTitle=''):
        print(sql)
        try:
            sqlToData.run(cv_db, sql, fileName, queryTitle)
            print(f"Do sql acima, o arquivo {fileName} foi gerado com sucesso\n")
            return True
        except Exception as e:
            print(f"Do sql acima, {fileName} ##NÃO## foi gerado em razão do seguinte erro:",
                  e, "\n")
            traceback.print_exc()
            return False

    def DfeNFe(self, window, osf, cv_db, fileName: str, key: str):
        cvi_sys_data = self.config.load_cvi_sys_data()
        sqlToData = CviSqlToData(toDataType='html', maxCells=-1,
                                 showSql=cvi_sys_data['showSql'])
        sql = f'''\
SELECT
CASE WHEN IND_EMIT = 0 THEN
    CASE WHEN IND_OPER = 0 THEN 'NFe de ENTRADA - EMISSÃO PRÓPRIA' ELSE 'NFe de SAÍDA' END
ELSE
    CASE WHEN IND_OPER = 0 THEN 'NFe de DEVOLUÇÃO EMITIDA POR TERCEIROS'
        ELSE 'NFe de ENTRADA - EMITIDA POR TERCEIROS' END
END AS Tipo_De_NFe,
CASE WHEN COD_SIT <> 0 THEN
    'ATENÇÃO! NOTA FISCAL NÃO VÁLIDA - VER COD_SIT (2 Cancelada, 4 Denegada, 5 NrInutilizado)'
    ELSE 'NFe Válida' END AS Situacao_Da_NFe,
'[NfeC100]' AS tA, A.IND_OPER, A.COD_MOD, A.COD_SIT, A.NUM_DOC, A.CHV_NFE,
A.DT_DOC, A.DT_E_S, A.VL_DOC, A.VL_BC_ICMS, A.VL_ICMS, A.VL_BC_ICMS_ST, A.VL_ICMS_ST,
    A.VL_IPI, A.IND_EMIT, A.NaturezaOperacao,
'[NfeC101-Emitente]' AS tC, C.CNPJ, C.CPF, C.IE, C.IEST, C.UF, C.NOME, C.Bairro,
    C.Municipio, C.Im, C.Cnae, C.Fantasia, C.xLgr, C.nro, C.xCpl, C.Cep,
    C.Telefone, C.Pais, C.CodRegTrib,
'[NfeC102-Dest(Saida)_Remet(Entr)]' AS tD, D.CNPJ, D.CPF, D.IE, D.IDESTRANG, D.UF,
    D.NOME, D.Bairro, D.Municipio, D.Im, D.xLgr, D.nro, D.xCpl, D.Telefone,
    D.Pais, D.Suframa, D.Email, D.Cep,
'[NfeC110-Obs]' AS tG, G.INF_AD_FISCO, G.INF_COMPL, '[NfeC112]' AS tH, H.CHV_NFE,
'[NfeC115-Coleta]' AS tI, I.CNPJ_COL, I.COD_MUN_COL, I.LOGR_COL, I.NUM_COL,
    I.COMPL_COL, I.BAIRRO_COL,
'[NfeC116-Entrega]' AS tJ, J.CNPJ_ENTG, J.COD_MUN_ENTG, J.LOGR_ENTG,
    J.NUM_ENTG, J.COMPL_ENTG, J.BAIRRO_ENTG, J.NOM_MUN_ENTG, J.UF_ENTG,
'[NfeC130-DemaisTribs]' AS tM, M.VL_SERV_NT, M.VL_BC_ISSQN, M.VL_ISSQN,
    M.VL_IRRF, M.VL_PREV, M.vPIS, M.vCOFINS, M.vOutro, M.vDescIncond, M.vDescCond, M.vISSRet,
'[NfeC140-Fat]' AS tN, N.NRO_FAT, N.VL_ORIG, N.VL_DESC, N.VL_LIQ
   FROM dfe_fiscal_NfeC100 AS A
   LEFT OUTER JOIN dfe_fiscal_NfeC100Detalhe AS B ON B.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC101 AS C ON C.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC102 AS D ON D.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC110 AS G ON G.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC112 AS H ON H.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC115 AS I ON I.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC116 AS J ON J.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC127 AS L ON L.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC130 AS M ON M.idNfeC100 = A.idNfeC100
   LEFT OUTER JOIN dfe_fiscal_NfeC140 AS N ON N.idNfeC100 = A.idNfeC100
   WHERE A.CHV_NFE = '{key}'
'''
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC100', 'CHV_NFE')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC100Detalhe', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC101', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC102', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC110', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC112', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC115', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC116', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC127', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC130', 'idNfeC100')
        cv_db.createIndex(osf, 'dfe_fiscal_NfeC140', 'idNfeC100')

        queryTitle = f"{key} - Dados Principais da NFe"
        self.DfeNFe_aux(window, cv_db, fileName, sqlToData, sql, queryTitle)
        sqlToData.tableSpread(fileName)
#    $aHtmlFiles[] = $fileName;    
