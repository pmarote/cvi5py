import os
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _02_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando 02 Auditorias Conciliação na osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_02A-ConciliacaoAnaliticoDoAudit_01Bpy')
    sql = 'SELECT * FROM chaveNroTudao;'
    ah.sqlToData_run_aux(window, cv_db, sql, fileName,
                         os.path.basename(fileName))

    cv_db.createIndex(osf, 'dfe_fiscal_EfdC100', 'idEfdC100')
    cv_db.createIndex(osf, 'dfe_fiscal_NfeC100', 'idNfeC100')
    nivelDetalhe = 1
    if (nivelDetalhe != 0):
        nd0 = f'''\
SELECT
  '[EfdNfe]' AS tA, A.*,
  '[EfdC100]' AS tB, B.idEfdC100, B.IND_OPER, B.IND_EMIT, B.COD_SIT, B.NUM_DOC,
    B.CHV_NFE, B.DT_DOC, B.VL_DOC, B.VL_ICMS, B.VL_ICMS_ST,
  '[NfeC100]' AS tC, C.idNFeC100, C.IND_OPER, C.IND_EMIT, C.COD_SIT, C.NUM_DOC,
    C.CHV_NFE, C.DT_DOC, C.VL_DOC, C.VL_ICMS, C.VL_ICMS_ST
'''
    else:
        nd0 = f'''\
SELECT
  '[EfdNfe]' AS tA, A.*, '[EfdC100]' AS tB, B.*, '[NfeC100]' AS tC, C.*
'''
    sql = f'''\
{nd0}
FROM _fiscal_EfdNfe AS A
LEFT OUTER JOIN dfe_fiscal_EfdC100 AS B ON B.idEfdC100 = A.idEfdC100
LEFT OUTER JOIN dfe_fiscal_NfeC100 AS C ON C.idNfeC100 = A.idNfeC100
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_02B-ConciliacaoEfdNFepy')
    queryTitle = os.path.basename(fileName) +\
        "<h3>tpJoin: 0 - Chave de Acesso bate; 1 - Número Bate; " +\
        "2 - Não localizou nem número, nem chave de acesso<br>" +\
        "O inverso pode ser verificado em .[fiscal].[NfeEfdParticip]</h3>"
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)
