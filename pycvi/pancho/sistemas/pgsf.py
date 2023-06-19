"""Módulo com definições do sistema PGSF."""

import os
from enum import Enum

from bs4 import BeautifulSoup, Comment
from requests import Response
from selectorlib import Extractor

from pycvi.pancho import AuthenticationError, Sistema, preparar_metodo
from pycvi.pancho.utils.texto import formatar_osf, limpar_texto

URL_BASE = "https://portal60.sede.fazenda.sp.gov.br/"
URL_AUTENTICADO = URL_BASE + "wps_migrated/myportal"
URL_ORIGEM_FORM = URL_BASE + "pgsf/pgsfOrigemCorrenteSelecao.do"
URL_OSF_RESULTADO = URL_BASE + "pgsf/pgsftplOsfResultado.do"
URL_CONSULTA_OSF = URL_BASE + "pgsf/pgsftplConsultaOSF.do"
URL_PDF_OSF = URL_BASE + "pgsf/OrdemServicoFiscal.rp?numeroOSF="
URL_PDF_OSF_COMPLETA_GERAL = URL_BASE + "pgsf/EmissaoOSF.rp?IDOSF="
URL_PDF_OSF_COMPLETA_SERV_DIV = URL_BASE + "pgsf/EmissaoOSFServicoDiverso.rp?IDOSF="
URL_CONSULTA_ACIONAMENTO = URL_BASE + "pgsf/pgsftplConsultaAcionamentosFiscais.do"
URL_ANEXAR = URL_BASE + "pgsf/pgsftplOsfAnexarInformacoes.do"
URL_RELATO_RESULTADO_DATAS = URL_BASE + "/pgsf/pgsftplCadastroResultadoOSFDados.do"
URL_RELATO_RESULTADO_SERVICO = (
    URL_BASE + "/pgsf/pgsftplCadastroResultadoOSFServicoDiverso.do"
)
URL_LOGIN = (
    URL_BASE
    + "wps_migrated/portal/!ut/p/b1/"
    + "04_Sj9CPykssy0xPLMnMz0vMAfGjzOKd3R09TMx9DAwsTC0MDTwdPULNzYJdjAxczYEKIoEKDHAARwNC"
    + "-sP1o8BK_PyNQt1MPA0NLcxcDQ2MzDxMnHzCPA3cXYyhCvBY4eeRn5uqX5AbYZBl4qgIAOYYCCY!/dl4"
    + "/d5/L0lDUWtpQ1NZSkNncFJBISEvb0VvZ0FFQ1FRREdJUXBTR0djRndUT0EhLzRHMGhSQjdRUjM1UWhT"
    + "WkNuNnBoL1o3X1RCSzBCQjFBME9ONkEwSTdMSTFNVTUzMEc1LzAvd3BzLnBvcnRsZXRzLmxvZ2lu/"
)

OSFS_POR_PAGINA = 50

PERIODO_TODOS = "-1"

OPERACAO_NENHUMA = "-1"

PLANO_TRABALHO_NENHUM = "-1"


class PgsfSituacaoOSF(Enum):
    """Enumerador com as possíveis situações de uma OSF."""

    SITUACAO_TODOS = "-1"
    SITUACAO_AGUARDANDO_INICIO = "1"
    SITUACAO_CANCELADA = "2"
    SITUACAO_DEVOLVIDA_SEM_EXEC = "4"
    SITUACAO_EM_ESPERA_QUALI_1 = "5"
    SITUACAO_NAO_APROVADA_QUALI_1 = "6"
    SITUACAO_CONCLUIDA = "7"
    SITUACAO_EM_EXEC = "8"
    SITUACAO_EM_ESPERA_ASSINATURA = "9"
    SITUACAO_EM_ESPERA_QUALI_2 = "10"
    SITUACAO_NAO_APROVDA_QUALI_2 = "11"
    SITUACAO_EM_ESPERA_ADIT = "12"
    SITUACAO_EM_ANDAMENTO = "Agr:1"


class Pgsf(Sistema):
    """Representa o sistema [Planejamento e Gestão de Serviços Fiscais (PGSF)](https://portal60.sede.fazenda.sp.gov.br/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=None) -> None:
        """Cria um objeto da classe Pgsf.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self._cookie_iframe_configurado = False
        self._cookie_origem_configurado = False
        self.origem_id = None
        self._url_iframe = None
        self._url_rel_result = None
        self._campos_ocultos = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_AUTENTICADO)
        is_logged_in = "Logout" in r.text
        if is_logged_in and not self._url_rel_result:
            self._update_url_rel_result(r)
        return is_logged_in

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        data = {
            "renderAction": "",
            "tipo": "$LDAP",
            "userID2": usuario,
            "wps.portlets.userid": usuario + "$LDAP",
            "password": senha,
            "ns_Z7_TBK0BB1A0ON6A0I7LI1MU530G5__login.x": "28",
            "ns_Z7_TBK0BB1A0ON6A0I7LI1MU530G5__login.y": "5",
        }

        self.session.post(URL_LOGIN, data=data)

        if not self.autenticado():
            raise AuthenticationError()

        self._configurar_cookie_iframe()
        self._configurar_cookie_origem()
        self._configurar_campos_ocultos()

    @preparar_metodo
    def listar_osfs(
        self,
        periodo: str = PERIODO_TODOS,
        origem: str = "",
        forma_acionamento: str = "",
        operacao: str = OPERACAO_NENHUMA,
        plano_trabalho: str = PLANO_TRABALHO_NENHUM,
        cnpj: str = "",
        ie: str = "",
        setorial: str = "",
        num_osf: str = "",
        protocolo_ua: str = "",
        protocolo_doc: str = "",
        protocolo_ano: str = "",
        situacao: PgsfSituacaoOSF = PgsfSituacaoOSF.SITUACAO_EM_ANDAMENTO,
        pagina=None,
    ) -> list:
        """Lista OSFs em conformidade com os argumentos passados.

        Alguns parâmetros do tipo `str` devem receber os códigos que representam os
        valores desejados na consulta ao PGSF. Os principais códigos estão definidos
        como constantes nessa classe.

        Args:
            periodo (str, opcional): Código do período. Valor padrão é `PERIODO_TODOS`.
            origem (str, opcional): Código da origem.
            forma_acionamento (str, opcional): Código da forma de acionamento.
            operacao (str, opcional): Código da operação. Valor padrão está na constante
                `OPERACAO_NENHUMA`.
            plano_trabalho (str, opcional): Código do plano de trabalho. Valor padrão
                está na constante PLANO_TRABALHO_NENHUM.
            cnpj (str, opcional): CPNJ completo do estabelecimento, com ou sem
                pontuação.
            ie (str, opcional): Inscrição Estadual (IE) do estabelecimento, com ou sem
                pontuação.
            setorial (str, opcional): Código da setorial.
            num_osf (str, opcional): Número completo da OSF, com ou sem pontuação. Valor
                padrão é "".
            protocolo_ua (str, opcional): Número da UA que forma a primeira parte de um
                número de protocolo.
            protocolo_doc (str, opcional): Número do documento que forma a segunda parte
                de um número de protocolo.
            protocolo_ano (str, opcional): Ano que forma a terceira parte de um número
                de protocolo.
            situacao (PgsfSituacaoOSF, opcional): Código da situação. Valores
                disponíveis estão no enumerador `PgsfSituacaoOSF`. Valor padrão é
                `SITUACAO_EM_ANDAMENTO`.
            pagina (int ou list, opcional): Número da página da consulta em que estão as
                OSFs. Também aceita uma lista de ints. Caso nenhum valor seja passado, o
                método retorna todas as OSFs de todas as páginas.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
            TypeError: Erro indicando valor de `pagina` inválido.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            uma OSF.
        """
        if isinstance(pagina, int):
            primeira_pagina = pagina
            demais_paginas = []
        elif isinstance(pagina, list) and len(pagina) > 0:
            primeira_pagina = pagina[0]
            demais_paginas = pagina[1:]
        elif pagina is None:
            primeira_pagina = 1
        else:
            raise TypeError("pagina deve receber um int, uma lista de ints ou None")

        # Requisitando a primeira página
        data = {
            "ACAO": "VISUALIZAR",
            "limparSessao": "",
            "idUA": self._campos_ocultos["idUA"],
            "idFiscalResponsavel": self._campos_ocultos["idFiscalResponsavel"],
            "numUA": self._campos_ocultos["numUA"],
            "uaMovimento": self._campos_ocultos["uaMovimento"],
            "numUsuario": self._campos_ocultos["numUsuario"],
            "login": self._campos_ocultos["login"],
            "uaUsuario": self._campos_ocultos["uaUsuario"],
            "descricaoUAHidden": self._campos_ocultos["descricaoUAHidden"],
            "contraSenhaHidden": self._campos_ocultos["contraSenhaHidden"],
            "idOSFHidden": self._campos_ocultos["idOSFHidden"],
            "tipoDetTrabFiscal": self._campos_ocultos["tipoDetTrabFiscal"],
            "estadoPesquisaAvancada": self._campos_ocultos["estadoPesquisaAvancada"],
            "exibeDiasTrabalhados": self._campos_ocultos["exibeDiasTrabalhados"],
            "txtFiscalResponsavel": self._campos_ocultos["txtFiscalResponsavel"],
            "periodo": periodo,
            "cbOrigem": origem,
            "cbFormaAcionamento": forma_acionamento,
            "cbOperacao": operacao,
            "cbnomePlanoTrabalho": plano_trabalho,
            "cnpj": cnpj,
            "inscEstadual": ie,
            "setorial": setorial,
            "numOsf": num_osf,
            "numProtocoloUA": protocolo_ua,
            "numProtocoloNumDocumento": protocolo_doc,
            "numProtocoloAno": protocolo_ano,
            "situacao": situacao.value,
            "currentPageNumber": str(primeira_pagina),
        }
        r = self.session.post(URL_OSF_RESULTADO, data=data)

        try:
            osfs = Pgsf._extrair_osfs_html(r.text)
        except TypeError:
            raise KeyError("Nenhuma OSF encontrada com os parâmetros passados.")

        # Requisitando demais páginas
        if pagina is None:
            n_paginas = Pgsf._extrair_n_paginas(r.text)
            demais_paginas = range(2, n_paginas + 1)

        for n_pagina in demais_paginas:
            data["currentPageNumber"] = str(n_pagina)
            r = self.session.post(URL_OSF_RESULTADO, data=data)
            osfs += Pgsf._extrair_osfs_html(r.text)

        return osfs

    def obter_osf(self, num_osf: str):
        """Obtém detalhes de uma dada OSF.

        Os campos retornados são os mesmos que aparecem ao se clicar em uma OSF
        diretamente no PGSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.

        Returns:
            Um dicionário que contém as propriedades da OSF.

        """
        detalhes_osf = self.listar_osfs(num_osf=num_osf)[0]
        r = self.session.post(URL_CONSULTA_OSF, data={"idOSF": detalhes_osf["id"]})
        soup = BeautifulSoup(r.text, "html.parser")
        spans = soup.find_all("span", class_="txtcpn")

        for span in spans[6:]:
            td_valor = span.parent.next_sibling.next
            detalhes_osf[span["name"]] = td_valor.text.strip()

        detalhes_osf["servico"] = soup.find(
            string="Serviço"
        ).parent.parent.next_sibling.next_sibling.text.strip()
        detalhes_osf["relato"] = soup.find(
            "td", string="Relato do Serviço Fiscal"
        ).parent.next_sibling.next_sibling.text.strip()

        return detalhes_osf

    def obter_id_osf(self, num_osf: str) -> str:
        """Obtém o identificador de OSF usado internamente pelo PGSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.

        Returns:
            Uma string contendo o identificador.
        """
        return self.listar_osfs(num_osf=num_osf)[0]["id"]

    def obter_pdf_osf(self, num_osf: str, completa: bool = False) -> bytes:
        """Obtém a versão impressa da OSF em PDF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            completa (bool, optional): Se `False`, a versão do contribuinte será gerada.
                Se `True`, a versão completa será gerada.

        Returns:
            `bytes` no formato PDF contendo a versão impressa da OSF.
        """
        if completa:
            osf = self.listar_osfs(num_osf=num_osf)[0]
            if osf["forma_acionamento"] == "Serv Div":
                r = self.session.get(URL_PDF_OSF_COMPLETA_SERV_DIV + osf["id"])
            else:
                r = self.session.get(URL_PDF_OSF_COMPLETA_GERAL + osf["id"])
        else:
            digitos_osf = formatar_osf(osf=num_osf)[0]
            r = self.session.get(URL_PDF_OSF + digitos_osf)

        return r.content

    def relatar_resultado(
        self,
        num_osf: str,
        data_inicio: str = "",
        data_entrega: str = "",
        data_recebimento: str = "",
        data_termino: str = "",
        relato: str = "",
    ) -> None:
        """Registra datas e texto de relato de uma determinada OSF no PGSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            data_inicio (str, optional): Data de início da OSF, no formato DD/MM/AAAA.
            data_entrega (str, optional): Data de entrega da OSF ao contribuinte, no
                formato DD/MM/AAAA.
            data_recebimento (str, optional): Data de recebimento de livros, documentos
                fiscais e outros documentos solicitados da OSF, no formato DD/MM/AAAA.
            data_termino (str, optional): Data de término da OSF, no formato DD/MM/AAAA.
            relato (str, optional): Texto do relato da OSF.
        """
        id_osf = self.obter_id_osf(num_osf=num_osf)

        # Requisitando página "Relatar resultado da ação fiscal"
        data = {"ACAO": "RELATAR_RESULTADO", "idOSF": id_osf}
        r = self.session.post(URL_OSF_RESULTADO, data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        id_contrib = soup.find(id="idContrib")["value"]

        # Inserindo datas
        if data_inicio or data_entrega or data_recebimento or data_termino:
            # Coletando dados atuais da OSF para usar caso algum campo tenha sido
            # passado sem valor
            osf = self.obter_osf(num_osf=num_osf)
            data = {
                "ACAO": "CONFIRMAR",
                "idOSF": id_osf,
                "idContrib": id_contrib,
            }
            data["dtcInicio"] = data_inicio if data_inicio else osf["dataInicioAcao"]
            data["dtcEntregaOSF"] = (
                data_entrega if data_entrega else osf["dtcEntregaOSF"]
            )
            data["dtcEntregaDoc"] = (
                data_recebimento if data_recebimento else osf["dataEntregaDoc"]
            )
            data["dtcTermino"] = data_termino if data_termino else osf["dataFimAcao"]

            # TODO: checar consistências das datas, pois o PGSF falha silenciosamente se
            # as datas não são consistentes

            try:
                # São necessários dois posts para a mesma URL
                r = self.session.post(URL_RELATO_RESULTADO_DATAS, data=data)
                r = self.session.post(URL_RELATO_RESULTADO_DATAS, data=data)
            except UnicodeDecodeError:
                pass

        # Inserindo relato
        if relato:
            data = {
                "ACAO": "CONFIRMAR",
                "idOSF": id_osf,
                "idContrib": id_contrib,
                "txtBxObservacoes": relato.encode("latin1"),
            }

            try:
                r = self.session.post(URL_RELATO_RESULTADO_SERVICO, data=data)
            except UnicodeDecodeError:
                pass

    @preparar_metodo
    def listar_acionamentos(self, ie: str) -> list:
        """Lista os acionamentos atrelados a um estabelecimento.

        Acionamentos são OSFs. A diferença entre listar OSFs usando `listar_osfs` e esse
        método é que esse método é capaz de listar OSFs com qualquer responsável.

        Args:
            ie (str): Inscrição Estadual (IE) do estabelecimento, com ou sem pontuação.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            um acionamento.
        """
        data = {"ACAO": "VISUALIZAR", "numIe": ie, "currentPageNumber": "1"}
        r = self.session.post(URL_CONSULTA_ACIONAMENTO, data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        cabecalho_comment = soup.find(
            string=lambda text: isinstance(text, Comment) and "Cabeçalhos" in text
        )

        # Pegar todos os trs até achar o comentário de rodapé
        proximo_elemento = cabecalho_comment.next
        trs = []

        while not (
            isinstance(proximo_elemento, Comment) and "Rodapé" in proximo_elemento
        ):
            if proximo_elemento.name == "tr":
                trs.append(proximo_elemento)

            proximo_elemento = proximo_elemento.next

        # Pecorrer elementos e colocar acionamentos em uma lista
        acions = []

        for tr in trs[1:-2]:  # Descartando cabeçalho e rodapé
            ac = {}
            tds = tr.find_all("td")
            ac["osf"] = tds[1].a.text.strip()
            ac["id"] = tds[0].input.get("onclick").split("'")[5].strip()
            ac["data_osf"] = tds[1].br.next.text.strip()
            ac["forma_acionamento"] = tds[2].text.strip()
            ac["origem"] = tds[3].text.strip()
            ac["servico"] = tds[4].text.strip()
            ac["NF"] = tds[5].text.strip()
            ac["eq"] = tds[6].text.strip()
            ac["responsavel"] = tds[7].text.strip()
            ac["situacao"] = tds[8].next.text.strip()
            ac["data_situacao"] = tds[8].font.text.strip()
            ac["resultado"] = tds[9].text.strip()

            acions.append(ac)

        return acions

    @preparar_metodo
    def listar_anexos(self, num_osf: str, incluir_codigos: bool = False) -> list:
        """Lista nomes de arquivo e códigos dos anexos de uma dada OSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            incluir_codigos (bool): Se `True`, inclui nos resultados os codigos dos
                anexos (usado internamente pelo PGSF).

        Returns: Se `incluir_codigos == False`, uma lista de nomes de arquivos anexos.
            Se `incluir_codigos == True`, uma lista de `(nome_arquivo, cod_anexo)`,
            onde `nome_arquivo` é o nome do arquivo e `cod_anexo` é o código do anexo.
        """
        id_osf = self.obter_id_osf(num_osf=num_osf)
        r = self.session.get(URL_ANEXAR, params={"idOSF": id_osf})
        anexos = Pgsf._scrape_listar_anexos(r.text)

        if incluir_codigos:
            return anexos
        else:
            return [nome_anexo for nome_anexo, _ in anexos]

    @preparar_metodo
    def baixar_anexo(self, num_osf: str, nome_anexo: str, caminho: str) -> None:
        """Baixa um arquivo anexado a uma dada OSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            nome_anexo (str): Nome do arquivo anexo à OSF que será baixado.
            caminho (str): Caminho completo da pasta onde será salvo o arquivo.
        """
        raise NotImplementedError()

        if nome_anexo not in self.listar_anexos(num_osf=num_osf):
            raise ValueError(f"OSF {num_osf} não possui o anexo {nome_anexo}.")

    @preparar_metodo
    def subir_anexo(self, num_osf: str, caminho: str) -> None:
        """Sobe um arquivo como anexo em uma dada OSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            caminho (str): Caminho completo do arquivo que será anexado.
        """
        id_osf = self.obter_id_osf(num_osf=num_osf)
        data = {"ACAO": "CONFIRMAR_NOVO", "idOSF": id_osf}
        files = {"file": open(caminho, "rb")}

        try:
            self.session.post(URL_ANEXAR, data=data, files=files)
        except UnicodeDecodeError:
            pass

    @preparar_metodo
    def deletar_anexo(self, num_osf: str, nome_anexo: str):
        """Deleta um anexo de uma dada OSF.

        Args:
            num_osf (str): Número completo da OSF, com ou sem pontuação.
            nome_anexo (str): Nome do anexo, incluindo sua extensão se houver.

        Raises:
            KeyError: Erro indicando que OSF ou anexo não foi encontrado.
        """
        anexos = self.listar_anexos(num_osf=num_osf, incluir_codigos=True)
        lista_cod_anexo = [
            id_anx for nome_anx, id_anx in anexos if nome_anx == nome_anexo
        ]

        if not lista_cod_anexo:
            raise KeyError("Anexo não encontrado.")

        cod_anexo = lista_cod_anexo[0]  # TODO: lidar com anexos duplicados
        id_osf = self.obter_id_osf(num_osf=num_osf)
        data = {"ACAO": "EXCLUIR", "idOSF": id_osf, "dataUpload": cod_anexo}

        try:
            self.session.post(URL_ANEXAR, data=data)
        except UnicodeDecodeError:
            pass

    def _obter_url_rel_result(self):
        if not self._url_rel_result:
            r = self.session.get(URL_AUTENTICADO)
            self._update_url_rel_result(r)
        return self._url_rel_result

    def _update_url_rel_result(self, r: Response):
        soup = BeautifulSoup(r.text, "html.parser")
        script_rel_result = soup.find(lambda tag: "Relato de Resultado" in tag.text)
        self._url_rel_result = script_rel_result.text.split('"')[5]

    def _obter_url_iframe(self):
        if not self._url_iframe:
            url_rel_result = self._obter_url_rel_result()
            r = self.session.get(URL_BASE + url_rel_result)
            soup = BeautifulSoup(r.text, "html.parser")
            url_iframe = soup.iframe["src"]
            self._url_iframe = url_iframe
        return self._url_iframe

    def _configurar_cookie_iframe(self) -> None:
        self.session.get(self._obter_url_iframe())
        self._cookie_iframe_configurado = True

    @staticmethod
    def _scrape_obter_cookies_origens(html):
        caminho_yaml = os.path.join(
            os.path.dirname(__file__), "yaml", "pgsf_cookie_origem.yaml"
        )
        e = Extractor.from_yaml_file(caminho_yaml)

        return e.extract(html)

    def _configurar_cookie_origem(self) -> None:
        r = self.session.get(URL_ORIGEM_FORM)
        dados = Pgsf._scrape_obter_cookies_origens(r.text)
        self.origem_id = dados["origem_id"]
        # usar como ID o primeiro ou ultimo ? testando usando o ultimo
        index_id = len(self.origem_id) - 1

        if not self._cookie_iframe_configurado:
            raise Exception(
                "Cookie necessário para realizar essa operação não foi configurado."
            )

        data = {
            "ACAO": "CONFIRMAR_EDITAR",
            "idOrigem": str(self.origem_id[index_id]["id_origem"]),
        }

        try:  # para usuarios da FDT isso não é necessário
            self.session.post(URL_ORIGEM_FORM, data=data)
        except Exception:
            # raise Exception("A configuração do cookie origem falhou.")
            # continuar para nao dar erro no caso de FDT
            pass
        self._cookie_origem_configurado = True

    def _configurar_campos_ocultos(self):
        if not self._cookie_iframe_configurado:
            raise Exception(
                "Cookie necessário para realizar essa operação não foi configurado."
            )

        if not self._campos_ocultos:
            r = self.session.get(self._url_iframe)
            soup = BeautifulSoup(r.text, "html.parser")
            campos_ocultos_comment = soup.find(
                string=lambda text: isinstance(text, Comment)
                and "Componentes Ocultos" in text
            )

            # Pegar todos os inputs até achar um novo comentário
            proximo_elemento = campos_ocultos_comment.next
            inputs = []

            while not isinstance(proximo_elemento, Comment):
                if proximo_elemento.name == "input":
                    inputs.append(proximo_elemento)

                proximo_elemento = proximo_elemento.next

            self._campos_ocultos = {inpt["name"]: inpt["value"] for inpt in inputs}
            self._campos_ocultos

            # Aproveitar para configurar campo necessário, mas que não está oculto
            self._campos_ocultos["txtFiscalResponsavel"] = soup.find(
                id="txtFiscalResponsavel"
            )["value"]

    @staticmethod
    def _extrair_osfs_html(html):
        soup = BeautifulSoup(html, "html.parser")
        detalhe_comment = soup.find(
            string=lambda text: isinstance(text, Comment) and "Linhas Detalhe" in text
        )

        # Pegar todos os trs até achar um novo comentário
        proximo_elemento = detalhe_comment.next
        trs = []

        while not isinstance(proximo_elemento, Comment):
            if proximo_elemento.name == "tr":
                trs.append(proximo_elemento)

            proximo_elemento = proximo_elemento.next

        # Pecorrer elementos e colocar OSFs em uma lista
        osfs = []

        for tr in trs:
            osf = {}
            tds = tr.find_all("td")
            osf["id"] = tds[0].input["value"]
            osf["osf"] = tds[1].a.text.strip()
            osf["data"] = tds[1].br.next.text.strip()
            osf["origem"] = tds[2].text.strip()
            osf["forma_acionamento"] = limpar_texto(tds[3].text)
            osf["razao_social"] = tds[4].next.text.strip()
            osf["ie"] = tds[4].b.text.strip()
            osf["responsavel"] = tds[5].text.strip()
            osf["situacao"] = tds[6].text.strip()
            osfs.append(osf)

        return osfs

    @staticmethod
    def _extrair_n_paginas(html):
        soup = BeautifulSoup(html, "html.parser")
        page_links = soup.find_all("a", class_="pagelinks")

        if not page_links:
            return 1
        else:
            return int(page_links[-1].text)

    @staticmethod
    def _scrape_listar_anexos(html):
        soup = BeautifulSoup(html, "html.parser")
        tds_arquivos = soup.select('td[id*="file_"]')

        return [(td.text, td["id"].removeprefix("file_")) for td in tds_arquivos]

    def osf_restabelecimento_pendente(self, ie: str) -> bool:
        """Consulta se existe uma OSF de Restabelecimento de IE para determinada IE.

        As OSFs de Restabelecimento de IE fazem parte do programa Nos Conformes.

        Args:
            ie (str): Inscrição Estadual (IE) do estabelecimento, com ou sem pontuação.

        Returns:
            True para IE com OSF de Restabelecimento de IE na situação "Em execução" ou
            com OSF de Restabelecimento de IE na situação "Aguardando Início"

            False para IE sem OSF de Restabelecimento de IE  ou
            com OSF de Restabelecimento de IE na situação "Concluída".
        """
        osf_list = self.listar_acionamentos(ie)
        for o in osf_list:
            if (
                "Nos_Conformes - Orientação - Restabelecimento de IE" == o["servico"]
                and "Em execução" in o["situacao"]
            ):
                return True
            elif (
                "Nos_Conformes - Orientação - Restabelecimento de IE" == o["servico"]
                and "Aguardando Início" in o["situacao"]
            ):
                return True
        return False
