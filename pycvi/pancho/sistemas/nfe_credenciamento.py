"""Módulo com definições do sistema NFE - Credenciamento."""
import re

from bradocs4py import ChaveAcessoNFe, ValidadorChaveAcessoNFe
from bs4 import BeautifulSoup

import pepe.utils.texto
from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import extrair_validadores_aspnet, scrape_tabela

URL_BASE = "https://sefaznet11.intra.fazenda.sp.gov.br/Credenciamento/"


class NfeCredenciamento(Sistema):
    """Representa o sistema [Nfe](https://nfe.fazenda.sp.gov.br/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Nfe.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.viewstate = ""
        self.viewstategenerator = ""
        self.eventvalidation = ""

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        try:
            r = self.session.get(
                URL_BASE + "Sistema/Consulta/SituacaoContribuinteCriterioEscolha.aspx"
            )
        except Exception:
            return False
        return "Encerrar" in r.text

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login_cert(nome_cert=nome_cert)

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE + "Base/Paginas/Login.aspx")
        self._update_asp_state(r.text)
        r = self.session.post(
            URL_BASE + "Base/Paginas/Login.aspx",
            data={
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "__EVENTVALIDATION": self.eventvalidation,
                "Usuario": usuario,
                "Senha": senha,
                "Conectar": "Entrar",
            },
        )

        if not self.autenticado():
            raise AuthenticationError()

    def _update_asp_state(self, html: str):
        (
            self.viewstate,
            self.viewstategenerator,
            self.eventvalidation,
        ) = extrair_validadores_aspnet(html)

    @preparar_metodo
    def listar_autorizacoes_cancelamento(self) -> list[dict]:
        """Lista as autorizações de cancelamento de NF-e cadastradas e ativas.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades da
            autorização de cancelamento extemporâneo.
        """
        r = self.session.get(
            URL_BASE + "Sistema/Obrigatoriedade/ContribuinteNfeExtemporanea.aspx"
        )
        self._update_asp_state(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table", {"class": "grid"})
        trs = tabela.find_all("tr", {"class": re.compile("linha_grid*")})
        tabela = scrape_tabela("multi", soup=tabela)
        i = 0
        for tr in trs:
            postback = tr.find_all("td")[-1].a.get("href")
            tabela[i]["eventtarget"] = re.match(
                r".*doPostBack\('(.*?)\'", postback
            ).group(1)
            i += 1
        return tabela

    @preparar_metodo
    def autorizar_cancelamento_extemporaneo(self, chave: str, expediente: str):
        """Cadastra uma autorização de cancelamento extemporâneo de NF-e.

        O cadastro autoriza o contribuinte a submeter o evento de cancelamento.

        Args:
            chave (str): Chave da NF-e a ser cancelada extemporaneamente. Deve ser uma
                NF-e emitida por contribuinte na circunscrição do usuário.
            expediente (str): Indica o expediente Sem Papel ao qual está relacionada a
                autorização para cancelamento extemporâneo.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos, ou NF-e já
                cadastrada.
            KeyError: Erro indicando falha no cadastramento, possivelmente por ser uma
                NF-e emitida por CNPJ de outra circunscrição que não a do usuário.
        """
        if not re.search(r"^35\d{18}55\d{22}$", chave):
            raise ValueError("Chave NF-e inválida")
        if not ValidadorChaveAcessoNFe.validar(ChaveAcessoNFe(chave)):
            raise ValueError("Chave NF-e inválida")
        expediente_formatado = pepe.utils.texto.formatar_sigla_sempapel(expediente)[1]

        chaves_autorizadas = self.listar_autorizacoes_cancelamento()
        if chave in [
            item["Chave de acesso da NF-e a ser cancelada"]
            for item in chaves_autorizadas
        ]:
            raise ValueError("Chave NF-e já cadastrada")

        r = self.session.get(
            URL_BASE + "Sistema/Obrigatoriedade/ContribuinteNfeExtemporanea.aspx"
        )
        self._update_asp_state(r.text)

        r = self.session.post(
            URL_BASE + "Sistema/Obrigatoriedade/ContribuinteNfeExtemporanea.aspx",
            data={
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "__EVENTVALIDATION": self.eventvalidation,
                "CNPJ": chave[6:20],
                "Gdoc": expediente_formatado,
                "NfeExtemporanea": chave,
                "Incluir": "Incluir",
            },
        )
        self._update_asp_state(r.text)

        chaves_autorizadas = self.listar_autorizacoes_cancelamento()
        if chave not in [
            item["Chave de acesso da NF-e a ser cancelada"]
            for item in chaves_autorizadas
        ]:
            raise KeyError(f"Não foi possível inserir autorização para chave {chave}")

    @preparar_metodo
    def desautorizar_cancelamento_extemporaneo(self, chave: str, expediente: str):
        """Descadastra uma autorização de cancelamento extemporâneo de NF-e.

        O descadastro faz com que o contribuinte não seja mais autorizado a submeter o
        evento de cancelamento.

        Args:
            chave (str): Chave da NF-e a ser impedido o cancelamento extemporâneo. Deve
                ser uma NF-e listada pelo método `listar_autorizacoes_cancelamento`.
            expediente (str): Indica o expediente Sem Papel ao qual está relacionada a
                autorização para cancelamento extemporâneo. Deve ser o mesmo apontado no
                cadastramento previamente realizado.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos, ou NF-e não
                cadastrada.
            KeyError: Erro indicando falha no descadastramento, possivelmente por ser
                uma NF-e emitida por CNPJ de outra circunscrição que não a do usuário.
        """
        if not re.search(r"^35\d{18}55\d{22}$", chave):
            raise ValueError("Chave NF-e inválida")
        if not ValidadorChaveAcessoNFe.validar(ChaveAcessoNFe(chave)):
            raise ValueError("Chave NF-e inválida")
        expediente_formatado = pepe.utils.texto.formatar_sigla_sempapel(expediente)[1]

        chaves_autorizadas = self.listar_autorizacoes_cancelamento()
        if chave not in [
            item["Chave de acesso da NF-e a ser cancelada"]
            for item in chaves_autorizadas
        ]:
            raise ValueError("Chave NF-e não cadastrada")
        eventtarget = [
            item["eventtarget"]
            for item in chaves_autorizadas
            if item["Chave de acesso da NF-e a ser cancelada"] == chave
        ][0]

        r = self.session.get(
            URL_BASE + "Sistema/Obrigatoriedade/ContribuinteNfeExtemporanea.aspx"
        )
        self._update_asp_state(r.text)

        r = self.session.post(
            URL_BASE + "Sistema/Obrigatoriedade/ContribuinteNfeExtemporanea.aspx",
            data={
                "__EVENTTARGET": eventtarget,
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "__EVENTVALIDATION": self.eventvalidation,
                "CNPJ": "",
                "Gdoc": expediente_formatado,
                "NfeExtemporanea": chave,
            },
        )
        self._update_asp_state(r.text)

        chaves_autorizadas = self.listar_autorizacoes_cancelamento()
        if chave in [
            item["Chave de acesso da NF-e a ser cancelada"]
            for item in chaves_autorizadas
        ]:
            raise KeyError(f"Não foi possível cancelar autorização para chave {chave}")
