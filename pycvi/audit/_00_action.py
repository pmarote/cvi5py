import os
import subprocess
from pycvi.Config import Config
from pycvi.audit.AuditHelpers import AuditHelpers

config = Config()
ah = AuditHelpers(config)


def _00_action(window, values: str):
    osf, cnpj = ah.values_to_osf_cnpj(values)
    cv_db = ah.audits_action(osf, cnpj)
    if cv_db is False:
        return
    file_selection = os.path.join(config.CVI_VAR, 'result', cnpj, f'cv_{osf}.db3')
    exe_path = os.path.join(config.CVI_USR, 'Sqliteman-1.2.2', 'sqliteman.exe')
    subprocess.run([exe_path] + [file_selection])
    print(f"Gerando 00 Pesquisa Livre na osf {osf} \
        do cnpj {cnpj}...\n\n#AGUARDE#")
    window.refresh()
    fileName = os.path.join(config.CVI_VAR, 'result', cnpj, osf,
                            'Pesquisa_Livre_py')
    sql = 'SELECT 1;'
    ah.sqlToData_run_aux(window, cv_db, sql, fileName, os.path.basename(fileName))
