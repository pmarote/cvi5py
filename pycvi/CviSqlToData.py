import os
import html
from bs4 import BeautifulSoup
from typing import List


class CviSqlToData:
    def __init__(self, toDataType: str, maxCells: int, showSql: bool) -> None:
        self.setToDataType(toDataType)
        # maxCells are not used in toDataType == 'txt'
        self.maxCells = maxCells
        self.showSql = showSql

    def setToDataType(self, toDataType):
        if toDataType not in ['html', 'txt']:
            toDataType = 'html'  # if an unknown data type is provided, set it to html by default
        self.toDataType = toDataType

    def putHeader(self, fields: List, sql: str, queryTitle: str) -> str:
        if self.toDataType == 'txt':
            line = ""
            for campo in fields:
                line += "" if line == "" else "\t"
                # a linha abaixo é bizarra mas garante que o caso venha newline no campo, tira
                line += campo.replace("\r", "").replace("\n", "")
            line += "\n"
            return line
        if self.toDataType == 'html':
            html = self.htmlHead(queryTitle,
                                 (f"<h6>{sql}</h6>" if self.showSql else ""),
                                 self.FileName, fields)
            for campo in fields:
                html += f'        <th>{campo}</th>\n'
            html += "      </tr>\n    </thead>\n    <tbody>\n"
            return html

    def putLine(self, row: List) -> str:
        if self.toDataType == 'txt':
            return self.putLineTxt(row)
        else:
            return self.putLineHtml(row)

    def tipo_campo(self, campo) -> int:
        """
        Atençao para este método, usado em putLineHtml e putLineTxt
        columnType é meio que herança do sqlite em .php
        1 = int   2 = float  3 = text  4 = blob  5 = null
        lembrando que "SQLite 3 doesn't have column types,
        but it has column affinities"
        """
        if campo is None:
            return 5
        if isinstance(campo, bytes):
            return 4
        if isinstance(campo, int):
            return 1
        if isinstance(campo, float):
            return 2
        if isinstance(campo, str) and campo.lstrip('-').isdigit():
            return 1
        return 3

    def putLineTxt(self, row: List) -> str:
        """
        Atençao para putLineHtml e putLineTxt - leia em putLineHtml
        """
        line = ""
        for campo in row:
            columnType = self.tipo_campo(campo)
            # abaixo é o seguinte... campo int é o que parece int,
            #     mesmo que seja string
            # campo float sempre vem float,
            #     não precisa corrigir o tipo da variável
            campo = int(campo) if columnType == 1 else campo
            line += "" if line == "" else "\t"
            if columnType == 1:
                if campo > 999999999999999:
                    # Excel cuts off numbers above 15 digits,
                    # exemplo: Chave de Acesso
                    # so prepend "#" to treat them as strings
                    line += "#"
                line += str(campo)
            if columnType == 2:
                line += self.dotToComma(campo, True)
            if columnType == 3:
                # caso venha newline no campo, tira
                line += campo.replace("\r", "").replace("\n", "")
            if columnType == 4:
                line += '#Bytes#'
            if columnType == 5:
                line += '#NaN#'
        line += "\n"
        return line

    def putLineHtml(self, row: List) -> str:
        line = '      <tr>\n'
        for campo in row:
            columnType = self.tipo_campo(campo)
            # abaixo é o seguinte... campo int é o que parece int,
            #     mesmo que seja string
            # campo float sempre vem float,
            #     não precisa corrigir o tipo da variável
            campo = int(campo) if columnType == 1 else campo
            negative_css = 'color: red;'\
                if columnType <= 2 and campo < 0 else ''
            textalign = f' style="text-align: right;{negative_css}"'\
                if columnType <= 2 else ''
            if columnType == 1:
                if campo > 999999999999999:
                    # Excel cuts off numbers above 15 digits,
                    # exemplo: Chave de Acesso
                    # so prepend "#" to treat them as strings
                    htmlValue = "#" + str(campo)
                else:
                    htmlValue = str(campo)
            if columnType == 2:
                # em formato html se coloca também os pontos de milhar
                e_value = self.dotToComma(campo, True).split(',')
                s_com_pontos = "{:,}".format(int(e_value[0])).replace(',', '.')
                htmlValue = s_com_pontos + ',' + e_value[1]
            if columnType == 3:
                htmlValue = self.htmlHighlight(html.escape(campo))
            if columnType == 4:
                htmlValue = '#Bytes#'
            if columnType == 5:
                htmlValue = '#NaN#'

#            columnType = 2 if isinstance(campo, float) else 1 if isinstance(campo, int) else 3
#            negative_css = 'color: red;' if columnType <= 2 and campo < 0 else ''
#            textalign = f' style="text-align: right;{negative_css}"' if columnType <= 2 else ''
#            if (columnType == 2):
#                campo = self.dotToComma(campo, True)
            # htmlValue = campo if columnType == 1 else self.htmlHighlight(html.escape(campo))
#            htmlValue = campo
            line += f"""\
        <td title="{columnType}#{type(campo)}"{textalign}>{htmlValue}</td>
"""
        line += "      </tr>\n"
        return line

    def run(self, sqlDb, sql: str, fileName: str, queryTitle=''):
        # Config.create_dir_if_not_exists()
        self.FileName = fileName + '.' + self.toDataType
        if os.path.exists(self.FileName):
            os.remove(self.FileName)
        try:
            self.FileHandle = open(self.FileName, 'w', encoding='utf-8')
            sqlDb.cursor.execute(sql)
            #  ##TODO##  falta prever se há erro no sql !
            row = sqlDb.cursor.fetchone()
            fields = [description[0]
                      for description in sqlDb.cursor.description]
            self.FileHandle.write(self.putHeader(fields, sql, queryTitle))
            cells = 0
            while row is not None:
                self.FileHandle.write(self.putLine(row))
                cells += len(row)
                if self.toDataType == 'html' and self.maxCells != -1 and cells >= self.maxCells:
                    break
                row = sqlDb.cursor.fetchone()
            if self.toDataType == 'html':
                self.FileHandle.write("    </tbody>\n  </table>\n</body>\n</html>\n")
        except IOError as e:
            print("##FATAL ERROR### : ", e)
        finally:
            self.FileHandle.close()
#        if lines == 0:
#            if self.toDataType == 'html':
#                html = self.htmlHead(queryTitle, "<h6>{}</h6><h4>O SQL (acima) não gerou nenhuma linha</h4>".format(sql), fileName)
#                if self.htmlFileHandle.write(html) == -1:
#                    print("##FATAL ERROR... Could not write a line ({}) in .html file".format(html))
#                    return
#
#            if self.toDataType == 'txt':
#                if self.txtFileHandle.write("O SQL (abaixo) não gerou nenhuma linha\n\n{}".format(sql)) == -1:
#                    print("##FATAL ERROR... Could not write a line ({}) in sql.txt file".format(line))
#                    return

    def htmlHighlight(self, htmlValue):
        if not isinstance(htmlValue, str):
            return htmlValue
        ep1 = htmlValue.find('##')
        if ep1 != -1:
            ep2 = htmlValue.find('##', ep1 + 3)
            if ep2 != -1:
                htmlValue = htmlValue[:ep1] + \
                    "<span style=\"font-weight: bold; color: white; "\
                    + "background-color: red; font-size: larger;\">" \
                    + htmlValue[ep1:ep2 + 2] \
                    + "</span>" \
                    + htmlValue[ep2 + 2:]
        else:
            ep1 = htmlValue.find('#')
            if ep1 != -1:
                ep2 = htmlValue.find('#', ep1 + 2)
                if ep2 != -1:
                    htmlValue = htmlValue[:ep1] + \
                        "<span style=\"font-weight: bold; background-color: yellow;\">" + \
                        htmlValue[ep1:ep2 + 1] + \
                        "</span>" + \
                        htmlValue[ep2 + 1:]
        return htmlValue

    def htmlHead(self, title='', sql='', fileName='', fieldNames=''):
        tableid = fileName.replace('.', '_').replace(']', '_').replace('[', '_').split('/')[-1]
        if isinstance(fieldNames, list):
            style = "  <style>\n"
            for ind, val in enumerate(fieldNames, 1):
                style += f"    #{tableid}.hide{ind} tr > *:nth-child({ind}) "\
                         + "{{ display: none; }}\n    #{tableid}_b{ind}.cl{ind} "\
                         + "{{ background-color: lightcoral; }}\n"

        html = f"""<!DOCTYPE HTML>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>Exportação html de {fileName}</title>
  <meta name="author" content="pmarote">
  <style>
    html{{ font-family: sans-serif; color:#333; background-color:#fff; padding:1em; }}
    body{{ padding:0; margin:0; line-height:1 }}
    p{{ text-align: justify; }}
    table {{ font-size: 0.9em; margin: 0 auto;
           width:100%; margin-bottom:1em; border-collapse: collapse;}}
    th{{ font-weight:bold; background-color:#ddd; }}
    td, th {{ padding:0.5em; border:1px solid #ccc;}}
    h1, h2, h3, h4, h5, h6 {{ padding:0.5em; margin: 0.2em; }}
    button:hover {{background-color:lightgray;}}
  </style>
</head>
<body>
  <h2>{title}</h2>
  {sql}
  <table id="{tableid}">
    <thead>
      <tr>
"""
        return html

    def dotToComma(self, value, two_decimal_places=False):
        # If the field is float, comes to this method,
        # which by default puts 2 decimal places.
        # However, if there are more places, it puts all of them
        value = str(value)
        value = value.replace('.', ',')
        e_value = value.split(',')
        # sempre vai ter algo depois da vírgula
        # exemplos de valores que temos até aqui:
        # 222588,85 ['222588', '85']    0,0 ['0', '0']  60328,8 ['60328', '8']
        # value = "{:,}".format(float(e_value[0])).replace(",", ".")
        # print(value, e_value)
        if two_decimal_places:
            if len(e_value) > 1 and len(e_value[1]) == 1:
                value += '0'
        return value

    def join_html(self, new_html, html_list):
        global PR, CVI_RESULT

        if PR != '':
            new_html = os.path.join(PR, new_html)
        print(f"Consolidating in {CVI_RESULT}\\{new_html}.html "
              + "the following files: ")

        new_html_path = os.path.join(CVI_RESULT, new_html)
        # If there are subfolders, create everything before generating the file
        os.makedirs(os.path.dirname(new_html_path), exist_ok=True)

        new_html_path = f"{new_html_path}.html"

        if os.path.exists(new_html_path):
            os.remove(new_html_path)
            time.sleep(1)  # Sometimes it takes time to delete, so I'm going to give it one more second

        if os.path.exists(new_html_path):
            logging.error(f"##FATAL ERROR... Could not delete {new_html_path}")
            return

        with open(new_html_path, 'w') as w_fh:
            first_file = True
            for val in html_list:
                if PR != '':
                    val = os.path.join(PR, val)

                print(f" `->{val}.html")
                curr_html = os.path.join(CVI_RESULT, f"{val}.html")

                if not os.path.exists(curr_html):
                    logging.error(f"##FATAL ERROR... Could not find {curr_html}")
                    return

                with open(curr_html, 'r') as r_fh:
                    after_body = False
                    for line in r_fh:
                        if line.strip() == '</body>':
                            break
                        if first_file or after_body:
                            w_fh.write(line)
                        if line.strip() == '<body>':
                            after_body = True

                first_file = False
                os.remove(curr_html)

            w_fh.write('</body>\n</html>\n')

    def tableSpread(self, html):
        print(f"Espalhando a tabela de {html}.html: \n")
        newHtml = os.path.join(f"{html}.html")
        oldHtml = os.path.join(f"{html}.old.html")
        print(f"Primeiro movendo a tabela de {newHtml} para {oldHtml}:n")
        try:
            if os.path.exists(oldHtml):
                os.remove(oldHtml)
            os.rename(newHtml, oldHtml)
        except Exception as e:
            print(f"##FATAL ERROR... Could not rename {newHtml} to {oldHtml}", e)
            return
        # Carregue o arquivo HTML
        with open(oldHtml, "r", encoding='utf-8') as file:
            soup = BeautifulSoup(file, "html.parser")
        # Encontra a tabela original
        original_table = soup.find('table')
        # Encontra o cabeçalho e os dados da tabela original
        header_cells = original_table.find_all('th')
        data_cells = original_table.find_all('td')
        # Remove a tabela original
        original_table.decompose()
        # Divide o cabeçalho e os dados em três partes
        for i in range(0, len(header_cells), 4):
            header_part = header_cells[i:i + 4]
            data_part = data_cells[i:i + 4]
            # Cria uma nova tabela
            new_table = soup.new_tag('table')
            # Cria a linha do cabeçalho na nova tabela
            new_header_row = soup.new_tag('tr')
            for header_cell in header_part:
                new_th = soup.new_tag('th')
                new_th.string = header_cell.text
                new_header_row.append(new_th)
            new_table.append(new_header_row)
            # Cria a linha de dados na nova tabela
            new_data_row = soup.new_tag('tr')
            for data_cell in data_part:
                new_td = soup.new_tag('td')
                new_td.string = data_cell.text
                new_data_row.append(new_td)
            new_table.append(new_data_row)
            # Adiciona a nova tabela ao documento
            soup.append(new_table)
        # Salve o novo HTML
        with open(newHtml, "w", encoding='utf-8') as file:
            file.write(str(soup))

    def tableSpreadOld(self, html, keepOriginalTable=False):
        # se keepOriginalTable = True, ficam duas tabelas,
        #   a original e a 'spread'
        print(f"Espalhando a tabela de {html}.html: \n")
        newHtml = os.path.join(f"{html}.html")
        oldHtml = os.path.join(f"{html}.old.html")
        print(f"Primeiro movendo a tabela de {newHtml} para {oldHtml}:n")
        try:
            if os.path.exists(oldHtml):
                os.remove(oldHtml)
            os.rename(newHtml, oldHtml)
        except Exception as e:
            print(f"##FATAL ERROR... Could not rename {newHtml} to {oldHtml}", e)
        if os.path.exists(newHtml):
            print(f"##FATAL ERROR... File {newHtml} still there...")
            return
        try:
            wFH = open(newHtml, 'w', encoding='utf-8')
        except Exception as e:
            print(f"##FATAL ERROR... Could not open {newHtml} for write", e)
            wFH.close()
        if not os.path.exists(oldHtml):
            print(f"##FATAL ERROR... Could not find {oldHtml}")
            return
        try:
            rFH = open(oldHtml, 'r', encoding='utf-8')
        except Exception as e:
            print(f"##FATAL ERROR... Could not open {oldHtml} for read", e)
            rFH.close()
        # ok, estamos assim: rFW é a leitura do antigo, wFH é a gravação do novo
        # primeiro vamos ler inteiro rFW no próximo bloco
        # varrendo o html, espera-se que seja uma linha apenas
        headerTr = ''
        alineTr = []
        innerTable = False  # True quando começa a table, False quando termina
        for saux in rFH:
            saux = saux.strip()
            if saux == '</body>':
                break
            if saux.strip()[:6]('<table'):
                innerTable = True
            if saux == '<thead>':
                headerTr = '<thead>'
            if saux.strip()[:4]('<tr>'):
                if headerTr == '<thead>':
                    headerTr = saux
                else:
                    alineTr.append(saux)
            if keepOriginalTable:
                try:
                    wFH.write(saux)
                except Exception as e:
                    print(f"##FATAL ERROR while writing {newHtml}", e)
                    wFH.close()
                    return
            else:
                if not innerTable:
                    try:
                        wFH.write(saux)
                    except Exception as e:
                        print(f"##FATAL ERROR while writing {newHtml}", e)
                        wFH.close()
                        return
            if saux.strip()[:7] == '</table':
                innerTable = False

            if saux.startswith('</table'):
                innerTable = False
        aeheaderTr = [item for item in headerTr.replace('<tr>', '').replace('</tr>', '').split('</th>') if item]
        aelineTr = []
        for i, val in enumerate(alineTr):
            aelineTr.append([item for item in val.replace('<tr>', '').replace('</tr>', '').split('</td>') if item])

        for linTr in range(len(alineTr)):
            headerTr = ''
            lineTr = ''
            tableSpread = ''
            if len(alineTr) > 1:
                tableSpread = f"<h4 style=\"color: brown; padding: 0; margin: 10px 0 0 0;\">Linha {linTr + 1}</h4>\n"
            ilength = 0

            for i in range(len(aeheaderTr)):
                if '>t' in aeheaderTr[i][-3:]:
                    aeheaderTr[i] = aeheaderTr[i].replace('>t', ' style="color: green; background-color: lightyellow;">t')

                headerTr += (aeheaderTr[i] if headerTr == '' else '</th>' + aeheaderTr[i])
                lineTr   += (aelineTr[linTr][i] if lineTr == '' else '</td>' + aelineTr[linTr][i])

                hlen = len(aeheaderTr[i]) - aeheaderTr[i].find('>')
                llen = len(aelineTr[linTr][i]) - aelineTr[linTr][i].find('>')

                ilength += (hlen if hlen > llen else llen)

                detectFieldGroup = False
                if 0 < i < (len(aeheaderTr) - 1) and '>t' in aeheaderTr[i+1][-3:]:
                    detectFieldGroup = True
                if detectFieldGroup or ilength > 100:
                    tableSpread += f"<table><thead><tr>{headerTr}</th></tr></thead><tbody><tr>{lineTr}</td></tr></tbody></table>\n"
                    headerTr = ''
                    lineTr = ''
                    ilength = 0

            if headerTr != '':
                tableSpread += f"<table><thead><tr>{headerTr}</th></tr></thead><tbody><tr>{lineTr}</td></tr></tbody></table>\n"
            
            tableSpread = tableSpread.replace('<table>', '<table style="margin: 0px 0px 5px 0px;">')

            try:
                wFH.write(f"{tableSpread}\n")
            except Exception as e:
                print(f"##FATAL ERROR while writing {newHtml}")
                return
        rFH.close()
        wFH.close()
        os.remove(oldHtml)
