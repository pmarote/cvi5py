import os
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _03_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando 02 Auditorias-DocAtribs na osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()

    nivelDetalhe = 1
    if (nivelDetalhe != 0):
        nd0 = f'''\
SELECT
  '[docAtribBase]' AS tB,
  B.classifs, substr(A.referencia, 1, 7) AS ref, B.tp_origem, B.origem,
  A.codSit, A.indEmit, A.indOper,
  B.Part, B.SituacaoPart, B.dtinifimSitPart,
  B.regPart, B.dtinifimRegPart,
  B.chave, B.numero, B.uf, B.dtEmissao, B.dtEntSd, B.cfopcvs, B.g1s,
  B.vlTotalDoc, B.vlBcIcmsProprio, B.vlIcmsProprio, B.vlBcIcmsSt, B.vlIcmsSt,
  B.EfdPartCodSit, B.EfdPartCfops, B.EfdPartVal, B.EfdPartIcms,
  B.NatOp, B.descris, CO.obs,
  B.tFinal, B.CHV_DFE, B.NUM_DOC, B.VL_DOC, B.VL_ICMS, B.VL_ICMS_ST
'''
    else:
        nd0 = f'''\
SELECT '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*,
  '[docAtribTudao]' AS tB, B.*,
  '[idDocAtributos_chaveObs]' AS tCO, CO.*
'''
    sql = f'''\
{nd0}
  FROM
  DocAtrib_fiscal_DocAtributos AS A
  LEFT OUTER JOIN docAtribTudao AS B ON B.idDocAtributos = A.idDocAtributos
  LEFT OUTER JOIN idDocAtributos_chaveObs AS CO ON CO.idDocAtributos = A.idDocAtributos
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_03A-DocAtributos_py')
    queryTitle = os.path.basename(fileName)
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    if (nivelDetalhe != 0):
        nd0 = f'''\
SELECT
  '[docAtribBase]' AS tB,
  B.classifs, substr(A.referencia, 1, 7) AS ref, B.tp_origem, B.origem,
  A.codSit, A.indEmit, A.indOper,
  B.Part, B.SituacaoPart, B.dtinifimSitPart,
  B.regPart, B.dtinifimRegPart,
  B.chave, B.numero, B.uf, B.dtEmissao, B.dtEntSd, B.cfopcvs, B.g1s,
  B.vlTotalDoc, B.vlBcIcmsProprio, B.vlIcmsProprio, B.vlBcIcmsSt, B.vlIcmsSt,
  B.EfdPartCodSit, B.EfdPartCfops, B.EfdPartVal, B.EfdPartIcms,
  B.NatOp, B.descris, CO.obs,
  '[docAtribOper]' AS tAO,
  AA.cstCsosnIcms, AA.indCstCsosn, AA.indOrigem, AA.cfop,
  AA.aliqIcms, AA.bcIcmsOpPropria, AA.bcIcmsSt, AA.valorDaOperacao, AA.icmsProprio, AA.icmsSt,
    '[cfopcv]' AS tEI,
  CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN  CFOPES.cfopEfd ELSE CAST(AA.cfop AS INT) END AS cfopcv,
  CASE WHEN CAST(AA.cfop AS INT) < 5000 THEN -AA.valorDaOperacao ELSE AA.valorDaOperacao END AS es_valcon,
  CASE WHEN CAST(AA.cfop AS INT) < 5000 THEN -AA.bcIcmsOpPropria ELSE AA.bcIcmsOpPropria END AS es_bcicms,
  CASE WHEN CAST(AA.cfop AS INT) < 5000 THEN -AA.icmsProprio ELSE AA.icmsProprio END AS es_icms,
  CASE WHEN CAST(AA.cfop AS INT) < 5000 THEN -AA.bcIcmsSt ELSE AA.bcIcmsSt END AS es_bcicmsst,
  CASE WHEN CAST(AA.cfop AS INT) < 5000 THEN -AA.icmsSt ELSE AA.icmsSt END AS es_icmsst,
  EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif
'''
    else:
        nd0 = f'''\
SELECT
  '[DocAtrib_fiscal_DocAtributosDeApuracao]' AS tAA, AA.*,
  '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*,
  '[docAtribTudao]' AS tB, B.*,
  '[idDocAtributos_chaveObs]' AS tCO, CO.*,
  '[cfopEntSai]' AS tCFOPES, CFOPES.*,
  CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN  CFOPES.cfopEfd ELSE CAST(AA.cfop AS INT) END AS cfopcv,
  '[cfopd]' AS tEI, EI.*,
'''
    sql = f'''\
{nd0}
FROM
  DocAtrib_fiscal_DocAtributosDeApuracao AS AA
  LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AA.idDocAtributos
  LEFT OUTER JOIN docAtribTudao AS B ON B.idDocAtributos = A.idDocAtributos
  LEFT OUTER JOIN idDocAtributos_chaveObs AS CO ON CO.idDocAtributos = A.idDocAtributos
  LEFT OUTER JOIN cfopEntSai AS CFOPES ON CFOPES.cfopDfe = CAST(AA.cfop AS INT)
  LEFT OUTER JOIN cfopd AS EI ON EI.cfop = cfopcv
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_03B-DocAtributosDeApuracao_py')
    queryTitle = os.path.basename(fileName)
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)

    cv_db.createIndex(osf, '_fiscal_ItemServicoDeclarado',
                      'idItemServicoDeclarado')
    cv_db.createIndex(osf, 'dfe_fiscal_NfeC170', 'idNFeC170')
    cv_db.createIndex(osf, 'dfe_fiscal_EfdC170', 'idEfdC170')
    if (nivelDetalhe != 0):
        nd0 = f'''\
SELECT AI.idDocAtributosItem,
  '[docAtribBase]' AS tB, 
  B.classifs, substr(A.referencia, 1, 7) AS ref, B.tp_origem, B.origem, A.codSit, A.indEmit, A.indOper, 
  B.Part, B.SituacaoPart, B.dtinifimSitPart,
  B.regPart, B.dtinifimRegPart, 
  B.chave, B.numero, B.uf, B.dtEmissao, B.dtEntSd, B.cfopcvs, B.g1s,  
  B.vlTotalDoc, B.vlBcIcmsProprio, B.vlIcmsProprio, B.vlBcIcmsSt, B.vlIcmsSt, 
  B.EfdPartCodSit, B.EfdPartCfops, B.EfdPartVal, B.EfdPartIcms, 
  B.NatOp, B.descris, CO.obs,
  '[docAtribBaseItem]' AS tA, AI.cstCsosnIcms, AI.indCstCsosn, AI.cfop, AI.COD_NCM, AI.CEST, 
  AI.valorDaOperacao, AI.bcIcmsOpPropria, AI.aliqIcms, AI.icmsProprio, AI.bcIcmsSt, AI.aliqIcmsSt, AI.icmsSt,  
  AI.qtde, AI.unid, AI.aliqEfetOpSemIpi, AI.aliqEfetOpComIpi, AI.mvaCalculado, 
  '[ItemServicoDeclarado]' AS tBI, BI.descricao, BI.codigo,
  '[cfopcv]' AS tEI, 
  CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN  CFOPES.cfopEfd ELSE CAST(AI.cfop AS INT) END AS cfopcv,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN -AI.valorDaOperacao ELSE AI.valorDaOperacao END AS es_valcon,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN -AI.bcIcmsOpPropria ELSE AI.bcIcmsOpPropria END AS es_bcicms,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN -AI.icmsProprio ELSE AI.icmsProprio END AS es_icms,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN -AI.bcIcmsSt ELSE AI.bcIcmsSt END AS es_bcicmsst,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN -AI.icmsSt ELSE AI.icmsSt END AS es_icmsst,
  EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
  '[NfeC170]' AS tH, H.NUM_ITEM, H.CFOP, H.IND_ORIG_MERCADORIA, H.CST_ICMS, H.CSOSN, H.cstCsosnIcms, H.COD_PROD_SERV, H.COD_CEANTRIB, H.COD_NCM, H.DESCR_PROD, 
  H.QTD_TRIB, H.UNID_TRIB, H.PERC_MVA_ICMS_ST, H.Fci, H.CEST, H.VL_FCP, H.VL_BC_ICMS_ST_RETIDO, H.VL_ICMS_ST_RETIDO, H.VL_TOTAL_NFE_PROD,
  '[EfdC170]' AS tI, I.NUM_ITEM, I.CFOP, I.CST_ICMS, I.COD_ITEM, I.DESCR_COMPL, I.QTD   UNID, I.ALIQ_ICMS, I.VL_ICMS, I.ALIQ_ST, I.VL_ICMS_ST, I.VL_ITEM
'''
    else:
        nd0 = f'''\
SELECT
  '[DocAtrib_fiscal_DocAtributosItem]' AS tAI, AI.*,
  '[_fiscal_ItemServicoDeclarado]' AS tBI, BI.*,
  '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*,
  '[docAtribTudao]' AS tB, B.*,
  '[idDocAtributos_chaveObs]' AS tCO, CO.*,
  '[cfopEntSai]' AS tCFOPES, CFOPES.*,
  CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN  CFOPES.cfopEfd ELSE CAST(AI.cfop AS INT) END AS cfopcv,
  '[cfopd]' AS tEI, EI.*,
  '[NfeC170]' AS tH, H.*, '[EfdC170]' AS tI, I.*
'''
    sql = f'''\
{nd0}
FROM
  docatrib_fiscal_DocAtributosItem AS AI
  LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS BI ON BI.idItemServicoDeclarado = AI.idItemServicoDeclarado
  LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AI.idDocAtributos
  LEFT OUTER JOIN docAtribTudao AS B ON B.idDocAtributos = A.idDocAtributos
  LEFT OUTER JOIN idDocAtributos_chaveObs AS CO ON CO.idDocAtributos = A.idDocAtributos
  LEFT OUTER JOIN dfe_fiscal_NfeC170 AS H ON B.tp_origem = 'DFe' AND H.idNFeC170 = AI.idRegistroItem
  LEFT OUTER JOIN dfe_fiscal_EfdC170 AS I ON B.tp_origem = 'EFD' AND I.idEfdC170 = AI.idRegistroItem
  LEFT OUTER JOIN cfopEntSai AS CFOPES ON CFOPES.cfopDfe = CAST(AI.cfop AS INT) 
  LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CFOPES.cfopEfd ELSE CAST(AI.cfop AS INT) END
'''
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_03C-DocAtributosItem_py')
    queryTitle = os.path.basename(fileName)
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, queryTitle)
