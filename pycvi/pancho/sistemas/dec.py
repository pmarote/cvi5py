"""Módulo com definições do sistema Dec."""
import datetime
import os
import re
from urllib.parse import urlencode

import urllib3
import win32com.client
from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import extrair_validadores_aspnet, scrape_tabela

URL_BASE = "https://sefaznet11.intra.fazenda.sp.gov.br/DEC/"
URL_LOGIN = URL_BASE + "UCLogin/login.aspx"
URL_HOME = URL_BASE + "UCGeraMensagem/ExibeRascunhos.aspx"
URL_CONSULTA_PUBLICA = URL_BASE + "UCConsultaPublica/Consulta.aspx"


def _formatar_identificador_mensagem(identificador: str = ""):
    identificador_regex = re.compile(
        r"(\w{2})/([ACNI])/(\w{3})/(\d+)/(\d{4})",
        re.VERBOSE,
    )

    id_char = identificador_regex.search(identificador.upper())
    if not id_char:
        raise ValueError(
            "Valor no parâmetro identificador deve conter texto no formato "
            "XX/X/XXX/XXXXXXXXX/XXXX."
        )
    if not 2000 <= int(id_char[5]) <= datetime.date.today().year:
        raise ValueError(f"Ano do identificador DEC inválido ({id_char[5]})")
    return f"{id_char[1]}/{id_char[2]}/{id_char[3]}/{id_char[4].zfill(9)}/{id_char[5]}"


class Dec(Sistema):
    """Representa o sistema [Dec](https://sefaznet11.intra.fazenda.sp.gov.br/DEC/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Dec.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.viewstate = ""
        self.viewstategenerator = ""
        self.eventvalidation = ""
        self.eventtarget = ""
        self.in_transaction = False
        self.lastfocus = ""
        self.viewstateencrypted = ""
        self.html_dados_usuario = ""

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_HOME)
        return "lblUsuario" in r.text

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        self._pre_login()
        specific_payload = {
            "menu1": "Destaques",
            "ctl00$ConteudoPagina$btnCertificacao.x": "21",
            "ctl00$ConteudoPagina$btnCertificacao.y": "30",
        }
        specific_payload.update(self._asp_payload())
        r = self.session.post(URL_LOGIN, data=specific_payload)
        self._update_asp_variables(r.text)
        # Requests não suporta certificados em smartcards, WinHttp (PyWin32) sim
        # Tratar apenas erro de certificado
        if "Erro na identificação do winlogon do usuário" in r.text:
            winhttp = win32com.client.Dispatch("WinHTTP.WinHTTPRequest.5.1")
            winhttp.Open("POST", r.url)
            domain = urllib3.util.parse_url(r.url).netloc
            # Adiciona na chamada HTTP via COM os cookies para o domínio
            for c in [c for c in self.session.cookies if c.domain == domain]:
                winhttp.SetRequestHeader("Cookie", f"{c.name}={c.value}")
            winhttp.SetClientCertificate(nome_cert)
            specific_payload.update(self._asp_payload())
            winhttp.Send(urlencode(specific_payload))
            texto_resposta = winhttp.responseText
            self._update_asp_variables(texto_resposta)
            self.html_dados_usuario = texto_resposta

            specific_payload = {
                "menu1": "Destaques",
                "ctl00$ConteudoPagina$lstPerfil": "Natural",
                "ctl00$ConteudoPagina$btnContinuar": "Continuar",
            }
            specific_payload.update(self._asp_payload())
            r = self.session.post(
                URL_BASE + "UCLogin/ExibeDadosUsuario.aspx", specific_payload
            )
            self._update_asp_variables(r.text)

        if r.url != URL_HOME:
            raise AuthenticationError()

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario=usuario, senha=senha)

    def obter_situacao(self, cnpj: str) -> dict:
        """Obtém a situação junto ao DEC de um estabelecimento.

        Args:
            cnpj (str): CNPJ completo do estabelecimento, com ou sem pontuação.

        Returns:
            Um dicionário que contém as propriedades da situação do estabelecimento.
        """
        r = self.session.get(URL_CONSULTA_PUBLICA)
        self._update_asp_variables(r.text)
        data = {
            "ctl00$ConteudoPagina$txtEstabelecimentoBusca": cnpj,
            "ctl00$ConteudoPagina$btnBuscarPorEstabelecimento": "Buscar",
            "menu1": "Destaques",
        }
        data.update(self._asp_payload())
        r = self.session.post(r.url, data=data)

        return Dec._scrape_consulta_publica(html=r.text)

    @preparar_metodo
    def obter_dados_usuario(self) -> dict:
        """Obtém os dados do usuário.

        Dados do usuário são aqueles que aparecem no início da sessão do DEC, o login,
        nome completo, cargo, CPF e e-mail.

        Returns:
            Um dicionário contendo os dados do usuário.
        """
        r = self.session.get(URL_BASE + "UCLogin/ExibeDadosUsuario.aspx")
        soup = BeautifulSoup(r.text, "html.parser")
        linhas_tabela = soup.find_all("td", {"class": "DEC_esquerda"})
        linhas = [t.find("span") for t in linhas_tabela if t.find("span")]
        return {span["id"][18:]: span.text for span in linhas}

    @preparar_metodo
    def baixar_mensagem(
        self, identificador: str, caminho_mensagem: str, pasta_anexos: str = ""
    ):
        """Baixa PDFs da mensagem DEC e eventuis anexos.

        Args:
            identificador (str): Número da mensagem DEC, cou ou sem zeros, no formato
                XX/X/XXX/numero/ano.
            caminho_mensagem (str): Caminho completo onde será baixado o PDF da
                mensagem, incluindo o nome do arquivo. Deve terminar com .pdf.
            pasta_anexos (str, optional): Caminho completo onde serão baixados os PDFs
                dos anexos da mensagem. Deve ser um diretório, não um nome de arquivo.
                Se não for informado, não serão baixados os anexos.
        """
        id_formatado = _formatar_identificador_mensagem(identificador)
        ano = id_formatado[-4:]
        url = URL_BASE + "UCConsultaMensagem/ConsultaMensagens.aspx?Tipo=All"
        self._update_asp_variables(self.session.get(url).text)

        # faz a pesquisa após abrir a página de consulta
        specific_payload = {
            "ctl00$ConteudoPagina$txtIdentificacao": id_formatado,
            "ctl00$ConteudoPagina$DataEnvioIniBusca": f"01/01/{ano}",
            "ctl00$ConteudoPagina$DataEnvioFimBusca": f"31/12/{ano}",
            "ctl00$ConteudoPagina$lstTipoCiencia": "0",
            "ctl00$ConteudoPagina$btnBuscar": "Buscar",
            "menu1": "Destaques",
            "ctl00$ConteudoPagina$txtLoginEmitente": "",
            "ctl00$ConteudoPagina$txtAno": "",
            "ctl00$ConteudoPagina$lstCategoria": "-1",
            "ctl00$ConteudoPagina$lstTributo": "-1",
            "ctl00$ConteudoPagina$lstTipoMensagem": "-1",
            "ctl00$ConteudoPagina$lstAssunto": "-1",
            "ctl00$ConteudoPagina$txtComplementoAssunto": "",
            "ctl00$ConteudoPagina$lstTipoDestinatario": "",
            "ctl00$ConteudoPagina$txtNome": "",
        }
        specific_payload.update(self._asp_payload())
        r = self.session.post(url, data=specific_payload)
        self._update_asp_variables(r.text)

        # verifica se encontrou o link para a notificação
        soup = BeautifulSoup(r.text, "html.parser")
        msgs = soup.find(id="ConteudoPagina_gvMensagens").find_all(
            "a", {"id": re.compile(".*LinkConsultarMsg.*")}
        )
        if not msgs:
            raise ValueError(f"Não foi localizada mensagem {id_formatado}")
        self._set_eventtarget_from_postback(msgs[0]["href"])
        specific_payload = {
            "menu1": "Destaques",
            "ctl00$ConteudoPagina$tbPaginacao$ddlPagina": "1",
        }
        specific_payload.update(self._asp_payload())
        r = self.session.post(url, data=specific_payload)
        self._update_asp_variables(r.text)

        # buscar informações da abertura de nova janela com o conteúdo da notificação
        soup = BeautifulSoup(r.text, "html.parser")
        regex_script = re.compile(r"window.open\('(.*)'")
        script = soup.find("script", text=regex_script)
        if not script:
            raise ValueError(
                f"Não localizou link para abrir notificação {id_formatado}"
            )
        link = regex_script.search(script.text).group(1).split("'")[0][5:]

        r = self.session.get(URL_BASE + link)
        self._update_asp_variables(r.text)

        # primeiro baixa a própria mensagem...
        # link para ReportServices dentro de script
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find(
            "script", {"language": "javascript"}, text=re.compile(r"RSClientController")
        )
        link_report_services = re.search(r'"\\/DEC\\/(.*Format=)"', tag.text).group(1)
        mensagem_pdf = self.session.get(URL_BASE + link_report_services + "PDF").content
        with open(caminho_mensagem, mode="wb") as anexo:
            anexo.write(mensagem_pdf)

        if pasta_anexos:
            # agora vai baixar cada um dos anexos, se existirem...
            specific_payload = {
                "ReportViewer1$ctl01$ctl05$ctl00": "Select a format",
                "ReportViewer1$ctl04": "",
                "ReportViewer1$ctl05": "",
                "ReportViewer1$ctl06": "1",
                "ReportViewer1$ctl07": "false",
                "ReportViewer1$ctl08": "false",
            }
            for anexo_tag in soup.find_all(
                "a", {"id": re.compile(r"ListaAnexos_LnkDownload_\d+")}
            ):
                self._set_eventtarget_from_postback(anexo_tag["href"])
                specific_payload.update(self._asp_payload())
                r = self.session.post(URL_BASE + link, specific_payload)
                with open(
                    os.path.join(pasta_anexos, anexo_tag.text), mode="wb"
                ) as anexo:
                    anexo.write(r.content)

    @staticmethod
    def _scrape_consulta_publica(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id="ConteudoPagina_Panel4")
        table.find_all("tr")[-1].decompose()  # Remove o último TR
        dados = scrape_tabela(
            tipo_entidade="unica",
            soup=table,
            pular_td=2,
            limiar_similaridade=0.85,
        )

        return {k[:-1] if k.endswith(":") else k: v for k, v in dados.items()}

    def _pre_login(self):
        self.session.headers.update(
            {
                "DNT": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/99.0.4844.83 Safari/537.36",
                "Accept-Language": "pt-BR,pt/q=0.9",
            }
        )
        req = self.session.get(URL_LOGIN)
        self._update_asp_variables(req.text)

    def _update_asp_variables(self, text: str):
        # CAPTURANDO VALIDADORES
        (
            self.viewstate,
            self.viewstategenerator,
            self.eventvalidation,
        ) = extrair_validadores_aspnet(text)
        if (
            not self.viewstate
            or not self.viewstategenerator
            or not self.eventvalidation
        ):
            raise AuthenticationError("DEC ficou perdido no meio da autenticação!")

        self.eventtarget = ""
        soup = BeautifulSoup(text, "html.parser")
        try:
            self.viewstateencrypted = soup.find("input", id="__VIEWSTATEENCRYPTED")[
                "value"
            ]
            self.lastfocus = soup.find("input", id="__LASTFOCUS")["value"]
            self.in_transaction = True
        except Exception:
            self.viewstateencrypted = ""
            self.lastfocus = ""
            self.in_transaction = False

    def _asp_payload(self) -> dict[str, str]:
        dicionario = {
            "__EVENTTARGET": self.eventtarget,
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self.viewstate,
            "__VIEWSTATEGENERATOR": self.viewstategenerator,
            "__EVENTVALIDATION": self.eventvalidation,
        }
        if self.in_transaction:
            dicionario.update(
                {
                    "__VIEWSTATEENCRYPTED": self.viewstateencrypted,
                    "__LASTFOCUS": self.lastfocus,
                }
            )
        return dicionario

    def _set_eventtarget_from_postback(self, javascript_link: str):
        self.eventtarget = javascript_link.split("'")[1]
