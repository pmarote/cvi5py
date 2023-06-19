"""Módulo com definições do sistema SIVEI."""

from urllib.parse import unquote

from bs4 import BeautifulSoup

from pepe import AuthenticationError, Sistema
from pepe.utils.login import login_identity_cert

URL_BASE = "https://www3.fazenda.sp.gov.br/SIVEI/"
URL_IDENTITY_INICIAL = (
    "https://www.identityprd.fazenda.sp.gov.br/v002/"
    "Sefaz.Identity.STS.Certificado/Logincertificado.aspx"
)
URL_WTREALM = (
    "https://www.identityprd.fazenda.sp.gov.br/v003/"
    "Sefaz.Identity.STS.Certificado.SSO/LoginSSO.aspx"
)
WCTX = "rm=0&id=STS.Certificado.SSO"
CLAIM_SETS = "00000001"
TIPO_LOGIN = "1"
AUTO_LOGIN = "1"


class Sivei(Sistema):
    """Classe Sivei."""

    def __init__(self, usar_proxy=False) -> None:
        """Classe Sivei."""
        super().__init__(usar_proxy=usar_proxy)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                + "AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/99.0.4844.83 Safari/537.36"
            }
        )

    def login_cert(self, nome_cert: str) -> None:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        url, _, wctx, claimsets = self._pre_login()
        outros_params = {
            "wfresh": "60",
            "wauth": "urn:oasis:names:tc:SAML:2.0:assertion",
            "Layout": "0",
        }
        cookies_aute, r = login_identity_cert(
            url_inicial=url,
            wtrealm=URL_WTREALM,
            claim_sets=claimsets,
            wctx=wctx,
            outros_params=outros_params,
            nome_cert=nome_cert,
            cookies=self.session.cookies,
        )
        self.session.cookies.update(cookies_aute)
        soup = BeautifulSoup(r.text, "html.parser")
        data = {"wa": "wsignin1.0"}
        data["wresult"] = soup.find("input", {"name": "wresult"})["value"]
        data["wctx"] = soup.find("input", {"name": "wctx"})["value"]
        url_post = soup.find("form", {"name": "hiddenform"}).get("action")
        r = self.session.post(url_post, data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", {"name": "hiddenform"})
        url_post = form.get("action")
        d, _ = self._get_hidden_input(form)
        self.session.post(url_post, data=d)

        if not self.autenticado():
            raise AuthenticationError()

    def _pre_login(self):
        # GET na URL base
        r = self.session.get(
            URL_BASE + "/LoginFazendarios/Login", allow_redirects=False
        )
        identidy_base = r.headers["Location"].split("/v003")[0]
        url_prox = r.headers["Location"]
        r = self.session.get(url_prox, allow_redirects=False)
        url_prox = identidy_base + r.headers["Location"]
        r = self.session.get(url_prox, allow_redirects=False)
        url_prox = r.headers["Location"]
        r = self.session.get(url_prox, allow_redirects=False)
        url_prox = identidy_base + r.headers["Location"]
        r = self.session.get(url_prox, allow_redirects=False)
        url_prox = r.headers["Location"]
        url = url_prox.split("?")[0]
        url = unquote(url)
        wtrealm = unquote(url_prox.split("wtrealm=")[1].split("&")[0])
        wctx = unquote(url_prox.split("wctx=")[1].split("&")[0])
        claimsets = url_prox.split("ClaimSets=")[1].split("&")[0]

        return url, wtrealm, wctx, claimsets

    def _get_hidden_input(self, el):
        hid_ipt = el.findAll("input")
        data = []
        file = []
        for hi in hid_ipt:
            if hi.get("name") is not None:
                file += [(hi.get("name"), None)]
                if hi.get("value") == "":
                    data += [(hi.get("name"), None)]
                else:
                    data += [(hi.get("name"), hi.get("value"))]
        return data, file

    def autenticado(self) -> bool:
        """Ver classe base ([Sistema][1]).

        [1]: https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60
        """  # noqa: E501
        r = self.session.get(URL_BASE)

        return "consultarAcessoRapidoForm" in r.text
