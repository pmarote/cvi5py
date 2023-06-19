"""Módulo com funções utilitárias para login em sistemas."""

from datetime import datetime
from typing import Dict
from urllib.parse import parse_qs, urlsplit

import requests
import win32com.client
from bs4 import BeautifulSoup
from pycvi.pancho import AuthenticationError
from pywintypes import com_error

IDENTITY_URL = "https://www.identityprd.fazenda.sp.gov.br/"


def login_identity_cert(
    nome_cert: str,
    url_inicial: str,
    wtrealm: str,
    claim_sets: str,
    wctx: str,
    outros_params: Dict[str, str] = None,
    cookies: requests.cookies.RequestsCookieJar = None,
):
    """Realiza o login em um sistema com certificado por meio do sistema Identity.

    Você pode descobrir os valores a serem passados aos parâmetros `url_inicial`,
    `wtrealm`, `claim_sets`, `wctx` e `outros_params` inpecionando o tráfego de rede
    durante o login feito no sistema pelo console de desenvolvedor do navegador.

    Args:
        nome_cert (str): Nome do certificado que será usado no login.
        url_inicial (str): URL da página onde se inicia o processo de login.
        wtrealm (str): O realm do sistema, conforme cadastrado no Identity.
        claim_sets (str): Hexadecimal de 8 dígitos que codifica o conjunto de claims.
        wctx (str): parâmetros de contexto para serem devolvidos ao sistema após o
            login.
        outros_params (Dict[str, str], optional): Outros parâmetros para serem passados
            ao Identity. Valores comuns são "TipoLogin" e "AutoLogin".
        cookies (requests.cookies.RequestsCookieJar, optional): conjunto de cookies
            obtidos anteriormente para serem usados no processo de login.

    Returns:
        Uma tupla `(cookies, req)`, onde `cookies` são os cookies obtidos para o sistema
        após o login e `req` é o resultado da última requisição do procedimento de
        login.
    """
    session = requests.Session()

    if cookies:
        session.cookies.update(cookies)

    params = {
        "wa": "wsignin1.0",
        "wct": str(datetime.utcnow()).split(".")[0].replace(" ", "T") + "Z",
        "wtrealm": wtrealm,
        "ClaimSets": claim_sets,
        "wctx": wctx,
    }

    if outros_params:
        params = outros_params | params

    try:
        r = session.get(url_inicial, params=params)
        r.raise_for_status()

    # Requests não suporta certificados em smarcards, WinHttp (PyWin32) sim
    except requests.exceptions.HTTPError as e:
        # Tratar apenas erro de certificado
        if not str(e).startswith("403"):
            raise AuthenticationError("Erro de autenticação com o Identity: " + str(e))

        winhttp = win32com.client.Dispatch("WinHTTP.WinHTTPRequest.5.1")
        winhttp.Open("GET", r.url)
        winhttp.SetClientCertificate(nome_cert)
        winhttp.SetOption(9, 512)  #  forçando tls 1.1

        try:
            winhttp.Send()
        except com_error as e:
            if "É necessário um certificado para concluir a autenticação" in str(e):
                raise AuthenticationError(
                    "Erro de certificado. "
                    "Você digitou o nome do certificado corretamente? "
                    "Você pode verificar os certificados disponíveis por meio da função"
                    " pepe.utils.cert.listar_nomes_certs."
                )
            else:
                raise e

        texto_resposta = winhttp.responseText

        if "wresult" not in texto_resposta:
            raise AuthenticationError(
                "Erro de autenticação com o Identity: wresult não encontrado"
            )

        # É preciso enviar POST para algumas URLs para completar a autenticação
        data = {"wa": "wsignin1.0"}

        urls_post = [
            h.url.split("?")[0]
            for h in r.history
            if h.url.startswith(IDENTITY_URL) and "Account/Login.aspx" not in h.url
        ]
        urls_post.reverse()
        urls_post.append(wtrealm)

        wctx_post = [
            parse_qs(urlsplit(h.headers["location"]).query)["wctx"]
            for h in r.history
            if "Account/Login.aspx" in h.url
        ]
        wctx_post.reverse()
        wctx_post.append(wctx)

        for url_p, wtcx_p in zip(urls_post, wctx_post):
            soup = BeautifulSoup(texto_resposta, "html.parser")
            data["wresult"] = soup.find("input", {"name": "wresult"})["value"]
            data["wctx"] = wtcx_p
            r = session.post(url_p, data=data)
            texto_resposta = r.text

    return session.cookies, r
