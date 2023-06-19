"""Módulo com definições do sistema Ecredac."""

import os
import shutil

import win32com.client
from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import extrair_validadores_aspnet
from pepe.utils.texto import (
    formatar_cnpj,
    formatar_data,
    formatar_ie,
    formatar_mes_referencia,
)

URL_BASE = "https://www.fazenda.sp.gov.br/CreditoAcumulado"
URL_LOGIN = URL_BASE + "/Web/paginas/login/login.aspx"
URL_CONSULTA_OPC_ARQ_SIMP = (
    URL_BASE
    + "/Web/paginas/arquivoDigital/apuracao/consultaOpcaoArquivoSimplificado.aspx"
)
URL_CONSULTA_ARQ_SIMP = (
    URL_BASE
    + "/Web/paginas/arquivoDigital/arquivoSimplificado/consultaArquivoSimplificado.aspx"
)
URL_CONSULTA_ARQ_CUSTO = (
    URL_BASE + "/Web/paginas/arquivoDigital/arquivoCusto/consultaArquivoCusto.aspx"
)
URL_CONSULTA_VER_SUM_ARQ = (
    URL_BASE
    + "/Web/paginas/arquivoDigital/verificacaoSumaria/"
    + "consultaVerificacaoSumariaPorArquivo.aspx"
)
URL_CONSULTA_VER_SUM_REQ = (
    URL_BASE
    + "/Web/paginas/arquivoDigital/verificacaoSumaria/"
    + "consultaVerificacaoSumariaPorRequisicao.aspx"
)


PERFIL_FAZENDARIO_LOGIN = "1"
PERFIL_FAZENDARIO_LOGIN_CERT = "0"

SIMPLIFICADO_FINALIDADE = {
    "": "00",
    "01 - REMESSA REGULAR DE ARQUIVO": "01",
    "03 - REMESSA DE ARQUIVO PARA SUBSTITUIÇÃO": "03",
    "04 - REMESSA DE ARQUIVO COM INFORMAÇÕES COMPLEMENTARES": "04",
}

CUSTO_FINALIDADE = {
    "": "-01",
    "00 - Remessa regular de arquivo": "00",
    "01 - Remessa de arquivo para registrar a continuidade do estoque": "01",
    "02 - Remessa de arquivo requerido por intimação específica": "02",
    "03 - Remessa de arquivo para substituição": "03",
    "04 - Remessa de arquivo com informações complementares": "04",
}

FICHAS_CUSTO = {
    "5C_PPAL": "tipoFicha=71",
    "5C_POUT": "tipoFicha=72",
    "5C_PEXT": "tipoFicha=73",
    "5D": "tipoFicha=8",
    "5H": "tipoFicha=9",
    "RESUMO": "tipoFicha=74",
    "6A_IEST7": "tipoFicha=11",
    "6A_IEST12": "tipoFicha=12",
    "6A_INT7": "tipoFicha=13",
    "6A_INT": "tipoFicha=14",
    "6A_OUTRAS": "tipoFicha=15",
    "6B_DESTPAL": "tipoFicha=21",
    "6B_DESTSUL": "tipoFicha=22",
    "6B_DESTOUT": "tipoFicha=23",
    "6C": "tipoFicha=3",
    "6D": "tipoFicha=4",
    "6E_DIF": "tipoFicha=51",
    "6E_ISCRED": "tipoFicha=52",
    "6E_ST": "tipoFicha=53",
    "6E_OUT": "tipoFicha=54",
    "6F_DESTPAL": "tipoFicha=61",
    "6F_DESTSUL": "tipoFicha=62",
    "6F_DESTOUT": "tipoFicha=63",
    "6F_DESTEXT": "tipoFicha=64",
    "6H": "tipoFicha=101",
}

FICHAS_SIMPLIFICADO = {
    "5C": "tipoFicha=7",
    "5D": "tipoFicha=8",
    "5H": "tipoFicha=9",
    "RESUMO": "RelatorioGeral",
    "6A": "tipoFicha=1",
    "6B": "tipoFicha=2",
    "6C": "tipoFicha=3",
    "6D": "tipoFicha=4",
    "6E": "tipoFicha=5",
    "6F": "tipoFicha=6",
}

FICHAS_SUMARIA = {
    "SISCOMEX": "codigoAplicacao=4",
    "SUFRAMA": "codigoAplicacao=3",
    "CADESP": "codigoAplicacao=2",
    "NFE": "codigoAplicacao=6",
}


class Ecredac(Sistema):
    """Representa o sistema [e-CredAc](https://www.fazenda.sp.gov.br/CreditoAcumulado).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe Ecredac.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/99.0.4844.83 Safari/537.36",
            }
        )

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(
            URL_BASE + "/Web/paginas/mensagens/mensagensPendentes.aspx"
        )

        return "ctl00_linkButtonEncerrarSessao" in r.text

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )
        data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ConteudoPagina$Login1$lstPerfil": PERFIL_FAZENDARIO_LOGIN,
            "ctl00$ConteudoPagina$Login1$UserName": usuario,
            "ctl00$ConteudoPagina$Login1$Password": senha,
            "ctl00$ConteudoPagina$Login1$btnLogin": "Acessar",
        }
        r = self.session.post(URL_LOGIN, data=data)

        if not self.autenticado():
            raise AuthenticationError()

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # CLIQUE NO CERTIFICADO (POST)
        data = {
            "ctl00_ConteudoPagina_ScriptManager1_HiddenField": "",
            "__EVENTTARGET": "ctl00$ConteudoPagina$LinkButtonLoginCert",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ConteudoPagina$checkBoxFazendario": "on",
            "ctl00$ConteudoPagina$Login1$lstPerfil": PERFIL_FAZENDARIO_LOGIN_CERT,
            "ctl00$ConteudoPagina$Login1$PerfilReqE_ClientState": "",
            "ctl00$ConteudoPagina$Login1$UserName": "",
            "ctl00$ConteudoPagina$Login1$UserNameReqE_ClientState": "",
            "ctl00$ConteudoPagina$Login1$Password": "",
            "ctl00$ConteudoPagina$Login1$PasswordReqE_ClientState": "",
        }

        r = self.session.post(URL_LOGIN, data=data)

        cookies = ""
        for cookie in self.session.cookies.get_dict().keys():
            cookies += cookie + "=" + self.session.cookies.get_dict()[cookie] + "; "

        winhttp = win32com.client.Dispatch("WinHTTP.WinHTTPRequest.5.1")
        winhttp.Open(
            "GET", URL_BASE + "/Web/paginas/login/certificate/loginCertificate.aspx"
        )
        winhttp.SetOption(6, False)  # BLOQUEIO REDIRECIONAMENTOS PRA PEGAR COOKIE
        winhttp.SetClientCertificate(nome_cert)
        winhttp.SetRequestHeader("Cookie", cookies)
        winhttp.Send()

        response = winhttp.GetAllResponseHeaders().split("\n")
        cookies = {}
        for resp in response:
            if "Set-Cookie" in resp:
                cookie = resp.split("Set-Cookie: ")[1].split(";")[0]
                if cookie.split("=")[1] != "":
                    cookies[cookie.split("=")[0]] = cookie.split("=")[1]

        self.session.cookies.update(cookies)
        r = self.session.get(
            URL_BASE + "/Web/paginas/mensagens/mensagensPendentes.aspx"
        )

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def consultar_apuracao_simplificada(self, cnpj: str = None, ie: str = None) -> dict:
        """Obtém dados da apuração simplificada de um estabelecimento.

        Args:
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`.

        Returns:
            Um dicionário com os dados do estabelecimento e sua adesão.
        """
        # TRABALHANDO AS VARIÁVEIS
        if bool(ie) != bool(cnpj):  # XOR
            if ie:
                id_empresa = formatar_ie(ie)[1]
            else:
                id_empresa = formatar_cnpj(cnpj)[1]
        else:
            raise ValueError("Informe ie ou cnpj (mas não ambos).")

        # ABRINDO TELA DE CONSULTA
        r = self.session.get(URL_CONSULTA_OPC_ARQ_SIMP)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # Se passado IE, necessário fazer um post antes do post final
        if ie:
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$updatePanelPrincipal|"
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ),
                "__EVENTTARGET": (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ),
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ): "1",
                "VersaoSite": "MAIN 1.00",
                "__ASYNCPOST": "true",
            }
            r = self.session.post(URL_CONSULTA_OPC_ARQ_SIMP, data=data)
            viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
                r.text
            )

        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$updatePanelPrincipal|"
                "ctl00$ConteudoPagina$buttonConsultar"
            ),
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "VersaoSite": "MAIN 1.00",
            "__ASYNCPOST": "true",
            "ctl00$ConteudoPagina$buttonConsultar": "Consultar",
        }
        ctl_selec_estab = (
            "ctl00$"
            "ConteudoPagina$"
            "controlFiltroConsulta$"
            "controlSelecaoEstabelecimento$"
        )

        if cnpj:
            data |= {
                ctl_selec_estab + "textBoxFiltroCNPJ": id_empresa,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "0",
            }
        else:  # ie
            data |= {
                ctl_selec_estab + "textBoxFiltroIE": id_empresa,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "1",
            }

        r = self.session.post(URL_CONSULTA_OPC_ARQ_SIMP, data=data)

        return Ecredac._scrape_consulta_apuracao_simplificada(html=r.text)

    @preparar_metodo
    def listar_arquivos_simplificados_transmitidos(
        self,
        cnpj: str = "",
        ie: str = "",
        data_transmissao_inicial: str = "",
        data_transmissao_final: str = "",
        referencia_inicial: str = "",
        referencia_final: str = "",
        protocolo: str = "",
        finalidade: str = "",
    ):
        """Lista arquivos simplificados conforme os critérios de pesquisa passados.

        Args:
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
                Obrigatório se não for passado valor em `protocolo` e `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`. Obrigatório se não for passado valor em
                `protocolo` e `cnpj`.
            data_transmissao_inicial (str, optional): Data de transmissão inicial, no
                formato DD/MM/AAAA.
            data_transmissao_final (str, optional): Data de transmissão final, no
                formato DD/MM/AAAA.
            referencia_inicial (str, optional): Mês de referência inicial, no formato
                MM/AAAA.
            referencia_final (str, optional): Mês de referência final, no formato
                MM/AAAA.
            protocolo (str, optional): Protocolo de arquivo simplificado, no formato
                XXXXX/AAAA. Obrigatório se não for passado valor em `cnpj` ou `ie`.
            finalidade (str, optional): Finalidade do arquivo. Deve ser uma da chaves do
                dicionário `SIMPLIFICADO_FINALIDADE`.

        Returns:
            Uma lista de tuplas com os dados dos arquivos na seguinte ordem: Protocolo,
            CNPJ, Referência, Finalidade, Data de Transmissão e Situação.
        """
        # TRABALHANDO AS VARIÁVEIS
        if cnpj:
            if ie:
                raise ValueError("Informe apenas ie ou cnpj (mas não ambos).")

            cnpj = formatar_cnpj(cnpj)[1]
        elif ie:
            ie = formatar_ie(ie)[1]
        elif not protocolo:
            raise TypeError(
                "Se a pesquisa não for feita por número de protocolo, a ie ou cnpj "
                "devem ser informados."
            )

        if data_transmissao_inicial:
            data_transmissao_inicial = formatar_data(
                data_transmissao_inicial, "%d/%m/%Y"
            )

        if data_transmissao_final:
            if not data_transmissao_inicial:
                raise Exception(
                    "Se informado data_transmissao_final, deve ser informado também "
                    "data_transmissao_inicial."
                )

            data_transmissao_final = formatar_data(data_transmissao_final, "%d/%m/%Y")

        if referencia_inicial:
            referencia_inicial = formatar_mes_referencia(
                ref=referencia_inicial, formato_saida="mm/aaaa"
            )

        if referencia_final:
            referencia_final = formatar_mes_referencia(
                ref=referencia_final, formato_saida="mm/aaaa"
            )

        if protocolo:
            Ecredac._validar_protocolo(protocolo)

        return self._listar_arquivos(
            tipo="simplificado",
            cnpj=cnpj,
            ie=ie,
            data_transmissao_inicial=data_transmissao_inicial,
            data_transmissao_final=data_transmissao_final,
            referencia_inicial=referencia_inicial,
            referencia_final=referencia_final,
            protocolo=protocolo,
            finalidade=finalidade,
        )

    @preparar_metodo
    def obter_ficha_arquivo_simplificado(protocolo: str, ficha: str) -> dict:
        """Método não implementado."""
        raise NotImplementedError()
        """
        Ecredac._verificar_protocolo(protocolo)

        ficha = ficha.upper()
        if ficha not in FICHAS_SIMPLIFICADO:
            raise ValueError(
                "Ficha inválida.\n"
                f"Valores aceitos: {list(FICHAS_SIMPLIFICADO)}\n"
                f"Valor passado: {ficha}"
            )

        pagina = self._detalhar_ficha_arquivo_simplificado(
            protocolo=protocolo, ficha=ficha
        )

        return Ecredac._scrape_ficha_arquivo_simplificado(html=pagina)
        """

    @preparar_metodo
    def baixar_txt_arquivo_simplificado(self, protocolo: str, caminho: str) -> None:
        """Baixa um arquivo de texto com as informações de um arquivo simplificado.

        Args:
            protocolo (str): Protocolo do arquivo, no formato XXXXX/AAAA.
            caminho (str): Caminho completo onde deverá ser salvo o arquivo, incluindo
                seu nome.
        """
        Ecredac._validar_protocolo(protocolo)
        pagina_detalhe = self._detalhar_arquivo(
            tipo="simplificado", protocolo=protocolo
        )

        if (
            "ctl00_ConteudoPagina_controlDetalheTransmissao_buttonDownload"
            not in pagina_detalhe
        ):
            raise Exception(
                "Não foi encontrado o arquivo simplificado na página do protocolo "
                + protocolo
            )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            pagina_detalhe
        )

        data = {
            "ctl00_ScriptManager1_HiddenField": "",
            "__LASTFOCUS": "",
            "__EVENTTARGET": (
                "ctl00$ConteudoPagina$controlDetalheTransmissao$" "buttonDownload"
            ),
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$textBoxHiddenAuxiliar": "",
            "VersaoSite": "MAIN 1.00",
            "__AjaxControlToolkitCalendarCssLoaded": "",
        }

        r = self.session.post(URL_CONSULTA_ARQ_SIMP, data=data)
        with open(caminho, "wb") as f:
            f.write(r.content)

    @preparar_metodo
    def baixar_fichas_arquivo_simplificado(
        self, protocolo: str, caminho: str, fichas: list = None, formato: str = None
    ) -> None:
        """Baixa fichas de um arquivo simplificado.

        Args:
            protocolo (str): Protocolo de um arquivo simplificado.
            caminho (str): caminho da pasta onde serão salvas as fichas.
            fichas (list, optional): Fichas que devem ser baixadas. Cada ficha da lista
                passada deve ser uma chave do dicionário `FICHAS_SIMPLIFICADO`. Se
                `None`, todas as fichas serão baixadas.
            formato (str, optional): Formato em que devem ser salvas as fichas. Pode ser
                `"pdf"`, `"xlsx"` ou `None`. Se `None`, as fichas serão baixadas em
                ambos os formatos.

        Raises:
            ValueError: Erro indicando fichas inválidas ou formato de arquivo inválido.
        """
        Ecredac._validar_protocolo(protocolo)

        if fichas:
            fichas_ajust = [
                ficha.upper()
                for ficha in fichas
                if ficha.upper() in FICHAS_SIMPLIFICADO
            ]

            if not fichas_ajust:
                raise ValueError(
                    "Lista de fichas inválida.\n"
                    f"Valores aceitos: {list(FICHAS_SIMPLIFICADO)}\n"
                    f"Valores passados: {fichas}"
                )

            if len(fichas_ajust) < len(fichas):
                # TODO: avisar que algumas fichas inválidas foram removidas
                pass
        else:
            fichas_ajust = list(FICHAS_SIMPLIFICADO)

        if formato:
            formato = formato.lower()

            if formato not in ["pdf", "xlsx"]:
                raise ValueError(
                    f"Formato {formato} inválido. Formatos válidos são 'pdf' e 'xlsx'."
                )

        # SEGUE O BAILE
        pagina_detalhe = self._detalhar_arquivo(
            tipo="simplificado", protocolo=protocolo
        )

        if (
            "ctl00_ConteudoPagina_controlResultadoProcessamento_panelInformacoes"
            "DeclaradasArquivo" not in pagina_detalhe
        ):
            raise Exception(
                "Não foram encontradas fichas na página do protocolo " + protocolo
            )

        # CAPTURANDO VALIDADORES
        (
            viewstate,
            viewstategenerator,
            eventvalidation,
        ) = extrair_validadores_aspnet(pagina_detalhe)

        for ficha in fichas_ajust:
            if ficha != "RESUMO":
                name = "ResultadoProcessamentoArqSimplificado"
                url_comp = (
                    "/Web/paginas/arquivoDigital/arquivoSimplificado/"
                    "resultadoProcessamento.aspx?" + FICHAS_SIMPLIFICADO[ficha]
                )
            else:
                name = "ReportFichasConsolidadas6"
                url_comp = "/Web/paginas/administracao/relatorios/RelatoriosPopup.aspx"
                data = {
                    "ctl00$ScriptManager1": (
                        "ctl00$ConteudoPagina$updatePanelPrincipal|ctl00$"
                        "ConteudoPagina$controlResultadoProcessamento$"
                        "LinkButtonRelatorioGeral"
                    ),
                    "__EVENTTARGET": (
                        "ctl00$ConteudoPagina$controlResultadoProcessamento"
                        "$LinkButtonRelatorioGeral"
                    ),
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "VersaoSite": "MAIN 1.00",
                    "__ASYNCPOST": "true",
                }
                r = self.session.post(URL_CONSULTA_ARQ_SIMP, data=data)

            r = self.session.get(URL_BASE + url_comp)
            control_id = r.text.split("ControlID=")[1].split("&")[0]
            report_session = r.text.split("ReportSession=")[1].split("&")[0]

            # EXCEL
            if not formato or formato == "xlsx":
                r = self.session.post(
                    URL_BASE
                    + "/Reserved.ReportViewerWebControl.axd?"
                    + "ReportSession="
                    + report_session
                    + "&Culture=1046&CultureOverrides=True&UICulture=1046"
                    + "&UICultureOverrides=True&ReportStack=1"
                    + "&ControlID="
                    + control_id
                    + "&OpType=Export&FileName="
                    + name
                    + "&ContentDisposition=OnlyHtmlInline&Format=EXCELOPENXML",
                    data="",
                )
                caminho_xlsx = os.path.join(
                    caminho, protocolo.replace("/", "_") + "_" + ficha + ".xlsx"
                )
                with open(caminho_xlsx, "wb") as f:
                    f.write(r.content)

            # PDF
            if not formato or formato == "pdf":
                r = self.session.post(
                    URL_BASE
                    + "/Reserved.ReportViewerWebControl.axd?"
                    + "ReportSession="
                    + report_session
                    + "&Culture=1046&CultureOverrides=True&UICulture=1046"
                    + "&UICultureOverrides=True&ReportStack=1"
                    + "&ControlID="
                    + control_id
                    + "&OpType=Export&FileName="
                    + name
                    + "&ContentDisposition=OnlyHtmlInline&Format=PDF",
                    data="",
                )

                caminho_pdf = os.path.join(
                    caminho, protocolo.replace("/", "_") + "_" + ficha + ".pdf"
                )
                with open(caminho_pdf, "wb") as f:
                    f.write(r.content)

    @preparar_metodo
    def listar_arquivos_custo_transmitidos(
        self,
        cnpj: str = "",
        ie: str = "",
        data_transmissao_inicial: str = "",
        data_transmissao_final: str = "",
        referencia_inicial: str = "",
        referencia_final: str = "",
        protocolo: str = "",
        finalidade: str = "",
    ):
        """Lista arquivos de custo conforme os critérios de pesquisa passados.

        Args:
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
                Obrigatório se não for passado valor em `protocolo` e `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`. Obrigatório se não for passado valor em
                `protocolo` e `cnpj`.
            data_transmissao_inicial (str, optional): Data de transmissão inicial, no
                formato DD/MM/AAAA.
            data_transmissao_final (str, optional): Data de transmissão final, no
                formato DD/MM/AAAA.
            referencia_inicial (str, optional): Mês de referência inicial, no formato
                MM/AAAA.
            referencia_final (str, optional): Mês de referência final, no formato
                MM/AAAA.
            protocolo (str, optional): Protocolo de arquivo simplificado. Obrigatório se
                não for passado valor em `cnpj` ou `ie`.
            finalidade (str, optional): Finalidade do arquivo. Deve ser uma da chaves do
                dicionário `CUSTO_FINALIDADE`.

        Returns:
            Uma lista de tuplas com os dados dos arquivos na seguinte ordem: Protocolo,
            CNPJ, Referência, Finalidade, Data de Transmissão e Situação.
        """
        if cnpj:
            if ie:
                raise ValueError("Informe apenas ie ou cnpj (mas não ambos).")

            cnpj = formatar_cnpj(cnpj)[1]
        elif ie:
            ie = formatar_ie(ie)[1]

        if data_transmissao_inicial:
            data_transmissao_inicial = formatar_data(
                data_transmissao_inicial, "%d/%m/%Y"
            )

        if data_transmissao_final:
            if not data_transmissao_inicial:
                raise Exception(
                    "Se informado data_transmissao_final, deve ser informado também "
                    "data_transmissao_inicial."
                )

            data_transmissao_final = formatar_data(data_transmissao_final, "%d/%m/%Y")

        if referencia_inicial:
            referencia_inicial = formatar_mes_referencia(
                ref=referencia_inicial, formato_saida="mm/aaaa"
            )

        if referencia_final:
            referencia_final = formatar_mes_referencia(
                ref=referencia_final, formato_saida="mm/aaaa"
            )

        return self._listar_arquivos(
            tipo="custo",
            cnpj=cnpj,
            ie=ie,
            data_transmissao_inicial=data_transmissao_inicial,
            data_transmissao_final=data_transmissao_final,
            referencia_inicial=referencia_inicial,
            referencia_final=referencia_final,
            protocolo=protocolo,
            finalidade=finalidade,
        )

    @preparar_metodo
    def obter_ficha_arquivo_custo(protocolo: str, ficha: str) -> dict:
        """Método não implementado."""
        raise NotImplementedError()

        """
        ficha = ficha.upper()
        if ficha not in FICHAS_CUSTO:
            raise ValueError(
                "Ficha inválida.\n"
                f"Valores aceitos: {list(FICHAS_CUSTO)}\n"
                f"Valor passado: {ficha}"
            )

        pagina = self._detalhar_ficha_arquivo_custo(protocolo=protocolo, ficha=ficha)

        return Ecredac._scrape_ficha_arquivo_custo(html=pagina)
        """

    @preparar_metodo
    def baixar_fichas_arquivo_custo(
        self, protocolo: str, caminho: str, fichas: list = None, formato: str = None
    ):
        """Baixa fichas de um arquivo de custo.

        Args:
            protocolo (str): Protocolo de um arquivo de custo.
            caminho (str): caminho da pasta onde serão salvas as fichas.
            fichas (list, optional): Fichas que devem ser baixadas. Cada ficha da lista
                passada deve ser uma chave do dicionário `FICHAS_CUSTO`. Se `None`,
                todas as fichas serão baixadas.
            formato (str, optional): Formato em que devem ser salvas as fichas. Pode ser
                `"pdf"`, `"xlsx"` ou `None`. Se `Nome`, as fichas serão baixadas em
                ambos os formatos.

        Raises:
            ValueError: Erro indicando fichas inválidas ou formato de arquivo inválido.
        """
        if fichas:
            fichas_ajust = [
                ficha.upper() for ficha in fichas if ficha.upper() in FICHAS_CUSTO
            ]

            if not fichas_ajust:
                raise ValueError(
                    "Lista de fichas inválida.\n"
                    f"Valores aceitos: {list(FICHAS_CUSTO)}\n"
                    f"Valores passados: {fichas}"
                )

            if len(fichas_ajust) < len(fichas):
                # TODO: avisar que algumas fichas inválidas foram removidas
                pass
        else:
            fichas_ajust = list(FICHAS_CUSTO)

        if formato:
            formato = formato.lower()

            if formato not in ["pdf", "xlsx"]:
                raise ValueError(
                    f"Formato {formato} inválido. Formatos válidos são 'pdf' e 'xlsx'."
                )

        # SEGUE O BAILE
        pagina_detalhe = self._detalhar_arquivo(tipo="custo", protocolo=protocolo)

        if (
            "ctl00_ConteudoPagina_controlResultadoProcessamento_panelInformacoes"
            "DeclaradasArquivo" not in pagina_detalhe
        ):
            raise Exception(
                "Não foram encontradas fichas na página do protocolo " + protocolo
            )

        for ficha in fichas_ajust:
            name = "ResultadoProcessamentoArqCusto"
            url_comp = (
                "/Web/paginas/arquivoDigital/arquivoCusto/"
                + "resultadoProcessamento.aspx?"
                + FICHAS_CUSTO[ficha]
            )
            r = self.session.get(URL_BASE + url_comp)

            if ficha == "RESUMO":
                # O sistema não possui versões pdf e xlsx para a ficha RESUMO
                # então o HTML é salvo e os arquivos são criados via pywin32
                caminho_html = os.path.join(caminho, protocolo + "_" + ficha + ".html")
                html = r.content.replace(
                    bytes("../../..", "utf-8"), bytes(URL_BASE + "/Web", "utf-8")
                )  # ajustando links relativos
                """
                tmp = tempfile.NamedTemporaryFile(delete=False)
                tmp.write(html)
                tmp.close()
                """
                with open(caminho_html, "wb") as f:
                    f.write(html)

                # EXCEL
                if not formato or formato == "xlsx":
                    caminho_xlsx = os.path.join(
                        caminho, protocolo + "_" + ficha + ".xlsx"
                    )
                    oExcel = win32com.client.DispatchEx("Excel.Application")
                    oExcel.DisplayAlerts = False
                    oSht = oExcel.Workbooks.Open(caminho_html)
                    oSht.SaveAs(caminho_xlsx, FileFormat=51)
                    oSht.Close()
                    oExcel.Quit()

                # PDF
                if not formato or formato == "pdf":
                    caminho_pdf = os.path.join(
                        caminho, protocolo + "_" + ficha + ".pdf"
                    )
                    oWord = win32com.client.DispatchEx("Word.Application")
                    oWord.DisplayAlerts = False
                    oDoc = oWord.Documents.Open(caminho_html, ConfirmConversions=False)
                    oDoc.WebOptions.Encoding = 28591  # msoEncodingISO88591Latin1
                    oDoc.PageSetup.Orientation = 1  # wdOrientLandscape
                    oDoc.PageSetup.LeftMargin = 20
                    oDoc.PageSetup.RightMargin = 20
                    oDoc.PageSetup.TopMargin = 20
                    oDoc.PageSetup.BottomMargin = 20
                    oDoc.PageSetup.HeaderDistance = 10
                    oDoc.PageSetup.FooterDistance = 10
                    oDoc.SaveAs(caminho_pdf, FileFormat=17)
                    oDoc.Close()
                    oWord.Quit()

                # os.remove(tmp.name)

                os.remove(caminho_html)

                # SEMPRE É SALVA UMA PASTA COM OS ARQUIVOS DO HTML
                if os.path.exists(caminho_html.replace(".html", "_arquivos")):
                    shutil.rmtree(caminho_html.replace(".html", "_arquivos"))

            else:
                control_id = r.text.split("ControlID=")[1].split("&")[0]
                report_session = r.text.split("ReportSession=")[1].split("&")[0]

                # EXCEL
                if not formato or formato == "xlsx":
                    r = self.session.post(
                        URL_BASE
                        + "/Reserved.ReportViewerWebControl.axd?"
                        + "ReportSession="
                        + report_session
                        + "&Culture=1046&CultureOverrides=True&UICulture=1046"
                        + "&UICultureOverrides=True&ReportStack=1"
                        + "&ControlID="
                        + control_id
                        + "&OpType=Export&FileName="
                        + name
                        + "&ContentDisposition=OnlyHtmlInline&Format=EXCELOPENXML",
                        data="",
                    )
                    caminho_xlsx = os.path.join(
                        caminho, protocolo + "_" + ficha + ".xlsx"
                    )
                    with open(caminho_xlsx, "wb") as f:
                        f.write(r.content)

                # PDF
                if not formato or formato == "pdf":
                    r = self.session.post(
                        URL_BASE
                        + "/Reserved.ReportViewerWebControl.axd?"
                        + "ReportSession="
                        + report_session
                        + "&Culture=1046&CultureOverrides=True&UICulture=1046"
                        + "&UICultureOverrides=True&ReportStack=1"
                        + "&ControlID="
                        + control_id
                        + "&OpType=Export&FileName="
                        + name
                        + "&ContentDisposition=OnlyHtmlInline&Format=PDF",
                        data="",
                    )

                    caminho_pdf = os.path.join(
                        caminho, protocolo + "_" + ficha + ".pdf"
                    )
                    with open(caminho_pdf, "wb") as f:
                        f.write(r.content)

    @preparar_metodo
    def listar_verificacoes_sumarias(
        self,
        cnpj: str = "",
        ie: str = "",
        referencia: str = "",
        protocolo_simplificado: str = "",
        protocolo_custo: str = "",
        protocolo_requisicao: str = "",
    ):
        """Lista verificações sumárias conforme os critérios de pesquisa passados.

        Args:
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`.
            referencia (str, optional): Mês de referência, no formato MM/AAAA.
            protocolo_simplificado (str, optional): Protocolo de arquivo simplificado,
                no formato XXXXX/AAAA. Não deve ser usado junto com
                `protocolo_requisicao`.
            protocolo_custo (str, optional): Protocolo de arquivo de custo. Não deve ser
                usado junto com `protocolo_requisicao`.
            protocolo_requisicao (str, optional): Protocolo da requisição, no formato
                XXXXX/AAAA. Não ser usado junto com `protocolo_simplificado` ou
                `protocolo_custo`.

        Returns:
            Uma lista de tuplas com os dados das verificações na seguinte ordem:
            Protocolo de Transmissão, Tipo de Arquivo, Data da Transmissão, CNPJ,
            Referência, Finalidade e Situação.
        """
        if cnpj:
            if ie:
                raise ValueError("Informe apenas ie ou cnpj (mas não ambos).")

            cnpj = formatar_cnpj(cnpj)[1]
        elif ie:
            ie = formatar_ie(ie)[1]

        if referencia:
            """
            if protocolo_simplificado or protocolo_custo or protocolo_requisicao:
                raise ValueError(
                    "Parâmetro referencia não pode ter valor caso algum protocolo seja "
                    "passado."
                )
            """

            referencia = formatar_mes_referencia(
                ref=referencia, formato_saida="mm/aaaa"
            )

        if (protocolo_simplificado or protocolo_custo) and protocolo_requisicao:
            raise ValueError(
                "Parâmetro protocolo_requisicao não pode ter valor caso algum outro "
                "protocolo seja passado."
            )

        if protocolo_simplificado:
            Ecredac._validar_protocolo(protocolo=protocolo_simplificado)

        if protocolo_requisicao:
            Ecredac._validar_protocolo(protocolo=protocolo_requisicao)

        pagina_consulta = self._consultar_verificacao_sumaria(
            cnpj=cnpj,
            ie=ie,
            referencia=referencia,
            protocolo_simplificado=protocolo_simplificado,
            protocolo_custo=protocolo_custo,
            protocolo_requisicao=protocolo_requisicao,
        )

        lista_dados = []
        if protocolo_requisicao:
            soup_id = (
                "ctl00_ConteudoPagina_controlListagemRequisicao_gridViewRequisicao"
            )
            url_consulta = URL_CONSULTA_VER_SUM_REQ
        else:
            # A CONSULTA POR ARQUIVOS RETORNA A TABELA ZERADA DE UMA FORMA DIFERENTE
            if (
                "ctl00_ConteudoPagina_controlListagemArquivo_gridViewArquivo"
                not in pagina_consulta
            ):
                return lista_dados

            soup_id = "ctl00_ConteudoPagina_controlListagemArquivo_gridViewArquivo"
            url_consulta = URL_CONSULTA_VER_SUM_ARQ

        # IDENTIFICO A QUANTIDADE DE PÁGINAS
        soup = BeautifulSoup(pagina_consulta, "html.parser")
        try:
            td_list = soup.find("tr", {"class": "pgr"}).find("table").find_all("td")
            paginas = range(1, len(td_list) + 1)
        except Exception:
            paginas = [1]

        # LOOP EM TODAS AS PÁGINAS
        for pagina in paginas:
            dados_trs = soup.find(id=soup_id).find_all(
                "tr", {"class": "", "align": "center"}
            )
            lista_dados += [
                (
                    tr.find_all("td")[0].text.strip(),
                    tr.find_all("td")[1].text.strip(),
                    tr.find_all("td")[2].text.strip(),
                    tr.find_all("td")[3].text.strip(),
                    tr.find_all("td")[4].text.strip(),
                    tr.find_all("td")[5].text.strip(),
                    tr.find_all("td")[6].text.strip(),
                )
                if not protocolo_requisicao
                else (
                    tr.find_all("td")[0].text.strip(),
                    tr.find_all("td")[1].text.strip(),
                    tr.find_all("td")[2].text.strip(),
                    tr.find_all("td")[3].text.strip(),
                    tr.find_all("td")[4].text.strip(),
                    tr.find_all("td")[5].text.strip(),
                    tr.find_all("td")[6].text.strip(),
                    tr.find_all("td")[7].text.strip(),
                )
                for tr in dados_trs
            ]

            if pagina == paginas[-1]:
                break

            # Faz a requisição da próxima página
            (
                viewstate,
                viewstategenerator,
                eventvalidation,
            ) = extrair_validadores_aspnet(pagina_consulta)

            data = {
                "ctl00$ScriptManager1": "ctl00$ConteudoPagina$updatePanelPrincipal|"
                + soup_id.replace("_", "$"),
                "__EVENTTARGET": soup_id.replace("_", "$"),
                "__EVENTARGUMENT": "Page$" + str(pagina + 1),
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "VersaoSite": "MAIN 1.00",
                "__ASYNCPOST": "true",
            }

            r = self.session.post(url_consulta, data=data)
            pagina_consulta = r.text
            soup = BeautifulSoup(pagina_consulta, "html.parser")

        return lista_dados

    @preparar_metodo
    def baixar_fichas_verificacao_sumaria(
        self,
        caminho: str,
        cnpj: str = "",
        ie: str = "",
        protocolo_simplificado: str = "",
        protocolo_custo: str = "",
        protocolo_requisicao: str = "",
        fichas: list = None,
        formato: str = None,
    ) -> None:
        """Baixa fichas de um resultado de verificação sumária.

        Args:
            caminho (str): caminho da pasta onde serão salvas as fichas.
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`.
            protocolo_simplificado (str, optional): Protocolo de arquivo simplificado,
                no formato XXXXX/AAAA. Não deve ser usado junto com
                `protocolo_requisicao`.
            protocolo_custo (str, optional): Protocolo de arquivo de custo. Não deve ser
                usado junto com `protocolo_requisicao`.
            protocolo_requisicao (str, optional): Protocolo da requisição, no formato
                XXXXX/AAAA. Não ser usado junto com `protocolo_simplificado` ou
                `protocolo_custo`.
            fichas (list, optional): Fichas que devem ser baixadas. Cada ficha da lista
                passada deve ser uma chave do dicionário `FICHAS_SUMARIA`. Se `None`,
                todas as fichas serão baixadas.
            formato (str, optional): Formato em que devem ser salvas as fichas. Pode ser
                `"pdf"`, `"xlsx"` ou `None`. Se `Nome`, as fichas serão baixadas em
                ambos os formatos.

        Raises:
            ValueError: Erro indicando conflito nos valores passados aos parâmetros, ou
                valor no formato errado passado para `protocolo_simplificado` ou
                `protocolo_requisicao`, ou fichas inválidas ou formato de arquivo
                inválido.
        """
        if cnpj:
            if ie:
                raise ValueError("Informe apenas ie ou cnpj (mas não ambos).")

            cnpj = formatar_cnpj(cnpj)[1]
        elif ie:
            ie = formatar_ie(ie)[1]

        if fichas:
            fichas_ajust = [
                ficha.upper() for ficha in fichas if ficha.upper() in FICHAS_SUMARIA
            ]

            if not fichas_ajust:
                raise ValueError(
                    "Lista de fichas inválida.\n"
                    f"Valores aceitos: {list(FICHAS_SUMARIA)}\n"
                    f"Valores passados: {fichas}"
                )

            if len(fichas_ajust) < len(fichas):
                # TODO: avisar que algumas fichas inválidas foram removidas
                pass
        else:
            fichas_ajust = list(FICHAS_SUMARIA)

        if formato:
            formato = formato.lower()

            if formato not in ["pdf", "xlsx"]:
                raise ValueError(
                    f"Formato {formato} inválido. Formatos válidos são 'pdf' e 'xlsx'."
                )

        if protocolo_simplificado or protocolo_custo:
            if protocolo_requisicao:
                raise ValueError(
                    "Parâmetro protocolo_requisicao não pode ter valor caso algum outro"
                    " protocolo seja passado."
                )
        elif not protocolo_requisicao:
            raise ValueError("Informe pelo menos um protocolo.")

        if protocolo_custo:
            protocolo = protocolo_custo

        if protocolo_simplificado:
            try:
                Ecredac._validar_protocolo(protocolo_simplificado)
            except ValueError:
                raise ValueError(
                    "protocolo_simplificado deve ser passado no formato XXXXX/AAAA."
                )

            protocolo = protocolo_simplificado.replace("/", "_")

        if protocolo_requisicao:
            try:
                Ecredac._validar_protocolo(protocolo_requisicao)
            except ValueError:
                raise ValueError(
                    "protocolo_requisicao deve ser passado no formato XXXXX/AAAA."
                )

            protocolo = protocolo_requisicao.replace("/", "_")

        # SEGUE O BAILE
        pagina_detalhe = self._detalhar_verificacao_sumaria(
            ie=ie,
            cnpj=cnpj,
            protocolo_simplificado=protocolo_simplificado,
            protocolo_custo=protocolo_custo,
            protocolo_requisicao=protocolo_requisicao,
        )

        if (
            "ctl00_ConteudoPagina_controlDetalheVerificacaoSumaria_panelArquivo"
            not in pagina_detalhe
        ):
            raise Exception("Não foram encontradas fichas.")

        soup = BeautifulSoup(pagina_detalhe, "html.parser")
        for ficha in fichas_ajust:
            link = soup.find("a", onclick=lambda v: v and FICHAS_SUMARIA[ficha] in v)

            if not link:
                continue

            cod = link["onclick"].split("codigoVerificacaoSumaria=")[1].split("&")[0]
            url_comp = (
                "/Web/paginas/arquivoDigital"
                + "/verificacaoSumaria/relatorioVerificacaoSumaria.aspx?"
                + "codigoVerificacaoSumaria="
                + cod
                + "&"
                + FICHAS_SUMARIA[ficha]
            )
            r = self.session.get(URL_BASE + url_comp)
            caminho_html = os.path.join(caminho, protocolo + "_" + ficha + ".html")

            try:
                # HTML
                html = r.content.replace(
                    bytes("../../..", "utf-8"), bytes(URL_BASE + "/Web", "utf-8")
                )  # ajustando links relativos
                with open(caminho_html, "wb") as f:
                    f.write(html)

                # EXCEL
                if not formato or formato == "xlsx":
                    caminho_xlsx = os.path.join(
                        caminho, protocolo + "_" + ficha + ".xlsx"
                    )
                    oExcel = win32com.client.DispatchEx("Excel.Application")
                    oExcel.DisplayAlerts = False
                    oSht = oExcel.Workbooks.Open(caminho_html)
                    oSht.SaveAs(caminho_xlsx, FileFormat=51)
                    oSht.Close()
                    oExcel.Quit()

                # PDF
                if not formato or formato == "pdf":
                    caminho_pdf = os.path.join(
                        caminho, protocolo + "_" + ficha + ".pdf"
                    )
                    oWord = win32com.client.DispatchEx("Word.Application")
                    oWord.DisplayAlerts = False
                    oDoc = oWord.Documents.Open(caminho_html, ConfirmConversions=False)
                    oDoc.WebOptions.Encoding = 28591  # msoEncodingISO88591Latin1
                    oDoc.PageSetup.Orientation = 1  # wdOrientLandscape
                    oDoc.PageSetup.LeftMargin = 20
                    oDoc.PageSetup.RightMargin = 20
                    oDoc.PageSetup.TopMargin = 20
                    oDoc.PageSetup.BottomMargin = 20
                    oDoc.PageSetup.HeaderDistance = 10
                    oDoc.PageSetup.FooterDistance = 10
                    oDoc.SaveAs(caminho_pdf, FileFormat=17)
                    oDoc.Close()
                    oWord.Quit()
            except PermissionError:
                raise PermissionError(
                    "O documento está travado na memória, fruto de algum "
                    "erro em alguma execução anterior. É necessário reiniciar o "
                    "computador ou encerrar as instâncias do WORD e/ou EXCEL no "
                    "gerenciador de tarefas."
                )

            os.remove(caminho_html)

            # SEMPRE É SALVA UMA PASTA COM OS ARQUIVOS DO HTML
            if os.path.exists(caminho_html.replace(".html", "_arquivos")):
                shutil.rmtree(caminho_html.replace(".html", "_arquivos"))

    """
    def _detalhar_ficha_arquivo_simplificado(self, protocolo: str, ficha: str):
        pagina_detalhe = self._detalhar_arquivo(protocolo=protocolo)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            pagina_detalhe
        )

        if (
            "ctl00_ConteudoPagina_controlResultadoProcessamento_panelInformacoes"
            "DeclaradasArquivo" not in pagina_detalhe
        ):
            raise Exception(
                "Não foram encontradas fichas na página do protocolo " + protocolo
            )

        if FICHAS_SIMPLIFICADO[ficha] != "RelatorioGeral":
            url_comp = (
                "/Web/paginas/arquivoDigital/arquivoSimplificado/"
                + "resultadoProcessamento.aspx?"
                + FICHAS_SIMPLIFICADO[ficha]
            )
        else:
            url_comp = "/Web/paginas/administracao/relatorios/RelatoriosPopup.aspx"
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$updatePanelPrincipal|"
                    "ctl00$ConteudoPagina$controlResultadoProcessamento$"
                    "LinkButtonRelatorioGeral"
                ),
                "ctl00_ScriptManager1_HiddenField": "",
                "__LASTFOCUS": "",
                "__EVENTTARGET": (
                    "ctl00$ConteudoPagina$controlResultadoProcessamento$"
                    "LinkButtonRelatorioGeral"
                ),
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "VersaoSite": "MAIN 1.00",
                "__ASYNCPOST": "true",
            }
            r = self.session.post(URL_CONSULTA_ARQ_SIMP, data=data)

        r = self.session.get(URL_BASE + url_comp)

        return r.text
    """

    """
    def _detalhar_ficha_arquivo_custo(
        self,
        protocolo: int,
        ficha: str,
    ):

        if not self.autenticado():
            raise AuthenticationError(
                "É necessário autenticar-se antes de utilizar o método."
            )

        ficha = FICHAS_CUSTO[ficha.upper()]

        r = self._detalhar_arquivo_custo(protocolo=protocolo)

        # CAPTURANDO VALIDADORES
        (
            viewstate,
            viewstategenerator,
            eventvalidation,
        ) = extrair_validadores_aspnet(r.text)

        if (
            "ctl00_ConteudoPagina_controlResultadoProcessamento_"
            "panelInformacoesDeclaradasArquivo"
        ) in r.text:

            url_comp = (
                "/Web/paginas/arquivoDigital/arquivoCusto/resultadoProcessamento.aspx?"
                + ficha
            )

            r = self.session.get(URL_BASE + url_comp)

            return r.text

        else:
            return "Não foram encontradas fichas na página do protocolo " + protocolo
    """

    def _listar_arquivos(
        self,
        tipo: str,
        cnpj: str = "",
        ie: str = "",
        data_transmissao_inicial: str = "",
        data_transmissao_final: str = "",
        referencia_inicial: str = "",
        referencia_final: str = "",
        protocolo: str = "",
        finalidade: str = "",
    ):
        assert tipo in ["simplificado", "custo"]

        # Requisita a primeira página de resultados
        pagina_consulta = self._consultar_arquivos(
            tipo=tipo,
            cnpj=cnpj,
            ie=ie,
            data_transmissao_inicial=data_transmissao_inicial,
            data_transmissao_final=data_transmissao_final,
            referencia_inicial=referencia_inicial,
            referencia_final=referencia_final,
            protocolo=protocolo,
            finalidade=finalidade,
        )

        lista_dados = []

        if "Nenhum registro encontrado" in pagina_consulta:
            return lista_dados

        # IDENTIFICO A QUANTIDADE DE PÁGINAS
        soup = BeautifulSoup(pagina_consulta, "html.parser")
        try:
            td_list = soup.find("tr", {"class": "pgr"}).find("table").find_all("td")
            paginas = range(1, len(td_list) + 1)
        except Exception:
            paginas = [1]

        url_consulta = (
            URL_CONSULTA_ARQ_SIMP if tipo == "simplificado" else URL_CONSULTA_ARQ_CUSTO
        )

        # LOOP EM TODAS AS PÁGINAS
        for pagina in paginas:
            dados_trs = soup.find(
                id="ctl00_ConteudoPagina_controlListagemTransmissao_gridViewTransmissao"
            ).find_all("tr", {"class": "", "align": "center"})
            lista_dados += [
                (
                    tr.find_all("td")[0].text.strip(),
                    tr.find_all("td")[1].text.strip(),
                    tr.find_all("td")[2].text.strip(),
                    tr.find_all("td")[3].text.strip(),
                    tr.find_all("td")[4].text.strip(),
                    tr.find_all("td")[5].text.strip(),
                )
                for tr in dados_trs
            ]

            if pagina == paginas[-1]:
                break

            # Faz a requisição da próxima página
            (
                viewstate,
                viewstategenerator,
                eventvalidation,
            ) = extrair_validadores_aspnet(pagina_consulta)

            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$updatePanelPrincipal|"
                    "ctl00$ConteudoPagina$controlListagemTransmissao$"
                    "gridViewTransmissao"
                ),
                "__EVENTTARGET": (
                    "ctl00$ConteudoPagina$controlListagemTransmissao$"
                    "gridViewTransmissao"
                ),
                "__EVENTARGUMENT": "Page$" + str(pagina + 1),
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "VersaoSite": "MAIN 1.00",
                "__ASYNCPOST": "true",
            }
            r = self.session.post(url_consulta, data=data)
            pagina_consulta = r.text
            soup = BeautifulSoup(pagina_consulta, "html.parser")

        return lista_dados

    def _consultar_arquivos(
        self,
        tipo: str,
        cnpj: str = "",
        ie: str = "",
        data_transmissao_inicial: str = "",
        data_transmissao_final: str = "",
        referencia_inicial: str = "",
        referencia_final: str = "",
        protocolo: str = "",
        finalidade: str = "",
    ):
        assert tipo in ["simplificado", "custo"]

        mes_ini = ""
        ano_ini = ""
        mes_fim = ""
        ano_fim = ""
        protocolo_pre = ""
        protocolo_suf = ""

        if referencia_inicial:
            mes_ini, ano_ini = referencia_inicial.split("/")

        if referencia_final:
            mes_fim, ano_fim = referencia_final.split("/")

        if protocolo and tipo == "simplificado":
            protocolo_pre, protocolo_suf = protocolo.split("/")
            protocolo = ""

        # ABRINDO TELA DE CONSULTA
        url_consulta = (
            URL_CONSULTA_ARQ_SIMP if tipo == "simplificado" else URL_CONSULTA_ARQ_CUSTO
        )
        r = self.session.get(url_consulta)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )

        # Nessa situação específica, é necessário fazer um post antes do post final
        if ie and tipo == "simplificado":
            data = {
                "ctl00$ScriptManager1": (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "updatePanelFiltro|ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ),
                "__EVENTTARGET": (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ),
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "controlSelecaoEstabelecimento$dropDownListSelecaoTipoBusca"
                ): "1",
                (
                    "ctl00$ConteudoPagina$controlFiltroConsulta$"
                    "dropDownListFinalidadeArquivo"
                ): "00",
                "VersaoSite": "MAIN 1.00",
                "__ASYNCPOST": "true",
            }
            r = self.session.post(URL_CONSULTA_ARQ_SIMP, data=data)
            viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
                r.text
            )

        finalidade = (
            SIMPLIFICADO_FINALIDADE[finalidade]
            if tipo == "simplificado"
            else CUSTO_FINALIDADE[finalidade]
        )
        ctl_filtro = "ctl00$ConteudoPagina$controlFiltroConsulta"
        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$updatePanelPrincipal|"
                "ctl00$ConteudoPagina$buttonConsultar"
            ),
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_filtro + "$textBoxFiltroDataInicial": data_transmissao_inicial,
            ctl_filtro + "$textBoxFiltroDataFinal": data_transmissao_final,
            ctl_filtro + "$dropDownListReferenciaMesInicial": mes_ini,
            ctl_filtro + "$textBoxReferenciaAnoInicial": ano_ini,
            ctl_filtro + "$dropDownListReferenciaMesFinal": mes_fim,
            ctl_filtro + "$textBoxReferenciaAnoFinal": ano_fim,
            ctl_filtro + "$textBoxFiltroNumeroProtocolo": protocolo,
            ctl_filtro + "$textBoxFiltroPrefixoNumeroPedido": protocolo_pre,
            ctl_filtro + "$textBoxFiltroSufixoNumeroPedido": protocolo_suf,
            ctl_filtro + "$dropDownListFinalidadeArquivo": finalidade,
            "VersaoSite": "MAIN 1.00",
            "__ASYNCPOST": "true",
            "ctl00$ConteudoPagina$buttonConsultar": "Consultar",
        }
        ctl_selec_estab = ctl_filtro + "$controlSelecaoEstabelecimento$"

        if cnpj:
            data |= {
                ctl_selec_estab + "textBoxFiltroCNPJ": cnpj,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "0",
            }
        elif ie:
            data |= {
                ctl_selec_estab + "textBoxFiltroIE": ie,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "1",
            }

        r = self.session.post(url_consulta, data=data)

        return r.text

    def _detalhar_arquivo(self, tipo: str, protocolo: str):
        assert tipo in ["simplificado", "custo"]

        pagina_consulta = self._consultar_arquivos(tipo=tipo, protocolo=protocolo)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            pagina_consulta
        )

        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$updatePanelPrincipal|"
                "ctl00$ConteudoPagina$controlListagemTransmissao$gridViewTransmissao$"
                "ctl02$ctl00"
            ),
            "__EVENTTARGET": (
                "ctl00$ConteudoPagina$controlListagemTransmissao$"
                "gridViewTransmissao$ctl02$ctl00"
            ),
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "VersaoSite": "MAIN 1.00",
            "__ASYNCPOST": "true",
        }
        url = (
            URL_CONSULTA_ARQ_SIMP if tipo == "simplificado" else URL_CONSULTA_ARQ_CUSTO
        )
        r = self.session.post(url, data=data)

        return r.text

    def _consultar_verificacao_sumaria(
        self,
        cnpj: str = "",
        ie: str = "",
        referencia: str = "",
        protocolo_simplificado: str = "",
        protocolo_custo: int = "",
        protocolo_requisicao: str = "",
    ):
        ref_mes = ""
        ref_ano = ""
        prot_simp_pre = ""
        prot_simp_suf = ""
        prot_req_pre = ""
        prot_req_suf = ""

        if referencia:
            ref_mes, ref_ano = referencia.split("/")

        if protocolo_simplificado:
            prot_simp_pre, prot_simp_suf = protocolo_simplificado.split("/")

        if protocolo_requisicao:
            prot_req_pre, prot_req_suf = protocolo_requisicao.split("/")

        # ABRINDO TELA DE CONSULTA
        url_consulta = (
            URL_CONSULTA_VER_SUM_REQ
            if protocolo_requisicao
            else URL_CONSULTA_VER_SUM_ARQ
        )
        r = self.session.get(url_consulta)

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            r.text
        )
        ctl_filtro = "ctl00$ConteudoPagina$controlFiltro"
        data = {
            "ctl00$ScriptManager1": (
                "ctl00$ConteudoPagina$updatePanelPrincipal|"
                "ctl00$ConteudoPagina$buttonConsultar"
            ),
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            ctl_filtro + "$dropDownListReferenciaMes": ref_mes,
            ctl_filtro + "$dropDownListReferenciaAno": ref_ano,
            ctl_filtro + "$textBoxFiltroNumeroProtocoloCusto": protocolo_custo,
            ctl_filtro
            + "$textBoxFiltroPrefixoNumeroProtocoloSimplificado": prot_simp_pre,
            ctl_filtro
            + "$textBoxFiltroSufixoNumeroProtocoloSimplificado": prot_simp_suf,
            ctl_filtro + "$textBoxFiltroPrefixoNumeroProtocolo": prot_req_pre,
            ctl_filtro + "$textBoxFiltroSufixoNumeroProtocolo": prot_req_suf,
            "VersaoSite": "MAIN 1.00",
            "__ASYNCPOST": "true",
            "ctl00$ConteudoPagina$buttonConsultar": "Consultar",
        }
        ctl_selec_estab = ctl_filtro + "$controlSelecaoEstabelecimento$"

        if cnpj:
            data |= {
                ctl_selec_estab + "textBoxFiltroCNPJ": cnpj,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "0",
            }
        elif ie:
            data |= {
                ctl_selec_estab + "textBoxFiltroIE": ie,
                ctl_selec_estab + "dropDownListSelecaoTipoBusca": "1",
            }

        r = self.session.post(url_consulta, data=data)

        return r.text

    def _detalhar_verificacao_sumaria(
        self,
        cnpj: str = "",
        ie: str = "",
        protocolo_simplificado: str = "",
        protocolo_custo: str = "",
        protocolo_requisicao: str = "",
    ):
        pagina_consulta = self._consultar_verificacao_sumaria(
            cnpj=cnpj,
            ie=ie,
            protocolo_simplificado=protocolo_simplificado,
            protocolo_custo=protocolo_custo,
            protocolo_requisicao=protocolo_requisicao,
        )

        # CAPTURANDO VALIDADORES
        viewstate, viewstategenerator, eventvalidation = extrair_validadores_aspnet(
            pagina_consulta
        )

        if not protocolo_requisicao:
            tipo_url = (
                "/Web/paginas/arquivoDigital/verificacaoSumaria/"
                "consultaVerificacaoSumariaPorArquivo.aspx"
            )
            data_comp = (
                "ctl00$ConteudoPagina$controlListagemArquivo"
                "$gridViewArquivo$ctl02$LinkButton1"
            )
        else:
            tipo_url = (
                "/Web/paginas/arquivoDigital/verificacaoSumaria/"
                "consultaVerificacaoSumariaPorRequisicao.aspx"
            )
            data_comp = (
                "ctl00$ConteudoPagina$controlListagemRequisicao"
                "$gridViewRequisicao$ctl02$LinkButton1"
            )

        data = {
            "ctl00$ScriptManager1": "ctl00$ConteudoPagina$updatePanelPrincipal|"
            + data_comp,
            "__EVENTTARGET": data_comp,
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "VersaoSite": "MAIN 1.00",
            "__ASYNCPOST": "true",
        }

        r = self.session.post(URL_BASE + tipo_url, data=data)

        return r.text

    """
    def _detalhar_ficha_sumaria(
        self,
        ie_cnpj: str,
        ficha: str,
        protocolo_simp: str = "",
        protocolo_custo: str = "",
        requisiçao: str = "",
    ):

        if not self.autenticado():
            raise AuthenticationError(
                "É necessário autenticar-se antes de utilizar o método."
            )

        # TRABALHANDO AS VARIÁVEIS
        if len(ie_cnpj) == 12 or len(ie_cnpj) == 15:
            ie_cnpj = formatar_ie(ie_cnpj)[1]
        if len(ie_cnpj) == 14 or len(ie_cnpj) == 17:
            ie_cnpj = formatar_cnpj(ie_cnpj)[1]

        if (
            (requisiçao != "" and (protocolo_simp != "" or protocolo_custo != ""))
            or (requisiçao == "" and protocolo_simp != "" and protocolo_custo != "")
            or (requisiçao == "" and protocolo_simp == "" and protocolo_custo == "")
        ):
            raise Exception(
                "Informar ou requisiçao, ou protocolo_simp ou protocolo_custo"
            )

        if protocolo_simp != "":
            if (
                "/" not in protocolo_simp
                or not protocolo_simp[-5].isascii()
                or not protocolo_simp[-4:].isdigit()
            ):
                raise Exception(
                    "Informar protocolo_simp no formato XXXXX/AAAA, "
                    "com 4 dígitos para o ano"
                )

        if requisiçao != "":
            if (
                "/" not in requisiçao
                or not requisiçao[-5].isascii()
                or not requisiçao[-4:].isdigit()
            ):
                raise Exception(
                    "Informar requisiçao no formato XXXXX/AAAA, "
                    "com 4 dígitos para o ano"
                )

        ficha = FICHAS_SUMARIA[ficha.upper()]

        r = self._detalhar_verificacao_sumaria(
            ie_cnpj=ie_cnpj,
            protocolo_simplificado=protocolo_simp,
            protocolo_custo=protocolo_custo,
            requisicao=requisiçao,
        )

        # CAPTURANDO VALIDADORES
        (
            viewstate,
            viewstategenerator,
            eventvalidation,
        ) = extrair_validadores_aspnet(r.text)

        if (
            "ctl00_ConteudoPagina_controlDetalheVerificacaoSumaria_panelArquivo"
            in r.text
        ):

            # MONTANDO O DICT QUE RELACIONA, PRA CADA FICHA, O CODIGO VERIFICAÇÃO
            soup = BeautifulSoup(r.text, "html.parser")
            links = soup.find(
                id="ctl00_ConteudoPagina_controlDetalheVerificacaoSumaria_panelArquivo"
            ).find_all("a")
            cod_dict = {}
            cod_dict[ficha] = {
                link["onclick"].split("=")[1].split("&")(0)
                for link in links
                if ficha in str(link)
            }

            url_comp = (
                "/Web/paginas/arquivoDigital/verificacaoSumaria/relatorioVerificacaoSumaria.aspx?codigoVerificacaoSumaria="
                + cod_dict[ficha]
                + "&"
                + ficha
            )

            r = self.session.get(URL_BASE + url_comp)
            return r.text

        else:
            return "Não foram encontradas fichas na página do protocolo "
    """

    @preparar_metodo
    def listar_resultados_verificacao_sumaria(
        self,
        cnpj: str = "",
        ie: str = "",
        protocolo_simplificado: str = "",
        protocolo_custo: str = "",
        protocolo_requisicao: str = "",
    ) -> list:
        """Lista os resultados de uma verificação sumária.

        Os parâmetros desse método servem como critério de pesquisa da verificação
        sumária. Caso mais de uma verificação atena aos parâmetros, serão listados os
        resultados da primeira verificação sumária resultante.

        Args:
            cnpj (str, optional): CNPJ da empresa. Não deve ser usado junto com `ie`.
            ie (str, optional): Inscrição Estadual do estabelecimento. Não deve ser
                usado junto com `cnpj`.
            protocolo_simplificado (str, optional): Protocolo de arquivo simplificado,
                no formato XXXXX/AAAA. Não deve ser usado junto com
                `protocolo_requisicao`.
            protocolo_custo (str, optional): Protocolo de arquivo de custo. Não deve ser
                usado junto com `protocolo_requisicao`.
            protocolo_requisicao (str, optional): Protocolo da requisição, no formato
                XXXXX/AAAA. Não ser usado junto com `protocolo_simplificado` ou
                `protocolo_custo`.

        Returns:
            Uma lista de tuplas com os dados dos resultados na seguinte ordem:
            Aplicação, Protocolo da Requisição, Data da Requisição, Situação e
            Resultado.
        """
        if cnpj:
            if ie:
                raise ValueError("Informe apenas ie ou cnpj (mas não ambos).")

            cnpj = formatar_cnpj(cnpj)[1]
        elif ie:
            ie = formatar_ie(ie)[1]

        if protocolo_simplificado or protocolo_custo:
            if protocolo_requisicao:
                raise ValueError(
                    "Parâmetro protocolo_requisicao não pode ter valor caso algum outro"
                    " protocolo seja passado."
                )
        elif not protocolo_requisicao:
            raise ValueError("Informe pelo menos um protocolo.")

        if protocolo_requisicao:
            try:
                Ecredac._validar_protocolo(protocolo_requisicao)
            except ValueError:
                raise ValueError(
                    "protocolo_requisicao deve ser passado no formato XXXXX/AAAA."
                )

        if protocolo_simplificado:
            try:
                Ecredac._validar_protocolo(protocolo_simplificado)
            except ValueError:
                raise ValueError(
                    "protocolo_simplificado deve ser passado no formato XXXXX/AAAA."
                )

        pagina_detalhe = self._detalhar_verificacao_sumaria(
            ie=ie,
            cnpj=cnpj,
            protocolo_simplificado=protocolo_simplificado,
            protocolo_custo=protocolo_custo,
            protocolo_requisicao=protocolo_requisicao,
        )

        lista_dados = []

        if (
            "ctl00_ConteudoPagina_controlDetalheVerificacaoSumaria_panelArquivo"
            not in pagina_detalhe
        ):
            return lista_dados

        soup = BeautifulSoup(pagina_detalhe, "html.parser")
        dados = soup.find(
            id="ctl00_ConteudoPagina_controlDetalheVerificacaoSumaria_panelArquivo"
        ).find_all(lambda tag: tag.name == "div" and tag.has_attr("id"))

        if not dados:
            return lista_dados

        lista_dados += [
            (
                dado.find("b").text.strip(),
                dado.find("div", {"id": ""})
                .find("tr", {"class": "", "align": "center"})
                .find_all("td")[0]
                .text.strip(),
                dado.find("div", {"id": ""})
                .find("tr", {"class": "", "align": "center"})
                .find_all("td")[1]
                .text.strip(),
                dado.find("div", {"id": ""})
                .find("tr", {"class": "", "align": "center"})
                .find_all("td")[2]
                .text.strip(),
                dado.find("div", {"id": ""})
                .find("tr", {"class": "", "align": "center"})
                .find_all("td")[3]
                .text.strip(),
            )
            for dado in dados
        ]

        return lista_dados

    @staticmethod
    def _checar_erro_pagina(soup):
        erro = soup.find(id="ctl00_ConteudoPagina_MsgErro_labelMensagem")

        if erro:
            raise Exception(erro.text)

    @staticmethod
    def _validar_protocolo(protocolo):
        if (
            "/" not in protocolo
            or not protocolo[:-5].isascii()
            or not protocolo[-4:].isdigit()
        ):
            raise ValueError("protocolo deve ser passado no formato XXXXX/AAAA.")

    @staticmethod
    def _scrape_consulta_apuracao_simplificada(html):
        soup = BeautifulSoup(html, "html.parser")
        Ecredac._checar_erro_pagina(soup)
        dados = soup.find(
            id=(
                "ctl00_ConteudoPagina_controlDetalheEstabelecimento_"
                "detailsViewEstabelecimento"
            )
        ).find_all("tr")
        dados_dict = {
            dado.find_all("td")[0].text[:-2]: dado.find_all("td")[1].text.strip()
            for dado in dados
        }

        try:
            opcao = soup.find(
                id=(
                    "ctl00_ConteudoPagina_controlDetalheOpcaoArquivoSimplificado_"
                    "labelOpcao"
                )
            ).text

            if opcao == "Não Optante":
                dados_dict["Adesão"] = False
            elif opcao == "Adesão":
                dados_dict["Adesão"] = True
        except Exception:
            # TODO: registrar warning de que não foi possível recuperar opção de adesão
            pass

        return dados_dict
