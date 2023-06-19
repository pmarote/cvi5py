"""Módulo com definições que servem de base para outros sistemas."""

import requests
import urllib3
import wrapt
from requests.exceptions import ConnectionError

PROXY_URL = "http://proxyservidores.lbintra.fazenda.sp.gov.br:8080"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@wrapt.decorator
def preparar_metodo(wrapped, instance, args, kwargs):
    """Decorator que adiciona verificações aos métodos de um sistema."""
    if not instance.autenticado():
        raise AuthenticationError(
            "É necessário se autenticar através dos métodos login ou login_cert "
            f"antes de usar o método {wrapped.__name__}."
        )

    return wrapped(*args, **kwargs)


class Sistema:
    """Classe base para sistemas.

    Classes derivadas devem implementar todos os métodos dessa classe, exceto os métodos
    que se iniciam com `login` (no mínimo um método de login deve ser implementado).

    Attributes:
        session (requests.session): Session usada para requisições ao sistema.
    """

    def __init__(self, usar_proxy: bool = False) -> None:
        """Cria um objeto da classe Sistema.

        Args:
            usar_proxy (bool, opcional): Define se o sistema deve usar o proxy da Sefaz.
                Geralmente o valor desse parâmetro deve ser `True` quando o sistema for
                externo e seu acesso será feito a partir da rede da Sefaz. Valor padrão
                é `False`.

        Raises:
            ConnectionError: Erro ao configurar o proxy.
        """
        print("#DEBUG#Sistema#Classe Sistema iniciada")
        self.session = requests.session()
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }
        # print("#DEBUG#Sistema#self.session#", self.session)

        if usar_proxy:
            print("#DEBUG#Sistema#Usando proxy")
            proxies = {
                "http": PROXY_URL,
                "https": PROXY_URL,
            }
            self.session.proxies.update(proxies)

            # Checar conexão com o proxy
            try:
                self.session.head("https://www.google.com/")  # URL externa
            except ConnectionError as e:
                raise ConnectionError(
                    "Erro de conexão durante a configuração do proxy."
                    "Você está na rede da Sefaz?"
                ) from e

    def login(self, usuario: str, senha: str) -> None:
        """Realiza o login no sistema por meio de usuario e senha.

        Args:
            usuario (str): Nome de usuário.
            senha (str): Senha do usuário.

        Raises:
            NotImplementedError: Indica que esse método de login não foi implementado.
        """
        raise NotImplementedError(
            "login() não implementado para esse sistema. Tente usar login_cert()."
        )

    def login_cert(self, nome_cert: str) -> None:
        """Realiza o login no sistema com um certificado digital.

        Args:
            nome_cert (str): Nome do certificado, geralmente o nome completo do usuário
                em letras maiúsculas.

        Raises:
            NotImplementedError: Indica que esse método de login não foi implementado.
        """
        raise NotImplementedError(
            "login_cert() não implementado para esse sistema. Tente usar login()."
        )

    def autenticado(self) -> bool:
        """Verifica se sistema se encontra autenticado.

        Returns:
            `True` se o sistema estiver corretamente autenticado. Do contrário `False`.
        """
        raise NotImplementedError()

    def logout(self) -> None:
        """Realiza o logout no sistema."""
        pass


class AuthenticationError(Exception):
    """Representa erros de autenticação nos sistemas."""

    pass
