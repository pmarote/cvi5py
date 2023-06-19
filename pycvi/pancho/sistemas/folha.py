"""Módulo com definições do sistema Folha de Pagamento."""

from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema, preparar_metodo

URL_BASE = "https://www.fazenda.sp.gov.br/folha/nova_folha/"
URL_INICIAL = URL_BASE + "menu_inicial.asp"
URL_LOGIN_FORM = URL_BASE + "acessar_dce.asp?user=rs"
URL_LOGIN_POST = URL_BASE + "autentica.asp"
URL_FOLHA_DETALHE = URL_BASE + "dem_pagto_vis_rs.asp"

TIPO_FOLHA_NORMAL = "0"
TIPO_FOLHA_SUPLEMENTAR = "5"
TIPO_FOLHA_13 = "8"


class FolhaPagamento(Sistema):
    """Representa o sistema [Folha de Pagamento](https://www.fazenda.sp.gov.br/folha/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_INICIAL)

        return "Alterar Senha" in r.text

    def login(self, usuario, senha) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        self._usuario = usuario
        self._configurar_cookie_login()

        data = {
            "hid_tipouser": "rs",
            "txt_logindce": usuario,
            "txt_senhadce": senha,
            "enviar": "Acessar",
        }

        r = self.session.post(URL_LOGIN_POST, data=data)  # noqa: F841

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def obter_folha_normal(self, mes: int, ano: int) -> dict:
        """Obtém uma folha normal (que não é suplementar).

        Args:
            mes (int): número do mês da folha (1-12)
            ano (_type_): número do ano da folha (4 dígitos)

        Raises:
            TypeError: Erro indicando data inválida.

        Returns:
            Um dicionário com que contém propriedades de uma folha.
        """
        if not (
            isinstance(mes, int)
            and mes >= 1
            and mes <= 12
            and isinstance(ano, int)
            and ano >= 1900
            and ano <= 2100
        ):
            raise TypeError("Data inválida")

        params = {
            "sq": "1",
            "tp": "0",
            "dt": "1" + str(ano)[-2:] + str(mes).zfill(2),
            "rb": "0",
            "rs": self._usuario,
            "nro": "0",
            "tabela": "atual",
            "sit": "4",
            "pv": "01",
            "opcao_pagto": "visualizar",
            "tipo_usuario": "rs",
        }

        r = self.session.get(URL_FOLHA_DETALHE, params=params)
        detalhes_folha = {}
        soup = BeautifulSoup(r.text, "html.parser")
        div_area_impressao = soup.find("div", id="area_impressao")
        fonts = div_area_impressao.find_all("font", color="#000000")

        for font in fonts:
            campo = font.parent.b.text.strip()
            valor = font.text.strip()
            detalhes_folha[campo] = valor

        detalhes_folha["rubricas"] = []
        tbl_rubricas = div_area_impressao.find_all("table", class_="tabela1")[6]

        for tbody in tbl_rubricas.find_all("tbody"):
            linha = [font.text.strip() for font in tbody.find_all("font")]
            detalhes_folha["rubricas"].append(linha)

        return detalhes_folha

    def _configurar_cookie_login(self) -> None:
        self.session.get(URL_LOGIN_FORM)
