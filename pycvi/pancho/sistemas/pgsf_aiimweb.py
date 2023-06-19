"""Módulo com definições do sistema AIIMWEB."""

import os
import webbrowser

from bs4 import BeautifulSoup
from selectorlib import Extractor

from pepe import Pgsf

URL_BASE = "https://portal60.sede.fazenda.sp.gov.br/"
URL_AUTENTICADO = URL_BASE + "wps_migrated/myportal"
URL_AIIMWEB_MENU = URL_BASE + "AIIMWeb/menu.do?path=selecionarAIIM"
URL_AIIMWEB_CONSULTAR = URL_BASE + "AIIMWeb/selecao.do"
URL_LOGIN_REDIRECT = URL_BASE + "wps_migrated/myportal/!ut/p/b1/0wcA1NLTeQ!!/"


class Aiimweb(Pgsf):
    """Representa o sistema AIIMWEB.

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=None) -> None:
        raise NotImplementedError(
            "Classe não funciona devido a mudanças na classe pai Pgsf"
        )

    def obter_aiim(self, num_aiim: str):
        """Obtém detalhes de um AIIM.

        Os campos retornados são os mesmos que aparecem ao Consultar Detalhes do AIIM
        no PGSF.

        Args:
            num_aiim (str): Número completo da AIIM, com ou sem pontuação.

        Returns:
            Um dicionário que contém as propriedades do AIIM.

        Raises:
            ValueError: Erro indicando que valor passado para o parâmetro `num_aiim` não
            é uma string que contém 8 números.
        """
        aiim = {}

        num_aiim_digits = "".join(i for i in num_aiim if i.isdigit())
        if len(num_aiim_digits) != 8:
            raise Exception("num_aiim deve conter 8 números.")
        num_aiim_sem_digito_verificador = num_aiim_digits[:-1]
        # num_aiim_sem_digito_verificador = "4145829"

        r = self.session.get(URL_LOGIN_REDIRECT)

        self._configurar_cookie_iframe_aiim()
        # Abrindo MENU da Consulta
        r = self.session.get(URL_AIIMWEB_MENU)
        # soup = BeautifulSoup(r.text, "html.parser")

        # Consultar AIIM
        URL_CONSULTA = (
            "AIIMWeb/"
            + "selecao.do?tpConsulta=0&tpDocumento=5&documento="
            + num_aiim_sem_digito_verificador
            + "&nrAiim="
            + num_aiim_sem_digito_verificador
            + "&dsDocumento="
            + num_aiim_sem_digito_verificador
        )
        r = self.session.post(URL_BASE + URL_CONSULTA)
        dados = Aiimweb._scrape_obter_detalhes_aiim(r.text)

        aiim["detalhes_aiim"] = dados["detalhes_aiim"]

        # Consultar Relato
        URL_CONSULTA = (
            "AIIMWeb/"
            + "selecao.do?tpConsulta=4&tpDocumento=5&cdDocumento="
            + num_aiim_sem_digito_verificador
            + "&documento="
            + num_aiim_sem_digito_verificador
            + "&nrAiim="
            + num_aiim_sem_digito_verificador
            + "&tpInfrator=2"
        )
        r = self.session.post(URL_BASE + URL_CONSULTA)

        # Caso seja necessário gerar um arquivo local para testar posteriormente:
        # Aiimweb._salvar_e_exibir_html(r.content)

        dados = Aiimweb._scrape_obter_relato(r.text)
        # Ajustando campo com base na: descricao_infringencia_capitulacao
        # """
        lista_valores = [k for k in dados.values()]
        valores = lista_valores[0]
        num_itens_aiim = int(len(valores) / 3)
        itens_aiim = {}
        dados_relato = {}
        for i in range(num_itens_aiim):
            dados_relato["descricao"] = valores[i]["descricao_infringencia_capitulacao"]
            dados_relato["infringencia"] = valores[i + 1][
                "descricao_infringencia_capitulacao"
            ]
            dados_relato["capitulacao"] = valores[i + 2][
                "descricao_infringencia_capitulacao"
            ]
            num_item_aiim = i + 1
            itens_aiim[num_item_aiim] = dados_relato
        # """

        aiim["relato"] = itens_aiim
        # aiim["relato"] = dados
        return aiim

    def _obter_url_aiim_consulta(self):
        r = self.session.get(URL_AUTENTICADO)
        soup = BeautifulSoup(r.text, "html.parser")
        script_rel_result = soup.find(lambda tag: "Consulta&nbsp;&nbsp" in tag.text)
        url_rel_result = script_rel_result.text.split('"')[5]

        return url_rel_result

    def _obter_url_iframe_aiim(self):
        url_rel_result = self._obter_url_aiim_consulta()
        r = self.session.get(URL_BASE + url_rel_result)
        soup = BeautifulSoup(r.text, "html.parser")
        url_iframe = soup.iframe["src"]

        return url_iframe

    def _configurar_cookie_iframe_aiim(self) -> None:
        # if not self._url_iframe:
        self._url_iframe = self._obter_url_iframe_aiim()

        self.session.get(self._url_iframe)
        self._cookie_iframe_configurado = True

    def formatar_num_aiim(num_aiim: str):
        """Formata um número de Inscrição Estadual (IE).

        Args:
            num_aiim (str): IE para ser formatada. Pode ser qualquer string contendo 12
                números.

        Returns:
            Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas
                os dígitos da IE e `completa` é um `str` no formato "X.XXX.XXX-X".

        Raises:
            ValueError: Erro indicando que valor passado para o parâmetro `ie` não é uma
                string que contém 7 números.
        """
        num_aiim_digits = "".join(i for i in num_aiim if i.isdigit())

        if len(num_aiim_digits) != 7:
            raise Exception("num_aiim deve conter 8 números.")

        num_aiim_char = (
            num_aiim_digits[0]
            + "."
            + num_aiim_digits[1:3]
            + "."
            + num_aiim_digits[4:6]
            + "-"
            + num_aiim_digits[7]
        )

        return num_aiim_digits, num_aiim_char

    # Funções estáticas

    @staticmethod
    def _scrape_obter_detalhes_aiim(html):
        caminho_yaml = os.path.join(
            os.path.dirname(__file__), "yaml", "aiimweb_pgsf_aiim.yaml"
        )
        e = Extractor.from_yaml_file(caminho_yaml)

        return e.extract(html)

    @staticmethod
    def _scrape_obter_relato(html):
        caminho_yaml = os.path.join(
            os.path.dirname(__file__), "yaml", "aiimweb_pgsf_relato.yaml"
        )
        e = Extractor.from_yaml_file(caminho_yaml)

        return e.extract(html)

    # Funções utilizadas em testes locais

    @staticmethod
    def _salvar_e_exibir_html(html, exibir=True, caminho="page.html"):
        soup = BeautifulSoup(html, "html.parser")
        # write the page content to a file
        open(caminho, "w").write(str(soup))
        # open the page on the default browser
        if exibir:
            webbrowser.open("page.html")

    @staticmethod
    def _carregar_html(caminho="page.html"):
        # write the page content to a file
        with open(caminho) as html:
            soup = BeautifulSoup(html, "html.parser")
        # print(str(soup.find_all("td", class_="texto2")))
        # open the page on the default browser
        return soup
