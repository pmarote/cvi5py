import os
import codecs
import chardet


class ConvCookbook:

    @staticmethod
    def fileConv(entry):
        try:
            with open(entry, 'rb') as f:
                result = chardet.detect(f.read())
            print(f"Processando arquivo {entry}, "
                  + f"codificação detectada como tipo {result['encoding']}")
            with codecs.open(entry, 'r', encoding=result['encoding']) as handle:
                linha1 = handle.readline().strip()
                linha2 = handle.readline().strip()
                fileDetected = ConvCookbook.fileDetect(entry, linha1, linha2)
                if fileDetected == "unknown":
                    print(f"Mas não foi reconhecido como algum tipo de arquivo específico\n")
                else:
                    print(f"detectado como " + ConvCookbook.fileDescription(fileDetected) + "\n")
                return fileDetected, result['encoding']
        except Exception as e:
            print(f"Erro... Não foi possivel a leitura do arquivo {entry}\n", e)
            return False, False

    @staticmethod
    def fileDetect(entry, linha1, linha2):
        fileDetected = "unknown"
        if entry.lower().endswith('.txt'):
            fileDetected = "Generic_Txt"
        if os.path.basename(entry)[0:5].lower() == 'safic':
            fileDetected = "Safic"
        if linha1.startswith('|0000|LECD|'):
            fileDetected = "SpedCont"
        if linha1.startswith('|0000|') and not linha1.startswith('|0000|RessarcimentoSt|'):
            fileDetected = "SpedEfd"
        if linha1.startswith('01') and linha2.startswith('02'):
            fileDetected = "Cat17"
        if linha1.startswith('0000|LADCA|'):
            fileDetected = "Ladca"
        if linha1.startswith('0000|LASIMCA|'):
            fileDetected = "Lasimca"
        if linha1.startswith('|0000|RessarcimentoSt|'):
            fileDetected = "Cat42"
        if linha1.startswith('0000|') and not linha1.startswith('0000|LADCA|')\
           and not linha1.startswith('0000|LASIMCA|'):
            fileDetected = "Cat42"
        return fileDetected

    @staticmethod
    def fileDescription(fileDetected):
        switcher = {
            "unknown": "Arquivo Desconhecido",
            "Generic_Txt": "Arquivo .txt ainda não reconhecido",
            "SpedCont": "Sped Contábil",
            "SpedEfd": "Sped Fiscal EFD",
            "Safic": "Arquivo catado da pasta local download do Safic",
            "Cat17": "Cat 17/99, antigo ressarcimento ST",
            "Ladca": "Crédito acumulado Custeio, Cat 83",
            "Lasimca": "Crédito acumulado Simplificado, Cat 207",
            "Cat42": "Cat 42 (e-ressarcimento)",
        }
        return switcher.get(fileDetected, "Não processado em fileDetect()")
