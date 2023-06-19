import os
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _35_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando 35 Scanc - Verificações na osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            '_35A-Scanc')
    sql = 'SELECT * FROM chaveNroTudao;'
    sql = '''\
SELECT '[EfdC170]' AS tI, I.NUM_ITEM, I.CFOP, I.CST_ICMS, I.COD_ITEM, I.DESCR_COMPL, I.QTD, I.UNID,
    I.ALIQ_ICMS, I.VL_ICMS, I.ALIQ_ST, I.VL_ICMS_ST, I.VL_ITEM,
  '[EfdC100]' AS tJ, J.CHV_NFE,
  '[NfeC100]' AS tK, K.CHV_NFE,
  '[NfeC170]' AS tH, H.NUM_ITEM, H.CFOP, H.IND_ORIG_MERCADORIA, H.CST_ICMS, H.CSOSN,
    H.cstCsosnIcms, H.COD_PROD_SERV, H.COD_CEANTRIB, H.COD_NCM, H.DESCR_PROD, H.QTD_TRIB,
    H.UNID_TRIB, H.PERC_MVA_ICMS_ST, H.Fci, H.CEST, H.VL_FCP, H.VL_BC_ICMS_ST_RETIDO,
    H.VL_ICMS_ST_RETIDO, H.VL_TOTAL_NFE_PROD,
  '[chaveNroTudao]' AS tL, L.*
FROM dfe_fiscal_EfdC170 AS I
LEFT OUTER JOIN Dfe_fiscal_EfdC100 AS J ON J.idEfdC100 = I.idEfdC100
LEFT OUTER JOIN Dfe_fiscal_NfeC100 AS K ON K.CHV_NFE = J.CHV_NFE
LEFT OUTER JOIN dfe_fiscal_NfeC170 AS H ON H.idNFeC100 = K.idNFeC100 AND H.NUM_ITEM = I.NUM_ITEM
LEFT OUTER JOIN chaveNroTudao AS L ON L.chave = J.CHV_NFE
WHERE cod_item = '000003'
'''
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, os.path.basename(fileName))
