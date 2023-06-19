import os
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _95_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando 95 Específico - Verificações na osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()
    sql = '''\
SELECT AI.idDocAtributosItem, A.codSit,
  B.chave, A.dtEntSd,
  '[#ItemServicoDeclarado#]' AS `#tBI#`, BI.codigo, BI.cnpj, BI.descricao,
  '[#cfopcv#]' AS `#tEI#`,
  CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN
      CFOPES.cfopEfd ELSE CAST(AI.cfop AS INT) END AS cfopcv,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.valorDaOperacao ELSE AI.valorDaOperacao END AS es_valcon,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.bcIcmsOpPropria ELSE AI.bcIcmsOpPropria END AS es_bcicms,
  AI.aliqIcms,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.icmsProprio ELSE AI.icmsProprio END AS es_icms,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.bcIcmsSt ELSE AI.bcIcmsSt END AS es_bcicmsst,
  AI.aliqIcmsSt,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.icmsSt ELSE AI.icmsSt END AS es_icmsst,
  CASE WHEN CAST(AI.cfop AS INT) < 5000 THEN
      -AI.qtde ELSE AI.qtde END AS es_qtde,
  AI.unid,
  '[#cfopcv_pt2#]' AS `#tEI2#`,
  EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
  '[#NfeC170#]' AS `#tH#`,
  CASE WHEN A.indEmit = 1 THEN 'Terceiro' ELSE 'Em.Prop.' END AS tpNFeC170,
  CASE WHEN A.indEmit = 1 THEN H.NUM_ITEM ELSE W.NUM_ITEM END AS NUM_ITEM,
  CASE WHEN A.indEmit = 1 THEN H.CFOP ELSE W.CFOP END AS CFOP,
  CASE WHEN A.indEmit = 1 THEN
      H.IND_ORIG_MERCADORIA ELSE W.IND_ORIG_MERCADORIA END
      AS IND_ORIG_MERCADORIA,
  CASE WHEN A.indEmit = 1 THEN
      H.CST_ICMS ELSE W.CST_ICMS END AS CST_ICMS,
  CASE WHEN A.indEmit = 1 THEN
      H.CSOSN ELSE W.CSOSN END AS CSOSN,
  CASE WHEN A.indEmit = 1 THEN
      H.COD_PROD_SERV ELSE W.COD_PROD_SERV END AS COD_PROD_SERV,
  CASE WHEN A.indEmit = 1 THEN
      H.COD_CEANTRIB ELSE W.COD_CEANTRIB END AS COD_CEANTRIB,
  CASE WHEN A.indEmit = 1 THEN
      H.COD_NCM ELSE W.COD_NCM END AS COD_NCM,
  CASE WHEN A.indEmit = 1 THEN
      H.DESCR_PROD ELSE W.DESCR_PROD END AS DESCR_PROD,
  CASE WHEN A.indEmit = 1 THEN
      H.IND_ITEM_COMPOE_TOTAL ELSE W.IND_ITEM_COMPOE_TOTAL END
      AS IND_ITEM_COMPOE_TOTAL,
  CASE WHEN A.indEmit = 1 THEN
      H.QTD_TRIB ELSE W.QTD_TRIB END AS QTD_TRIB,
  CASE WHEN A.indEmit = 1 THEN
      H.UNID_TRIB ELSE W.UNID_TRIB END AS UNID_TRIB,
  CASE WHEN A.indEmit = 1 THEN
      H.VL_UNIT_TRIB ELSE W.VL_UNIT_TRIB END AS VL_UNIT_TRIB,
  CASE WHEN A.indEmit = 1
      THEN H.VL_TOTAL_NFE_PROD ELSE W.VL_TOTAL_NFE_PROD END
      AS VL_TOTAL_NFE_PROD,
  CASE WHEN A.indEmit = 1
      THEN H.VL_PROD ELSE W.VL_PROD END AS VL_PROD,
  CASE WHEN A.indEmit = 1
      THEN H.VL_DESCONTO ELSE W.VL_DESCONTO END AS VL_DESCONTO,
  CASE WHEN A.indEmit = 1
      THEN H.VL_FRETE ELSE W.VL_FRETE END AS VL_FRETE,
  CASE WHEN A.indEmit = 1
      THEN H.VL_DESP_ACESS ELSE W.VL_DESP_ACESS END AS VL_DESP_ACESS,
  CASE WHEN A.indEmit = 1
      THEN H.VL_SEGURO ELSE W.VL_SEGURO END AS VL_SEGURO,
  CASE WHEN A.indEmit = 1
      THEN H.PERC_RED_BC_ICMS ELSE W.PERC_RED_BC_ICMS END AS PERC_RED_BC_ICMS,
  CASE WHEN A.indEmit = 1
      THEN H.VL_BC_ICMS ELSE W.VL_BC_ICMS END AS VL_BC_ICMS,
  CASE WHEN A.indEmit = 1
      THEN H.PERC_ALIQ_ICMS ELSE W.PERC_ALIQ_ICMS END AS PERC_ALIQ_ICMS,
  CASE WHEN A.indEmit = 1
      THEN H.VL_ICMS ELSE W.VL_ICMS END AS VL_ICMS,
  CASE WHEN A.indEmit = 1
      THEN H.CEST ELSE W.CEST END AS CEST,
  CASE WHEN A.indEmit = 1
      THEN H.PERC_MVA_ICMS_ST ELSE W.PERC_MVA_ICMS_ST END AS PERC_MVA_ICMS_ST,
  CASE WHEN A.indEmit = 1
      THEN H.PERC_RED_BC_ICMS_ST ELSE W.PERC_RED_BC_ICMS_ST END
      AS PERC_RED_BC_ICMS_ST,
  CASE WHEN A.indEmit = 1
      THEN H.VL_BC_ICMS_ST ELSE W.VL_BC_ICMS_ST END AS VL_BC_ICMS_ST,
  CASE WHEN A.indEmit = 1
      THEN H.PERC_ALIQ_ICMS_ST ELSE W.PERC_ALIQ_ICMS_ST END
      AS PERC_ALIQ_ICMS_ST,
  CASE WHEN A.indEmit = 1
      THEN H.VL_ICMS_ST ELSE W.VL_ICMS_ST END AS VL_ICMS_ST,
  CASE WHEN A.indEmit = 1
      THEN H.VL_BC_ICMS_ST_RETIDO ELSE W.VL_BC_ICMS_ST_RETIDO END
      AS VL_BC_ICMS_ST_RETIDO,
  CASE WHEN A.indEmit = 1
      THEN H.VL_ICMS_ST_RETIDO ELSE W.VL_ICMS_ST_RETIDO END
      AS VL_ICMS_ST_RETIDO,
  CASE WHEN A.indEmit = 1
      THEN H.VL_ICMS_DESONERADO ELSE W.VL_ICMS_DESONERADO END
      AS VL_ICMS_DESONERADO,
  CASE WHEN A.indEmit = 1
      THEN H.VL_ICMS_DIFERIDO ELSE W.VL_ICMS_DIFERIDO END AS VL_ICMS_DIFERIDO,
  CASE WHEN A.indEmit = 1
      THEN H.VL_II ELSE W.VL_II END AS VL_II,
  CASE WHEN A.indEmit = 1
      THEN H.Fci ELSE W.Fci END AS Fci,
  CASE WHEN A.indEmit = 1
      THEN H.VL_IPI ELSE W.VL_IPI END AS VL_IPI,
  '[#EfdC170#]' AS `#tI#`, I.NUM_ITEM, I.COD_ITEM, I.DESCR_COMPL,
  I.CST_ICMS, I.CFOP, I.QTD, I.UNID, I.VL_ITEM, I.VL_DESC, I.IND_MOV,
  I.ALIQ_ICMS, I.VL_ICMS, I.ALIQ_ST, I.VL_ICMS_ST,
  I.COD_NAT, I.VL_BC_ICMS, I.ALIQ_ICMS, I.VL_ICMS,
  I.VL_BC_ICMS_ST, I.ALIQ_ST, I.VL_ICMS_ST,
  I.VL_BC_IPI, I.ALIQ_IPI, I.VL_IPI,
  I.VL_BC_PIS, I.ALIQ_PIS_percentual, I.VL_PIS,
  I.VL_BC_COFINS, I.ALIQ_COFINS_percentual, I.VL_COFINS,
  I.COD_CTA TEXT, I.aliqEfetOpSemIpi, I.aliqEfetOpComIpi, I.mvaCalculado,
  '[#docatrib_fiscal_DocAtributosItem#]' AS `#tA#`, AI.idRegistroDeOrigem,
  AI.cstCsosnIcms, AI.indCstCsosn, AI.indOrigem, AI.cfop, AI.COD_NCM, AI.CEST,
  AI.aliqEfetOpSemIpi, AI.aliqEfetOpComIpi, AI.mvaCalculado
FROM
  -- ## Veja o WHERE lá embaixo! ##
  -- Como é específico,
  --   vamos partir apenas do livro SPED ! (B.tp_origem = 'EFD')
  docatrib_fiscal_DocAtributosItem AS AI
  LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS BI
      ON BI.idItemServicoDeclarado = AI.idItemServicoDeclarado
  LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A
      ON A.idDocAtributos = AI.idDocAtributos
  LEFT OUTER JOIN idDocAtributos_compl AS B
      ON B.idDocAtributos = A.idDocAtributos
  -- CFOP é CAST(AI.cfop AS INT) via de regra, ou CFOPES.cfopEfd
  --    apenas se for NFe de terceiros e registro de NFe (não EFD)
  LEFT OUTER JOIN cfopEntSai AS CFOPES
      ON CFOPES.cfopDfe = CAST(AI.cfop AS INT)
  LEFT OUTER JOIN cfopd AS EI
      ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1
          THEN CFOPES.cfopEfd ELSE CAST(AI.cfop AS INT) END
  -- NfeC170, se for Em.Própria, vai buscar diretamente em idDocAtributosItem
  -- Veja na planilha MapaItemNFe, de TrabPaulo.xlsm, que:
  --   Não existe EfdC170 para NFe emissão própria !
  --   Por isso, idRegistroItem de DocAtrib_fiscal_DocAtributosItem quando
  --   indEmit for igual a Zero, é sempre um link para dfe_fiscal_NfeC170,
  --   mesmo quando o registro de DocAtrib_fiscal_DocAtributosItem for de EFD!
  LEFT OUTER JOIN idDocAtributos_compl_item AS BB
      ON BB.idDocAtributosItem = AI.idDocAtributosItem AND A.indEmit = 0
  LEFT OUTER JOIN dfe_fiscal_NfeC170 AS W
      ON W.idNFeC170 = BB.idRegistroItem AND A.indEmit = 0
  --   Como explicado acima, só temos EfcC170 em NFe de terceiros
  LEFT OUTER JOIN dfe_fiscal_EfdC170 AS I
      ON I.idEfdC170 = AI.idRegistroItem AND A.indEmit = 1
  -- Todo o resto abaixo é para buscar o item da NFe (NfeC170) se for NFe
  --    de terceiros. Vamos primeiro localizar a NFe correspondente ao EFd
  --    Lembra que estamos partindo apenas do livro SPED ?
  --    Agora, para cada B.tp_origem = 'EFD',
  --        vamos procurar o correspondente B.tp_origem = 'DFe'
  LEFT OUTER JOIN idDocAtributos_compl AS Y
      ON Y.chave = B.chave AND Y.tp_origem = 'DFe'  AND A.indEmit = 1
  -- Temos agora Y.docAtributos da NFe de terceiros que corresponde ao item
  --    da EFD. Agora vai buscar os dados do Mesmo Item da NFe de terceiros,
  --    igual ao Item da EFD
  LEFT OUTER JOIN idDocAtributos_compl_item AS HH
      ON HH.idDocAtributos = Y.idDocAtributos AND HH.NUM_ITEM = I.NUM_ITEM
      AND A.indEmit = 1
  -- idDocAtributos_compl_item AS HH traz o idRegistroItem que procuro
  LEFT OUTER JOIN dfe_fiscal_NfeC170 AS H
      ON H.idNFeC170 = HH.idRegistroItem AND A.indEmit = 1
WHERE B.tp_origem = 'EFD' AND A.codsit NOT IN (2, 3, 4, 5)
'''
    ah.createTableFromSql(window, cv_db, 'especifico', sql)

    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Audit_95-Especifico_py')
    sql = f'''\
SELECT A.*,
  '[#chaveNroTudao#]' AS tZ, Z.*
  FROM especifico AS A
  LEFT OUTER JOIN chaveNroTudao AS Z ON Z.chave = A.chave
  WHERE Z.codSit = '<>2-3-4-5'
      AND A.dtEntSd > '2010-00-00'
      AND A.g1 IN ('1-Receitas', '2-Compras Insumos')
  LIMIT 500000
'''
    ah.sqlToData_run_aux(window, cv_db, sql, fileName,
                         os.path.basename(fileName))
