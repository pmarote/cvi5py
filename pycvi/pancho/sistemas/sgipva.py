"""Módulo com definições do sistema SGIPVA."""

from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.login import login_identity_cert

URL_BASE = "https://sefaznet11.intra.fazenda.sp.gov.br/SGIPVAF2/"
URL_CONSULTA_VEICULO = URL_BASE + "Veiculo/ConsultarVeiculo"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v003/"
    "Sefaz.Identity.STS.PortalSSO/LoginPortalSSO.aspx"
)
URL_WTREALM = "https://sefaznet11.intra.fazenda.sp.gov.br/SGIPVAF2/Login/Logon"
WCTX = "https://sefaznet11.intra.fazenda.sp.gov.br/SGIPVAF2/Login/Logon"
CLAIM_SETS = "80F10000"
TIPO_LOGIN = "1"
AUTO_LOGIN = "1"
COMBO_PESQUISA = {"renavam": "2", "placa": "3", "cnpj": "4", "cpf": "5"}


class Sgipva(Sistema):
    """Representa o sistema [SGIPVA](https://sefaznet11.intra.fazenda.sp.gov.br/SGIPVAF2/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Sgipva.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE)
        soup = BeautifulSoup(r.text, "html.parser")
        el_usuario_logado = soup.find(id="usuarioLogado")

        return bool(el_usuario_logado.text.strip())

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        outros_params = {"TipoLogin": TIPO_LOGIN, "AutoLogin": AUTO_LOGIN}

        cookies_aute, _ = login_identity_cert(
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=URL_WTREALM,
            claim_sets=CLAIM_SETS,
            wctx=WCTX,
            outros_params=outros_params,
            nome_cert=nome_cert,
            cookies=self.session.cookies,
        )
        self.session.cookies.update(cookies_aute)

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def obter_veiculo(
        self, renavam: str = None, placa: str = None, cnpj: str = None, cpf: str = None
    ) -> dict:
        """Obtém dados de um veículo.

        Apenas um dos parâmetros deve ser utilizado em uma chamada a esse método.

        Args:
            renavam (str): RENAVAM do veículo (zeros iniciais podem ser ignorados).
            placa (str): Placa do veículo, sem traço.
            cnpj (str): CNPJ do proprietário do veículo, com ou sem pontuação.
            cpf (str): CPF do proprietário do veículo, com ou sem pontuação.

        Returns:
            um dicionário com os dados do veículo.
        """
        if bool(renavam) + bool(placa) + bool(cnpj) + bool(cpf) != 1:
            raise ValueError(
                "É obrigatório passar um valor para um dos parâmetros: "
                "renavam, placa, cnpj ou cpf. Apenas um valor deve ser passado."
            )

        parametro, valor = [
            (key, value) for key, value in locals().items() if key != "self" and value
        ][0]
        params = {"comboPesquisa": COMBO_PESQUISA[parametro], "txtPesquisa": valor}
        r = self.session.get(URL_CONSULTA_VEICULO, params=params)

        return Sgipva._scrape_veiculo(html=r.text)

    @staticmethod
    def _scrape_veiculo(html):
        dados = {}
        soup = BeautifulSoup(html, "html.parser")
        fs_veiculo = soup.find(id="veiculo")
        rows = fs_veiculo.find_all("div", class_="row")

        for i in range(0, len(rows), 2):
            campos = [label.text for label in rows[i].find_all("label")]
            valores = [div.text.strip() for div in rows[i + 1].find_all("div")]
            dados |= {c: v for c, v in zip(campos, valores)}

        return dados
