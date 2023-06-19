"""Módulo com definições do sistema Sped."""

from bs4 import BeautifulSoup

from pepe import Sistema
from pepe.utils.html import scrape_tabela
from pepe.utils.texto import formatar_cnpj, formatar_ie

URL_BASE = "https://www.fazenda.sp.gov.br/sped"
URL_OBRIGADOS = URL_BASE + "/obrigados/obrigados.asp"


class Sped(Sistema):
    """Representa o sistema [Sped](https://www.fazenda.sp.gov.br/sped).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Sped.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        return super().autenticado()

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login_cert(nome_cert=nome_cert)

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario=usuario, senha=senha)

    def obter_historico_obrigatoriedade(self, ie: str = "", cnpj: str = "") -> dict:
        """Obtém o histórico de obrigatoriedade de emissão de EFD de um estabelecimento.

        Args:
            cnpj (str, opcional): CPNJ completo ou base do estabelecimento, com ou sem
                pontuação.
            ie (str, opcional): Inscrição Estadual (IE) do estabelecimento, com ou sem
                pontuação.

        Returns:
            Um dicionário com os dados de histórico de obrigatoriedade de um
            estabelecimento.
        """
        if ie:
            ie = formatar_ie(ie=ie)[0]
            r = self.session.get(URL_OBRIGADOS, params={"IE": ie})

            return Sped._scrape_historico_obrigatoriedade(r.text)

        if len(cnpj) == 8:
            cnpj = formatar_cnpj(cnpj=cnpj, base=True)[0]
            r = self.session.get(URL_OBRIGADOS, params={"CNPJBase": cnpj})

            return Sped._scrape_historico_obrigatoriedade(r.text)

        else:
            cnpj = formatar_cnpj(cnpj=cnpj, base=False)
            r = self.session.get(URL_OBRIGADOS, params={"CNPJLimpo": cnpj})

            return Sped._scrape_historico_obrigatoriedade(r.text)

    @staticmethod
    def _scrape_historico_obrigatoriedade(html):
        soup = BeautifulSoup(html, "html.parser")
        soup_tabela = soup.find("div", {"id": "tf_texto"}).table.find_all("table")[3]

        return scrape_tabela(tipo_entidade="multi", soup=soup_tabela)[0]
