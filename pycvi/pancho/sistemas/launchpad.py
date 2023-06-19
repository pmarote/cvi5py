"""Módulo com definições do sistema BI LaunchPad."""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from queue import LifoQueue, SimpleQueue
from typing import Dict, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests_kerberos import HTTPKerberosAuth

from pepe import AuthenticationError, Sistema
from pepe.sistemas.base import preparar_metodo

URL_BASE = "https://srvbo-v42.intra.fazenda.sp.gov.br"
URL_BASE_LDAP = "https://srvbo-v42.intra.fazenda.sp.gov.br/BOE"
URL_LOGIN = URL_BASE + "/biprws/logon/adsso"
URL_LOGOUT = URL_BASE + "/biprws/logoff"
URL_API = URL_BASE + "/biprws/raylight/v1"

AUTH = "secLDAP"
PASTA_SEFAZ_ID = 25804


class LaunchPad(Sistema):
    """Representa o sistema [BI LaunchPad](https://srvbo-v42.intra.fazenda.sp.gov.br).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=None) -> None:
        """Cria um objeto da classe LaunchPad.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.modo_login = None
        self.home_url = None
        self.bttoken = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        if self.modo_login == "kerberos":
            return "X-SAP-LogonToken" in self.session.headers
        elif self.modo_login == "ldap":
            if not self.home_url or not self.bttoken:
                return False
            r = self.session.post(
                urljoin(f"{self.home_url}/", "InfoView/listing/BOETimeoutPing"),
                headers={"X-Requested-With": "XMLHttpRequest"},
                data={
                    "resetCountdown": "false",
                    "logoff": "false",
                    "appKind": "InfoView",
                },
            )
            resposta = r.json()

            return not resposta.get("showExpiry", [True])[0]
        else:
            return False

    def login(self, usuario: str = None, senha: str = None) -> None:
        """Ver classe base ([Sistema][1]).

        Esse método realiza o login pelo protocolo Kerberos. Nesse protocolo, é
        utilizado o usuário que está logado na máquina onde o método é executado. Os
        parâmetros `usuario` e `senha` não são utilizados e estão presentes apenas por
        questões de compatibilidade.

        Recomendamos esse método para efetuar o login, porém, em algumas situações, não
        é possível utilizar o protocolo Kerberos (por exemplo, quando o login é feito de
        uma máquina que acessa a rede da Sefaz pelo VPN Checkpoint). Nesses casos
        utilize o método `login_ldap`.

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        if self.autenticado():
            self.logout()

        kerberos_auth = HTTPKerberosAuth(delegate=True)
        r = self.session.get(URL_LOGIN, auth=kerberos_auth)

        # CABEÇALHOS QUE DEVEM SER PERSISTIDOS
        self.session.headers["X-SAP-LogonToken"] = r.headers["X-SAP-LogonToken"]
        self.session.headers["X-SAP-PVL"] = "pt_BR"
        self.modo_login = "kerberos"

        if not self.autenticado():
            self.modo_login = None
            raise AuthenticationError()

    def login_ldap(self, usuario: str, senha: str) -> None:
        """Realiza o login pelo protocolo LDAP.

        Recomendamos a utilização desse método apenas quando não for possível utilizar o
        método `login`. Ao fazer o login pelo protocolo LDAP, alguns métodos dessa
        classe podem apresentar limitações. Leia a documentação do método para maiores
        detalhes.

        Args:
            usuario (str): Nome de usuário.
            senha (str): Senha do usuário.
        """
        if self.autenticado():
            self.logout()

        # primeiro get serve pra descobrir o endereço para fazer um post
        request = self.session.get(URL_BASE_LDAP + "/BI")
        soup = BeautifulSoup(request.text, "html.parser")
        login_url = urljoin(f"{URL_BASE_LDAP}/", soup.find("form").get("action"))
        self.home_url = login_url.rpartition("/")[0]

        # o post traz a próxima URL a ser feito post, com algumas variáveis
        request = self.session.post(login_url, data="")
        soup = BeautifulSoup(request.text, "html.parser")
        login_post_url = urljoin(f"{self.home_url}/", soup.find("form").get("action"))
        login_post_data = [
            (a.get("name"), a.get("value")) for a in soup.find("form").find_all("input")
        ]
        cms = soup.find("input", {"name": "vint_cms"}).get("value")

        # aqui é uma página de tentativa de single sign-on
        # se já der certo, encerra por aqui; se não, autentica manualmente
        try:
            self.session.post(login_post_url, data=login_post_data)
            return
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code != 401:
                raise ex
            redirect_url = re.search(r".*\(\s+\'(.*)\'", ex.response.text).group(1)

        # se não deu certo SSO, vai pra página de redirect de login
        request = self.session.get(urljoin(login_post_url, redirect_url))
        soup = BeautifulSoup(request.text, "html.parser")
        sun_faces_view = soup.find("input", {"name": "com.sun.faces.VIEW"}).get("value")

        # agora tentando fazer o login de fato
        # precisa vir com um bttoken, se não é porque não autenticou
        request = self.session.post(
            login_url,
            data={
                "_id0:logon:CMS": cms,
                "_id0:logon:SAP_SYSTEM": "",
                "_id0:logon:SAP_CLIENT": "",
                "_id0:logon:USERNAME": usuario,
                "_id0:logon:PASSWORD": senha,
                "_id0:logon:AUTH_TYPE": "secLDAP",
                "vint_success": "false",
                "com.sun.faces.VIEW": sun_faces_view,
                "_id0": "_id0",
            },
        )
        soup = BeautifulSoup(request.text, "html.parser")
        if soup.find("div", {"class": "logonError"}):
            raise ValueError(
                f"Falha na autenticação no Launchpad: "
                f"{soup.find('div', {'class': 'logonError'}).string}"
            )

        self.bttoken = soup.find("input", {"name": "bttoken"}).get("value")

        # vai pra página principal, pra não dar problema nas próximas chamadas
        self.session.post(
            urljoin(f"{self.home_url}/", "listing/main.do"),
            params={"service": "/common/appService.do", "appKind": "InfoView"},
            data={"bttoken": self.bttoken, "vint_success": "false"},
        )
        self.home_url = self.home_url.rpartition("/")[0]
        self.modo_login = "ldap"

        if not self.autenticado():
            self.modo_login = None
            raise AuthenticationError()

    def logout(self) -> None:
        """Realiza o logout no sistema."""
        if self.modo_login == "kerberos":
            self.session.post(URL_LOGOUT)

            try:
                del self.session.headers["X-SAP-LogonToken"]
                del self.session.headers["X-SAP-PVL"]
            except KeyError:
                pass

        elif self.modo_login == "ldap":
            if not self.home_url or not self.bttoken:
                return

            # descobre todas as páginas onde deve ser feito clean up da sessão
            try:
                request = self.session.get(
                    urljoin(f"{self.home_url}/", "InfoView/logon/logoff.do"),
                    params={"bttoken": self.bttoken},
                )
                soup = BeautifulSoup(request.text, "html.parser")
                for iframe in soup.find_all("iframe"):
                    self.session.get(urljoin(f"{request.url}/", iframe.get("src")))
                self.session.post(
                    urljoin(f"{self.home_url}/", "InfoView/logon/logoff.do"),
                    params={"bttoken": self.bttoken, "cleanedUp": True},
                )
            except Exception:
                pass

            self.home_url = None
            self.bttoken = None

        self.modo_login = None

    @preparar_metodo
    def obter_id_relatorio(
        self,
        nome: str,
        id_pasta: int = PASTA_SEFAZ_ID,
        nome_exato: bool = False,
        modo: str = "bfs",
    ) -> int:
        """Obtém o ID de um relatório.

        Caso haja mais de um relatório com o mesmo nome, será retornado o ID do primeiro
        encontrado, conforme o modo de busca (ver descrição do parâmetro `modo`).

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login`.

        Args:
            nome (str): Nome do relatório. Pode ser o nome exato ou uma parte do nome.
            id_pasta (int, optional): ID da pasta onde está o relatório. Não é
                necessário que o relatório esteja imediatamene abaixo da pasta informada
                nesse parâmetro, podendo estar em alguma subpasta. Valor padrão é o ID
                da pasta "Sefaz".
            nome_exato (bool, optional): Se `True`, o nome do relatório deve ter
                exatamente o valor em `nome`. Se `False`, basta que o nome do relatório
                contenha o valor em `nome`. Valor padrão é `False`.
            modo (str, optional): Modo de busca do relatório. Os modos suportados são:
            - `"bfs"` (valor padrão): utiliza o algorítimo
                [Breadth-First Search (BFS)][2].
            - `"dfs"`: utiliza o algorítimo [Depth-First Search (DFS)][3].

        Returns:
            O ID do relatório (se encontrado).

        Raises:
            ValueError: Erro indicando que o parâmetro `modo` recebeu um valor diferente
                de `"bfs"` e `"dfs"`.
            KeyError: Erro indicando que não foi encontrado o relatório.

        [2]: https://en.wikipedia.org/wiki/Breadth-first_search

        [3]: https://en.wikipedia.org/wiki/Depth-first_search
        """
        if self.modo_login != "kerberos":
            raise AuthenticationError(
                "É necessário se autenticar através do método login antes de usar esse "
                "método."
            )

        if modo.lower() == "bfs":
            pastas = SimpleQueue()
        elif modo.lower() == "dfs":
            pastas = LifoQueue()
        else:
            raise ValueError("modo deve ser 'bfs' ou 'dfs'.")

        pastas.put(id_pasta)

        while not pastas.empty():
            proximo_id = pastas.get()
            subpastas, relatorios = self.listar_itens_pasta(id_pasta=proximo_id)

            for rel in relatorios:
                if (nome_exato and rel["nome"] == nome) or (
                    not nome_exato and nome in rel["nome"]
                ):
                    return rel["id"]

            for p in subpastas:
                pastas.put(p["id"])

        raise KeyError(f"Nenhum relatório com o nome '{nome}' foi encontrado.")

    @preparar_metodo
    def baixar_relatorio(
        self, id_relatorio: int, caminho: str, campos: dict = None, id_aba: int = 0
    ) -> None:
        """Roda e baixa um relatório nos formatos HTML, XLSX, PDF, CSV ou TXT.

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login`.

        Args:
            id_relatorio (int): ID do relatório. Para descobrir o ID de um relatório,
                acesse o sistema pelo navegador, clique com o botão direito no relatório
                e clique em 'Propriedades' ou use o método `obter_id_relatorio`.
            caminho (str): Caminho completo onde deverá ser salvo o relatório, incluindo
                seu nome. Deve terminar com .html, .xlsx, .pdf, .csv ou .txt, conforme o
                formato desejado.
            campos (dict, optional): Dicionário com itens no formato `id: valor` onde
                `id` é um `int` com o ID do campo do relatório e `valor` é um `str` com
                o valor do campo. Parâmetro obrigatório se o relatório possui campos
                obrigatórios. Use o método `listar_campos_relatorio` para descobrir os
                campos do relatório e quais são obrigatórios. Observe que `valor` deve
                ser um `str` independentemente do tipo retornado para aquele campo pelo
                método `listar_campos_relatorio`.
            id_aba (int, optional): ID da aba. Obrigatório caso `caminho` termine com
                .csv ou .txt. Use o método `listar_abas_relatorio` para descobrir os IDs
                das abas de um relatório.

        Raises:
            ValueError: Erro indicando que extensão de arquivo inválida.
        """
        if self.modo_login != "kerberos":
            raise AuthenticationError(
                "É necessário se autenticar através do método login antes de usar esse "
                "método."
            )

        lista_campos = self.listar_campos_relatorio(id_relatorio=id_relatorio)
        campos_obrigatorios = [c for c in lista_campos if c["obrigatorio"]]

        for c_obrig in campos_obrigatorios:
            if c_obrig["id"] not in campos and str(c_obrig["id"]) not in campos:
                raise ValueError(
                    f"O campo de ID {c_obrig['id']} ({c_obrig['nome']}) é obrigatório"
                    " para esse relatório, porém não consta no parâmetro campos."
                )

        if id_aba > 0:
            lista_abas = self.listar_abas_relatorio(id_relatorio=id_relatorio)
            if id_aba not in [item["id"] for item in lista_abas]:
                raise ValueError(
                    f"A aba de ID {id_aba} não consta na lista de abas desse relatório."
                )

        self._rodar_relatorio(id_relatorio=id_relatorio, campos=campos)
        is_pdf = caminho.lower().endswith(".pdf")
        if caminho.lower().endswith(".html"):
            headers = {"Accept": "text/xml"}
        elif is_pdf:
            headers = {"Accept": "application/pdf"}
        elif caminho.lower().endswith(".xlsx"):
            headers = {
                "Accept": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            }
        elif caminho.lower().endswith(".csv"):
            if id_aba > 0:
                headers = {"Accept": "text/csv"}
            else:
                raise ValueError(
                    "caminho apenas pode terminar com .csv se id_aba não é None."
                )
        elif caminho.lower().endswith(".txt"):
            if id_aba > 0:
                headers = {"Accept": "text"}
            else:
                raise ValueError(
                    "caminho apenas pode terminar com .txt se id_aba não é None."
                )
        else:
            raise ValueError(
                "caminho deve terminar com .html, .xlsx, .pdf, .csv ou .txt"
            )

        url = URL_API + "/documents/" + str(id_relatorio)
        if id_aba > 0:
            url += "/reports/" + str(id_aba)
            if is_pdf:
                url += "/pages"
        url += "?mode=normal&optimized=true"
        r = self.session.get(url, headers=headers)
        with open(caminho, "wb") as f:
            f.write(r.content)

    @preparar_metodo
    def baixar_relatorio_ldap(
        self,
        id_relatorio: int,
        caminho: str,
        campos: Dict[int, str] = None,
        relatorios: list[str] = None,
        dados: list[str] = None,
        csv_text_qualifier: str = '"',
        csv_column_separator: str = ";",
        csv_charset: str = "UTF-8",
        timeout_relatorio: int = 30,
    ) -> None:
        """Roda e baixa um relatório nos formatos HTML, XLSX, PDF, CSV ou TXT.

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login_ldap`.

        Args:
            id_relatorio (int): ID do relatório. Para descobrir o ID de um relatório,
                acesse o sistema pelo navegador, clique com o botão direito no relatório
                e clique em 'Propriedades' ou use o método `obter_id_relatorio`.
            caminho (str): caminho completo onde deverá ser salvo o relatório, incluindo
                seu nome. Deve terminar com .xlsx, .pdf ou .csv, conforme o
                formato desejado.
            campos (dict[int: str], optional): dicionário com itens no formato
                `id: valor` onde `id` é um `int` com o ID do campo do relatório e
                `valor` é um `str` com o valor do campo. Parâmetro obrigatório se o
                relatório possui campos obrigatórios. Use o método
                `listar_campos_relatorio` para descobrir os campos do relatório e quais
                são obrigatórios. Observe que `valor` deve ser um `str`
                independentemente do tipo retornado para aquele campo pelo método
                `listar_campos_relatorio`.
            relatorios (list[str], optional): lista com os nomes das abas do relatorio
                que se deseja que estejam presentes no arquivo baixado. Não pode ser
                usado caso `caminho` termine com .csv. Caso não seja informado, todas as
                abas do relatório serão incluídas no arquivo. Use o método
                `listar_abas_relatorio` para descobrir os nomes das abas de um
                relatório, ou verifique os nomes no menu Exportar, opção "Relatórios" do
                relatório no LaunchPad Web.
            dados (list[str], optional): lista com os nomes das fontes de dados do
                relatório que se deseja que estejam presentes no arquivo baixado. Apenas
                pode ser usado caso `caminho` termine com .csv. Caso não seja informado,
                todas as fontes de dados do relatório serão incluídas no arquivo.
                Para descobrir os nomes das fontes de dados de um relatório, verifique
                os nomes no menu Exportar, opção "Dados" do relatório no LaunchPad Web.
            csv_text_qualifier (str, optional): caractere a ser utilizado como
                qualificador de texto, caso `caminho` termine com .csv. Caso não seja
                informado, serão usadas aspas duplas ("). Opções válidas de
                qualificadores: '"' (aspa dupla), "'" (aspa simples) e '' (string vazia,
                indica para não utilizar qualificador).
            csv_column_separator (str, optional): caractere a ser utilizado como
                delimitador de colunas, caso `caminho` termine com .csv. Caso não seja
                informado, será usado ponto-e-vírgula (;). Opções válidas de
                delimitador: ',' (vírgula), ';' (ponto-e-vírgula) e 'Tab' (tabulação).
            csv_charset (str, optional): codificação de caracteres a ser utilizada para
                gerar o arquivo, caso `caminho` termine com .csv. Caso não seja
                informado, será usado UTF-8. Opções válidas (para simplificar): 'UTF-8',
                'CP1252' (Windows) e 'ISO-8859-1' (Latin).
            timeout_relatorio (int, optional): tempo máximo de espera pelo processamento
                do arquivo pelo servidor, em minutos. Caso não seja informado, será
                aguardado 30 minutos. Valores não positivos ou None farão com que seja
                aguardado resultado indefinidamente.

        Raises:
            ValueError: Erro indicando que extensão de arquivo inválida.
            Exception: Erro ocorrido no servidor ao baixar o arquivo do relatório.
        """
        if self.modo_login != "ldap":
            raise AuthenticationError(
                "É necessário se autenticar através do método login_ldap antes de usar "
                "esse método."
            )

        # valida os argumentos que não dependem de servidor para avaliar
        if csv_text_qualifier not in ['"', "'", ""]:
            raise ValueError(f"Qualificador de texto {csv_text_qualifier} inválido.")
        if csv_column_separator not in [",", ";", "Tab"]:
            raise ValueError(f"Delimitador de coluna {csv_column_separator} inválido.")
        if csv_charset not in ["UTF-8", "CP1252", "ISO-8859-1"]:
            raise ValueError(f"Charset {csv_charset} inválido.")
        timeout = (
            timeout_relatorio * 60
            if timeout_relatorio and timeout_relatorio > 0
            else None
        )

        sufixo = Path(caminho).suffix.lower()
        if sufixo == ".pdf":
            link_report_process = "downloadPDForXLS"
            link_download = "DownloadPDForXLS"
            view_type = "P"
            save_option_name = "saveReport"
        elif sufixo == ".xlsx":
            link_report_process = "downloadPDForXLS"
            link_download = "DownloadPDForXLS"
            view_type = "XO"
            save_option_name = "saveReport"
        elif sufixo == ".csv":
            link_report_process = "processCSVOptions"
            link_download = "DownloadCSV"
            view_type = "COp"
            save_option_name = "saveData"
        else:
            raise ValueError(
                "Sufixo do caminho inválido! Apenas aceita pdf, xlsx e csv!"
            )

        # aqui é feita uma correção nos ids dos campos, pois quando se usa a interface
        # HTTP, os índices iniciam em 1 (na API, começam em 0)
        campos = {k + 1: v for k, v in campos.items()} if campos else {}

        # busca existência do relatório solicitado e ganha um token
        r = self.session.get(
            urljoin(f"{self.home_url}/", "AnalyticalReporting/WebiView.do"),
            params={
                "defaultView": "true",
                "cafWebSesInit": "true",
                "bttoken": self.bttoken,
                "opendocTarget": "infoviewOpenDocFrame",
                "appKind": "InfoView",
                "service": "/InfoView/common/appService.do",
                "loc": "pt",
                "pvl": "pt_BR",
                "ctx": "standalone",
                "actId": "4687",
                "objIds": id_relatorio,
                "pref": "maxOpageU=50;maxOpageUt=200;maxOpageC=10;tz=America/Sao_Paulo;"
                "mUnit=inch;showFilters=true;smtpFrom=true;"
                "promptForUnsavedData=true;",
                "tidtime": "",
            },
        )
        if "CSRF_TOKEN_COOKIE" not in r.text:
            raise ValueError(f"ID do relatório {id_relatorio} inválido.")
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_token = soup.find("input", {"name": "CSRF_TOKEN_COOKIE"}).get("value")

        # pega dados do relatório (abas, dados, nome, id)e ganha mais um token para
        # prosseguir
        r = self.session.get(
            urljoin(
                f"{self.home_url}/",
                "AnalyticalReporting/webiDHTML/viewer/viewDocument.jsp",
            ),
            params={
                "CSRF_TOKEN_COOKIE": csrf_token,
                "id": id_relatorio,
                "defaultView": "true",
                "cafWebSesInit": "true",
                "bttoken": self.bttoken,
                "opendocTarget": "infoviewOpenDocFrame",
                "appKind": "InfoView",
                "service": "/InfoView/common/appService.do",
                "loc": "pt",
                "pvl": "pt_BR",
                "ctx": "standalone",
                "actId": "4687",
                "objIds": id_relatorio,
                "pref": (
                    "maxOpageU=50;"
                    "maxOpageUt=200;"
                    "maxOpageC=10;"
                    "tz=America/Sao_Paulo;"
                    "mUnit=inch;"
                    "showFilters=true;"
                    "smtpFrom=true;"
                    "promptForUnsavedData=true;"
                ),
                "tidtime": "",
                "kind": "Webi",
                "iventrystore": "widtoken",
                "ViewType": "H",
                "entSession": "InfoViewCE_ENTERPRISESESSION",
                "lang": "pt",
            },
        )
        datasource_properties = json.loads(
            re.search(r"DS\s+=\s+({.*})</script>", r.text).group(1)
        )
        webservice_properties = json.loads(
            re.search(r"WS\s+=\s+({.*})</script>", r.text).group(1)
        )
        str_entry = datasource_properties["strEntry"]
        internal_report_id = datasource_properties["iReportID"]
        str_docname = datasource_properties["strDocName"]
        iviewer = webservice_properties["iViewerID"]

        # validando lista de abas solicitada
        id_abas = []
        abas_dict = {
            rep["name"]: rep["reportID"] for rep in datasource_properties["arrReports"]
        }
        if relatorios:
            for aba in relatorios:
                if aba not in abas_dict:
                    raise ValueError(
                        f"Aba solicitada ({aba}) não está presente na lista de abas do "
                        f"relatório: {list(abas_dict)}"
                    )
                else:
                    id_abas.append(abas_dict[aba])

        # validando lista de dados a serem baixados quando CSV
        id_dados = []
        dados_dict = {
            datasource["name"]: datasource["id"]
            for datasource in datasource_properties["arrDPs"]
        }
        if dados:
            for ds in dados:
                if ds not in dados_dict:
                    raise ValueError(
                        f"Dado solicitado ({ds}) não está presente na lista de dados do"
                        f" relatório: {list(dados_dict)}"
                    )
                else:
                    id_dados.append(dados_dict[ds])

        self.session.get(
            urljoin(
                f"{self.home_url}/", "AnalyticalReporting/webiDHTML/viewer/report.jsp"
            ),
            params={
                "iViewerID": iviewer,
                "sEntry": str_entry,
                "iReport": list(abas_dict.values()).index(internal_report_id),
                "iReportID": internal_report_id,
                "iPage": "1",
                "sPageMode": "QuickDisplay",
                "sReportMode": datasource_properties["strReportMode"],
                "zoom": "100",
                "isInteractive": "false",
                "isStructure": "false",
                "appKind": "InfoView",
                "sBid": "",
            },
        )

        # descobre quais são os inputs do relatório
        r = self.session.post(
            urljoin(
                f"{self.home_url}/",
                "AnalyticalReporting/webiDHTML/viewer/getPrompts.jsp",
            ),
            params={
                "iViewerID": iviewer,
                "sEntry": str_entry,
                "iReport": list(abas_dict.values()).index(internal_report_id),
                "iReportID": internal_report_id,
                "iPage": "1",
                "sPageMode": "QuickDisplay",
                "sReportMode": datasource_properties["strReportMode"],
                "zoom": "100",
                "isInteractive": "false",
                "isStructure": "false",
                "appKind": "InfoView",
            },
            data={
                "keyDate": "",
                "sEmptyLab": "[EMPTY_VALUE]",
                "CSRF_TOKEN_COOKIE": csrf_token,
                "bttoken": self.bttoken,
            },
        )
        existem_prompts = re.search(r"prompts=(\[.+])", r.text)
        prompts = json.loads(existem_prompts.group(1)) if existem_prompts else []
        campos_obrigatorios = [c for c in prompts if not c["isOptional"]]
        for c_obrig in campos_obrigatorios:
            if campos is None or int(c_obrig["key"]) not in campos:
                raise ValueError(
                    f"O campo de ID {int(c_obrig['key']) - 1} - '{c_obrig['name']}' é "
                    "obrigatório para esse relatório, porém não consta no parâmetro "
                    "campos."
                )

        post_data_spv = []
        for p in prompts:
            dic_prompt = {
                "id": p["id"],
                "index": p["groupIndex"],
                "key": p["key"],
                "dataType": p["dataType"],
            }
            # segrega valores passados pelo usuário, separados por ;
            dic_values = [
                {"caption": valor if int(p["key"]) in campos else "", "key": ""}
                for valor in campos[int(p["key"])].split(";")
            ]
            dic_prompt["values"] = dic_values
            dic_prompt.update({"deps": [], "dataproviderInfo": p["dataproviderInfo"]})
            # quando o tipo de dado é data, tem que adicionar uns validadores mock
            if p["dataType"] == 3:
                for valor in dic_values:
                    try:
                        datetime.strptime(valor["caption"], "%d/%m/%Y")
                    except ValueError:
                        raise ValueError(
                            f"O campo de ID {p['key']} ({p['name']}) é do tipo data,"
                            f" e o valor passado é inválido: {valor['caption']}"
                        )
                dic_prompt["isDateValid"] = True
                dic_prompt["isDateChecked"] = True
                dic_prompt["checkDate"] = True
            post_data_spv.append(dic_prompt)

        # aqui, de fato, solicita ao servidor a execução do relatório com os argumentos
        # aguarda a execução do relatório conforme timeout definido
        # a thread fica travada aqui enquanto não termina a execução do relatório
        post_params = {
            "iViewerID": iviewer,
            "sEntry": str_entry,
            "iReport": list(abas_dict.values()).index(internal_report_id),
            "iReportID": internal_report_id,
            "iPage": "1",
            "sPageMode": "QuickDisplay",
            "sReportMode": datasource_properties["strReportMode"],
            "zoom": "100",
            "isInteractive": "false",
            "isStructure": "false",
            "appKind": "InfoView",
            "setKeyDateFirst": "true",
        }
        post_data = {
            "sPV": json.dumps(post_data_spv, ensure_ascii=False),
            "keyDate": "",
            "sEmptyLab": "[EMPTY_VALUE]",
            "CSRF_TOKEN_COOKIE": csrf_token,
            "bttoken": self.bttoken,
        }
        print(f"Params: {post_params}")
        print(f"Post: {post_data}")
        r = self.session.post(
            urljoin(
                f"{self.home_url}/",
                "AnalyticalReporting/webiDHTML/viewer/processPrompts.jsp",
            ),
            params=post_params,
            data=post_data,
            timeout=timeout,
        )

        # se chegou aqui sem erro, é porque rodou. Atualiza o token str_entry
        if "Error" in r.text:
            raise Exception(
                "Ocorreu uma falha na execução do relatório. Verifique os campos."
            )
        soup = BeautifulSoup(r.text, "html.parser")
        str_entry = re.search(r"&sEntry=(\w+)&", str(soup.find("script").string)).group(
            1
        )

        # prepara para fazer o download
        r = self.session.get(
            urljoin(
                f"{self.home_url}/", "AnalyticalReporting/webiDHTML/viewer/report.jsp"
            ),
            params={
                "iViewerID": iviewer,
                "sEntry": str_entry,
                "iReport": list(abas_dict.values()).index(internal_report_id),
                "iReportID": internal_report_id,
                "iPage": "1",
                "sPageMode": "QuickDisplay",
                "sReportMode": datasource_properties["strReportMode"],
                "zoom": "100",
                "isInteractive": "false",
                "isStructure": "false",
                "appKind": "InfoView",
                "nbPage": "NaN",
                "sEmptyLab": "[EMPTY_VALUE]",
            },
        )
        self.session.get(
            urljoin(
                f"{self.home_url}/",
                "AnalyticalReporting/webiDHTML/viewer/language/"
                "pt/html/exportDialog.html",
            ),
            params={"saveReport": "Y"},
        )

        # link varia se for CSV ou outra coisa, assim como parâmetros e dados do POST
        post_params = {
            "iViewerID": iviewer,
            "sEntry": str_entry,
            "iReport": list(abas_dict.values()).index(internal_report_id),
            "iReportID": internal_report_id,
            "sPageMode": "Page",
            "sReportMode": datasource_properties["strReportMode"],
            "iPage": "1",
            "zoom": "100",
            "isInteractive": "false",
            "isStructure": "false",
            "appKind": "InfoView",
            "doctype": "wid",
            "viewType": view_type,
        }
        # tenho que alterar os parametros de dict para lista de tuplas,
        # pois há situações em que há duplicidade de parâmetros
        post_params = list(post_params.items())
        post_data = {
            "Export": "on",
            "CSRF_TOKEN_COOKIE": csrf_token,
            "bttoken": self.bttoken,
        }

        # faz download conforme a terminação do arquivo e abas desejadas
        if not id_abas or len(abas_dict) == len(id_abas):
            post_data["check_SelectAllReport"] = "on"
            if sufixo != ".csv":
                post_params.append((save_option_name, "N"))
        else:
            if sufixo != ".csv":
                post_params.append((save_option_name, "Y"))
            for id_aba in id_abas:
                post_params.append(("repotID", id_aba))
        for id_aba in id_abas if id_abas else abas_dict.values():
            post_data[f"check_{id_aba}"] = "on"

        if sufixo == ".csv":
            post_params.append((save_option_name, "Y"))
            post_data["cbCharDelimiter"] = csv_text_qualifier
            post_data["cbColSep"] = csv_column_separator
            post_data["cbCharset"] = csv_charset
            for id_dado in id_dados if id_dados else dados_dict.values():
                post_params.append(("dpID", id_dado))
                post_data[f"check_{id_dado}"] = "on"
        else:
            post_params.append(("dpi", "Default"))
            post_data["check_SelectAllData"] = "on"
            for _, id_ds in dados_dict.items():
                post_data[f"check_{id_ds}"] = "on"
            post_data["fileTypeList"] = sufixo.upper()[1:]
            post_data["txtCharset"] = ""
            if sufixo == ".xlsx":
                post_data["priotize"] = "on"

        # manda gerar arquivo no servidor
        print(f"Params: {post_params}")
        print(f"Post: {post_data}")
        r = self.session.post(
            urljoin(
                f"{self.home_url}/",
                f"AnalyticalReporting/webiDHTML/viewer/{link_report_process}.jsp",
            ),
            params=post_params,
            data=post_data,
            timeout=timeout,
        )
        # finalmente, baixa o arquivo!
        download_filename = re.sub(r'[\s\\/*?"<>|%#\[\]]', "_", str_docname)
        r = self.session.get(
            urljoin(
                f"{self.home_url}/",
                f"AnalyticalReporting/webiDHTML/"
                f"{link_download}/{str_entry}/{download_filename}{sufixo}",
            ),
            timeout=timeout,
        )
        if "html" in r.headers["Content-Type"]:
            raise Exception("Ocorreu erro no download do arquivo, tente novamente")
        with open(caminho, mode="wb") as f:
            f.write(r.content)

    @preparar_metodo
    def listar_campos_relatorio(self, id_relatorio: int) -> list:
        """Lista campos de um relatório.

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login`.

        Args:
            id_relatorio (int): ID do relatório. Para descobrir o ID de um relatório,
                acesse o sistema pelo navegador, clique com o botão direito no relatório
                e clique em 'Propriedades' ou use o método `obter_id_relatorio`.

        Returns:
            Uma lista de campos, cada um representado por um `dict`.
        """
        if self.modo_login != "kerberos":
            raise AuthenticationError(
                "É necessário se autenticar através do método login antes de usar esse "
                "método."
            )

        r = self.session.get(
            URL_API
            + "/documents/"
            + str(id_relatorio)
            + "/parameters?formattedValues=true"
        )
        soup = BeautifulSoup(r.text, "html.parser")
        parameters = soup.find_all("parameter")
        campos = [
            {
                "id": int(p.id.text),
                "nome": p.find("name").text,
                "tipo": p.answer["type"],
                "obrigatorio": True,
                "opcoes": [v.text for v in p.find_all("value")],
            }
            if p["optional"] == "false" and len(p.find_all("value")) > 0
            else {
                "id": int(p.id.text),
                "nome": p.find("name").text,
                "tipo": p.answer["type"],
                "obrigatorio": True,
                "opcoes": None,
            }
            if p["optional"] == "false"
            else {
                "id": int(p.id.text),
                "nome": p.find("name").text,
                "tipo": p.answer["type"],
                "obrigatorio": False,
                "opcoes": [v.text for v in p.find_all("value")],
            }
            if len(p.find_all("value")) > 0
            else {
                "id": int(p.id.text),
                "nome": p.find("name").text,
                "tipo": p.answer["type"],
                "obrigatorio": False,
                "opcoes": None,
            }
            for p in parameters
        ]

        return campos

    @preparar_metodo
    def listar_abas_relatorio(self, id_relatorio: int) -> list:
        """Lista abas de um relatório.

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login`.

        Args:
            id_relatorio (int): ID do relatório. Para descobrir o ID de um relatório,
                acesse o sistema pelo navegador, clique com o botão direito no relatório
                e clique em 'Propriedades' ou use o método `obter_id_relatorio`.

        Returns:
            Uma lista de campos, cada um representado por um `dict`.
        """
        if self.modo_login != "kerberos":
            raise AuthenticationError(
                "É necessário se autenticar através do método login antes de usar esse "
                "método."
            )

        r = self.session.get(
            URL_API
            + "/documents/"
            + str(id_relatorio)
            + "/reports?formattedValues=true"
        )
        soup = BeautifulSoup(r.text, "lxml-xml")
        reports = soup.find_all("report")
        abas = [{"id": int(p.id.text), "nome": p.find("name").text} for p in reports]
        return abas

    @preparar_metodo
    def listar_itens_pasta(self, id_pasta: int = PASTA_SEFAZ_ID) -> Tuple[list, list]:
        """Lista subpastas e relatórios presentes em uma pasta.

        Esse método funciona apenas quando o login no sistema foi feito pelo método
        `login`.

        Args:
            id_pasta (int, optional): ID da pasta em que os itens devem ser listados.
                Valor padrão é o ID da pasta "Sefaz".

        Returns:
            uma tupla `(pastas, relatorios)`, onde `pastas` é uma lista de subpastas e
            `relatorios` é uma lista de relatórios. Cada item dessas listas é
            representado por um `dict`.
        """
        if self.modo_login != "kerberos":
            raise AuthenticationError(
                "É necessário se autenticar através do método login antes de usar esse "
                "método."
            )

        data = (
            "<search>"
            + "<folder><folderId>"
            + str(id_pasta)
            + "</folderId></folder>"
            + "<document><folderId>"
            + str(id_pasta)
            + "</folderId></document>"
            + "</search>"
        )
        r = self.session.post(URL_API + "/searches", data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        pastas = [
            {"id": int(pasta.id.text), "nome": pasta.find("name").text}
            for pasta in soup.find_all("folder")
        ]
        relatorios = [
            {"id": int(rel.id.text), "nome": rel.find("name").text}
            for rel in soup.find_all("document")
        ]

        return pastas, relatorios

    def _rodar_relatorio(self, id_relatorio: int, campos: dict = None):
        data = LaunchPad._montar_payload_relatorio(campos=campos) if campos else None
        self.session.put(
            URL_API
            + "/documents/"
            + str(id_relatorio)
            + "/parameters?formattedValues=true",
            data=data,
        )

    @staticmethod
    def _montar_payload_relatorio(campos: dict):
        root = ET.Element("parameters")
        for campo_id, campo_valor in campos.items():
            param = ET.SubElement(root, "parameter")
            id_tag = ET.SubElement(param, "id")
            id_tag.text = str(campo_id)

            ans = ET.SubElement(param, "answer")
            values = ET.SubElement(ans, "values")
            for subvalor in campo_valor.split(";"):
                value = ET.SubElement(values, "value")
                value.text = subvalor

        xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=False)
        return xml_string
