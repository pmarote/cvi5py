__author__ = 'Paulo Marote'

"""pyCVI (Audit) é uma evolução do velho CVI, que era em .php, agora em python

A ideia é abandonar o velho desenvolvimento e fazer tudo agora em python.
Oremos.

Neste momento aqui é um "launcher" de todas as auditorias diesponíveis
Não sei se é o melhor método, é mais pra botar pra funcionar
"""
from pycvi.audit._00_action import _00_action  # noqa: F401
from pycvi.audit._02_action import _02_action  # noqa: F401
from pycvi.audit._03_action import _03_action  # noqa: F401
from pycvi.audit._21_action import _21_action  # noqa: F401
from pycvi.audit._35_action import _35_action  # noqa: F401
from pycvi.audit._90_action import _90_action  # noqa: F401
from pycvi.audit._95_action import _95_action  # noqa: F401
