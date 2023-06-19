__author__ = 'Paulo Marote'

"""pyCVI (Conv) é uma evolução do velho CVI, que era em .php, agora em python

A ideia é abandonar o velho desenvolvimento e fazer tudo agora em python. Oremos.

Neste momento aqui é um "launcher" de todas as conversões disponíveis
Não sei se é o melhor método, é mais pra botar pra funcionar
"""

import os
import uuid
import zipfile
# import traceback

from pycvi.Config import Config
from pycvi.conv.ConvHelpers import ConvHelpers
from pycvi.conv.ConvCookbook import ConvCookbook
from pycvi.conv.ConvCat42 import ConvCat42

config = Config()


def conv_action(window, values: str):
    zipfile_path = ConvHelpers.get_zip_file(window)
    if zipfile_path is None:
        print("Conversão cancelada pelo usuário")
        # return False
    zipfile_path = 'J:\\sef\\my\\NovaQualityVeiculos\\Fontes\\Testes.zip'
    tmppath = os.path.join(config.CVI_VAR, 'tmp', str(uuid.uuid1()))
    print(f"Convertendo {zipfile_path} dentro da pasta temporária {tmppath} Oremos...\n")
    Config.create_dir_if_not_exists(tmppath)
    if not os.path.isdir(tmppath):
        print(f'##ERRO## Cancelando a conversão... não consegui criar a pasta {tmppath}')
        return
    srcpath = os.path.join(tmppath, 'source')
    Config.create_dir_if_not_exists(srcpath)
    if not os.path.isdir(srcpath):
        print(f'##ERRO## Cancelando a conversão... não consegui criar a pasta {srcpath}')
        return
    respath = os.path.join(tmppath, 'result')
    Config.create_dir_if_not_exists(respath)
    if not os.path.isdir(respath):
        print(f'##ERRO## Cancelando a conversão... não consegui criar a pasta {respath}')
        return
    print(f"\nExtraindo {zipfile_path} para {srcpath}")
    try:
        with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
            zip_ref.extractall(srcpath)
    except Exception as e:
        print(f"##ERRO## Cancelando a conversão... Falha ao extrair {zipfile}", e)
        return
    print(f"\nExtração concluída... {srcpath} agora contém:")
    for entry in os.scandir(srcpath):
        print(entry.path)
    arqs = ConvHelpers.listdir(srcpath, True)
    if len(arqs) == 0:
        print(f"Nada a fazer, não há arquivos na pasta {srcpath}")
        return
    for index, entry in enumerate(arqs):
        fileDetected, encoding = ConvCookbook.fileConv(entry)
        if fileDetected == 'Cat42':
            convcat42 = ConvCat42(window, entry, respath, encoding)  # noqa: F401
    if ConvHelpers.verifica_arquivo(respath, 'cat42'):
        print('tem Cat42')
    if ConvHelpers.verifica_arquivo(respath, 'efd'):
        print('tem Efd')
    return
