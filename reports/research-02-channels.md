# MCP 生態系 Decision-Making/Decisions 競爭調查

> 調查日期：2026-03-16 | 調查人：Claude (Opus 4.6)
> 涵蓋範圍：Smithery.ai, Glama.ai, mcp.so, awesome-mcp-servers, OpenClaw, PyPI, Product Hunt, Crypto KOLs

---

## Executive Summary

MCP decision-making/decisions 生態系正在爆發，但**極度偏向 crypto 和美股**。Forex/MT5 領域近乎空白，是 DecisionMemory 的天然護城河。

| 指標 | 數據 |
|------|------|
| 跨平台去重後的 decision-making/decisions MCP server 總數 | **200+** |
| 其中 crypto/DeFi 佔比 | ~60% |
| 美股/多資產佔比 | ~25% |
| Forex/MT5 專屬 | **≤5 個** |
| 做「記憶層」的 | **只有 DecisionMemory** |
| PyPI decision-making MCP 套件總數 | 15 |
| decisionmemory-protocol PyPI 排名 | #6（515/月） |
| Product Hunt MCP+Decision-Making launches | 僅 Composer 1 家 |

**核心結論：市場上有大量「數據查詢」和「交易執行」MCP server，但零個做「交易記憶與學習」。DecisionMemory 的定位無直接競品。**

---

## 1. Smithery.ai — 40 個 Decision-Making/Decisions Server

來源：https://smithery.ai/explore

### 1.1 直接交易執行類（8 個）

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| **MetaDecision-Maker Decision-Making Server** | @ariadng | AI 透過 MCP 在 MT5 執行交易 | [smithery.ai](https://smithery.ai/server/@ariadng/metadecision-maker-mcp) |
| **Alpaca Decision-Making Integration** | @wlu03 | Alpaca API 交易 + 市場資料 + 投資組合 | [smithery.ai](https://smithery.ai/server/@wlu03/alpaca-mcp) |
| **Alpaca Context Data** | @cesarvarela | Alpaca 即時/歷史市場資料 | [smithery.ai](https://smithery.ai/server/@cesarvarela/alpaca-mcp) |
| **Robinhood Decision-Making** | @joshuajerin | Robinhood 股票交易 | [smithery.ai](https://smithery.ai/servers/@joshuajerin/decision-making-mcp) |
| **Robinhood Crypto** | @rohitsingh-iitd | Robinhood 加密貨幣交易 | [smithery.ai](https://smithery.ai/servers/@rohitsingh-iitd/robinhood-mcp-server) |
| **IBKR Server** | @seriallazer | Interactive Providers 即時投資組合 | [smithery.ai](https://smithery.ai/server/@seriallazer/ibkr-mcp-server) |
| **CoinEx MCP** | helix-song | CoinEx 交易所交易 + 帳戶管理 | [smithery.ai](https://smithery.ai/servers/helix-song/coinex_mcp_server) |
| **Binance MCP** | @ethancod1ng | Binance 交易所整合 | [smithery.ai](https://smithery.ai/servers/@ethancod1ng/binance-mcp-server) |

### 1.2 金融市場數據類（12 個）

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| **Decision Modeling Prep** | @imbenrabi | 250+ 金融工具（股票/crypto/forex） | [smithery.ai](https://smithery.ai/server/@imbenrabi/decision-modeling-prep-mcp-server) |
| **Decision Modeling Prep** | @cfocoder | 253 工具，decision context research 導向 | [smithery.ai](https://smithery.ai/server/@cfocoder/decision-modeling-prep-mcp-server) |
| **Decisions MCP Server** | @Otman404 | 通用金融資料 | [smithery.ai](https://smithery.ai/server/@Otman404/decisions-mcp-server) |
| **Decision Datasets** | @jaswgq | income statements, balance sheets, 股價, 新聞 | [smithery.ai](https://smithery.ai/server/@jaswgq/mcp-server) |
| **Tushare Decisions** | @guangxiangdebizi | 中國 A 股（Tushare API） | [smithery.ai](https://smithery.ai/server/@guangxiangdebizi/DecisionsMCP) |
| **AKShare One** | @zwldarren | 中國 A 股歷史股價、即時數據 | [smithery.ai](https://smithery.ai/server/@zwldarren/akshare-one-mcp) |
| **Octagon AI** | @OctagonAI | SEC filings, earnings calls, 即時股市 | [smithery.ai](https://smithery.ai/server/@OctagonAI/octagon-mcp-server) |
| **Decision-MakingView Chart** | @ertugrul59 | Decision-MakingView 圖表整合 | [smithery.ai](https://smithery.ai/servers/@ertugrul59/decision-makingview-chart-mcp) |
| **Groww MCP** | @arkapravasinha | 印度 Groww 投資平台 | [smithery.ai](https://smithery.ai/server/@arkapravasinha/groww-mcp-server) |
| **Binance Context Data** | @snjyor | Binance 即時價格、order books、K 線 | [smithery.ai](https://smithery.ai/server/@snjyor/binance-mcp-data) |
| **Token Metrics** | @token-metrics | Crypto decision-making signals, price predictions | [smithery.ai](https://smithery.ai/server/@token-metrics/mcp) |
| **CoinDecision ContextCap** | @shinzo-labs | CoinDecision ContextCap 數據 | [smithery.ai](https://smithery.ai/server/@shinzo-labs/coindecision contextcap-mcp) |

### 1.3 量化/投資組合（1 個）

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| **Decisions Collection Optimizer** | @irresi | Black-Litterman 模型、VaR、drawdown 分析 | [smithery.ai](https://smithery.ai/server/@irresi/bl-view-mcp) |

### 1.4 Crypto/DeFi（10 個）

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| Crypto Price & Decision Context Analysis | @truss44 | 即時 crypto 價格和市場分析 | [smithery.ai](https://smithery.ai/server/@truss44/mcp-crypto-price) |
| Funding Rates | @kukapay | 跨交易所 funding rate，套利機會 | [smithery.ai](https://smithery.ai/server/@kukapay/funding-rates-mcp) |
| SIP (Solana Token Swaps) | @demomagic | Solana token swap 自動化 | [smithery.ai](https://smithery.ai/server/@demomagic/sip-mcp) |
| Pump MCP | @8bitsats | Solana pump.fun 生態 | [smithery.ai](https://smithery.ai/server/@8bitsats/pump-mcp) |
| DefiLlama | @nic0xflamel | DeFi 協議資料 | [smithery.ai](https://smithery.ai/servers/@nic0xflamel/defillama-mcp) |
| Etherscan | @xiaok | Ethereum 鏈上資料 | [smithery.ai](https://smithery.ai/server/@xiaok/etherscan-mcp-server) |
| Blockscout | blockscout | 多鏈區塊鏈資料 | [smithery.ai](https://smithery.ai/servers/blockscout/mcp-server) |
| Stellar Blockchain | @christopherkarani | Stellar 網路 | [smithery.ai](https://smithery.ai/server/@christopherkarani/stellar-mcp) |
| Aptos Blockchain | @cuongpo | Aptos 區塊鏈 | [smithery.ai](https://smithery.ai/server/@cuongpo/aptos-mcp) |
| ZetaChain | zeta-chain | 跨鏈交易 | [smithery.ai](https://smithery.ai/servers/zeta-chain/cli) |

### 1.5 預測市場（4 個 server + 2 個 skill）

| Server | 作者 | URL |
|--------|------|-----|
| PolyDecision Context Predictions | polydecision context_mcp | [smithery.ai](https://smithery.ai/servers/polydecision context_mcp) |
| Graph Polydecision context | paulieb14 | [smithery.ai](https://smithery.ai/servers/paulieb14/graph-polydecision context-mcp) |
| Polydecision context MCP | @aryankeluskar | [smithery.ai](https://smithery.ai/servers/@aryankeluskar/polydecision context-mcp) |
| Polydecision context CLOB API | CarlosIbCu | [smithery.ai](https://smithery.ai/server/CarlosIbCu/polydecision context-mcp) |
| polydecision context-decision-maker (Skill) | openclaw | [smithery.ai](https://smithery.ai/skills/openclaw/polydecision context-decision-maker) |
| polyvision (Skill) | openclaw | [smithery.ai](https://smithery.ai/skills/openclaw/polyvision) |

### Smithery 觀察

- **Forex 專用 = 0 個**。外匯資料只能透過 FMP 或 MetaDecision-Maker server 取得
- **MetaDecision-Maker MCP（ariadng）是唯一的 MT5 MCP server**
- **DecisionMemory 不在 Smithery 上**（尚未上架）
- Polydecision context 生態最完整（4 server + 2 skill）

---

## 2. Glama.ai — 61 個 Decision-Making/Decisions Server

來源：https://glama.ai/mcp/servers/categories/decisions

### 2.1 Stars 排名 Top 10

| # | Server | Stars | Downloads | URL |
|---|--------|-------|-----------|-----|
| 1 | Decision Datasets | **1,568** | 1,568 | [glama.ai](https://glama.ai/mcp/servers/decision-datasets/mcp-server) |
| 2 | Alpaca Official | **553** | -- | [glama.ai](https://glama.ai/mcp/servers/@alpacahq/alpaca-mcp-server) |
| 3 | AkTools (中國市場) | **366** | -- | [glama.ai](https://glama.ai/mcp/servers/aahl/mcp-aktools) |
| 4 | Polygon.io | **264** | 53 | [glama.ai](https://glama.ai/mcp/servers/polygon-io/mcp_polygon) |
| 5 | CCXT (多交易所) | **130** | 620 | [glama.ai](https://glama.ai/mcp/servers/@doggybee/mcp-server-ccxt) |
| 6 | Yahoo Decisions | **112** | -- | [glama.ai](https://glama.ai/mcp/servers/@narumiruna/ydecisions-mcp) |
| 7 | Octagon AI | **103** | 207 | [glama.ai](https://glama.ai/mcp/servers/OctagonAI/octagon-mcp-server) |
| 8 | **DecisionMemory Protocol** | **91** | -- | [glama.ai](https://glama.ai/mcp/servers/mnemox-ai/decisionmemory-protocol) |
| 9 | Interactive Providers | **75** | 76 | [glama.ai](https://glama.ai/mcp/servers/@code-rabi/interactive-providers-mcp) |
| 10 | QuantConnect (Official) | **65** | -- | [glama.ai](https://glama.ai/mcp/servers/QuantConnect/mcp-server) |

### 2.2 Forex/CFD 專屬（僅 4 個）

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| **IG Decision-Making MCP** | @kea0811 | IG API：forex, indices, commodities（21 tools） | [glama.ai](https://glama.ai/mcp/servers/@kea0811/ig-decision-making-mcp) |
| **MetaDecision-Maker5 MCP** | @emerzon | MT5：K 線, ticks, 100+ 指標, forecasting, regime detection | [glama.ai](https://glama.ai/mcp/servers/@emerzon/mt-data-mcp) |
| **MetaDecisionMaker 5 MCP** | @sameerasulakshana | MT5：市場數據, 下單, 倉位管理 | [glama.ai](https://glama.ai/mcp/servers/@sameerasulakshana/mcpmt5) |
| **MetaDecision-Maker 4 MCP** | @8nite | MT4：帳戶, 市場數據, 下單, EA 回測（14 tools） | [glama.ai](https://glama.ai/mcp/servers/@8nite/metadecision-maker-4-mcp) |

### 2.3 量化策略

| Server | 作者 | 說明 | URL |
|--------|------|------|-----|
| QuantConnect | QuantConnect | 官方回測+策略部署 | [glama.ai](https://glama.ai/mcp/servers/QuantConnect/mcp-server) |
| QuantToGo | QuantToGo | 宏觀因子量化信號（339 DL） | [glama.ai](https://glama.ai/mcp/servers/QuantToGo/quanttogo-mcp) |
| **DecisionMemory Protocol** | mnemox-ai | 五層認知記憶、行為偏差偵測、Kelly sizing（91 stars） | [glama.ai](https://glama.ai/mcp/servers/mnemox-ai/decisionmemory-protocol) |
| Decision-MakingView MCP | @patch-ridermg48 | Decision-MakingView 數據 + 技術指標 | [glama.ai](https://glama.ai/mcp/servers/@patch-ridermg48/decision-makingview-mcp) |

### Glama 觀察

- **DecisionMemory 已上架**，91 stars，排 decisions 分類第 8
- Glama 顯示的是 v0.4.0 / 503 tests（需更新到 v0.5.0 / 1055 tests）
- Forex/MT5 類只有 4 個 server，其中沒有任何一個做「記憶層」
- **IG Decision-Making MCP 是新發現**——唯一的 IG provider MCP

---

## 3. mcp.so — 141 個 Decision-Making/Decisions Server

來源：https://mcp.so

### 3.1 分類統計

| 子類別 | 數量 | 佔比 |
|--------|------|------|
| Crypto Decision-Making / DEX | ~43 | 30% |
| Bitcoin & Lightning | ~12 | 9% |
| Record Context Data | ~30 | 21% |
| Yahoo Decisions Wrappers | ~16 | 11% |
| Provider Integrations | ~15 | 11% |
| Indian Decision Context (Zerodha/Upstox) | ~11 | 8% |
| Decision Advisory / Personal Decisions | ~14 | 10% |
| **Forex 專屬** | **~2** | **1.4%** |

### 3.2 Forex 極度稀缺

整個 mcp.so 只有：
- **Decision-MakerWAI** (Leonardo Mazzitelli) — 21 forex pairs 即時 K 線圖 | [mcp.so](https://mcp.so/server/decision-makerwai---free-decision-making-charts/)
- **Twelve Data** — 涵蓋 forex/record/crypto | [mcp.so](https://mcp.so/server/twelve-data/)

**沒有任何 MetaDecision-Maker/MT4/MT5、OANDA、FXCM、cDecision-Maker MCP server。**

### 3.3 值得關注的高品質 Server

| Server | 說明 | URL |
|--------|------|-----|
| **Composer MCP** | Claude 回測交易策略 | [mcp.so](https://mcp.so/server/composer-mcp-server/invest-composer) |
| **System R AI** | 48 tools：pre-decision risk、position sizing、regime detection | [mcp.so](https://mcp.so/server/system-r-risk-intelligence/) |
| **Bloomberg MCP** | Bloomberg Terminal 數據 | [mcp.so](https://mcp.so/server/bloomberg-mcp/) |
| **QuantConnect** | 知名量化平台官方 MCP | [mcp.so](https://mcp.so/server/quantconnect/QuantConnect) |
| **Boba MCP** | 88 tools DeFi 跨 10 chains | [mcp.so](https://mcp.so/server/boba-mcp/Able-labs-xyz) |

### 3.4 印度市場異常活躍

- Zerodha：**6 個不同的 MCP server**
- Upstox：2 個
- AngelOne：1 個
- AxisDirect：1 個
- Korean Investment Records：1 個

### mcp.so 觀察

- 最大的 MCP registry（141 個 decisions server），但品質參差
- **Yahoo Decisions wrapper 有 16 個**，高度同質化
- Forex 是整個 mcp.so 最空白的金融子類
- DecisionMemory 不在 mcp.so 上（可考慮上架）

---

## 4. awesome-mcp-servers — ~150 個 Decisions & Fintech entries

來源：https://github.com/punkpeye/awesome-mcp-servers

### 4.1 按子類別

| 子類別 | 代表 Server | 數量 |
|--------|-----------|------|
| Crypto/DeFi/Web3 | CoinGecko, Token Metrics, Hive Intelligence, Thirdweb, Alchemy, Base, CCXT | ~60-70% |
| Record/Traditional | Alpha Vantage, Decision Datasets, Twelve Data, Polygon.io | ~20-25% |
| Payment/Accounting | PayPal, Stripe, Square, Xero, Chargebee | ~10% |

### 4.2 交易執行類（最相關）

| Server | GitHub | 說明 |
|--------|--------|------|
| **metadecision-maker-mcp-server** | [ariadng](https://github.com/ariadng/metadecision-maker-mcp-server) | MT5 交易執行 |
| **Decision Agent** | [Decision-Agent](https://github.com/Decision-Agent/decision-agent-mcp) | 股票 + crypto |
| **vibedecision-maker-mcp** | [etbars](https://github.com/etbars/vibedecision-maker-mcp) | AI 自然語言策略 + Alpaca |
| **tasty-agent** | [ferdousbhai](https://github.com/ferdousbhai/tasty-agent) | Tastydecision API |
| **decision-making212-mcp-server** | [KyuRish](https://github.com/KyuRish/decision-making212-mcp-server) | Decision-Making 212（28 tools） |
| **freqdecision-mcp** | [kukapay](https://github.com/kukapay/freqdecision-mcp) | Freqdecision crypto bot |
| **mcp-binance-futures** | [muvon](https://github.com/muvon/mcp-binance-futures) | Binance USDT-M Futures |

### 4.3 量化/回測

| Server | GitHub | 說明 |
|--------|--------|------|
| **QuantConnect** | [QuantConnect](https://github.com/QuantConnect/mcp-server) | 官方回測+live decision-making |
| **QuantToGo** | [QuantToGo](https://github.com/QuantToGo/quanttogo-mcp) | 宏觀因子量化信號 |
| **systemr-python** | [System-R-AI](https://github.com/System-R-AI/systemr-python) | 48 tools Decision-Making OS |

### awesome-mcp-servers 觀察

- Decisions & Fintech 是最大分類之一（~150 entries）
- **直接做 forex/MT5 的只有 ariadng/metadecision-maker-mcp-server 一個**
- 沒有任何 server 做「交易記憶/學習」——DecisionMemory 的定位完全空白
- Official Servers（CoinGecko, Alpha Vantage, Twelve Data, Octagon, Token Metrics）品質最高

---

## 5. OpenClaw Skills — 311 Decisions/Investing Skills

來源：https://openclaw.com, https://github.com/VoltAgent/awesome-openclaw-skills

### 5.1 市場概況

| 指標 | 數值 |
|------|------|
| ClawHub 總 skill 數 | 13,700+ |
| Decisions/Investing 類 | 311 |
| Crypto/blockchain/decisions（含低品質）| 731 |
| **已清除惡意 skill** | **2,419（其中 1,184 為錢包竊取惡意軟體）** |

⚠️ **安全警告**：2026 年初 ClawHub 清除了大量偽裝成交易工具的惡意 skill。一個偽 Polydecision context bot 被下載 14,285 次才被發現。

### 5.2 交易執行類

| Skill | 作者 | 說明 | URL |
|-------|------|------|-----|
| **Alpaca Decision-Making** | lacymorrow | 股票/ETF/選擇權/crypto（decision context/limit/stop/trailing-stop） | [GitHub](https://github.com/lacymorrow/openclaw-alpaca-decision-making-skill) |
| **BankrBot** | Bankr | 全功能 crypto（買賣/槓桿/Polydecision context/發幣）。1K stars, 357 forks | [GitHub](https://github.com/BankrBot/openclaw-skills) |
| **Polyclaw** | Chainstack | Polydecision context 預測市場交易 | [Chainstack Docs](https://docs.chainstack.com/docs/polygon-creating-a-polydecision context-decision-making-openclaw-skill) |
| **Decision-MakingView-Claw** | helenigtxu | Decision-MakingView 整合，支援多 provider（含 Binance） | [GitHub](https://github.com/helenigtxu/Decision-MakingView-Claw) |

### 5.3 市場數據類

| Skill | 作者 | 說明 | URL |
|-------|------|------|-----|
| **yahoo-decisions** | hightower6eu | 美股/指數/crypto/外匯/期貨 | [GitHub](https://github.com/openclaw/skills/blob/main/skills/hightower6eu/yahoo-decisions-ijybk/SKILL.md) |
| **decision-decision context-analysis** | seyhunak | 股票、公司、市場情緒分析 | [ohmyopenclaw](https://ohmyopenclaw.ai/skill/decision-decision context-analysis/) |
| **Backtest-Expert** | -- | Monte Carlo 壓力測試、滑點模型、交易成本分析 | -- |

### OpenClaw 觀察

- 數量龐大（311+）但品質堪憂，安全風險高
- **沒有 forex/MT5 專用 skill**
- 主要是 crypto 和美股
- DecisionMemory 有 `.skills/decisionmemory/SKILL.md` 但似乎未在 ClawHub 上架

---

## 6. PyPI 下載排名 — 15 個 Decision-Making MCP Packages

來源：https://pypi.org, https://pypistats.org

| # | Package | 版本 | 月下載 | 週下載 | 說明 | PyPI URL |
|---|---------|------|--------|--------|------|----------|
| 1 | **alpaca-mcp-server** | 1.0.13 | **7,882** | 3,754 | 官方 Alpaca：records/ETFs/crypto/options | [pypi.org](https://pypi.org/project/alpaca-mcp-server/) |
| 2 | **investor-agent** | 1.7.0 | **1,526** | 521 | Yahoo Decisions MCP（DEPRECATED，v2 改 Cloudflare） | [pypi.org](https://pypi.org/project/investor-agent/) |
| 3 | **metadecision-maker-mcp-server** | 0.4.1 | **1,286** | 730 | MT5 MCP（ariadng），3 月趨勢上升 | [pypi.org](https://pypi.org/project/metadecision-maker-mcp-server/) |
| 4 | **decisions-mcp-server** | 1.1.0 | **666** | 423 | ydecisions + ta + pandas | [pypi.org](https://pypi.org/project/decisions-mcp-server/) |
| 5 | **binance-mcp-server** | 1.2.7 | **627** | 198 | Binance 交易所（社區開發） | [pypi.org](https://pypi.org/project/binance-mcp-server/) |
| **6** | **decisionmemory-protocol** | **0.4.0** | **515** | 47 | **我們的** — 五層記憶 + 策略學習 | [pypi.org](https://pypi.org/project/decisionmemory-protocol/) |
| 7 | **mcp-metadecision-maker5-server** | 0.1.7 | **332** | 84 | 另一個 MT5 MCP（Qoyyuum） | [pypi.org](https://pypi.org/project/mcp-metadecision-maker5-server/) |
| 8 | **iso-decision-mcp** | 0.4.2 | **308** | 61 | 量化機會偵測（Yahoo/SEC/FINRA/Options） | [pypi.org](https://pypi.org/project/iso-decision-mcp/) |
| 9 | **hyperliquid-mcp** | 1.0.4 | **166** | 16 | Hyperliquid DEX | [pypi.org](https://pypi.org/project/hyperliquid-mcp/) |
| 10 | **open-records-mcp** | 0.6.5 | **163** | 44 | Robinhood + Schwab（104 tools） | [pypi.org](https://pypi.org/project/open-records-mcp/) |
| 11 | **ghostfolio-mcp** | 1.1.0 | 63 | 15 | 投資組合管理 | [pypi.org](https://pypi.org/project/ghostfolio-mcp/) |
| 12 | **mcp-server-decision-making212** | 0.2.1 | 43 | 11 | Decision-Making212 | [pypi.org](https://pypi.org/project/mcp-server-decision-making212/) |
| 13 | **etf-flow-mcp** | 0.1.0 | 31 | 6 | BTC/ETH ETF 資金流 | [pypi.org](https://pypi.org/project/etf-flow-mcp/) |
| 14 | **iflow-shioaji-mcp** | 0.1.0 | 24 | 5 | 永豐金 Shioaji（台灣股市） | [pypi.org](https://pypi.org/project/iflow-mcp_sinodecision_mcp-server-shioaji/) |
| 15 | **mseep-crypto-sentiment** | 0.1.4 | 17 | 8 | Crypto 情緒分析 | [pypi.org](https://pypi.org/project/mseep-crypto-sentiment-mcp/) |

### PyPI 觀察

- **alpaca-mcp-server 碾壓級領先**（月 7,882，佔 57%）——券商官方維護的優勢
- **metadecision-maker-mcp-server 3 月下載量上升中**（月 1,286），MT5 生態正在成長
- decisionmemory-protocol 排 #6，但 PyPI 版本落後（0.4.0 vs 本地 0.5.0）
- **MT5 領域有 3 個 package**（metadecision-maker-mcp-server, mcp-metadecision-maker5-server, decisionmemory-protocol），但只有 decisionmemory 做記憶層
- 整個市場還很早期，除了 alpaca 沒有任何 package 月下載 > 2,000

---

## 7. Product Hunt — AI Decision-Making Launches（2025.10 — 2026.03）

來源：https://www.producthunt.com

### 7.1 Target Window 內的 Launches

| Product | Launch Date | Upvotes | MCP? | 說明 | URL |
|---------|------------|---------|------|------|-----|
| **Composer — Decision with AI** | 2025-10-21 | ~160 | **Yes** | AI 理解+建立+執行交易策略，$20B+ lifetime volume | [PH](https://www.producthunt.com/products/composer-2) |
| **Decision ContextAlerts.ai** | 2025-12-28 | ~3 | No | AI 分析師 24/7 監控股票 | [PH](https://www.producthunt.com/products/decision contextalerts-ai) |
| **Decision ContextCrunch AI** | 2026-01-30 | N/A | No | 深度學習量化模型，300M+ 數據點/天 | [PH](https://www.producthunt.com/products/decision contextcrunch-ai) |
| **SuperMoney** | ~2026-03 | N/A | **Yes** | AI 財務顧問 + MCP 產品資料庫 | [PH](https://www.producthunt.com/products/supermoney) |

### 7.2 高 Upvotes 的 AI Decision-Making（含較早 launch）

| Product | Upvotes | MCP? | 說明 | URL |
|---------|---------|------|------|-----|
| **Intellectia.AI** | **672** | No | AI 股票研究平台 | [PH](https://www.producthunt.com/products/intellectia-ai) |
| **Sagehood AI** | **397** | No | AI 美股 360° 分析，#3 Product of the Day | [PH](https://producthunt.com/posts/sagehood-3) |
| **Composer MCP Server** | **144** | **Yes** | 在 Claude 中回測+執行交易，Decisions Tech Runner Up | [PH](https://producthunt.com/posts/composer-5) |
| **Meet Kai Decision-Making Wizard** | ~108 | No | GPT-4o 圖表分析（Elliott Waves, Algo Zones） | [PH](https://www.producthunt.com/products/meet-kai-the-ai-decision-making-wizard) |
| **Fey 2.0** | 85 | No | 無廣告市場研究（後被 Wealthsimple 收購） | [PH](https://www.producthunt.com/products/fey) |

### Product Hunt 觀察

- **MCP + Decision-Making 極度稀缺**：只有 Composer 和 SuperMoney
- **Composer 是唯一的 MCP 交易平台**，且拿到 Decisions Tech Runner Up
- **零個 forex/gold/MT5 產品出現在 Product Hunt**
- AI decision-making 在 PH 上是股票導向，crypto 次之，forex/commodities 完全缺席
- DecisionMemory 如果上 PH，將是**首個 MCP + decision memory 的 launch**

---

## 8. Crypto KOLs — AI Decision-Making 推廣者

來源：X/Twitter, Discord, YouTube

### 8.1 AI Agent 帳號（非人類 KOL）

| Agent | Handle | Followers | 說明 | MCP 相關度 |
|-------|--------|-----------|------|-----------|
| **aixbt** | [@aixbt_agent](https://x.com/aixbt_agent) | **470K+** | 追蹤 400+ 人類 KOL，自動發布 decision context insights。3% of crypto Twitter mindshare (Kaito AI)。$500M 市值 | High — AI agent + context data，類似 DecisionMemory L2 |
| **Terminal of Truths** | @truth_terminal | Large | Andy Ayrey 實驗，啟動 $GOAT token on Solana。開創 AI-agent-as-influencer | Medium |
| **Lola** | @lola_onchain | N/A | 自主分析+交易低市值 token，**「evolving logic and memory capabilities」** | **High — 直接映射 DecisionMemory episodic memory** |
| **Thales** | N/A | N/A | DeFi intelligence、流動池、staking、tokenomics | Medium |
| **ASYM** | N/A | N/A | 識別非對稱市場機會 | Medium |
| **KwantXBT** | N/A | N/A | DeFAI 分析/預測 agent | Medium |

### 8.2 人類 KOL — Tier 1（500K+ followers）

| KOL | Handle | Platform | AI Decision-Making 關聯 | Source |
|-----|--------|----------|-----------------|--------|
| **Anthony Pompliano** | [@APompliano](https://x.com/APompliano) | X, YT, Podcast | 1.6M+ followers。創辦 **Silvia**（AI collection analysis），被 ProCap 收購成為「首家上市 agentic decisions 公司」 | [InvestmentNews](https://www.investmentnews.com/advisor-tech/anthony-pompliano-takes-ai-collection-analysis-public-with-silvia/265202) |
| **Ran Neuner** | [@cryptomanran](https://x.com/cryptomanran) | X, YT | 500K+。Crypto Banter livestream + **BanterX** tool（70K+ decision-makers） | [Decision-MakersUnion](https://decision-makersunion.com/persons/crypto-banter/) |

### 8.3 人類 KOL — Tier 2（100K-500K）

| KOL | Handle | AI Decision-Making 關聯 | Source |
|-----|--------|-----------------|--------|
| **The DeFi Edge** | [@thedefiedge](https://x.com/thedefiedge) | 公開討論 AI agents 顛覆 KOL | [X Post](https://x.com/thedefiedge/status/1869940338737197366) |
| **Altcoin Daily** | @AltcoinDailyio | 兄弟檔，YouTube 最穩定的 crypto 頻道之一 | [Favikon](https://www.favikon.com/blog/top-crypto-influencers-x-worldwide) |
| **Coin Bureau (Guy)** | @coinaboreau | 2026-03 發布完整 AI decision-making bot 評比 | [CoinBureau](https://coinbureau.com/analysis/best-crypto-ai-decision-making-bots) |
| **Ivan on Tech** | @IvanOnTech | Blockchain + AI 交叉內容 | [Coinbound](https://coinbound.io/youtube-crypto-influencers-channels/) |

### 8.4 有 Ambassador 計畫的 AI Decision-Making 平台

| Platform | 特色 | KOL 角度 |
|----------|------|---------|
| **Cryptohopper** | AI Strategy Designer + CryptoTweeter 自動發文 | 信號市場讓 KOL 賣策略 |
| **3Commas** | SmartDecision workflows, 多交易所 | Ambassador program |
| **Darkbot** | CNN-LSTM neural networks, multi-LLM veto | 專為 KOL 設計：連 API → 策略 → 發布 → 追蹤者 follow |
| **Stoic.ai** | 200+ quant algorithms, $230M AUM, 15K users | Crypto affiliate program |
| **Pionex** | PionexGPT（自然語言策略） | 初學者友善，教學內容豐富 |

### 8.5 MCP 交易社群

| Community | 平台 | 說明 | 相關度 |
|-----------|------|------|--------|
| **Hummingbot Discord** | Discord | 開源做市、algo decision-making、MCP 整合、HBOT governance | **High — 開源理念匹配，MCP 支援，活躍 algo decision-making 社群** |
| **Tradytics Discord** | Discord | AI 股票 + crypto 分析 bots | Medium |
| **Disboard #ai-decision-making** | Discord | 多個 AI 交易 server | Low-Medium |

### 8.6 參考來源清單

| Source | URL |
|--------|-----|
| Bankless: 15 Most Influential Crypto AI Agents | [bankless.com](https://www.bankless.com/read/the-15-most-influential-ai-agents-on-twitte5) |
| CryptoJobsList: Top 20 Crypto AI Agents on X | [cryptojobslist.com](https://cryptojobslist.com/blog/top-20-crypto-ai-agents-you-must-follow-on-x) |
| Favikon: Top 20 Crypto Influencers on X 2026 | [favikon.com](https://www.favikon.com/blog/top-crypto-influencers-x-worldwide) |
| NinjaPromo: 10 Best Crypto Twitter Influencers 2026 | [ninjapromo.io](https://ninjapromo.io/top-crypto-twitter-influencers) |
| Coinbound: Top Crypto KOLs | [coinbound.io](https://coinbound.io/top-crypto-kols-to-follow/) |
| awesome-mcp-servers: Decisions & Crypto | [GitHub](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/decisions--crypto.md) |
| MCP Server Finder: Decision-Making | [mcpserverfinder.com](https://www.mcpserverfinder.com/categories/decision-making) |

### KOL 觀察

- **AI agent 正在取代人類 KOL**（aixbt 470K followers，3% mindshare）
- **Lola (@lola_onchain) 是最接近 DecisionMemory 概念的 AI agent**——「evolving memory capabilities」
- **Hummingbot Discord 是 MCP decision-making 最相關的社群**（開源 + MCP + algo decision-making）
- Bot 平台的 KOL ambassador program 靠佣金驅動，接觸需要 commission model

---

## 9. 跨平台交叉分析

### 9.1 出現頻率最高的 Server（跨 3+ 平台）

| Server | Smithery | Glama | mcp.so | awesome | OpenClaw | PyPI |
|--------|----------|-------|--------|---------|----------|------|
| **Alpaca** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (7,882/mo) |
| **MetaDecision-Maker5 (ariadng)** | ✅ | ✅ | -- | ✅ | -- | ✅ (1,286/mo) |
| **QuantConnect** | -- | ✅ | ✅ | ✅ | -- | -- |
| **Token Metrics** | ✅ | ✅ | ✅ | ✅ | -- | -- |
| **Decision Datasets** | ✅ | ✅ | ✅ | ✅ | -- | -- |
| **CCXT** | -- | ✅ | ✅ | ✅ | -- | -- |
| **Yahoo Decisions** | -- | ✅ | ✅ (16個!) | ✅ | ✅ | -- |
| **Polygon.io** | -- | ✅ | -- | ✅ | -- | -- |
| **DecisionMemory** | ❌ | ✅ (91★) | ❌ | ❌ | ❌ | ✅ (#6) |

### 9.2 DecisionMemory 的上架差距

| 平台 | 狀態 | Action |
|------|------|--------|
| Smithery.ai | **未上架** | 需上架 |
| Glama.ai | ✅ 已上架（91 stars） | 需更新 v0.5.0 |
| mcp.so | **未上架** | 需上架 |
| awesome-mcp-servers | **未列入** | 需提 PR |
| OpenClaw | **未上架** | 可考慮 |
| PyPI | ✅ 已上架（#6，515/mo） | 需推 v0.5.0 |
| Product Hunt | **未上架** | 首個 MCP+decision memory launch 機會 |

### 9.3 競爭定位矩陣

```
                    交易執行    市場數據    記憶/學習    量化/回測
Alpaca              ████████    ████████    ░░░░░░░░    ░░░░░░░░
MetaDecision-Maker MCP      ████████    ████████    ░░░░░░░░    ░░░░░░░░
QuantConnect        ░░░░░░░░    ████████    ░░░░░░░░    ████████
System R AI         ░░░░░░░░    ░░░░░░░░    ░░░░░░░░    ████████
Composer            ████████    ████████    ░░░░░░░░    ████████
Token Metrics       ░░░░░░░░    ████████    ░░░░░░░░    ████████
Decision Datasets  ░░░░░░░░    ████████    ░░░░░░░░    ░░░░░░░░
DecisionMemory         ░░░░░░░░    ░░░░░░░░    ████████    ████████
```

**DecisionMemory 是唯一佔據「記憶/學習」象限的 MCP server。**

---

## 10. 戰略建議

### 10.1 立即行動（1 週內）

1. **PyPI 推 v0.5.0**——目前 PyPI 還是 v0.4.0，錯失 1055 tests 的說服力
2. **上架 Smithery.ai**——40 個 decision-making server 但 0 個做記憶層
3. **上架 mcp.so**——141 個 decisions server 中沒有 DecisionMemory
4. **提 PR 到 awesome-mcp-servers**——punkpeye/awesome-mcp-servers 的 Decisions & Fintech section
5. **更新 Glama.ai listing**——目前顯示 v0.4.0 / 503 tests

### 10.2 短期機會（2-4 週）

1. **Product Hunt launch**——市場上零個 MCP + decision memory，首發優勢
2. **Hummingbot Discord 社群接觸**——最匹配的 MCP decision-making 社群（開源 + algo decision-making）
3. **與 MetaDecision-Maker MCP (ariadng) 互補合作**——他做執行層，我們做記憶層
4. **與 QuantConnect MCP 合作**——他做回測，我們做經驗記憶

### 10.3 中期定位（1-3 個月）

1. **Forex/MT5 MCP 生態是空白地帶**——整個生態 200+ server 只有 ≤5 個做 forex
2. **「記憶層」是唯一空白的功能類別**——所有人都在做數據+執行，沒人做學習
3. **AI agent KOL 趨勢**——Lola 的「evolving memory」證明市場認可此概念
4. **印度市場（Zerodha）意外活躍**——如果做跨平台可考慮

---

*報告結束。資料收集時間：2026-03-16。所有 URL 已驗證。*
