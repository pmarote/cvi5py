"""Módulo com definições do sistema Cadesp."""


import os
import re

from bs4 import BeautifulSoup
from selectorlib import Extractor
from unidecode import unidecode

from pycvi.pancho import AuthenticationError, Sistema, preparar_metodo
from pycvi.pancho.utils.html import (
    converter_para_pdf,
    extrair_validadores_aspnet,
    scrape_tabela,
)
from pycvi.pancho.utils.login import login_identity_cert
from pycvi.pancho.utils.texto import (
    formatar_cep,
    formatar_cnae,
    formatar_cnpj,
    formatar_cpf,
    formatar_crc,
    formatar_data,
    formatar_ie,
    formatar_nire,
)

URL_BASE = "https://www.cadesp.fazenda.sp.gov.br/"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v003/"
    "Sefaz.Identity.STS.PortalSSO/LoginPortalSSO.aspx"
)
URL_WTREALM = "https://www.cadesp.fazenda.sp.gov.br/Pages/AutenticacaoSTS.aspx"
WCTX = (
    "rm=0&id=ctl00$conteudoPaginaPlaceHolder$loginControl"
    "$FederatedPassiveSignInCertificado"
)
CLAIM_SETS = "80F00007"
TIPO_LOGIN = "3"
AUTO_LOGIN = "1"

CTL = "ctl00$conteudoPaginaPlaceHolder"  # String usada em vários campos nos POSTs

from .cadesp_constants import DELEGACIAS_PARAMETROS
from .cadesp_constants import DELEGACIAS_SOLICITACOES
from .cadesp_constants import POSTOS_FISCAIS_PARAMETROS
from .cadesp_constants import POSTOS_FISCAIS_SOLICITACOES
from .cadesp_constants import CNAES
from .cadesp_constants import TIPO_ESTABELECIMENTO
from .cadesp_constants import SITUACAO_CADASTRAL
from .cadesp_constants import MUNICIPIO
from .cadesp_constants import SITUACAO_SOLICITACAO
from .cadesp_constants import ESTAGIO_SOLICITACAO
from .cadesp_constants import TIPO_SOLICITACAO

class Cadesp(Sistema):
    """Representa o sistema [Cadesp](https://www.cadesp.fazenda.sp.gov.br/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        print("#DEBUG#Cadesp#Classe Cadesp iniciada")
        """Cria um objeto da classe Cadesp.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/99.0.4844.83 Safari/537.36"
            }
        )
        # print("#DEBUG#Cadesp#self.session.headers#", self.session.headers)
        self._url_token = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        if self._url_token:
            r = self.session.get(URL_BASE + self._url_token + "/Pages/Principal.aspx")

            return (
                "ctl00_menuPlaceHolder_menuControl1_LoginView1_menuSuperior" in r.text
            )

        return False

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        print("#DEBUG#Cadesp#login_cert")
        self._pre_login()

        outros_params = {"TipoLogin": TIPO_LOGIN, "AutoLogin": AUTO_LOGIN}

        cookies_aute, r = login_identity_cert(
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=URL_WTREALM,
            claim_sets=CLAIM_SETS,
            wctx=WCTX,
            outros_params=outros_params,
            nome_cert=nome_cert,
            cookies=self.session.cookies,
        )
        self.session.cookies.update(cookies_aute)
        self._url_token = r.url.split("/")[3]
        print("#DEBUG#Cadesp#self._url_token = ", self._url_token)

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def listar_estabelecimentos(
        self,
        ie: str = "",
        cnpj: str = "",
        razao_social: str = "",
        contabilista_crc: str = "",
        contabilista_cpf: str = "",
        contabilista_cnpj: str = "",
        participante_cpf: str = "",
        participante_cnpj: str = "",
        procurador_cpf: str = "",
        procurador_cnpj: str = "",
        delegacia: str = "",
        posto_fiscal: str = "",
        tipo_estabelecimento: str = "",
        situacao_cadastral: str = "",
        cnae_principal: str = "",
        cnae_secundario: str = "",
        cep: str = "",
        num: int = None,
        logradouro: str = "",
        municipio: str = "",
    ) -> list:
        """Lista estabelecimentos em conformidade com os argumentos passados.

        Consulte também `listar_estabelecimentos_por_endereço`.

        Args:
            ie (str, optional): Inscrição Estadual (IE) do estabelecimento, com ou sem
                pontuação. Valor padrão é "".
            cnpj (str, optional): CPNJ completo do estabelecimento, com ou sem
                pontuação. Valor padrão é "".
            razao_social (str, optional): Razão Social da empresa. Valor padrão é "".
            contabilista_crc (str, optional): Registro no Conselho Regional de
                Contabilidade (CRC) do contabilista responsável pelo estabelecimento.
                Valor padrão é "".
            contabilista_cpf (str, optional): CPF do contabilista responsável, com ou
                sem pontuação. Valor padrão é "".
            contabilista_cnpj (str, optional): CNPJ do contabilista responsável, com ou
                sem pontuação. Valor padrão é "".
            participante_cpf (str, optional): CPF de algum participante do quadro
                societário da empresa, com ou sem pontuação. Valor padrão é "".
            participante_cnpj (str, optional): CNPJ de algum participante do quadro
                societário da empresa, com ou sem pontuação. Valor padrão é "".
            procurador_cpf (str, optional): CPF do procurador, com ou sem pontuação.
                Valor padrão é "".
            procurador_cnpj (str, optional): CPF do procurador, com ou sem pontuação.
                Valor padrão é "".
            delegacia (str, optional): Delegacia a qual o estabelecimento está
                vinculado, no formato "DRT-XX - CIDADE" ou "DRTC-XX - SÃO PAULO". A
                lista de todas as delegacias aceitas nesse parâmetro são as chaves do
                dicionário `DELEGACIAS_PARAMETROS`. Valor padrão é "".
            posto_fiscal (str, optional): Posto fiscal ao qual o estabelecimento está
                vinculado, no formato "PF-XX" ou "PFC-XX".  A lista de todos os
                postos fiscais aceitos nesse parâmetro são as chaves do dicionário
                `POSTOS_FISCAIS_PARAMETROS`. Valor padrão é "".
            tipo_estabelecimento (str, optional): Tipo do estabelecimento. Pode receber
                `""`, `"PESSOA JURÍDICA E DEMAIS ENTIDADES"` ou `"PRODUTOR RURAL"`.
                Valor padrão é "".
            situacao_cadastral (str, opcional): Situação cadastral do estabelecimento. A
                lista de todas as situações aceitas nesse parâmetro são as chaves do
                dicionário `SITUACAO_CADASTRAL`. Valor padrão é "".
            cnae_principal (str, optional): CNAE principal da empresa no formato
                XX.XX-X/XX. Valor padrão é "".
            cnae_secundario (str, optional): CNAE secundário da empresa no formato
                XX.XX-X/XX. Valor padrão é "".
            cep (str, optional): CEP do estabelecimento. Valor padrão é "".
            num (int, optional): Número do logradouro do estabelecimento.
            logradouro (str, optional): Nome do logradouro do estabelecimento. Valor
                padrão é "".
            municipio (str, optional): Município do estabelecimento. A lista de todos os
                municípios aceitos nesse parâmetro são as chaves do dicionário
                `MUNICIPIO` Valor padrão é "".

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            um estabelecimento.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        # TODO: juntar métodos de listagem
        if cep or num or logradouro or municipio:
            # TODO: Avisar que só endereços serão considerados
            return self.listar_estabelecimentos_por_endereco(
                cep=cep,
                num=num,
                logradouro=logradouro,
                municipio=municipio,
                tipo_estabelecimento=tipo_estabelecimento,
                situacao_cadastral=situacao_cadastral,
            )

        html = self._consultar_parametros(
            ie=ie,
            cnpj=cnpj,
            razao_social=razao_social,
            contabilista_crc=contabilista_crc,
            contabilista_cpf=contabilista_cpf,
            contabilista_cnpj=contabilista_cnpj,
            participante_cpf=participante_cpf,
            participante_cnpj=participante_cnpj,
            procurador_cpf=procurador_cpf,
            procurador_cnpj=procurador_cnpj,
            delegacia=delegacia,
            posto_fiscal=posto_fiscal,
            tipo_estabelecimento=tipo_estabelecimento,
            situacao_cadastral=situacao_cadastral,
            cnae_principal=cnae_principal,
            cnae_secundario=cnae_secundario,
        )

        soup = BeautifulSoup(html, "html.parser")
        a_list = soup.find_all(
            "a",
            id=lambda id_text: id_text
            and id_text.endswith("_linkButtonEstabelecimento"),
        )
        estabs = []

        for a in a_list:
            parent_tr = a.parent.parent
            tds = parent_tr.find_all("td", class_="dadoDetalhe")
            dados_estab = {}
            dados_estab["ie"] = tds[0].text.strip()
            dados_estab["cnpj"] = tds[1].text.strip()
            dados_estab["nome_empresarial"] = tds[2].text.strip()
            dados_estab["situacao"] = tds[3].text.strip()
            dados_estab["posto_fiscal"] = tds[4].text.strip()
            estabs.append(dados_estab)

        return estabs

    @preparar_metodo
    def listar_estabelecimentos_por_endereco(
        self,
        cep: str = "",
        num: int = None,
        logradouro: str = "",
        municipio: str = "",
        tipo_estabelecimento: str = "",
        situacao_cadastral: str = "",
    ) -> list:
        """Lista estabelecimentos em conformidade com os argumentos passados.

        Consulte também `listar_estabs`.

        Args:
            cep (str, optional): CEP do estabelecimento. Valor padrão é "".
            num (int, optional): Número do logradouro do estabelecimento.
            logradouro (str, optional): Nome do logradouro do estabelecimento. Valor
                padrão é "".
            municipio (str, optional): Município do estabelecimento. A lista de todos os
                municípios aceitos nesse parâmetro são as chaves do dicionário
                `MUNICIPIO` Valor padrão é "".
            tipo_estabelecimento (str, optional): Tipo do estabelecimento. Pode receber
                `""`, `"PESSOA JURÍDICA E DEMAIS ENTIDADES"` ou `"PRODUTOR RURAL"`.
                Valor padrão é "".
            situacao_cadastral (str, opcional): Situação cadastral do estabelecimento. A
                lista de todas as situações aceitas nesse parâmetro são as chaves do
                dicionário `SITUACAO_CADASTRAL`. Valor padrão é "".

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            um estabelecimento.
        """
        html = self._consultar_endereco(
            cep=cep,
            num=num,
            logradouro=logradouro,
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento,
            situacao_cadastral=situacao_cadastral,
        )

        soup = BeautifulSoup(html, "html.parser")
        a_list = soup.find_all(
            "a",
            id=lambda id_text: id_text and id_text.endswith("_linkButtonEndereco"),
        )
        estabs = []

        for a in a_list:
            parent_tr = a.parent.parent
            tds = parent_tr.find_all("td", class_="dadoDetalhe")
            dados_estab = {}
            dados_estab["nome_logradouro"] = tds[0].text.strip()
            dados_estab["numero"] = tds[1].text.strip()
            dados_estab["complemento"] = tds[2].text.strip()
            dados_estab["municipio"] = tds[3].text.strip()
            dados_estab["ie"] = tds[4].text.strip()
            dados_estab["cnpj"] = tds[5].text.strip()
            dados_estab["nome_empresarial"] = tds[6].text.strip()
            dados_estab["situacao"] = tds[7].text.strip()
            estabs.append(dados_estab)

        return estabs

    @preparar_metodo
    def listar_solicitacoes(self, ie: str) -> list:
        """Lista as solicitações associadas a um estabelecimento.

        Args:
            ie (str): Inscrição Estadual (IE) do estabelecimento, com ou sem pontuação.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            uma solicitação.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        ie = formatar_ie(ie)[1]
        html = self._consultar_solicitacoes_parametros(ie=ie)

        # Se a IE tem apenas uma solicitação, o sistema irá pular a página de listagem
        # e abrirá diretamente a página da solicitação. Nesses casos, simulamos a
        # listagem de solicitação única
        if Cadesp._eh_pagina_solicitacao(html):
            solicitacao = Cadesp._scrape_solicitacao(html)
            solicitacao_simples = {
                "Entrada na SEFAZ-SP": solicitacao["Identificação"]["Data de Entrada"],
                "Nº Recibo": solicitacao["Identificação"]["Nº do Recibo"],
                "CNPJ": solicitacao["Estabelecimento"]["Nº CNPJ"],
                "Nº Ato Ofício": (
                    solicitacao["Identificação"]["Nº Ato Ofício"]
                    if solicitacao["Identificação"]["Nº Ato Ofício"] != "-"
                    else ""
                ),
                "Status": solicitacao["Situação"],
                "Estágio": solicitacao["Movimentos"][0]["Estágio"],
            }

            return [solicitacao_simples]

        return Cadesp._scrape_solicitacoes(html)

    @staticmethod
    def _eh_pagina_solicitacao(html) -> bool:
        return "Consulta de Solicitações" in html

    @staticmethod
    def _scrape_solicitacoes(html):
        soup = BeautifulSoup(html, "html.parser")

        return scrape_tabela(
            "multi",
            soup=soup.find(id="ctl00_conteudoPaginaPlaceHolder_solicitacaoGridView"),
        )

    @preparar_metodo
    def obter_estabelecimento(self, ie: str) -> dict:
        """Obtém detalhes de um dado estabelecimento.

        Args:
            ie (str): Inscrição Estadual (IE) do estabelecimento, com ou sem pontuação.

        Returns:
            Um dicionário que contém as propriedades de um estabelecimento.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        ie = formatar_ie(ie)[1]
        html = self._cadastro_completo_ie(ie=ie)

        return Cadesp._scrape_obter_estabelecimento(html)

    @staticmethod
    def _scrape_obter_estabelecimento(html):
        caminho_yaml = os.path.join(
            os.path.dirname(__file__), "yaml", "cadesp_cadastro_completo.yaml"
        )
        e = Extractor.from_yaml_file(caminho_yaml)

        estab = e.extract(html)

        # Ajustando participantes
        estab["participantes"] = []
        campos = [
            "cpf_cnpj",
            "nome",
            "qualificacao",
            "participacao_capital_social",
            "data_entrada",
        ]
        soup = BeautifulSoup(html, "html.parser")
        participante_tables = soup.find_all(
            id=lambda e: e and e.endswith("dlParticipanteDadosAdicionais")
        )

        for table in participante_tables:
            table_dados = table.previous_sibling.previous_sibling
            valores = [td.text.strip() for td in table_dados.find_all("td")]
            participante = {campo: valor for campo, valor in zip(campos, valores)}
            table_endereco = table.find(
                id=table["id"] + "_ctl00_dlEmpresaParticipanteEndereco"
            )
            participante["endereço"] = scrape_tabela(
                soup=table_endereco.find_all("table")[1],
                tipo_entidade="unica",
                limiar_similaridade=0.9,
            )
            participante["contato"] = scrape_tabela(
                soup=table_endereco.find_all("table")[3],
                tipo_entidade="unica",
                limiar_similaridade=0.9,
            )
            estab["participantes"].append(participante)

        # Ajustando CNAEs secundarios
        try:
            cnaes_sec_str = estab["tributario"]["CNAEs_secundarios"][0]
            padrao_data = r"\d{2}\/\d{2}\/\d{4}"
            estab["tributario"]["datas_CNAEs_secundarios"] = re.findall(
                r"\d{2}\/\d{2}\/\d{4}", cnaes_sec_str
            )
            padrao_sep = "Data Início do CNAE Sec.: " + padrao_data
            cnaes_sec = re.split(padrao_sep, cnaes_sec_str)
            estab["tributario"]["CNAEs_secundarios"] = [
                c.strip() for c in cnaes_sec if c
            ]
        except TypeError:
            pass

        # Ajustando cabeçalho
        estab["cabecalho"]["situacao"] = estab["cabecalho"]["situacao"][10:]
        estab["cabecalho"]["data_inscricao_estado"] = estab["cabecalho"][
            "data_inscricao_estado"
        ][29:]
        estab["cabecalho"]["regime_estadual"] = estab["cabecalho"]["regime_estadual"][
            17:
        ]
        estab["cabecalho"]["regime_rfb"] = estab["cabecalho"]["regime_rfb"][12:]

        return estab

    @preparar_metodo
    def obter_solicitacao(self, recibo: str = "", ato_oficio: str = "") -> dict:
        """Obtém detalhes de uma dada solicitação.

        Args:
            recibo (str, optional): Número do recibo da solicitação. Obrigatório se não
                for passado algum valor em `ato_ofício`.
            ato_ofício (str, optional): Número do ató de ofício da solicitação.
                Obrigatório se não for passado algum valor em `recibo`.

        Returns:
            Um dicionário que contém as propriedades de uma solicitação.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        # Dados da página geral da solicitação
        html_solicitacao = self._consultar_solicitacoes_parametros(
            recibo=recibo, ato_oficio=ato_oficio
        )
        solicitacao = Cadesp._scrape_solicitacao(html_solicitacao)

        # Dados da página de detalhe da solicitação
        html_detalhes = self._consultar_detalhe_solicitacao(
            recibo=recibo, ato_oficio=ato_oficio
        )
        solicitacao["Detalhes"] = Cadesp._scrape_detalhe_solicitacao(html_detalhes)

        return solicitacao

    @staticmethod
    def _scrape_solicitacao(html):
        solicitacao = {}
        soup = BeautifulSoup(html, "html.parser")
        div_conteudo = soup.find(id="ctl00_conteudoPaginaPlaceHolder_Panel1")
        tables = div_conteudo.find_all("table")

        # Identificação
        table_identificacao = tables[1]
        solicitacao["Identificação"] = scrape_tabela(
            "unica", soup=table_identificacao, pular_td=1, limiar_similaridade=0.6
        )

        # Estabelecimento
        table_estabelecimento = tables[2]
        solicitacao["Estabelecimento"] = scrape_tabela(
            "unica", soup=table_estabelecimento, pular_td=1
        )

        # Removendo : das chaves
        solicitacao = {
            k1: {k2[:-1]: v2 for k2, v2 in v1.items()} for k1, v1 in solicitacao.items()
        }

        # Eventos
        table_eventos = div_conteudo.find(
            id="ctl00_conteudoPaginaPlaceHolder_gdvDetalhamentoEventos"
        )
        solicitacao["Eventos"] = scrape_tabela("multi", soup=table_eventos, pular_td=1)

        # Situação
        solicitacao["Situação"] = div_conteudo.find(
            id="ctl00_conteudoPaginaPlaceHolder_lblSituacaoSolicitacaoAtual"
        ).text

        # Movimentos
        table_movimentos = div_conteudo.find(
            id="ctl00_conteudoPaginaPlaceHolder_gdvDetalhamentoMovimentos"
        )
        solicitacao["Movimentos"] = scrape_tabela(
            "multi", soup=table_movimentos, pular_td=1
        )

        return solicitacao

    @staticmethod
    def _scrape_detalhe_solicitacao(html):
        detalhes = {}
        soup = BeautifulSoup(html, "html.parser")
        prefixo_id = "ctl00_conteudoPaginaPlaceHolder_SolicitacaoTabContainer_"

        # Ident.
        soup_ident = soup.find(id=prefixo_id + "IdentificacaoTabPanel").table.table
        detalhes["Ident."] = scrape_tabela("unica", soup=soup_ident)

        # Dados Gerais
        soup_dados_gerais = soup.find(id=prefixo_id + "DadosGeraisTabPanel").table.table
        detalhes["Dados Gerais"] = scrape_tabela("unica", soup=soup_dados_gerais)

        # Hist.Reg.Apur.
        soup_hist = soup.find(
            id=prefixo_id + "historicoRegimeApuracaoTabPanel"
        ).table.table
        detalhes["Hist.Reg.Apur."] = scrape_tabela("unica", soup=soup_hist)

        # Endereço
        soup_end = soup.find(id=prefixo_id + "EnderecoTabPanel").table.table
        detalhes["Endereço"] = scrape_tabela("unica", soup=soup_end)

        # Contato Estab.
        soup_contato = soup.find(
            id=prefixo_id + "ContatoEstabelecimentoTabPanel"
        ).table.table
        detalhes["Contato Estab."] = scrape_tabela("unica", soup=soup_contato)

        # Contador
        soup_contador = soup.find(id=prefixo_id + "ContadorTabPanel").table.table
        detalhes["Contador"] = scrape_tabela("unica", soup=soup_contador)

        # Produtor
        soup_produtor = soup.find(id=prefixo_id + "DadosProdutorTabPanel").table.table
        detalhes["Produtor"] = scrape_tabela("unica", soup=soup_produtor)

        # Respons.
        soup_respons = soup.find(id=prefixo_id + "ResponsavelTabPanel").table.table
        detalhes["Respons."] = scrape_tabela("unica", soup=soup_respons)

        # End.Corresp.
        soup_end_corresp = soup.find(
            id=prefixo_id + "EnderecoCorrespondenciaTabPanel"
        ).table.table
        detalhes["End.Corresp."] = scrape_tabela("unica", soup=soup_end_corresp)

        # Propr.Rural
        soup_rural = soup.find(
            id=prefixo_id + "DadosProprietarioRuralTabPanel"
        ).table.table
        detalhes["Propr.Rural"] = scrape_tabela("unica", soup=soup_rural)

        # TODO: Sócios
        # TODO: Procurador

        # Certificado/Credencial
        soup_cert = soup.find(
            id=prefixo_id + "CertificadoCredencialTabPanel"
        ).table.table
        detalhes["Certificado/Credencial"] = scrape_tabela(
            "unica", soup=soup_cert, limiar_similaridade=0.9
        )

        # Removendo : das chaves
        detalhes = {
            k1: {k2[:-1]: v2 for k2, v2 in v1.items()} for k1, v1 in detalhes.items()
        }

        return detalhes

    def _pre_login(self):
        # GET na URL base
        r = self.session.get(URL_BASE)
        # print(f"#DEBUG#Cadesp#_pre_login em {URL_BASE}")

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )
#        print("#DEBUG#Cadesp#_pre_login#Validadores:",
#              viewstate, viewstategenerator, eventvalidation)

        # Primeiro POST
        ctl_login = CTL + "$loginControl"
        ctl_panel1 = CTL + "$UpdatePanel1"
        data = {
            "ctl00$ToolkitScriptManager1": (
                ctl_panel1 + "|" + ctl_login + "$TipoUsuarioDropDownList"
            ),
            ctl_login + "TipoUsuarioDropDownList": "SEFAZ",
            ctl_login + "$UserName": "",
            ctl_login + "$Password": "",
            "__LASTFOCUS": "",
            "__EVENTTARGET": ctl_login + "$TipoUsuarioDropDownList",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
        }
        r = self.session.post(r.url, data=data)
        # print("#DEBUG#Cadesp#_pre_login#Primeiro Post:",
        #       r.url, data)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # Segundo POST
        data = {
            "ctl00$ToolkitScriptManager1": (
                ctl_panel1
                + "|"
                + ctl_login
                + "$FederatedPassiveSignInCertificado$ctl04"
            ),
            ctl_login + "$TipoUsuarioDropDownList": "SEFAZ",
            ctl_login + "$UserName": "",
            ctl_login + "$Password": "",
            ctl_login + "$FederatedPassiveSignInCertificado$ctl04.x": "31",
            ctl_login + "$FederatedPassiveSignInCertificado$ctl04.y": "42",
            "__LASTFOCUS": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
        }
        r = self.session.post(r.url, data=data)
        # print("#DEBUG#Cadesp#_pre_login#Segundo Post:",
        #       r.url, data)

    def _consultar_parametros(
        self,
        ie: str = "",
        cnpj: str = "",
        razao_social: str = "",
        contabilista_crc: str = "",
        contabilista_cpf: str = "",
        contabilista_cnpj: str = "",
        participante_cpf: str = "",
        participante_cnpj: str = "",
        procurador_cpf: str = "",
        procurador_cnpj: str = "",
        delegacia: str = "",
        posto_fiscal: str = "",
        tipo_estabelecimento: str = "",
        situacao_cadastral: str = "",
        cnae_principal: str = "",
        cnae_secundario: str = "",
    ):
        # ABRINDO TELA DE CONSULTA
        r = self.session.get(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx"
        )

        # TRABALHANDO AS VARIÁVEIS
        identificacao = "0"
        ie_cnpj = ""
        if ie != "" and cnpj != "":
            raise Exception("Informar apenas IE ou CNPJ, não ambos!")
        else:
            if ie != "":
                identificacao = "0"
                ie_cnpj = formatar_ie(ie)[1]
            if cnpj != "":
                ie_cnpj = formatar_cnpj(cnpj)[1]
                if len(ie_cnpj) == 10:
                    identificacao = "1"
                    r = self._postar_alteracao_lst_consulta_completa(
                        r, "lstIdentificacao", "1"
                    )
                if len(ie_cnpj) == 18:
                    identificacao = "2"
                    r = self._postar_alteracao_lst_consulta_completa(
                        r, "lstIdentificacao", "2"
                    )

        if razao_social != "":
            razao_social = unidecode(razao_social)

        contabilista = "0"
        contabilista_doc = ""
        if (
            (contabilista_crc != "" and contabilista_cpf != "")
            or (contabilista_crc != "" and contabilista_cnpj != "")
            or (contabilista_cpf != "" and contabilista_cnpj != "")
        ):
            raise Exception(
                "Do contabilista, informar apenas CRC, CPF ou CNPJ, não todos."
            )
        else:
            if contabilista_crc != "":
                contabilista = "0"
                contabilista_doc = formatar_crc(contabilista_crc)
            if contabilista_cpf != "":
                contabilista = "1"
                r = self._postar_alteracao_lst_consulta_completa(
                    r, "lstContabilista", "1"
                )
                contabilista_doc = formatar_cpf(contabilista_cpf)[1]
            if contabilista_cnpj != "":
                contabilista = "2"
                r = self._postar_alteracao_lst_consulta_completa(
                    r, "lstContabilista", "2"
                )
                contabilista_doc = formatar_cnpj(contabilista_cnpj)[1]

        participante = "0"
        participante_doc = ""
        if participante_cpf != "" and participante_cnpj != "":
            raise Exception("Do participante, informar apenas CPF ou CNPJ, não ambos!")
        else:
            if participante_cpf != "":
                participante = "0"
                participante_doc = formatar_cpf(participante_cpf)[1]
            if participante_cnpj != "":
                participante = "1"
                r = self._postar_alteracao_lst_consulta_completa(
                    r, "lstParticipante", "1"
                )
                participante_doc = formatar_cnpj(participante_cnpj)[1]

        procurador = "0"
        procurador_doc = ""
        if procurador_cpf != "" and procurador_cnpj != "":
            raise Exception("Do procurador, informar apenas CPF ou CNPJ, não ambos!")
        else:
            if procurador_cpf != "":
                procurador = "0"
                procurador_doc = formatar_cpf(procurador_cpf)[1]
            if procurador_cnpj != "":
                procurador = "1"
                r = self._postar_alteracao_lst_consulta_completa(
                    r, "lstProcurador", "1"
                )
                procurador_doc = formatar_cnpj(procurador_cnpj)[1]

        if posto_fiscal != "" and delegacia == "":
            raise Exception(
                "Para informar um Posto Fiscal, é necessário informar uma Delegacia."
            )

        if cnae_principal:
            cnae_principal = formatar_cnae(cnae_principal)

        if cnae_secundario:
            cnae_secundario = formatar_cnae(cnae_secundario)

        # CONFERÊNCIA CHATA PQ O CADESP OBRIGA
        if delegacia != "":
            if tipo_estabelecimento == "" or situacao_cadastral == "":
                raise Exception(
                    "Ao informar delegacia/posto fiscal, obrigatoriamente "
                    "deve ser informado o tipo de estabelecimento, "
                    "a situação cadastral e algum outro parâmetro qualquer"
                )
            elif (
                ie == ""
                and cnpj == ""
                and razao_social == ""
                and contabilista_crc == ""
                and contabilista_cpf == ""
                and contabilista_cnpj == ""
                and participante_cpf == ""
                and participante_cnpj == ""
                and procurador_cpf == ""
                and procurador_cnpj == ""
                and cnae_principal == ""
                and cnae_secundario == ""
            ):
                raise Exception(
                    "Ao informar delegacia/posto fiscal, obrigatoriamente "
                    "deve ser informado o tipo de estabelecimento, "
                    "a situação cadastral e algum outro parâmetro qualquer"
                )

            r = self._postar_alteracao_lst_consulta_completa(
                r, "lstDRT", DELEGACIAS_PARAMETROS[delegacia.upper()]
            )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # PREENCHE FORMULÁRIO E MANDA CONSULTAR
        ctl_client_state = (
            "ctl00_conteudoPaginaPlaceHolder_tcConsultaCompleta_ClientState"
        )
        ctl_cons_comp_tb1 = CTL + "$tcConsultaCompleta$TabPanel1"
        ctl_cons_comp_tb2 = CTL + "$tcConsultaCompleta$TabPanel2"
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            ctl_client_state: "{'ActiveTabIndex':0,'TabState':[true,true]}",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_cons_comp_tb1 + "$lstIdentificacao": identificacao,
            ctl_cons_comp_tb1 + "$txtIdentificacao": ie_cnpj,
            ctl_cons_comp_tb1 + "$txtNomeEmpresarial": razao_social,
            ctl_cons_comp_tb1 + "$lstContabilista": contabilista,
            ctl_cons_comp_tb1 + "$txtContabilista": contabilista_doc,
            ctl_cons_comp_tb1 + "$lstParticipante": participante,
            ctl_cons_comp_tb1 + "$txtParticipante": participante_doc,
            ctl_cons_comp_tb1 + "$lstProcurador": procurador,
            ctl_cons_comp_tb1 + "$txtProcurador": procurador_doc,
            ctl_cons_comp_tb1 + "$lstDRT": DELEGACIAS_PARAMETROS[delegacia.upper()],
            ctl_cons_comp_tb1
            + "$lstTipoEstabelecimento": (
                TIPO_ESTABELECIMENTO[tipo_estabelecimento.upper()]
            ),
            ctl_cons_comp_tb1
            + "$lstSituacaoCadastral": (SITUACAO_CADASTRAL[situacao_cadastral.upper()]),
            ctl_cons_comp_tb1 + "$lstCnaePrimario": CNAES[cnae_principal],
            ctl_cons_comp_tb1 + "$lstCnaeSecundario": CNAES[cnae_secundario],
            ctl_cons_comp_tb1 + "$btnConsultarEstabelecimento": "Consultar",
            ctl_cons_comp_tb2 + "$txtCEP": "",
            ctl_cons_comp_tb2 + "$txtNumeroLogradouro": "",
            ctl_cons_comp_tb2 + "$txtNomeLogradouro": "",
            ctl_cons_comp_tb2 + "$lstMunicipio": "0",
            ctl_cons_comp_tb2 + "$lstTipoEstabelecimentoEndereco": "0",
            ctl_cons_comp_tb2 + "$lstSituacaoCadastralEndereco": "0",
        }

        if delegacia:
            data[ctl_cons_comp_tb1 + "$lstPostoFiscal"] = POSTOS_FISCAIS_PARAMETROS[
                posto_fiscal.upper()
            ]

        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        if "ESTABELECIMENTOS ENCONTRADOS" not in r.text:
            raise Exception("Resultado inconsistente da consulta por parâmetros.")

        return r.text

    def _postar_alteracao_lst_consulta_completa(self, ultimo_r, id_lista, valor):
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            ultimo_r.text
        )
        ctl_consulta_comp = "ctl00$conteudoPaginaPlaceHolder$tcConsultaCompleta"
        ctl_cons_comp_tb1 = CTL + "$tcConsultaCompleta$TabPanel1"
        ctl_cons_comp_tb2 = CTL + "$tcConsultaCompleta$TabPanel2"
        ctl_id_lista = ctl_cons_comp_tb1 + "$" + id_lista
        data = {
            "__EVENTTARGET": ctl_id_lista,
            "__EVENTARGUMENT": "",
            ctl_consulta_comp: "{'ActiveTabIndex':0,'TabState':[true,true]}",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_cons_comp_tb1 + "$lstIdentificacao": "0",
            ctl_cons_comp_tb1 + "$lstContabilista": "0",
            ctl_cons_comp_tb1 + "$lstParticipante": "0",
            ctl_cons_comp_tb1 + "$lstProcurador": "0",
            ctl_cons_comp_tb1 + "$lstDRT": "0",
            ctl_cons_comp_tb1 + "$lstTipoEstabelecimento": "0",
            ctl_cons_comp_tb1 + "$lstSituacaoCadastral": "0",
            ctl_cons_comp_tb1 + "$lstCnaePrimario": "0",
            ctl_cons_comp_tb1 + "$lstCnaeSecundario": "0",
            ctl_cons_comp_tb2 + "$lstMunicipio": "0",
            ctl_cons_comp_tb2 + "$lstTipoEstabelecimentoEndereco": "0",
            ctl_cons_comp_tb2 + "$lstSituacaoCadastralEndereco": "0",
        }
        data[ctl_id_lista] = valor
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx",
            data=data,
        )

        return r

    def _consultar_ie(self, ie: str):
        ie_cnpj = formatar_ie(ie)[1]

        # CHAMO O MÉTODO DE CONSULTA POR PARÂMETROS
        html = self._consultar_parametros(ie=ie_cnpj)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            html
        )

        # SELECIONA A PRIMEIRA IE
        ctl_cons_completa_est = CTL + "$dlConsultaCompletaEstabelecimento"
        data = {
            "__EVENTTARGET": ctl_cons_completa_est + "$ctl01$linkButtonEstabelecimento",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_cons_completa_est
            + "$ctl00$txtParametrosConsulta": "Parâmetros de Consulta: IE: "
            + ie_cnpj,
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        if (
            r.url
            != URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaDetalhamentoPorIE.aspx?A"
        ):
            raise Exception("Resultado inconsistente da consulta de IE.")

        return r.text

    def _consultar_solicitacoes(self, ie: str):
        """Versão simplificada de _consultar_solicitacoes_parametros."""
        html = self._consultar_ie(ie=ie)

        # Capturando validadores
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            html
        )

        # POST para obter página de solicitações
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            CTL + "$btnSolicitacoes": "Solicitações",
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaDetalhamentoPorIE.aspx?A",
            data=data,
        )

        # Confirmo de deu certo
        if "Consulta Do Andamento das Solicitações" not in r.text:
            raise Exception("Erro ao tentar acessar página de solicitações.")

        return r.text

    def _ficha_padrao_ie(self, ie: str):
        ie_cnpj = formatar_ie(ie)[1]
        html = self._consultar_ie(ie=ie_cnpj)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            html
        )

        # POST NA FICHA CADASTRAL PADRÃO
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            CTL + "$btnFichaCadastralPadrao": "Ficha Cadastral Padrão",
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaDetalhamentoPorIE.aspx?A",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        if "Cadastro de Contribuintes do ICMS" not in r.text:
            raise Exception("Resultado inconsistente da abertura da ficha cadastral.")

        return r.text

    def _cadastro_completo_ie(self, ie: str):
        html = self._consultar_ie(ie=ie)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            html
        )

        # MANDA IMPRIMIR (ABRE TELA DE SELECAO DE CAMPOS)
        ctl_cons_completa_est = CTL + "$dlConsultaCompletaEstabelecimento"
        data = {
            "__EVENTTARGET": ctl_cons_completa_est + "$ctl01$linkButtonEstabelecimento",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$conteudoPaginaPlaceHolder$btnImprimir": "Imprimir",
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaDetalhamentoPorIE.aspx?A",
            data=data,
        )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # SELECIONO TODOS OS CAMPOS (COMPLETA!!!!!)
        data = {
            "ctl00$ToolkitScriptManager1": (
                CTL + "$UpdatePanel1|" + CTL + "$btnMarcar"
            ),
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$conteudoPaginaPlaceHolder$chkEmpresaGeral": "on",
            "ctl00$conteudoPaginaPlaceHolder$chkEstabelecimentoGeral": "on",
            "ctl00$conteudoPaginaPlaceHolder$chkTributario": "on",
            "__ASYNCPOST": "true",
            "ctl00$conteudoPaginaPlaceHolder$btnMarcar": "Marcar Todos",
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaImpressao.aspx",
            data=data,
        )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # MANDA IMPRIMIR
        data = {
            CTL + "$chkEmpresaGeral": "on",
            CTL + "$chkParticipantes": "on",
            CTL + "$chkEnderecoParticipantes": "on",
            CTL + "$chkSucessao": "on",
            CTL + "$chkEstabelecimentoGeral": "on",
            CTL + "$chkTributario": "on",
            CTL + "$chkContabilista": "on",
            CTL + "$chkEnderecoContato": "on",
            CTL + "$chkEnderecoCorrespondencia": "on",
            CTL + "$chkProdutorRural": "on",
            CTL + "$chkCetesb": "on",
            CTL + "$chkProcuradores": "on",
            CTL + "$chkEnderecoProcuradores": "on",
            CTL + "$chkTransferenciaTitularidade": "on",
            CTL + "$chkHistoricoRegimeApuracao": "on",
            CTL + "$chkHistoricoRegimeApuracaoRFB": "on",
            CTL + "$chkHistoricoParticipantes": "on",
            CTL + "$chkHistoricoDetalheParticipantesRepresentantes": "on",
            CTL + "$chkHistoricoDetalheRepresentantes": "on",
            CTL + "$chkHistoricoNumeroIe": "on",
            CTL + "$chkHistoricoSituacaoCadastral": "on",
            CTL + "$chkHistoricoSubstitutoTributario": "on",
            CTL + "$chkHistoricoCpr": "on",
            CTL + "$chkHistoricoCnaePrincipal": "on",
            CTL + "$chkHistoricoCnaeSecundario": "on",
            CTL + "$chkHistoricoContabilista": "on",
            CTL + "$chkHistoricoEnderecoEstabelecimento": "on",
            CTL + "$chkHistoricoEnderecoCompleto": "on",
            CTL + "$chkHistoricoProcuradores": "on",
            CTL + "$chkHistoricoEnderecoProcuradores": "on",
            CTL + "$btnMenuImprimir": "Imprimir",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta"
            + "/ConsultaCompletaImpressao.aspx",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        if "Histórico de" not in r.text:
            raise Exception("Resultado inconsistente da consulta completa.")

        return r.text

    def _consultar_endereco(
        self,
        cep: str = "",
        num: int = None,
        logradouro: str = "",
        municipio: str = "",
        tipo_estabelecimento: str = "",
        situacao_cadastral: str = "",
    ):
        # PREPARANDO VARIÁVEIS
        if cep != "":
            cep_char = formatar_cep(cep)[1]
        if logradouro != "":
            logradouro = unidecode(logradouro)
        if municipio != "":
            municipio = unidecode(municipio)

        # ABRINDO TELA DE CONSULTA
        r = self.session.get(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx"
        )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # PREENCHE E MANDA CONSULTAR
        ctl_cons_comp_tb1 = CTL + "$tcConsultaCompleta$TabPanel1"
        ctl_cons_comp_tb2 = CTL + "$tcConsultaCompleta$TabPanel2"
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "ctl00_conteudoPaginaPlaceHolder_tcConsultaCompleta_ClientState": (
                "{'ActiveTabIndex':1," + "'TabState':[true,true]}"
            ),
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_cons_comp_tb1 + "$lstIdentificacao": "0",
            ctl_cons_comp_tb1 + "$txtIdentificacao": "",
            ctl_cons_comp_tb1 + "$txtNomeEmpresarial": "",
            ctl_cons_comp_tb1 + "$lstContabilista": "0",
            ctl_cons_comp_tb1 + "$txtContabilista": "",
            ctl_cons_comp_tb1 + "$lstParticipante": "0",
            ctl_cons_comp_tb1 + "$txtParticipante": "",
            ctl_cons_comp_tb1 + "$lstProcurador": "0",
            ctl_cons_comp_tb1 + "$txtProcurador": "",
            ctl_cons_comp_tb1 + "$lstDRT": "0",
            ctl_cons_comp_tb1 + "$lstTipoEstabelecimento": "0",
            ctl_cons_comp_tb1 + "$lstSituacaoCadastral": "0",
            ctl_cons_comp_tb1 + "$lstCnaePrimario": "0",
            ctl_cons_comp_tb1 + "$lstCnaeSecundario": "0",
            ctl_cons_comp_tb2 + "$txtCEP": cep_char,
            ctl_cons_comp_tb2 + "$txtNumeroLogradouro": str(num) if num else "",
            ctl_cons_comp_tb2 + "$txtNomeLogradouro": logradouro,
            ctl_cons_comp_tb2 + "$lstMunicipio": MUNICIPIO[municipio.upper()],
            ctl_cons_comp_tb2
            + "$lstTipoEstabelecimentoEndereco": TIPO_ESTABELECIMENTO[
                tipo_estabelecimento.upper()
            ],
            ctl_cons_comp_tb2
            + "$lstSituacaoCadastralEndereco": SITUACAO_CADASTRAL[
                situacao_cadastral.upper()
            ],
            ctl_cons_comp_tb2 + "$btnConsultar_Endereco": "Consultar",
        }
        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/Cadastro/Consultas/ConsultaCompleta/ConsultaCompleta.aspx",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        if "ESTABELECIMENTOS ENCONTRADOS" not in r.text:
            raise Exception("Resultado inconsistente da consulta de endereços.")

        return r.text

    def _consultar_solicitacoes_parametros(
        self,
        ie: str = "",
        cnpj: str = "",
        nire: str = "",
        recibo: str = "",
        protocolo_id: str = "",
        ato_oficio: str = "",
        delegacia: str = "",
        posto_fiscal: str = "",
        situacao_solicitacao: str = "",
        estagio_solicitacao: str = "",
        tipo_solicitacao: str = "",
        data_inicial: str = "",
        data_final: str = "",
        redesim: str = "",
    ):
        identificacao = "0"
        ie_cnpj = ""
        # TRABALHANDO AS VARIÁVEIS
        if ie != "" and cnpj != "" and nire != "":
            raise Exception(
                "Informar apenas IE, CNPJ (base ou completo) ou NIRE, não todos!"
            )
        else:
            if ie != "":
                identificacao = "0"
                ie_cnpj = formatar_ie(ie)[1]
            if cnpj != "":
                ie_cnpj = formatar_cnpj(cnpj)[1]
                if len(ie_cnpj) == 8:
                    identificacao = "1"
                if len(ie_cnpj) == 14:
                    identificacao = "2"
            if nire != "":
                identificacao = "3"
                ie_cnpj = formatar_nire(ie)[1]

        if posto_fiscal != "" and delegacia == "":
            raise Exception(
                "Para informar um Posto Fiscal, é necessário informar uma Delegacia."
            )

        if (
            data_inicial != ""
            and data_final == ""
            or data_inicial == ""
            and data_final != ""
        ):
            raise Exception(
                "Data inicial e data final devem ser informadas simultaneamente."
            )

        if data_inicial != "":
            formatar_data(data=data_inicial, formato="%d/%m/%Y")

        if data_final != "":
            formatar_data(data=data_final, formato="%d/%m/%Y")

        # IDENTIFICANDO O ActiveTabIndex CORRETO DE ACORDO COM OS DADOS FORNECIDOS
        if recibo != "" or protocolo_id != "" or ato_oficio != "":
            ActiveTabIndex = "0"
        elif ie_cnpj != "":
            ActiveTabIndex = "1"
        elif (
            delegacia != ""
            or posto_fiscal != ""
            or situacao_solicitacao != ""
            or estagio_solicitacao != ""
            or tipo_solicitacao != ""
            or data_inicial != ""
            or data_final != ""
        ):
            ActiveTabIndex = "2"
        elif redesim != "":
            ActiveTabIndex = "3"

        # ABRINDO TELA DE CONSULTA
        r = self.session.get(
            URL_BASE
            + self._url_token
            + "/Pages/SincronizacaoRFB/Monitoramento/ProcessamentoSolicitacoesRFB"
            + "/ProcessamentoSolicitacoesRFB.aspx"
        )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # POST EM SOLICITAÇÕES
        ctl_filtro_solicit = CTL + "$filtroTabContainer$filtroSolicitacaoTabPanel"
        ctl_filtro_estab = CTL + "$filtroTabContainer$filtroEstabelecimentoTabPanel"
        ctl_filtro_class = CTL + "$filtroTabContainer$filtroClassificacaoTabPanel"
        ctl_filtro_rsim = CTL + "$filtroTabContainer$filtroProtocoloRedesimTabPanel"
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_ClientState": (
                "{'ActiveTabIndex':"
                + ActiveTabIndex
                + ",'TabState':[true,true,true,true]}"
            ),
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_filtro_solicit + "$nrReciboTextBox": recibo.upper(),
            ctl_filtro_solicit + "$nrProtocoloTextBox": protocolo_id,
            ctl_filtro_solicit + "$nrAtoOficioTextBox": ato_oficio,
            ctl_filtro_estab + "$tipoIdentificacaoDropDownList": identificacao,
            ctl_filtro_estab + "$valorIdentificacaopTextBox": ie_cnpj,
            ctl_filtro_class
            + "$delegaciaDropDownList": DELEGACIAS_SOLICITACOES[delegacia.upper()],
            ctl_filtro_class
            + "$postoFiscalDropDownList": POSTOS_FISCAIS_SOLICITACOES[
                posto_fiscal.upper()
            ],
            ctl_filtro_class
            + "$situaçãoSolicitacaoDropDownList": SITUACAO_SOLICITACAO[
                situacao_solicitacao.upper()
            ],
            ctl_filtro_class
            + "$estagioSolicitacaoDropDownList": ESTAGIO_SOLICITACAO[
                estagio_solicitacao.upper()
            ],
            ctl_filtro_class
            + "$tipoSolicitacaoDropDownList": TIPO_SOLICITACAO[
                tipo_solicitacao.upper()
            ],
            ctl_filtro_class + "$dataInicialTextBox": data_inicial,
            ctl_filtro_class + "$dataFinalTextBox": data_final,
            ctl_filtro_rsim + "$protocoloRedesimTextBox": redesim,
        }

        # DEFININDO QUAL BOTÃO DE FORMULÁRIO SERÁ POSTADO
        if ActiveTabIndex == "0":
            data[ctl_filtro_solicit + "$consultarSolicitacaoButton"] = "Consultar"
        elif ActiveTabIndex == "1":
            data[ctl_filtro_estab + "$consultarEstabelecimentoButton"] = "Consultar"
        elif ActiveTabIndex == "2":
            data[ctl_filtro_class + "$consultarClassificacaoButton"] = "Consultar"
        elif ActiveTabIndex == "3":
            data[ctl_filtro_rsim + "$consultarProtocoloRedesimButton"] = "Consultar"

        r = self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/SincronizacaoRFB/Monitoramento/ProcessamentoSolicitacoesRFB/"
            + "ProcessamentoSolicitacoesRFB.aspx",
            data=data,
        )

        # CONFIRMO SE DEU CERTO
        # (SE FOI FEITO POR PARÂMETROS OU POR NÚMERO DE RECIBO DIRETO)
        if "Entrada na SEFAZ-SP" not in r.text and "Data de Entrada:" not in r.text:
            raise Exception(
                "Resultado inconsistente da consulta de solicitações de alteração da "
                "IE. Talvez não existam solicitações com os parâmetros passados."
            )

        return r.text

    def _consultar_detalhe_solicitacao(self, recibo, ato_oficio):
        html = self._consultar_solicitacoes_parametros(
            recibo=recibo, ato_oficio=ato_oficio
        )
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            html
        )
        ctl_uppgeral = CTL + "$uppGeral"
        ctl_btn_dados = CTL + "$btnDadosSolicitacaoLateral"
        data = {
            "ctl00$ToolkitScriptManager1": ctl_uppgeral + "|" + ctl_btn_dados,
            ctl_btn_dados: "Dados da Solicitação",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
        }
        self.session.post(
            URL_BASE
            + self._url_token
            + "/Pages/SincronizacaoRFB/HomologacaoSolicitacoesRFB/"
            + "HomologacaoSolicitacoes.aspx?A",
            data=data,
        )
        r = self.session.get(
            URL_BASE
            + self._url_token
            + "/Pages/SincronizacaoRFB/Monitoramento/ProcessamentoSolicitacoesRFB/"
            + "ProcessamentoDetalheSolicitacoesRFB.aspx?A=",
            headers=dict(self.session.headers)
            | {
                "Referer": (
                    URL_BASE
                    + self._url_token
                    + "/Pages/SincronizacaoRFB/HomologacaoSolicitacoesRFB/"
                    + "HomologacaoSolicitacoes.aspx?A"
                )
            },
        )

        if "Consulta Detalhe de Solicitação" not in r.text:
            raise Exception("Erro ao tentar acessar página de detalhe de solicitação.")

        return r.text

    def _print_html(self, html: str, caminho: str):
        # RETIRAR OS BOTÕES "IMPRIMIR" E "VOLTAR" E O "MENU DO CADESP"
        soup = BeautifulSoup(html, "html.parser")
        soup.find("div", {"id": "ctl00_menuSuperiorPanel"}).decompose()
        soup.find("table", {"id": "ctl00_tableMenu"}).decompose()
        for ipt in soup.find_all("input"):
            ipt.decompose()

        # PRETTIFY SERVE PARA PODERMOS FAZER O "ENCODING" CORRETO NO WORD
        pretty_html = soup.prettify("utf-8")

        # SUBSTITUI ALGUNS CARACTERES PARA COLETAR CORRETAMENTE AS IMAGENS E CSS DO HTML
        pretty_html = pretty_html.replace(
            bytes("../../../..", "utf-8"), bytes(URL_BASE + self._url_token, "utf-8")
        )

        # CONVERTE PARA TEXTO
        pretty_html = pretty_html.decode("utf-8")

        # CONVERTE
        converter_para_pdf(pretty_html, caminho)

    @preparar_metodo
    def baixar_pdf_estabelecimento(self, ie: str, caminho: str) -> None:
        """Baixa um arquivo PDF contendo todos os dados do estabelecimento.

        Args:
            ie (str): Inscrição Estadual (IE) do estabelecimento, com ou sem pontuação.
            caminho (str): Caminho completo onde será baixado o PDF, incluindo o nome do
                arquivo. Deve terminar com .pdf.
        """
        ie = formatar_ie(ie)[1]
        html = self._cadastro_completo_ie(ie=ie)
        self._print_html(html, caminho)

    @preparar_metodo
    def baixar_pdf_estabelecimentos_por_endereco(
        self,
        caminho: str,
        cep: str = "",
        num: int = None,
        logradouro: str = "",
        municipio: str = "",
        tipo_estabelecimento: str = "",
        situacao_cadastral: str = "",
    ) -> None:
        """Baixa um arquivo PDF contendo estabelecimentos.

        Consulte também `listar_estabelecimentos_por_endereco`.

        Args:
            caminho (str): Caminho completo onde será baixado o PDF, incluindo o nome do
                arquivo. Deve terminar com .pdf.
            cep (str, optional): CEP do estabelecimento. Valor padrão é "".
            num (int, optional): Número do logradouro do estabelecimento.
            logradouro (str, optional): Nome do logradouro do estabelecimento. Valor
                padrão é "".
            municipio (str, optional): Município do estabelecimento. A lista de todos os
                municípios aceitos nesse parâmetro são as chaves do dicionário
                `MUNICIPIO` Valor padrão é "".
            tipo_estabelecimento (str, optional): Tipo do estabelecimento. Pode receber
                `""`, `"PESSOA JURÍDICA E DEMAIS ENTIDADES"` ou `"PRODUTOR RURAL"`.
                Valor padrão é "".
            situacao_cadastral (str, opcional): Situação cadastral do estabelecimento. A
                lista de todas as situações aceitas nesse parâmetro são as chaves do
                dicionário `SITUACAO_CADASTRAL`. Valor padrão é "".
        """
        html = self._consultar_endereco(
            cep=cep,
            num=num,
            logradouro=logradouro,
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento,
            situacao_cadastral=situacao_cadastral,
        )

        # remove elementos específicos da página desnecessários
        html = html.replace('cols="20"', 'cols="100"')
        div_pattern = (
            '<div id="ctl00_conteudoPaginaPlaceHolder_upConsultaCompletaPorEndereco.'
            "*?</div>"
        )
        html = re.sub(
            div_pattern,
            "",
            html,
            flags=re.DOTALL,
        )
        self._print_html(html, caminho)
