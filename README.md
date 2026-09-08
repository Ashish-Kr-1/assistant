# IP-SAKTI Sahayak (PS045)
> **Multilingual, RAG-Based AI Assistant for Intellectual Property & Regulatory Guidance in Ayurveda across National & International Regimes**

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-0f382c.svg)](backend/)
[![React 18](https://img.shields.io/badge/react-18.0+-blue.svg)](frontend/)
[![RAG Grounded](https://img.shields.io/badge/RAG-Source--Cited-success.svg)](ml_pipeline/)
[![DPDP Act Compliant](https://img.shields.io/badge/DPDP_2023-Privacy_Compliant-green.svg)](docs/dpdp_compliance_policy.md)

---

## 🌟 Overview

**IP-SAKTI Sahayak** is an authoritative, source-cited AI assistant designed to solve the dual challenges of under-protected Ayurvedic innovation and exposure to biopiracy/misappropriation. Grounded in a version-tracked legal corpus, IP-SAKTI Sahayak bridges the gap between traditional knowledge (TK) therapeutics and modern IP/regulatory compliance.

### Key Capabilities

1. **Dual Jurisdiction Isolation**: Visibly separate answer sets for **National (India)** and **International** legal regimes to eliminate cross-jurisdictional conflation.
2. **Ayurvedic Formulation Classifier**: Interactive decision engine categorizing products into Classical Generics (First Schedule texts), Patent & Proprietary Medicines, Phytopharmaceuticals, Ayurveda-Aahar (Nutraceuticals), or Cosmetics — outputting precise IP barriers (e.g., Section 3(p)) and Access-and-Benefit-Sharing (ABS) duties.
3. **Access & Benefit Sharing (ABS) Helper**: Automatic benefit-sharing fee calculator and approval routing under India's Biological Diversity Act (amended 2023) and the Nagoya Protocol.
4. **Mandatory Statutory Citations & Confidence Score**: Traceable references down to section, rule, gazette, or treaty article with zero-hallucination guardrails.
5. **Relational Knowledge Graph & Multi-Agent RAG**: LangGraph orchestrator backed by Qdrant vector search and Neo4j knowledge graph linking herbs, formulations, statutes, and patent bars.
6. **Multilingual & Voice (Bhashini)**: Indic voice input and 22 Indian language translations powered by Bhashini.
7. **DPDP Compliance & Human Escalation**: Built-in privacy controls, consent logging, standing legal disclaimers, and direct routing to registered IP Facilitators and Patent Agents.

---

## 🏗 Repository Architecture

```
ip-assistant/
├── .github/              # CI/CD Workflows (Frontend, Backend, ML Evals) & Issue Templates
├── frontend/             # React / Vite / Tailwind CSS Client with Jurisdiction & Classifier UI
├── backend/              # FastAPI Server, REST API, WebSockets, ABS Helper & DPDP Logger
├── ml_pipeline/          # LangGraph Multi-Agent RAG, Neo4j Graph, Vector Embeddings & Evals
├── connectors/           # Public (InPASS, India Code, WIPO) & Paid (Manupatra, SCC) Connectors
├── docs/                 # Legal Framework Documentation, Guides & API Specs
├── docker/               # Docker Compose & Reverse Proxy Configurations
└── scripts/              # Corpus Seeding, Knowledge Graph Builders & Evaluation Runners
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js `v18+` & `npm`
- Python `3.11+`
- Docker & Docker Compose (optional, for full stack)

### Local Environment Setup

1. **Clone the repository & switch to development branch**:
   ```bash
   git clone https://github.com/YOUR_ORG/ip-sakti-sahayak.git
   cd ip-sakti-sahayak
   git checkout -b feature/initial-setup
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

3. **Launch Backend (FastAPI)**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

4. **Launch Frontend (React + Vite)**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

5. **Run Full Docker Stack**:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

---

## 📚 Grounded Legal Corpus

IP-SAKTI Sahayak relies on a continuously updated corpus including:
- **Patents Act 1970 & Patents (Amendment) Rules 2024** (Sec 3(p) TK bar, InPASS records)
- **Biological Diversity Act 2002 & Biological Diversity (Amendment) Act 2023 / 2024 Rules**
- **Traditional Knowledge Digital Library (TKDL)** prior-art classifications
- **WIPO Treaty on Intellectual Property, Genetic Resources and Associated TK (2024)**
- **Drugs & Cosmetics Act 1940** (Ayurvedic/Siddha/Unani provisions & Phytopharmaceuticals)
- **FSSAI (Ayurveda Aahar) Regulations 2022** & Cosmetic Rules 2020
- **TRIPS, CBD, Nagoya Protocol, Budapest Treaty, PCT, Madrid & Hague Systems**

---

## 🛡 Privacy & DPDP Compliance

This project enforces strict adherence to India's **Digital Personal Data Protection (DPDP) Act 2023**:
- No user query data is stored without explicit consent.
- All backend sessions use cryptographic anonymization for audit logs.
- Standing disclaimer: *"Information Provided is for Educational & Guidance Purposes Only and Does Not Constitute Formal Legal Advice."*

---

## 👥 Branching & Contributing Strategy

We follow a structured Git branching workflow:
- `main`: Stable, release-ready code.
- `develop`: Integration branch for tested features.
- `feature/*`: UI/Backend functionality (e.g., `feature/formulation-classifier`).
- `ml/*`: RAG, Knowledge Graph, and evaluation benchmark experiments (e.g., `ml/neo4j-graph-builder`).
- `hotfix/*`: Production bug fixes.

See [docs/architecture.md](docs/architecture.md) for full architectural documentation.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
