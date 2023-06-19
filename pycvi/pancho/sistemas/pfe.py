"""Módulo com definições do sistema PFE."""
import datetime
import re
import tempfile
from enum import Enum
from pathlib import Path

from bradocs4py import InscricaoEstadual
from bs4 import BeautifulSoup
from lxml import etree

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import converter_para_pdf, extrair_validadores_aspnet
from pepe.utils.login import login_identity_cert
from pepe.utils.texto import limpar_texto

URL_BASE = "https://www3.fazenda.sp.gov.br/CAWeb/pages/Default.aspx"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v003/"
    "Sefaz.Identity.STS.PortalSSO/LoginPortalSSO.aspx"
)
URL_LOGIN = "https://www3.fazenda.sp.gov.br/CAWEB/Account/Login.aspx"
URL_WTREALM = "https://www3.fazenda.sp.gov.br/CAWeb/pages/Default.aspx"
URL_GIA_EFD = "https://www3.fazenda.sp.gov.br/GIAEFD"
URL_GIA = "https://cert01.fazenda.sp.gov.br/novaGiaWEB"

WCTX = "rm=0&id=STS.Windows.WebForms"
CLAIM_SETS = "80F00000"
TIPO_LOGIN = "00000003"
AUTO_LOGIN = "1"


class GIARelatorio(Enum):
    """Representa um relatório da GIA."""

    GIA_RELATORIO_CFOPS_ENTRADA = (
        "2 - CFOPs Entradas",
        "consultaCFOPsEntradas",
        "consultarCFOPsEntrada",
    )
    GIA_RELATORIO_CFOPS_SAIDA = (
        "3 - CFOPs Saídas",
        "consultaCFOPsSaidas",
        "consultarCFOPsSaidas",
    )
    GIA_RELATORIO_APURACAO_PROPRIA = (
        "10 - Apuração do ICMS - Operações Próprias",
        "consultaApuracaoICMSOpeProp",
        "consultaApuracaoIcmsOpeProp",
    )
    GIA_RELATORIO_CENTRALIZACAO = (
        "12 - Centralização de Imposto (Subitens 002.18, 002.19, 002.26, "
        "007.29, 007.30 e 007.48) Operações Próprias",
        "consultaCentralizacaoImposto",
        "consultaCentralizacaoImposto",
    )
    GIA_RELATORIO_APURACAO_ST = (
        "14 - Apuração do ICMS - Substituição Tributária",
        "consultaApuracaoICMSST",
        "consultaApuracaoIcmsST",
    )

    def __new__(cls, nome: str, link: str, metodo: str):
        """Cria um objeto da classe GIARelatorio."""
        obj = object.__new__(cls)
        obj._value_ = nome
        obj.link = link
        obj.metodo = metodo
        return obj


class GIASubRelatorio(Enum):
    """Representa um subrelatório da GIA."""

    GIA_RELATORIO_APURACAO_SAIDAS_COM_DEBITO = (
        "051",
        "findSaidasDebitoByIdGeraReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_OUTROS_DEBITOS = (
        "052",
        "findOutrosDebitosByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_ESTORNO_CREDITO = (
        "053",
        "findEstornoCreditosByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_ENTRADAS_COM_CREDITO = (
        "056",
        "findEntradasCreditosByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_OUTROS_CREDITOS = (
        "057",
        "findOutrosCreditosByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_ESTORNO_DEBITO = (
        "058",
        "findEstornoDebitosByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_DEDUCOES = (
        "064",
        "findDeducoesByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )
    GIA_RELATORIO_APURACAO_IMPOSTOS_A_RECOLHER = (
        "065",
        "findPagamentoByIdGeralReferencia",
        GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA,
    )

    def __new__(cls, nome: str, metodo: str, relatorio: GIARelatorio):
        """Cria um objeto da classe GIASubRelatorio."""
        obj = object.__new__(cls)
        obj._value_ = nome
        obj.metodo = metodo
        obj.relatorio = relatorio
        return obj


class Pfe(Sistema):
    """Representa o sistema [PFE](https://www3.fazenda.sp.gov.br/CAWeb/pages/Default.aspx).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe PFE.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/99.0.4844.83 Safari/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9",
            }
        )
        self._sid = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        if self._sid:
            params = {
                "funcao": "montatelacategoria",
                "SID": self._sid,
                "SERVICO": "FISCA",
                "proxtela": "/deca.docs/fiscal/servfiscal.htm",
            }
            r = self.session.get(
                "https://cert01.fazenda.sp.gov.br/ca/ca", params=params
            )

            return "/ca/ca?funcao=logout" in r.text

        return False

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
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

        # LOGIN FEITO, MAS PRECISO FAZER UMA ÚLTIMA REQUISIÇÃO DA PÁGINA INICIAL
        # PRA CAPTURAR O SID DA SESSÃO (QUERY STRING)
        soup = BeautifulSoup(r.text, "html.parser")
        input_token = soup.find("input", {"name": "TokenLogin"})
        if not input_token:
            raise AuthenticationError(
                "Erro login PFE, retorno da requisição Default.aspx veio sem TokenId!"
            )

        form = soup.find("form")
        payload = {t["name"]: t["value"] for t in soup.find("form").find_all("input")}
        r = self.session.post(form["action"], data=payload)

        url_split = [qs for qs in r.url.split("&")]
        for qs in url_split:
            if qs.split("=")[0] == "SID":
                self._sid = qs.split("=")[1]
                break

        if not self.autenticado():
            raise AuthenticationError()

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario=usuario, senha=senha)

    def _pre_login(self):
        # GET na URL base
        r = self.session.get(URL_BASE)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        data = {
            "ctl00$ScriptManager1": "ctl00$ConteudoPagina$upnConsulta|ctl00$"
            "ConteudoPagina$btn_Login_Certificado_WebForms",
            "ctl00$ConteudoPagina$rdoListPerfil": "4",
            "ctl00$ConteudoPagina$cboPerfil": "0",
            "ctl00$ConteudoPagina$txtUsuario": "",
            "ctl00$ConteudoPagina$txtSenha": "",
            "g-recaptcha-response": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEENCRYPTED": "",
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ConteudoPagina$btn_Login_Certificado_WebForms.x": "54",
            "ctl00$ConteudoPagina$btn_Login_Certificado_WebForms.y": "36",
        }
        self.session.post(r.url, data=data)

    def _acessar_gia_da_efd(self):
        self.session.get(URL_GIA_EFD + "/EFD/ConsultaEFD/?SID=" + self._sid)

    @preparar_metodo
    def listar_gias(
        self,
        ie: str,
        inicio: datetime.date,
        fim: datetime.date,
        apenas_ultima_entregue: bool = True,
        incluir_recusadas: bool = False,
        incluir_pendentes: bool = False,
    ) -> list[dict]:
        """Lista GIAs em conformidade com os argumentos passados.

        Args:
            ie (str): Inscrição estadual do estabelecimento.
            inicio (date): Data inicial das referências a serem listadas.
            fim (date): Data final das referências a serem listadas.
            apenas_ultima_entregue (bool, optional): Indica se a listagem deve
                apresentar apenas a última GIA entregue pelo contribuinte para cada
                referência. Valor padrão é `True`.
            incluir_recusadas (bool, optional): Indica se a listagem deve apresentar
                tanto as GIAs aprovadas como as recusadas para cada referência.
                Valor padrão é `False`.
            incluir_pendentes (bool, optional): Indica se a listagem deve apresentar
                tanto as GIAs aprovadas como as pendentes de análise para cada referência.
                Valor padrão é `False`.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades da
            frente da GIA e da apuração do ICMS Próprio.
        """
        if inicio > fim:
            raise ValueError("Data início deve ser menor ou igual a data fim")

        validator = InscricaoEstadual(ie, "SP")

        if not validator.isValid:
            raise ValueError("Inscrição estadual inválida.")

        ie = str(validator)
        self._acessar_gia_da_efd()

        # ABRE LINK DA CONSULTA COMPLETA
        self.session.get(URL_GIA_EFD + "/Menu/ConsultaCompletaUrlGia?SID=" + self._sid)
        r = self.session.post(
            URL_GIA + "/consultaCompleta.gia",
            data={
                "SID": self._sid,
                "servico": "",
                "method": "consultaCompleta",
                "ie": ie,
                "refInicialMes": int(inicio.strftime("%m")),
                "refInicialAno": inicio.strftime("%Y"),
                "refFinalMes": int(fim.strftime("%m")),
                "refFinalAno": fim.strftime("%Y"),
                "botao": "Consultar",
            },
        )
        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table", {"class": "RESULTADO-TABELA"})

        if not tabela:
            erro = soup.find("td", {"class": "RESULTADO-ERRO"})
            raise KeyError(re.sub(r'[\n\t\'"]', "", erro.text))

        result = []
        ultima_referencia = ""
        gias = [
            [re.sub(r"\W", "", td.text) for td in tr.find_all("td")] + [tr["id"]]
            for tr in tabela.find_all("tr", {"class": "CORPO-TEXTO-FUNDO"})
        ]

        if not incluir_recusadas:
            gias = [gia for gia in gias if "Recusada" not in gia[1]]

        if not incluir_pendentes:
            gias = [
                gia
                for gia in gias
                if "análise" not in gia[1].lower()
                and "pendente" not in gia[1].lower()
                and "recebida" not in gia[1].lower()
            ]

        gias.sort(key=lambda gia: (gia[0][2:], gia[0][:2], 1 / int(gia[4])))

        for gia in gias:
            if ultima_referencia == gia[0] and apenas_ultima_entregue:
                continue

            ultima_referencia = gia[0]
            # acessa gia específica
            self.session.post(
                URL_GIA + "/consultaCompleta.gia",
                data={
                    "SID": self._sid,
                    "servico": "",
                    "method": "montaMenuConsultaCompleta",
                    "idGeral": gia[-1],
                    "idProtocolo": gia[4],
                    "ie": ie,
                },
            )
            # busca dados detalhados da apuração
            html = self._gia_post(
                ie, int(gia[-1]), GIARelatorio.GIA_RELATORIO_APURACAO_PROPRIA
            )

            soup = BeautifulSoup(html, "html.parser")
            dom = etree.HTML(str(soup))
            dic_referencia = {
                "referencia": datetime.datetime.strptime(
                    dom.xpath("/html/body/form/table[2]/tr[7]/td[2]/span")[0].text,
                    "%m/%Y",
                ).date(),
                "tipo": limpar_texto(
                    re.sub(
                        "[\t\n/]",
                        "",
                        dom.xpath("/html/body/form/table[2]/tr[7]/td[1]/span")[0].text,
                    )
                ),
                "protocolo": int(
                    dom.xpath("/html/body/form/table[2]/tr[7]/td[4]/span")[0].text
                ),
                "controle_gia": int(gia[-1]),
                "controle_conta_fiscal": int(gia[3]),
                "entrega": datetime.datetime.strptime(
                    dom.xpath("/html/body/form/table[2]/tr[7]/td[7]/span")[0].text,
                    "%d/%m/%Y %H:%M:%S",
                ),
                "saidas_debito": float(
                    dom.xpath("/html/body/form/table[3]/tr[2]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "outros_debitos": float(
                    dom.xpath("/html/body/form/table[3]/tr[3]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "estorno_credito": float(
                    dom.xpath("/html/body/form/table[3]/tr[4]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "entradas_credito": float(
                    dom.xpath("/html/body/form/table[3]/tr[7]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "outros_creditos": float(
                    dom.xpath("/html/body/form/table[3]/tr[8]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "estorno_debito": float(
                    dom.xpath("/html/body/form/table[3]/tr[9]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "saldo_credor_anterior": float(
                    dom.xpath("/html/body/form/table[3]/tr[11]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "saldo_devedor": float(
                    dom.xpath("/html/body/form/table[3]/tr[14]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
                "saldo_credor_a_transportar": float(
                    dom.xpath("/html/body/form/table[3]/tr[17]/td[4]/span")[0]
                    .text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                ),
            }
            result.append(dic_referencia)

        return result

    def baixar_pdf_gia(
        self,
        ie: str,
        protocolo: int,
        controle: int,
        caminho: str,
        relatorio: GIARelatorio,
        subrelatorio: GIASubRelatorio = None,
    ):
        """Baixa um PDF com o relatório ou subrelatório de uma GIA.

        Para preencher os parâmetros `protocolo` e `controle`, consulte o método
        `listar_gias`.

        Args:
            ie (str): Inscrição estadual do estabelecimento.
            protocolo (int): Número de protocolo da GIA entregue.
            controle (int): Número de controle da GIA entregue.
            caminho (str): Caminho completo do arquivo PDF a ser salvo.
            relatorio (GIARelatorio): Indica qual o relatório da GIA deve ser baixado,
                dentro das possibilidades elencadas no enumumerador `GIARelatorio`. Se
                não for indicado subrelatório, será baixado o próprio relatório.
            subrelatorio (GIASubRelatorio, optional): Indica qual subrelatório da GIA
                deve ser baixado, quando houver disponibilidade.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos.
            KeyError: Erro indicando que não há subrelatório disponível na referência
                indicada.
        """
        validator = InscricaoEstadual(ie, "SP")

        if not validator.isValid:
            raise ValueError("Inscrição estadual inválida.")

        ie = str(validator)

        if subrelatorio and subrelatorio.relatorio != relatorio:
            raise ValueError(
                f"O subrelatório {subrelatorio.name} não existe dentro do relatório "
                f"{relatorio.name}"
            )

        self._acessar_gia_da_efd

        # ABRE LINK DA CONSULTA COMPLETA
        self.session.get(URL_GIA_EFD + "/Menu/ConsultaCompletaUrlGia?SID=" + self._sid)

        # acessa gia específica
        self.session.post(
            URL_GIA + "/consultaCompleta.gia",
            data={
                "SID": self._sid,
                "servico": "",
                "method": "montaMenuConsultaCompleta",
                "idGeral": controle,
                "idProtocolo": protocolo,
                "ie": ie,
            },
        )
        html = self._gia_post(ie, controle, relatorio)

        # incluir erro caso não exista apura
        if "RESULTADO-ERRO" in html:
            # nao existe o relatório
            raise KeyError(f"Relatório {relatorio.value} não existe para a referência")
        else:
            if subrelatorio:
                html = self._gia_post(ie, controle, relatorio, subrelatorio)
                if "RESULTADO-ERRO" in html:
                    # nao existe o subrelatorio
                    raise KeyError(
                        f"Subrelatório {subrelatorio.value} não existe para a referência"
                    )
                else:
                    self._print_html(html, caminho, "ISO-8859-1")
            else:
                self._print_html(html, caminho, "ISO-8859-1")

    def _gia_post(
        self,
        ie: str,
        controle: int,
        relatorio: GIARelatorio,
        subrelatorio: GIASubRelatorio = None,
    ):
        metodo = subrelatorio.metodo if subrelatorio else relatorio.metodo
        r = self.session.post(
            URL_GIA + f"/{relatorio.link}.gia",
            data={
                "idGeral": controle,
                "ie": ie,
                "method": metodo,
                "servico_ca": "NGIA_CONCP",
                "SID": self._sid,
                "servico": "",
            },
        )
        return r.text

    @staticmethod
    def _print_html(html: str, caminho: str, encoding="utf-8"):
        soup = BeautifulSoup(html, "html.parser")

        # PRETTIFY SERVE PARA PODERMOS FAZER O "ENCODING" CORRETO NO WORD
        pretty_html = soup.prettify(encoding)

        # SUBSTITUI ALGUNS CARACTERES PARA COLETAR CORRETAMENTE AS IMAGENS E CSS DO HTML
        pretty_html = pretty_html.replace(
            bytes('"/novaGiaWEB', encoding), bytes(f'"{URL_GIA}', encoding)
        )
        tmp = None
        try:
            if encoding != "utf-8":
                pretty_html = pretty_html.decode(encoding)
                tmp = tempfile.NamedTemporaryFile("w", encoding=encoding, delete=False)
                tmp.write(pretty_html)
                pretty_html = tmp.name
                tmp.close()
            else:
                # CONVERTE PARA TEXTO
                pretty_html = pretty_html.decode("utf-8")

            # CONVERTE
            converter_para_pdf(pretty_html, caminho, paisagem=False)
        finally:
            if tmp:
                Path(pretty_html).unlink(missing_ok=True)
