"""Pancho é uma recriação simplória e mal feita do Pepe
A ideia é inserir no pacote Cvi5, rodando em modo portátil, sem instalação,
  somente com o que for necessário

Pepe é uma biblioteca em Python para acesso aos sistemas da Sefaz.
Pode ser usado para facilitar a implementação de automatizações diversas.
"""
import PySimpleGUI as sg
import os
import traceback
import getpass

from pycvi.Config import Config
from pycvi.CviPr import CviPr
from pycvi.CviDb import CviDb

config = Config()
cviPr = CviPr(config)

from pycvi.pancho.sistemas.base import Sistema  # noqa: F401
from pycvi.pancho.sistemas.base import AuthenticationError, preparar_metodo  # noqa: F401

# isort: split

# from pepe.sistemas.arquivosdigitais import ArquivosDigitais  # noqa: F401
from pycvi.pancho.sistemas.cadesp import Cadesp  # noqa: F401
# from pepe.sistemas.cassacaocontrib import CassacaoContribuintes  # noqa: F401
# from pepe.sistemas.classificacao import Classificacao  # noqa: F401
# from pepe.sistemas.consultasdfe import ConsultasDfe  # noqa: F401
# from pepe.sistemas.contafiscalicms import ContaFiscalICMS  # noqa: F401
# from pepe.sistemas.dec import Dec  # noqa: F401
# from pepe.sistemas.ecredac import Ecredac  # noqa: F401
# from pepe.sistemas.etc import Etc  # noqa: F401
# from pepe.sistemas.folha import FolhaPagamento  # noqa: F401
# from pepe.sistemas.graph import Graph  # noqa: F401
# from pepe.sistemas.launchpad import LaunchPad  # noqa: F401
# from pepe.sistemas.nfe_credenciamento import NfeCredenciamento  # noqa: F401
# from pepe.sistemas.onedrive import OneDrive  # noqa: F401
# from pepe.sistemas.outlook import Outlook  # noqa: F401
# from pepe.sistemas.pfe import Pfe  # noqa: F401
from pycvi.pancho.sistemas.pgsf import Pgsf  # noqa: F401
# from pepe.sistemas.pgsf_aiimweb import Aiimweb  # noqa: F401
# from pepe.sistemas.sei import Sei  # noqa: F401
# from pepe.sistemas.sgipva import Sgipva  # noqa: F401
# from pepe.sistemas.sharepointonline import SharePointOnline  # noqa: F401
# from pepe.sistemas.sipet import Sipet  # noqa: F401
# from pepe.sistemas.sivei import Sivei  # noqa: F401
# from pepe.sistemas.sped import Sped  # noqa: F401
from pycvi.pancho.sistemas.spsempapel import SpSemPapel  # noqa: F401


def dict_to_tab_separated(dict_obj, file_obj, line_prefix=""):
    for key, value in dict_obj.items():
        if isinstance(value, dict):
            file_obj.write(f"{line_prefix}{key}\n")
            dict_to_tab_separated(value, file_obj, line_prefix + "\t")
        elif isinstance(value, list):
            file_obj.write(f"{line_prefix}{key}\n")
            for i, v in enumerate(value):
                if isinstance(v, dict):
                    file_obj.write(f"{line_prefix}\t{i}\n")
                    dict_to_tab_separated(v, file_obj, line_prefix + "\t\t")
        else:
            file_obj.write(f"{line_prefix}{key}\t{value}\n")


def cadesp_action(window, values: str):
    ie = values[37:49]
    cnpj = values[18:32]
    print(values, ie, cnpj)
    cadesp = Cadesp()
    # from pepe.utils.cert import listar_nomes_certs
    # lst_nome_certs = listar_nomes_certs(store_name="MY", somente_validos=True)
    # nome = str([s for s in lst_nome_certs if ':' in s][0].split(':')[0])
    try:
        cadesp.login_cert(nome_cert="PAULO RICARDO DOS SANTOS OLIM MAROTE")
    except Exception as e:
        traceback.print_exc()
        print(e, "\n\nErro de autenticação, cancelando...")
        return
    ie_pop = sg.popup_get_text(f'Digite a IE desejada:')
    if ie_pop is None:
        print("Pesquisa cancelada...")
        return
    try:
        dict_resultado = cadesp.obter_estabelecimento(ie_pop)
    except Exception as e:
        print(f"Não consegui obter dados da ie {ie_pop} em razão de {e}")
        return
    print(dict_resultado)
    fileName = os.path.join(config.CVI_VAR, f'cadesp_ie_{ie_pop}.txt')
    try:
        with open(fileName, "w") as f:
            dict_to_tab_separated(dict_resultado, f)
            print(f"Pronto. Gerado arquivo {fileName}")
    except Exception as e:
        print(f"Erro ao gerar o arquivo {fileName}.", e)
        return


def pgsf_action(window, values: str):
    ie = values[37:49]
    cnpj = values[18:32]
    print(values, ie, cnpj)
    cvidb_sys = CviDb(os.path.join(config.CVI_VAR), 'cvi_sys.db')
    try:
        cvidb_sys.opendb()
    except Exception as e:
        print(f"Erro fatal na ao abrir o banco de dados "
              + f"{os.path.join(config.CVI_VAR), 'cvi_sys.db'}.", e)
        return False
    pgsf = Pgsf()
    usuario = getpass.getuser()
    print("Entrando no PGSF com o seguinte usuário:", usuario)
    senha_pop = sg.popup_get_text(f'Digite a senha para o usuário {usuario}',
                                  password_char='*')
    if senha_pop is None:
        print("Login cancelado.")
        return
    print("Aguarde uns instantes para o login e a relação das OSFs do usuário",
          usuario)
    window.refresh()
    pgsf.login(usuario=usuario, senha=senha_pop)
    osfs = pgsf.listar_osfs()
    cvidb_sys.exec_commit('DELETE FROM pgsf_list;')
    for osf in osfs:
        # print(osf)
        insert_data = (osf['id'], osf['osf'],
                       cvidb_sys.dtaBarra_AAAA_MM_DD(osf['data']),
                       osf['origem'], osf['forma_acionamento'],
                       osf['razao_social'], osf['ie'],
                       osf['responsavel'], osf['situacao'])
        sql = 'INSERT OR REPLACE INTO pgsf_list VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cvidb_sys.exec_commit(sql, insert_data)
    print("Ok, dados inseridos na tabela pgsf_list")


def sempapel_action(window, values: str):
    ie = values[37:49]
    cnpj = values[18:32]
    print(values, ie, cnpj)
    cvidb_sys = CviDb(os.path.join(config.CVI_VAR), 'cvi_sys.db')
    try:
        cvidb_sys.opendb()
    except Exception as e:
        print(f"Erro fatal na ao abrir o banco de dados "
              + f"{os.path.join(config.CVI_VAR), 'cvi_sys.db'}.", e)
        return False
    sempapel = SpSemPapel()
    print("Entrando no SemPapel. Digite usuário SFP1287296 e senha Sqff2986.3 .")
    user_pop = sg.popup_get_text(f'Digite a nome do usuário')
    senha_pop = sg.popup_get_text(f'Digite a senha para o usuário {user_pop}',
                                  password_char='*')
    if senha_pop is None or user_pop is None:
        print("Login cancelado.")
        return
    sempapel.login(usuario=user_pop, senha=senha_pop)
    print("Login efetuado com sucesso."
          + " Carregando relação dos processos do usuário:",
          user_pop)
    window.refresh()
    docs = sempapel.listar_documentos()
    for doc in docs:
        # print(doc)
        # primeiro divide o campo descr em suas 4 partes, ver exemplo abaixo
        # doc['descr'] = 'Complemento do Assunto: Ressarc. de ICMS-ST ref. 11/16 a 07/17, 10/17, 02/18 a 0518, 07/18, 08/18, 10/18 a 11/19, 02 a 06/20 | Interessado: AUTO POSTO BOM CLIMA LT | CNPJ: 58.293.788/0001-51 | IE: 336.229.890.116'
        try:
            parts = doc['descr'].split('|')
            # Cria um dicionário com as chaves e conteúdo vazio
            d = {'Complemento do Assunto': '',
                 'Interessado': '', 'CNPJ': '', 'IE': ''}
            # Percorre cada parte
            for part in parts:
                for key in d.keys():
                    # Verifica se a chave está na string
                    if key in part:
                        # Se estiver, substitui a chave por uma string vazia
                        part = part.replace(key + ':', '')
                        # Remove espaços em branco das extremidades do valor
                        part = part.strip()
                        d[key] = part
                    insert_data = (doc['codigo'], doc['descr'],
                                   d['Complemento do Assunto'],
                                   d['Interessado'],
                                   d['CNPJ'], d['IE'])
            sql = 'INSERT OR REPLACE INTO sempapel_list VALUES (?, ?, ?, ?, ?, ?)'
            cvidb_sys.exec_commit(sql, insert_data)
        except Exception as e:
            # This will print the error message to the sg.Output element
            print(sql, insert_data, e)
            traceback.print_exc()
    print("Ok, dados inseridos na tabela sempapel_list")
