"""
corpus/connectors — External legal database and registry connectors for Charaka IP.
Supports WIPO Lex, IP India (InPASS / TM / GI), Manupatra, and SCC Online.
"""

from corpus.connectors.wipo_lex import WIPOLexConnector
from corpus.connectors.ip_india_live import IPIndiaLiveConnector
from corpus.connectors.manupatra import ManupatraConnector
from corpus.connectors.scc_online import SCCOnlineConnector

__all__ = [
    "WIPOLexConnector",
    "IPIndiaLiveConnector",
    "ManupatraConnector",
    "SCCOnlineConnector",
]
