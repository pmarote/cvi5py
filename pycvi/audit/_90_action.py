import os
from pycvi.Config import Config
from pycvi.audit.DFeHelpers import DFeHelpers

config = Config()
dh = DFeHelpers(config)


def _90_action(window, values: str):
    osf, cnpj = dh.values_to_osf_cnpj(values)
    cv_db = dh.audits_action(osf, cnpj)
    if cv_db is False:
        return
    print(f"Gerando DFe(s), a partir da osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()
    dirName = os.path.join(config.CVI_VAR, 'result', cnpj, osf, 'DFes')
    dirName, keys = dh.get_keys_input(window, dirName)
    # se veio separado por ponto e vírgula, muda para separado por \n
    keys = keys.replace(';', "\n")
    keys = keys.split("\n")

    i = 0
    for key in keys:
        key = key.replace('#', '').strip()  # dá uma limpada
        fileName = os.path.join(dirName, key)
        tpDfe = key[20:22]
        # só vai gerar se conseguir achar o modelo na string
        if tpDfe == '55':
            dh.DfeNFe(window, osf, cv_db, fileName, key)
        elif tpDfe == '57':
            # sqlite_dfe_DfeCte(pr, key, pr.cvSaficLib.nivelDetalhe)
            print(f'Não gerei a DFe {key}. Modelo 57 ainda não disponível')
        elif tpDfe == '59':
            # sqlite_dfe_DfeSat(pr, key, pr.cvSaficLib.nivelDetalhe)
            print(f'Não gerei a DFe {key}. Modelo 57 ainda não disponível')
        i += 1

    if i == 1:
        print("\nComo gerei somente uma DFe, vou abrir o arquivo .html.\n")
        os.startfile(os.path.realpath(os.path.join(dirName, f"{key}.html")))
        print(f"Aberto {fileName} - verifique se está em segundo plano")
