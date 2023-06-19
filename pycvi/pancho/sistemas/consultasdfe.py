"""Módulo com definições do sistema Consultas DFe."""

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.login import login_identity_cert

URL_BASE = "https://www3.fazenda.sp.gov.br/One/ConsultaCupons/"
URL_DOWNLOAD_XML = URL_BASE + "DownloadXml"
URL_IDENTITY_INICIAL = "https://www3.fazenda.sp.gov.br/One/Login/LoginCartaoFazendario"
URL_WTREALM = "https://www3.fazenda.sp.gov.br/One/"
WCTX = (
    "rm=0&id=ctl00$conteudoPaginaPlaceHolder$loginControl"
    "$FederatedPassiveSignInCertificado"
    "rm=0&id=4ae29287-5635-4a63-b362-2d7d15f0bdb8&ru="
    "https://www3.fazenda.sp.gov.br/One/"
)
CLAIM_SETS = "80F30E33"


class ConsultasDfe(Sistema):
    """Representa o sistema [Consultas DFe](https://www3.fazenda.sp.gov.br/One/ConsultaCupons).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe ConsultasDfe.

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

        return '<a href="/One/Login/Logout">' in r.text

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        cookies_aute, _ = login_identity_cert(
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=URL_WTREALM,
            wctx=WCTX,
            claim_sets=CLAIM_SETS,
            nome_cert=nome_cert,
            cookies=self.session.cookies,
        )
        self.session.cookies.update(cookies_aute)

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def baixar_xml(self, chave_acesso: str, caminho: str):
        """Baixa a versão XML de um documento fiscal.

        Args:
            chave_acesso (str): Chave de acesso do documento fiscal eletrônico, com 44
                dígitos.
            caminho (str): Caminho completo onde será salvo o arquivo XML, incluindo o
                nome do arquivo.
        """
        data = {"chave": chave_acesso}
        r = self.session.post(URL_DOWNLOAD_XML, data=data)

        with open(caminho, "w") as f:
            f.write(r.text)
