"""Módulo com funções utilitárias para manipulação de arquivos HTML."""

import os
import tempfile
from typing import Literal, Union

import win32com
from bs4 import BeautifulSoup

from pycvi.pancho.utils.texto import comparar_textos, limpar_texto


def extrair_validadores_aspnet(html: str, opcionais: list = None) -> tuple:
    """Extrai os validadores de uma página ASP.NET.

    Validadores são __VIEWSTATE, __VIEWSTATEGENERATOR e __EVENTVALIDATION.

    Args:
        html (str): Código fonte em HTML de uma página ASP.NET.
        opcionais (list, optional): Lista com nomes dos validadores para os quais não
            deve ser gerada uma exceção se não forem encontrados. Se `None`, a ausência
            de qualquer validador gerará uma exceção.

    Returns:
        Uma tupla `(__VIEWSTATE, __VIEWSTATEGENERATOR, __EVENTVALIDATION)`

    Raises:
        ValueError: Erro indicando que o código-fonte passado não contém todos os
            validadores, exceto os listados em `opcionais`.
    """
    viewstate = ""
    viewstategenerator = ""
    eventvalidation = ""
    if opcionais is None:
        opcionais = []

    # CAPTURANDO VALIDADORES
    soup = BeautifulSoup(html, "html.parser")

    try:
        viewstate = soup.find("input", id="__VIEWSTATE")["value"]
        viewstategenerator = soup.find("input", id="__VIEWSTATEGENERATOR")["value"]
        eventvalidation = soup.find("input", id="__EVENTVALIDATION")["value"]

    except Exception:
        # ÀS VEZES, OS VALIDADORES VÊM COMO ATRIBUTOS name DA TAG input SEM POSSUÍREM id
        try:
            viewstate = soup.find("input", name="__VIEWSTATE")["value"]
            viewstategenerator = soup.find("input", name="__VIEWSTATEGENERATOR")[
                "value"
            ]
            eventvalidation = soup.find("input", name="__EVENTVALIDATION")["value"]

        except Exception:
            # RARAMENTE, OS VALIDADORES VÊM COMO STRINGS SOLTAS NO HTML
            # NÃO COMO ATRIBUTOS DE QUALQUER TAG
            if "__VIEWSTATE" in html:
                resposta_split = html.split("|")

                for index in range(len(resposta_split)):
                    if resposta_split[index] == "__VIEWSTATE":
                        viewstate = resposta_split[index + 1]
                    elif resposta_split[index] == "__VIEWSTATEGENERATOR":
                        viewstategenerator = resposta_split[index + 1]
                    elif resposta_split[index] == "__EVENTVALIDATION":
                        eventvalidation = resposta_split[index + 1]

    if (
        (not viewstate and "__VIEWSTATE" not in opcionais)
        or (not viewstategenerator and "__VIEWSTATEGENERATOR" not in opcionais)
        or (not eventvalidation and "__EVENTVALIDATION" not in opcionais)
    ):
        raise ValueError("Erro de requisição, validadores não contidos na página.")

    return viewstate, viewstategenerator, eventvalidation


def salvar(html: str, caminho: str) -> None:
    """Salva um arquivo HTML.

    Args:
        html (str): Código fonte em HTML.
        caminho (str): Caminho completo onde deverá ser salvo o arquivo, incluindo seu
            nome. Deve terminhar com .html.
    """
    with open(caminho, "w") as f:
        f.write(html)


def converter_para_pdf(html: str, caminho: str, paisagem=True) -> None:
    """Converte um arquivo HTML em PDF.

    Args:
        html (str): Código fonte em HTML ou o caminho completo de um arquivo (deve
            terminar com .html)
        caminho (str): Caminho completo onde deverá ser salvo o arquivo PDF, incluindo
            seu nome. Deve terminar com .pdf.
        paisagem (bool, optional): Se `True`, a orientação do arquivo PDF resultante
            será em modo paisagem. Se `False`, a orientação será em modo retrato.
    """
    if os.path.isfile(html):
        caminho_html = html
    else:
        tmp = tempfile.NamedTemporaryFile("w", encoding="UTF-8", delete=False)
        tmp.write(html)
        caminho_html = tmp.name
        tmp.close()

    oWord = None
    try:
        oWord = win32com.client.DispatchEx("Word.Application")
        oWord.DisplayAlerts = False
        oDoc = oWord.Documents.Open(FileName=caminho_html, ConfirmConversions=False)
        oDoc.WebOptions.Encoding = 28591  # msoEncodingISO88591Latin1
        oDoc.PageSetup.Orientation = int(paisagem)  # wdOrientLandscape
        oDoc.PageSetup.LeftMargin = 20
        oDoc.PageSetup.RightMargin = 20
        oDoc.PageSetup.TopMargin = 20
        oDoc.PageSetup.BottomMargin = 20
        oDoc.PageSetup.HeaderDistance = 10
        oDoc.PageSetup.FooterDistance = 10
        oDoc.SaveAs(FileName=caminho, FileFormat=17)  # 17 = PDF
        oDoc.Close(SaveChanges=0)
    finally:
        if oWord:
            oWord.Quit()
        try:
            os.remove(tmp.name)
        except UnboundLocalError:
            pass


def find_all_deepest(soup: BeautifulSoup, tag: str) -> list:
    """Lista todos os elementos de um soup que não possuem o mesmo elemento como descendente.

    Args:
        soup (BeautifulSoup): Soup do código fonte em HTML.
        tag (str): Nome do elemento.

    Returns:
        Uma lista dos elementos encontrados. Caso nenhum elemento seja encontrado, será
        retornada uma lista vazia.
    """  # noqa: E501
    return [e for e in soup.find_all(tag) if not e.find(tag)]


def scrape_tabela(
    tipo_entidade: Literal["unica", "multi"],
    html: str = None,
    soup: BeautifulSoup = None,
    pular_tr=0,
    pular_td=0,
    limiar_similaridade: float = 0.8,
) -> Union[dict, list]:
    """ "Raspa" (scrape) os dados de uma tabela HTML.

    Essa função consegue raspar dados de dois tipos tabela: entidade única e múltiplas
    entidades.

    Tabela de entidade única é aquela que contém dados de uma única entidade, por
    exemplo:

    |                 |               |
    | --------------- | ------------- |
    | **Nome:**       | Ada Lovelace  |
    | **Profissão:**  | Programadora  |

    Tabelas de múltiplas entidades possuem dados de mais de uma entidade, uma por linha,
    por exemplo:

    |  **Nome**             | **Profissão** |
    | --------------------- | ------------- |
    | Leonhard Euler        | Matemático    |
    | Alberto Santos-Dumont | Aviador       |

    Para tabelas de entidade única, a função identifica automaticamente se um `<td>`
    contém um nome de campo (`<td>`-nome) ou um valor (`<td>`-valor). Para identificar
    os `<td>`-nome, é criada uma assinatura para o primeiro `<td>` da tabela. Essa
    assinatura é composta pelos atributos do `<td>` e também pelos nomes e atributos de
    seus elementos filhos. Todos os demais `<td>` da tabela que tiverem uma assinatura
    similar à primeira serão considerados `<td>`-nome. Os `<td>` não similares serão
    considerados `<td>`-valor. O conteúdo de um `<td>`-valor será atribuído ao último
    `<td>`-nome encontrado. `<td>` vazios são desconsiderados.

    Para tabelas de entidade múltipla, a primeira linha (`<tr>`) é considerada contendo
    os nomes dos campos. As demais linhas são consideradas como tendo os valores dos
    campos, uma linha para cada entidade.

    Para ambos os tipos de tabela, `<td>` aninhados são desconsiderados.

    Args:
        tipo_entidade ("unica" ou "multi"): Se "unica", considerar tabela de entidade
            única. Se "multi", considerar tabela de entidade múltipla.
        html (str): Código fonte em HTML contendo a tabela. Caso haja mais de
            uma tabela, será raspada a primeira. Parâmetro ignorado caso seja passado
            algum valor para `soup` e obrigatório caso `soup` seja `None`.
        soup (BeautifulSoup, optional): Soup do código fonte em HTML contendo a tabela.
        pular_td (int, optional): Quantidade de elementos `<td>` a serem pulados a
            partir do início da tabela. O primeiro `<td>` imediatamente após aqueles que
            foram pulados terá sua assinatura considerada como padrão para determinar os
            nomes de campo. Útil para ignorar cabeçalhos. Utilizado apenas se
            `tipo_entidade` é `"unica"`. Valor padrão é 0.
        pular_tr (int, optional): Quantidade de elementos `<tr>` a serem pulados a
            partir do início da tabela. Útil para ignorar cabeçalhos. Utilizado apenas
            se `tipo_entidade` é `"multi". `Valor padrão é 0.
        limiar_similaridade (float,): Valor de 0 a 1 que indica o mínimo de
            similaridade que a assinatura de um `<td>` deve ter em relação ao primeiro
            `<td>`-nome para também ser considerado um `<td>`-nome. Valor padrão é 0.8.

    Returns:
        Um dicionário com os dados da tabela.
    """  # noqa: D210
    if not soup:
        soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table") if soup.name != "table" else soup

    if tipo_entidade == "unica":
        resultado = {}
        td_nome_assinatura = None
        nome_atual = None

        for td in find_all_deepest(table, "td")[pular_td:]:
            texto_limpo = limpar_texto(td.text)

            if not texto_limpo:  # Vazio, pulando
                continue

            if not td_nome_assinatura:
                td_nome_assinatura = _obter_assinatura_tag(td)

            assinatura_atual = _obter_assinatura_tag(td)
            similaridade = comparar_textos(td_nome_assinatura, assinatura_atual)
            if similaridade > limiar_similaridade:
                nome_atual = texto_limpo
            else:
                if not nome_atual:
                    continue  # Sem nome de campo para o <td>, pulando

                valor_atual = texto_limpo

                if nome_atual in resultado:
                    try:
                        resultado[nome_atual].append(valor_atual)
                    except AttributeError:
                        resultado[nome_atual] = [resultado[nome_atual]] + [valor_atual]
                else:
                    resultado[nome_atual] = valor_atual

    elif tipo_entidade == "multi":
        resultado = []
        td_nome_assinatura = None
        nomes = []

        # Extraindo nomes de campos
        trs = find_all_deepest(table, "tr")
        tr_nomes = trs[pular_tr]

        if tr_nomes.find("th"):
            nomes = [limpar_texto(th.text) for th in tr_nomes.find_all("th")]
        else:
            nomes = [limpar_texto(td.text) for td in tr_nomes.find_all("td")]

        # Extraindo valores de campos
        for tr in trs[pular_tr + 1 :]:
            valores = [limpar_texto(td.text) for td in tr.find_all("td")]
            assert len(valores) == len(nomes)
            item = {nome: valor for nome, valor in zip(nomes, valores)}
            item.pop("", None)
            resultado.append(item)

    else:
        raise ValueError(
            "Parâmetro 'tipo_entidade' deve receber valores 'unica' ou 'multi'."
        )

    return resultado


def _obter_assinatura_tag(tag):
    tag_str = (
        tag.name
        + " "
        + " ".join(
            attr + " " + str(val)
            for attr, val in tag.attrs.items()
            if attr not in ["id", "name"]
        )
    )
    children_str = " ".join(
        t.name
        + " "
        + " ".join(
            attr + " " + str(val)
            for attr, val in t.attrs.items()
            if attr not in ["id", "name"]
        )
        for t in tag()
    )

    return tag_str + " " + children_str
