"""Módulo com definições do sistema Classificação de Contribuintes do ICMS."""

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.login import login_identity_cert
from pepe.utils.texto import formatar_cnpj

URL_BASE = "https://www3.fazenda.sp.gov.br/Classificacao/"
URL_IDENTITY_INICIAL = URL_BASE + "Login/ValidarCertificadoAdminPFe"
URL_CONSULTA_CLASSIFICACAO = URL_BASE + "Fazendario/ConsultarClassificacao"
URL_LISTAR_CLASSIFICACAO = URL_BASE + "Fazendario/ListarClassificacao"
URL_WTREALM = URL_BASE + "/Login/Logado"
CLAIM_SETS = "FFFFFFFF"


class Classificacao(Sistema):
    """Representa o sistema [Classificação de Contribuintes do ICMS](https://www3.fazenda.sp.gov.br/classificacao/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Classificacao.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_CONSULTA_CLASSIFICACAO)

        return (
            "javascript: location.href='/Classificacao/Classificacao/Encerrar'"
            in r.text
        )

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        cookies_aute, r = login_identity_cert(
            nome_cert=nome_cert,
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=URL_WTREALM,
            claim_sets=CLAIM_SETS,
            wctx=URL_WTREALM,
        )
        self.session.cookies.update(cookies_aute)

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def listar_classificacoes(
        self, cnpj_base: str = "", razao_social: str = ""
    ) -> list:
        """Lista classificações de uma empresa.

        Args:
            cnpj_base (str, optional): CNPJ base da empresa, com ou sem pontuação.
                Obrigatório se não for passado alguma valor para `razao_social`.
            razao_social (str, optional): Razão social da empresa (completo ou parcial).
                Obrigatório se não for passado alguma valor para `cnpj_base`.

        Returns:
            Uma lista de classificações.

        Raises:
            ValueError: Erro indicando que não foi passado um valor para `cnpj_base` ou
            `razao_social`.
        """
        if not cnpj_base and not razao_social:
            raise ValueError("É obrigatório um valor de 'cnpj_base' ou 'razao_social'.")

        cnpj_formatado = formatar_cnpj(cnpj_base, base=True)[0]
        data = {"nrCnpjBase": cnpj_formatado, "nmRazaoSocial": razao_social}
        r = self.session.post(URL_LISTAR_CLASSIFICACAO, json=data)

        return r.json()["Content"]
