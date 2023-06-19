"""Módulo com definições do sistema ETC."""

import requests
from requests_ntlm import HttpNtlmAuth

from pepe import AuthenticationError, Sistema, preparar_metodo

URL_BASE = "http://etc.intra.fazenda.sp.gov.br/"
URL_BASE_SITES = URL_BASE + "sites/"


class Etc(Sistema):
    """Representa um site de um espaço de trabalho do sistema [ETC](https://etc.intra.fazenda.sp.gov.br/).

    Um site engloba listas e bibliotecas daquele site, mas não de seus subsites. Para
    trabalhar com diferentes subsites, diferentes objetos dessa classe devem ser
    instanciados.

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, url_site: str, usar_proxy: bool = False) -> None:
        """Cria um objeto da classe Etc.

        Args:
            url_site (str): endereço do site no formato http://etc.intra.fazenda.sp.gov.br/sites/site_raiz/subsite.
                É também possível passar o endereço apenas do site raiz ou de subsites
                em maiores níveis na hierarquia. É necessário que o último termo do
                endereço seja a o nome de um subsite conforme aparece em sua URL. Não
                são válidos endereços com nomes de listas e bibliotecas.

            - Exemplos de endereços **válidos**:
                - http://etc.intra.fazenda.sp.gov.br/sites/feriasdti
                - http://etc.intra.fazenda.sp.gov.br/sites/feriasdti/teletrabalho

            - Exemplos de endereços **inválidos**:
                - http://etc.intra.fazenda.sp.gov.br/
                - http://etc.intra.fazenda.sp.gov.br/sites/feriasdti/Lists/Funces/AllItems.aspx
                - http://etc.intra.fazenda.sp.gov.br/sites/feriasdti/Documentos (se
                "Documentos" for nome de uma biblioteca)
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().__init__(usar_proxy)
        self.session.headers.update(
            {
                "accept": "application/json; odata=verbose",
                "content-type": "application/json; odata=verbose",
            }
        )

        if not url_site.startswith(URL_BASE_SITES) or url_site == URL_BASE_SITES:
            raise Exception(url_site + " não é um endereço válido de um site do ETC")

        self._url_site = url_site
        self._auth = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        try:
            r = self.session.get(URL_BASE + "_api/web/lists")  # noqa: F841

            return True
        except Exception:
            return False

    def login(self, usuario: str, senha: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        self.session.auth = HttpNtlmAuth(usuario, senha)

        if not self.autenticado():
            raise AuthenticationError()

    @preparar_metodo
    def listar_itens(self, lista: str) -> list:
        """Lista itens de uma lista.

        Args:
            lista (str): Nome da lista conforme aparece em sua URL.

        Raises:
            KeyError: Erro indicando que lista não existe no site.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            um item da lista.
        """
        url = self._url_site + "/_api/web/lists/GetByTitle('" + lista + "')/items"

        try:
            r = self.session.get(url)
        except requests.exceptions.HTTPError as e:
            if str(e).startswith("404"):
                raise KeyError(f"Lista {lista} não existe.") from e
            else:
                raise e

        return r.json()["d"]["results"]

    @preparar_metodo
    def obter_item(self, lista: str, id_: int) -> dict:
        """Obtém detalhes um item de uma lista.

        Args:
            lista (str): Nome da lista conforme aparece em sua URL.
            id_ (int): ID do item.

        Raises:
            KeyError: Erro indicando que lista ou item não existem.

        Returns:
            Um dicionário que contém as propriedades do item.
        """
        url = (
            self._url_site
            + "/_api/web/lists/GetByTitle('"
            + lista
            + "')/items("
            + str(id_)
            + ")"
        )

        try:
            r = self.session.get(url)
        except requests.exceptions.HTTPError as e:
            if str(e).startswith("404"):
                raise KeyError(f"Item de id {id_} não existe.") from e
            else:
                raise e

        return r.json()["d"]

    @preparar_metodo
    def criar_item(self, lista: str, dados: dict) -> int:
        """Cria um item em uma lista.

        Args:
            lista (str): Nome da lista conforme aparece em sua URL.
            dados (dict): Valores dos campos a serem incluídos no novo item. As chaves
                do dicionário devem corresponder aos nomes internos das colunas da
                lista. É possível incluir apenas um subconjunto de colunas.

        Returns:
            Um `int` com o ID do item criado.
        """
        # Obter ListItemEntityTypeFullName necessário para criação de item
        ent_type = self._obter_list_item_entity_type_full_name(lista)

        # Atualizar o CSRF token
        digest = self._obter_digest()
        self.session.headers.update({"X-RequestDigest": digest})

        # Fazer a requisição
        url = self._url_site + "/_api/web/lists/GetByTitle('" + lista + "')/items"
        data = {"__metadata": {"type": ent_type}}
        data |= dados
        r = self.session.post(url, json=data)

        return r.json()["d"]["Id"]

    @preparar_metodo
    def deletar_item(self, lista: str, id_: int) -> dict:
        """Deleta um item de uma lista.

        Args:
            lista (str): Nome da lista conforme aparece em sua URL.
            id_ (int): ID do item.

        Raises:
            KeyError: Erro indicando que lista ou item não existem.

        Returns:
            Um dicionário com os dados do item que foi deletado, equivalente ao obtido
            ao se chamar o método `obter_item(lista, id_).
        """
        url = (
            self._url_site
            + "/_api/web/lists/GetByTitle('"
            + lista
            + "')/items("
            + str(id_)
            + ")"
        )

        try:
            # Obter item a ser deletado para recuperar Etag e retornar o item ao final
            item_deletado = self.obter_item(lista, id_)
            etag = item_deletado["__metadata"]["etag"]

            # Atualizar o CSRF token
            digest = self._obter_digest()
            self.session.headers.update({"X-RequestDigest": digest})

            # Fazer a requisição
            del_headers = {"X-HTTP-Method": "DELETE", "IF-MATCH": etag}
            all_headers = dict(self.session.headers) | del_headers
            r = self.session.post(url, headers=all_headers)  # noqa: F841

            return item_deletado

        except requests.exceptions.HTTPError as e:
            if str(e).startswith("404"):
                raise KeyError(f"Item de id {id_} não existe.") from e
            elif str(e).startswith("412"):  # Erro de Etag
                raise requests.exceptions.HTTPError(
                    "Item atualizado durante deleção."
                ) from e
            else:
                raise e

    @preparar_metodo
    def atualizar_item(self, lista: str, id_: id, dados: dict) -> None:
        """Atualiza um item de uma lista.

        Args:
            lista (str): Nome da lista conforme aparece em sua URL.
            id_ (int): ID do item.
            dados (dict): Valores dos campos a serem alterados no item. As chaves
                do dicionário devem corresponder aos nomes internos das colunas da
                lista.

        Raises:
            KeyError: Erro indicando que lista ou item não existem.

        """
        url = (
            self._url_site
            + "/_api/web/lists/GetByTitle('"
            + lista
            + "')/items("
            + str(id_)
            + ")"
        )

        try:
            # Obter ListItemEntityTypeFullName necessário para atualização de item
            ent_type = self._obter_list_item_entity_type_full_name(lista)

            # Obter item a ser atualizado para recuperar Etag
            item_original = self.obter_item(lista, id_)
            etag = item_original["__metadata"]["etag"]

            # Atualizar o CSRF token
            digest = self._obter_digest()
            self.session.headers.update({"X-RequestDigest": digest})

            # Fazer a requisição
            upd_headers = {"X-HTTP-Method": "MERGE", "IF-MATCH": etag}
            all_headers = dict(self.session.headers) | upd_headers

            data = {"__metadata": {"type": ent_type}}
            data |= dados

            r = self.session.post(url, headers=all_headers, json=data)  # noqa: F841

        except requests.exceptions.HTTPError as e:
            if str(e).startswith("404"):
                raise KeyError(f"Item de id {id_} não existe.") from e
            elif str(e).startswith("412"):  # Erro de Etag
                raise requests.exceptions.HTTPError(
                    "Item atualizado por outro processo durante a atualização."
                ) from e
            else:
                raise e

    def _obter_digest(self):
        contextinfo = self._url_site + "/_api/contextinfo"
        r = self.session.post(contextinfo)
        digest_value = r.json()["d"]["GetContextWebInformation"]["FormDigestValue"]

        return digest_value

    def _obter_list_item_entity_type_full_name(self, lista):
        url = (
            self._url_site
            + "/_api/web/lists/GetByTitle('"
            + lista
            + "')?$select=ListItemEntityTypeFullName"
        )
        r = self.session.get(url)

        return r.json()["d"]["ListItemEntityTypeFullName"]
