"""Módulo com definições do sistema Outlook."""

from pepe import Graph, preparar_metodo
from pepe.sistemas.graph import URL_API

URL_BASE = "https://outlook.office365.com/"


class Outlook(Graph):
    """Representa o sistema [Outlook](https://outlook.office365.com/).

    Para maiores detalhes, ver classe base ([Graph](https://ads.intra.fazenda.sp.gov.br/tfs/PRODUTOS/pepe/_wiki/wikis/pepe-wiki?pagePath=%2Fsistemas.base&anchor=<kbd>class<%2Fkbd>-%60sistema%60)).
    """  # noqa: E501

    @preparar_metodo
    def enviar_email(
        self,
        para: str,
        cc: str = None,
        bcc: str = None,
        assunto: str = None,
        mensagem: str = None,
        tipo_conteudo: str = "text",
        importancia: str = "normal",
        json: dict = None,
    ) -> None:
        """Envia um email.

        Args:
            para (str | list): Destinatário ou lista de destinatários.
            cc (str | list, optional): Destinatário ou lista de destinatários em cópia.
            bcc (str | list, optional): Destinatário ou lista de destinatários em cópia
                oculta.
            assunto (str, optional): Assunto do email.
            mensagem (str, optional): Corpo da mensagem.
            tipo_conteudo (str, optional): Tipo do conteúdo em `mensagem`. Pode ser
                `"text"` ou `"html"`. Valor padrão é `"text"`.
            importancia (str, optional): Importância do email. Pode ser `"low"` (baixa),
                `"normal"` e `"high"` (alta). Valor padrão é `"normal"`.
            json (dict, optional): Mensagem completa no formato
                [*message resource type*][1]. Deve ser usado para mensagens mais
                complexas. Se passado um valor para esse parâmetro, todos os demais
                parâmetros são ignorados.

        [1]: https://learn.microsoft.com/graph/api/resources/message#properties
        """
        url = URL_API + "users/" + self._user_id + "/sendMail"

        if json:
            self.session.post(url, json=json)
            return
        else:
            if not isinstance(para, list):
                para = [para]

            if not isinstance(cc, list):
                cc = [cc]

            if not isinstance(bcc, list):
                bcc = [bcc]

            data = {
                "message": {
                    "toRecipients": [
                        {"emailAddress": {"address": end}} for end in para if end
                    ],
                    "ccRecipients": [
                        {"emailAddress": {"address": end}} for end in cc if end
                    ],
                    "bccRecipients": [
                        {"emailAddress": {"address": end}} for end in bcc if end
                    ],
                    "subject": assunto,
                    "body": {"contentType": tipo_conteudo, "content": mensagem},
                    "importance": importancia,
                }
            }

            self.session.post(url, json=data)
