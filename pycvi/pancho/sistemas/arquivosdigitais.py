"""Módulo com definições do sistema ArquivosDigitais."""
import datetime
import gzip
import os
import re
import tempfile
import zipfile

from bs4 import BeautifulSoup, Tag
from requests import Response

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import extrair_validadores_aspnet
from pepe.utils.login import login_identity_cert
from pepe.utils.texto import formatar_osf, limpar_texto

URL_BASE = "https://www10.fazenda.sp.gov.br/ArquivosDigitais"
URL_MAIN = URL_BASE + "/Pages/Menu.aspx"
URL_LOGIN = URL_BASE + "/Account/Login.aspx"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v002/"
    "Sefaz.Identity.STS.Certificado/LoginCertificado.aspx"
)
URL_WTREALM = "https://www10.fazenda.sp.gov.br/arquivosdigitais/Pages/Default.aspx"
URL_GIA = "https://cert01.fazenda.sp.gov.br/novaGiaWEB"

WCTX = "rm=0&id=STS.Windows.WebForms"
CLAIM_SETS = "FFFFFFFF"


class ArquivosDigitais(Sistema):
    """Representa o sistema [ArquivosDigitais](https://www10.fazenda.sp.gov.br/ArquivosDigitais).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe ArquivosDigitais.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6",
                "Cache-Control": "no-cache",
                "DNT": "1",
                "Host": "www10.fazenda.sp.gov.br",
                "Pragma": "no-cache",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "sec-ch-ua": (
                    '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"'
                ),
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/110.0.0.0 Safari/537.36",
            }
        )
        self._viewstate = ""
        self._viewstategenerator = ""
        self._eventvalidation = ""

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_MAIN)
        is_logged_in = not r.url.startswith(URL_LOGIN)
        if is_logged_in:
            # CAPTURANDO VALIDADORES
            (
                self._viewstate,
                self._viewstategenerator,
                self._eventvalidation,
            ) = extrair_validadores_aspnet(r.text)
        return is_logged_in

    def _pre_login(self):
        r = self.session.get(URL_LOGIN)

        # CAPTURANDO VALIDADORES
        (
            self._viewstate,
            self._viewstategenerator,
            self._eventvalidation,
        ) = extrair_validadores_aspnet(r.text)

        data = {
            "ctl00$ScriptManager1": "ctl00$ConteudoPagina$upnConsulta|"
            "ctl00$ConteudoPagina$btn_Login_Certificado_WebForms",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstategenerator,
            "__EVENTVALIDATION": self._eventvalidation,
            "ctl00$ConteudoPagina$btn_Login_Certificado_WebForms.x": "153",
            "ctl00$ConteudoPagina$btn_Login_Certificado_WebForms.y": "20",
        }
        self.session.post(URL_LOGIN, data=data)

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        self._pre_login()

        outros_params = {"wfresh": "60"}

        cookies_aute, r = login_identity_cert(
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

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario=usuario, senha=senha)

    @preparar_metodo
    def listar_entregas_efd_ecd(
        self, cnpj: str, periodo_inicial: str, periodo_final: str
    ) -> list[dict]:
        """Lista as entregas de EFD ou ECD realizadas pelo contribuinte.

        Args:
            cnpj (str): CNPJ do contribuinte, pode ser formatado ou não.
            periodo_inicial (str): Referência inicial para pesquisa no formato MM/AAAA.
            periodo_final (str): Referência final para pesquisa no formato MM/AAAA.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades da
            EFD ou ECD de determinada referência, podendo ser original ou substituta.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos, ou inexistência de
                entregas dentro do período solicitado.
        """
        URL_PESQUISA = URL_BASE + "/Pages/ConsultaEntregaArquivos.aspx"

        r = self.session.get(URL_PESQUISA)
        # CAPTURANDO VALIDADORES
        (
            self._viewstate,
            self._viewstategenerator,
            self._eventvalidation,
        ) = extrair_validadores_aspnet(r.text)

        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$btnPesquisar"
            ),
            "__EVENTTARGET": "ctl00$ConteudoPagina$btnPesquisar",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstategenerator,
            "__EVENTVALIDATION": self._eventvalidation,
            "ctl00$ConteudoPagina$usrControlFiltroTipoArquivoPesquisa$ddlTipoArquivo": (
                "EFD e ECD"
            ),
            "ctl00$ConteudoPagina$usrControlCNPJ$txtCNPJ": cnpj,
            "ctl00$ConteudoPagina$usrControlReferenciaInicial$txtReferencia": (
                periodo_inicial
            ),
            "ctl00$ConteudoPagina$usrControlReferenciaFinal$txtReferencia": (
                periodo_final
            ),
        }
        r = self.session.post(URL_PESQUISA, data=data)
        # CAPTURANDO VALIDADORES
        (
            self._viewstate,
            self._viewstategenerator,
            self._eventvalidation,
        ) = extrair_validadores_aspnet(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        erro = soup.find(id="ctl00_ConteudoPagina_ListaInconsistencia_ListErro")
        if erro:
            raise ValueError(erro.li.text)
        table = soup.find("table", {"class": "GridView"})

        # Extraindo nomes de campos
        tr_nomes = table.find("tr", {"class": "HeaderStyle"})
        nomes = [th.text for th in tr_nomes.find_all("th")]
        nomes = nomes[:-1]  # última coluna tem nome codificado

        trs = table.find_all("tr")
        resultado = self._scrape_tabela(nomes, trs[1:])

        # se existirem outras páginas, adiciona conteúdo delas
        # de forma recursiva, pois não consegui fazer funcionar o
        # request do PagerStyle :-(((
        # Então apaga a última referência buscada e coloca ela
        # como data início da recursão
        paginas = [a.text for a in trs[-1].find_all("a")]
        if paginas:
            ultima_referencia = resultado[-1]["Referência"]
            resultado = [
                efd for efd in resultado if efd["Referência"] != ultima_referencia
            ]
            resultado.extend(
                self.listar_entregas_efd_ecd(cnpj, ultima_referencia, periodo_final)
            )
        return resultado

    @staticmethod
    def _scrape_tabela(header: list[str], trs: list[Tag]):
        resultado = []
        # Extraindo valores de campos
        for tr in trs:
            # se chegou no paginador, pode parar
            if tr.get("class") is not None and "PagerStyle" in tr.get("class"):
                break
            tds = tr.find_all("td")
            if len(tds) > 1:
                valores = [limpar_texto(td.text) for td in tds]
                item = {nome: valor for nome, valor in zip(header, valores)}
                item.pop("", None)
                resultado.append(item)
        return resultado

    @preparar_metodo
    def baixar_arquivos_digitais(
        self,
        osf: str,
        caminho: str,
        inicio: str = None,
        fim: str = None,
        enviados_apos: datetime.date = None,
        apenas_mais_recente: bool = True,
    ) -> list[str]:
        """Baixa os arquivos SPED referentes às EFDs entregues por um contribuinte.

        Args:
            osf (str): Ordem de Serviço Fiscal, em que o usuário seja executante e
                esteja na situação "Em Execução", para que haja autorização para baixar
                arquivos.
            caminho (str): Caminho completo da pasta aonde serão salvos os arquivos
                localizados. Caso já haja arquivos no caminho com mesmos nomes daqueles
                a serem baixados, os existentes serão substituídos.
            inicio (str): Período inicial de download, no formato MM/AAAA.
            fim (str): Período final de download, no formato MM/AAAA.
            enviados_apos (date, optional): Caso esteja indicado, somente serão baixados
                arquivos entregues pelo contribuinte após a data indicada. Se não for
                indicada, serão baixados todos os arquivos do período entre os
                parâmetros início e fim.
            apenas_mais_recente (bool, optional): Indica se deverão apenas ser baixados
                os últimos arquivos entregues para cada referência (ou seja, EFDs
                atuais). Se `False`, serão baixados todos os arquivos entregues para
                cada referência. Valor padrão é `True`.

        Raises:
            ValueError: Erro indicando uso de parâmetros inválidos.
        """
        inicio = (
            datetime.date(2000, 1, 1)
            if inicio is None
            else datetime.datetime.strptime(inicio, "%m/%Y").date()
        )
        fim = (
            datetime.date.today()
            if fim is None
            else datetime.datetime.strptime(fim, "%m/%Y").date()
        )
        if enviados_apos is None:
            enviados_apos = inicio
        osf = formatar_osf(osf)[1]

        r = self.session.get(
            URL_BASE + "/Pages/DownloadArquivoDigital.aspx",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7",
                "Referer": (
                    "https://www10.fazenda.sp.gov.br/ArquivosDigitais/Pages/Menu.aspx"
                ),
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
            },
        )
        # CAPTURANDO VALIDADORES
        (
            self._viewstate,
            self._viewstategenerator,
            _,
        ) = extrair_validadores_aspnet(r.text, opcionais=["__EVENTVALIDATION"])

        self.session.headers.update(
            {
                "Accept": "*/*",
                "Origin": "https://www10.fazenda.sp.gov.br",
                "Referer": (
                    "https://www10.fazenda.sp.gov.br/"
                    + "ArquivosDigitais/Pages/DownloadArquivoDigital.aspx"
                ),
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-User": None,
                "Upgrade-Insecure-Requests": None,
                "X-MicrosoftAjax": "Delta=true",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$btnPesquisar"
            ),
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstategenerator,
            "ctl00$ConteudoPagina$btnPesquisar": "Pesquisar",
            "ctl00$ConteudoPagina$usrControlOSF$txtOSF": osf,
        }
        r = self.session.post(
            URL_BASE + "/Pages/DownloadArquivoDigital.aspx",
            data=data,
        )
        (
            self._viewstate,
            self._viewstategenerator,
            _,
        ) = extrair_validadores_aspnet(r.text, opcionais=["__EVENTVALIDATION"])

        tamanho_conjunto = 0
        ultima_referencia = ""
        ultima_referencia_recepcao = datetime.datetime(
            inicio.year, inicio.month, inicio.day
        )
        ultimo_tamanho = 0
        (
            resultado,
            tamanho_conjunto,
            ultimo_tamanho,
            ultima_referencia,
            ultima_referencia_recepcao,
        ) = self._baixa_arquivos_efd_de_uma_pagina(
            r,
            caminho,
            inicio,
            fim,
            enviados_apos,
            apenas_mais_recente,
            tamanho_conjunto,
            ultimo_tamanho,
            ultima_referencia,
            ultima_referencia_recepcao,
        )

        # Caso haja outras páginas num paginador, realiza as mesmas ações nelas
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"class": "GridView"})
        paginas = [a.text for a in table.find_all("tr")[-1].find_all("a")]
        for pagina in paginas:
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$grid"
                ),
                "ctl00$ConteudoPagina$ddlQtdPagina": "100",
                "ctl00$ConteudoPagina$usrControlFiltroTipoArquivoGrid$ddlFiltro": (
                    "Todos"
                ),
                "__EVENTTARGET": "ctl00$ConteudoPagina$grid",
                "__EVENTARGUMENT": f"Page${pagina}",
                "__LASTFOCUS": "",
                "__ASYNCPOST": "true",
                "__VIEWSTATE": self._viewstate,
                "__VIEWSTATEGENERATOR": self._viewstategenerator,
            }
            r = self.session.post(
                URL_BASE + "/Pages/DownloadArquivoDigital.aspx",
                data=data,
            )
            (
                self._viewstate,
                self._viewstategenerator,
                _,
            ) = extrair_validadores_aspnet(r.text, opcionais=["__EVENTVALIDATION"])

            (
                efds_pagina,
                tamanho_conjunto,
                ultimo_tamanho,
                ultima_referencia,
                ultima_referencia_recepcao,
            ) = self._baixa_arquivos_efd_de_uma_pagina(
                r,
                caminho,
                inicio,
                fim,
                enviados_apos,
                apenas_mais_recente,
                tamanho_conjunto,
                ultimo_tamanho,
                ultima_referencia,
                ultima_referencia_recepcao,
            )
            resultado.extend(efds_pagina)
        return resultado

    def _baixa_arquivos_efd_de_uma_pagina(
        self,
        r: Response,
        caminho: str,
        inicio: datetime.date,
        fim: datetime.date,
        enviados_apos: datetime.date,
        apenas_mais_recente: bool,
        tamanho_conjunto: int,
        ultimo_tamanho: int,
        ultima_referencia: str,
        ultima_referencia_recepcao: datetime.datetime,
    ):
        soup = BeautifulSoup(r.text, "html.parser")
        erro = soup.find(id="ctl00_ConteudoPagina_ListaInconsistencia_ListErro")
        if erro:
            raise ValueError(erro.li.text)
        table = soup.find("table", {"class": "GridView"})
        # descobrindo nomes dos campos das EFDs a serem baixadas
        campos = []
        trs = table.find_all("tr")[1:]
        for tr in trs:
            tds = tr.find_all("td")
            # chegou no paginador, encerra
            if tr.get("class") and "PagerStyle" in tr.get("class"):
                break
            valores = [limpar_texto(td.text) for td in tds]
            if valores[1] != "EFD-SP":
                continue
            referencia = datetime.datetime.strptime(
                "01/" + valores[3], "%d/%m/%Y"
            ).date()
            if referencia < inicio:
                ultima_referencia = referencia
                continue
            if referencia > fim:
                ultima_referencia = referencia
                break
            recepcao = re.findall(r"(\d+)\.(?:txt|TXT)\.(?:gz|GZ)$", valores[5])[0]
            datahora_recepcao = datetime.datetime.strptime(recepcao, "%d%m%Y%H%M%S")
            if datahora_recepcao.date() < enviados_apos:
                continue

            tamanho_atual = int(re.sub(r"\D", "", valores[2]))
            # verifica se deve baixar todas as EFDs da referencia ou apenas última
            if not apenas_mais_recente or referencia != ultima_referencia:
                campos.append(tds[0].input.get("name"))
                tamanho_conjunto += tamanho_atual
                ultima_referencia_recepcao = datahora_recepcao
            elif ultima_referencia_recepcao < datahora_recepcao:
                campos[-1] = tds[0].input.get("name")
                ultima_referencia_recepcao = datahora_recepcao
                tamanho_conjunto = tamanho_conjunto - ultimo_tamanho + tamanho_atual
            ultima_referencia = referencia
            ultimo_tamanho = tamanho_atual
        lista_arquivos = []
        if campos:
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$btnDownload"
                ),
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LAST_FOCUS": "",
                "__ASYNCPOST": "true",
                "__VIEWSTATE": self._viewstate,
                "__VIEWSTATEGENERATOR": self._viewstategenerator,
                "ctl00$ConteudoPagina$btnDownload": "Download",
            }
            # adiciona no post os nomes dos campos a serem baixados
            for campo in campos:
                data[campo] = "on"
            self.session.post(
                URL_BASE + "/Pages/DownloadArquivoDigital.aspx", data=data
            )
            (
                self._viewstate,
                self._viewstategenerator,
                _,
            ) = extrair_validadores_aspnet(r.text, opcionais=["__EVENTVALIDATION"])

            # dá ciência de sigilo do download para baixar
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$btnDownload"
                ),
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LAST_FOCUS": "",
                "__VIEWSTATE": self._viewstate,
                "__VIEWSTATEGENERATOR": self._viewstategenerator,
                "ctl00$ConteudoPagina$btnCiente": "Ciente",
            }
            r = self.session.post(
                URL_BASE + "/Pages/DownloadArquivoDigital.aspx", data=data
            )

            if "Content-Disposition" in r.headers and r.headers[
                "Content-Disposition"
            ].endswith("zip"):
                tmp = tempfile.NamedTemporaryFile("wb", delete=False)
                tmp.write(r.content)
                caminho_zip = tmp.name
                tmp.close()
            else:
                raise Exception(
                    f"Arquivo não pôde ser baixado! Resposta do servidor: {r.text}"
                )

            # depois de baixado, descompactar arquivo na pasta indicada
            # cada arquivo zip contém arquivos gz, que devem ser descompactados também
            with zipfile.ZipFile(caminho_zip, "r") as f:
                for arquivo in f.namelist():
                    f.extract(arquivo, path=caminho)
                    caminho_gz = os.path.join(caminho, arquivo)
                    with gzip.open(caminho_gz, "rb") as gz:
                        caminho_txt = os.path.join(caminho, arquivo[:-3])
                        with open(caminho_txt, "wb") as out:
                            out.write(gz.read())
                        lista_arquivos.append(caminho_txt)
                    os.unlink(caminho_gz)
            os.unlink(caminho_zip)

            # por fim, volta pra página com listagem, pois pode ter mais
            # coisas a baixar
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$upnConsulta|ctl00$ConteudoPagina$btnVoltar"
                ),
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LAST_FOCUS": "",
                "__ASYNCPOST": "true",
                "__VIEWSTATE": self._viewstate,
                "__VIEWSTATEGENERATOR": self._viewstategenerator,
                "ctl00$ConteudoPagina$btnVoltar": "Voltar",
            }
            r = self.session.post(
                URL_BASE + "/Pages/DownloadArquivoDigital.aspx", data=data
            )
            (
                self._viewstate,
                self._viewstategenerator,
                _,
            ) = extrair_validadores_aspnet(r.text, opcionais=["__EVENTVALIDATION"])
        return (
            lista_arquivos,
            tamanho_conjunto,
            ultimo_tamanho,
            ultima_referencia,
            ultima_referencia_recepcao,
        )
