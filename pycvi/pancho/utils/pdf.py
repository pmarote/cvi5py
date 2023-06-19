"""Módulo com funções utilitárias para manopulação de arquivos PDF."""

import os

import fitz
from natsort import natsorted


def juntar_arquivos(pdf_saida, dir="", arquivos=None):
    """Junta diversos arquivos em um único arquivo PDF.

    Args:
        dir (str): Caminho completo de uma pasta que contém os arquivos PDFs
        arquivos (list): Arquivos PDFs que estão na pasta e devem ser ordenados
            na sequencia passada
        pdf_saida (str): Caminho completo onde deverá ser salvo o arquivo PDF, incluindo
            seu nome. Deve terminhar com .pdf.

    Raises:
        TODO: Erro indicando que o sistema não conseguiu realizar a funcionalidade.

    Returns:
        Quantidade de arquivos PDFs juntados.
    """
    try:
        pdfs_count = 1
        if len(arquivos) == 0:
            arquivos = [f for f in os.listdir(dir) if f.endswith(".pdf")]
            arquivos = natsorted(arquivos)
        if len(arquivos) > 0:
            print("\tArquivos ordenados: " + str(arquivos))
            result = fitz.open()
            for pdf in arquivos:
                pdfs_count += 1
                with fitz.open(dir + "/" + pdf) as mfile:
                    result.insert_pdf(mfile)
            result.save(pdf_saida)
            print("Arquivos juntados!")
            pdf_saida_size = os.path.getsize(pdf_saida) / (1024 * 1024)
            if pdf_saida_size > 0:
                print("Tamanho do novo arquivo gerado: %.2f " % (pdf_saida_size))
                return pdfs_count
        return 0
    except Exception as e1:  # falha na tentativa
        print("\t\t\t\tErro no processamento com mensagem de erro: ", str(e1))
        return 0


def dividir_pdf_por_tamanho(caminho, tamanho_maximo):
    """Separa um arquivo PDF em diversos arquivos menores.

    Args:
        caminho (str): Caminho completo onde está o arquivo PDF, incluindo
            seu nome. Deve terminhar com .pdf.
        tamanho_maximo (int): Tamanho máximo em MB que os arquivos PDFs devem ter.
            Por exemplo, no SIGADOC esse tamanho é de no máximo 10 MBs.
            # TODO: PENDENTE DE MELHORIA NA IMPLEMENTAÇÃO.

    Raises:
        TODO: Erro indicando que o sistema não conseguiu realizar a funcionalidade.

    Returns:
        Quantidade de arquivos PDFs que foram separados em arquivos menores.
    """
    try:
        doc = fitz.open(caminho)

        # Verificar tamanho o PDF em MB
        pdf_size = os.path.getsize(caminho) / (1024 * 1024)
        total_pages = len(doc)
        avg_size = pdf_size / total_pages
        print(
            "\tDocumento '%s' tem %i paginas com tamanho total %.2f MB"
            % (doc.name, total_pages, pdf_size)
        )
        print("\t Páginas de tamanho em torno de %.2f MB." % (avg_size))

        # leitura do documento
        if pdf_size > tamanho_maximo:
            avg_step = int(tamanho_maximo / avg_size)
            pdfs_count = 1
            current_page = 0
            end_page = current_page + avg_step
            out_pdf_size = 0
            while current_page != total_pages:
                if end_page > total_pages:
                    end_page = total_pages
                incluir_paginas = str(current_page + 1) + "-" + str(end_page)
                print(
                    f"\tProcessando Documento '{doc.name}' : "
                    f"Parte {pdfs_count} : "
                    f"pag_inicial = {current_page} :"
                    f" pag_final = {end_page}"
                )
                pages = _auxiliar(
                    incluir_paginas
                )  # ajustar os indices começando em zero
                print("\tProcessando Documento : intervalo = %s" % (pages))
                # tratamento para quando há somente 1 página
                # e ainda é maior que o tamanho máximo
                if current_page == end_page:
                    print(
                        f"\t\t\t\tErro no tamanho máximo {tamanho_maximo}, "
                        f"pois a pagina {end_page} é maior que isso: "
                        f"{out_pdf_size:.2f} MB"
                    )
                    return 0
                # gerando novo pdf
                fitz.open()
                # get the pages
                try:  # inserir paginas
                    outdoc = fitz.open(caminho)
                    outdoc.select(pages)  # delete all others
                    ofile = caminho.replace(".pdf", "-{}.pdf".format(pdfs_count))
                    outdoc.ez_save(ofile)  # save and clean new PDF
                    outdoc.close()
                    # verificar se o tamanho do arquivo ainda ficou menor
                    # e pegar menos páginas
                    out_pdf_size = os.path.getsize(ofile) / (1024 * 1024)
                    print(
                        f"\tProcessando Documento : Parte {pdfs_count} : "
                        f"ficou com tamanho de {out_pdf_size:.2f} MB"
                    )
                    if out_pdf_size > tamanho_maximo:
                        # refazer essa parte do arquivo com menos páginas (metade)
                        # qtd_digitos = len(str(end_page))
                        # tratamento para arquivos com muitas paginas
                        # end_page = current_page + int(avg_step/2)
                        end_page = int(end_page * 0.95)
                        # diminui mais do que deveria
                        if end_page < current_page:
                            end_page = current_page
                        print(end_page)
                        # return
                        continue
                except Exception as e1:  # falha na tentativa
                    print(
                        "\t\t\t\tErro no processamento com mensagem de erro: ", str(e1)
                    )
                    break
                # continuar o loop
                current_page = end_page
                end_page = current_page + avg_step
                pdfs_count += 1
            return pdfs_count
        else:
            print(
                "\tDocumento '%s' é menor do com tamanho total %.2f MB"
                % (doc.name, tamanho_maximo)
            )
            return 0
    except Exception as e1:  # falha na tentativa
        print("\t\t\t\tErro no processamento com mensagem de erro: ", str(e1))
        return 0


def excluir_paginas_do_pdf(arquivo_original="", paginas="", pdf_saida=""):
    """Deleta um CONJUNTO DE PÁGINAS de um arquivo PDF.

    Args:
        arquivo_original (str): Caminho completo onde está o arquivo PDF, incluindo
            seu nome. Deve terminhar com .pdf.
        paginas (str): Intervalo de páginas que devem ser excluídas do PDF Original
            Pode ser usada a mesma notação que usamos para imprimir, por exeemplo:
            2-7 (vai excluir as páginas do intervalo, da 2 até a 7)
            1,5,9 (vai excluir somente as páginas 1, 5 e 9)
            1;5;9 (vai excluir somente as páginas 1, 5 e 9)
        pdf_saida (str): Caminho completo onde deverá ser salvo o arquivo PDF, incluindo
            seu nome. Deve terminhar com .pdf.

    Raises:
        TODO: Erro indicando que o sistema não conseguiu realizar a funcionalidade.

    Returns:
        Quantidade de arquivos PDFs que foram separados em arquivos menores.
    """
    try:
        doc = fitz.open(arquivo_original)
        excluir_paginas = _auxiliar(paginas)  # ajustar os indices começando em zero
        incluir_paginas = range(len(doc))
        paginas = set(incluir_paginas) - set(excluir_paginas)

        # gerando novo pdf
        fitz.open()

        # get the pages
        try:  # inserir paginas
            doc.select(list(paginas))  # delete all others
            doc.ez_save(pdf_saida)  # save and clean new PDF
            doc.close()
            return len(excluir_paginas)
        except Exception as e1:  # falha na tentativa
            print("\t\tErro no processamento com mensagem de erro: ", str(e1))
            return 0
    except Exception as e1:  # falha na tentativa
        print("\t\t\t\tErro no processamento com mensagem de erro: ", str(e1))
        return 0


def parse_pdf(caminho: str) -> list[str]:
    """Gera uma lista de linhas de texto extraídas de um arquivo PDF.

    Args:
        caminho (str): Caminho completo onde está o arquivo PDF, incluindo
            seu nome. Deve terminhar com .pdf.

    Returns:
        Lista de strings extraídas do arquivo.
    """
    doc = fitz.Document()
    texto_pdf: list[str] = []
    try:
        doc = fitz.Document(caminho)
        for page in doc:
            texto_pdf.extend(
                page.get_text(
                    flags=~fitz.TEXT_PRESERVE_SPANS & ~fitz.TEXT_PRESERVE_IMAGES,
                    sort=False,
                ).splitlines()
            )
    finally:
        if doc is not None:
            doc.close()
    return [linha.strip() for linha in texto_pdf if linha.strip()]


def _auxiliar(data):
    # ==============================================================================
    # Delimitadores, função auxiliar
    # Input: recebe as páginas iniciando em 1 (como o usuario ve o doc)
    # Retorno: lista de paginas iniciando em 0 (como o fitz ve o doc)
    # ==============================================================================
    try:
        delimiters = "\n\r\t,;"
        for d in delimiters:
            data = data.replace(d, " ")
        lines = data.split(" ")
        numbers = []

        for line in lines:
            if line == "":
                continue
            elif "-" in line:
                t = line.split("-")
                # numbers += range(int(t[0]), int(t[1]) + 1)
                numbers += range(int(t[0]) - 1, int(t[1]))
            else:
                # numbers.append(int(line))
                numbers.append(int(line) - 1)
        return numbers
    except Exception as e1:  # falha na tentativa
        print("\t\t\t\tErro no processamento com mensagem de erro: ", str(e1))
        return 0
