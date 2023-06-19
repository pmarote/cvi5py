"""Módulo com definições do sistema OneDrive."""


import pepe.sistemas.base
import pepe.sistemas.graph
import pepe.sistemas.sharepointonline
from pepe import preparar_metodo
from pepe.sistemas.graph import URL_API


class OneDrive(pepe.sistemas.graph.Graph):
    # TODO: Fazer essa classe ser derivada (ou composição) da classe SharePointOnline
    """Representa o sistema [OneDrive](https://fazendaspgovbr-my.sharepoint.com/personal/<usuario>_fazenda_sp_gov_br/_layouts/15/onedrive.aspx).

    Para maiores detalhes, ver classe base ([Graph](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy: bool = False, escopos: list = None) -> None:
        """Cria um objeto da classe OneDrive.

        Args:
            usar_proxy (bool, optional): ver classe base ([Graph][1]).
            escopos (list, optional): ver classe base ([Graph][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60graph%60
        """  # noqa: E501
        super().__init__(usar_proxy, escopos)
        self.shp = pepe.sistemas.sharepointonline.SharePointOnline()

    def login(self, usuario: str, senha: str = None, nome_cert: str = None) -> None:
        """Ver classe base ([Sistema][1]).

        Args:
            usuario (str): Nome de usuário, sem `"INTRA/"`.
            senha (str, optional): Não utilizado. Presente apenas por compatibilidade.
            nome_cert (str, optional): Nome do certificado, geralmente o nome completo
                do usuário em letras maiúsculas. Se passado algum valor para esse
                parâmetro, será tentado o login com certificado caso não seja possível
                realizar o login apenas com o nome do usuário.

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        super().login(usuario, senha, nome_cert)
        self.shp.login(usuario, senha, nome_cert)

    @preparar_metodo
    def listar_itens(self, id_pasta: str = None, termo_busca: str = None) -> list:
        """Lista itens do OneDrive (pastas e arquivos).

        Args:
            id_pasta (str, optional): Identificador da pasta de onde serão listados os
                itens. Se `None`, são listados os itens da raiz. Valor padrão é `None`.
            termo_busca (str, optional): Termo para busca de itens. Itens são buscados
                a partir da pasta indicada em `id_pasta` (ou raiz se `id_pasta` é
                `None`), incluindo subpastas. Valor padrão é `None`.

        Returns:
            Uma lista de dicionários, em que cada dicionário contém propriedades de
            um item do OneDrive.
        """
        url = (
            URL_API
            + "users/"
            + self._user_id
            + "/drive/"
            + ("items/" + id_pasta if id_pasta else "root")
            + ("/search(q=')" + termo_busca + "')" if termo_busca else "/children")
        )
        r = self.session.get(url)

        return r.json()["value"]

    @preparar_metodo
    def obter_item(self, id_item: str) -> dict:
        """Obtém detalhes de um item do OneDrive (pasta ou arquivo).

        Args:
            id_item (str): Identificador do item.

        Returns:
            Um dicionário que contém as propriedades do item.
        """
        url = URL_API + "users/" + self._user_id + "/drive/items/" + id_item
        r = self.session.get(url)

        return r.json()

    @preparar_metodo
    def baixar_arquivo(self, id_arquivo: str, caminho: str) -> None:
        """Baixa um arquivo do OneDrive.

        Args:
            id_arquivo (str): Identificador do arquivo.
            caminho (str): Caminho completo onde será salvo o arquivo, incluindo seu
                nome.
        """
        url = (
            URL_API
            + "users/"
            + self._user_id
            + "/drive/items/"
            + id_arquivo
            + "/content"
        )
        r = self.session.get(url, headers=None)

        with open(caminho, "wb") as f:
            f.write(r.content)

    @preparar_metodo
    def criar_pasta(
        self, nome: str, id_pasta_pai: str = None, renomear: bool = False
    ) -> dict:
        """Cria uma pasta.

        Args:
            nome (str): Nome da pasta a ser criada.
            id_pasta_pai (str, optional): Identificador da pasta onde a nova pasta será
                criada. Se `None`, a nova pasta é criada na raiz. Valor padrão é `None`.
            renomear (bool, optional): Indica o que deve ser feito caso já exista uma
                pasta com o mesmo nome. Se `True`, um novo nome é gerado
                automaticamente. Se `False`, um erro ocorre. Valor padrão é `False`.

        Returns:
            Um dicionário que contém as propriedades da pasta criada.
        """
        url = (
            URL_API
            + "users/"
            + self._user_id
            + "/drive/"
            + ("items/" + id_pasta_pai if id_pasta_pai else "/root")
            + "/children"
        )
        data = {
            "name": nome,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename" if renomear else "fail",
        }
        r = self.session.post(url, json=data)

        return r.json()

    @preparar_metodo
    def subir_arquivo(self, caminho: str, id_pasta: str = None) -> dict:
        """Sobe (upload) um arquivo no OneDrive.

        Args:
            caminho (str): Caminho completo do arquivo.
            id_pasta (str, optional): Identificador da pasta onde o arquivo será subido.
                Se `None`, o arquivo é subido na raiz. Valor padrão é `None`.

        Raises:
            ValueError: Erro indicando que não foi encontrado o arquivo em `caminho`.

        Returns:
            Um dicionário que contém as propriedades do arquivo subido.
        """
        return self.shp.subir_arquivo(caminho=caminho, id_pasta=id_pasta, renomear=True)

    @preparar_metodo
    def renomear_item(self, id_item: str, novo_nome: str) -> dict:
        """Renomeia um item do OneDrive (pasta ou arquivo).

        Args:
            id_item (str): Identificador do item.
            novo_nome (str): Novo nome do item.

        Returns:
            Um dicionário que contém as propriedades do item modificado.
        """
        url = URL_API + "users/" + self._user_id + "/drive/items/" + id_item
        data = {"name": novo_nome}
        r = self.session.patch(url, json=data)

        return r.json()

    @preparar_metodo
    def mover_item(self, id_item: str, id_pasta_destino: str) -> None:
        """Move um item do OneDrive (pasta ou arquivo) para uma outra pasta.

        Args:
            id_item (str): Identificador do item a ser movido.
            id_pasta_destino (str): Identificador da pasta para onde o item será movido.
        """
        url = URL_API + "users/" + self._user_id + "/drive/items/" + id_item
        data = {"parentReference": {"id": id_pasta_destino}}
        self.session.patch(url, json=data)

    @preparar_metodo
    def deletar_item(self, id_item: str) -> None:
        """Deleta um item do OneDrive (pasta ou arquivo).

        Args:
            id_item (str): Identificador do item.
        """
        url = URL_API + "users/" + self._user_id + "/drive/items/" + id_item
        self.session.delete(url)
