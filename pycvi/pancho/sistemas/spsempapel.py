"""Módulo com definições do sistema SP Sem Papel."""
import os
import re
from time import asctime, sleep

from bs4 import BeautifulSoup, Tag
from requests.exceptions import ConnectionError, ProxyError

from pycvi.pancho import AuthenticationError, Sistema, preparar_metodo
from pycvi.pancho.utils.texto import (
    formatar_cep,
    formatar_cnpj,
    formatar_data,
    formatar_ie,
    formatar_osf,
    formatar_sigla_sempapel,
    formatar_sigla_temp_sempapel,
    formatar_usuario_sempapel,
)

URL_BASE = "https://www.documentos.spsempapel.sp.gov.br"
URL_LOGIN = URL_BASE + "/siga/public/app/login"
URL_PADRAO = URL_BASE + "/sigaex/app/expediente"
URL_MESA_JSON_BASE = URL_BASE + "/sigaex/app/mesa2.json?parms="
URL_MODELOS = URL_BASE + "/sigaex/api/v1/modelos/lista-hierarquica"

TIPO_DOCUMENTO_UP = [
    "Ata",
    "Atestado",
    "Auto de Infração",
    "Autorização",
    "Apostila",
    "Balanço",
    "Boletim",
    "Carta",
    "Certidão",
    "Certificado",
    "Comunicado",
    "Contrato",
    "Convênio",
    "Declaração",
    "Despacho",
    "Diária",
    "Edital",
    "E-mail",
    "Extrato",
    "Formulário",
    "Guia",
    "Guia de Recolhimento",
    "Informação",
    "Instrução",
    "Item BEC",
    "Nota de empenho",
    "Nota de lançamento",
    "Nota de reserva",
    "Nota Fiscal",
    "Notificação",
    "Ordem Bancária",
    "Ofício",
    "Orçamento",
    "Parecer",
    "Planilha",
    "Plano de trabalho",
    "Procuração",
    "Proposta",
    "Protocolo",
    "Publicação",
    "Recibo",
    "Relatório",
    "Requerimento",
    "Termo",
    "Outros",
]

TIPO_CONFERENCIA = [
    "Cópia autenticada administrativamente",
    "Cópia autenticada por cartório",
    "Cópia simples",
    "Documento Original",
]


class SpSemPapel(Sistema):
    """Representa o sistema [SP Sem Papel](https://www.documentos.spsempapel.sp.gov.br/).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe SpSemPapel.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE + "/sigaex/app/mesa2ant")
        return "/siga/public/app/logout" in r.text

    def login(self, usuario, senha) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pycvi.pancho/_wiki/wikis/pycvi.pancho-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        usuario = formatar_usuario_sempapel(usuario)
        data = {"username": usuario.upper(), "password": senha}
        r = self.session.post(URL_LOGIN, data=data)  # noqa: F841

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def obter_documento(self, sigla: str) -> dict:
        """Obtém o conjunto de propriedades de um documento.

        Para obter a versão PDF do documento, use o método `baixar_pdf_completo`.

        Args:
            sigla (str): sigla completa do documento.

        Returns:
            Um dicionário que contém as propriedades do documento.
        """
        sigla_curta = formatar_sigla_sempapel(sigla)[0]
        r = self.session.get(URL_PADRAO + "/doc/exibir?sigla=" + sigla_curta)
        soup = BeautifulSoup(r.text, "html.parser")

        # Extrair dados do quadro "Propriedades do Documento"
        propriedades = {}
        div_doc_detalhes = soup.find(id="collapseDocDetalhes")
        for b in div_doc_detalhes.find_all("b"):
            key = b.text[:-1].strip()  # Eliminando o : no final do nome do campo
            value = " ".join(b.next.next.text.split())
            propriedades[key] = value

        # Extrair texto do quadro "Situação do Documento"
        div_situacao_doc = soup.find(id="collapseSituacaoDoc")
        propriedades["Situação"] = " ".join(div_situacao_doc.text.split())

        # Extrair texto do quadro "Nível de Acesso"
        div_nivel_acesso = soup.find(id="collapseNivelAcesso")
        propriedades["Nível de Acesso"] = " ".join(div_nivel_acesso.text.split())

        # Extrair texto do quadro "Tramitação"
        is_mapeada_tramitacao = re.search(
            r"function bigmapTramitacao.*?var\s+input.*?'(.*?)'",
            r.text,
            flags=re.DOTALL,
        )
        if is_mapeada_tramitacao:
            script_tramitacao = is_mapeada_tramitacao.group(1)
            script_tramitacao = re.sub(r'["\s]', "", script_tramitacao)
            propriedades["Tramitação"] = [
                re.split(r"->", t[: t.index("[")])
                for t in script_tramitacao.split(";")
                if "->" in t
            ]
        else:
            propriedades["Tramitação"] = []

        propriedades["Em Tramitação"] = bool(soup.find("a", id="desfazer-tramitacao"))

        # Extrair texto do quadro de Juntadas
        juntadas_tr = soup.find_all("tr", {"class": "juntada"})
        propriedades["Juntadas"] = [
            tr.find_all("td")[3].find("a").text for tr in juntadas_tr
        ]

        # Extrair texto do quadro de Pendências
        div_pendencias = soup.find("div", id="headPendencias")
        if div_pendencias:
            prox = (
                [x for x in list(div_pendencias.next_siblings) if isinstance(x, Tag)]
            )[0]
            propriedades["Pendências"] = [a.text.strip() for a in prox.find_all("a")]
        else:
            propriedades["Pendências"] = []

        return propriedades

    @preparar_metodo
    def criar_documento(
        self,
        modelo: str,
        usuario_mesa: str,
        caminho_pdf=None,
        quem_assina: str = None,
        **kwargs: str,
    ) -> str:
        """Cria um novo documento.

        Args:
            modelo (str): Nome do modelo do documento a ser criado. Deve ser um dos
                modelos listados pelo método `listar_modelos_criar`.
            usuario_mesa (str): Usuário da mesa onde será criado o documento.
            caminho_pdf (str): Caminho do arquivo PDF que será subido ao documento.
                Válido apenas para modelos em que o método `aceita_upload` retorna
                `True`.
            quem_assina (str, optional): Sigla do usuário que assinará o documento. Se
                `None`, o criador do documento é considerado o assinante.
            **kwargs: Demais parâmetros específicos do modelo passado em `modelo`. Os
                parâmetros de cada modelo podem ser consultados pelo método
                `listar_campos`.

        Returns:
            Uma `str` contendo a sigla temporária do documento criado.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
            ValueError: Erro indicando impossibilidade de criar documento do modelo
                informado ou ausência de valor para parâmetro obrigatório do modelo.
        """
        dados_modelo = self.obter_modelo_criar(nome_modelo=modelo)
        modelo_up = SpSemPapel.aceita_upload(dados_modelo=dados_modelo)

        if modelo_up:
            if not caminho_pdf:
                raise ValueError(
                    "Modelo informado necessita do parâmetro 'caminho_pdf'."
                )

            if not os.path.isfile(caminho_pdf):
                raise ValueError(
                    "Arquivo passado no parâmetro 'caminho_pdf' não existe."
                )

            if not caminho_pdf.endswith(".pdf"):
                raise ValueError(
                    "Arquivo passado no parâmetro 'caminho_pdf' deve ser um PDF."
                )

            if (
                "especie" in kwargs
                and kwargs["especie"] == "Outros"
                and "outros" not in kwargs
            ):
                raise ValueError(
                    'O parâmetro "especie" possui o valor "Outros". Nesse caso, é '
                    'obrigatório informar o parâmetro "outros" com um valor válido.'
                )

        # CONFERIR SE OS CAMPOS OBRIGATÓRIOS FORAM PASSADOS
        campos_modelo = self.listar_campos(modelo)
        campos_obrigatorios = {c[0] for c in campos_modelo if c[1]}
        if not campos_obrigatorios.issubset(kwargs):
            raise ValueError(
                "Não foram passados valores de campos obrigatórios ao modelo.\n"
                f"Campos obrigatorios: {campos_obrigatorios}"
                f"Campos passados: {set(kwargs)}"
            )

        # INDO PRA MESA ADEQUADA, PRA CAPTURAR OS IDENTIFICADORES CORRETOS
        usuario_mesa_curto = formatar_usuario_sempapel(usuario_mesa)
        self._trocar_mesa(usuario_mesa=usuario_mesa_curto)

        # CRIAR NOVO, SELECIONO O MODELO
        r = self.session.get(
            URL_PADRAO
            + "/doc/editar?modelo="
            + dados_modelo["idModelo"]
            + "&criandoAnexo=false&criandoSubprocesso=false"
        )

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO
        (
            usuario_id,
            usuario_nome,
            classificacao_id,
            classificacao_desc,
            classificacao_sigla,
            _,
            _,
            _,
        ) = SpSemPapel._extrair_dados_doc(r.text)

        # SE UM TERCEIRO FOR ASSINAR, CAPTURO OS DADOS DO USUÁRIO
        if quem_assina is not None:
            dados_assinante = SpSemPapel._obter_dados_usuario(self, quem_assina)
            usuario_id = dados_assinante[0]
            usuario_nome = dados_assinante[1]
            usuario_mesa_curto = formatar_usuario_sempapel(dados_assinante[2])

        # TRANSFORMANDO O DICIONÁRIO EM LISTA DE TUPLAS
        kwargs_list = []
        if kwargs:
            for key, value in kwargs.items():
                kwargs_list += [("vars", key), (key, value)]

        # GRAVAR FORMULÁRIO DE INCLUSÃO DE DOCUMENTO
        data = [
            ("exDocumentoDTO.idMod.original", dados_modelo["idModelo"]),
            ("exDocumentoDTO.idMod", dados_modelo["idModelo"]),
            ("exDocumentoDTO.tamanhoMaximoDescricao", "4000"),
            ("hasPai", "false"),
            ("isPaiEletronico", "false"),
            ("postBack", "1"),
            ("campos", "criandoAnexo"),
            ("campos", "criandoSubprocesso"),
            ("campos", "autuando"),
            ("exDocumentoDTO.autuando", "false"),
            ("exDocumentoDTO.criandoAnexo", "false"),
            ("exDocumentoDTO.criandoSubprocesso", "false"),
            ("campos", "idMobilAutuado"),
            ("cliente", "GOVSP"),
            ("campos", "idTpDoc"),
            ("campos", "dtDocString"),
            ("campos", "nivelAcesso"),
            ("exDocumentoDTO.nivelAcesso", "3"),
            ("campos", "eletronico"),
            ("exDocumentoDTO.eletronico", "1"),
            ("campos", "nmFuncaoSubscritor"),
            ("campos", "tipoDestinatario"),
            ("exDocumentoDTO.tipoDestinatario", "2"),
            ("campos", "lotacaoDestinatarioSel.id"),
            ("campos", "classificacaoSel.id"),
            ("exDocumentoDTO.classificacaoSel.id", classificacao_id),
            ("exDocumentoDTO.classificacaoSel.descricao", classificacao_desc),
            ("campos", "subscritorSel.id"),
            ("campos", "substituicao"),
            ("campos", "personalizacao"),
            ("exDocumentoDTO.subscritorSel.id", usuario_id),
            ("exDocumentoDTO.subscritorSel.descricao", usuario_nome),
            ("exDocumentoDTO.subscritorSel.sigla", usuario_mesa_curto),
        ] + kwargs_list

        if modelo_up:
            data += [
                ("exDocumentoDTO.idTpDoc", "4"),
                ("exDocumentoDTO.classificacaoSel.sigla", classificacao_sigla),
                ("campos", "descrDocumento"),
                ("arquivo", caminho_pdf.split("\\")[-1]),
            ]
            files = {"arquivo": (caminho_pdf.split("\\")[-1], open(caminho_pdf, "rb"))}
        else:
            data += [
                ("exDocumentoDTO.idTpDoc", "1"),
                ("exDocumentoDTO.preenchimento", "0"),
                ("campos", "titularSel.id"),
            ]
            files = None

        r = self.session.post(URL_PADRAO + "/doc/gravar", data=data, files=files)

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO TEMP GERADO
        soup = BeautifulSoup(r.text, "html.parser")
        temp_sigla = soup.find(id="marcarForm").find("input", {"name": "sigla"})[
            "value"
        ]

        return temp_sigla

    @preparar_metodo
    def incluir_documento(
        self,
        modelo: str,
        sigla_pai: str,
        usuario_mesa: str,
        caminho_pdf=None,
        quem_assina: str = None,
        **kwargs: str,
    ) -> str:
        """Inclui um documento em um documento já criado.

        Args:
            modelo (str): Nome do modelo do documento a ser incluído. Deve ser um dos
                modelos listados pelo método `listar_modelos_incluir`.
            sigla_pai (str): Sigla completa do documento pai onde será incluído o
                documento.
            usuario_mesa (str): Usuário da mesa onde será incluído o documento.
            caminho_pdf (str): Caminho do arquivo PDF que será subido ao documento.
                Válido apenas para modelos em que o método `aceita_upload` retorna
                `True`.
            quem_assina (str, optional): Sigla do usuário que assinará o documento. Se
                `None`, o criador do documento é considerado o assinante.
            **kwargs: Demais parâmetros específicos do modelo passado em `modelo`. Os
                parâmetros de cada modelo podem ser consultados pelo método
                `listar_campos`.

        Returns:
            Uma `str` contendo a sigla temporária do documento incluído.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
            ValueError: Erro indicando impossibilidade de incluir documento do
                modelo indicado dentro do sigla_pai informado ou ausência de valor
                para parâmetro obrigatório do modelo.
        """
        dados_modelo = self.obter_modelo_incluir(
            nome_modelo=modelo, sigla_pai=sigla_pai
        )
        modelo_up = SpSemPapel.aceita_upload(dados_modelo=dados_modelo)

        if modelo_up:
            if not caminho_pdf:
                raise ValueError(
                    "Modelo informado necessita do parâmetro 'caminho_pdf'."
                )

            if not os.path.isfile(caminho_pdf):
                raise ValueError(
                    "Arquivo passado no parâmetro 'caminho_pdf' não existe."
                )

            if not caminho_pdf.endswith(".pdf"):
                raise ValueError(
                    "Arquivo passado no parâmetro 'caminho' deve ser um PDF."
                )

            if (
                "especie" in kwargs
                and kwargs["especie"] == "Outros"
                and "outros" not in kwargs
            ):
                raise ValueError(
                    'O parâmetro "especie" possui o valor "Outros". Nesse caso, é '
                    'obrigatório informar o parâmetro "outros" com um valor válido.'
                )

        # CONFERIR SE OS CAMPOS OBRIGATÓRIOS FORAM PASSADOS
        campos_modelo = self.listar_campos(modelo, sigla_pai)
        campos_obrigatorios = {c[0] for c in campos_modelo if c[1]}
        if not campos_obrigatorios.issubset(kwargs):
            raise ValueError(
                "Não foram passados valores de campos obrigatórios ao modelo.\n"
                f"Campos obrigatorios: {campos_obrigatorios}\n"
                f"Campos passados: {set(kwargs)}"
            )

        # INDO PRA MESA ADEQUADA, PRA CAPTURAR OS IDENTIFICADORES CORRETOS
        usuario_sigla = formatar_usuario_sempapel(usuario_mesa)
        r = self._trocar_mesa(usuario_mesa=usuario_sigla)

        # CRIAR NOVO, SELECIONO O MODELO
        sigla_pai_curta = formatar_sigla_sempapel(sigla_pai)[0]
        r = self.session.get(
            URL_PADRAO
            + "/doc/editar?modelo="
            + dados_modelo["idModelo"]
            + "&mobilPaiSel.sigla="
            + sigla_pai_curta
            + "&criandoAnexo=true&criandoSubprocesso=false"
        )

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO
        (
            usuario_id,
            usuario_nome,
            classificacao_id,
            classificaçao_desc,
            classificaçao_sigla,
            documento_id,
            doc_desc_curta,
            doc_desc_longa,
        ) = SpSemPapel._extrair_dados_doc(r.text)

        # SE UM TERCEIRO FOR ASSINAR, MUDO O USUARIO_MESA
        if quem_assina is not None:
            dados_assinante = SpSemPapel._obter_dados_usuario(self, quem_assina)
            usuario_id = dados_assinante[0]
            usuario_nome = dados_assinante[1]
            usuario_sigla = dados_assinante[2]

        # TRANSFORMANDO O DICIONÁRIO EM LISTA DE TUPLAS
        kwargs_list = []
        if kwargs:
            for key, value in kwargs.items():
                kwargs_list += [("vars", key), (key, value)]

        # GRAVAR FORMULÁRIO DE INCLUSÃO DE DOCUMENTO
        data = [
            ("exDocumentoDTO.tamanhoMaximoDescricao", "4000"),
            ("hasPai", "true"),
            ("isPaiEletronico", "true"),
            ("postBack", "1"),
            ("campos", "criandoAnexo"),
            ("campos", "criandoSubprocesso"),
            ("campos", "autuando"),
            ("exDocumentoDTO.autuando", "false"),
            ("exDocumentoDTO.criandoSubprocesso", "false"),
            ("campos", "idMobilAutuado"),
            ("exDocumentoDTO.idMod.original", dados_modelo["idModelo"]),
            ("exDocumentoDTO.idMod", dados_modelo["idModelo"]),
            ("cliente", "GOVSP"),
            ("campos", "idTpDoc"),
            ("campos", "dtDocString"),
            ("campos", "nivelAcesso"),
            ("exDocumentoDTO.nivelAcesso", "3"),
            ("campos", "eletronico"),
            ("exDocumentoDTO.eletronico", "1"),
            ("campos", "nmFuncaoSubscritor"),
            ("campos", "tipoDestinatario"),
            ("exDocumentoDTO.tipoDestinatario", "2"),
            ("campos", "lotacaoDestinatarioSel.id"),
            ("campos", "classificacaoSel.id"),
            ("exDocumentoDTO.classificacaoSel.id", classificacao_id),
            ("exDocumentoDTO.classificacaoSel.descricao", classificaçao_desc),
            ("exDocumentoDTO.classificacaoSel.sigla", classificaçao_sigla),
            ("exDocumentoDTO.descrDocumento", doc_desc_longa),
            ("campos", "titularSel.id"),
            ("campos", "descrDocumento"),
            ("exDocumentoDTO.mobilPaiSel.id", documento_id),
            ("exDocumentoDTO.mobilPaiSel.descricao", doc_desc_curta),
            ("exDocumentoDTO.criandoAnexo", "true"),
            ("exDocumentoDTO.desativarDocPai", "sim"),
            ("campos", "subscritorSel.id"),
            ("campos", "substituicao"),
            ("campos", "personalizacao"),
            ("exDocumentoDTO.subscritorSel.id", usuario_id),
            ("exDocumentoDTO.subscritorSel.descricao", usuario_nome),
            ("exDocumentoDTO.subscritorSel.sigla", usuario_sigla),
        ] + kwargs_list

        if modelo_up:
            data += [
                ("exDocumentoDTO.idTpDoc", "4"),
                ("arquivo", caminho_pdf.split("\\")[-1]),
            ]
            files = {"arquivo": (caminho_pdf.split("\\")[-1], open(caminho_pdf, "rb"))}
        else:
            data += [
                ("desconsiderarExtensao", "false"),
                ("exDocumentoDTO.idTpDoc", "1"),
                ("exDocumentoDTO.preenchimento", "0"),
            ]
            files = None

        r = self.session.post(URL_PADRAO + "/doc/gravar", data=data, files=files)

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO TEMP GERADO
        soup = BeautifulSoup(r.text, "html.parser")
        temp_sigla = soup.find(id="marcarForm").find_all("input")[0]["value"]

        return temp_sigla

    @preparar_metodo
    def assinar_documento(self, sigla_temp, usuario, senha) -> str:
        """Assina um documento.

        Aplicável apenas a documentos de modelos em que o método `aceita_upload` retorna
        `False`. Documentos de modelos com suporte a upload de arquivos (aqueles que
        `aceita_upload` retorna `True`), podem ser autenticados pelo método
        `autenticar_documento`.

        Args:
            sigla_temp (str): Sigla completa do documento a ser assinado. Deve ser
                uma sigla de documento temporário (inicia com `TMP-`).
            usuario (str): Usuário que assinará o documento.
            senha (str): Senha do usuário que assinará o documento.

        Returns:
            Uma `str` contendo a sigla definitiva do documento assinado.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        return self._assinar_ou_autenticar(sigla_temp, usuario, senha, assinar=True)

    @preparar_metodo
    def cancelar_documento_assinado(self, sigla: str, motivo: str) -> None:
        """Cancela um documento já assinado anteriormente.

        Documentos não assinados (ou seja, aqueles que possuem siglas que iniciam com
            `TMP-`) não podem ser cancelados, mas podem ser excluídos pelo método
            `excluir_documento_temp`.

        Args:
            sigla (str): sigla completa do documento a ser cancelado. Não deve iniciar
                com `TMP-`
            motivo (str): motivo do cancelamento.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        documento_curto = formatar_sigla_sempapel(sigla)[0]

        # MARCANDO PARA CANCELAR
        r = self.session.get(
            URL_PADRAO + "/doc/tornarDocumentoSemEfeito?sigla=" + documento_curto + "&"
        )

        data = {
            "postback": "1",
            "sigla": sigla,
            "campos": "titularSel.id",
            "descrMov": motivo,
        }
        r = self.session.post(  # noqa: F841
            URL_PADRAO + "/doc/tornarDocumentoSemEfeitoGravar",
            data=data,
        )

    @preparar_metodo
    def autenticar_documento(self, sigla_temp, usuario, senha):
        """Autentica um documento.

        Aplicável apenas a documentos de modelos em que o método `aceita_upload` retorna
        `True`. Documentos de modelos sem suporte a upload de arquivos (aqueles que
        `aceita_upload` retorna `False`), podem ser assinados pelo método
        `assinar_documento`.

        Args:
            sigla_temp (str): Sigla completa do documento a ser autenticado. Deve ser
                uma sigla de documento temporário (inicia com `TMP-`).
            usuario (str): Usuário que autenticará o documento.
            senha (str): Senha do usuário que autenticará o documento.

        Returns:
            Uma `str` contendo a sigla definitiva do documento autenticado.
        """
        return self._assinar_ou_autenticar(sigla_temp, usuario, senha, assinar=False)

    @preparar_metodo
    def finalizar_documento(self, sigla_temp):
        """Finaliza um documento.

        Args:
            sigla_temp (str): Sigla completa do documento a ser finalizado. Deve ser
                uma sigla de documento temporário (inicia com `TMP-`).

        Returns:
            Uma `str` contendo a sigla definitiva do documento finalizado.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        sigla_temp = formatar_sigla_temp_sempapel(sigla_temp)[0]

        r = self.session.get(
            URL_PADRAO + "/doc/finalizar?sigla=" + sigla_temp + "&",
        )

        r = self.session.get(URL_PADRAO + "/doc/exibir?sigla=" + sigla_temp)

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO ASSINADO
        soup = BeautifulSoup(r.text, "html.parser")
        try:
            documento_sigla = soup.find(id="marcarForm").find(
                "input", {"name": "sigla"}
            )["value"]
        except Exception:
            raise Exception("Falha ao finalizar.")

        return documento_sigla

    @preparar_metodo
    def excluir_documento_temp(self, sigla_temp: str) -> None:
        """Exclui um documento temporário (não assinado).

        Documentos assinados (ou seja, aqueles que possuem siglas que não iniciam com
            `TMP-`) não podem ser excluídos, mas podem ser cancelados pelo método
            `cancelar_documento_assinado`.

        Args:
            sigla (str): sigla completa do documento a ser excluído. Deve iniciar com
                `TMP-`.

        Raises:
            AuthenticationError: Erro indicando que o sistema não está autenticado.
        """
        documento_curto = formatar_sigla_temp_sempapel(sigla_temp)[0]

        # EXCLUINDO DOCUMENTO
        r = self.session.get(  # noqa: F841
            URL_PADRAO + "/doc/excluir?sigla=" + documento_curto + "&"
        )

    @preparar_metodo
    def juntar(self, sigla_pai: str, sigla_filho: str):
        """Junta um documento filho a um documento pai.

        Ambos os documentos não podem ser temporários (sigla iniciada com `TMP-`).

        Args:
            sigla_pai (str): Sigla completa do documento pai.
            sigla_filho (str): Sigla completa do documento filho.
        """
        sigla_pai_curta = formatar_sigla_sempapel(sigla_pai)[0]
        sigla_filho_curta = formatar_sigla_sempapel(sigla_filho)[0]

        # CAPTURANDO DADOS DA JUNTADA
        r = self.session.get(
            URL_PADRAO + "/selecionar?propriedade=documentoRef&sigla=" + sigla_pai_curta
        )
        postback, documento_id, _, documento_descriçao = r.text.split(";")

        # JUNTANDO
        data = {
            "postback": postback,
            "sigla": sigla_filho_curta,
            "idDocumentoEscolha": "1",
            "documentoRefSel.id": documento_id,
            "documentoRefSel.descricao": documento_descriçao,
            "documentoRefSel.sigla": sigla_pai_curta,
        }
        r = self.session.post(URL_PADRAO + "/mov/juntar_gravar", data=data)

    @preparar_metodo
    def desfazer_juntada(self, sigla: str):
        """Desfaz a juntada de um documento.

        Args:
            sigla (str): Sigla completa do documento.
        """
        sigla_curta = formatar_sigla_sempapel(sigla)[0]
        r = self.session.get(  # noqa: F841
            URL_PADRAO + "/mov/cancelarMovimentacao?sigla=" + sigla_curta
        )

    @preparar_metodo
    def obter_sigla_pai(self, sigla_filho: str):
        """Obtém sigla do documento pai de um dado documento filho.

        Args:
            sigla_filho (str): Sigla completa do documento filho.

        Returns:
            A sigla completa do documento pai.

        Raises:
            Exception: Erro indicando que não foi possível obter a sigla do documento
                pai, possivelmente porque o documento passado em `sigla_filho` não tem
                um pai.
        """
        try:
            sigla_curta = formatar_sigla_sempapel(sigla_filho)[0]
        except ValueError:
            sigla_curta = formatar_sigla_temp_sempapel(sigla_filho)[0]

        r = self.session.get(URL_PADRAO + "/doc/exibir?sigla=" + sigla_curta)
        soup = BeautifulSoup(r.text, "html.parser")

        try:
            return soup.find("div", id="outputRelacaoDocs").li.text.strip()
        except Exception:
            raise Exception(
                f"Não foi possível obter a sigla do documento pai de {sigla_filho}"
            )

    @preparar_metodo
    def anotar(self, sigla: str, anotacao: str):
        """Adiciona anotações a um documento.

        De acordo com o sistema, *"anotações cadastradas não constituem o
        documento, são apenas lembretes ou avisos para os usuários com acesso ao
        documento, podendo ser excluídas a qualquer tempo."*

        Args:
            sigla (str): Sigla completa do documento.
            anotacao (str): Texto da anotação.
        """
        sigla_curta = formatar_sigla_temp_sempapel(sigla)[0]
        data = [
            ("postback", "1"),
            ("sigla", sigla_curta),
            ("campos", "titularSel.id"),
            ("campos", "nmFuncaoSubscritor"),
            ("descrMov", anotacao),
        ]
        r = self.session.post(  # noqa: F841
            URL_PADRAO + "/mov/anotar_gravar",
            data=data,
        )

    @preparar_metodo
    def tramitar(
        self,
        sigla: str,
        ua_destino: str = "",
        usuario_destino: str = "",
        data_devoluçao: str = "",
    ) -> None:
        """Tramita o documento para uma Unidade Administrativa (UA) ou usuário.

        Args:
            sigla (str): Sigla completa do documento a ser tramitado.
            ua_destino (str): UA para onde o documento será tramitado. Deve ser `None`
                se o parâmetro `usuario_destino` não for `None`.
            usuario_destino (str): Usuário para onde o documento será tramitado. Deve
                ser `None` se o parâmetro `ua_destino` não for `None`.

        Raises:
            ValueError: Erro indicando que ambos `ua_destino` e `usuario_destino` não
            são `None`.
        """
        sigla_curta = formatar_sigla_sempapel(sigla)[0]

        if ua_destino and usuario_destino:
            raise ValueError(
                "Informar apenas ua_destino ou usuario_destino, não ambos."
            )

        if ua_destino:
            alvo = formatar_usuario_sempapel(ua_destino)
            sublink1 = "lotacao"
            sublink2 = "lotaResponsavel"
            tipoResponsavel = "1"
        elif usuario_destino:
            alvo = formatar_usuario_sempapel(usuario_destino)
            sublink1 = "pessoa"
            sublink2 = "responsavel"
            tipoResponsavel = "2"
        else:
            raise ValueError("Informar ua_destino ou usuario_destino")

        if data_devoluçao:
            data_devoluçao = formatar_data(
                data=data_devoluçao, formato_saida="%d/%m/%Y"
            )

        # CAPTURANDO DADOS DO DESTINO
        complemento = (
            f"/siga/app/{sublink1}/selecionar?propriedade={sublink2}&sigla={alvo}"
        )
        r = self.session.get(URL_BASE + complemento)
        if r.text == "0":
            raise ValueError(
                f"Não foi encontrada unidade ou usuário com a sigla {usuario_destino}"
                if usuario_destino
                else f"Não foi encontrada unidade ou usuário com a sigla {ua_destino}"
            )
        postback = r.text.split(";")[0]
        resp_id = r.text.split(";")[1]
        resp_sigla = r.text.split(";")[2]
        resp_descriçao = r.text.split(";")[3]

        data = {
            "postback": postback,
            "docFilho": "true",
            "sigla": sigla_curta,
            "tipoTramite": 3,
            "tipoResponsavel": tipoResponsavel,
            f"{sublink2}Sel.id": resp_id,
            f"{sublink2}Sel.descricao": resp_descriçao,
            f"{sublink2}Sel.sigla": resp_sigla,
            "dtDevolucaoMovString": data_devoluçao,
        }

        # JUNTANDO
        r = self.session.post(  # noqa: F841
            URL_PADRAO + "/mov/transferir_gravar",
            data=data,
        )

    @preparar_metodo
    def cancelar_tramitacao(self, sigla: str) -> None:
        """Cancela a tramitação de um documento.

        Args:
            sigla (str): Sigla completa do documento a ter sua tramitação cancelada.
        """
        sigla_curta = formatar_sigla_sempapel(sigla)[0]
        r = self.session.get(  # noqa: F841
            URL_PADRAO + "/mov/cancelarMovimentacao?sigla=" + sigla_curta
        )

    @preparar_metodo
    def listar_campos(self, modelo: str, sigla_pai: str = None) -> list:
        """Lista os nomes dos campos de um modelo de documento.

        Os nomes dos campos, juntamente com seus valores, podem posteriormente ser
        passados para o parâmetro `kwargs` dos métodos `criar_documento` e
        `incluir_documento`.

        Args:
            modelo (str): Nome do modelo do documento. Deve ser um dos modelos listados
                pelo método `listar_modelos_criar` ou `listar_modelos_incluir`.
            sigla_pai (str, optional): Sigla completa do documento pai. Obrigatório para
                modelos listados pelo método `listar_modelos_incluir`.

        Returns:
            Retorna uma lista de tuplas no formato `(campo, obrigatorio)`, onde `campo`
            é o nome do campo e `obrigatório` é um `bool` indicando o se o campo é
            obrigatório.

        Raises:
            ValueError: Erro indicando que não foi passado valor para o parâmetro
                `sigla_pai` quando esse era necessário.
        """
        url_modelo = URL_PADRAO + "/doc/editar?modelo="

        if not sigla_pai:
            dict_modelos = self.listar_modelos_criar()
            params = list(
                filter(
                    lambda x: modelo.upper().strip() == x["nome"].upper().strip(),
                    dict_modelos,
                )
            )[0]

            try:
                cod_modelo = params["idModelo"]

                url_modelo += (
                    cod_modelo + "&criandoAnexo=false&criandoSubprocesso=false"
                )

            except Exception:
                raise ValueError(
                    "Não é possível criar_documento com o modelo informado."
                    + " Se for o caso, veja se faltou informar sigla_pai"
                )

        else:
            dict_modelos = self.listar_modelos_incluir(sigla_pai)
            params = list(
                filter(
                    lambda x: modelo.upper().strip() == x["nome"].upper().strip(),
                    dict_modelos,
                )
            )[0]

            try:
                cod_modelo = params["idModelo"]

                sigla_pai_curta = formatar_sigla_sempapel(sigla_pai)[0]
                url_modelo += (
                    cod_modelo
                    + "&mobilPaiSel.sigla="
                    + sigla_pai_curta
                    + "&criandoAnexo=true&criandoSubprocesso=false"
                )

            except Exception:
                raise ValueError(
                    "Não é possível incluir_documento do modelo informado no"
                    + " sigla_pai informado."
                )

        r = self.session.get(url_modelo)

        # LISTANDO OS INPUTS OBRIGATÓRIOS
        soup = BeautifulSoup(r.text, "html.parser")
        ipt_list = [
            (ipt["value"], True)
            for ipt in soup.find("span", id="spanEntrevista").find_all(
                "input", {"name": "obrigatorios"}
            )
        ]

        # CONCATENANDO OS CASOS DE CAIXAS DE TEXTO QUE NÃO APARECEM COMO OBRIGATÓRIAS
        ipt_list += [
            (ipt["id"], True)
            for ipt in soup.find("span", id="spanEntrevista").find_all("textarea")
        ]

        # CONCATENANDO OS INPUTS OPCIONAIS
        ipt_list += [
            (ipt["value"], False)
            for ipt in soup.find("span", id="spanEntrevista").find_all(
                "input", {"name": "vars"}
            )
            if (ipt["value"], True) not in ipt_list
        ]

        return ipt_list

    @preparar_metodo
    def listar_modelos_criar(self) -> list:
        """Lista modelos de documento que podem ser criados pelo método `criar_documento`.

        Para listar modelos que podem ser usados com o método `incluir_documento`,
        consulte o método `listar_modelos_incluir`.

        Returns:
            Uma lista de dicionários, onde cada dicionário contém dados de um modelo.
        """  # noqa: E501
        r = self.session.get(URL_MODELOS)

        return r.json()["list"]

    @preparar_metodo
    def listar_modelos_incluir(self, sigla_pai: str) -> list:
        """Lista modelos de documento que podem ser incluídos pelo método `incluir_documento`.

        Para listar modelos que podem ser usados com o método `criar_documento`,
        consulte o método `listar_modelos_criar`.

        Args:
            sigla_pai (str): Sigla completa do documento pai.

        Returns:
            Uma lista de dicionários, onde cada dicionário contém dados de um modelo.
        """  # noqa: E501
        params = {"isEditandoAnexo": "true", "siglaMobPai": sigla_pai}
        r = self.session.get(URL_MODELOS, params=params)

        return r.json()["list"]

    @preparar_metodo
    def obter_modelo_criar(self, nome_modelo: str) -> dict:
        """Obtém dados de um modelo de documento que pode ser criado pelo método `criar_documento`.

        Para obter os dados de um modelo que pode ser usado com o método
        `incluir_documento`, consulte o método `obter_modelo_incluir`.

        Args:
            nome_modelo (str): Nome do modelo.

        Returns:
            Um dicionário contendo os dados do modelo.
        """  # noqa: E501
        nome_modelo_lower = nome_modelo.lower()
        modelos = self.listar_modelos_criar()

        for m in modelos:
            if m["nome"].lower() == nome_modelo_lower:
                return m

        raise ValueError(
            "Nome de modelo inexistente. Se sua intenção é obter dados de um modelo que"
            " pode ser usado com o método incluir_documento, utilize o método "
            "obter_modelo_incluir."
        )

    @preparar_metodo
    def obter_modelo_incluir(self, nome_modelo: str, sigla_pai: str) -> dict:
        """Obtém dados de um modelo de documento que pode ser criado pelo método `incluir_documento`.

        Para obter os dados de um modelo que pode ser usado com o método
        `criar_documento`, consulte o método `obter_modelo_criar`.

        Args:
            nome_modelo (str): Nome do modelo.
            sigla_pai (str): Sigla completa do documento pai.

        Returns:
            Um dicionário contendo os dados do modelo.
        """  # noqa: E501
        nome_modelo_lower = nome_modelo.lower()
        modelos = self.listar_modelos_incluir(sigla_pai=sigla_pai)

        for m in modelos:
            if m["nome"].lower() == nome_modelo_lower:
                return m

        raise ValueError(
            "Nome de modelo inexistente ou modelo incompatível com modelo pai. Se sua "
            "intenção é obter dados de um modelo que pode ser usado com o método "
            "criar_documento, utilize o método obter_modelo_criar."
        )

    @staticmethod
    def aceita_upload(dados_modelo: dict) -> bool:
        """Verifica se um modelo de documento aceita upload de arquivos.

        Args:
            dados_modelo (dict): dicionário de dados do modelo, obtido pelos métodos
                `obter_modelo_criar` ou `obter_modelo_incluir`.

        Returns:
            Um booleano com `True` se o modelo aceita upload e `False` se não.
        """
        return (
            "capturad" in dados_modelo["descr"].lower()
            or "digitalizad" in dados_modelo["descr"].lower()
        )

    @preparar_metodo
    def baixar_pdf_completo(self, sigla: str, caminho: str) -> None:
        """Baixa a versão completa em PDF de um documento.

        Args:
            sigla (str): Sigla completa do documento a ser baixado.
            caminho (str): Caminho completo onde deverá ser salvo o arquivo, incluindo
                seu nome. Deve terminar com .pdf.
        """
        sigla_curta = formatar_sigla_sempapel(sigla)[0]

        # REQUISITO A PÁGINA COM O PDF
        r = self.session.get(
            URL_BASE
            + "/sigaex/app/arquivo/exibir?idVisualizacao=&iframe=true&arquivo="
            + sigla_curta
            + ".pdf&completo=1&sigla="
            + sigla_curta
        )

        # ALGUNS PROCESSOS MUITO GRANDES DEMORAM PARA SEREM GERADOS
        partes_url = r.url.split("/")
        codigo = partes_url[partes_url.index(sigla_curta) + 1]
        while "PDF completo gerado" not in r.text:
            r = self.session.get(URL_BASE + "/sigaex/api/v1/status/" + codigo)

        r = self.session.get(
            URL_BASE
            + "/sigaex/api/v1/download/"
            + partes_url[-2]
            + "/"
            + partes_url[-1],
        )

        with open(caminho, "wb") as f:
            f.write(r.content)

    @preparar_metodo
    def criar_205P(
        self,
        usuario_mesa: str,
        senha: str,
        ie: str,
        cnpj: str,
        razao_social: str,
        data_diligência: str,
        osf: str,
        logradouro: str,
        numero: int,
        bairro: str,
        municipio: str,
        cep: str,
        texto_quadro4: str,
        complemento_end: str = "",
        uf: str = "SP",
    ) -> str:
        """Cria um processo 2.05P completo.

        Args:
            usuario_mesa (str): Usuário da mesa onde será criado o processo.
            senha (str): Senha do usuário que assinará os documentos.
            ie (str): Inscrição Estadual do estabelecimento.
            cnpj (str): CNPJ da empresa.
            razao_social (str): Razão social da empresa.
            data_diligência (str): Data da diligência. Note que esse parâmetro
                possui a letra "ê" em seu nome.
            osf (str): Número da OSF.
            logradouro (str): Nome do logradouro.
            numero (int): Número do logradouro.
            bairro (str): Bairro do endereço.
            municipio (str): Município do endereço.
            cep (str): CEP do endereço.
            texto_quadro4 (str): Texto a ser incluído no Quadro 4.
            complemento_end (str, optional): Complemento do endereço.
            uf (str, optional): Sigla do estado do endereço. Valor padrão é "SP".

        Returns:
            Um `str` contendo a sigla do processo.
        """
        # ALGUNS PARÂMETROS PADRÃO PARA ESSA ROTINA
        modelo_pai = "Expediente de verificação fiscal"
        modelo_filho = "ROTEIRO 2.05-P - NÃO LOCALIZAÇÃO - PROGRAMA NOS CONFORMES"
        comp_assunto = "NOS CONFORMES - DECLARAÇÃO DE NÃO LOCALIZAÇÃO - 2.05P"
        situacao = "SUSPENSA PREVENTIVAMENTE"

        # FORMATANDO VARIÁVEIS
        ie_char = formatar_ie(ie)[1]
        cnpj_char = formatar_cnpj(cnpj)[1]
        osf_char = formatar_osf(osf)[1]
        data_diligência = formatar_data(data_diligência, "%d/%m/%Y")
        cep = formatar_cep(cep)[1]

        # CRIA PROTOCOLO
        sigla_temp_pai = self.criar_documento(
            usuario_mesa=usuario_mesa,
            modelo=modelo_pai,
            complemento_do_assunto=comp_assunto,
            interessado_nome=razao_social,
            interessado_ie=ie_char,
            interessado_cnpj=cnpj_char,
        )

        # ASSINA PROTOCOLO
        sigla_pai = self.assinar_documento(
            sigla_temp=sigla_temp_pai, usuario=usuario_mesa, senha=senha
        )

        # CRIA 2.05P
        sigla_temp_filho = self.incluir_documento(
            modelo=modelo_filho,
            sigla_pai=sigla_pai,
            usuario_mesa=usuario_mesa,
            complemento_do_assunto=comp_assunto,
            interessado_ie=ie_char,
            interessado_cnpj=cnpj_char,
            interessado_nome=razao_social,
            data_da_visita=data_diligência,
            numero_osf=osf_char,
            interessado_logradouro=logradouro,
            interessado_numero=numero,
            interessado_endereco_complemento=complemento_end,
            interessado_bairro=bairro,
            interessado_municipio=municipio,
            interessado_municipio_uf=uf,
            interessado_cep=cep,
            condicao_da_empresa=situacao,
            texto_documento=texto_quadro4,
        )

        # ASSINA 2.05P
        self.assinar_documento(
            sigla_temp=sigla_temp_filho, usuario=usuario_mesa, senha=senha
        )

        return sigla_pai

    def _assinar_ou_autenticar(self, sigla_temp, usuario, senha, assinar):
        copia = "false" if assinar else "true"
        data = {
            "id": "undefined",
            "sigla": sigla_temp,
            "nomeUsuarioSubscritor": usuario,
            "senhaUsuarioSubscritor": senha,
            "senhaIsPin": "false",
            "copia": copia,
        }
        r = self.session.post(
            URL_PADRAO + "/mov/assinar_senha_gravar",
            data=data,
        )

        r = self.session.get(URL_PADRAO + "/doc/exibir?sigla=" + sigla_temp)

        # CAPTURANDO IDENTIFICADORES DO PROTOCOLO ASSINADO
        soup = BeautifulSoup(r.text, "html.parser")
        try:
            documento_sigla = soup.find(id="marcarForm").find(
                "input", {"name": "sigla"}
            )["value"]
        except Exception:
            raise Exception("Falha ao assinar/autenticar.")

        return documento_sigla

    def _trocar_mesa(self, usuario_mesa):
        r = self.session.get(  # noqa: F841
            URL_BASE + "/siga/app/swapUser?username=" + usuario_mesa
        )

    @staticmethod
    def _extrair_dados_doc(html):
        soup = BeautifulSoup(html, "html.parser")

        try:
            usuario_id = soup.find(id="formulario_exDocumentoDTO.subscritorSel_id")[
                "value"
            ]
        except TypeError:
            usuario_id = None

        try:
            usuario_nome = soup.find(
                id="formulario_exDocumentoDTO.subscritorSel_descricao"
            )["value"]
        except TypeError:
            usuario_nome = None

        classificacao_id = soup.find(
            id="formulario_exDocumentoDTO.classificacaoSel_id"
        )["value"]
        classificaçao_desc = soup.find(
            id="formulario_exDocumentoDTO.classificacaoSel_descricao"
        )["value"]
        classificaçao_sigla = soup.find(
            id="formulario_exDocumentoDTO.classificacaoSel_sigla"
        )["value"]
        doc_id = soup.find(id="formulario_exDocumentoDTO.mobilPaiSel_id")["value"]
        doc_desc_curta = soup.find(
            id="formulario_exDocumentoDTO.mobilPaiSel_descricao"
        )["value"]
        doc_desc_longa = soup.find(id="descrDocumento").text

        return (
            usuario_id,
            usuario_nome,
            classificacao_id,
            classificaçao_desc,
            classificaçao_sigla,
            doc_id,
            doc_desc_curta,
            doc_desc_longa,
        )

    def listar_grupos(self) -> list:
        """Lista os nomes dos grupos de documentos ("filas") da mesa virtual.

        Returns:
            Uma lista com os nomes dos grupos de documentos da mesa virtual.
        """
        URL_BASE_MESA_JSON = URL_BASE + "/sigaex/app/mesa2.json"

        r = self.session.get(URL_BASE_MESA_JSON)
        json_mesa = r.json()
        lista_grupos = [dict_grupo["grupoNome"] for dict_grupo in json_mesa]

        return lista_grupos

    def listar_documentos(
        self,
        filtro: str = "",
        grupos: list = None,
        trazer_arquivados: bool = False,
        trazer_cancelados: bool = False,
        lotacao: bool = False,
    ) -> list:
        """Lista documentos conforme os parâmetros informados.

        Args:
            filtro (str, optional): Subtexto de filtro.
            grupos (list, optional): Nomes dos grupos.
            trazer_arquivados (bool, optional): Define se serão listados documentos
                arquivados. Valor padrão é `False`.
            trazer_cancelados (bool, optional): Define se serão listados documentos
                cancelados. Valor padrão é  `False`.
            lotacao (bool, optional): Se `True`, serão listados os documentos da lotação
                (unidade administrativa) do usuário logado. Se `False`, serão listados
                apenas os documentos do usuário logado. Valor padrão é `False`.

        Returns:
            Uma lista de dicionários, em que cada dicionário representa um documento.
        """
        params_2 = (
            '":{"grupoQtd":20,"grupoQtdLota":20}}'
            + "&qtd=20&contar=true&trazerAnotacoes=true"
            + "&ordemCrescenteData=true&dtDMA=false"
            + "&trazerArquivados="
            + str(trazer_arquivados)
            + "&trazerCancelados="
            + str(trazer_cancelados)
            + "&exibeLotacao="
            + str(lotacao)
            + "&filtro="
            + filtro
        )

        temp_grupos = self.listar_grupos()

        if grupos is None:
            grupos = temp_grupos

        if len(grupos) > len(temp_grupos):
            raise ValueError(
                "Número de grupos passados em `grupos` é maior do que o número de "
                "grupos existentes."
            )

        lista_documentos = []
        my_timer = {}
        for grupo in grupos:
            # contatena uma string para acessar o API do SP Sem Papel
            # e obter o número total de documentos que passam pelo filtro
            # (grupoCounterUser):
            params_3 = '{"' + grupo + params_2 + "&offset="
            url_json = URL_MESA_JSON_BASE + params_3

            r = self.session.get(url_json + "0")
            json_mesa = r.json()

            if lotacao is False:
                contador_grupo = int(json_mesa[0]["grupoCounterUser"])
            else:
                contador_grupo = int(json_mesa[0]["grupoCounterLota"])

            if contador_grupo == 0:
                continue
            my_iterable = range(20, contador_grupo + 1, 20)

            lista_documentos += json_mesa[0]["grupoDocs"]
            for offset in my_iterable:
                try:
                    r = self.session.get(url_json + str(offset))
                except (ConnectionError, ProxyError):
                    sleep(10)
                    r = self.session.get(url_json + str(offset))
                finally:
                    json_mesa = r.json()
                    try:
                        lista_documentos += json_mesa[0]["grupoDocs"]
                    except KeyError:
                        breakpoint
                    time_stamp = asctime()
                    my_timer[f"{grupo}-{offset/20}"] = time_stamp
                    sleep(1)

        return lista_documentos

    def listar_mesas(self) -> list:
        """Lista as mesas virtuais disponíveis ao usuário logado.

        Returns:
            Uma lista de tuplas no formato (UA, mesa).
        """
        URL_BASE_MESA = URL_BASE + "/sigaex/app/mesa2"

        r = self.session.get(URL_BASE_MESA)

        lista_mesas = []
        soup = BeautifulSoup(r.text, "html.parser")

        # PRIMEIRO, PEGO A MESA LOGADA
        ua_atual = soup.find(id="dropdownLotaMenuButton").get_text().split()[0]
        mesa_atual = soup.find(id="cadastrante")["title"]
        tupla = (ua_atual, mesa_atual)
        lista_mesas.append(tupla)

        # DEPOIS, COMPLETO COM AS DEMAIS MESAS DISPONÍVEIS
        a_list = soup.find("div", class_="dropdown-menu").find_all("a")

        for a in a_list:
            tupla = (
                a.text.split()[0],
                a.text.split()[1].replace("(", "").replace(")", ""),
            )
            lista_mesas.append(tupla)

        return lista_mesas

    def _obter_dados_usuario(self, usuario_sigla) -> list:
        # SÓ FUNCIONA COM USUÁRIOS DA SFP, CÓDIGO 118... PREGUIÇA DE ABRIR GERAL
        # QUEM QUISER GENERALIZAR E MONTAR UM DICT DE ÓRGÃOS, BE MY GUEST
        data = [
            ("propriedade", "subscritor"),
            ("postBack", "1"),
            ("paramoffset", "0"),
            ("p.offset", "0"),
            ("buscarFechadas", ""),
            ("modal", "true"),
            ("sigla", usuario_sigla),
            ("reqlotacaoSel", ""),
            ("alterouSel", ""),
            ("lotacaoSel.id", ""),
            ("lotacaoSel.descricao", ""),
            ("lotacaoSel.buscar", ""),
            ("lotacaoSel.sigla", ""),
            ("idOrgaoUsu", "118"),
        ]

        r = self.session.post(
            URL_BASE + "/siga/app/pessoa/buscar",
            data=data,
        )

        soup = BeautifulSoup(r.text, "html.parser")
        a_list = soup.find_all("a")
        for a in a_list:
            if 'href="javascript: parent.retorna_subscritor' in str(a):
                bloco = str(a).split("('")[1]
                bloco = bloco.split("')")[0]
                assina_id = bloco.split("','")[0]
                assina_sigla = bloco.split("','")[1]
                assina_nome = bloco.split("','")[2]

        return [assina_id, assina_nome, assina_sigla]
