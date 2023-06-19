"""Módulo com definições do sistema SIPET."""
from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema, preparar_metodo
from pepe.utils.html import _obter_assinatura_tag, find_all_deepest
from pepe.utils.login import login_identity_cert
from pepe.utils.texto import comparar_textos, limpar_texto

URL_BASE = "https://www3.fazenda.sp.gov.br/SIPET"
URL_MEIO = "https://www3.fazenda.sp.gov.br/SIPET/Home/LoginFazendarioCertificado"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v002/"
    "Sefaz.Identity.STS.Certificado/LoginCertificado.aspx"
)
URL_PESQUISA = URL_BASE + "/Triagem/Pesquisar"
URL_VISUALIZA = URL_BASE + "/Triagem/Visualizar/"
URL_EXPORTA = URL_BASE + "/Triagem/Exportar"
URL_SITUACOES = URL_BASE + "/api/triagem/situacoes/"

WTREALM = "https://www3.fazenda.sp.gov.br/SIPET"
WREPLY = "https://www3.fazenda.sp.gov.br/SIPET"
WCTX = "https://www3.fazenda.sp.gov.br/SIPET"
WAUTH = "urn:oasis:names:tc:SAML:2.0:assertion"
CLAIM_SETS = "00F30001"


class Sipet(Sistema):
    """Representa o sistema [SIPET](https://www3.fazenda.sp.gov.br/SIPET).

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy=False) -> None:
        """Cria um objeto da classe SIPET.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE + "/Triagem/Pesquisar")
        soup = BeautifulSoup(r.text, "html.parser")
        el_usuario_logado = soup.find_all("p", class_="login-info")[0]

        return bool(el_usuario_logado.text.strip())

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE)

        # cookies = ""
        # for cookie in self.session.cookies.get_dict().keys():
        #     cookies += cookie + "=" + self.session.cookies.get_dict()[cookie] + "; "

        outros_params = {"wauth": WAUTH, "wreply": WREPLY}

        cookies_aute, r = login_identity_cert(
            nome_cert=nome_cert,
            url_inicial=URL_IDENTITY_INICIAL,
            wtrealm=WTREALM,
            claim_sets=CLAIM_SETS,
            wctx=WCTX,
            cookies=self.session.cookies,
            outros_params=outros_params,
        )
        self.session.cookies.update(cookies_aute)
        self.session.get(URL_MEIO)

        if not self.autenticado():
            raise AuthenticationError()

    # não serve, pois código != sequencial de definição (usado no API).
    @preparar_metodo
    def listar_tipos_solicitacao(
        self,
    ) -> dict:
        """Retorna dicionário com tipos de solicitação e seus sequenciais.

        Para ser usado, ainda que não exclusivamente, como enumeration para seleção do
        tipo de solicitação que será passados à função listar_solicitacoes, sob
        argumento 'sequencial_definicao'.

        Returns:
            Um 'dict' contendo nome de cada um dos tipos de solicitações e seus
            sequenciais.
        """
        r = self.session.get(
            "https://www3.fazenda.sp.gov.br/SIPET/Triagem/Pesquisar?"
            "Protocolo="
            "&CpfCnpjInteressado="
            "&CpfCnpjCadastrador="
            "&Situacao="
            "&NumeroSpSemPapel="
            "&DataInicial="
            "&DataFinal="
            "&NomeResponsavelTriagem="
            "&TipoCampoInformacaoServico="
            "&ValorInformacaoServico="
            "&SequencialDefinicao="
        )
        s = BeautifulSoup(r.text, "html.parser")
        my_options = s.find_all("select", attrs={"id": "SequencialDefinicao"})[
            0
        ].find_all("option")
        tipos_solicitacao = [{o.text: o.attrs["value"]} for o in my_options]

        return tipos_solicitacao

    @preparar_metodo
    def listar_solicitacoes(
        self,
        protocolo: str = "",
        cpf_cnpj_interessado: str = "",
        cpf_cnpj_cadastrador: str = "",
        situacao: str = "",
        numero_spsempapel: str = "",
        data_inicial: str = "",
        data_final: str = "",
        responsavel_triagem: str = "",
        sequencial_definicao: str = "",
    ) -> list:
        """Lista solicitações no SIPET conforme os parâmetros informados.

        Args:
            protocolo (str, optional): Protocolo no formato
                000000-00000000-000000000-00.
            cpf_cnpj_interessado (str, optional): CPF ou CNPJ do interessado.
            cpf_cnpj_cadastrador (str, optional): CPF ou CNPJ do cadastrador.
            situacao (str, optional): Situação.
            numero_spsempapel (str, optional): Protocolo do SP Sem Papel, no formato
                UAA-DOC-AAAA/NNNNNNNNN.
            data_inicial (str, optional): Data inicial, no formato dd/mm/aaaa.
            data_final (str, optional): Data final, no formato dd/mm/aaaa.
            responsavel_triagem (str, optional): Nome completo do responsável pela
                triagem, em letras maiúsculas e sem acentos.
            sequencial_definicao (str, optional): Utilize o método
                `listar_tipos_solicitacao` para obter a lista completa dos possíveis
                valores para esse parâmetro.

        Returns:
            Uma lista de dicionários, cada um representando uma solicitação.
        """
        # TODO: extrair relação do <select class="form-control input-sm"
        # id="TipoCampoInformacaoServico" name="TipoCampoInformacaoServico"><option
        # value="">Selecionar</option>

        # TODO: explorar exportação, pois retorna o número total de resultados,
        # contornando a limitação ao número de itens exibidos via browser.

        params = {
            "Protocolo=": protocolo,
            "CpfCnpjInteressado=": cpf_cnpj_interessado,
            "CpfCnpjCadastrador=": cpf_cnpj_cadastrador,
            "Situacao=": situacao,
            "NumeroSpSemPapel=": numero_spsempapel,
            "DataInicial=": data_inicial,
            "DataFinal=": data_final,
            "NomeResponsavelTriagem=": responsavel_triagem,
            "TipoCampoInformacaoServico=": "",
            "ValorInformacaoServico=": "",
            "SequencialDefinicao=": sequencial_definicao,
        }

        s_params = "".join(k + v + "&" for k, v in params.items())
        URL_PARAMS = URL_PESQUISA + "?" + s_params
        s_mais_que_mil = (
            "Resultado da pesquisa apresentado parcialmente,"
            + " pois ultrapassou o limite máximo de registros por consulta."
        )
        r = self.session.get(URL_PARAMS)
        s = BeautifulSoup(r.text, "html.parser")
        tabela_1 = self.scrape_tabela_sipet(soup=s, retornar_visu=True)
        tabela_2 = {}
        if len(s.find_all("p", string=s_mais_que_mil)) > 0:
            # se houver > 1000 solicitações, baixar o .csv:
            r = self.session.get(URL_EXPORTA + "?" + s_params)
            my_file_name = r.headers._store["content-disposition"][1].split(
                "filename="
            )[1]

            with open(my_file_name, "wb") as f:
                f.write(r.content)

            with open(my_file_name, newline="") as f:
                my_csv = f.readlines()

            lista = []
            # FALTA APAGAR O /r/n ao final da linha
            # Usa o índice [-1] pra pegar o último elemento
            for i, l in enumerate(my_csv):
                lista.append([f"n_visualizar:{i}"] + [j for j in l.split(";")])

            if str(lista[-1]).find(
                "\x00"
            ):  # no csv.reader, "\x00" suscita erro "line contains NUL"
                lista.pop()

            tabela_2 = {i[1]: [i[0]] + i[2:] for i in lista}
            tabela_2["Nº Protocolo"][0] = "Nº Visualizar"

        tabela = {**tabela_1, **tabela_2}  # une os dois dicionários

        return tabela

    @preparar_metodo
    def scrape_tabela_sipet(
        self,
        html: str = None,
        soup: BeautifulSoup = None,
        pular_td=0,
        limiar_similaridade: float = 0.8,
        retornar_visu: bool = False,
    ) -> dict:
        """ "Raspa" (scrape) os dados da tabela HTML do SIPET.

        Também são raspados bem como os números das hrefs da primeira coluna.

        A tabela deve conter dados de uma única entidade (ex.: dados cadastrais de uma
        empresa) e ter elementos `<td>` separados para os nomes dos campos e seus
        valores.

        A função identifica automaticamente se um `<td>` contém um nome de campo
        (`<td>`-nome) ou um valor (`<td>`-valor). Para identificar os `<td>`-nome, é
        criada uma assinatura para o primeiro `<td>` da tabela. Essa assinatura é
        composta pelos atributos do `<td>` e também pelos nomes e atributos de seus
        elementos filhos. Todos os demais `<td>` da tabela que tiverem uma assinatura
        similar à primeira serão considerados `<td>`-nome. Os `<td>` não similares serão
        considerados `<td>`-valor. O conteúdo de um `<td>`-valor será atribuído ao
        último `<td>`-nome encontrado.

        Durante o processo, `<td>` vazios ou que tenham outros `<td>` aninhados são
        desconsiderados.

        Args:
            html (str): Código fonte em HTML contendo a tabela. Caso haja mais de
                uma tabela, será raspada a primeira. Parâmetro ignorado caso seja
                passado algum valor para `soup` e obrigatório caso `soup` seja `None`.
            soup (BeautifulSoup, optional): Soup do código fonte em HTML contendo a
                tabela.
            pular_td (int, optional): Quantidade de elementos `<td>` a serem pulados a
                partir do início da tabela. O primeiro `<td>` imediatamente após aqueles
                que foram pulados terá sua assinatura considerada como padrão para
                determinar os nomes de campo. Útil para ignorar cabeçalhos. Valor padrão
                é `0`.
            limiar_similaridade (float,): Valor de 0 a 1 que indica o mínimo de
                similaridade que a assinatura de um `<td>` deve ter em relação ao
                primeiro `<td>`-nome para também ser considerado um `<td>`-nome. Valor
                padrão é `0.8`.
            retornar_visu (bool, optional): determina se devem ser retornados os números
                que representam as chaves para visualização de cada página de
                solicitação.

        Returns:
            Um dicionários com os dados da tabela
        """  # noqa: D210
        if retornar_visu is True:
            s_visu = "Nº Visualizar"

        if not soup:
            soup = BeautifulSoup(html, "html.parser")

        resultado = {}
        table = soup.find("table") if soup.name != "table" else soup
        td_nome_assinatura = None
        nome_atual = None

        my_headers = [
            q.text.replace("\n", "").strip() for q in find_all_deepest(table, "th")
        ]

        if retornar_visu is True:
            resultado[my_headers[0]] = [s_visu] + my_headers[1:]
        else:
            resultado[my_headers[0]] = my_headers[1:]

        td_nome_assinatura = None
        nome_atual = None

        n_visualizar = None

        for td in find_all_deepest(table, "td")[pular_td:]:
            texto_limpo = limpar_texto(td.text)

            if not td_nome_assinatura:
                td_nome_assinatura = _obter_assinatura_tag(td)

            assinatura_atual = _obter_assinatura_tag(td)
            similaridade = comparar_textos(td_nome_assinatura, assinatura_atual)
            if similaridade > limiar_similaridade:
                nome_atual = texto_limpo
                if retornar_visu is True:
                    try:
                        if td.contents is None:
                            breakpoint  # inesperado, debuggar
                        if len(td.contents) > 0:
                            if str(td).find('href="/SIPET/Triagem/Visualizar/') > -1:
                                n_visualizar = (
                                    td.contents[1]
                                    .attrs["href"]
                                    .replace("/SIPET/Triagem/Visualizar/", "")
                                )
                    except Exception:
                        breakpoint
            else:
                if not nome_atual:
                    continue  # Sem nome de campo para o <td>, pulando

                valor_atual = texto_limpo

                if nome_atual in resultado:
                    try:
                        resultado[nome_atual].append(valor_atual)
                    except AttributeError:
                        resultado[nome_atual] = [resultado[nome_atual]] + [
                            (valor_atual)
                        ]
                elif n_visualizar is not None and nome_atual not in resultado:
                    resultado[nome_atual] = [n_visualizar, valor_atual]
                    n_visualizar = ""
                else:
                    resultado[nome_atual] = [valor_atual]

        return resultado

    @preparar_metodo
    def extrair_campos(
        self,
        lista_solicitacoes: dict = None,
        campos_req: list = None,
    ) -> dict:
        """Visualiza cada solicitação SIPET contida no dicionário `lista_solicitacoes`.

        Extrai de cada solicitação o valor dos campos requeridos e os apende ao
        dicionário.

        Args:
            lista_solicitacoes (list, optional): obtido do método listar_solicitacoes.
                Em sua omissão, busca lista todas as solicitações de situação
                `"Aprovado na triagem"`.

            campos_req (list): Lista de strings que representam os rótulos dos campos
                de texto cujo valor correspondente se requer.

            retornar_historico (bool, optional):

        Returns:
            Um dicionário, já obtido mediante método listar_solicitacoes, expandido com
            o apensamento dos valores dos campos requeridos em `campos_req`.
        """
        ID_HISTORICO = "historico"
        # TODO: deveria recuperar sempre esta lista do script
        # https://www3.fazenda.sp.gov.br/SIPET/bundles/sipet.triagem
        # sob function sipet.pedidos.descricaoSituacao
        tipo_situacao = {
            "1": "Rascunho",
            "2": "Aguardando triagem",
            "3": "Em triagem",
            "4": "Deferido",
            "5": "Pendente de correção",
            "6": "Rejeitado na triagem",
            "7": "Aprovado na triagem",
            "12": "Excluído pela Sefaz",
            "15": "Desistência",
        }

        if lista_solicitacoes is None:
            lista_solicitacoes = self.listar_solicitacoes()

        for v in lista_solicitacoes.values():
            n_visualizar = v[0]
            r = self.session.get(URL_VISUALIZA + n_visualizar)
            s = BeautifulSoup(r.text, "html.parser")

            if str.isnumeric(n_visualizar):
                # Campos Principais
                campos = [
                    {e.text: e.nextSibling.nextSibling.text.replace("\n", "")}
                    if e.nextSibling.nextSibling is not None
                    else {e.text: e.nextSibling.text.replace("\n", "")}
                    for e in s.find_all("label")
                ]
                v.append(campos)

                # Histórico de Situações
                my_s = s.find_all(id=ID_HISTORICO)[0]
                d = self.scrape_tabela_sipet(soup=my_s)
                historico = list(d.values())[0]
                historico.insert(0, list(d.keys())[0])
                w = self.session.get(URL_SITUACOES + n_visualizar).json()
                lwk = list(w[0].keys())
                # d = [wi[lwk[1]], wi[lwk[2]], wi[lwk[0]], wi[lwk[3]] for wi in w]
                d = []

                for wi in w:
                    d.append(
                        [
                            {historico[0]: wi[lwk[1]]},
                            {historico[1]: tipo_situacao[str(wi[lwk[3]])]},
                            {historico[2]: wi[lwk[0]]},
                            {historico[3]: wi[lwk[2]]},
                        ]
                    )

                v.append(d)
            else:  # adiciona rótulos de colunas ao cabeçalho
                v.append("Campos Principais")
                v.append("Histórico de Situações")

        return lista_solicitacoes
