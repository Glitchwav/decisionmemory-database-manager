# DecisionMemory Protocol — Competitor Research Report

> Generated: 2026-03-16 | Research scope: GitHub, PyPI, academic papers, product sites

---

## Executive Summary

DecisionMemory Protocol 在 AI decision-making 生態系中定位為**唯一以「交易記憶」為核心的 MCP server**。市場上有 49k+ stars 的 AI hedge fund 框架、32k stars 的 multi-agent 交易系統，但**沒有任何專案把 decision memory 做成獨立的 protocol-level 產品**。最接近的 FinMem（858 stars）是學術論文代碼，已停更 2 年。

### 關鍵發現

1. **記憶層 = 藍海**：所有主流競品都是「分析/執行」工具，沒有人做「從過去交易學習」的獨立服務
2. **Forex/Gold = 空白市場**：全部開源 AI decision-making 專案集中在美股和 crypto，沒有 XAUUSD
3. **MCP decision-making 生態早期**：PyPI 上最大的 decision-making MCP 月下載才 6.5K，DecisionMemory 排第 6（515/mo）
4. **學術 vs 產品的鴻溝**：FinMem / FinAgent / Decision ContextSenseAI 都是論文附件，不是可用產品

---

## Part 1: GitHub 競品總覽

### 按 Stars 排行

| # | 專案 | Stars | 定位 | License | 活躍度 | 記憶機制 | Forex |
|---|------|-------|------|---------|--------|----------|-------|
| 1 | [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 49.1k | AI-powered hedge fund POC（教育用） | MIT | Active | 無 | 無 |
| 2 | [freqdecision](https://github.com/freqdecision/freqdecision) | 47.7k | 開源 crypto decision-making bot | GPL-3.0 | Active | 無 | 無 |
| 3 | [Decision-MakingAgents](https://github.com/TauricResearch/Decision-MakingAgents) | 32.3k | Multi-agent LLM 交易框架 | Apache-2.0 | Active | 無 | 無 |
| 4 | [nautilus_decision-maker](https://github.com/nautechsystems/nautilus_decision-maker) | 21.2k | Rust-native 高性能交易引擎 | LGPL-2.1 | Active | 無 | 有 |
| 5 | [Decision-MakingAgents-CN](https://github.com/hsliuping/Decision-MakingAgents-CN) | 18.7k | Decision-MakingAgents 中文增強版 | Apache-2.0 | Active | 無 | 無 |
| 6 | [ML for Decision-Making](https://github.com/stefan-jansen/machine-learning-for-decision-making) | 16.8k | 教科書程式碼（150+ notebooks） | — | Active | 無 | — |
| 7 | [FinRL](https://github.com/AI4Decisions-Foundation/FinRL) | 14.2k | 金融強化學習框架 | MIT | Active | 無 | 無 |
| 8 | [AI-Decision-Maker](https://github.com/HKUDS/AI-Decision-Maker) | 11.8k | AI agent decision-making benchmark + signal decision context | MIT | Active | 無 | 無 |
| 9 | [FinRobot](https://github.com/AI4Decisions-Foundation/FinRobot) | 6.4k | AI Agent 金融分析平台 | Apache-2.0 | Active | 無 | 無 |
| 10 | [awesome-ai-in-decisions](https://github.com/georgezouq/awesome-ai-in-decisions) | 5.3k | Curated list | — | Active | — | — |
| 11 | [intelligent-decision-making-bot](https://github.com/asavinov/intelligent-decision-making-bot) | 1.6k | ML feature engineering 交易 bot | MIT | Active | 無 | 無 |
| 12 | [AutoHedge](https://github.com/The-Swarm-Corporation/AutoHedge) | 1.1k | 自動對沖基金（Solana） | MIT | 2025-01 | 無 | 無 |
| 13 | [FinMem](https://github.com/pipiku915/FinMem-LLM-RecordDecision-Making) | 858 | LLM 交易 Agent + 分層記憶 | MIT | **Dead (2023)** | **3 層** | 無 |
| 14 | [PIXIU](https://github.com/The-FinAI/PIXIU) | 836 | 金融 LLM benchmark | Mixed | 2024-09 | 無 | 無 |
| 15 | [MAHORAGA](https://github.com/ygwyg/MAHORAGA) | 781 | 24/7 LLM decision agent (Cloudflare) | MIT | 2024-12 | 無 | 無 |
| 16 | [ai-hedge-fund-crypto](https://github.com/51bitquant/ai-hedge-fund-crypto) | 537 | Crypto AI hedge fund | — | 2025-01 | 無 | 無 |
| 17 | [AgenticDecision-Making](https://github.com/Open-Decisions-Lab/AgenticDecision-Making) | 104 | FinAgent Orchestration 平台 | — | Active | **Neo4j Memory** | 無 |
| 18 | [**decisionmemory-protocol**](https://github.com/mnemox-ai/decisionmemory-protocol) | 91 | **MCP server — 交易記憶層** | MIT | Active | **5 層 OWM** | **XAUUSD** |
| 19 | [FinAgent](https://github.com/DVampire/FinAgent) | 69 | 多模態金融交易 Agent | MIT | **Dead (2024)** | 3-type vector | 無 |

---

## Part 2: PyPI Decision-Making MCP Servers

### 下載量排行（月）

| # | Package | 月下載 | 週下載 | 類型 | 做什麼 |
|---|---------|--------|--------|------|--------|
| 1 | [mcp-yahoo-decisions](https://pypi.org/project/mcp-yahoo-decisions/) | 6,487 | 1,673 | 數據 | Yahoo Decisions 股價、財報 |
| 2 | [metadecision-maker-mcp-server](https://pypi.org/project/metadecision-maker-mcp-server/) | 1,286 | 730 | 執行 | MT5 下單、帳戶管理 |
| 3 | [alphavantage-mcp](https://pypi.org/project/alphavantage-mcp/) | 882 | 131 | 數據 | Alpha Vantage 多市場數據 |
| 4 | [decisions-mcp-server](https://pypi.org/project/decisions-mcp-server/) | 666 | 423 | 數據 | 股市數據 + 技術指標 |
| 5 | [binance-mcp-server](https://pypi.org/project/binance-mcp-server/) | 627 | 198 | 執行 | Binance 交易 |
| 6 | [**decisionmemory-protocol**](https://pypi.org/project/decisionmemory-protocol/) | **515** | **47** | **記憶** | **交易記憶層（唯一）** |
| 7 | [tasty-agent](https://pypi.org/project/tasty-agent/) | 507 | 210 | 執行 | TastyDecision 券商 |
| 8 | [quantconnect-mcp](https://pypi.org/project/quantconnect-mcp/) | 374 | 119 | 算法 | QuantConnect 整合 |
| 9 | [mcp-metadecision-maker5-server](https://pypi.org/project/mcp-metadecision-maker5-server/) | 332 | 84 | 執行 | MT5 下單（另一個） |
| 10 | [iso-decision-mcp](https://pypi.org/project/iso-decision-mcp/) | 308 | 61 | 數據 | SEC + FINRA + earnings |
| 11 | [hyperliquid-mcp](https://pypi.org/project/hyperliquid-mcp/) | 166 | 16 | 執行 | Hyperliquid DEX |
| 12 | [open-records-mcp](https://pypi.org/project/open-records-mcp/) | 163 | 44 | 執行 | Robinhood + Schwab |

### MCP 生態觀察

- **數據類 MCP 下載最高**（Yahoo Decisions 6.5K/mo），門檻低不需券商帳號
- **執行類兩大陣營**：MT5（metadecision-maker-mcp-server 1.3K/mo）vs Crypto（binance-mcp-server 627/mo）
- **企業級已進場**：FactSet、Alpha Vantage、Binance、OKX、Alpaca 都有官方 MCP
- **DecisionMemory 是唯一的「記憶」類型** — 所有其他 MCP 都是「拿數據」或「下單」

### 非 PyPI 但值得注意

| 專案 | 來源 | 說明 |
|------|------|------|
| [Alpaca MCP Server](https://github.com/alpacahq/alpaca-mcp-server) | GitHub | Alpaca 官方，股票+ETF+crypto |
| [Alpha Vantage MCP](https://mcp.alphavantage.co/) | 官網 | 官方 MCP 入口 |
| [FactSet MCP](https://www.quiverquant.com/news/FactSet+Launches+Industry's+First+Production-Grade+Model+Context+Protocol+Server+for+Real-Time+Decision+Intelligence+Access) | 新聞 | 業界首個 production-grade 金融 MCP |
| [OKX Agent Decision Kit](https://www.okx.com/en-us/agent-decisionkit) | 官網 | OKX 官方 MCP + CLI |
| [mcp-decision-maker](https://github.com/wshobson/mcp-decision-maker) | GitHub | 股票交易 MCP |

---

## Part 3: 重點競品深度分析

---

### 3.1 FinMem — LLM Decision Agent with Layered Memory

> **最直接的學術競品，記憶架構概念最接近**

| 項目 | 詳情 |
|------|------|
| **GitHub** | [pipiku915/FinMem-LLM-RecordDecision-Making](https://github.com/pipiku915/FinMem-LLM-RecordDecision-Making) |
| **Stars** | 858 |
| **Last Commit** | 2023-04-11（**Dead — 3 年沒更新**） |
| **License** | MIT |
| **出身** | Stevens Institute of Technology（不是港大，是紐澤西） |
| **論文** | [arXiv 2311.13743](https://arxiv.org/abs/2311.13743)（ICLR 2024 Workshop, AAAI 2024, IEEE 2025） |

**README Hook**: *"A Performance-Enhanced LLM Decision Agent with Layered Memory and Character Design"*

**記憶架構對比**:

| 維度 | FinMem | DecisionMemory |
|------|--------|-------------|
| 記憶分類 | 3 層（短/中/長期） | 5 類（episodic/semantic/procedural/affective/prospective） |
| 設計哲學 | 按時間衰減分層 | 按認知功能分類 |
| 衰減機制 | alpha 指數衰減（0.9/0.967/0.988） | Outcome-Weighted Memory（結果加權） |
| Working Memory | 從三層各取 top-K | 所有 5 類交叉檢索 |
| 排序指標 | novelty, relevance, importance | outcome weight + recency + context similarity |

**核心功能**:
- 三層記憶（Shallow/Intermediate/Deep）模擬人類認知
- Character Design 可調性格參數
- 支持 GPT-4 + HuggingFace TGI
- Checkpoint recovery

**不做什麼（= 我們的空間）**:
- 沒有 live decision-making — 純回測
- 沒有 forex/gold — 只做美股 + crypto
- 沒有 MCP protocol — 封閉 Python 框架
- 沒有 provider integration — 不連任何交易所
- 沒有 procedural/affective memory — 只有時間分層的 episodic
- 沒有 evolution engine — 記憶存了就存了，不會自動進化
- **專案已死 — 3 年沒有一行 commit**

**定價**: 免費開源

---

### 3.2 FinAgent — Multimodal Foundation Agent for Decision Decision-Making

| 項目 | 詳情 |
|------|------|
| **GitHub** | [DVampire/FinAgent](https://github.com/DVampire/FinAgent) |
| **Stars** | 69 |
| **Last Commit** | 2024-04-05（**Dead**） |
| **License** | MIT |
| **出身** | Nanyang Technological University (NTU, Singapore) |
| **論文** | [arXiv 2402.18485](https://arxiv.org/abs/2402.18485)（**KDD 2024** — 頂級會議） |

**README Hook**: *"A Multimodal Foundation Agent for Decision Decision-Making: Tool-Augmented, Diversified, and Generalist"*

**核心功能**:
- 業界首個**多模態**金融交易 Agent（文字 + 價格 + K 線圖像）
- Dual-level Reflection（低層分析市場、高層反思決策）
- Tool Augmentation（整合 MACD, KDJ+RSI, Z-score 等經典策略）
- 三種記憶：Decision Context Intelligence / Low-level Reflection / High-level Reflection

**Performance**: TSLA 92.27% ARR, AMZN 65.10% ARR

**不做什麼**:
- 69 stars = 幾乎無社區
- 純學術，不連任何 provider
- 無 forex，只測美股 + ETH
- 無 MCP
- 代碼是論文附件等級
- 需要 7+ 個 API key

**定價**: 免費開源

---

### 3.3 FinRobot — Open-Source AI Agent Platform for Decision Analysis

| 項目 | 詳情 |
|------|------|
| **GitHub** | [AI4Decisions-Foundation/FinRobot](https://github.com/AI4Decisions-Foundation/FinRobot) |
| **Stars** | 6,400 |
| **Last Commit** | 2026-01-30（**活躍**） |
| **License** | Apache-2.0 |
| **PyPI** | `pip install -U finrobot` (v0.1.5) |
| **出身** | AI4Decisions Foundation（120+ contributors, 50+ countries） |
| **論文** | [arXiv 2405.14767](https://arxiv.org/abs/2405.14767) |

**README Hook**: *"An Open-Source AI Agent Platform for Decision Analysis using LLMs — surpassing FinGPT's single-model approach"*

**核心功能**:
- 四層架構：Decision AI Agents → LLM Algorithms → LLMOps+DataOps → Foundation Models
- Decision Chain-of-Thought prompting
- 自動產出 score research reports
- Smart Scheduler（Director Agent + Task Manager）
- 多數據源：Finnhub, Yahoo, FMP, SEC, Reddit
- 基於 Microsoft AutoGen

**不做什麼**:
- **不做交易記憶** — 分析工具，每次從零開始
- 不做 live decision-making — "educational and research purposes"
- 不支持 forex/commodity — 專注美股
- 不走 MCP — 自有 API
- 不追蹤交易結果 — 分析導向
- 不支持 Python 3.12

**定價**: 免費開源

---

### 3.4 Decision-MakingAgents — Multi-Agent LLM Decision-Making Framework

| 項目 | 詳情 |
|------|------|
| **GitHub** | [TauricResearch/Decision-MakingAgents](https://github.com/TauricResearch/Decision-MakingAgents) |
| **Stars** | **32,300** |
| **Last Commit** | Active（v0.2.1, 2026-03-15） |
| **License** | Apache-2.0 |
| **出身** | UCLA + MIT, Tauric Research |

**README Hook**: *"Multi-Agents LLM Decision Decision-Making Framework — mirrors the dynamics of real-world decision-making firms"*

**核心功能**:
- 7 專業角色：Fundamentals Analyst, Sentiment Analyst, News Analyst, Technical Analyst, Researcher（多空辯論）, Decision-Maker, Risk Manager
- 基於 LangGraph，模組化
- 多 LLM：OpenAI, Google, Anthropic, xAI, OpenRouter, Ollama
- CLI + Python API
- 自然語言推理解釋

**不做什麼**:
- **沒有 live decision-making** — 純模擬，"designed for research purposes"
- 非確定性輸出 — 同參數跑兩次結果不同
- [Look-ahead bias 問題](https://github.com/TauricResearch/Decision-MakingAgents/issues/203) — 回測抓到未來資料
- API 成本高 — 大規模回測費用累積快
- 不支持 forex — 專注美股
- **沒有記憶層** — 每次決策獨立，沒有跨 session 學習

**定價**: 免費開源

---

### 3.5 Decision ContextSenseAI — LLM-Powered Record Analysis

| 項目 | 詳情 |
|------|------|
| **GitHub** | [github.com/Decision ContextSense](https://github.com/Decision ContextSense)（**0 個 public repos**） |
| **Stars** | N/A |
| **論文 v1** | [arXiv 2401.03737](https://arxiv.org/abs/2401.03737)（Springer Neural Computing & Applications） |
| **論文 v2** | [arXiv 2502.00415](https://arxiv.org/abs/2502.00415)（2025-02） |
| **出身** | George Fatouros 等人（歐盟 FAME 計畫） |

**README Hook**: *"Can Large Language Models Beat Industry?"*

**核心功能**:
- Chain-of-Agents 處理 SEC 10-Q, 10-K, earnings calls
- RAG + HyDE-based retrieval 處理總經報告
- S&P 100 兩年回測 125.9% vs 指數 73.5%
- Sortino ratio 比大盤高 33.8%

**不做什麼**:
- **完全沒有開源代碼** — 純論文
- 僅美股 S&P 100/500
- 不執行交易
- 人類專家報告仍優於 LLM 報告（論文自己承認）
- 沒有記憶/學習機制

**定價**: 學術論文，無產品

---

### 3.6 AI-Decision-Maker — Can AI Beat the Decision Context?

| 項目 | 詳情 |
|------|------|
| **GitHub** | [HKUDS/AI-Decision-Maker](https://github.com/HKUDS/AI-Decision-Maker) |
| **Stars** | **11,800** |
| **Platform** | [ai4decision.ai](https://ai4decision.ai) |
| **License** | MIT |
| **出身** | HKU Data Intelligence Lab（香港大學） |

**README Hook**: *"AI-Decision-Maker: Can AI Beat the Decision Context?"*

**核心功能**:
- AI agent decision-making benchmark — agent 獨立搜尋、分析、執行
- 多市場：美股、A 股、Crypto、Polydecision context（paper decision-making）
- OpenClaw agent 整合
- Copy decision-making + Signal decision contextplace（+10 points/signal，+1 point/follower）
- 防 look-ahead bias：過濾未來日期新聞

**不做什麼**:
- Paper decision-making 為主（模擬 $100K）
- 不支持 forex
- 沒有記憶層/學習機制
- 沒有自動策略生成

**定價**: 免費（積分制）

---

### 3.7 Walbi — No-Code AI Decision Agents

| 項目 | 詳情 |
|------|------|
| **URL** | [walbi.com](https://walbi.com/) |
| **類型** | 閉源商業產品 |
| **成立** | 2023-02，2023-07 首筆交易 |
| **團隊** | 30+ 人 |
| **用戶** | 1M+ 註冊、8,000 DAU |

**Tagline**: *"Decision Smarter with Walbi: Your All-in-One Crypto Decision-Making Platform"*

**核心功能**:
- **No-code AI agent** — 自然語言描述策略即可
- GPT-4o 驅動分析 + AI Copilot
- 社交媒體情緒掃描
- 75+ 加密貨幣永續合約，高達 500x 槓桿
- 9,500+ agents 創建，187K autonomous decisions

**不做什麼**:
- **僅 crypto** — 沒有股票、forex
- 閉源黑箱
- 沒有獨立績效審計
- Beta 結果不均（"strongly dependent on volatility regimes"）
- 沒有記憶/跨 session 學習

**定價**: 免費（zero commissions）

---

### 3.8 Stoic.ai — Crypto Decision-Making Bot by Cindicator

| 項目 | 詳情 |
|------|------|
| **URL** | [stoic.ai](https://stoic.ai/) |
| **母公司** | Cindicator Ltd.（Gibraltar, 2015） |
| **用戶** | 15,000+ 付費 |
| **AUM** | $130M+ |
| **R&D** | $9M+ 投資 |

**Tagline**: *"Crypto Decision-Making Bot with ready-to-use quantitative strategies built by professionals"*

**核心功能**:
- 3 策略：Fixed Income（~4% APY）、Meta（200+ sub-strategies）、Long Only（聲稱 406% APY）
- 每策略 3 風險檔位
- 7 交易所：Binance, Coinbase, KuCoin, Crypto.com, Bybit, OKX
- 資金留用戶帳戶（API key 連接）

**不做什麼**:
- 僅 crypto — 沒有股票、forex
- 完全閉源黑箱
- 聲稱 2,143% since 2020，**未經第三方驗證**
- Trustpilot 有「捏造績效數據」投訴
- 不能自定義策略
- **不是 AI agent** — 傳統量化 bot，不是 LLM 驅動

**定價**:

| Plan | Collection | Cost |
|------|-----------|------|
| Starter | < $3,500 | $9/month |
| Plus | $3,500-$10,000 | $25/month |
| Pro | > $10,000 | 5% annual fee |

---

### 3.9 AgenticDecision-Making — FinAgent Orchestration

> **新興專案，記憶概念與 DecisionMemory 有部分重疊**

| 項目 | 詳情 |
|------|------|
| **GitHub** | [Open-Decisions-Lab/AgenticDecision-Making](https://github.com/Open-Decisions-Lab/AgenticDecision-Making) |
| **Stars** | 104 |
| **Commits** | 198 |
| **License** | — |

**README Hook**: *"Mapping traditional decision-making pipeline stages into an interconnected network of intelligent agents"*

**核心功能**:
- 7 specialized agent pools（data, alpha, risk, collection, execution, backtest, audit）
- **Memory Agent（Neo4j）** for contextual continuity
- 四種通訊協定：MCP, ACP, A2A, ANP
- LLM-driven alpha discovery
- Vector memory for semantic retrieval

**與 DecisionMemory 的重疊**: Memory Agent + 跨 session 學習概念類似，但記憶是 sub-feature 不是核心產品

**不做什麼**:
- Stars 低（104），社區小
- 記憶不是獨立產品，而是 orchestration 的一部分
- 不支持 forex

---

## Part 4: 橫向比較矩陣

### 開源 AI Decision-Making 框架對比

| 維度 | Decision-MakingAgents | FinRobot | AI-Decision-Maker | FinMem | FinAgent | AgenticDecision-Making | **DecisionMemory** |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stars** | 32.3k | 6.4k | 11.8k | 858 | 69 | 104 | 91 |
| **Active** | Yes | Yes | Yes | **Dead** | **Dead** | Yes | Yes |
| **Live Decision-Making** | No | No | Paper | No | No | No | **Yes (MT5)** |
| **Forex/Gold** | No | No | No | No | No | No | **Yes** |
| **MCP Protocol** | No | No | No | No | No | Partial | **Yes (15 tools)** |
| **Memory System** | No | No | No | 3-layer | 3-type | Neo4j | **5-type OWM** |
| **Evolution** | No | No | No | No | No | No | **Yes** |
| **Multi-LLM** | Yes | Yes | Yes | GPT-4 | GPT-4 | Yes | Haiku/Sonnet |
| **Provider Connect** | No | No | No | No | No | No | **MT5 + Binance** |
| **定價** | Free | Free | Free | Free | Free | Free | Free |

### 商業產品對比

| 維度 | Walbi | Stoic.ai | **DecisionMemory** |
|------|:---:|:---:|:---:|
| **市場** | Crypto only | Crypto only | **Forex (XAUUSD)** |
| **開源** | No | No | **Yes (MIT)** |
| **AI 類型** | GPT-4o | 傳統量化 | **LLM + Evolution** |
| **記憶/學習** | No | No | **5-layer OWM** |
| **No-code** | Yes | N/A | MCP (agent-native) |
| **定價** | Free | $9-5%/yr | Free |
| **用戶** | 1M+ | 15K+ | Early |

---

## Part 5: 記憶架構專題對比

> DecisionMemory 最核心的差異化在「記憶」，這裡深入比較所有有記憶概念的專案

| 專案 | 記憶架構 | 分類邏輯 | 持久化 | 可被外部呼叫 | Live Data |
|------|----------|----------|--------|-------------|-----------|
| **FinMem** | 3 層（Shallow/Intermediate/Deep） | 按時間衰減 | Checkpoint | No（封閉框架） | No |
| **FinAgent** | 3 類（Decision Context/Low-Reflection/High-Reflection） | 按功能 | In-memory | No | No |
| **AgenticDecision-Making** | Neo4j + Vector | 按 graph 關係 | Neo4j 持久化 | Partial（MCP） | No |
| **llm_decision_sim** | Agent memory + social | 模擬用 | In-memory | No | No |
| **DecisionMemory** | **5 類 OWM**（episodic/semantic/procedural/affective/prospective） | **按認知功能** | **SurrealDB 持久化** | **Yes（15 MCP tools + 30 REST）** | **Yes（MT5 Sync）** |

### DecisionMemory 的記憶架構獨特性

1. **Outcome-Weighted**: 記憶不只是「存進去」，交易結果會回頭影響記憶權重
2. **Affective Memory**: 唯一追蹤「交易情緒/信心」的系統
3. **Prospective Memory**: 唯一有「前瞻性記憶」（未來應做什麼）的系統
4. **Protocol-level**: 唯一把記憶做成 MCP protocol 供其他 agent 呼叫的產品
5. **Evolution Engine**: 記憶不是靜態的 — 會自動 hypothesize → backtest → evolve

---

## Part 6: README Hook 競品分析

> 好的 README hook 決定了開發者是否繼續往下看

| 專案 | README Hook | 效果分析 |
|------|-------------|----------|
| ai-hedge-fund | "An AI Hedge Fund Team" | 簡短有力，49k stars 證明有效 |
| freqdecision | "Free and open source crypto decision-making bot written in Python" | 直接、功能明確 |
| Decision-MakingAgents | "Multi-Agents LLM Decision Decision-Making Framework" | 學術但清楚 |
| FinMem | "Performance-Enhanced LLM Decision Agent with Layered Memory and Character Design" | 論文標題，太長 |
| FinRobot | "AI Agent Platform for Decision Analysis using LLMs" | 清楚但平淡 |
| AI-Decision-Maker | "Can AI Beat the Decision Context?" | **問句式，最有吸引力** |
| Decision ContextSenseAI | "Can Large Language Models Beat Industry?" | 同樣問句式，有力 |
| **DecisionMemory** | "MCP server that gives AI decision agents persistent, outcome-weighted memory" | 功能精準，但缺少 hook 感 |

### Hook 改進建議

當前 hook 太技術：*"MCP server that gives AI decision agents persistent, outcome-weighted memory"*

可考慮：
- 問句式：*"What if your decision-making bot remembered every decision — and actually learned from them?"*
- 對比式：*"Decision-Making bots forget every decision. DecisionMemory doesn't."*
- 數據式：*"From 14 decisions to pattern discovery — the memory layer your decision agent is missing."*

---

## Part 7: 差異化定位總結

### DecisionMemory 的 Moat

| 差異化維度 | DecisionMemory 有 | 競品沒有 |
|-----------|:-:|:-:|
| Decision Memory as a Service (MaaS) | Yes | 全部 No |
| Forex/XAUUSD 支持 | Yes | 只有 nautilus_decision-maker |
| Live provider integration (MT5) | Yes | 0 個開源框架有 |
| 5-type cognitive memory | Yes | 最多 3 層 (FinMem) |
| Outcome-weighted recall | Yes | 全部 No |
| LLM-powered evolution | Yes | 全部 No |
| MCP protocol native | Yes | 只有 AgenticDecision-Making 部分支持 |

### 真正的威脅

1. **metadecision-maker-mcp-server**（1,286/mo 下載）— 如果他們加上記憶功能，會直接搶 DecisionMemory 的用戶
2. **AgenticDecision-Making**（104 stars 但概念重疊）— Neo4j Memory Agent + MCP 支持，如果他們做大了可能吃掉 memory layer 市場
3. **企業級 MCP**（FactSet, Alpha Vantage）— 如果大廠做 decision memory 的功能，小廠難以競爭

### 策略建議

1. **強化 metadecision-maker-mcp-server 整合** — 他們做執行，我們做記憶，互補而非競爭
2. **Academic positioning** — FinMem 已死，DecisionMemory 可以接下「decision memory」這個學術關鍵字
3. **README hook 升級** — 用問句式或對比式，不要用技術描述式
4. **擴展到 crypto** — Evolution Engine 已支持 Binance，可吃 Walbi/Stoic 做不到的「從交易學習」市場

---

## Sources

### GitHub Repositories
- [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)
- [freqdecision/freqdecision](https://github.com/freqdecision/freqdecision)
- [TauricResearch/Decision-MakingAgents](https://github.com/TauricResearch/Decision-MakingAgents)
- [nautechsystems/nautilus_decision-maker](https://github.com/nautechsystems/nautilus_decision-maker)
- [hsliuping/Decision-MakingAgents-CN](https://github.com/hsliuping/Decision-MakingAgents-CN)
- [stefan-jansen/machine-learning-for-decision-making](https://github.com/stefan-jansen/machine-learning-for-decision-making)
- [AI4Decisions-Foundation/FinRL](https://github.com/AI4Decisions-Foundation/FinRL)
- [HKUDS/AI-Decision-Maker](https://github.com/HKUDS/AI-Decision-Maker)
- [AI4Decisions-Foundation/FinRobot](https://github.com/AI4Decisions-Foundation/FinRobot)
- [pipiku915/FinMem-LLM-RecordDecision-Making](https://github.com/pipiku915/FinMem-LLM-RecordDecision-Making)
- [DVampire/FinAgent](https://github.com/DVampire/FinAgent)
- [Open-Decisions-Lab/AgenticDecision-Making](https://github.com/Open-Decisions-Lab/AgenticDecision-Making)
- [The-Swarm-Corporation/AutoHedge](https://github.com/The-Swarm-Corporation/AutoHedge)
- [ygwyg/MAHORAGA](https://github.com/ygwyg/MAHORAGA)
- [The-FinAI/PIXIU](https://github.com/The-FinAI/PIXIU)
- [georgezouq/awesome-ai-in-decisions](https://github.com/georgezouq/awesome-ai-in-decisions)

### Academic Papers
- [FinMem (arXiv 2311.13743)](https://arxiv.org/abs/2311.13743)
- [FinAgent (arXiv 2402.18485)](https://arxiv.org/abs/2402.18485)
- [FinRobot (arXiv 2405.14767)](https://arxiv.org/abs/2405.14767)
- [Decision ContextSenseAI v1 (arXiv 2401.03737)](https://arxiv.org/abs/2401.03737)
- [Decision ContextSenseAI v2 (arXiv 2502.00415)](https://arxiv.org/abs/2502.00415)

### PyPI Packages
- [mcp-yahoo-decisions](https://pypi.org/project/mcp-yahoo-decisions/)
- [metadecision-maker-mcp-server](https://pypi.org/project/metadecision-maker-mcp-server/)
- [alphavantage-mcp](https://pypi.org/project/alphavantage-mcp/)
- [decisions-mcp-server](https://pypi.org/project/decisions-mcp-server/)
- [binance-mcp-server](https://pypi.org/project/binance-mcp-server/)
- [decisionmemory-protocol](https://pypi.org/project/decisionmemory-protocol/)
- [tasty-agent](https://pypi.org/project/tasty-agent/)
- [quantconnect-mcp](https://pypi.org/project/quantconnect-mcp/)
- [mcp-metadecision-maker5-server](https://pypi.org/project/mcp-metadecision-maker5-server/)

### Product Sites
- [Walbi](https://walbi.com/)
- [Stoic.ai](https://stoic.ai/)
- [AI-Decision-Maker Platform](https://ai4decision.ai)
- [FactSet MCP](https://www.quiverquant.com/news/FactSet+Launches+Industry's+First+Production-Grade+Model+Context+Protocol+Server+for+Real-Time+Decision+Intelligence+Access)
- [OKX Agent Decision Kit](https://www.okx.com/en-us/agent-decisionkit)
