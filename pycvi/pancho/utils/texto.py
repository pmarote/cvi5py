"""Módulo com funções utilitárias para manipulação de strings."""

import re
from datetime import datetime
from difflib import SequenceMatcher


def formatar_mes_referencia(ref: str, formato_saida: str):
    """Formata um mês de referência.

    Args:
        ref (str): mês de referência para ser formatado. Pode ser qualquer string no
            formato mm/aaaa ou mm_aaaa, onde mm são os dois dígitos que representam o
            mês e aaa os quatro digitos que representam o ano.
        formato_saida (str): formato que deve ser utilizado. Formatos suportados são:
            - `mm/aaaa`: numérico separado por /
            - `MM/aaaa`: mês por extenso separado por /
            - `mm_aaaa`: numérico separado por _
            " `MM/aaaa`: mês por extenso separado por _

    Returns:
        Uma string com o mês de referência no formato especificado.

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `ref` não está no
            formato mm/aaaa ou mm_aaaa, ou o valor passado para o parâmetro
            `formato_saida` não é suportado.
    """
    meses = {
        "01": "JANEIRO",
        "02": "FEVEREIRO",
        "03": "MARCO",
        "04": "ABRIL",
        "05": "MAIO",
        "06": "JUNHO",
        "07": "JULHO",
        "08": "AGOSTO",
        "09": "SETEMBRO",
        "10": "OUTUBRO",
        "11": "NOVEMBRO",
        "12": "DEZEMBRO",
    }
    ref_digits = "".join(i for i in ref if i.isdigit())

    # POSSIBILIDADES DE SEPARADORES NA ENTRADA
    if ("/" not in ref and "_" not in ref) or len(ref_digits) != 6:
        raise ValueError("ref deve ter o formato mm/aaaa ou mm_aaaa")

    if (
        formato_saida != "mm/aaaa"
        and formato_saida != "MM/aaaa"
        and formato_saida != "mm_aaaa"
        and formato_saida != "MM_aaaa"
    ):
        raise ValueError(
            "formato de saída deve ser: mm/aaaa (numérico separado por / ) "
            "ou MM/aaaa (mês por extenso separado por / ) "
            "ou mm_aaaa (numérico separado por _ )"
            "ou MM/aaaa (mês por extenso separado por _ )"
        )

    if formato_saida == "mm/aaaa":
        return ref_digits[0:2] + "/" + ref_digits[2:6]
    if formato_saida == "mm_aaaa":
        return ref_digits[0:2] + "_" + ref_digits[2:6]
    if formato_saida == "MM/aaaa":
        return meses[ref_digits[0:2]].lower() + "/" + ref_digits[2:6]
    if formato_saida == "MM_aaaa":
        return meses[ref_digits[0:2]].lower() + "_" + ref_digits[2:6]


def formatar_data(data: str, formato_saida: str):
    """Formata uma data.

    Args:
        data (str): data para ser formatada. Pode ser qualquer string no formato
            dd/mm/yy ou dd/mm/yyyy e com algum dos seguintes separadores: `/`, `-`, `_`,
            `.` ou espaço.
        formato_saida (str): formato que deve ser utilizado. Formatos suportados são os
            mesmos suportados pela função [`strftime`][1].

    Returns:
        Uma string com a data no formato especificado.

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `data` não está no
            formato correto ou o valor passado para o parâmetro `formato_saida` não é
            suportado.

    [1]: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    """  # noqa: E501
    # POSSIBILIDADES DE SEPARADORES NA ENTRADA
    if "/" in data:
        formato_entrada = "%d/%m/%y"
    elif "-" in data:
        formato_entrada = "%d-%m-%y"
    elif "_" in data:
        formato_entrada = "%d_%m_%y"
    elif "." in data:
        formato_entrada = "%d.%m.%y"
    else:
        raise ValueError(
            "data de entrada deve utilizar algum dos seguintes separadores: / - _ ."
        )

    # CONFIRMO SE É DATA VÁLIDA NA ENTRADA, E CONVERTO PRO PADRÃO NA SAÍDA
    try:  # ANO COM DOIS DÍGITOS %y
        return datetime.strptime(data, formato_entrada).strftime(formato_saida)

    except ValueError:  # ANO COM QUATRO DÍGITOS %Y
        try:
            return datetime.strptime(
                data, formato_entrada.replace("%y", "%Y")
            ).strftime(formato_saida)

        except ValueError:
            raise ValueError(
                "data deve ter o formato dd/mm/yy ou dd/mm/yyyy e algum dos seguintes"
                " separadores: / - _ . ou espaço"
            )


#
#     SE NO FUTURO QUISER REVERTER PRA REGEX, TÁ FEITO
#     data_regex = re.compile(
#         r"""(
#         [0|1|2|3]?\d            # DIA, PODENDO OU NÃO TER O PRIMEIRO DÍGITO 0
#         (/|-|_)                 # SEPARADOR
#         [0|1]?\d                # MÊS, PODENDO OU NÃO TER O PRIMEIRO DÍGITO 0
#         (/|-|_)                 # SEPARADOR
#         (\d{2})?\d{2}           # ANO, PODENDO OU NÃO TER OS PRIMEIROS DÍGITOS
#         )""", # FORMATO dD/mM/aaAA ou dD-mM-aaAA ou dD_mM_aaAA
#     re.VERBOSE,
# )

#     try:
#         return data_regex.search(data)[0]
#     except TypeError:
#         raise Exception("data deve ter o formato dd/mm/aaaa com separador /, - ou _")


def formatar_cep(cep: str):
    """Formata um número de CEP.

    Args:
        cep (str): CEP para ser formatado. Pode ser qualquer string contendo 8 números.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos do CEP e `completa` é um `str` no formato "XX.XXX-XXX".

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `cep` não é uma
            string que contém 8 números.
    """
    cep_digits = "".join(i for i in cep if i.isdigit())

    if len(cep_digits) != 8:
        raise Exception("cep deve ser uma string com 8 dígitos.")

    cep_char = cep_digits[0:2] + "." + cep_digits[2:5] + "-" + cep_digits[5:8]

    return cep_digits, cep_char


def formatar_ie(ie: str):
    """Formata um número de Inscrição Estadual (IE).

    Args:
        ie (str): IE para ser formatada. Pode ser qualquer string contendo 12 números.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos da IE e `completa` é um `str` no formato "XXX.XXX.XXX.XXX".

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `ie` não é uma
            string que contém 12 números.
    """
    ie_digits = "".join(i for i in ie if i.isdigit())

    if len(ie_digits) != 12:
        raise Exception("ie deve ser conter 12 números.")

    ie_char = (
        ie_digits[0:3]
        + "."
        + ie_digits[3:6]
        + "."
        + ie_digits[6:9]
        + "."
        + ie_digits[9:12]
    )

    return ie_digits, ie_char


def formatar_cnpj(cnpj: str, base: bool = False):
    """Formata um número de CNPJ.

    Args:
        cnpj (str): CNPJ para ser formatado. Pode ser qualquer string contendo 14
            números. Se `base` é `False`, a string pode conter apenas 8 números.
        base (bool, optional): indica se deve ser retornado apenas o número base. Valor
            padrão é `False`.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos do CNPJ e `completa` é um `str` no formato "XX.XXX.XXX/XXXX-XX", se
            `base` é `False`, ou "XX.XXX.XXX", se `base` é `True`.

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `cnpj` não é uma
            string que contém 8 ou 14 números.
    """
    cnpj_digits = "".join(i for i in cnpj if i.isdigit())

    if not base:
        if len(cnpj_digits) != 14:
            raise Exception("cnpj deve conter 14 números.")

        cnpj_char = (
            cnpj_digits[0:2]
            + "."
            + cnpj_digits[2:5]
            + "."
            + cnpj_digits[5:8]
            + "/"
            + cnpj_digits[8:12]
            + "-"
            + cnpj_digits[12:14]
        )

    else:
        if len(cnpj_digits) != 14 and len(cnpj_digits) != 8:
            raise Exception("cnpj deve ter ao menos 8 ou 14 números.")

        cnpj_digits = cnpj_digits[0:8]

        cnpj_char = cnpj_digits[0:2] + "." + cnpj_digits[2:5] + "." + cnpj_digits[5:8]

    return cnpj_digits, cnpj_char


def formatar_nire(nire: str):
    """Formata um número de NIRE.

    Args:
        nire (str): NIRE para ser formatado. Pode ser qualquer string contendo 11
            números.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos do NIRE e `completa` é um `str` no formato "XX.X.XXXXXXX-X".

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `nire` não é uma
            string que contém 11 números.
    """
    nire_digits = "".join(i for i in nire if i.isdigit())

    if len(nire_digits) != 11:
        raise ValueError("nire deve conter 11 números.")

    nire_char = (
        nire_digits[0:2]
        + "."
        + nire_digits[2:3]
        + "."
        + nire_digits[3:10]
        + "-"
        + nire_digits[10:11]
    )

    return nire_digits, nire_char


def formatar_cnae(cnae: str):
    """Formata um número de CNAE.

    Args:
        cnae (str): CNAE para ser formatado. Pode ser qualquer string contendo 7
            números.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos do CNAE e `completa` é um `str` no formato "XX.XX-X/XX".

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `cnae` não é uma
            string que contém 7 números.
    """
    cnae_digits = "".join(i for i in cnae if i.isdigit())

    if len(cnae_digits) != 7:
        raise ValueError("cnae deve conter 7 números.")

    cnae_char = (
        cnae_digits[0:2]
        + "."
        + cnae_digits[2:4]
        + "-"
        + cnae_digits[4:5]
        + "/"
        + cnae_digits[5:7]
    )

    return cnae_digits, cnae_char


def formatar_cpf(cpf: str):
    """Formata um número de CPF.

    Args:
        cpf (str): CPF para ser formatado. Pode ser qualquer string contendo 11 números.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos do CPF e `completa` é um `str` no formato "XXX.XXX.XXX-XX".

    Raises:
        ValueError: Erro indicando que valor passado para o parâmetro `cpf` não é uma
            string que contém 11 números.
    """
    cpf_digits = "".join(i for i in cpf if i.isdigit())

    if len(cpf_digits) != 11:
        raise ValueError("cpf deve conter com 11 números.")

    cpf_char = (
        cpf_digits[0:3]
        + "."
        + cpf_digits[3:6]
        + "."
        + cpf_digits[6:9]
        + "-"
        + cpf_digits[9:11]
    )

    return cpf_digits, cpf_char


def formatar_crc(crc: str):
    """Formata um número de CRC (Conselho Regional de Contabilidade).

    Args:
        crc (str): CRC para ser formatado. Pode ser qualquer `str` contendo um texto no
            formato "1SP999999/P1".

    Returns:
        Um `str` no formato "1SP999999/P1".

    Raises:
        ValueError: erro indicando que valor passado para o parâmetro `crc` não contém
            um texto no formato "1SP999999/P1".
    """
    crc_regex = re.compile(
        r"""(
        \d
        [a-zA-Z]{2}
        \d{6}
        /[a-zA-Z]{1}
        \d'
        )""",
        re.VERBOSE,
    )  # FORMATO 1SP999999/P1

    try:
        return crc_regex.search(crc)[0]
    except TypeError:
        raise Exception("crc deve ter o formato 1SP999999/P1.")


def formatar_usuario_sempapel(usuario: str):
    """Formata uma identificador de usuário do SpSemPapel.

    Essa função não deve ser utilizada para formatar CPFs.

    Args:
        usuario (str): identificador de usuário para ser formatado. Pode ser qualquer
            `str` contendo um texto no formato "SFPXXXXX".

    Returns:
        Um `str` no formato "SFPXXXXX".

    Raises:
        ValueError: erro indicando que valor passado para o parâmetro `sigla` não contém
            um texto no formato "SFPXXXXX".
    """
    usuario_regex = re.compile(
        r"""(
        [a-zA-Z]{3}
        \d{5,9}
        )""",  # FORMATO SFPXXXXX
        re.VERBOSE,
    )

    try:
        return usuario_regex.search(usuario)[0].upper()
    except TypeError:
        raise Exception(
            "Valor no parâmetro usuario deve conter texto no formato SFPXXXXX."
        )


def formatar_sigla_sempapel(sigla: str):
    """Formata uma sigla (não temporária) de um documento do SpSemPapel.

    Para siglas temporárias, consulte a função `formatar_sigla_temp_sempapel`.

    Args:
        sigla (str): Sigla para ser formatada. Pode ser qualquer `str` contendo um texto
            no formato "SFP-PRC-AAAA/XXXXX-VXX" ou "SFP-EXP-AAAA/XXXXX-A".

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos da sigla e `completa` é um `str` no formato "SFP-PRC-AAAA/XXXXX-VXX"
            ou "SFP-EXP-AAAA/XXXXX-A".

    Raises:
        ValueError: erro indicando que valor passado para o parâmetro `sigla` contem um
            texto no formato "SFP-PRC-AAAA/XXXXX-VXX" ou "SFP-EXP-AAAA/XXXXX-A".
    """
    if "PRC" in sigla.upper():
        protocolo_regex = re.compile(
            r"""(
            [a-zA-Z]{3}
            (-)
            [prcPRC]{3}
            (-)
            \d{4}
            (/)
            \d{5,10}
            (-)
            [vV]{1}
            \d{2}
            )""",  # FORMATO SFP-PRC-AAAA/XXXXX-VXX
            re.VERBOSE,
        )

        try:
            protocolo_char = protocolo_regex.search(sigla)[0].upper()
        except TypeError:
            raise ValueError(
                "Valor no parâmetro sigla deve conter texto no formato "
                "SFP-PRC-AAAA/XXXXX-VXX ou SFP-EXP-AAAA/XXXXX-A."
            )

    else:
        protocolo_regex = re.compile(
            r"""(
            [a-zA-Z]{3}
            (-)
            [a-zA-Z]{3}
            (-)
            \d{4}
            (/)
            \d{5,10}
            (-)
            [^vV]{1}
            )""",  # FORMATO SFP-EXP-AAAA/XXXXX-A
            re.VERBOSE,
        )

        try:
            protocolo_char = protocolo_regex.search(sigla)[0].upper()
        except TypeError:
            raise ValueError(
                "Valor no parâmetro sigla deve conter texto no formato "
                "SFP-PRC-AAAA/XXXXX-VXX ou SFP-EXP-AAAA/XXXXX-A."
            )

    protocolo_curto = "".join(i for i in protocolo_char if i.isalnum())

    return protocolo_curto, protocolo_char


def formatar_sigla_temp_sempapel(sigla: str):
    """Formata uma sigla temporária de um documento do SpSemPapel.

    Para siglas não temporárias, consulte a função `formatar_sigla_sempapel`.

    Args:
        sigla (str): Sigla para ser formatada. Pode ser qualquer `str` contendo um texto
            no formato "TMP-XXXXXX".

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos da sigla e `completa` é um `str` no formato "TMP-XXXXXX".

    Raises:
        ValueError: erro indicando que valor passado para o parâmetro `sigla` não contém
            um texto no formato "TMP-XXXXXX".
    """
    documento_regex = re.compile(
        r"""(
        [tmpTMP]{3}
        (-)
        \d{1,12}
        )""",  # FORMATO TMP-XXXXXX
        re.VERBOSE,
    )

    try:
        documento_char = documento_regex.search(sigla)[0].upper()
    except TypeError:
        raise Exception(
            "Valor no parâmetro sigla deve conter texto no formato TMP-XXXXXX."
        )

    documento_curto = "".join(i for i in documento_char if i.isalnum())

    return documento_curto, documento_char


def formatar_osf(osf: str):
    """Formata um número de OSF.

    Args:
        osf (str): OSF para ser formatada. Pode ser qualquer string contendo 11 dígitos.

    Returns:
        Uma tupla `(digitos, completa)`, onde `digitos` é um `str` contendo apenas os
            dígitos da OSF e `completa` é um `str` com digitos e separadores.

    Raises:
        ValueError: erro indicando que valor passado para o parâmetro `osf` não é uma
            string com 11 dígitos.
    """
    osf_digits = "".join(i for i in osf if i.isdigit())

    if len(osf_digits) != 11:
        raise ValueError("Valor no parâmetro osf deve conter 11 números.")

    osf_char = (
        osf_digits[0:2]
        + "."
        + osf_digits[2:3]
        + "."
        + osf_digits[3:8]
        + "/"
        + osf_digits[8:10]
        + "-"
        + osf_digits[10:11]
    )

    return osf_digits, osf_char


def limpar_texto(texto: str) -> str:
    """Remove caracteres não imprimíveis de um texto, mantendo os espaços.

    Args:
        texto (str): texto a ser limpo

    Returns:
        O texto limpo.
    """
    return " ".join(texto.split())


def comparar_textos(texto1: str, texto2: str) -> float:
    """Compara e atribui um valor de similaridade entre dois textos.

    Args:
        texto1 (str): Primeiro texto a ser comparado.
        texto2 (str): Segundo texto a ser comparado.

    Returns:
        O resultado da comparação. Quanto maior o valor retornado, mais similares são os
        textos.
    """
    return SequenceMatcher(None, texto1, texto2).ratio()
