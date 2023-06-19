"""Módulo com definições do sistema ContaFiscalICMS."""
import datetime
import re

from bs4 import BeautifulSoup

from pepe import AuthenticationError, preparar_metodo
from pepe.sistemas.pfe import Pfe
from pepe.utils.html import extrair_validadores_aspnet

URL_BASE = "https://www10.fazenda.sp.gov.br/ContaFiscalICMS/Pages/ContaFiscal.aspx"


class ContaFiscalICMS(Pfe):
    """Representa o sistema [Conta Fiscal ICMS](https://www10.fazenda.sp.gov.br/ContaFiscalICMS/Pages/ContaFiscal.aspx).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe ContaFiscalICMS.

        Args:
            usar_proxy (bool, optional): ver classe Pfe ([Pfe][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.pfe
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.viewstate = ""
        self.viewstategenerator = ""
        self.eventvalidation = ""
        self.url = ""

    def autenticado(self) -> bool:
        """Ver classe Pfe ([Pfe][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.pfe
        """  # noqa: E501
        # tem que verificar primeiro se está logado no PFE...
        is_logged_in_pfe = super().autenticado()
        if not is_logged_in_pfe or not self.url:
            return False
        r = self.session.get(self.url)
        return "lblUsuario" in r.text

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe Pfe ([Pfe][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.pfe
        """  # noqa: E501
        try:
            super().login_cert(nome_cert)
        except AuthenticationError:
            # Ignoro o erro lançado na verificação final do login da classe base
            # pois autenticação da classe derivada não terminou
            pass

        self.url = f"{URL_BASE}?SID={self._sid}"
        self.session.headers.update({"DNT": "1"})
        r = self.session.get(self.url)
        # CAPTURANDO VALIDADORES
        self._update_asp_state(r.text)
        if (
            r.url != self.url
            and len(r.history) > 0
            and r.history[-1].status_code == 302
        ):
            # precisa fazer login federado no Identity
            payload = {
                "btnAcessar.x": "0",
                "btnAcessar.y": "0",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "__EVENTVALIDATION": self.eventvalidation,
            }
            r = self.session.post(r.url, data=payload)
            if "wresult" not in r.text:
                raise AuthenticationError(
                    "Erro de autenticação com o Identity: wresult não encontrado"
                )
            soup = BeautifulSoup(r.text, "html.parser")
            data = {
                "wa": soup.find("input", {"name": "wa"})["value"],
                "wctx": soup.find("input", {"name": "wctx"})["value"],
                "wresult": soup.find("input", {"name": "wresult"})["value"],
            }
            r = self.session.post(
                soup.find("form")["action"],
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        soup = BeautifulSoup(r.text, "html.parser")
        if not soup.find("div", {"id": "erro"}):
            raise AuthenticationError(
                "Aparente indisponibilidade do Conta Fiscal do ICMS Declarado"
            )
        tag_erro = soup.find("div", {"id": "erro"}).find("span").text.strip()
        if tag_erro and tag_erro != "Label":
            raise AuthenticationError(tag_erro)

        # CAPTURANDO VALIDADORES
        self._update_asp_state(r.text)

    def _update_asp_state(self, html: str):
        (
            self.viewstate,
            self.viewstategenerator,
            self.eventvalidation,
        ) = extrair_validadores_aspnet(html)

    @preparar_metodo
    def consulta_conta_fiscal_icms_declarado(
        self,
        cnpj: str = "",
        ie: str = "",
        referencia: int = datetime.date.today().year,
        recolhimentos_especiais: bool = False,
    ) -> str:
        """Realiza a consulta da Conta Fiscal do ICMS declarado para uma empresa.

        Args:
            cnpj (str, optional): CNPJ da empresa no formato 00.000.000/0000-00.
                Se não for utilizado, o campo ie deve estar preenchido.
            ie (str, optional): IE da empresano formato 000.000.000.000.
                Se não for utilizado, o campo cnpj deve estar preenchido.
            referencia (int, optional): Ano que se deseja pesquisar. Deve ser um valor
                entre 2003 e o ano atual. Se não for utilizado, será pesquisado o ano
                    atual.
            recolhimentos_especiais (bool, optional): Se `True`, a consulta retorna
                informações sobre recolhimentos especiais. Valor padrão é `False`.

        Returns:
            O HTML da página, contendo todas as informações do extrato, que pode ser
            usado como entrada para um dos demais métodos da classe.

        Raises:
            ValueError: Erro indicando que não foi informado CNPJ ou IE, ou que a
                referência é inválida.
            ContaFiscalICMSException: Erro com informações apresentadas pelo sistema
                Conta Fiscal ICMS, como contribuinte sem informações no período, ou
                CNPJ/IE não localizado.
        """
        if not cnpj and not ie:
            raise ValueError("Deve ser informado ao menos CNPJ ou IE")
        if not 2003 <= referencia <= datetime.date.today().year:
            raise ValueError(
                f"Referência deve ser um ano entre 2003 e {datetime.date.today().year}"
            )

        data = {
            "__EVENTTARGET": "ctl00$MainContent$btnConsultar",
            "ctl00$MainContent$ddlContribuinte": "IE" if ie else "CNPJ",
            "ctl00$MainContent$txtCriterioConsulta": ie if ie else cnpj,
            "ctl00$MainContent$ddlReferencia": str(referencia),
            "ctl00$MainContent$hdfConteudoPopupDataInicioAtividade": "",
            "ctl00$MainContent$txtHdfIndicesMesesAbertos": "",
            "ctl00$MainContent$hdfHeight": "751",
            "ctl00$MainContent$hfMesReferenciaSelecionado": "",
            "ctl00$MainContent$HistoricoAjustePagamento$keyDictionary": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self.viewstate,
            "__VIEWSTATEGENERATOR": self.viewstategenerator,
            "__EVENTVALIDATION": self.eventvalidation,
        }
        if recolhimentos_especiais:
            data["ctl00$MainContent$chkrecolhimento"] = "on"
        r = self.session.post(
            self.url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self._update_asp_state(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        msg_erro = soup.find("span", {"id": "MainContent_lblMensagemDeErro"})
        if msg_erro:
            raise ContaFiscalICMSException(msg_erro.text)
        return r.text

    @preparar_metodo
    def imprime_conta_fiscal_icms_declarado(
        self, html: str, caminho: str, meses: list[int] = None
    ) -> None:
        """Imprime o extrato da Conta Fiscal do ICMS declarado de uma empresa em PDF.

        Args:
            html (str): Código-fonte HTML retornado pelo método
                `consulta_conta_fiscal_icms_declarado`.
            caminho (str): Caminho completo onde deverá ser salvo o relatório, incluindo
                seu nome. Deve terminar com .pdf.
            meses (list[int], optional): Lista de inteiros, contendo os meses que se
                deseja que façam parte do relatório (ex: `[2, 5]` imprimirá os meses de
                fevereiro e maio). Caso não exista o mês indicado no relatório, não será
                apresentado erro. Se o parâmetro não for preenchido, serão impressos
                todos os meses presentes no HTML.
        """
        soup = BeautifulSoup(html, "html.parser")
        tipo_pesquisa = soup.find("select", {"id": "MainContent_ddlContribuinte"}).find(
            "option", {"selected": "selected"}
        )["value"]
        contribuinte = soup.find("input", {"id": "MainContent_txtCriterioConsulta"})[
            "value"
        ]
        referencia = soup.find("select", {"id": "MainContent_ddlReferencia"}).find(
            "option", {"selected": "selected"}
        )["value"]
        data = {
            "__EVENTTARGET": "ctl00$MainContent$lnkImprimeContaFiscal",
            "ctl00$MainContent$ddlContribuinte": tipo_pesquisa,
            "ctl00$MainContent$txtCriterioConsulta": contribuinte,
            "ctl00$MainContent$ddlReferencia": referencia,
            "ctl00$MainContent$hdfConteudoPopupDataInicioAtividade": "",
            "ctl00$MainContent$txtHdfIndicesMesesAbertos": "",
            "ctl00$MainContent$hdfHeight": "751",
            "ctl00$MainContent$HistoricoAjustePagamento$keyDictionary": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self.viewstate,
            "__VIEWSTATEGENERATOR": self.viewstategenerator,
            "__EVENTVALIDATION": self.eventvalidation,
        }
        meses_existentes_tags = soup.find_all(
            "input",
            {
                "name": re.compile(
                    r"ctl00\$MainContent\$rptContaFiscalMes\$ctl\d+"
                    r"\$gdvResultadoDetalhe\$ctl\d+\$hdfReferencia"
                )
            },
        )
        meses_existentes = set([t["value"] for t in meses_existentes_tags])
        if meses:
            meses_existentes = [
                m
                for m in meses_existentes
                if m
                in [
                    f"{str(parametro).zfill(2)}{referencia[-2:]}" for parametro in meses
                ]
            ]
        data["ctl00$MainContent$hfMesReferenciaSelecionado"] = ",".join(
            sorted(meses_existentes)
        )
        # Tem que adicionar todas as informações que aparecem no extrato como argumentos
        # do POST :-(
        for tag in soup.find_all(
            "input", {"name": re.compile(r"ctl00\$MainContent\$rptContaFiscalMes.*")}
        ):
            data[tag["name"]] = tag["value"] if "value" in tag.attrs else ""
        r = self.session.post(
            self.url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with open(caminho, mode="wb") as f:
            f.write(r.content)


class ContaFiscalICMSException(Exception):
    """Representa erros do sistema ContaFiscalICMS."""

    pass
