# Technical & Legal System Architecture - Charaka IP

## 1. System Overview

**Charaka IP** is designed as a multi-tier, agentic RAG system tailored for Intellectual Property and Regulatory Compliance in Ayurveda across Indian (National) and Global (International) legal regimes.

---

## 2. Core Legal Regimes Handled

### National Regimes (India)
1. **The Patents Act, 1970 & Patents (Amendment) Rules 2024**
   - **Section 3(p)**: Excludes traditional knowledge or aggregations from patentability.
   - **Section 3(d)**: Heightened efficacy bar for known substances.
   - **Section 3(e)**: Admixture bar.
   - **Rule 24B**: Revised 31-month timeline for Request for Examination (RFE).
2. **Biological Diversity Act, 2002 & Biological Diversity (Amendment) Act, 2023**
   - Exemption of registered AYUSH practitioners and domestic cultivated flora.
   - Benefit-sharing slabs (0.1% to 0.5% of turnover).
   - NBA Form I / II / III approval routing.
3. **Drugs and Cosmetics Act, 1940 & Rules**
   - First Schedule Authoritative Texts (2024 Edition).
   - Rule 158B for Patent & Proprietary medicines.
   - Rule 122E for Phytopharmaceutical drugs (standardized active fractions).
4. **FSSAI (Ayurveda Aahar) Regulations, 2022**
   - Food supplement parameters for traditional formulations.
5. **Geographical Indications (GI), Trademarks, Designs & PPVFR**
   - Rights over plant varieties and regional reputation (e.g. Navara rice, Nilambur teak).

### International Regimes
1. **WIPO Treaty on Intellectual Property, Genetic Resources and Associated TK (2024)**
   - Article 3 mandatory disclosure requirement for patent applications.
2. **Convention on Biological Diversity (CBD) & Nagoya Protocol**
   - Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT).
3. **TRIPS, PCT, Madrid & Hague Systems**
   - Multi-country patent and trademark filings.

---

## 3. Multi-Agent RAG Pipeline Workflow

```
[User Query] -> RouterAgent -> (Jurisdiction Filter: National | International)
                   |
                   v
             FormulationClassifierAgent (if taxonomy requested)
                   |
                   v
        Hybrid Retrieval (Qdrant Vector Store + Neo4j Knowledge Graph)
                   |
                   v
      Citation Verification Agent (Grounds answer in India Code / WIPO)
                   |
                   v
          DPDP Audit Logger (Cryptographic SHA-256 Hashing)
```
