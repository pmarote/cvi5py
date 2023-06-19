import os
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _21_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando 21 Dados das EFDs na osf {osf} "
          + "do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()

    cv_db.createIndex(osf, 'dfe_fiscal_EfdC100Detalhe', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_Efd0150', 'idEfd0150')
    sql = f'''\
SELECT '[EfdC100]' AS tA, A.*, '[EfdC100Detalhe]' AS tB, B.*, '[Efd0150]' AS tG, G.*
   FROM dfe_fiscal_EfdC100 AS A
   LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS B ON B.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = A.idEfd0150
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01a-EFDC100_py')
    queryTitle = "01a - Lista de EFDs C100 (sem duplicar) com C100Detalhe"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, '_fiscal_efd0200', 'COD_ITEM', 'idArquivo')
    cv_db.createIndex(osf, '_fiscal_efd0190', 'UNID', 'idArquivo')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC100', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC100Detalhe', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_Efd0150', 'idEfd0150')
    sql = f'''\
SELECT '[EfdC170]' AS tA, A.*, '[Efd0200]' AS tD, D.*, '[Efd0190]' AS tE, E.*,
   '[EfdC100]' AS tB, B.*, '[EfdC100Detalhe]' AS tC, C.*, '[Efd0150]' AS tG, G.*
   FROM dfe_fiscal_EfdC170 AS A
   LEFT OUTER JOIN _fiscal_efd0200 AS D ON D.COD_ITEM = A.COD_ITEM AND D.idArquivo = A.idArquivo
   LEFT OUTER JOIN _fiscal_efd0190 AS E ON E.UNID = D.UNID_INV AND E.idArquivo = A.idArquivo
   LEFT OUTER JOIN dfe_fiscal_EfdC100 AS B ON B.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS C ON C.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = B.idEfd0150
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01b-EFDC170_EFDC100_py')
    queryTitle = "01b - Lista de EFDs C170 com C100, C100Detalhe e Efd0150"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, 'dfe_fiscal_EfdC100Detalhe', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC110', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC190', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC195', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC197', 'idEfdC195')
    cv_db.createIndex(osf, 'dfe_fiscal_Efd0150', 'idEfd0150')
    sql = f'''\
SELECT '[EfdC100]' AS tA, A.*, '[EfdC100Detalhe]' AS tB, '[Efd0150]' AS tG, G.*,
B.*, '[EfdC110]' AS tC, C.*,
'[EfdC190]' AS tD, D.*, '[EfdC195]' AS tE, E.*, '[EfdC197]' AS tF, F.*
   FROM dfe_fiscal_EfdC100 AS A
   LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS B ON B.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_EfdC110 AS C ON C.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_EfdC190 AS D ON D.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_EfdC195 AS E ON E.idEfdC100 = A.idEfdC100
   LEFT OUTER JOIN dfe_fiscal_EfdC197 AS F ON F.idEfdC195 = E.idEfdC195
   LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = A.idEfd0150
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01c-EFDsC100s_C190s')
    queryTitle = "01c - Lista de EFDs C100s e C190 podendo duplicar"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, 'dfe_fiscal_EfdD100Detalhe', 'idEfdD100')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdD190', 'idEfdD100')
    sql = f'''\
SELECT '[EfdD100]' AS tA, A.*, '[EfdD100Detalhe]' AS tB, B.*, '[EfdD190]' AS tC, C.*
   FROM dfe_fiscal_EfdD100 AS A
   LEFT OUTER JOIN dfe_fiscal_EfdD100Detalhe AS B ON B.idEfdD100 = A.idEfdD100
   LEFT OUTER JOIN dfe_fiscal_EfdD190 AS C ON C.idEfdD100 = A.idEfdD100
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01d-EFDD100_py')
    queryTitle = "01d - Lista de EFDs D100 (sem duplicar) com D100Detalhe e D190"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, '_fiscal_EfdE111', 'idEfdE110')
    cv_db.createIndex(osf, '_fiscal_EfdE111Descr', 'idEfdE111')
    cv_db.createIndex(osf, '_fiscal_EfdE112', 'idEfdE111')
    cv_db.createIndex(osf, '_fiscal_EfdE112Descr', 'idEfdE112')
    cv_db.createIndex(osf, '_fiscal_EfdE113', 'idEfdE111')
    cv_db.createIndex(osf, '_fiscal_EfdE115', 'idEfdE110')
    cv_db.createIndex(osf, '_fiscal_EfdE115Descr', 'idEfdE115')
    cv_db.createIndex(osf, '_fiscal_EfdE116', 'idEfdE110')
    cv_db.createIndex(osf, '_fiscal_EfdE116Descr', 'idEfdE116')
    sql = f'''\
SELECT '[EfdE110]' AS tA, A.*, '[EfdE111]' AS tB, B.*, '[EfdE111Descr]' AS tC, C.*,
   '[EfdE112]' AS tD, D.*, '[EfdE112Descr]' AS tE, E.*,
   '[EfdE113]' AS tF, F.*,
   '[EfdE115]' AS tH, H.*, '[EfdE115Descr]' AS tI, I.*,
   '[EfdE116]' AS tJ, J.*, '[EfdE116Descr]' AS tK, K.*
   FROM _fiscal_EfdE110 AS A
   LEFT OUTER JOIN _fiscal_EfdE111 AS B ON B.idEfdE110 = A.idEfdE110
   LEFT OUTER JOIN _fiscal_EfdE111Descr AS C ON C.idEfdE111 = B.idEfdE111
   LEFT OUTER JOIN _fiscal_EfdE112 AS D ON D.idEfdE111 = B.idEfdE111
   LEFT OUTER JOIN _fiscal_EfdE112Descr AS E ON E.idEfdE112 = D.idEfdE112
   LEFT OUTER JOIN _fiscal_EfdE113 AS F ON F.idEfdE111 = B.idEfdE111
   LEFT OUTER JOIN _fiscal_EfdE115 AS H ON H.idEfdE110 = A.idEfdE110
   LEFT OUTER JOIN _fiscal_EfdE115Descr AS I ON I.idEfdE115 = H.idEfdE115
   LEFT OUTER JOIN _fiscal_EfdE116 AS J ON J.idEfdE110 = A.idEfdE110
   LEFT OUTER JOIN _fiscal_EfdE116Descr AS K ON K.idEfdE116 = J.idEfdE116
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01e1-EFDBlocoE100_py')
    queryTitle = "EFD_BlocoE100"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, 'Dfe_fiscal_EfdG125', 'idEfdG110')
    cv_db.createIndex(osf, 'Dfe_fiscal_EfdG126', 'idEfdG125')
    sql = f'''\
SELECT '[EfdG110]' AS tA, A.*, '[EfdG125]' AS tB, B.*, '[EfdG126]' AS tC, C.*
   FROM Dfe_fiscal_EfdG110 AS A
   LEFT OUTER JOIN Dfe_fiscal_EfdG125 AS B ON B.idEfdG110 = A.idEfdG110
   LEFT OUTER JOIN Dfe_fiscal_EfdG126 AS C ON C.idEfdG125 = B.idEfdG125;
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01f1-EFDBlocoG')
    queryTitle = "01f1 - Bloco G - Sintético"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, 'Dfe_fiscal_EfdG130', 'idEfdG125')
    cv_db.createIndex(osf, 'Dfe_fiscal_EfdG140', 'idEfdG130')
    sql = f'''\
SELECT '[EfdG110]' AS tA, A.*, '[EfdG125]' AS tB, B.*, '[EfdG126]' AS tC,
   C.*, '[EfdG130]' AS tD, D.*, '[EfdG140]' AS tE, E.*
   FROM Dfe_fiscal_EfdG110 AS A
   LEFT OUTER JOIN Dfe_fiscal_EfdG125 AS B ON B.idEfdG110 = A.idEfdG110
   LEFT OUTER JOIN Dfe_fiscal_EfdG126 AS C ON C.idEfdG125 = B.idEfdG125
   LEFT OUTER JOIN Dfe_fiscal_EfdG130 AS D ON D.idEfdG125 = B.idEfdG125
   LEFT OUTER JOIN Dfe_fiscal_EfdG140 AS E ON E.idEfdG130 = D.idEfdG130
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01f2-EFDBlocoG_py')
    queryTitle = "01f2 - Bloco G - Analítico"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, '_fiscal_ItemServicoDeclarado', 'codigo')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdH005', 'idEfdH005')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdH010Descr', 'idEfdH010')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdH010Posse', 'idEfdH010')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdH010Prop', 'idEfdH010')
    sql = f'''\
SELECT '[EfdH010]' AS tA, A.*, '[ItemServicoDeclarado]' AS tE, E.*,
'[EfdH005]' AS tF, F.*, '[EfdH010Descr]' AS tB, B.*, '[EfdH010Posse]' AS tC, C.*,
'[EfdH010Prop]' AS tD, D.*
   FROM dfe_fiscal_EfdH010 AS A
   LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS E ON E.codigo = A.COD_ITEM
   LEFT OUTER JOIN dfe_fiscal_EfdH005 AS F ON F.idEfdH005 = A.idEfdH005
   LEFT OUTER JOIN dfe_fiscal_EfdH010Descr AS B ON B.idEfdH010 = A.idEfdH010
   LEFT OUTER JOIN dfe_fiscal_EfdH010Posse AS C ON C.idEfdH010 = A.idEfdH010
   LEFT OUTER JOIN dfe_fiscal_EfdH010Prop AS D ON D.idEfdH010 = A.idEfdH010
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01f2-EFDBlocoH_py')
    queryTitle = "01g - Bloco H"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, '_fiscal_RelItemServicoEfd0200', 'idEfd0200')
    cv_db.createIndex(osf, '_fiscal_ItemServicoDeclarado', 'idItemServicoDeclarado')
    sql = f'''\
SELECT '[Efd0200]' AS tA, A.*,'[RelItemServicoEfd0200]' AS tB, B.*,
'[ItemServicoDeclarado]' AS tC, C.*
   FROM _fiscal_Efd0200 AS A
   LEFT OUTER JOIN _fiscal_RelItemServicoEfd0200 AS B ON B.idEfd0200 = A.idEfd0200
   LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS C ON C.idItemServicoDeclarado = B.idItemServicoDeclarado
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'EFD_01g-EFD0200_py')
    queryTitle = "01h - 0200"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)
