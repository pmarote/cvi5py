"""Módulo com definições do sistema Cassação de Contribuintes."""

from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema
from pepe.utils.login import login_identity_cert

URL_BASE = "https://sefaznet11.intra.fazenda.sp.gov.br/cassacao/"
URL_AUTENTICADO = URL_BASE + "Pages/Menu.aspx"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v002/"
    "Sefaz.Identity.STS.Certificado/LoginCertificado.aspx"
)
URL_WTREALM = "https://sefaznet11.intra.fazenda.sp.gov.br/cassacao/Pages/Default.aspx"
WCTX = "https://sefaznet11.intra.fazenda.sp.gov.br/cassacao/Pages/Default.aspx"
CLAIM_SETS = "FFFFFFFF"


class CassacaoContribuintes(Sistema):
    """Representa o sistema [Cassação de Contribuintes](https://sefaznet11.intra.fazenda.sp.gov.br/cassacao/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe CassacaoContribuintes.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/99.0.4844.83 Safari/537.36"
                )
            }
        )

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        self.session.headers.update({"Cache-Control": "max-age=0"})

        r = self.session.get(URL_AUTENTICADO)
        soup = BeautifulSoup(r.text, "html.parser")
        lbl_usuario = soup.find("label", id="usuario")

        return bool(lbl_usuario.text.strip())

    def login_cert(self, nome_cert) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        outros_params = {"wfresh": "1"}
        cookies_auten, _ = login_identity_cert(
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=URL_WTREALM,
            claim_sets=CLAIM_SETS,
            wctx=WCTX,
            outros_params=outros_params,
            nome_cert=nome_cert,
        )

        self.session.cookies.update(cookies_auten)

        if not self.autenticado():
            raise AuthenticationError()
