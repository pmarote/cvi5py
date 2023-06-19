"""Módulo com definições do sistema Graph."""

import json
from urllib.parse import parse_qs, urlsplit

import win32com.client
from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema

TENANT_ID = "ccb3a8f5-7e40-4e20-9b73-2a6bd0be61a4"
CLIENT_ID = "479f6bd7-b497-4379-9f39-6a6fd8dbee6a"
ESCOPOS = ["openid"]

URL_LOGIN = "https://login.microsoftonline.com"
URL_LOGIN_SRF = URL_LOGIN + "/login.srf"
REDIRECT_URI = URL_LOGIN + "/common/oauth2/nativeclient"
URL_AUTHORIZE = URL_LOGIN + "/" + TENANT_ID + "/oauth2/v2.0/authorize"
URL_GET_CREDENTIAL_TYPE = URL_LOGIN + "/common/GetCredentialType"
URL_TOKEN = URL_LOGIN + "/" + TENANT_ID + "/oauth2/v2.0/token"
URL_API = "https://graph.microsoft.com/v1.0/"
URL_AAD_LOGIN = "https://fazendaspgovbr-onmicrosoft-com.access.mcas.ms/aad_login"


class Graph(Sistema):
    """Representa a API [Graph](https://graph.microsoft.com/).

    Através da API Graph é possível acessar sistemas fazendários na nuvem da Microsoft.
    Recomenda-se usar essa classe como base desses sistemas.

    Para maiores detalhes, ver classe base ([Sistema](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    def __init__(self, usar_proxy: bool = False, escopos: list = None) -> None:
        """Cria um objeto da classe Graph.

        Args:
            usar_proxy (bool, optional): ver classe base ([Sistema][1]).
            escopos (list, optional): lista de escopos necessários para realizar as
                operações no sistema. Um escopo é uma permissão de acesso. A lista
                completa de escopos pode ser consultada nessa [página][2] (seções
                "Permissões delegadas"). Se nenhum valor for passado, a lista
                `["openid"]` será utilizada.

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60

        [2]: https://learn.microsoft.com/graph/permissions-reference
        """  # noqa: E501
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/104.0.0.0 Safari/537.36",
            }
        )

        if escopos is None:
            self.escopos = ESCOPOS
        else:
            self.escopos = escopos

            if "openid" not in self.escopos:
                self.escopos.insert(0, "openid")

        self._user_id = None

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        return "Authorization" in self.session.headers

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
        usuario = usuario.lower()

        try:
            auth_code = self._get_auth_code(modo="kerberos", usuario=usuario)
        except Exception:
            if nome_cert:
                auth_code = self._get_auth_code(
                    modo="cert", usuario=usuario, nome_cert=nome_cert
                )
            else:
                raise AuthenticationError(
                    "Não foi possível realizar o login. "
                    "Se não estiver conectado à rede da Sefaz, "
                    "passe um valor para o parâmetro 'nome_cert' "
                    "ou tente usar o método 'login_cert'"
                )

        token = self._get_token(auth_code)
        self.session.headers.update({"Authorization": "Bearer " + token})
        user_json = self._get_user(usuario)
        self._user_id = user_json["id"]
        self._usuario = usuario

        if not self.autenticado():
            raise AuthenticationError()

    def login_cert(self, nome_cert: str, usuario: str) -> None:
        """Ver classe base ([Sistema][1]).

        Esse método de login não funciona na rede interna da Sefaz.

        Args:
            nome_cert (str): Nome do certificado, geralmente o nome completo do usuário
                em letras maiúsculas.
            usuario (str): Nome de usuário, sem `"INTRA/"`.

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        usuario = usuario.lower()
        auth_code = self._get_auth_code(
            modo="cert", usuario=usuario, nome_cert=nome_cert
        )
        token = self._get_token(auth_code)
        self.session.headers.update({"Authorization": "Bearer " + token})
        user_json = self._get_user(usuario)
        self._user_id = user_json["id"]
        self._usuario = usuario

        if not self.autenticado():
            raise AuthenticationError()

    def _get_auth_code(self, modo, usuario, nome_cert=None):
        scope = " ".join(self.escopos)
        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "response_mode": "query",
            "scope": scope,
            "sso_reload": "true",
        }
        r = self.session.get(URL_AUTHORIZE, params=params)
        response = (r.text).split(";\n//]]")[0].split("[CDATA[\n$Config=")[1]
        response = json.loads(response)
        flowToken = response["sFT"]
        apiCanary = response["apiCanary"]
        originalRequest = response["sCtx"]
        clientRequestID = response["correlationId"]
        hpgRequestId = response["sessionId"]
        data = {
            "mkt": "pt-BR",
            "username": usuario + "@fazenda.sp.gov.br",
            "isOtherIdpSupported": "true",
            "checkPhones": "false",
            "isRemoteNGCSupported": "true",
            "isCookieBannerShown": "false",
            "isFidoSupported": "true",
            "originalRequest": originalRequest,
            "country": "BR",
            "forceotclogin": "false",
            "isExternalFederationDisallowed": "false",
            "isRemoteConnectSupported": "false",
            "federationFlags": "0",
            "isSignup": "false",
            "flowToken": flowToken,
            "isAccessPassSupported": True,
        }
        headers = {
            "canary": apiCanary,
            "client-request-id": clientRequestID,
            "hpgrequestid": hpgRequestId,
        }
        r = self.session.post(URL_GET_CREDENTIAL_TYPE, json=data, headers=headers)

        # Post para https://sts.fazenda.sp.gov.br/adfs/ls/?client-request-id
        url = r.json()["Credentials"]["FederationRedirectUrl"]
        url = url.replace("&wctx=", "&wctx=LoginOptions%3d3%26") + "&cbcxt=&mkt=&lc="
        data = {
            "username": usuario + "@fazenda.sp.gov.br",
            "isOtherIdpSupported": "true",
            "checkPhones": "false",
            "isRemoteNGCSupported": "true",
            "isCookieBannerShown": "false",
            "isFidoSupported": "true",
            "originalRequest": originalRequest,
            "country": "BR",
            "forceotclogin": "false",
            "isExternalFederationDisallowed": "false",
            "isRemoteConnectSupported": "false",
            "federationFlags": 0,
            "isSignup": "false",
            "flowToken": flowToken,
            "isAccessPassSupported": "true",
        }
        winhttp = win32com.client.Dispatch("WinHTTP.WinHTTPRequest.5.1")

        if modo == "cert":
            r = self.session.post(url, data=data)
            texto_resposta = self._make_cert_request(r.url, nome_cert, winhttp)
        elif modo == "kerberos":
            r = self.session.get(url, allow_redirects=False)
            texto_resposta = self._make_kerberos_request(r.headers["location"], winhttp)
        else:
            raise ValueError("modo deve receber 'cert' ou 'kerberos'.")

        # TEM UNS COOKIES QUE PRECISO MONTAR NA MÃO...
        cookie_resposta = winhttp.GetResponseHeader("Set-Cookie")
        chave_cookie = cookie_resposta.split("=")[0]
        valor_cookie = cookie_resposta.split(";")[0].replace(chave_cookie + "=", "")
        cookies_na_mao = {
            chave_cookie: valor_cookie,
            "ESTSWCTXFLOWTOKEN": flowToken,
            "AADSSO": "NA|NoExtension;SSOCOOKIEPULLED=1",
        }
        self.session.cookies.update(cookies_na_mao)

        # Post login.srf
        wctx_post = parse_qs(urlsplit(url).query)["wctx"][0]
        soup = BeautifulSoup(texto_resposta, "html.parser")
        data = {
            "wa": "wsignin1.0",
            "wresult": soup.find("input", {"name": "wresult"})["value"],
            "wctx": wctx_post,
        }
        login_srf_r = self.session.post(URL_LOGIN_SRF, data=data)

        # Post aad_login
        soup = BeautifulSoup(login_srf_r.text, "html.parser")
        data = {"id_token": soup.find("input", {"name": "id_token"})["value"]}
        aad_login_r = self.session.post(URL_AAD_LOGIN, data=data)

        if "?code=" in aad_login_r.url:
            code = parse_qs(urlsplit(aad_login_r.url).query)["code"][0]

            return code
        else:
            raise AuthenticationError()

    def _make_kerberos_request(self, location_url, winhttp):
        winhttp.SetAutoLogonPolicy(0)
        winhttp.Open("GET", location_url)
        winhttp.Send()
        return winhttp.responseText

    def _make_cert_request(self, sts_url, nome_cert, winhttp):
        # https://sts.fazenda.sp.gov.br/adfs/ls/?client-request-id
        data = "AuthMethod=CertificateAuthentication&RetrieveCertificate=1"
        winhttp.Open("POST", sts_url)
        winhttp.SetClientCertificate(nome_cert)
        winhttp.Send(data)
        texto_resposta = winhttp.responseText

        if "wresult" not in texto_resposta:
            raise AuthenticationError("Erro de autenticação: wresult não encontrado")

        return texto_resposta

    def _get_token(self, auth_code) -> str:
        """Troca o authorization code por um token."""
        scope = " ".join(self.escopos)
        data = {
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "scope": scope,
            "code": auth_code,
        }
        r = self.session.post(URL_TOKEN, data=data)
        token = r.json()["access_token"]

        return token

    def _get_user(self, login_fazendario: str) -> json:
        url = URL_API + "users/" + login_fazendario + "@fazenda.sp.gov.br"
        r = self.session.get(url)

        return r.json()
