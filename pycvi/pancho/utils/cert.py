"""Módulo com funções utilitárias para lidar com certificados."""

import datetime
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID


def listar_nomes_certs(store_name="MY", somente_validos=False):
    """Lista os nomes dos certificados instalados na máquina.

    Args:
        store_name (str, optional): Nome do repositório de certificados a ser
            consultado. Valores comuns são `"MY"`, `"CA"` e `"ROOT"`. Valor padrão é
            `"MY"`.
        somente_validos (bool, optional): Se `True`, lista apenas certificados com data
            de expiração válida. Valor padrão é `False`.

    Returns:
        Uma lista de nomes de certificados.
    """
    certs = ssl.enum_certificates(store_name=store_name)
    cert_bytes = [cert[0] for cert in certs]
    cert_decodados = [x509.load_der_x509_certificate(cert_b) for cert_b in cert_bytes]
    nomes = [
        cert_dec.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        for cert_dec in cert_decodados
        if not somente_validos or cert_dec.not_valid_after > datetime.datetime.now()
    ]

    return nomes
