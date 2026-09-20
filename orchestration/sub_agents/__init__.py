"""
orchestration/sub_agents — Specialized legal domain sub-agents for Charaka IP.

Each sub-agent encapsulates domain-specific reasoning, statutory rules,
case law standards, and procedural checklists for its respective area of law:
  - patent_agent: Patents Act 1970 (§3(p), §3(e), §3(d)), TRIPS Art. 27, PCT
  - trademark_agent: Trade Marks Act 1999 (§9, §11, §27), Madrid Protocol
  - gi_agent: Geographical Indications Act 1999, Lisbon System
  - copyright_agent: Copyright Act 1957, Berne Convention, classical treatises
  - ayush_agent: Drugs & Cosmetics Act 1940, Rule 158-B, ASU licensing
  - abs_agent: Biological Diversity Act 2002 §6, NBA Form III, Nagoya Protocol
  - tkdl_agent: Traditional Knowledge Digital Library prior art, risk scoring
"""

from orchestration.sub_agents.patent_agent import patent_agent
from orchestration.sub_agents.trademark_agent import trademark_agent
from orchestration.sub_agents.gi_agent import gi_agent
from orchestration.sub_agents.copyright_agent import copyright_agent
from orchestration.sub_agents.ayush_agent import ayush_agent
from orchestration.sub_agents.abs_agent import abs_agent
from orchestration.sub_agents.tkdl_agent import tkdl_agent

__all__ = [
    "patent_agent",
    "trademark_agent",
    "gi_agent",
    "copyright_agent",
    "ayush_agent",
    "abs_agent",
    "tkdl_agent",
]
