"""Módulo com definições do sistema SharePointOnline."""

import os

import requests
from tqdm import tqdm

from pepe import Graph, preparar_metodo
from pepe.sistemas.graph import URL_API

URL_PESSOAL = URL_API + "sites/fazendaspgovbr-my.sharepoint.com:/personal/"
URL_SITES = URL_API + "sites/fazendaspgovbr.sharepoint.com:/sites/"
TAM_ARQ_PEQ = 4000000
CHUNK_SIZE_UP = 10485760  # Precisa ser múltiplo de 320 KiB


class SharePointOnline(Graph):
    # TODO: Passar os métodos da classe OneDrive para essa classe
    """Representa um site do SharePoint Online.

    Um site engloba listas e bibliotecas daquele site, mas não de seus subsites. Para
    trabalhar com diferentes subsites, diferentes objetos dessa classe devem ser
    instanciados.

    Listas do SharePoint são repositórios de informações em formato tabular, semelhantes
    a planilhas.

    Bibliotecas do SharePoint são repositórios de arquivos, semelhantes a pastas.
    Bibliotecas também são consideradas listas e alguns métodos para lidar com listas
    dessa classe também se aplicam a bibliotecas.

    Para maiores detalhes, ver classe base ([Graph](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, nome_site: str = None, usar_proxy=False) -> None:
        """Cria um objeto da classe SharePointOnline.

        Args:
            nome_site (str, optional): Nome do site, conforme aparece em sua URL. Se
                `None`, é usado o site pessoal do usuário, onde podem ser acessadas as
                listas do Lists e os arquivos do OneDrive. Se você irá acessar apenas
                arquivos do OneDrive, recomendamos que use a classe [OneDrive][2].
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60

        [2]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60onedrive%60
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.nome_site = nome_site

    def login(self, usuario: str, senha: str = None, nome_cert: str = None) -> None:
        """Ver classe base ([Graph][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario=usuario, senha=senha, nome_cert=nome_cert)
        self._pos_login()

    def login_cert(self, nome_cert: str, usuario: str) -> None:
        """Ver classe base ([Graph][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login_cert(nome_cert=nome_cert, usuario=usuario)
        self._pos_login()

    def _pos_login(self):
        if self.nome_site:
            site_r = self.session.get(URL_SITES + self.nome_site)
        else:
            site_r = self.session.get(
                URL_PESSOAL + self._usuario + "_fazenda_sp_gov_br"
            )

        self._url_api = URL_API + "sites/" + site_r.json()["id"]

    @preparar_metodo
    def listar_listas(self) -> list:
        """Lista as listas do site.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de uma
            lista.
        """
        url = self._url_api + "/lists/"
        r = self.session.get(url)

        return r.json()["value"]

    @preparar_metodo
    def obter_lista(self, nome_lista: str) -> dict:
        """Obtém detalhes de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.

        Returns:
            Um dicionário que contém as propriedades da lista.
        """
        url = self._url_api + "/lists/" + nome_lista
        r = self.session.get(url)
        return r.json()

    @preparar_metodo
    def criar_lista(self, json: dict) -> dict:
        """Cria uma lista.

        Args:
            json (dict): Propriedades da nova lista no formato [*list resource*][1].

        Returns:
            Um dicionário que contém as propriedades da lista criada.

        [1]: https://learn.microsoft.com/graph/api/resources/list#properties
        """
        url = self._url_api + "/lists/"
        r = self.session.post(url, json=json)

        return r.json()

    @preparar_metodo
    def deletar_lista(self, nome_lista: str) -> None:
        """Deleta uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
        """
        url = self._url_api + "/lists/" + nome_lista
        self.session.delete(url)

    @preparar_metodo
    def listar_itens(self, nome_lista: str) -> list:
        """Lista itens de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de um
            item da lista.
        """
        url = self._url_api + "/lists/" + nome_lista + "/items?$expand=fields"
        r = self.session.get(url)
        lista_items = r.json()["value"]

        while "@odata.nextLink" in r.json():
            r = self.session.get(r.json()["@odata.nextLink"])
            lista_items += r.json()["value"]

        return lista_items

    @preparar_metodo
    def obter_item(self, nome_lista: str, id_item: str) -> dict:
        """Obtem detalhes de um item de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            id_item (str): Identificador do item.

        Returns:
            Um dicionário que contém as propriedades do item.
        """
        url = self._url_api + "/lists/" + nome_lista + "/items/" + id_item
        r = self.session.get(url)

        return r.json()

    @preparar_metodo
    def criar_item(self, nome_lista: str, json: dict) -> dict:
        """Cria um item em uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            json (dict): Propriedades do novo item no formato [*listItem resource*][1].

        Returns:
            Um dicionário que contém as propriedades do item criado.

        Example:
        ```
            >>> from pepe import SharePointOnline
            >>> shp = SharePointOnline(nome_site="pepe")
            >>> shp.login(usuario="kaleuud")
            >>> item = {"fields": {"Title": "Teste"}}
            >>> item_criado = shp.criar_item(nome_lista="Lista Teste", json=item)
        ```

        [1]: https://learn.microsoft.com/graph/api/resources/listitem#properties
        """
        url = self._url_api + "/lists/" + nome_lista + "/items/"
        r = self.session.post(url, json=json)

        return r.json()

    @preparar_metodo
    def deletar_item(self, nome_lista: str, id_item: str) -> None:
        """Deleta um item de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            id_item (str): Identificador do item.
        """
        url = self._url_api + "/lists/" + nome_lista + "/items/" + id_item
        self.session.delete(url)

    @preparar_metodo
    def atualizar_item(self, nome_lista: str, id_item: str, json: dict) -> dict:
        """Atualiza as propriedades de um item de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            id_item (str): Identificador do item.
            json (dict): Propriedades atualizadas do item no formato
                [*listItem resource*][1].

        Returns:
            Um dicionário que contém as propriedades do item atualizado.

        [1]: https://learn.microsoft.com/graph/api/resources/listitem#properties
        """
        url = self._url_api + "/lists/" + nome_lista + "/items/" + id_item + "/fields"
        r = self.session.patch(url, json=json)

        return r.json()

    @preparar_metodo
    def listar_colunas(self, nome_lista: str) -> list:
        """Lista as colunas de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de uma
            coluna da lista.
        """
        url = self._url_api + "/lists/" + nome_lista + "/columns"
        r = self.session.get(url)

        return r.json()["value"]

    @preparar_metodo
    def obter_coluna(self, nome_lista: str, nome_coluna: str) -> dict:
        """Obtém detalhes de uma coluna de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            nome_coluna (str): Nome interno da coluna (aquele que aparece na URL da
                página de configurações da coluna).

        Returns:
            Um dicionário que contém as propriedades da coluna.
        """
        url = self._url_api + "/lists/" + nome_lista + "/columns/" + nome_coluna
        r = self.session.get(url)

        return r.json()

    @preparar_metodo
    def renomear_coluna(
        self, nome_lista: str, nome_coluna: str, novo_nome: str
    ) -> dict:
        """Renomeia uma coluna de uma lista.

        O nome alterado por esse método é o nome de apresentação (*displayName*) da
        coluna, e não seu nome interno.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            nome_coluna (str): Nome interno da coluna (aquele que aparece na URL da
                página de configurações da coluna).
            novo_nome (str): Novo nome de apresentação da coluna.

        Returns:
            Um dicionário que contém as propriedades da coluna renomeada.
        """
        url = self._url_api + "/lists/" + nome_lista + "/columns/" + nome_coluna
        data = {"name": novo_nome, "displayName": novo_nome}
        r = self.session.patch(url, json=data)

        return r.json()

    @preparar_metodo
    def atualizar_coluna(
        self,
        nome_lista: str,
        nome_coluna: str,
        json: dict,
    ) -> dict:
        """Atualiza as propriedades de uma coluna de uma lista.

        Args:
            nome_lista (str): Nome interno (aquele que aparece na URL da lista) ou
                identificador da lista.
            nome_coluna (str): Nome interno da coluna (aquele que aparece na URL da
                página de configurações da coluna).
            json (dict): Propriedades atualizadas da coluna no formato
                [*columnDefinition resource type*][1].

        Returns:
            Um dicionário que contém as propriedades da coluna atualizada.

        [1]: https://learn.microsoft.com/graph/api/resources/columndefinition#properties
        """
        url = self._url_api + "/lists/" + nome_lista + "/columns/" + nome_coluna
        r = self.session.patch(url, json=json)

        return r.json()

    @preparar_metodo
    def subir_arquivo(
        self,
        caminho: str,
        id_biblioteca: str = None,
        id_pasta: str = None,
        renomear: bool = False,
        progresso=True,
    ) -> dict:
        """Sobe (upload) um arquivo em uma biblioteca.

        Args:
            caminho (str): Caminho completo do arquivo.
            id_biblioteca (str, optional): Identificador da biblioteca. Obrigatório se
                foi passado algum valor para o parâmetro `nome_site` do construtor da
                classe. Caso contrário, o parâmetro é ignorado. Nesse último caso, o
                arquivo será subido no OneDrive do usuário.
            id_pasta (str, optional): Identificador da pasta onde o arquivo será subido.
                Se `None`, o arquivo é subido na raiz da biblioteca. Valor padrão é
                `None`.
            renomear (bool, optional): Se `True`, caso haja um arquivo com o mesmo nome,
                será criado um novo com outro nome. Se `False`, cajo haja um arquivo com
                o mesmo nome, será gerado um erro. Esse parâmetro é ignorado para
                arquivos pequenos (<= 4 MB). Caso já haja um arquivo pequeno com o mesmo
                nome do que está sendo subido, ele será substituído no destino. Valor
                padrão é `False`.
            progresso (bool, optional): Se `True`, será apresentado uma barra de
                progresso enquanto a subida do arquivo ocorre. Esse parânetro é ignorado
                para arquivos pequenos (<= 4 MB). Valor padrão é `True`.

        Raises:
            ValueError: Erro indicando que não foi encontrado o arquivo em `caminho`, ou
                que não foi passado um valor em `id_biblioteca` quando necessário.

        Returns:
            Um dicionário que contém as propriedades do arquivo subido.
        """
        if self.nome_site and not id_biblioteca:
            raise ValueError(
                "Parâmetro 'id_biblioteca' é obrigatório quando o objeto não representa"
                " a área pessoal do usuário."
            )

        if not os.path.isfile(caminho):
            raise ValueError(f"Arquivo {caminho} não encontrado.")

        tamanho_arquivo = os.path.getsize(caminho)

        if tamanho_arquivo <= TAM_ARQ_PEQ:
            return self._subir_arquivo_direto(
                caminho=caminho, id_biblioteca=id_biblioteca, id_pasta=id_pasta
            )
        else:
            return self._subir_arquivo_sessao_upload(
                caminho=caminho,
                id_biblioteca=id_biblioteca,
                id_pasta=id_pasta,
                renomear=renomear,
                progresso=progresso,
            )

    def _subir_arquivo_direto(self, caminho, id_biblioteca, id_pasta):
        nome_arquivo = os.path.basename(caminho)
        url = (
            self._url_api
            + (f"/drives/{id_biblioteca}/" if self.nome_site else "/drive/")
            + (f"items/{id_pasta}" if id_pasta else "root")
            + ":/"
            + nome_arquivo
            + ":/content"
        )

        # Subindo o arquivo
        data = open(caminho, "rb").read()
        r = self.session.put(url, data=data)

        return r.json()

    def _subir_arquivo_sessao_upload(
        self, caminho, id_biblioteca, id_pasta, renomear, progresso
    ):
        nome_arquivo = os.path.basename(caminho)
        tamanho_arquivo = os.path.getsize(caminho)

        # Criando sessão de upload
        up_session_url = (
            self._url_api
            + (f"/drives/{id_biblioteca}/" if self.nome_site else "/drive/")
            + (f"items/{id_pasta}" if id_pasta else "root")
            + ":/"
            + nome_arquivo
            + ":/createUploadSession"
        )
        up_session_data = {
            "item": {
                "@microsoft.graph.conflictBehavior": "rename" if renomear else "fail"
            }
        }
        upload_session = self.session.post(up_session_url, json=up_session_data).json()

        # Subindo o arquivo
        inicio = 0
        chunk_size = CHUNK_SIZE_UP
        with tqdm(total=100) as pbar:
            while inicio < tamanho_arquivo:
                fim = (
                    tamanho_arquivo
                    if inicio + chunk_size > tamanho_arquivo
                    else inicio + chunk_size
                )
                data = open(caminho, "rb").read(fim - inicio)

                if not data:
                    break

                headers = {"Content-Range": f"bytes {inicio}-{fim-1}/{tamanho_arquivo}"}

                if progresso:
                    pbar.update(inicio / tamanho_arquivo * 100)

                r = requests.put(
                    upload_session["uploadUrl"], data=data, headers=headers
                )
                inicio = fim

        return r.json()
