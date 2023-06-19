"""Módulo com definições do sistema Sei."""
from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema

URL_BASE = "https://sei.sp.gov.br/sei/"
URL_LOGIN = "https://sei.sp.gov.br/sip/login.php"


class Sei(Sistema):
    """Representa o sistema [Sei](https://sei.sp.gov.br/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Sei.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(url=URL_BASE)
        return "Sair do Sistema" in r.text

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        params = {
            "sigla_orgao_sistema": "GESP",
            "sigla_sistema": "SEI",
            "infra_url": "L3NlaS8=",
        }
        data = {
            "txtUsuario": usuario,
            "pwdSenha": senha,
            "hdnAcao": "2",
            "selOrgao": "17",
        }
        self.session.post(URL_LOGIN, params=params, data=data)

        if not self.autenticado():
            raise AuthenticationError()

    def listar_tipos_processo(self) -> list:
        """Listar tipos de processos.

        Retorna uma lista de tipos de processos que podem ser criados pelo
        seu Órgão.

        Returns: lista com opções para tipo do processo.

        """
        r = self.session.get(url=URL_BASE)
        soup = BeautifulSoup(r.text, "html.parser")
        url_complemento = (
            soup.find("ul", {"id": "infraMenu"})
            .find(lambda tag: tag.name == "a" and "Iniciar Processo" in tag.text)
            .get("href")
        )
        r = self.session.get(url=URL_BASE + url_complemento)
        soup = BeautifulSoup(r.text, "html.parser")
        formulario = soup.find("form", {"id": "frmIniciarProcessoEscolhaTipo"})
        url_complemento = formulario.get("action")
        data = {"hdnInfraTipoPagina": "1", "hdnFiltroTipoProcedimento": "T"}
        r = self.session.post(url=URL_BASE + url_complemento, data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        tds = soup.find("table", {"id": "tblTipoProcedimento"}).tbody.find_all("td")
        lista_opcoes = [td.find_all("a")[1].text for td in tds]
        return lista_opcoes
