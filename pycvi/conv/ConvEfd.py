import os
import time

from pycvi.conv.ConvHelpers import ConvHelpers
from pycvi.Config import Config
config = Config()


class ConvEfd:
    def __init__(self, window, filename, result_dir):
        self.window = window
        self.filename = filename
        self.db = ConvHelpers(result_dir, 'efd.db3')
        window.refresh()
        self.db3_open()
        window.refresh()
        self.efdRead()

    def db3_open(self):
        db_path = os.path.join(self.db.dir, self.db.name)
        if os.path.exists(db_path):
            try:
                self.db.connect()
            except Exception as e:
                print(f"Falha ao abrir Banco de Dados {db_path}: {e}")
                return
        else:
            try:
                self.db.connect()
            except Exception as e:
                print(f"Falha ao criar Banco de Dados {db_path}: {e}")
                return

            self.db.exec("""
CREATE TABLE cfopd (cfop int, dfi text, st text, classe text,
    g1 text, c3 text, g2 text, g3 text, descri_simplif text, descri text, pod_creditar text);
""")
            self.db.exec("""
CREATE INDEX cfopd_cfop ON cfopd (cfop ASC);
""")
            self.db.insert_into_table_from_txt(
                os.path.join(config.CVI_RES, 'tabelas', 'cfopd.txt'),
                'cfopd')
            self.db.exec('CREATE TABLE conta_reg (arq, aaaamm, reg, qtd int)')
            self.db.exec("""
CREATE TABLE descri_reg (reg text, proc text, nivel int, descri text, obrig text, ocorr text);
""")
            self.db.exec("""
CREATE INDEX descri_reg_reg ON descri_reg (reg ASC);
""")
            self.db.insert_into_table_from_txt(
                os.path.join(config.CVI_RES, 'tabelas', 'CAT42_Reg_Descri.txt'),
                'descri_reg')
            self.db.exec("""
CREATE TABLE tab4_1_1 (cod text, descri text, mod text);
""")
            self.db.exec("""
CREATE INDEX tab4_1_1_cod ON tab4_1_1 (cod ASC);
""")
            self.db.insert_into_table_from_txt(
                os.path.join(config.CVI_RES, 'tabelas', 'Tab4.1.1.txt'),
                'tab4_1_1')
            self.db.exec("""
CREATE TABLE tab_munic (cod int primary key, uf text, munic text);
""")
            self.db.insert_into_table_from_txt(
                os.path.join(config.CVI_RES, 'tabelas', 'Tabela_Municipios.txt'),
                'tab_munic')

            self.db.exec("""
CREATE TABLE o000 (
  ord int primary key,
  periodo text,
  nome text,
  cnpj int,
  ie text,
  cod_mun text,
  cod_ver int,
  cod_fin int)
""")

            self.db.exec("""
CREATE TABLE o150 (
  ord int primary key,
  cod_part text,
  nome text,
  cod_pais int,
  cnpj int,
  cpf int,
  ie text,
  cod_mun text)
""")
            self.db.exec('CREATE INDEX "o150_reg_prim" ON o150 (cod_part ASC)')
            # 0200 - Tabela de Identificação do Item (Produtos e Serviços)
            self.db.exec("""
CREATE TABLE o200 (
  ord int primary key,
  cod_item text, descr_item text, cod_barra text, unid_inv text,
  cod_ncm text, aliq_icms real, cest int)
""")
            self.db.exec('CREATE INDEX "o200_reg_prim" ON o200 (cod_item ASC)')
            # 0205 - Alteração do Item
            self.db.exec("""
CREATE TABLE o205 (
  ord int primary key,
  cod_item text, cod_ant_item, descr_ant_item)
""")
            # REGISTRO 1050 – REGISTRO DE SALDOS
            self.db.exec("""
CREATE TABLE l050 (
  ord int primary key,
  cod_item text, qtd_ini real, icms_tot_ini real, qtd_fim real, icms_tot_fim reak)
""")
            # REGISTRO 1100 – REGISTRO DE DOCUMENTO FISCAL ELETRÔNICO
            # PARA FINS DE RESSARCIMENTO DE SUBSTITUIÇÂO TRIBUTÁRIA OU ANTECIPAÇÃO.
            self.db.exec("""
CREATE TABLE l100 (
  ord int primary key,
  chv_doc text, data text, num_item int, ind_oper int, cod_item text,
  cfop int, qtd real, icms_tot real, vl_confr real, cod_legal int)
""")
            # REGISTRO 1200 – REGISTRO DE DOCUMENTO FISCAL NÃO-ELETRÔNICO
            # PARA FINS DE RESSARCIMENTO DE SUBSTITUIÇÂO TRIBUTÁRIA – SP
            self.db.exec("""
CREATE TABLE l200 (
  ord int primary key,
  cod_part text, cod_mod text, ecf_fab text, ser text, num_doc int, num_item int, ind_oper int,
  data text, cfop int, cod_item text, qtd real, icms_tot real, vl_confr real, cod_legal int)
""")
            # REGISTRO 5000 – Processamento Portaria CAT 42/2018
            # - Auxiliar - Arquivo ACOLHIDO
            self.db.exec("""
CREATE TABLE s000 (
  ord int primary key,
  todo1, cod_item text)
""")
            # REGISTRO 5001 – Processamento Portaria CAT 42/2018 - Arquivo ACOLHIDO
            self.db.exec("""
CREATE TABLE s001 (
  ord int primary key,
  todo1, todo2, date text, chv_doc text, ecf_fab text,
  cod_mod text, ser text, num_doc int, cod_part text,
  cfop int, num_item int, cod_item text, ind_oper int,
  cod_legal int, ord2 int, e_s, todo3,
  qtd_ent real, icms_tot_ent real,
  qtd_sai real, icms_uni_sai real,
  tot_cod_legal1 real, tot_cod_legal2 real, tot_cod_legal3 real,
  tot_cod_legal4 real, tot_com_sub real,
  conf_20 real, conf_21 real,
  qtd_saldo real, icms_saldo real,
  val_ressarc real, val_complem real, cred_op_proprias real)
""")
            # REGISTRO 5010 – Processamento Portaria CAT 42/2018 - Totais - Arquivo ACOLHIDO
            self.db.exec("""
CREATE TABLE s010 (
  ord int primary key,
  todo1, todo2, todo3, todo4, todo5, todo6, todo7, todo8, todo9, todo10, todo11, todo12, todo13)
""")
            # REGISTRO 5100 – Processamento Portaria CAT 42/2018 - Log - Arquivo ACOLHIDO
            self.db.exec("""
CREATE TABLE s100 (
  ord int primary key,
  todo1, todo2, todo3, todo4, todo5, todo6, todo7, todo8)
""")

    def cat42Read(self):
        self.ilidos = 1
        self.ianomes = 601
        self.a_conta_reg = dict()
        self.aaaamm = ''
        # txt_encoding = 'ANSI'
        self.cat42difis = False
        start_time = time.time()  # Armazena o tempo inicial
        # self.db.execute('BEGIN;')
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                while True:
                    line = file.readline()
                    if not line:
                        break  # Fim do arquivo
                    self.cat42ReadLine(line)  # noqa: F401
                    if self.ilidos % 50000 == 0:
                        print("Tempo decorrido:", time.time() - start_time, "segundos")
                        # self.db.execute('COMMIT;')
                        # self.db.execute('BEGIN;')
                    self.ilidos += 1
        except Exception as e:
            print(f"Erro ao abrir ou ler o arquivo {self.filename}", e)
        self.db.conn.commit()
        for indice, valor in self.a_conta_reg.items():
            sql = f"INSERT INTO conta_reg VALUES (?, ?, ?, ?)"
            fields = [self.filename, self.aaaamm, indice, valor]
            self.db.cursor.execute(sql, fields)
        self.db.conn.commit()

        print(f"Parte 1 - Leitura finalizada: {self.ilidos} linhas do arquivo",
              f"{self.filename}")
        print("Tempo decorrido:", time.time() - start_time, "segundos\n")

    def cat42ReadLine(self, linha):
        if linha[:22] == '|0000|RessarcimentoSt|':
            self.cat42difis = True
        if not self.cat42difis:
            linha = '|' + linha
        campos = linha.strip().split('|')
        if len(campos) <= 1:
            return
        if campos[1] == '0000':
            if self.cat42difis:
                self.ianomes = int(campos[3][-2:] + campos[3][:2])
            else:
                self.ianomes = int(campos[2][-2:] + campos[2][:2])
        iord = self.ilidos + self.ianomes * 10000000

        if len(campos[1]) == 4:
            self.a_conta_reg[campos[1]] = self.a_conta_reg.get(campos[1], 0) + 1

        # campos = [self.db.execute("SELECT quote(?)", (valor,)).fetchone()[0] for valor in campos]

        if campos[1] == '0000':
            self.aaaamm = campos[2][-4:] + campos[2][:2]
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6], campos[7], campos[8]]
            self.db.insert('o000', fields)

        if campos[1] == '0150':
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6], campos[7], campos[8]]
            self.db.insert('o150', fields)

        if campos[1] == '0200':
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6],
                      campos[7].replace('.', '').replace(',', '.'), campos[8]]
            self.db.insert('o200', fields)

        if campos[1] == '0205':
            fields = [iord, campos[2], campos[3], campos[4]]
            self.db.insert('o205', fields)

        if campos[1] == '1050':
            fields = [iord, campos[2],
                      campos[3].replace('.', '').replace(',', '.'),
                      campos[4].replace('.', '').replace(',', '.'),
                      campos[5].replace('.', '').replace(',', '.'),
                      campos[6].replace('.', '').replace(',', '.')]
            self.db.insert('l050', fields)

        if campos[1] == '1100':
            fields = [iord, campos[2], self.db.dtaSPED(campos[3]),
                      campos[4], campos[5], campos[6], campos[7],
                      campos[8].replace('.', '').replace(',', '.'),
                      campos[9].replace('.', '').replace(',', '.'),
                      campos[10].replace('.', '').replace(',', '.'),
                      campos[11]]
            self.db.insert('l100', fields)

        if campos[1] == '1200':
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6], campos[7], campos[8],
                      self.db.dtaSPED(campos[9]),
                      campos[10], campos[11],
                      campos[12].replace('.', '').replace(',', '.'),
                      campos[13].replace('.', '').replace(',', '.'),
                      campos[14].replace('.', '').replace(',', '.'),
                      campos[15]]
            self.db.insert('l200', fields)

        if campos[1] == '5000':
            fields = [iord, campos[2], campos[3]]
            self.db.insert('s000', fields)

        if campos[1] == '5001':
            fields = [iord, campos[2], campos[3], self.db.dtaSPED(campos[4]),
                      campos[5], campos[6], campos[7], campos[8],
                      campos[9], campos[10], campos[11], campos[12],
                      campos[13], campos[14], campos[15], campos[16],
                      campos[17], campos[18],
                      campos[19].replace('.', '').replace(',', '.'),
                      campos[20].replace('.', '').replace(',', '.'),
                      campos[21].replace('.', '').replace(',', '.'),
                      campos[22].replace('.', '').replace(',', '.'),
                      campos[23].replace('.', '').replace(',', '.'),
                      campos[24].replace('.', '').replace(',', '.'),
                      campos[25].replace('.', '').replace(',', '.'),
                      campos[26].replace('.', '').replace(',', '.'),
                      campos[27].replace('.', '').replace(',', '.'),
                      campos[28].replace('.', '').replace(',', '.'),
                      campos[29].replace('.', '').replace(',', '.'),
                      campos[30].replace('.', '').replace(',', '.'),
                      campos[31].replace('.', '').replace(',', '.'),
                      campos[32].replace('.', '').replace(',', '.'),
                      campos[33].replace('.', '').replace(',', '.'),
                      campos[34].replace('.', '').replace(',', '.'),
                      ]
            self.db.insert('s001', fields)

        if campos[1] == '5010':
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6], campos[7], campos[8],
                      campos[9], campos[10], campos[11], campos[12],
                      campos[13], campos[14]]
            self.db.insert('s010', fields)

        if campos[1] == '5100':
            fields = [iord, campos[2], campos[3], campos[4],
                      campos[5], campos[6], campos[7], campos[8],
                      campos[9]]
            self.db.insert('s100', fields)
