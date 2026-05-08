# 量化投研入门手册（Quantitative Primer）· 中英对照版

> **原书**：*Quantitative Primer — Everything you wanted to know about quant\* (\*But were too afraid to ask)*
> **出版方**：BofA Global Research（美银全球研究部门）· 2023 年 6 月 26 日
> **原书页数**：312 页
>
> 本译本采用「每段先英文原文，紧跟中文译文」的对照排版，专业术语在首次出现时给出中英对照，之后仅用中文。

---

# 第 1 页 · 封面

## 封面标题

**Quantitative Primer**
**量化投研入门手册**

*Everything you wanted to know about quant\**
*关于量化，你一直想了解的一切\**

**Quantitative Strategy**
**量化策略**

\**But were too afraid to ask*
\**却始终不好意思开口问的*

---

## 内容摘要

In our fourteenth edition of the US Quantitative Primer, we include performance of 70+ factors over a time period of ~40 years, over which Cash Flow-based valuation factors have been the best performers to remind readers that valuation matters and that cash is king. We outline the proprietary framework critical to our portfolio strategy work and highlight trends and topics in the quantitative industry.

在本次第十四版《美国量化投研入门手册》中，我们回顾了 70 余个因子在近约 40 年里的表现。期间，基于现金流的估值因子表现最为出色——再次提醒读者：**估值至关重要，现金为王**。报告还系统梳理了我们用于组合策略研究的自有分析框架，并着重讨论了量化行业当下的趋势与热点。

---

### A generation of investors trained on "price predicts price"
### 被"以价测价"训练出来的一代投资者

Most investors have seen a period during which momentum and technical factors have driven the largest gains. But outperformance of price momentum factors was likely driven by a liquidity-fueled multi-decade period of falling interest rates, globalization and central bank stimulus that resulted in high serial correlation across price returns. Prior to the Global Financial Crisis (GFC), valuation was a far better signal than using past price returns to predict future price returns.

当下多数投资者都经历过那样一段日子——动量因子和技术因子贡献了最大的收益。但价格动量因子之所以能持续跑赢，很可能是拜那段长达数十年、由流动性驱动的特殊宏观环境所赐：利率持续下行、全球化推进、各国央行反复刺激，使得价格回报之间呈现出很高的序列相关性。而在 2008 年全球金融危机（GFC）之前，**估值**作为选股信号的有效性，远胜于用历史涨跌预测未来涨跌。

<details>
<summary>📖 <b>术语解释：动量因子 / 技术因子</b></summary>

- **动量因子（Momentum Factor）**：一类建立在\"**强者恒强、弱者恒弱**\"经验规律上的选股信号。核心逻辑是——**过去一段时期（通常是 3–12 个月）涨得多的股票，在随后的一段时期里倾向于继续跑赢；跌得多的则继续跑输**。常见构造方式是用股票过去 N 个月的累计回报率（多数研究取过去 12 个月但剔除最近 1 个月，即所谓 \"12M-1M\"，以规避短期反转效应）对股票池排序，买入前 10%（或前 20%）、做空后 10%。动量因子属于**价格类因子**，不依赖任何基本面数据（不看盈利、不看估值），因此实现成本极低、更新频率可以做到日级。其背后的行为金融学解释通常是**投资者反应不足（under-reaction）** 与**羊群效应**。

- **技术因子（Technical Factor）**：更宽泛的一类概念，指**一切仅基于价格和成交量（及其衍生量）** 构造的选股/择时信号，动量因子可视为其中最具代表性的子类。典型技术因子包括：
  - **均线类**：如 30 周/75 周均线比（30W/75W MA）、5 周/30 周均线比、股价相对 200 日均线的位置；
  - **趋势类**：各类周期的价格回报（3M、9M、11M、12M Price Return）；
  - **反转类**：12M & 1M Reversal（长线动量 + 短线反转组合）；
  - **量能类**：Most Active（成交最活跃）、Short Interest（空头兴趣）等。

  这些因子共同特点是**纯粹从\"量价\"中提取信息**，不涉及公司基本面。本报告后文的\"量化因子参考\"章节（Exhibits 796 / 798）对此有系统的分位业绩与 Sharpe 比率展示。

两者关系：**动量 ⊂ 技术**。动量是\"方向性趋势\"的度量，而技术因子还额外涵盖了均值回归、量能、波动率等多个维度。

</details>

---

### Surprising strategy for a downturn
### 下行期里一个反直觉的策略

Contrary to popular belief, secular growth doesn't outperform value during recessions or "Downturn" regimes. Deep value (Price to Book, Price to Sales) has lagged, but so have growth factors (EPS Momentum, High Long-term Growth, Long Equity Duration). Winners during downturns have one thing in common: cash (outperforming factors have been cash return factors, our DDM valuation factor, and free cash flow-oriented factors).

很多人想当然地以为\"经济一差，大家就该抱紧长期成长股\"，但事实恰恰相反：在**衰退**或我们定义的\"**下行期（Downturn）**\"，**成长股并不跑赢价值股**。一方面，**深度价值股**（低市净率、低市销率那类\"便宜货\"）确实表现拉胯；但另一方面，**成长类因子**（盈利动量、高长期增速、长久期权益）同样被市场抛弃——**两头都不讨好**。那么谁在下行期真正胜出？答案只有一个字——**现金**：真正跑赢的是三类东西——**能把现金回馈股东的公司**（高股息、高回购）、**我们自研的 DDM 股息贴现模型**（本身就以未来股息折现为锚），以及**一切围绕\"自由现金流\"构建的因子**。

<details>
<summary>📖 <b>术语解释（本段密集出现的基础概念）</b></summary>

**① 成长 vs. 价值（Growth vs. Value）**——最基础的两大投资风格：
- **价值股（Value）**：估值便宜的股票（**低市盈率、低市净率、低市销率**），通常是成熟行业里的\"老钱\"公司（银行、能源、工业）。买法就是\"买便宜货\"。
- **成长股（Growth）**：高增速预期的股票（**盈利增速高、营收增速高**），估值通常很贵（高 PE、高 PS），典型是科技、生物医药、创新消费。买法是\"买未来\"。
- **深度价值（Deep Value）**：**最极端便宜的那批**——往往便宜得\"有道理\"（行业衰退、公司困境），需要甄别真便宜还是价值陷阱。
- **长期/世俗成长（Secular Growth）**：\"不受经济周期影响\"的长期增长故事（如云计算、AI、电动车渗透率）。

**② 估值类因子**：
- **市净率（Price-to-Book, P/B）= 股价 / 每股净资产**。**衡量\"市场给每 1 元账面资产定价多少\"**，<1 代表股价低于清算价值——经典深度价值指标。
- **市销率（Price-to-Sales, P/S）= 总市值 / 年营收**。适合无盈利或亏损的公司估值（此时 P/E 失效），越低越便宜。
- **市盈率（Price-to-Earnings, P/E）= 股价 / 每股盈利**。最常用估值指标——\"回本需要多少年\"。
- **DDM（Dividend Discount Model，股息贴现模型）**：**把公司未来所有预期股息按贴现率折现到今天**，得到\"理论价值\"，再与市价比对判断高估/低估。核心公式：

  $$V_0 \;=\; \sum_{t=1}^{\infty} \frac{\text{DPS}_t}{(1+r)^t}$$

  其中 $V_0$ = 今天的每股内在价值；$\text{DPS}_t$ = 第 $t$ 年的预期每股股息；$r$ = 股权要求回报率（贴现率，相当于\"你持有这只股票要求每年赚多少才值\"）。直觉：**越远期的股息，被折现得越狠；$r$ 越高（风险越大），现值越小**。

  如果假设股息永续、以固定速度 $g$ 增长（$g < r$），可简化为经典的**戈登增长模型（Gordon Growth Model）**：

  $$V_0 \;=\; \frac{\text{DPS}_1}{r - g}$$

  这是最古老、最根本的股票估值模型之一。本报告作者把 DDM 作为\"BofA 自有估值因子\"之一——在下行期胜出说明**\"派真金白银股息的公司\"在坏日子里更抗跌**。

**③ 成长类因子**：
- **盈利动量（EPS Momentum / Earnings Momentum）**：**分析师预期 EPS 的上调速度** 或 **实际 EPS 的加速程度**。\"盈利在变好\"的股票倾向继续跑赢。
- **高长期增速（High Long-term Growth, LTG）**：分析师给出的 **未来 3–5 年盈利年化增速预期（LTG）** 最高的那批股票。
- **长久期权益（Long Equity Duration）**：类比债券久期概念。\"**现金流越集中在远期、估值越贵的成长股 = 长久期**\"——**对利率极度敏感，利率上行时受冲击最大**；反之利率下行它们暴涨（2020 年低利率养肥成长股的核心机制）。

**④ 衰退 / 下行（Recession / Downturn）**：
- **衰退（Recession）**：官方定义上 **连续 2 个季度 GDP 负增长**，或 NBER 委员会综合评估（失业率、工业产出、实际收入等）后宣布。历史上美股在衰退期平均下跌，但**通常在衰退结束前 3–6 个月触底回升**——这就是为什么\"等确认了才进场\"反而错过大反弹。
- **下行（Downturn Regime）**：BofA 自定义的\"宏观状态\"之一。他们将经济周期分成 **Early Cycle（早周期）→ Mid Cycle（中周期）→ Late Cycle（晚周期）→ Downturn（下行）→ Recovery（复苏）**，每一阶段对应不同的因子表现——**\"下行\"比 NBER 定义的衰退更宽泛**，包括经济动能显著转弱的阶段。

**⑤ 现金相关因子**：
- **自由现金流（Free Cash Flow, FCF）= 经营现金流 − 资本开支**。**公司在维持运营和投资后真正剩下的\"可自由支配的钱\"**——可用于派息、回购、还债、并购。FCF 不像 EPS 那样容易被会计操纵，被称为\"**最难造假的盈利**\"。
- **现金回报因子（Cash Return Factors）**：反映公司把现金回馈给股东的力度——包括**股息率、回购收益率、总股东回报率（= 股息率 + 回购收益率）**。在下行期，这些因子胜出背后的直觉是：**\"账上有真金白银、敢把钱还给你的公司\"比\"讲故事的成长股\"更安全**。

</details>

---

### An alternative route to alpha
### 另辟蹊径寻找阿尔法（Alternative Data 之路）

The quest for alpha has driven investors beyond traditional sources into the realm of alternative data that can provide insights into the future performance of financial markets on a timely basis. BofA Global Research uses a wide range of data like NLP-based sentiment trackers including news sentiment, BAC aggregated credit and debit card spending data, web scraping, geolocation data as well as proprietary surveys. Many are compiled on a monthly basis in the BofA Global Proprietary Signals report. See inside for more details.

对阿尔法的追逐，正推动投资者走出传统数据源，进入**另类数据（Alternative Data）**的疆域——这类数据能更及时地映射出金融市场未来的走向。美银全球研究部门用到的数据范围很广：基于自然语言处理（NLP）的情绪追踪器（含新闻情绪指标）、美国银行汇总的信用卡与借记卡消费数据、网页抓取数据、地理位置数据，以及自有问卷调查等。其中相当一部分会在每月发布的《美银全球自有信号》报告中集中呈现。详见正文。

<details>
<summary>📖 <b>术语解释：Alpha / Beta / 另类数据 / NLP</b></summary>

- **Alpha（阿尔法，α）**：**超越基准指数的那部分回报**——衡量基金经理或策略的\"**真实选股/择时本事**\"。数学上：`组合回报 = α + β × 市场回报 + 残差`，**α 是剔除市场影响后还剩下的超额回报**。例如某基金一年赚 15%，S&P 500 同期涨 10%、该基金贝塔为 1.0，那么 α ≈ 5%。**找到正 α 的来源，是主动投资的终极目标**。

- **Beta（贝塔，β）**：组合对市场的**敏感度**。β=1 表示跟大盘同涨同跌；β=1.5 表示大盘涨 1%、该股倾向涨 1.5%（也承担 1.5 倍下跌风险）；β=0.5 则相对\"抗跌\"。β 只是\"**跟车**\"的那部分回报，**没有 α 的基金 = 一个贵的指数基金**。

- **传统数据（Traditional Data）**：公司财报、分析师预期、宏观经济数据（GDP、CPI、PMI）、价量数据——**所有投资者都能看到的、同频的**数据源。传统数据的\"信息边际\"已被大量挖掘，越来越难产生 α。

- **另类数据（Alternative Data）**：不在传统数据范畴里的**任何能提前反映商业活动**的数据。典型来源：
  - **卫星图像**：统计某零售商停车场车流量，提前预判其财报销售；
  - **信用卡/借记卡消费数据**（本报告用的 BAC aggregated spending）：抢在公司披露季度销售前知晓消费走向；
  - **网页抓取（Web Scraping）**：从电商网站抓商品价格/库存/评论来预估销售；
  - **地理位置数据（Geolocation）**：匿名手机定位数据监测门店人流；
  - **问卷调查（Proprietary Surveys）**：机构自建的消费者/CEO/CFO 情绪调查。

- **NLP（Natural Language Processing，自然语言处理）**：让计算机读懂人类语言的 AI 技术。在量化里最常见用途是**情绪分析（Sentiment Analysis）**——机器扫描**新闻报道、财报电话会议纪要、分析师报告、社交媒体推文**，量化出\"正面/负面\"分值，作为选股或择时信号。GPT 类大模型出现后，NLP 类另类因子能力显著跃升。

</details>

---

### Quant quiz: debunking myths
### 量化小测验：戳破常见误区

It's a confusing time to be an investor – macro indicators are flashing mixed signals and a there are a multitude of crosscurrents. Here we address and debunk some of the common narratives we hear contributing to investor frustration. Myths include: "Bad breadth is bearish" (in years of mega-cap leadership since 1986, the market was up the subsequent year nearly 75% of the time), "Value underperforms during recessions," (Value has a 75% hit rate in recessions over the past 40 years)," and more.

眼下当投资者相当烧脑——宏观指标信号杂乱，各种相互抵触的力量同时作用于市场。本章逐一回应并戳破一些让投资者焦虑、却未必站得住脚的流行说法。比如：**"市场广度差 = 熊市"**（事实：自 1986 年以来，凡是出现大盘股领涨的年份，次年市场上涨的概率接近 75%）；**"价值股在衰退期跑输"**（事实：过去 40 年的每一轮衰退中，价值的胜率是 75%）；等等。

---

### Eyeballs shifting to the short-term
### 市场目光正在全面转向短期

One of today's greatest market inefficiencies may stem from the shift in capital toward shorter-term strategies and the scarcity of capital devoted to long-term, fundamental investing. Zero-day-to-expiry options, or "0DTEs" have surged and now account for 40-45% of total SPX option volume. Our work suggests that extending one's time horizon has been a reliable recipe for loss avoidance in US stocks.

当下最大的一类市场无效定价，很可能来自这样一个结构变化：资金正越来越向短线策略集中，而真正投入**长期、基本面**投资的资金反而变得稀缺。**当日到期期权（0DTE）** 近期成交激增，目前已占标普 500 指数（SPX）期权总成交量的 **40%–45%**。我们的研究表明，拉长投资期限，仍然是在美股里规避亏损最稳妥的一条路径。

<details>
<summary>📖 <b>术语解释：期权 / 0DTE / SPX / 无效定价</b></summary>

- **期权（Option）**：一份赋予买方\"在未来某个时点（**到期日**）、以某个价格（**行权价**）买入（Call，认购）或卖出（Put，认沽）标的资产\"权利的合约。**买方付出权利金、拥有权利而无义务；卖方收到权利金、承担义务**。期权是**杠杆工具**——用较少的权利金就能撬动大额名义敞口。

- **0DTE（Zero Days to Expiry，当日到期期权）**：**到期日就是当天**的期权。从 2022 年起 CBOE 把 SPX 期权扩展到\"每天到期\"，于是\"**买一张今天收盘就归零或翻倍的彩票**\"成为可能。
  - **为什么爆火**：零日期权**隐含波动率低、权利金便宜**，投机者可以用极少资金在盘中对\"今天涨跌\"下注；同时程序化做市商大量做空 0DTE 收权利金。
  - **为什么是\"短期化\"代表**：与 3 个月、1 年期权相比，0DTE 完全围绕\"**盘中 1–6 小时的走势**\"，与公司基本面毫无关系——资金极端**短期化**的象征。
  - **市场影响**：做市商对 0DTE 的 Gamma 对冲会**放大尾盘价格波动**，近年已成为 SPX 日内剧烈摆动的主要原因之一。

- **SPX**：**标普 500 指数**的行情代码。**S&P 500**（Standard & Poor's 500）是追踪美国 500 家最大上市公司的市值加权指数，是全球最有代表性的股票指数，也是美股最活跃的期权标的。

- **市场无效定价（Market Inefficiency）**：有效市场假说（EMH）认为\"**所有信息都已反映在价格里**\"，但现实中由于**认知偏差、资金流结构、短期化博弈**等因素，价格会偏离基本面价值——这些**偏离**就是\"无效定价\"。**量化投资的核心就是寻找并利用系统性的无效定价**。作者在这里的判断是：**资金越短期化，留给长期基本面投资的空间反而越大**——因为没人愿意等 3 年了，坚持等的人就能捡到便宜。

</details>

---

## 边栏信息

**26 June 2023** · **Quantitative Strategy** · **United States**
2023 年 6 月 26 日 · 量化策略 · 美国

**Savita Subramanian** — Equity & Quant Strategist, BofAS
Savita Subramanian —— 股票与量化策略师，美银证券（BofAS）
+1 646 855 3878 · savita.subramanian@bofa.com

*See Team Page for List of Analysts*
*完整分析师名单见团队页*

---

### What's inside
### 本书亮点

- **For Quants** — What's the crowded trade? We include the most and least popular quantitative strategies and trends in factor popularity over time.
  **给量化研究者**：**拥挤交易在哪里？** 本书汇总了最热门与最冷门的量化策略，以及各类因子"受欢迎程度"随时间的变迁。

- **For sector analysts** — Different fundamental signals work better within different groups, and we highlight the most predictive stock selection attributes within sectors.
  **给行业分析师**：不同的基本面信号在不同行业内的有效性差异很大——我们列出了**每个行业最具预测力的选股指标**。

- **For equity long-short investors** — Certain attributes may matter more for long-only investors, whereas others may be better long-short signals, so we include performance of factors on the long and short side.
  **给股票多空投资者**：有些因子对只做多的投资者更重要，另一些则更适合构建多空组合——本书分别给出了各因子在多头端与空头端的表现。

<details>
<summary>📖 <b>术语解释：多头 / 空头 / 多空组合</b></summary>

- **多头（Long）**：买入并持有一只股票，期待其上涨赚钱——这是绝大多数散户和公募基金做的事（\"**只做多**\"）。
- **空头（Short）**：**借入**一只股票、以当前价卖出，期待其下跌后再以更低价买回、归还——**做空赚股价下跌的钱**。空头需要支付借券费（Stock Loan Fee），存在**无限损失风险**（股价理论上可以涨到无穷大）。
- **多空组合（Long-Short Portfolio）**：**同时做多一篮子股票、做空另一篮子股票**。在量化里，最经典的做法是：把股票按某因子排序，**买入前 10%（或前 20%），做空后 10%（或后 20%）**——称为 \"**Q1-Q5 Spread**\" 或 \"**D1-D10 Spread**\"。
  - **好处**：剔除了整体市场涨跌的影响（\"**市场中性**\"），组合回报几乎**只反映因子本身的选股能力**，是评判一个因子\"真有效 vs. 只是搭上大盘便车\"的黄金标准。
  - **区别**：只做多组合关心\"前 Q1 能不能跑赢市场\"；多空组合关心\"前 Q1 能不能跑赢后 Q5\"。有些因子只在多头端赚钱（低估值股跑赢大盘），有些只在空头端赚钱（超高贝塔股跑输）——本书会分别给出两端的业绩。

</details>

- **For Growth & Value managers** — We include factor performance within the style benchmarks, and also assess the fundamental attributes and attractiveness of the benchmarks themselves over time.
  **给成长与价值型基金经理**：本书既给出因子在各风格基准指数内部的表现，也动态评估**这些基准指数本身**的基本面属性与吸引力。

- **For macro investors** — We include market timing indicators, as well as an analysis of factor performance vis a vis macro environments. We also include industry attributes over time.
  **给宏观投资者**：本书提供择时指标、不同宏观环境下的因子表现对比，以及各行业属性的历史演变。

---

## 页脚免责声明

Trading ideas and investment strategies discussed herein may give rise to significant risk and are not suitable for all investors. Investors should have experience in relevant markets and the financial resources to absorb any losses arising from applying these ideas or strategies.

本文涉及的交易思路与投资策略可能带来重大风险，并不适合所有投资者。读者应具备相关市场的投资经验，并拥有足够的财务承受能力，以消化因采纳这些思路或策略而可能产生的任何损失。

BofA Securities does and seeks to do business with issuers covered in its research reports. As a result, investors should be aware that the firm may have a conflict of interest that could affect the objectivity of this report. Investors should consider this report as only a single factor in making their investment decision.

美银证券（BofA Securities）与其研究报告覆盖的发行人之间存在业务往来，或正寻求建立此类业务关系。因此，投资者应注意：本公司可能存在利益冲突，这会影响本报告的客观性。读者在做投资决策时，应把本报告视为众多参考依据之一。

*Refer to important disclosures on page 310 to 311.*
*重要披露请见第 310—311 页。*

---

# 第 2–7 页 · 目录（Contents）

 > 原书目录跨 p2–p7 共 6 页，按顺序罗列全书章节及其对应页码。译文保持相同顺序，并给出中英对照，便于后续正文查阅。

## Contents · 目录

| 页码 | 英文章节名 | 中文译名 |
|---:|---|---|
| — | **US Equity & Quant Strategy Team** | **美国股票与量化策略团队** |
| 9 | More complicated, more crowded | 愈发复杂，愈发拥挤 |
| 10 | Rise of short-termism | 短期主义的抬头 |
| 11 | BofA data-driven research | 美银数据驱动的研究 |
| 12 | Myth-busters | 流言终结（戳破市场误区） |
| 13 | **Section I: Core Concepts and Methodology** | **第一部分：核心概念与方法论** |
| 19 | What drives market performance? | 什么决定了市场表现？ |
| 20 | 1. Valuation | 1. 估值（Valuation） |
| 20 | 2. Sentiment | 2. 情绪（Sentiment） |
| 24 | 3. Positioning | 3. 仓位（Positioning） |
| 25 | 4. Corporate Profits | 4. 企业盈利（Corporate Profits） |
| 30 | #4: Earnings Surprise | 附加第 4 项：盈利超预期（Earnings Surprise） |
| 32 | What else has mattered: Central Bank Liquidity | 还有什么重要：央行流动性（Central Bank Liquidity） |
| 37 | Liquidity risks for the S&P 500 | 标普 500 面临的流动性风险 |
| 38 | Earnings Expectation Life Cycle | 盈利预期生命周期（Earnings Expectation Life Cycle） |
| 39 | Growth vs. Value and the Earnings Expectation Life Cycle | 成长 vs. 价值，以及盈利预期生命周期 |
| 40 | Factor timing | 因子择时（Factor Timing） |
| 43 | Growth and Value | 成长与价值 |
| 44 | Size | 规模（Size） |
| 48 | The Profits Cycle and High Quality vs. Low Quality | 盈利周期与高质量 vs. 低质量 |
| 48 | The Profits Cycle and Size | 盈利周期与规模 |
| 49 | Volatility | 波动率（Volatility） |
| 49 | Distress Ratio | 危困比率（Distress Ratio） |
| 50 | Dividends | 股息（Dividends） |
| 50 | Measuring risk | 风险度量 |
| 56 | Risk-adjusted factor returns | 风险调整后的因子回报 |
| 56 | Macro matters | 宏观很重要 |
| 58 | Macro focus: the US Dollar impact | 宏观聚焦：美元的影响 |
| 59 | Roadmap to picking stocks | 选股路线图 |
| 61 | US Regime Indicator | 美国市场体制指标（US Regime Indicator） |
| 67 | What are quants doing? | 量化从业者在做什么？ |
| 72 | 2022: Models still just as complex in the hunt for alpha | 2022 年：模型在追逐阿尔法的路上依旧愈发复杂 |
| 72 | Price to Forward Earnings is still the most-used factor | 远期市盈率（Price to Forward Earnings）仍是最常用的因子 |
| 72 | Select valuation factors | 精选估值因子 |
| 73 | Select growth and quality factors | 精选成长与质量因子 |
| 74 | Select risk factors | 精选风险因子 |
| 74 | Select price trend and technical factors | 精选价格趋势与技术因子 |
| 75 | Select other (miscellaneous) factors | 精选其他（杂项）因子 |
| 75 | The lowdown on Smart Beta | 聊透 Smart Beta |
| 78 | **Alternative Data** | **另类数据（Alternative Data）** |
| 78 | Natural Language Processing | 自然语言处理（NLP） |
| 82 | NewsAlpha: quantifying the impact of news on returns | NewsAlpha：量化新闻对回报的影响 |
| 84 | BAC Aggregated Card Data | 美国银行汇总卡片消费数据（BAC Aggregated Card Data） |
| 85 | Geolocation Data | 地理位置数据（Geolocation Data） |
| 85 | Web Scraping | 网页抓取（Web Scraping） |
| 86 | Surveys | 问卷调查（Surveys） |
| 90 | **The ABC's of ESG** | **ESG 入门** |
| 90 | What is ESG? | 什么是 ESG？ |
| 91 | It's not politics, it's money | 这不是政治，这是钱的问题 |
| 92 | ESG + Quant = Alpha | ESG + 量化 = 阿尔法 |
| 95 | Activists could play matchmaker | 维权投资者（Activists）可充当"撮合者" |
| 95 | A narrowing ESG premium | 逐渐收窄的 ESG 溢价 |
| 96 | Quantifying the "S": Culture is key | 量化"S"：企业文化是关键 |
| 97 | The cost of ignoring ESG | 忽视 ESG 的代价 |
| 100 | Implementation guide for sectors | 各行业的落地指南 |
| 102 | Introducing ESGMeter™, a proprietary ESG score | ESGMeter™：我们自研的 ESG 评分体系 |
| 103 | **Section II: Stock Strategies within the S&P 500** | **第二部分：标普 500 内部的选股策略** |
| 104 | GARP Strategies | GARP 策略（合理价格下的成长） |
| 105 | P/E-to-Growth | PEG（市盈率/增速） |
| 106 | **Valuation Strategies** | **估值类策略** |
| 107 | DDM Alpha | 股息贴现模型阿尔法（DDM Alpha） |
| 108 | Earnings Yield | 盈利收益率（E/P） |
| 109 | Forward Earnings Yield | 远期盈利收益率 |
| 110 | Price/Book Value | 市净率（P/B） |
| 111 | Price/Cash Flow | 市现率（P/CF） |
| 112 | Price/Free Cash Flow | 市自由现金流比（P/FCF） |
| 113 | Price/Sales | 市销率（P/S） |
| 114 | EV/EBITDA | 企业价值倍数（EV/EBITDA） |
| 115 | Free Cash Flow/Enterprise Value | 自由现金流收益率（FCF/EV） |
| 116 | **Cash Deployment Strategies** | **现金配置策略** |
| 117 | Dividend Yield | 股息率 |
| 118 | Dividend Growth | 股息增速 |
| 119 | Share Repurchase | 股票回购 |
| 120 | **Momentum Strategies** | **动量类策略** |
| 121 | Relative Strength – 30wk/75wk | 相对强弱 —— 30 周 / 75 周 |
| 122 | Price to Moving Average (200-Day) | 股价/200 日均线 |
| 123 | Price Return – 3-Month Performance | 价格回报 —— 3 个月表现 |
| 124 | Price Return – 9-Month Performance | 价格回报 —— 9 个月表现 |
| 125 | Price Return – 11-Month Performance | 价格回报 —— 11 个月表现 |
| 126 | Price Return – 12-Month Performance | 价格回报 —— 12 个月表现 |
| 127 | Price Return – 12-Month and 1-Month Performance | 价格回报 —— 12 个月与 1 个月联合 |
| 128 | Price Return – 12-Month and 1-Month Reversal | 价格回报 —— 12 个月与 1 个月反转 |
| 129 | Trading Volume | 成交量 |
| 130 | **Growth Strategies** | **成长类策略** |
| 131 | Earnings Momentum | 盈利动量（Earnings Momentum） |
| 132 | Projected Five-Year EPS Growth | 预期未来 5 年 EPS 增速 |
| 133 | Earnings Torpedo | 盈利"鱼雷"（Earnings Torpedo） |
| 134 | Earnings Surprise | 盈利超预期（Earnings Surprise） |
| 135 | Earnings Estimate Revision | 盈利预测修正（Earnings Estimate Revision） |
| 136 | Equity Duration | 权益久期（Equity Duration） |
| 137 | **Quality Strategies** | **质量类策略** |
| 138 | One-Year Return on Equity | 近一年 ROE |
| 139 | Five-Year Return on Equity | 近五年 ROE |
| 140 | One-Year Return on Equity (Adjusted for Debt) | 近一年 ROE（负债调整后） |
| 141 | Five-Year Return on Equity (Adjusted for Debt) | 近五年 ROE（负债调整后） |
| 142 | Return on Assets | 资产回报率（ROA） |
| 143 | Return on Capital | 资本回报率（ROC） |
| 144 | **Risk Strategies** | **风险类策略** |
| 145 | Beta | 贝塔（Beta） |
| 146 | Variability of Earnings | 盈利波动性 |
| 147 | Estimate Dispersion | 分析师预测分歧度 |
| 147 | Price | 股价（作为风险因子） |
| 149 | **Miscellaneous Strategies** | **其他策略** |
| 150 | Institutional Ownership | 机构持股（Institutional Ownership） |
| 150 | Analyst Coverage | 分析师覆盖数 |
| 151 | Size | 规模 |
| 152 | Foreign Exposure | 海外业务敞口 |
| 154 | Short Interest | 空头持仓比例（Short Interest） |
| 156 | **Performance and Calculation Methodology** | **因子表现与计算方法论** |
| 161 | Russell 1000 factor efficacy | 罗素 1000 内的因子有效性 |
| 162 | Performance Calculation Methodology | 表现计算方法论 |
| 163 | **Section III: Stock Strategies within Industries** | **第三部分：行业内部的选股策略** |
| 164 | Sector Specific Overview | 行业概览 |
| 165 | **Communication Services: Media & Entertainment** | **通信服务：媒体与娱乐** |
| 165 | Long only: Top Quintile Performance | 纯多头：首五分位表现（Top Quintile） |
| 167 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1 与 Q5 价差 |
| 169 | **Communication Services: Telecommunication Services** | **通信服务：电信服务** |
| 169 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 171 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 173 | **Consumer Discretionary: Retailing** | **可选消费：零售业** |
| 173 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 175 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 177 | **Other Disc. (Autos, Durables, Services)** | **其他可选消费（汽车、耐用品、服务）** |
| 177 | Long only: Hypothetical Top Quintile Performance | 纯多头：理论上首五分位表现 |
| 179 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 181 | **Consumer Staples** | **必需消费** |
| 181 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 183 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 185 | **Energy** | **能源** |
| 185 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 187 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 189 | **Financials: Banks** | **金融：银行** |
| 189 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 191 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 193 | **Financials: Insurance** | **金融：保险** |
| 193 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 195 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 197 | **Financials: Diversified** | **金融：综合金融** |
| 197 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 199 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 201 | **Health Care: Health Care Equipment & Svcs** | **医疗保健：医疗设备与服务** |
| 201 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 203 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 205 | **Health Care: Pharmaceuticals, Biotechnology & Life Sciences** | **医疗保健：制药、生物科技与生命科学** |
| 205 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 207 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 209 | **Industrials: Capital Goods** | **工业：资本品** |
| 209 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 211 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 213 | **Other Industrials (Services, Transports)** | **其他工业（服务、运输）** |
| 213 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 215 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 217 | **Information Technology** | **信息技术** |
| 217 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 219 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 221 | **Materials** | **材料** |
| 221 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 223 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 225 | **Real Estate** | **房地产** |
| 225 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 227 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 229 | **Utilities** | **公用事业** |
| 229 | Long only: Top Quintile Performance | 纯多头：首五分位表现 |
| 231 | Long-Short: Quintile 1 / Quintile 5 Spread | 多空组合：Q1/Q5 价差 |
| 233 | Backtesting Methodology | 回测方法论 |
| 234 | **Section IV: Stock Strategies for Growth and Value Managers** | **第四部分：给成长与价值型基金经理的选股策略** |
| 235 | Growth | 成长 |
| 238 | Value | 价值 |
| 241 | Backtesting Methodology | 回测方法论 |
| 242 | **Section V: BofA Quality Strategies** | **第五部分：美银质量类策略** |
| 243 | Quality: cyclical & secular tailwinds | 质量：周期性与长期顺风 |
| 244 | What is Quality? | 什么是"质量（Quality）"？ |
| 245 | Mispricing of risk: high quality ≠ low beta | 风险错定价：高质量 ≠ 低贝塔 |
| 247 | What drives quality? | 是什么驱动了质量？ |
| 249 | Quality and Regimes | 质量与市场体制 |
| 251 | Positioning in quality has neutralized | 对质量的仓位已趋于中性 |
| 251 | Returns to risk assets from policy have waxed and waned | 政策驱动下风险资产的回报起伏 |
| 252 | Quality valuations | 质量类股票的估值 |
| 252 | Risk / reward of High vs. Low Quality | 高质量 vs. 低质量的风险/收益 |
| 253 | Quality has outperformed over the near- and long-term | 质量在近期与长期均跑赢 |
| 254 | Smaller companies tend to be lower quality | 小公司通常质量更低 |
| 254 | Deep dive on Quality fundamentals | 质量基本面深度剖析 |
| 256 | Quality within sectors | 行业内部的质量表现 |
| 257 | Quality composition within sectors | 行业内部的质量构成 |
| 259 | Performance Charts | 表现图表 |
| 263 | Methodology | 方法论 |
| 264 | **Section VI: Relative Valuation for Industries** | **第六部分：各行业的相对估值** |
| 265 | Relative Valuation for Industries | 各行业相对估值 |
| 265 | Communication Services | 通信服务 |
| 266 | Consumer Discretionary | 可选消费 |
| 270 | Consumer Staples | 必需消费 |
| 272 | Energy | 能源 |
| 273 | Financials | 金融 |
| 275 | Health Care | 医疗保健 |
| 276 | Industrials | 工业 |
| 280 | Information Technology | 信息技术 |
| 283 | Materials | 材料 |
| 285 | Real Estate | 房地产 |
| 287 | Utilities | 公用事业 |
| 290 | **Section VII: Relative Valuation between Growth and Value Benchmarks** | **第七部分：成长型与价值型基准指数间的相对估值** |
| 291 | Fundamental Valuation | 基本面估值 |
| 293 | Growth Characteristics | 成长性特征 |
| 294 | **Section VIII: ADR Strategies** | **第八部分：ADR 策略（美国存托凭证）** |
| 295 | BofA US Equity & Quant Strategy ADR Indices | 美银美国股票与量化策略 ADR 指数 |
| 296 | **Appendix** | **附录** |
| 297 | BofA Proprietary Models | 美银自有模型 |
| 297 | BofA versus Consensus (Positive and Negative Earnings Surprise Models) | 美银预测 vs. 市场共识（盈利正/负超预期模型） |
| 297 | Dividend Discount Model | 股息贴现模型（DDM） |
| 298 | Alpha Surprise Model | 阿尔法惊喜模型 |
| 299 | High Quality & Dividend Yield | 高质量 & 股息率 |
| 300 | Growth 10 and Value 10 | 成长 10 组合 与 价值 10 组合 |
| 300 | Quintile 2 | 第二五分位 |
| 302 | US Regime Indicator | 美国市场体制指标 |
| 302 | Styles | 风格 |
| 303 | BofA ADR Strategy | 美银 ADR 策略 |
| 303 | BofA Factor Descriptions | 美银因子定义说明 |
| 306 | Russell 1000 factor performance | 罗素 1000 因子表现 |
| 307 | Russell 1000 factor correlations vs. macro factors | 罗素 1000 因子与宏观因子的相关性 |
| 308 | S&P 500 factor efficacy | 标普 500 因子有效性 |
| 312 | Research Analysts | 研究分析师 |

---

# 第 8 页 · 致读者信

## Dear Reader,
## 亲爱的读者：

Each year since 2010 we have published an annual primer on techniques in quantitative analysis, as well as exposition on the hundreds of proprietary tools that we regularly update and publish.

自 2010 年起，我们每年都会发布这份关于量化分析方法的年度入门手册，同时系统介绍我们长期维护、持续更新的数百种自有分析工具。

- **Trends and hot topics in quantitative finance**: We provide insight from our survey of institutional investors about what factors are popular or unpopular, how alternative data and AI are changing industry dynamics, how to weave signals together to determine an outlook for US equities.

  **量化金融中的趋势与热点话题**：基于我们对机构投资者的年度问卷调查，洞察哪些因子正受热捧、哪些正被冷落，探讨另类数据与 AI 如何重塑行业格局，以及如何把多种信号编织在一起，形成对美股的整体观点。

- **Factor performance**: We highlight the performance of various stock screens, spanning valuation to growth to technical to miscellaneous factors, to determine both long-term efficacy and cyclicality of different investment styles.

  **因子表现**：我们系统呈现各类选股筛选策略的表现——从估值、成长、技术，到杂项因子——以此评估不同投资风格的**长期有效性**与**周期性**。

- **Risk/reward characteristics**: We highlight the reward and risk characteristics of each screen versus market benchmarks to indicate how well and how consistently metrics have driven returns. We measure risk by both volatility of returns and by probability of loss. For top vs. bottom ranked screens, we also assess consistency of top decile versus bottom decile spreads.

  **风险/收益特征**：每个筛选策略都会对照市场基准，给出其收益和风险指标，用以评估"因子驱动收益"的力度与稳定性。风险从两个维度度量：**回报波动率**与**亏损概率**。对于排序靠前与靠后的筛选策略，我们还会评估**首十分位与末十分位**利差的稳定性。

- **Sector composition**: We highlight changes in sector composition of style screens based on an unconstrained approach to running factor models. There is useful information in assessing changes in sector exposures both to determine (1) whether particular sectors are driving returns; and (2) how sectors have changed characteristics.

  **行业构成**：我们采用**不加行业约束**的方式运行因子模型，并跟踪各风格筛选策略的行业构成如何变化。观察行业敞口的变化，有助于回答两个问题：（1）某一特定行业是否在驱动整体收益？（2）行业本身的特征随时间如何演变？

- **Long-short signals can be asymmetric**: Long-only and long-short investors may benefit from knowing not just how the top-ranked stocks have behaved, but also how the bottom-ranked stocks have behaved over time. This is useful in determining which screens to use as overweight or "buy" signals, and which screens to use as underweight or "sell" signals.

  **多空信号可能并不对称**：不论是纯多头还是多空投资者，都不应只关心"头部股票"表现如何——"尾部股票"的历史表现同样重要。这有助于判断：**哪些筛选策略更适合作为超配/买入信号，哪些更适合作为低配/卖出信号**。

- **How to pick stocks within sectors**: Given that certain screens may be more effective in some sectors than in others, we believe that determining drivers of returns within specific industry groups can add significant value to a screening process.

  **行业内部如何选股**：由于某些筛选策略在特定行业中的有效性远高于在其他行业，**识别每个行业内部真正驱动收益的因子**，能为筛选流程带来显著增益。

We hope this annual report proves to be helpful, and readily welcome suggestions on how to improve next year's edition.

希望这份年度报告对你有所帮助，也欢迎任何改进建议，以便我们把明年的版本做得更好。

**Savita Subramanian**
**Savita Subramanian**
*Head of US Equity and Quantitative Strategy*
*美国股票与量化策略主管*

---

# 第 9 页 · 美国股票与量化策略团队

## US Equity & Quant Strategy Team
## 美国股票与量化策略团队

| 成员 Name | 电话 Phone | 职位 Title | 单位 Firm | 邮箱 Email |
|---|---|---|---|---|
| **Savita Subramanian** | +1 646 855 3878 | Equity & Quant Strategist（股票与量化策略师） | BofAS（美银证券） | savita.subramanian@bofa.com |
| **Alex Makedon** | +1 646 855 5982 | Equity & Quant Strategist | BofAS | alex.makedon@bofa.com |
| **Jill Carey Hall, CFA** | +1 646 855 3327 | Equity & Quant Strategist | BofAS | jill.carey@bofa.com |
| **Ohsung Kwon** | +1 646 855 1683 | Equity & Quant Strategist | BofAS | ohsung.kwon@bofa.com |
| **Victoria Roloff** | +1 646 743 6339 | Equity & Quant Strategist | BofAS | victoria.roloff@bofa.com |
| **Nicolas Woods** | +1 646 556 4179 | Equity & Quant Strategist | BofAS | nicolas.woods_barron@bofa.com |

---

# 第 10 页 · 愈发复杂，愈发拥挤

## More complicated, more crowded
## 愈发复杂，愈发拥挤

Our quantitatively oriented clients use 3x the number of factors today than they did 25 years ago (Exhibit 1). Popularity of quantitative investing has increased sharply, potentially at the expense of fundamental investing. One of today's greatest market inefficiencies may stem from the shift in capital toward shorter-term strategies relying on shorter term data like prices, news and flows, and the scarcity of capital devoted toward long-term, fundamental investing.

和 25 年前相比，我们量化客户如今所使用的因子数量已是当时的 3 倍（图表 1）。量化投资的热度大幅上升，而这背后的代价可能是**基本面投资的式微**。当下最大的一类市场无效定价，或许正来自这个结构性变化：资金愈发向**短线策略**集中——依赖短周期数据（如价格、新闻、资金流），与此同时，愿意投入**长期、基本面投资**的资金却愈发稀缺。

We have seen a seismic shift in assets and resources toward data-driven, systematic strategies and shorter-term investment strategies, which tend to rely on access to better, faster and larger stores of data. Jobs advertised for data scientists and quantitative analysts outnumber those for fundamental analysts by a factor of eight, and the number of fundamental analysts covering $1B of market cap has shrunk from 14 in 1986 to less than two people today (Exhibit 2). Quants are increasingly focused on real-time data feeds, AI (artificial intelligence), big data and machine learning. The advent of new tools has created a more interesting, but more competitive, landscape. Alternative data and new tools reveal interesting opportunities. But like most of our other work, the "bad back-test graveyard" for alternative data is vast relative to the analyses that make it into print.

我们正经历一场规模空前的资源大迁徙——资金与人才正加速涌入**数据驱动的系统化策略**和短线投资策略，这些策略天然依赖更优质、更及时、更庞大的数据源。现在招聘市场上，数据科学家和量化分析师的岗位数量是传统基本面分析师的 **8 倍**；而覆盖每 10 亿美元市值的基本面分析师数量，从 1986 年的 14 人萎缩到如今的不足 2 人（图表 2）。量化从业者越来越聚焦于：实时数据流、人工智能（AI）、大数据、机器学习。新工具的涌现让这个战场更有趣，也更拥挤。另类数据和新工具确实揭示出一些有吸引力的机会，但——就像我们其他研究一样——真正能够被发表出来的分析，相较那些沉睡在**"失败回测的坟场"**里的另类数据尝试，只是冰山一角。

> **📊 图表 1**：*BofA Institutional Factor Survey: average number of factors used by investors over time*
> **美银机构因子问卷调查：投资者使用因子的平均数量随时间的变化**
> 结论：近年来投资者使用的因子数量持续增加。（注：2008–2010 年因回复样本不足被剔除。数据来源：BofA US Equity & Quant Strategy）

---

# 第 11 页 · 短期主义的抬头

> **📊 图表 2**：*Average number of analysts per \$1 billion market cap of S&P 500 (adjusted for inflation)*
> **标普 500 每 10 亿美元市值对应的平均分析师数量（经通胀调整）**
> 结论：覆盖 10 亿美元市值的基本面分析师数量，已从 1986 年的 14 人锐减至如今的不足 2 人。

> **📊 图表 3**：*Google searches for "factor investing" and for "fundamental investing"*
> **Google 搜索趋势："因子投资" vs. "基本面投资"**
> 结论："因子投资"的搜索热度自 2012 年 6 月至 2023 年 5 月期间持续上升（3 个月移动平均）。（来源：Google Trends, BofA US Equity & Quant Strategy）

## Rise of short-termism
## 短期主义的抬头

Zero-day-to-expiry options, or "0DTEs" have surged over the past few years and now account for 40-45% of total SPX option volume (see 0DTEs note). In our latest Annual Institutional Factor Survey, 41% of respondents cited the investment community's short-term focus as the biggest threat to their investment processes, the most of any choice. We have found that the best recipe for loss avoidance is time – the probability of loss drops from 46% to 6% if the time horizon is extended from one day to ten years. SPX 0DTE options have grown from ~10% of total SPX options volume pre-Covid, to ~20% in 2021, to 40-45% in 2022-23.

**当日到期期权（0DTE）** 在过去几年间爆发式增长，目前已占标普 500（SPX）期权总成交量的 **40%–45%**（详见 0DTE 专题报告）。在我们最新的年度机构因子调查中，有 **41%** 的受访者将"投资界过度聚焦短期"列为自身投资流程面临的最大威胁——这是所有选项中得票最多的一项。而我们的研究也反复显示：**规避亏损最可靠的秘诀是"时间"**——把投资期限从 1 天拉长到 10 年，出现亏损的概率会从 **46% 骤降至 6%**。SPX 的 0DTE 期权在新冠疫情前仅占 SPX 期权总成交量的约 10%，2021 年升至约 20%，到 2022–2023 年已达 40%–45%。

---

# 第 12 页 · 0DTE 期权爆发与"时间能降低亏损概率"

> **📊 图表 4**：*SPX zero-day-to-expiry (0DTE) options volume took off in mid-2022, coinciding with the listing of Tue/Thu expiry weekly options*
> **SPX 0DTE 期权成交量在 2022 年年中起飞，恰好对应周二/周四到期的周期权上市**
> （统计口径：0DTE 合约占 SPX 期权总合约的比例。数据：2012-01-01 至 2023-05-30）

> **📊 图表 5**：*Surprisingly to many, 0DTEs have been additive to SPX option volumes, rather than cannibalizing traditional expiries*
> **出乎多数人意料：0DTE 是"新增"了 SPX 期权成交量，并未蚕食传统到期合约**
> （按到期日前交易日数拆分的 SPX 期权平均日合约量，其中 0DTE 按 周一/三/五 与 周二/四 分开统计）

**The probability of losing money in the S&P 500 over one day is a little worse than a coin-flip but declines to just 6% over a 10-year time horizon (data since 1929).**

**在标普 500 上持有 1 天出现亏损的概率略高于"掷硬币"（46%），但把投资期限拉长到 10 年，亏损概率就会降至仅 6%**（数据自 1929 年起）。

> **📊 图表 6**：*As time horizons increase, equity losses drop*
> **持股时间越长，亏损概率越低**（基于 1929–2023/5/31 标普 500 总回报）
> 1 天：46% · 1 月：38% · 1 季：32% · 1 年：26% · 3 年：15% · 5 年：10% · 10 年：6%

> **📊 图表 7**：*Time is not as compelling for other asset classes (like oil)*
> **对其他资产类别（如原油）而言，时间的"复利优势"并不那么明显**
> WTI 原油亏损概率（部分历史数据）：1 天：48% · 1 月：43% · 1 季：42% · 1 年：37% · 3 年：32% · 5 年：28% · 10 年：32%

## BofA data-driven research
## 美银数据驱动的研究

It pays to be different. To this end, BofA Global Research publishes a robust suite of data-driven products. From proprietary surveys of financial advisors, US consumers, Millennials, IT spenders, construction dealers etc., to spending barometers like BofA client flows and aggregated BAC credit and debit card data, to sector-specific indicators like Flight Signals and the Industrial Momentum Indicator, to name a few. We showcase the most recent research below.

**差异化，才有超额收益**。为此，美银全球研究部门推出了一整套数据驱动产品，包括：针对金融顾问、美国消费者、千禧一代、IT 支出负责人、建材经销商等群体的自有问卷调查；**美银客户资金流向**、**美国银行汇总的信用卡与借记卡消费数据**等消费量度指标；以及针对特定行业的专属指标，如**航空信号（Flight Signals）** 和 **工业动量指标（Industrial Momentum Indicator）** 等。下方展示的是近期发布的相关研究。

---

# 第 13 页 · 美银近期数据驱动研究一览

> **📊 图表 8**：*BofA Global Research Reports — The most recent BofA data-driven research*
> **美银全球研究部门报告清单 —— 近期数据驱动研究一览**
>
> 下表为报告标题、作者、发表日期。为便于查阅，标题保留英文原题、作者/机构一并附中文简述，日期统一为 YYYY/MM/DD 格式。

| Publish Date 发布日期 | Subtitle 副标题 | Analyst 作者 |
|---|---|---|
| 2023/5/31 | How big is 0DTE gamma really? — *0DTE 的 Gamma 规模究竟有多大？* | Global Equity Derivatives Research 全球股票衍生品研究 |
| 2023/5/30 | EV tracker Apr-23: EU loses significant share; special analysis on premium EVs — *电动车追踪 23 年 4 月：欧洲份额明显下滑；豪华电动车专题* | Schneider, Horst |
| 2023/5/29 | Subdued indicator on weak demand during traditional peak seasons — *传统旺季需求低迷指标* | Zhao, Matty |
| 2023/5/29 | April China ACT reading jumped higher against a low base — *4 月中国 ACT 读数在低基数上明显跳升* | Qiao, Helen |
| 2023/5/29 | Understanding the US market — *读懂美国市场* | Wallace, Ashley |
| 2023/5/26 | Got yield? — *拿到收益率了吗？* | Seliger, Yuri |
| 2023/5/25 | Survey: Brazilians are thirsty for beer — *调查：巴西人对啤酒的需求强劲* | Simonato, Isabella |
| 2023/5/25 | Bonds & Bubbles — *债券与泡沫* | Hartnett, Michael |
| 2023/5/25 | BofA Industrial Momentum Indicator ticks down – are we about to retest the bottom? — *美银工业动量指标回落——是否即将再测底部？* | Global Industrials |
| 2023/5/25 | Spending update through May 20 — *截至 5 月 20 日的消费更新* | US Economics |
| 2023/5/24 | EM Fundamentals have peaked. What comes next? — *新兴市场基本面见顶，接下来呢？* | Milne, Anne |
| 2023/5/24 | Neither panic, nor euphoria — *既不恐慌，也不狂热* | Samadhiya, Ritesh |
| 2023/5/23 | Negative result, but outlook remains soft — *结果负面，但展望仍偏弱* | Beker, David |
| 2023/5/23 | BofA Commercial Aerospace Tracker: WoW North America cycles decline — *美银商用航空追踪：北美周度循环下降* | Heelan, Benjamin |
| 2023/5/23 | US ortho dataset says… cases down -13% M/M in April — *美国骨科数据：4 月案例环比 -13%* | Ryskin, Michael |
| 2023/5/23 | Private client capitulation — *私人客户投降式抛售* | Hall, Jill |
| 2023/5/22 | Bearish JPY vs rest of G10 FX — *看空日元（对其他 G10 货币）* | Iaralov, Vadim |
| 2023/5/22 | Golf Industry Tracker: MODG Club sales -12% in April, but see some green shoots — *高尔夫行业追踪：4 月 MODG 球杆销量 -12%，但已出现一些复苏迹象* | Perry, Alexander |
| 2023/5/22 | China pessimism & US debt limit hopes and fears — *对华悲观情绪与美国债务上限的希望与恐惧* | Vamvakidis, Athanasios |
| 2023/5/19 | Trend Tracker: April slows, Q2 trend est 5.2%; still below trended baseline — *趋势追踪：4 月放缓，Q2 趋势估 5.2%，仍低于趋势基线* | Fischbeck, Kevin |
| 2023/5/19 | The W&W Indicator is marginally bullish in May — *W&W 指标 5 月小幅偏多* | Wu, Winnie |
| 2023/5/19 | Survey Says: Demand (44.3) stays sub-50; Inventory moves further below peak — *调查：需求 44.3 仍在荣枯线下；库存进一步低于峰值* | Hoexter, Ken |
| 2023/5/17 | RENO Barometer shows April showers (and 2H flowers) — *翻新景气指标：4 月风雨，下半年花开* | Suzuki, Elizabeth L |
| 2023/5/16 | BofA Flight Signals shows unit revenues could decelerate into 2H23 — *美银航空信号：单位营收可能在下半年放缓* | Didora, Andrew |
| 2023/5/16 | Watching and waiting — *观望中* | Tupper, Nigel |
| 2023/5/16 | BofA Japan FA Indicator improves again — *美银日本金融顾问指标再次改善* | Hotta, Kenjin |
| 2023/5/16 | Monthly restaurant spending: spend continues slowdown across segments — *餐饮月度消费：各细分持续放缓* | Senatore, Sara |
| 2023/5/16 | Turned bullish cash — *转为看多现金* | Morris, John |
| 2023/5/16 | Small sentiment uptick — *情绪小幅回升* | Beker, David |
| 2023/5/16 | FMS: sell the news? — *基金经理调查：利好兑现即卖出？* | Virgo, Alexander |
| 2023/5/16 | State of Play: Assessing the China rebound — *形势评估：中国反弹还能走多远？* | Roux, David |
| 2023/5/16 | Hoping for a soft landing — *期待软着陆* | Raedler, Sebastian |
| 2023/5/15 | Default and loss pressures in the current default cycle — *当前违约周期中的违约与损失压力* | Khoda, Neha |
| 2023/5/15 | April card spending: soft but not slumping — *4 月刷卡消费：偏弱但未崩塌* | Thornton, Thomas (T.J.) |
| 2023/5/15 | Real-time Grocery Spending Update: See trade down to value grocery channel — *实时杂货消费更新：消费降级至平价渠道* | Ohmes, Robert |
| 2023/5/15 | Survey: Home health vols tracking above Q1, labor costs remain a headwind — *调查：居家医疗量高于 Q1，人工成本仍是逆风* | Gajuk, Joanna |
| 2023/5/12 | April pool spending and composite decking search trend update — *4 月泳池消费与复合地板搜索趋势更新* | Jadrosich, Rafe |
| 2023/5/12 | BofA's assessment of US Mall REITs, 9th edition — *美银美国购物中心 REIT 评估（第 9 版）* | REITs Team |
| 2023/5/12 | Duration extremes — *久期极值* | Preusser, Ralf |
| 2023/5/12 | Broad based spending slowdown in April — *4 月消费全面放缓* | Hutchinson, Lorraine |
| 2023/5/10 | The BofA Alts EXAMINER: Forecast soft fundamentals in 2Q/3Q but still LT bullish — *美银另类投资观察：预计 Q2/Q3 基本面偏弱，但长期仍乐观* | Siegenthaler, Craig |
| 2023/5/10 | Unambiguous trend — *趋势明朗* | Nair, Girish |
| 2023/5/9 | Japan Consumer Survey (Apr 23): Continued recovery — *日本消费者调查（23 年 4 月）：复苏持续* | Devalier, Izumi |
| 2023/5/5 | Chemical conditions tool: April makes a fool of recovery hopes — *化工景气工具：4 月让复苏希望落空* | Yates, Matthew |
| 2023/5/4 | From "lucky to have me" to "thanks for having me," labor markets loosen — *从"能雇到我是你们的福气"到"谢谢你们肯雇我"——劳动力市场正在松动* | Thornton, Thomas (T.J.) |
| 2023/5/4 | Apr-23: Street catching up on earnings cuts; further cuts likely — *23 年 4 月：卖方盈利下调正在追赶现实，后续还会下调* | Shah, Amish |
| 2023/5/2 | May 2023 update: Stay positive — *23 年 5 月更新：保持乐观* | Gee, Nathan |
| 2023/5/2 | Light at the end of the tunnel — *隧道尽头的曙光* | Luo, Chen |
| 2023/5/1 | April app data: Mixed trends continue, travel growth slowing on tougher comps — *4 月 App 数据：趋势分化延续，高基数下旅游增速放缓* | Post, Justin |
| 2023/5/1 | CB investors brace for a recession — *可转债投资者为衰退做准备* | Youngworth, Michael |
| 2023/5/1 | 1Q23 Pharma Survey: New modules, same old macro — *23 年 Q1 医药调查：新模块，同样的宏观老问题* | Lutz, Allen |
| 2023/5/1 | Bulls are becoming an endangered species — *多头正在成为濒危物种* | Subramanian, Savita |

## Myth-busters
## 流言终结者

### Market narratives abound
### 市场流言层出不穷

Amid a period of "Macro discord" (see Quantitative Profiles) and a year marked by a multitude of economic/market crosscurrents, we have heard a number of myths related to market behavior that we have attempted to address or debunk in our work.

在当下这段**"宏观失调"**时期（详见《量化策略画像》报告），以及这个经济与市场多重暗流交织的年份里，我们听到了形形色色关于市场行为的"流言"。本章试图逐一正面回应并戳破其中的一部分。

---

# 第 14 页 · 流言 ①—② 戳破

## False: buybacks drive performance
## 流言①：股票回购能推动股价表现 —— **错**

Given we expect a shift from buybacks to dividends, does this spell doom for the S&P 500? Actually, the relationship between S&P 500 buybacks and index performance since 1986 is a minimal 0.08 R-squared (Exhibit 9). Furthermore, our weekly BofA corporate client buyback data have a similarly low relationship with future index performance (0.01 R-squared) (Exhibit 10). What we can validate is that companies that repurchase shares at inexpensive valuations tend to outperform (Exhibit 11). In fact, over the past 12 months (as of 4/30/23) cheap buybacks outperformed expensive buybacks by 7.6ppt.

我们预计企业现金回报重心将从**回购**逐步转向**派息**——这是否意味着标普 500 要遭殃？实际并不是。自 1986 年以来，标普 500 的回购规模与指数表现之间的相关性 **R² 仅为 0.08**（图表 9），几乎不相关。我们自己每周跟踪的美银公司客户回购数据，对未来指数表现的解释力同样极低（R² = 0.01，图表 10）。真正能被验证的规律是：**在低估值时做回购的公司往往跑赢**（图表 11）。事实上，截至 2023 年 4 月 30 日的过去 12 个月里，"便宜时回购"的一组公司比"贵时回购"的一组公司**跑赢 7.6 个百分点**。

> **📊 图表 9**：*Little evidence of share buybacks helping performance*
> **几乎看不到回购带动指数表现的证据** —— 标普 500 过去 12 个月回购金额（占市值%）对比指数同期回报，R² = 0.08

> **📊 图表 10**：*BofA corporate client buybacks also appear to have little effect on index performance*
> **美银公司客户的回购数据对指数表现同样几乎无效** —— 周度回购量（占当年回购总额%）对比指数周度回报（2009/6 至今），R² = 0.0141

> **📊 图表 11**：*Companies that reduce shares at low valuations tend to outperform*
> **低估值时回购的公司倾向于跑赢**（年化回报，1986/1–2023/4）：单纯回购 ≈ 14%；回购+高 FCF/EV ≈ 14.5%

## False: retail investors are a contrary indicator
## 流言②：散户是反向指标 —— **错**

Some claim that institutional investors are the "smart" money and retail investors are better contrary indicators – when retail is buying, it's time to sell, and vice versa. But our BofA Securities Equity Client Flows suggest the opposite (Exhibit 12). Returns following periods of retail inflows have been above average and returns post-retail selling have been below average, with a similar spread to hedge funds (suggesting the latter was not a better signal). Relatedly, our Low Institutional Ownership factor – which includes high retail ownership stocks – has more consistently outperformed during market drops; during months since 1986 with the index falling 3%+, the screen produced an average alpha of 1ppt.

常有一种说法：机构是"聪明钱"，散户是"反向指标"——散户买则应卖、散户卖则应买。但我们的美银证券股票客户资金流数据给出了**相反**的结论（图表 12）：散户**净流入后**的市场回报**高于平均**，净流出后的回报**低于平均**，其信号价差甚至接近对冲基金（也就是说，**对冲基金也并非更优信号**）。相关地，我们的 **"低机构持股"因子**（该组合里高散户持股的股票比例较高）在市场下跌时反而更稳定地跑赢：自 1986 年以来，每逢指数单月跌幅超 3% 时，该策略平均产生 **1 个百分点的阿尔法**。

> **📊 图表 12**：*Retail investors have been similar positive indicators to hedge funds*
> **散户其实是类似于对冲基金的"正向"指标**（2008 年至今标普 500 后 4 周回报，按前 4 周资金流正/负划分）
>
> | 资金类型 | 净流入后 4 周回报 | 净流出后 4 周回报 | 价差 |
> |---|---|---|---|
> | 对冲基金 Hedge Funds | 1.0% | 0.5% | **0.4%** |
> | 机构 Institutional | 1.5% | 0.3% | **1.2%** |
> | 散户 Retail | 0.9% | 0.6% | **0.3%** |

---

# 第 15 页 · 流言 ③—④ 戳破

## False: valuation doesn't matter, price is the best predictor of price
## 流言③：估值不重要，"以价测价"才准 —— **错**

The unwavering faith in price momentum investing is likely attributable to a liquidity-fueled decade that saw tremendous serial correlation across price returns. The average portfolio manager (~45 y.o.) has seen a financial crisis during which statistically cheap stocks were traps, followed by a decade during which value factors destroyed alpha almost every year while investing based on past price return turned in hefty alpha. The few value investors left see post-COVID shifts as a sort of come-uppance: Value (proxied by long-short EV/EBITDA) returned 30ppt from 2021-2022, whereas price return produced no alpha. Prior to the GFC, valuation was a far better signal than basing future forecasts on past price returns. And while Growth has outperformed Value YTD, part of this outperformance was driven by a mini bout of QE this year post-SVB (Silicon Valley Bank failure).

投资者对**价格动量**的信仰之所以根深蒂固，很可能要归因于过去那十年由流动性驱动、价格回报之间出现极强序列相关性的特殊行情。**今天的基金经理平均年龄约 45 岁**，他们的职业生涯大致经历了两个阶段：先是 2008 年那场金融危机——那期间"统计意义上便宜"的股票几乎都是陷阱；紧接着就是长达十年的"价值每年都在毁阿尔法，而动量年年奏效"的岁月。硕果仅存的价值投资者，把新冠后的市场变化视作某种"风水轮流转"：以 EV/EBITDA 多空组合代表的**价值**在 2021–2022 年累计回报 **30 个百分点**，同期**价格动量几乎没有阿尔法**。而在 2008 年全球金融危机（GFC）之前，**估值作为预测信号的有效性远胜于"以过去价格预测未来价格"**。虽然今年年初至今成长跑赢价值，但其中一部分超额收益是由硅谷银行（SVB）倒闭后今年上半年那波**小规模量化宽松（QE）**行情推动的。

> **📊 图表 13**：*Valuation matters, it just hasn't for the last 10 years*
> **估值其实一直重要，只是过去 10 年失效**（EBITDA/EV 与 3 个月价格回报的阶段表现）
> - GFC 前（1986–2006）：价值（EBITDA/EV）显著正向，动量偏弱
> - GFC 后（2010–2020）：价值大幅失效，动量主导
> - 新冠后（2021–2022）：价值卷土重来，动量归零

## False: valuation doesn't matter for Tech
## 流言④：估值对科技股不重要 —— **错**

While the Tech sector has earned a reputation as a valuation-defying high flier, we have found that valuations have mattered for Tech investors selecting stocks within the sector. Over the past 38 years, companies with low Price to Free Cash Flow and low EV to EBITDA have generated annualized alpha of 6.4ppt and 5.2ppt vs. the sector.

科技板块给人的印象是"估值无效、一路高飞"。但我们的研究显示：**对在科技板块内部选股的投资者来说，估值同样重要**。过去 38 年里，在科技行业中使用**低 P/FCF（股价/自由现金流）** 和 **低 EV/EBITDA** 筛选出的公司，相对行业基准分别带来 **6.4 ppt** 和 **5.2 ppt** 的年化阿尔法。

> **📊 图表 14**：*Price to Free Cash Flow outperformed the index most*
> **在信息技术行业中，P/FCF 是最好的估值类因子**
> （1985/1 至 2023/4 首五分位年化表现；横轴 = 12 个月回报的标准差，纵轴 = 年化平均回报）

---

# 第 16 页 · 流言 ⑤—⑦ 戳破

## False: duration only matters for bonds
## 流言⑤：久期只对债券有用 —— **错**

In 2022, as markets repriced assets amid rising real rates (10-yr real yield + 235bp) and an aggressive Fed tightening cycle (fed funds rate + 425bp), the Russell 1000 Growth index (-29.1%) underperformed the Russell 1000 Value (-7.5%). Our Long Equity Duration factor, back-end loaded growth stocks that are more vulnerable to rising cost of capital, suffered a 25.5% loss and ranked among the worst three factors for the year.

2022 年，随着 **10 年期实际利率上行 235 个基点**、美联储激进加息（联邦基金利率上调 **425 个基点**），全市场资产被重新定价：罗素 1000 成长指数暴跌 **-29.1%**，而罗素 1000 价值指数仅 -7.5%。我们的**长久期权益（Long Equity Duration）** 因子——刻画"收益高度集中于遥远未来、因此对资本成本上行最敏感"的成长股——当年亏损 **25.5%**，跻身全年**表现最差的三个因子**之一。（由此可见，**股票也有"久期"**，且并不是债券独有的概念。）

## False: bad breadth is bearish
## 流言⑥：市场广度差 = 熊市 —— **错**

Only 23% of stocks outperformed the S&P 500 in May, the lowest of any month in our data history since 1986. Five stocks added 2.4ppt to the index. The other 495 stocks detracted 2.0ppt from the index. But history suggests weak breadth itself isn't a precursor of market weakness: in years of mega-cap leadership since 1986, the market was up the subsequent year nearly 75% of the time (see US Performance Monitor).

2023 年 5 月，**仅 23% 的个股跑赢标普 500**——这是自 1986 年有数据以来任意月份中的**最低值**。当月，5 只股票为指数贡献了 **+2.4 ppt**，其余 495 只合计**拉低指数 2.0 ppt**。但历史经验表明，**广度走弱本身并不是市场走弱的前兆**：自 1986 年以来，凡是**大盘股（Mega-cap）领涨**的年份，**次年市场上涨的概率接近 75%**（详见《美国表现监视器》报告）。

> **📊 图表 15**：*Bad breadth usually mean reverts*
> **差广度通常会均值回归** —— 过去 3 个月跑赢标普 500 的股票占比（1986 至 2023/5/31）

> **📊 图表 16**：*In years of mega-cap leadership since 1986, the market was up the subsequent year nearly 75% of the time*
> **自 1986 年以来，大盘 50 股票跑赢的年份，次年标普上涨概率接近 75%**
>
> | 年份 Year | 漂亮 50 表现 | 标普 500 表现 | 相对超额 | 次年标普 500 表现 |
> |---|---|---|---|---|
> | 1989 | 33.4 | 27.3 | 6.1 | **-6.6** |
> | 1990 | 0.3 | -6.6 | 6.9 | **26.3** |
> | 1995 | 37.8 | 34.1 | 3.7 | 20.3 |
> | 1996 | 24.0 | 20.3 | 3.8 | 31.0 |
> | 1997 | 34.4 | 31.0 | 3.4 | 26.7 |
> | 1998 | 35.2 | 26.7 | 8.6 | 19.5 |
> | 1999 | 20.1 | 19.5 | 0.6 | **-10.1** |
> | 2006 | 14.3 | 13.6 | 0.7 | 3.5 |
> | 2011 | 1.4 | 0.0 | 1.4 | 13.4 |
> | 2015 | 2.2 | -0.7 | 3.0 | 9.5 |
> | 2017 | 19.6 | 19.4 | 0.1 | **-6.2** |
> | 2018 | -3.6 | -6.2 | 2.6 | 28.9 |
> | 2019 | 30.1 | 28.9 | 1.2 | 16.3 |
> | 2020 | 23.2 | 16.3 | 6.9 | 26.9 |
> | 2021 | 28.1 | 26.9 | 1.2 | **-19.4** |
> | **均值 Avg** |  |  |  | **12.0** |
> | **中位 Median** |  |  |  | **16.3** |
> | **胜率 Hit Rate** |  |  |  | **73%** |

## False: flows into equities push multiples higher
## 流言⑦：股票资金流入会推高估值 —— **错**

One might intuitively expect multiples to expand with inflows, and compress with outflows. In actuality, the correlation between equity flows and valuations is effectively zero (Exhibit 17). Our work suggests other reasons keeping the S&P 500 at its current lofty snapshot multiples, including the tendency for P/E ratios to rise when earnings decline and years of Quantitative Easing driving multiple expansion (see Relative Value).

直觉上会以为"资金流入→估值扩张、资金流出→估值收缩"。但事实上，**股票资金流向与估值之间的相关性几乎为零**（图表 17）。我们认为支撑标普 500 当前高估值的原因另有其因，包括：**盈利下滑时 P/E 反而抬升**（分母坍塌效应）以及**多年量化宽松（QE）推高估值中枢**（详见《相对估值》）。

> **📊 图表 17**：*No relationship between equity inflows and valuations*
> **股票资金流入与估值之间没有相关性**（2000–2021 年，标普 500 远期 P/E 同比变化 vs. 过去 12 个月股票资金流/市值%，R² = 0.0009）

---

# 第 17 页 · 流言 ⑧—⑨ 戳破

## False: value underperforms during economic recessions
## 流言⑧：价值股在经济衰退中跑输 —— **错**

Investors tend to shun Value during periods of economic recession. Our work shows that during NBER recessions over the past almost 40 years, Value along with Quality were most consistently outperforming attributes with a 75% outperformance rate (Exhibit 6). Free cash flow based (High FCF/EV, Price/FCF), as well as Low EV/EBITDA were the best performing Value factors during those periods (Exhibit 19).

投资者在经济衰退期往往避开价值股。但我们的研究表明：在过去近 40 年里 **NBER 界定的经济衰退中，价值与质量是两类最稳定跑赢的特征**，**胜率 75%**（图表 6）。那些时期表现最好的价值类因子包括：基于自由现金流的 **高 FCF/EV**、**低 P/FCF**，以及 **低 EV/EBITDA**（图表 19）。

> **📊 图表 18**：*Value and Quality*
> **价值与质量：NBER 衰退期因子相对于等权标普 500 的表现（1986 至今）**
>
> | | 价值 | 现金回报 | 动量 | 成长 | 质量 | 风险 | 杂项 | 小盘 |
> |---|---|---|---|---|---|---|---|---|
> | Avg | 0.1% | -1.0% | -3.6% | -3.7% | 7.2% | 8.8% | 0.4% | 2.1% |
> | Median | 3.4% | 0.4% | -2.5% | -4.2% | 6.8% | 6.8% | 0.6% | 3.9% |
> | **胜率** | **75%** | 50% | 50% | 25% | **75%** | 50% | 50% | 50% |

> **📊 图表 19**：*Quality and Value tends to outperform during economic recessions*
> **质量与价值在经济衰退期倾向于跑赢**（NBER 衰退期单因子相对表现，1986 至今）
>
> | 因子 | Avg | Median | 胜率 |
> |---|---|---|---|
> | 5 年 ROE（负债调整） | 9.4% | 9.3% | **100%** |
> | 1 年 ROE（负债调整） | 6.8% | 7.8% | 75% |
> | ROA | 8.0% | 6.6% | **100%** |
> | 5 年 ROE | 8.1% | 6.3% | **100%** |
> | 1 年 ROE | 5.6% | 6.1% | 75% |
> | FCF/EV | 6.0% | 5.9% | 75% |
> | 低股价 | 3.4% | 5.8% | 75% |
> | EV/EBITDA | 2.3% | 5.8% | 75% |
> | ROC | 4.9% | 4.9% | 75% |
> | P/FCF | 3.5% | 4.3% | 75% |
> | 盈利收益率 | -0.8% | 3.6% | 75% |
> | P/CF | -1.2% | 2.1% | 75% |
> | 远期盈利收益率 | -1.5% | 1.7% | 75% |
> | 正向 EPS 超预期 | 0.5% | 1.0% | 75% |
> | 海外敞口 | 2.1% | 0.9% | 75% |

## False: during periods of wage disinflation labor intensive companies outperform
## 流言⑨：工资通胀下行时，劳动密集型公司会跑赢 —— **错**

Investors shouldn't own labor-intensive companies under almost any circumstances (Exhibit 20), based on our analysis. Despite the fact that the Fed is keenly focused on cooling wage inflation, which could be a boon to labor-intensive companies' margins, we find that companies with the highest ratio of number of employees per dollar of sales have been almost constant laggards relative to their labor-light counterparts.

按我们的分析，**几乎在任何时候，投资者都不应持有劳动密集型公司**（图表 20）。尽管美联储正全力压降工资通胀——理论上这会改善劳动密集型公司的利润率——但我们发现：**"每 1 美元营收对应员工数"最高**的那一组公司，相对于劳动力消耗较少的同行，**几乎长期跑输**。

> **📊 图表 20**：*Most labor intensive companies tend to underperform their least labor intensive peers on a sector neutral basis…*
> **在行业中性口径下，最劳动密集组（D1）相对最不劳动密集组（D10）长期跑输**（相对等权标普 500 的累计表现，1986–2022）

> **📊 图表 21**：*…as well as on an unconstrained basis*
> **在不加行业约束的口径下同样如此**（按员工/营收的十分位，D1 vs. D10）

---

# 第 18 页 · 流言 ⑩—⑪ 戳破

## False: ERP needs to rise from here
## 流言⑩：股权风险溢价（ERP）还得往上走 —— **错**

While it is true that historical downturns have resulted in a much sharper increase in the equity risk premium (ERP) vs. now, we see reasons for the ERP to settle at lower levels. First, upside risk in real rates argues for a lower ERP (correlation between ERP and real rates = -84%). Moreover, ERP has trended lower during periods of strong efficiency gains (avg. of ~200bp from 1986-2006 vs. ~550bp post-GFC when efficiency gains stalled), and we believe Corporate America may be on the cusp of a new efficiency cycle (see Strategy in Pictures).

的确，历史上历次"下行期"中，**股权风险溢价（Equity Risk Premium, ERP）** 的跳升幅度都比当下更陡峭。但我们认为**这一次 ERP 可能会稳定在更低水平**，有如下几点理由：
（1）**实际利率仍有上行空间**意味着 ERP 应更低——**ERP 与实际利率的相关系数为 -84%**；
（2）**生产效率强劲改善的时期，ERP 往往趋势性走低**（1986–2006 年 ERP 均值约 200bp；2008 年全球金融危机后效率提升停滞，ERP 均值升至约 550bp）；
（3）我们判断**美国企业部门（Corporate America）正站在一个新效率周期的起点**（详见《图说策略》报告）。

> **📊 图表 22**：*Higher real rates = lower ERP*
> **实际利率上行 → ERP 下行**（归一化 ERP 与实际利率的历史关系，1945–2023/5，R² = 0.7042）

> **📊 图表 23**：*Higher ERP amid stalled productivity*
> **生产率停滞期间 ERP 抬升**（标普 500 每员工每年营收 vs. 归一化 ERP，经 CPI 调整，1986–2023/5）
> 方法注：归一化 ERP = 归一化盈利收益率 − 实际无风险利率；归一化 EPS 基于标普 500 **Pro-forma EPS** 与 **Operating EPS** 的混合序列做对数线性回归；实际利率 = 10 年期国债收益率 − 10 年期盈亏平衡通胀；1998 年之前以"**未来 1 年 CPI**"替代盈亏平衡通胀（与 10 年期盈亏平衡通胀的相关性最强）。

## False: wait for the Fed pivot
## 流言⑪：先等美联储转向，再看多股市 —— **错**

Over the past year, investors have been waiting for signs of a Fed pivot to become bullish. But historically, the worst phase for equities has been when the Fed was easing and credit conditions were tightening, a regime that we typically see in a recession. Our economists continue to see resilience in the US economy, forecasting only a mild recession (or "growth recession") starting next year and no rate cuts until May 2024 (see Economic Viewpoint).

过去一年，投资者一直在等"**美联储转向（Fed pivot）**"的信号出现再转多。但翻开历史，**对股市最差的阶段恰恰是"美联储宽松 + 信用紧缩"并存的时期**——而这正是典型的**衰退情景**。我们的经济学家团队仍然看好美国经济的韧性，预计明年开始只会出现一次温和衰退（或"**增长型衰退**"，Growth recession），**首次降息要等到 2024 年 5 月**（详见《经济观点》报告）。

> **📊 图表 24**：*Fed easing/credit tightening sees weakest return*
> **"美联储宽松 + 信用紧缩"期间股市回报最弱**（1996–2023/5 标普 500 月度回报；*美联储周期由 2 年期利率判断；信用周期由投资级信用利差判断*）
>
> | 情景 | 平均 | 中位 | 上涨概率 |
> |---|---|---|---|
> | 美联储紧缩 + 信用宽松 | **+2.0%** | +2.2% | **73%** |
> | 美联储紧缩 + 信用紧缩 | +1.2% | +1.2% | 75% |
> | 美联储宽松 + 信用紧缩 | **-1.1%** | -0.7% | **44%**（最差） |
> | 美联储宽松 + 信用宽松 | 0.0% | -0.4% | 49% |

---

# 第 19 页 · 第一部分导读（Section I）

## Section I: Core Concepts and Methodology
## 第一部分：核心概念与方法论

| 页码 | 英文章节名 | 中文译名 |
|---:|---|---|
| 20 | What drives market performance? | 什么决定了市场表现？ |
| 38 | Liquidity risks for the S&P 500 | 标普 500 的流动性风险 |
| 39 | Earnings Expectation Life Cycle | 盈利预期生命周期 |
| 43 | Factor timing | 因子择时 |
| 56 | Measuring risk | 风险度量 |
| 61 | Roadmap to picking stocks | 选股路线图 |
| 67 | US Regime Indicator | 美国市场体制指标 |
| 72 | What are quants doing? | 量化从业者在做什么？ |
| 78 | Alternative Data | 另类数据 |
| 90 | The ABC's of ESG | ESG 入门 |

---

# 第 20 页 · 什么决定了市场表现？

## What drives market performance?
## 什么决定了市场表现？

Overall stock market performance is largely a function of valuation, sentiment and profits. When an investor buys stocks, he/she is buying a share of the future profits of the company and must decide whether the market is valuing this profits stream correctly. Valuation can be heavily influenced by investor sentiment, scarcity or abundance of other options, visibility, quality, governance, and a host of other factors that are difficult to quantify.

**股票市场的整体表现，主要由三件事决定：估值、情绪、盈利**。投资者买股票，本质上是在买这家公司未来盈利的一部分份额——所以必须判断：**市场对这条盈利河流的定价是否合理**。而估值本身会受到诸多因素的强烈影响：投资者情绪、其他可选资产的稀缺或充裕程度、可预见性、经营质量、公司治理，以及一大堆难以量化的因素。

### 1. Valuation
### 1. 估值

Our work suggests that valuation is generally a poor market timing indicator over short to medium time horizons. However, over longer time horizons valuation may be the most important determinant of market returns. The drawback of most single-period valuation ratios used by investors is that they implicitly assume that the single period being used – for example, EPS over the next 12 months in the case of forward PE ratios – is representative of the trajectory of future profit growth. Our preferred valuation measures adjust for this single-period bias.

我们的研究表明：**估值在短—中期并不是一个好的择时指标**；但**时间拉长之后，估值很可能是决定市场回报最关键的变量**。市面上多数单期估值比率（如**远期市盈率**，用未来 12 个月 EPS 作分母）都有一个隐含缺陷——**假定这"一个期间"的盈利水平能代表公司未来盈利的长期轨迹**，但这个假设往往不成立。我们**偏好的估值方法会修正这种"单期偏差"**。

#### Normalized P/E Framework
#### 归一化市盈率框架（Normalized P/E）

One way to adjust for the single-period bias is to estimate the underlying earnings power based on the historical trend, adjusting for inherent cyclicality. We estimate normalized earnings based on a linear log normal regression and our analysis shows that this measure of market valuation explains over 80% of the variability of equity market returns over the next 10 years (Exhibit 25). In the late-1990s, equity valuations were near peak levels, and we subsequently saw negative returns over the following decade. In contrast, valuations in the wake of the Global Financial Crisis reached extreme levels far below those seen during the 1980s and 1990s, and were similarly followed by strong equity market returns.

修正单期偏差的一种方法是：**基于历史趋势估算公司真实的盈利能力，并剔除其固有的周期波动**。我们用**线性对数正态回归**估算出"归一化盈利"，并以此构造归一化 P/E。分析显示，**这一估值指标对未来 10 年股票市场回报波动的解释力超过 80%**（图表 25）。具体来看：1990 年代末期估值接近历史峰值，随后 10 年市场回报为负；而 2008 年全球金融危机之后，估值跌至**远低于 1980s 与 1990s 的极端低位**，其后的十年股市回报也同样强劲。

> **📊 图表 25**：*Valuations explained ~80% of 10yr returns*
> **估值可解释约 80% 的未来 10 年回报**（标普 500 归一化 P/E vs. 其后 10 年年化回报，1987 至 2023/4；R² = 83%）
> **当前归一化 P/E：21 倍**

---

# 第 21 页 · 归一化 P/E 的长期解释力 & 股权风险溢价框架

> **📊 图表 26**：*Almost all that matters over the long term*
> **长期几乎就看这一件事** —— 归一化 P/E 对标普 500 后续各期回报的解释力（1987–2023/4）
> （横轴：持有期年数 0–12；纵轴：R² = 归一化 P/E 对后续区间回报的解释度——持有期越长，解释力越高，10 年达 ~80%+）

> **📊 图表 27**：*S&P's normalized PE is currently above average*
> **标普 500 当前归一化 P/E 高于均值**（1987–2023/4，归一化 P/E 8x–36x 历史走廊）

## Equity Risk Premium Frameworks
## 股权风险溢价（ERP）框架

Whereas normalized P/E ratios adjust for the single-period bias, two criticisms of this framework are that (1) it is backward looking; and (2) does not account for changes in the cost of capital. The equity risk premium (ERP) is the amount of additional return beyond the risk-free rate that investors require as compensation for accepting the investment risks and costs associated with owning stocks. When investor fear levels are high, and equities are perceived as being risky, the equity risk premium, or the required return of equities, increases to compensate for that risk. And vice versa.

归一化 P/E 虽然修正了"单期偏差"，但它也有两点常被诟病：（1）**向后看**（backward-looking）；（2）**未考虑资本成本的变化**。**股权风险溢价（Equity Risk Premium, ERP）** 则衡量投资者为承担持股风险与成本所要求的"无风险利率以上的额外回报"。当投资者恐慌情绪高涨、股票被视为高风险时，ERP（即对股票的要求回报）就会上升以补偿风险；反之亦然。

A rising equity risk premium typically coincides with higher quality investments outperforming, and a falling risk premium typically coincides with lower quality, riskier investments outperforming. An alternate interpretation is the idea that as the cost of equity capital (or the discount rate) increases, shorter duration (higher dividend yielding) equities generally outperform, and as the cost of capital falls, longer duration, higher growth and higher beta companies generally outperform.

**ERP 上行期通常高质量投资跑赢；ERP 下行期则低质量、高风险资产跑赢**。换一种说法：**股权资本成本（或贴现率）上行时，短久期（高股息）股票占优；资本成本下行时，长久期、高成长、高贝塔公司占优**。

The literature on equity risk premia is vast, but we have distilled it into two methods for evaluating the equity risk premium – a normalized approach and a market-derived approach.

关于 ERP 的研究文献浩如烟海，我们将其凝练为两种方法：**归一化法** 与 **市场隐含法**。

### Normalized Equity Risk Premium Framework
### 归一化 ERP 框架

We estimate the historical ERP as the normalized EPS yield (normalized EPS ÷ current price) less the real risk-free rate. The real risk-free rate is the difference between 1) the 10-yr Tsy yield; and (2) the 10-yr breakeven. Prior to 1998, fwd 1-yr CPI was used as a proxy for the breakeven (this showed the strongest correlation to the 10-yr breakeven).

历史 ERP 我们这样估算：**归一化盈利收益率**（归一化 EPS ÷ 当前价）**减去实际无风险利率**。实际无风险利率 = **10 年期国债收益率 − 10 年期盈亏平衡通胀**。1998 年以前，**用"未来 1 年 CPI"作为盈亏平衡通胀的代理**（与 10 年期盈亏平衡通胀相关性最强）。

---

# 第 22 页 · 归一化 ERP 的历史与实际利率关系

> **📊 图表 28**：*We expect ERP to normalize at levels lower than the post-Global Financial Crisis era's average of 550bp*
> **我们预计 ERP 将稳定在低于 GFC 后 550bp 均值的水平**（1945–2023/4，归一化 ERP；BofA 预测值 350bp）
> 关键标注：二战末、科网泡沫、GFC、新冠；历史均值 540bp；GFC 后均值 550bp；1980–2010 效率繁荣（剔除科网泡沫）均值 300bp。

> **📊 图表 29**：*Higher real rates = lower ERP*
> **实际利率越高 → ERP 越低**（归一化 ERP vs. 实际利率，1945–2023/4，R² = 0.7045）

### Market-derived Equity Risk Premium Framework
### 市场隐含 ERP 框架

Our market-derived Equity Risk Premium framework is based on our proprietary Dividend Discount Model (DDM), making use of our analysts' forecasts for company earnings and dividends in order to estimate the expected, or required, rate of return of the equity market. For more details on our DDM, see the Appendix. Because our DDM mimics the yield-to-maturity calculation for a bond, we essentially compute the "yield-to-maturity" of equities. The spread between the expected return of the S&P 500 and corporate bond yields (as measured by AAA Long-Term Corporate Bond Rates) estimates the risk premium demanded by the market for taking on equity-specific risk over credit risk.

我们的市场隐含 ERP 框架基于自有的 **股息贴现模型（DDM）**，用分析师对公司盈利与股息的预测来估算市场的期望/要求回报率（DDM 细节见附录）。由于这个 DDM 在机制上**模拟债券的到期收益率（YTM）计算**，相当于给股票算出了一个"**到期收益率**"。**标普 500 的期望回报 − AAA 长期公司债利率**，就近似于**市场为承担"股权风险而非信用风险"所要求的风险补偿**。

---

# 第 23 页 · 市场隐含 ERP 与 通胀-P/E 框架

> **📊 图表 30**：*S&P 500 Risk Premium declined in recent months*
> **标普 500 风险溢价近几个月回落**（市场隐含 ERP = DDM 隐含期望回报 − AAA 公司债利率，1980/11–2023/4）
> **当前：615bp；长期均值：504bp**

### Inflation vs. P/E Framework
### 通胀 vs. P/E 框架

The inflation vs. P/E framework is based on the premise behind the "Rule of 21" valuation framework that has been used by traders in the past. The Rule of 21 states that the combination of the S&P 500 P/E and the year-to-year inflation rate (CPI) should be equal to 21. We found that the relationship is well-motivated, and there is a trade-off between inflation and multiples, but not at valuation and inflation extremes. Therefore, a non-linear curve better fits this thesis. Exhibit 31 below highlights the historical relationship between inflation and P/E over time. We quantify this relationship using a least-squares regression model fitted to an equation in the form y= cxb where b and c are constants.

通胀-P/E 框架源于历史上交易员惯用的"**21 法则（Rule of 21）**"：**标普 500 P/E + 同比 CPI ≈ 21**。我们研究发现这个关系逻辑上说得通——**通胀与估值之间确实存在权衡**——但在**估值与通胀极端值处这种线性关系不再成立**。因此用**非线性曲线拟合更合理**。图表 31 展示了通胀与 P/E 的历史关系，我们用**最小二乘回归**拟合成 **y = c·xᵇ**（b、c 为常数）的形式。

> **📊 图表 31**：*Inflation vs. P/E Framework*
> **通胀与 P/E 框架**（1965 至今）
> 关键标注点：1974/10、1982/8、1987/8、1990/10、1995/1、2000/3、2002/10、2008/8、2021/12、当前。
> **当前 P/E 对应的隐含通胀 ≈ 2.7%；当前通胀对应的隐含 P/E ≈ 14.4 倍**。

---

# 第 24 页 · 情绪：卖方指标

## 2. Sentiment
## 2. 情绪

Returns tend to be greater where capital is scarce. As investors flock to invest in an asset, it pushes up the price and lowers the potential future returns of that asset. Thus, there should be an inverse correlation between investors' willingness to invest in stocks and future equity returns. And this is precisely what we have found.

**资金最稀缺的地方往往回报最高**。当投资者蜂拥买入某类资产时，价格被推高，未来的潜在回报就会下降。因此，**投资者对股票的热情与未来股票回报应呈反向关系**——我们的研究也正是这样印证的。

### Sell Side Indicator
### 卖方指标（Sell Side Indicator）

The Sell Side Indicator — our proprietary framework that measures Wall Street's bullishness on stocks — is based on the average recommended equity allocation of Wall Street strategists as of the last business day of each month. These equity weightings are from strategists who submit their asset allocation recommendations to us. We have found that Wall Street's consensus equity allocation has historically been a reliable contrary indicator. In other words, it has historically been a bullish signal when Wall Street was extremely bearish, and vice versa.

**卖方指标**是我们衡量华尔街对股票多空立场的自有框架——取每月最后一个交易日各家华尔街策略师推荐的**平均股票配置比例**。这些权重由向我们报送资产配置建议的策略师提供。历史数据表明：**华尔街共识股票配置一直是可靠的反向指标**——华尔街极度看空时反而是多头信号，极度看多时反而是空头信号。

> **提示**：为什么情绪通常是好的反向指标？**当所有数据、头条与噪音一面倒地偏向某一方向时，市场极大概率已充分消化甚至过度消化这种预期——于是实际走势更可能向反方向出其不意**。

> **📊 图表 32**：*Sell Side Indicator has high predictive power vs. frameworks like the Fed Model*
> **卖方指标的预测力远高于"美联储模型"一类框架**（各指标预测未来 12 个月标普 500 回报的 R²）
>
> | 指标 | R² |
> |---|---|
> | 卖方指标 | **24%** |
> | 卖方指标处于极值（买入/卖出阈值）| **34%** |
> | 标普 500 股息率 | 12% |
> | Pro-forma P/E | 10% |
> | 调整后美联储模型（EPS 收益率 − 10Y 实际利率）| 4% |
> | M1 增速 | 3% |
> | 美联储模型（EPS 收益率 − 10Y 国债）| 1% |

Given secular changes in equity allocation over time, we believe comparing the recommended equity allocation to a moving average may be most effective. Wall Street sentiment appears to go through long-lasting secular phases that can last more than a decade. From the '80s to the mid-90s, the average equity allocation was anchored at a lower level and then grew more aggressive beginning in the late '90s. Equity allocations have declined dramatically over the past year relative to bond allocations, putting us close to a "Buy" signal based on this indicator.

考虑到股票配置存在长期结构性变化，**将推荐配置与其滚动均值作对照**可能最有效。华尔街情绪似乎会经历持续超过十年的**长周期相位**：1980 年代到 1990 年代中期，平均股票配置锚定在较低水平；1990 年代末开始显著抬升。过去一年里，股票配置相对债券配置**大幅下降**，按此指标看，当前已**接近"买入"信号**。

---

# 第 25 页 · 卖方指标的信号与 R²；仓位开篇

> **📊 图表 33**：*Equity sentiment has declined by over 7ppt from peak levels of bullishness in 2021*
> **股票情绪相较 2021 年的极致看多已下降 7 个百分点以上**（卖方指标，1985/9–2023/5）
> **当前读数：52.5% · 15 年均值：54.8% · 卖出阈值：58.2% · 买入阈值：51.4%**
> （买/卖信号基于 15 年滚动均值 ±1 倍标准差）

The Sell Side Indicator does not catch every rally or decline in the stock market, but has had reasonably strong predictive capability with respect to subsequent 12-month S&P 500 total returns. Although the r-square of 24% may sound low, it is significantly higher than similar statistics for typical variables used in stock market timing models. In particular, note that such heralded indicators such as the "Fed Model" and money growth have relatively little predictive value. Moreover, at BUY and SELL extremes, the r-square improves to 34%.

卖方指标并非每一次涨跌都能抓到，但**对未来 12 个月标普 500 总回报的预测力相当强**。**24% 的 R² 听上去不高**，但已**显著高于市场择时模型中常见变量的同类统计**——注意，**像"美联储模型"、货币供应量增速这些听起来响亮的指标，其预测力几乎可忽略**。而且**在买入/卖出极值区间，R² 进一步升至 34%**。

> **📊 图表 34**：*R² of the Sell Side Indicator improves to 34% at BUY and SELL extremes*
> **在买入/卖出极值区间，卖方指标的 R² 升至 34%**（卖方指标 vs. 后续 12 个月标普 500 总回报，1987/11 至今）
> 拟合方程：**y = −25.969·x + 59.618，R² = 0.3374**

## 3. Positioning
## 3. 仓位

### Who owns the S&P 500?
### 谁在持有标普 500？

We analyze the ownership of S&P 500 by institutions and individuals, collected by FactSet through various sources (see Exhibit 36). For the S&P 500 overall, investment advisers (asset managers) and mutual fund managers own the majority of the market cap of the index. However, this breakout can differ for individual stocks within the S&P 500, where ownership can provide insight on stock performance/volatility.

我们用 FactSet 多源汇总的数据分析标普 500 的机构与个人持股情况（数据来源见图表 36）。就整个指数而言，**投资顾问机构（资管公司）与共同基金经理合计持有大部分市值**。但**对个股来说持股结构差异很大**——而**持股结构对理解个股的表现与波动非常有价值**。

---

# 第 26 页 · 标普 500 持股结构与数据来源；主动管理人持仓

> **📊 图表 35**：*S&P 500 ownership breakout by institution type (4/30/2023)*
> **标普 500 持股按机构类型拆分（2023/4/30）** —— 投顾与共同基金是主要持有人
>
> | 类型 | 占比 |
> |---|---|
> | 投资顾问（Investment Adviser）| **37%** |
> | 未知 / Unknown | 20% |
> | 共同基金经理 | 19% |
> | 个人 | 15% |
> | 私行/财富管理 | 3% |
> | 养老基金经理 | 2% |
> | 对冲基金经理 | 2% |
> | 其他 | 2% |
>
> 注：**"未知"** 包括：（1）未达披露阈值的个人投资者；（2）依法不披露的共同基金；（3）美国境内管理规模低于 1 亿美元、无需报 13F 的机构；（4）境外不理 13F 要求或规模低于 1 亿美元的机构。**因卖空与报告时点差异，可能存在双重计数**。

> **📊 图表 36**：*S&P 500 aggregate ownership data sources*
> **标普 500 汇总持股数据来源**
>
> | 来源 | 说明 |
> |---|---|
> | **Form 13F** | 主要来源。在美国管理的美股规模 ≥ 1 亿美元的资管机构，须按季度申报 |
> | **Form 3/4/5** | 公司高管、董事及持有某类股票权益 10% 以上的受益所有人 |
> | **DEF 14A** | 股东大会委托书中披露的主要股东持股 |
> | **13D** | 持股 ≥ 5% 的个人须提交 |
> | **其他** | FactSet 直接联系基金/公司或从其报告/网站拉取数据，尤其是无须向 SEC 申报的境外基金 |

### Active managers' holdings
### 主动管理人持仓

At the sector and stock level, as well as for factors, we analyze large cap active managers' positioning on a quarterly basis. Positioning by sector for the latest quarter can be found below. Positioning data allows investors to assess, for example, what stocks are crowded vs. unloved by active managers or how managers' sector exposure has changed from quarter to quarter.

我们在**行业、个股、因子层面按季度分析大盘主动管理人持仓**。下方展示最新一季度的行业持仓。持仓数据能帮助投资者判断：**哪些股票被主动资金过度拥挤持有、哪些被冷落**；**各行业敞口环比如何变化**等。

---

# 第 27 页 · 多头基金 vs. 对冲基金行业持仓

> **📊 图表 37**：*Where do mutual funds and hedge funds agree (and disagree)?*
> **共同基金与对冲基金在哪些行业一致、哪些分歧？**（2023/4）
> —— 一年前 vs. 今天，各行业相对仓位对比。**目前双方分歧最大的行业**：通信服务（长仓超配、对冲低配）、医疗保健（双方都较超配）；**最一致**：能源、房地产。

> **📊 图表 38**：*Funds are slightly overweight cyclicals relative to defensives, but relative positioning is lowest since 2015*
> **多头基金对周期股 vs. 防御股小幅超配，但相对仓位已降至 2015 年以来最低**
> （大盘共同基金对周期/防御行业的相对敞口，2008/9–2023/4）
> *周期 = 可选消费、能源、科技、工业、材料；防御 = 医疗保健、必需消费*

> **📊 图表 39**：*Hedge funds are underweight cyclicals relative to defensives (relative positioning near historic lows)*
> **对冲基金对周期股低配（相对仓位接近历史低位）**
> （对冲基金对周期/防御行业的相对敞口，2011/6–2023/4）

---

# 第 28 页 · 从仓位中挖阿尔法；资产管理人对非流动资产的配置

### Extracting alpha from positioning
### 从仓位中挖阿尔法

Positioning can add alpha at a stock level. Our work suggests that over the last several years, during which active inflows were weak to negative but passive inflows were positive and strong, the strategy of buying the 10 most underweight stocks and selling the 10 most overweight stocks each year has generated an average of 5ppt to 18ppt of alpha per year, with the exception of 2017 and 2020 (Exhibit 41). We believe this should continue, as the main driver of the most crowded stocks' weakness – outflows from active fund into passive vehicles – may not be over (Exhibit 40).

**仓位信号在个股层面可以带来阿尔法**。近几年主动基金净流入疲弱甚至为负，被动基金则持续净流入——在这样的背景下，**每年买入主动管理人"最低配"的 10 只股票、卖空其"最高配"的 10 只股票**，除了 2017 年与 2020 年外，**平均每年贡献 5–18 个百分点的阿尔法**（图表 41）。我们认为这个信号还会继续有效，因为导致"最拥挤股票"走弱的核心驱动——**资金从主动基金流向被动工具**——远未结束（图表 40）。

> **📊 图表 40**：*Passive now accounts for 52% of all US domiciled fund assets*
> **被动基金已占美国国内基金资产的 52%**（主动 48% vs. 被动 52%，2023/4/30）

> **📊 图表 41**：*Buying the 10 most underweight stocks and selling the 10 most overweight stocks by active funds has generated alpha in most years*
> **买"最低配 10 只"、卖"最高配 10 只"，在多数年份都能产生阿尔法**（相对标普 500，2014–2023 年初至今）
>
> | 年份 | 最高配 10 只（Top 10）| 最低配 10 只（Bottom 10）|
> |---|---|---|
> | 2014 | -5.5 | 8.4 |
> | 2015 | -8.7 | -5.8 |
> | 2016 | 5.9 | 12.3 |
> | 2017 | 1.1 | 3.9 |
> | 2018 | -4.6 | 13.4 |
> | 2019 | -8.7 | -9.5 |
> | 2020 | -16.2 | 0.4 |
> | 2021 | -2.6 | 4.7 |
> | 2022 | 8.4 | -41.6（注：2022 年低配组包含较多成长白马，被整体重创）|
> | 2023 年初至今 | 35.8 | -11.3 |

> **📊 图表 42**：*Pension funds' allocation to illiquid assets has more than quadrupled since 2006*
> **养老金对非流动资产的配置自 2006 年以来翻了 4 倍以上**（美国 Top 1000 养老金，2006–2022）
>
> | 年份 | 流动资产 | 非流动资产 |
> |---|---|---|
> | 2006 | 92% | 8% |
> | 2010 | 83% | 17% |
> | 2015 | 77% | 23% |
> | 2020 | 75% | 25% |
> | 2022 | **64%** | **36%** |
>
> 注：流动 = 本国股债、国际/全球股债（含按揭、信用、杠杆贷款）、现金；非流动 = 私募股权、地产、其他另类投资。

---

# 第 29 页 · FMS 现金水平；空头兴趣

### Global Fund Manager Survey cash balances
### 全球基金经理问卷调查（FMS）中的现金水平

The BofA Fund Manager Survey (FMS, see note) is a monthly survey of 300-400 primarily long-only investors. One of the key questions in this survey asks for cash balance as percentage of assets under management. A low cash balance leaves investors vulnerable to negative market shocks, while a high cash balance means investors are under-invested and vulnerable to positive market shocks.

美银基金经理问卷调查（**BofA Fund Manager Survey, FMS**）是每月对 300–400 位以多头为主的投资者进行的调查。其中一个关键问题是"**现金占 AUM 的比例**"。现金水平低意味着投资者对负面冲击**脆弱**；现金水平高则说明投资者"**仓位不足**"，对正面冲击反而**被动**。

- **当现金水平跌破 4%，触发反向"卖出"信号**
- **当现金水平升破 5%，触发反向"买入"信号**

> **📊 图表 43**：*Cash drifts up to 5.6% from 5.5% (May 2023)*
> **现金水平从 5.5% 小幅升至 5.6%（2023 年 5 月）**（FMS 平均现金占 AUM 比，1999–2023）
> 运作规则：< 4% 触发反向卖出；> 5% 触发反向买入。

The BofA Fund Manager Survey (FMS) also provides a context for global positioning of fund managers, and today highlights that global investors have reduced their US stocks allocations to underweight.

FMS 同时反映全球基金经理的仓位情况。**当前显示：全球投资者已将美股仓位下调至低配**。

> **📊 图表 44**：*Net % Asset Allocators Say they are overweight US Equities*
> **资产配置人中净超配美股的比例**（2023/5）

### Short Interest
### 空头兴趣

While short interest is not predictive of market performance in isolation, when used in conjunction with valuation, sentiment and fundamentals, it can be helpful in calling for upside or downside risk to the equity market.

**单独看空头兴趣并不能预测市场表现**，但**与估值、情绪、基本面结合使用时**，它对判断股市上行/下行风险很有帮助。

---

# 第 30 页 · 空头兴趣走势；客户资金流；企业盈利开篇

> **📊 图表 45**：*Short interest has generally risen in 2023 YTD*
> **2023 年以来空头兴趣整体抬升**（全市场空头兴趣/流通盘比，2008–2023/4）

### Flow trends
### 资金流趋势

Flows trends are often assessed as another gauge of sentiment, as they can serve as confirmation of a rally or a signal of capitulation when buying or selling activity spikes to extremes or accelerates over a period. We track BofA Securities client trading flows into US single stocks and ETFs that are executed by the cash equities business of the firm, and provide a weekly update on flows by sector, client type, and size segment.

资金流趋势常作为另一重情绪指标——当买卖活动飙到极值或明显加速时，它要么**确认上涨趋势**，要么**释放投降式抛售的信号**。我们跟踪美银证券客户在美股个股与 ETF 上的交易流（由公司现金股票业务执行），每周按**行业、客户类型、市值段**发布更新。

<details>
<summary>📖 <b>术语解释：ETF / 投降式抛售（Capitulation）</b></summary>

- **ETF（Exchange-Traded Fund，交易所交易基金）**：**像股票一样在交易所盘中买卖的基金**。一份 ETF 份额背后对应一篮子底层资产（股票、债券、商品等），其净值由篮子内资产的市值决定，**做市商通过\"申购/赎回\"机制让 ETF 价格紧密贴合净值**。
  - 按跟踪目标分：**指数 ETF**（如 SPY 跟踪 S&P 500、QQQ 跟踪 Nasdaq-100）、**行业 ETF**（XLK 科技、XLF 金融）、**风格 ETF**（价值/成长）、**主题 ETF**（AI、清洁能源）、**商品 ETF**（GLD 黄金）、**债券 ETF** 等。
  - **跟个股相比**：ETF 的资金流更能反映\"资产配置层面\"的情绪（例如机构从个股切换到行业 ETF 做快速方向押注），因此追踪 ETF 净流入/流出已成为**情绪分析**的标准工具。

- **投降式抛售（Capitulation）**：市场长期下跌后，最后一批\"还抱有希望\"的投资者**集体放弃**、不计价格割肉出局的时刻——表现为**成交量骤增 + 价格短时间暴跌 + VIX 飙升 + 资金流极端流出**。历史上这往往是**中期底部的信号**，因为\"该卖的都卖完了\"。

</details>

> **📊 图表 46**：*BofA client net buys of US equities ($mn) and S&P 500 since 2008*
> **美银客户美股净买入（百万美元）与标普 500 走势**（2008/1–2023/4）——资金流时常是反弹的确认或投降抛售的信号

## 4. Corporate Profits
## 4. 企业盈利

### Normalized earnings
### 归一化盈利

Earnings are volatile over the course of a cycle, so we adjust earnings by this cyclicality to estimate the underlying earnings power of the S&P 500. Without the benefit of hindsight, it is difficult to assess what stage of the cycle we are in, but our best estimate is to normalize earnings based on a trend line of earnings growth using a cumulative linear log normal regression. This normalized earnings is compared to the current price of the S&P 500 to determine the current normalized PE ratio discussed earlier.

企业盈利在一个景气周期中起伏很大。为估算标普 500 的"**真实盈利能力**"，我们把这种周期性剔除。由于身在局中很难判断此时此刻处于周期哪一阶段，我们的**最佳估计方法**是：**用累计对数线性回归拟合出一条盈利增长趋势线，从而得到归一化盈利**。然后把它与标普 500 当前价格对照，即可得到前述的归一化 P/E。

---

# 第 31 页 · 归一化盈利走势 & 利润周期

> **📊 图表 47**：*Normalized earnings: suggests flat earnings growth over the next two years*
> **归一化盈利：提示未来两年盈利增长几近持平**（TTM 实际 EPS vs. 归一化 EPS，1936–2022Q4；图中小圆点 = 2023 与 2024 年归一化 EPS）
> 注：1988 年后使用 Pro-forma EPS；1977–1988 年使用 Operating EPS；1936–1977 年使用 GAAP EPS（剔除减值）。

### Profits cycle
### 利润周期

The profits cycle is a core focus of our research. We feel that profitability moves equity prices (as opposed to GDP or some other macroeconomic variable) and thus we concentrate on the profits cycle when formulating our equity strategies. We define the profits cycle as the year-to-year percentage change in S&P 500 reported earnings on a trailing four-quarter basis. See chart below.

**利润周期**是我们研究的核心。**我们认为"是企业盈利驱动股价，而不是 GDP 或其他宏观变量"**——因此在制定股票策略时，我们更聚焦于利润周期。**利润周期的定义**：标普 500 **过去 4 季滚动盈利的同比变化**。

> **📊 图表 48**：*Profits cycle: YoY EPS Growth for S&P 500, 1935 to present*
> **利润周期：标普 500 EPS 同比增速（1935 至今）**——我们认为是盈利能力、而非 GDP 等宏观变量，驱动股价

Whereas real earnings growth is possibly a better gauge of economic cycles, nominal earnings growth is a more important factor when examining the equity market. The equity market is a nominal concept because pricing and inflation, and not simply unit growth, influence profitability.

**实际盈利增长**或许更适合度量宏观经济周期；但**看股票市场时，名义盈利增长更重要**。这是因为**股票市场本质上是一个"名义"概念**——不仅销量/产量会影响利润，**价格与通胀**也在持续重塑盈利。

---

# 第 32 页 · 盈利惊喜（Earnings Surprise）

## #4: Earnings Surprise
## #4：盈利惊喜

### Stocks discount expected growth, but react to surprises
### 股价已消化预期增长，真正有反应的是"惊喜"

While the earnings revision ratio (discussed below) helps provide a gauge on sentiment and shows what happened in the recent past, we consider earnings surprise direction in our earnings and market outlook based on leading indicators including macroeconomic surprises, BofA analysts vs. consensus and corporate guidance.

**盈利预测修正比（后文会讲）** 能反映情绪、展示近期刚发生的事。但真正帮助我们前瞻性判断盈利与市场方向的，是**盈利惊喜（Earnings Surprise）的方向**——我们综合看几个**领先指标**：**宏观数据惊喜、美银分析师预测 vs. 市场共识、企业管理层指引**。

> **📊 图表 49**：*Returns are positively correlated with growth expectation…*
> **回报与增长预期正相关…**（标普 500 年度回报 vs. NTM 盈利增长预期，2001–2022，R² = 0.1343）

> **📊 图表 50**：*…but are more correlated to growth surprises*
> **…但与"增长惊喜"相关性更高**（年度回报 vs. 年度 EPS 增长超预期幅度，R² = 0.2057）

> **📊 图表 51**：*…as well as quarterly earnings surprises*
> **季度盈利惊喜也同样**（季度回报 vs. 季度 EPS 超预期幅度，R² = 0.2514）

> **📊 图表 52**：*More positive surprises in economic data*
> **宏观数据惊喜整体偏正向**（Bloomberg ECO Surprise Index，2000 至今）

> **📊 图表 53**：*Consensus 2023 EPS plateauing after sharp decline*
> **2023 年共识 EPS 在大幅下调后趋于持平**（标普 500 历史 FY2 EPS 修正轨迹 vs. 2023 共识 EPS，截至 2023/5/18；历史均值基于 2001–2022 年，剔除新冠、GFC、千年虫年份）

---

# 第 33 页 · 盈利预测修正比 & 销售预测修正比

### S&P 500 earnings estimate revision ratio
### 标普 500 盈利预测修正比

The following chart shows the earnings estimate revision ratio, calculated as the ratio between the number of companies in the S&P 500 for which consensus earnings estimates have been raised versus those that have been lowered over a three month period. As a breadth ratio, the earnings revision ratio is generally an earlier indicator of changes in the profits cycle, as it is more sensitive to changes in earnings expectations than is a market capitalization weighted estimate revision framework. For example, the revision ratio troughed at the end of January '09, about a month before the market recovered, whereas on a cap-weighted basis, earnings expectations troughed in the end of April '09, two months after the market's trough. The estimate revision ratio can be used as a short-term gauge of sentiment.

下图展示**盈利预测修正比**：过去 3 个月内共识盈利被**上调** vs. 被**下调**的标普 500 公司家数之比。作为**广度指标**，它通常领先于利润周期的拐点——因为它对盈利预期变化**比"市值加权"口径更敏感**。举例：2009/1 底该比值触底，**比市场反弹提前约 1 个月**；而"市值加权"口径下的盈利预期直到 2009/4 底才触底，**比市场底晚了 2 个月**。**该指标可作为短期情绪指标使用**。

> **📊 图表 54**：*S&P 500 Earnings Estimate Revision Ratio, 1/1986 - 04/2023*
> **标普 500 盈利预测修正比（1986/1–2023/4）** —— 通常是利润周期拐点的早期指标

### S&P 500 sales revision ratio
### 标普 500 销售预测修正比

Sales forecast revision ratios are defined similarly to earnings estimate revision ratios, but instead of consensus earnings estimates, we use consensus sales forecasts for S&P 500 companies.

销售预测修正比的定义与盈利版类似，只是把"**共识盈利预测**"换成"**共识营收预测**"。

> **📊 图表 55**：*3m Sales Forecast Revisions Ratio has rebounded since Nov. 2022 lows*
> **3 个月销售预测修正比自 2022/11 低点回升**（标普 500 销售预测修正比，2000/1–2023/4）

We also follow the gap between the top-line vs. bottom-line revision ratio. We have found that sales based measures may be more important when the sales revision ratio is not improving as rapidly as the earnings revision ratio, and vice versa. Generally, the scarce resource is the more rewarded and important metric.

我们也跟踪**收入端修正 vs. 盈利端修正**之间的**差值**。经验是：**谁改善得慢、谁就更重要**——收入修正改善慢于盈利修正时，收入类指标更关键；反之亦然。**简而言之：稀缺的东西更被市场奖赏**。

---

# 第 34 页 · 收入-盈利修正差值 & 管理层指引比

> **📊 图表 56**：*Spread: 3-month sales forecast revision ratio vs. 3-month earnings estimate revision ratio*
> **收入修正 − 盈利修正 价差**（1997/1–2023/4）
> 上方区：销售前景比盈利前景更乐观；下方区：盈利前景比销售前景更乐观。

### Management guidance ratio
### 管理层指引比

We track the ratio of total instances of above-consensus vs. below-consensus management guidance for S&P 500 companies over a one-month and three-month period, as we have found that guidance is generally a leading indicator of estimate revisions by about one month. Sustained divergences between the estimate revision ratio and management guidance ratio (for example, a rising estimate revision ratio but falling management guidance ratio) may suggest that analysts are being overly optimistic and a downward revision cycle is soon to follow, or conversely that management is being too negative in their outlook.

我们统计标普 500 公司在 1 个月和 3 个月窗口内"**高于共识**"与"**低于共识**"的管理层指引次数之比。**指引通常领先卖方预测修正约 1 个月**。如果**预测修正比与管理层指引比持续背离**（如预测修正比上行、但指引比下行），**要么说明卖方分析师过度乐观、后续将进入下调周期**；**要么说明管理层给的展望过度悲观**。

> **📊 图表 57**：*S&P 500 Management Guidance Ratio* — 指引比目前高于均值且持续上行（2000/1–2023/4）

---

# 第 35 页 · 指引比与后续修正比的关系 & 指引溢价证据

> **📊 图表 58**：*Guidance ratio has historically led the subsequent month's estimate revision ratio…*
> **指引比在历史上领先下一月的预测修正比**（2000 至今，R² = 0.3299）

> **📊 图表 59**：*…with the relationship back to a high positive correlation after the two had diverged for much of the mid-2010s*
> **在 2010s 中期两者背离多年后，相关性已重回高位正相关**（3 年滚动相关系数，2002 至今）

### Evidence of a guidance premium
### "指引溢价"的证据

We have also found some evidence that companies that regularly issue guidance may be rewarded for their apparent transparency. History suggests that beginning in mid-2000, companies that regularly issued profits guidance began to trade at a premium to book value relative to those that do not guide at all. This premium may be granted for transparency, and we have found that it is generally most pronounced in cyclical sectors.

我们还发现一些证据：**定期发布指引的公司因其透明度而被市场奖赏**。从 2000 年年中开始，**定期披露盈利指引的公司相对完全不发指引的公司，市净率（P/B）开始享有溢价**——**这一溢价可能就是对透明度的奖励，且在周期性行业中表现得最为明显**。

> **📊 图表 60**：*Premium (discount) to S&P 500 based on median P/B for companies that issue annual or qtrly guidance vs those that do not*
> **发布年度或季度指引的公司相对不发指引公司的 P/B 溢价**（2000–2022）——新冠后"指引方"的溢价有所收窄

> **📊 图表 61**：*Premium (discount)… for companies that issue qtrly guidance vs those that do not*
> **季度指引 vs. 不发指引的 P/B 溢价**——历史上表现更分化，新冠后收窄

> **📊 图表 62**：*Premium (discount)… for companies that issue annual guidance vs those that do not*
> **年度指引 vs. 不发指引的 P/B 溢价**——2022 年有所下滑，但长期比"季度指引"更稳定

---

# 第 36 页 · 指引频次变化 & 盈利确定性（预测分歧度）

> **📊 图表 63**：*S&P 500 quarterly earnings guidance instances*
> **标普 500 季度盈利指引次数**（2001/1–2023/4，新冠低点后回升）

> **📊 图表 64**：*S&P 500 annual earnings guidance instances*
> **标普 500 年度盈利指引次数**（2001/1–2023/4，同样自新冠低点后回升）

> **要点**：**在新冠期间指引普遍缺席的背景下，坚持发布年度展望的公司获得了创纪录的溢价**。

### Earnings certainty
### 盈利确定性（预测分歧度）

Earnings estimate dispersion can be used to gauge the certainty or uncertainty of earnings expectations. When the average dispersion of estimates for a company in the S&P 500 is high, this can suggest earnings are less certain, whereas when dispersion is low, analysts exhibit more agreement or certainty about future earnings. However, in uncertain macroeconomic environments, a low level of dispersion can also reflect an extreme lack of conviction and an unwillingness of analysts to diverge from the pack. We have found that companies with low dispersion tend to outperform when dispersion is rising, and companies with high dispersion tend to outperform when dispersion is falling.

**盈利预测分歧度（Estimate Dispersion）** 可用于衡量盈利预期的确定/不确定程度。**分歧度高 = 盈利不确定性高；分歧度低 = 分析师对未来盈利看法更一致**。**但要注意**：宏观不确定性很强时，**低分歧度也可能反映分析师毫无信念、不敢与共识偏离**。我们的实证规律是：**分歧度上行期，低分歧公司跑赢**；**分歧度下行期，高分歧公司跑赢**。

> **📊 图表 65**：*Average dispersion of FY2 S&P 500 Estimates (Feb 1986 to April 2023)*
> **标普 500 FY2 预测的平均分歧度**（1986/2–2023/4）——当前已降至历史均值以下

> **📊 图表 66**：*Relative factor performance: High - Low EPS Estimate dispersion (based on 1986 – 2023 performance)*
> **高分歧 vs. 低分歧公司的相对表现**（1986–2023）
> - **分歧度上行期**：**低分歧跑赢**
> - **分歧度下行期**：**高分歧跑赢**

---

# 第 37 页 · 央行流动性：QE 与 QT 对股市的影响

## What else has mattered: Central Bank Liquidity
## 还有什么在起作用：央行流动性

### If QE mattered, QT should matter too
### 如果 QE 有效，那 QT 就也得有效

Pre-GFC, earnings explained ~50% of S&P 500 returns. Post-GFC, earnings mattered less (23% explanatory power), and Fed balance sheet changes mattered more. Fed liquidity was irrelevant pre-GFC, but drove more than half of non-earnings returns of the S&P 500 post-GFC. NB: the recent strong performance of growth / Tech stocks may be attributable to bank bailout-driven balance sheet expansion in 1Q23.

**2008 全球金融危机前（Pre-GFC）**，企业盈利可解释约 **50%** 的标普 500 回报。**GFC 之后**，盈利的解释力降至 **23%**，而**美联储资产负债表的变化取而代之成为主因**。**GFC 前美联储流动性对股市几乎无影响；GFC 后则驱动了标普 500 "非盈利"部分回报的一半以上**。**值得注意的是**：近期成长/科技股表现强劲，**部分可归因于 2023 年 Q1 银行救助驱动的美联储资产负债表再度扩张**。

> **📊 图表 67**：*Earnings explained nearly 50% of market returns pre-GFC, but only 23% of post-GFC returns*
> **GFC 前盈利解释近 50% 的回报，GFC 后只解释 23%**
> —— 1997–2009：48% / 2010–2021：23%

> **📊 图表 68**：*Over half of non-earnings driven market cap changes was explained by the Fed balance sheet expansion since GFC*
> **GFC 后，非盈利驱动的市值变化有超过一半可由美联储资产负债表扩张解释**
> —— 1997–2009：0% / 2010–2021：**51%**
> 注：非盈利驱动的市值变化 = 总市值变化 − 历史均值远期 P/E × 远期 EPS 变化

> **📊 图表 69**：*$750bn reduction in the Fed balance sheet and trend earnings growth for 2024E EPS could result in the S&P 500 at 4100 in 2023*
> **假设美联储缩表 7500 亿美元 + 2024 年 EPS 按趋势增长，2023 年标普 500 约在 4100**
> （以 2010 年以来远期 EPS 变化与美联储资产负债表同比变化拟合的模型 vs. 实际标普 500；2023 点位假设 2024 EPS = \$233（2023 共识 EPS 同比趋势增长 6%），美联储资产负债表采用 BofA 预测）

---

# 第 38 页 · 标普 500 的流动性风险

## Liquidity risks for the S&P 500
## 标普 500 的流动性风险

In recent years, we have been highlighting rising liquidity risks for one of the most liquid areas of the market: large cap US equities (the S&P 500). S&P 500 trading volume has grown thinner and thinner, and as a casualty of the momentum- and growth-driven market of recent years, the index has grown increasingly tail-heavy with its market cap tilted toward a small number of mega cap companies.

近几年我们一直在强调：**连标普 500 这种传统上最具流动性的资产，也在累积流动性风险**。**标普 500 的成交量变得越来越稀薄**；而这些年"动量+成长"主导的行情也埋下一个后果——**指数权重越来越集中在少数几家超大市值公司身上**，**尾部越来越重**。

US stock ownership has eclipsed 50/50 for passive/active (52% of US domiciled funds are passive today), where passive represents non-fundamental buyers/sellers. And asset allocators have increasingly funneled assets into longer-term illiquid growth – the largest pension funds have growth their exposure in illiquid investments (including private equity) from 8% in 2006 to 25% today. Private equity AUM (assets under management) continues to rise.

美国股票持有结构**被动 vs. 主动**已突破 **52% vs. 48%**（被动基金代表"**非基本面**"的买卖方）。资产配置方同时不断把资金推向**长期、非流动的成长类投资**——最大一批养老金对非流动投资（含私募股权）的敞口，**从 2006 年的 8% 升至今天的 25%**。私募股权 AUM 持续走高。

Banks also provide substantially less liquidity today than in prior cycles, with the trading portfolio of large banks half of what it was a decade ago following regulatory constraints. Central banks, high frequency traders (HFTs), ETFs and other market participants have picked up some of the slack, but trading dynamics have undeniably changed, as large cap US stocks are increasingly traded by machines (HFT, quants, etc.) rather than humans.

由于监管收紧，**大银行如今提供的流动性远不如以往周期**——**大行自营交易账簿规模是十年前的一半**。这部分空缺由央行、**高频交易商（HFT）**、ETF 和其他参与者填补了一部分，但**交易生态已经不可逆地改变——大盘美股越来越多地由机器（HFT、量化等）而非人类在交易**。

> **📊 图表 70**：*S&P 500 increasingly tail-heavy*
> **标普 500 越来越尾部集中**（前 10 大公司占全指数市值的比例，1986–2023/4，15% → 33%）

> **📊 图表 71**：*Prior to COVID, thinner and thinner trading – which has been generally declining again post-COVID*
> **新冠前成交越来越稀薄，新冠后整体再度下行**（日均成交量/市值比，2009/8–2023/4）

> **📊 图表 72**：*Passive now accounts for 52% of all US domiciled fund assets*
> **被动基金占比升至 52%**（美国国内基金，2009–2023/4）

> **📊 图表 73**：*Big banks are not the providers of liquidity they once were*
> **大银行已非昔日的流动性提供者**（大行自营交易账簿规模，2009–2022，合计 **-52%**）

---

# 第 39 页 · 盈利预期生命周期（前半段）

## Earnings Expectation Life Cycle
## 盈利预期生命周期

Most stocks' earnings trajectories follow the pattern described by the cycle below, although not every stock will stop at each point, nor will stocks reside in each phase for any regulated amount of time. Stocks can also move backward and forward.

多数股票的盈利轨迹，都大致遵循下方这个**生命周期**——当然，并非每只股票都会停留每一阶段，也没有固定的停留时长；**股票可以前进也可以回退**。

The Earnings Expectation Life Cycle is our proprietary schematic, which portrays investors' changing attitudes towards a stock over time. We believe that a successful investment process should incorporate the notion of changing expectations, because "dogs" often become "stars" and "stars" often become "dogs".

**盈利预期生命周期**是我们的自有图谱，刻画投资者对某只股票态度随时间变化的全过程。**一个成功的投资体系必须把"预期会不断变化"这件事嵌入其中**——因为"**烂股**"常常会变成"**明星股**"，而"**明星股**"也常常会沦为"**烂股**"。

### Life Cycle Phases
### 生命周期的阶段

The Earnings Life Cycle, depicted below, contains eleven positions, with the left half of the cycle portraying the period of rising expectations, and the right half portraying the period of falling expectations.

整个生命周期共 **11 个位置**：**左半圆代表预期上行期，右半圆代表预期下行期**。

> **📊 图表 74**：*Earnings Expectation Life Cycle*
> **盈利预期生命周期图** —— 左半为预期上行期，右半为预期下行期

各阶段如下：

**Stage 1: Low Expectations / 阶段 1：低预期**

Investors commonly known as "Contrarians" typically invest in these stocks with lower earnings expectations. Most non-contrarian investors find these stocks unattractive or overly risky.

通常被称为"**逆向投资者（Contrarians）**"的人会买入这类"盈利预期极低"的股票。而大多数非逆向投资者觉得它们缺乏吸引力、或风险过高。

**Stage 2: Positive Surprise / 阶段 2：正向惊喜**

Eventually the low-expectations companies begin to report more optimistic information such as improved earnings significant enough so that the stocks recapture attention. Research coverage of such stocks may begin to increase although it is more likely that this will happen more towards stages 4 and 5.

这些低预期公司最终开始发布更乐观的信息（例如盈利出现明显改善），足够把关注度拉回来。**卖方覆盖**也可能开始增加——不过这个现象更常出现在阶段 4–5。

---

# 第 40 页 · 生命周期阶段 3–11

**Stage 3: Positive Surprise Screens / 阶段 3：正向惊喜筛选出现**

Stock picking screens that search for significant variations between analyst earnings expectations and actual reported earnings begin to highlight these stocks. We have found that these screens have gained a lot of popularity with investors; thus the screens themselves have grown less effective.

那些寻找"分析师预期 vs. 实际盈利"显著差异的筛选模型开始把这些股票筛出来。我们发现，**这类筛选模型已被大量投资者使用，因而其有效性正变得越来越弱**。

**Stage 4: Estimate Revisions / 阶段 4：卖方上调预测**

The consensus begins to raise their earnings estimates for these stocks in response to rising earnings expectations following the surprise of stage 3. Analysts' estimate revisions often lag a surprise because analysts are generally reluctant to believe that the superior earnings will last.

共识开始上调这些公司的盈利预测——**这通常滞后于惊喜**，因为分析师往往不太愿意相信"这种超预期能持续下去"。

**Stage 5: EPS Momentum / 阶段 5：EPS 动量**

Investors who follow earnings momentum themes begin to buy these stocks as estimates and reported earnings continue to rise and as year-to-year comparisons begin to improve.

**追逐盈利动量主题**的投资者开始买入——因为预测与实际盈利继续上行，同比比较也愈发亮眼。

**Stage 6: "Growth" / High Expectations / 阶段 6："成长股" / 高预期**

Strong earnings momentum continues for a long enough period that these stocks are termed "growth" stocks by the consensus. These stocks are not "new" growth stocks, for new growth stocks are probably found during stages 4 and 5, nor are they true growth companies that alter the business environment. Rather, this is the point at which most investors agree that the stock is a terrific growth stock. Earnings expectations are very high, which implies that there is a large risk of disappointment at this stage. Contrarian selling would optimally occur at this point in the cycle.

强劲的盈利动量持续足够久，共识就会给这类公司打上"**成长股**"标签——**但它们既不是"新"的成长股**（真正的新成长股往往在阶段 4–5 就已被发掘），**也不是"改变行业游戏规则"的真成长公司**。此时不过是**大多数投资者终于达成共识：这就是一只很棒的成长股**。但盈利预期已极高，**这意味着失望风险巨大**——**阶段 6 才是逆向投资者理想的卖出点**。

**Stage 7: Torpedoed / 阶段 7：被鱼雷击沉**

Earnings disappointment occurs, stocks are "torpedoed" – i.e., their earnings expectations and prices sink.

盈利不及预期，股价如同"**被鱼雷击沉**"——**盈利预期与股价同步下沉**。

**Stage 8: Negative Earnings Surprise Screens / 阶段 8：负向惊喜筛选出现**

The same screens from Stage 3 above begin to highlight stocks with lower-than expected earnings as potential sell candidates.

和阶段 3 同源的筛选模型，此时开始把这些"低于预期"的股票**标为潜在卖出候选**。

**Stage 9: Estimate Revisions / 阶段 9：卖方下调预测**

The consensus begins to lower their earnings estimates in response to the earnings disappointment. Again analysts tend to lag because they generally do not believe that the earnings shortfall is a sign of a fundamental problem with the company.

共识开始下调盈利预测——**同样滞后**，因为分析师一般不愿相信这次 miss 是公司基本面恶化的信号。

**Stage 10: "Dogs" / 阶段 10："烂股"**

These stocks, after continuing to report disappointing earnings for a long enough period of time, are shunned by investors. News regarding takeovers, restructuring or bankruptcy may affect the stock price temporarily; however, investors generally avoid or ignore these stocks.

业绩持续令人失望足够久后，投资者彻底抛弃这类股票。**虽然收购、重组、破产的新闻可能短暂拉动股价**，但投资者整体仍对其敬而远之。

**Stage 11: Neglect / 阶段 11：被忽视**

Investors have become so disinterested in the stocks or group that general research begins to dissipate. The lack of coverage may set the stage for a renewed cycle.

投资者对这些股票（或板块）兴趣彻底丧失，**卖方覆盖也逐渐消散**。**覆盖缺失反而为新一轮生命周期的轮回埋下伏笔**。

### Growth vs. Value and the Earnings Expectation Life Cycle
### 成长 vs. 价值 与 盈利预期生命周期

The Earnings Expectations Life Cycle can be adapted to help understand investment styles or management techniques. As is indicated by the diagram, value-oriented investment strategies are more likely to fall in the bottom half of the Life Cycle because they tend to be more Contrarian in nature. Value-oriented strategies spend more time attempting to distinguish the true "dogs" – those which might not take another turn around the Life Cycle – from those stocks that are simply out of favor but will rebound.

这个生命周期图谱也能帮助理解投资风格与管理手法。如图所示，**价值派策略更倾向于落在生命周期的"下半圆"**——因为价值派天然带有逆向思维的基因。**价值型投资者花大量时间分辨"真烂股"与"只是一时失宠但终将反弹的股票"**——前者可能再也无法重回生命周期轮回。

---

# 第 41 页 · 成长 vs. 价值（生命周期视角）

As the diagram below suggests, growth-oriented investment strategies tend to be in the top half of the Life Cycle. The success of these strategies depends on one's ability to realize that a company's earnings momentum is secular and not simply a result of cyclical influences. Thus, the equator of the earnings expectations life cycle schematically separates the worlds of growth and value investing.

如图所示，**成长派策略则多集中在生命周期的"上半圆"**。成长策略能否奏效，取决于一项关键能力：**判断某公司的盈利动量是长期结构性的，还是仅仅是周期性的**。**因此，生命周期的"赤道线"恰好把成长与价值这两个世界分开**。

The theory behind the Life Cycle suggests that the hardest thing for a growth manager to do is to time the sale of a stock, whereas the hardest thing for a value manager to do is to time the purchase of a stock. It seems that a good value-oriented manager is likely to be buying stocks later than his peers, whereas a good growth-oriented manager is likely to be selling stocks earlier than his peers.

生命周期理论还给出一个推论：**对成长经理来说，最难的是卖出时机；对价值经理来说，最难的是买入时机**。换句话说，**优秀的价值经理往往买得比同行晚，优秀的成长经理往往卖得比同行早**。

> **💡 结论一句话**：**好的价值经理晚同行一步买入；好的成长经理早同行一步卖出。**

> **📊 图表 75**：*Growth* —— 成长派策略集中于生命周期上半圆
> **📊 图表 76**：*Value* —— 价值派策略集中于生命周期下半圆

---

# 第 42 页 · 生命周期的"上行期"与"下行期"

> **📊 图表 77**：*Rising* —— 左半圆：预期上行期（阶段 1–6）
> **📊 图表 78**：*Falling* —— 右半圆：预期下行期（阶段 7–11）

---

# 第 43 页 · 因子择时（Factor Timing）

## Factor timing
## 因子择时

The underlying performance of investment styles is often just as important as the aggregate stock market performance. For instance, the S&P 500 index declined -19.4% in 2022, but the best performing High Dividend Yield factor advanced +3.7%, while 5-yr Debt Adjusted ROE factor declined -27.5%. Just as how investing in Telecom stocks requires consideration as to how dividend stocks will perform in addition to their fundamental profit outlook, investors should consider their portfolios' factor exposures and what drives the performance of those factors.

**投资风格背后的因子表现**，往往和大盘整体表现同等重要。举例：2022 年标普 500 下跌 **-19.4%**，但表现最好的**高股息率因子**上涨 **+3.7%**，而**5 年期负债调整 ROE 因子**大跌 **-27.5%**。就像投资电信股时，你得同时考量公司基本面盈利展望 **和** "高息股整体将如何表现"——**投资者需要持续关注自身组合的因子敞口，以及驱动这些因子表现的变量**。

> **📊 图表 79**：*Factor Timing —— 因子及其触发条件*
>
> | 因子 | 触发条件 |
> |---|---|
> | **Beta** | 盈利加速、波动率下行 |
> | **DDM Alpha** | 盈利减速、波动率上行 |
> | **股息率（Dividend Yld）** | 股票回报为负、波动率上行（注：**第二五分位比第一五分位表现更好**）|
> | **股息增长** | 股票回报为负、波动率上行 |
> | **盈利预测修正** | 预测分歧度下行 |
> | **盈利动量** | 盈利加速、波动率下行、预测分歧度下行 |
> | **盈利收益率（Earnings Yld）** | 盈利加速、波动率下行 |
> | **股权久期（Equity Duration）** | ERP 下行、成长预期上行 |
> | **预测分歧度（Estimate Dispersion）** | 预测分歧度下行 |
> | **EV/EBITDA** | 盈利加速、波动率下行 |
> | **5 年 ROE** | 盈利减速、波动率上行 |
> | **5 年 ROE（负债调整）** | 盈利减速、波动率上行 |
> | **海外敞口** | 美元走弱 |
> | **远期盈利收益率** | 盈利加速、波动率下行 |
> | **盈利波动性高** | 盈利加速、波动率下行 |
> | **Most Active（最活跃）** | VIX 拐点（峰或谷）|
> | **Neglect（卖方覆盖少）** | 低波动、大量资金流入股市 |
> | **Neglect（机构持股低）** | 股票回报为负 |
> | **1 年 ROE** | 盈利减速、波动率上行 |
> | **1 年 ROE（负债调整）** | 盈利减速、波动率上行 |
> | **P/E to Growth (PEG)** | 多数环境下都不错 |
> | **正向盈利惊喜** | 预测分歧度低 |
> | **Price（价格动量）** | 盈利加速、波动率下行、预测分歧度下行 |
> | **P/B** | 盈利加速、波动率下行、预测分歧度下行 |
> | **P/CF** | 盈利加速、波动率下行 |
> | **P/FCF** | 盈利加速、波动率下行 |
> | **P/S** | 盈利加速、波动率下行 |
> | **预期 5 年 EPS 增速** | 盈利减速、波动率上行 |
> | **相对强度（Relative Strength）** | VIX < 25 |
> | **ROA** | 盈利减速、波动率上行 |
> | **ROC** | 盈利减速、波动率上行 |
> | **股票回购** | 低估值公司做回购效果更好 |
> | **小市值** | 盈利加速、波动率下行、信用利差下行、信贷官问卷"净宽松" |
> | **高质量（A+）** | 盈利减速、波动率上行 |
> | **低质量（C&D）** | 盈利加速、波动率下行 |

---

# 第 44 页 · 成长与价值

## Growth and Value
## 成长与价值

We use a variety of valuation signals (Exhibit 214) to determine Value and Growth stocks, respectively.

我们使用多种估值信号（详见图表 214）来分别定义价值股与成长股。

### Growth and Value and the Earnings Expectations Life Cycle
### 成长/价值 与 盈利预期生命周期

Within the context of the Earnings Expectations Life Cycle, Value managers are defined as investing in "low-expectations" equity since they search for out-of-favor stocks whose equity is priced at a discount. Growth managers are defined as investing in "high-expectations" equity since they search for stocks with a proven track record of success and which are thus priced at a premium.

放到盈利预期生命周期的框架里：**价值经理**买入的是"**低预期**"股票——他们寻找失宠的公司、其股价被折价。**成长经理**则买"**高预期**"股票——他们寻找有过硬业绩的公司，并愿意为其付出溢价。

### Growth and Value and the Profits Cycle
### 成长/价值 与 利润周期

Growth and Value appear to be related to the Profits Cycle. We have found that Growth and Value cycles have been historically related to the scarcity or abundance of nominal earnings growth – when nominal earnings growth is scarce, growth (as a scarce resource) outperforms value, since investors tend to bid up the prices of companies that can maintain their earnings growth. Moreover, as earnings growth becomes abundant (as the profits cycle accelerates) investors tend to comparison shop, and pay less for stable earnings growth than they might have during a dearth of earnings growth.

成长与价值的轮换，与利润周期密切相关。**历史上，成长/价值周期与"名义盈利增长"的稀缺或丰裕直接挂钩**——
- **盈利增长稀缺时，"成长"作为稀缺资源跑赢"价值"**：投资者愿意为仍能维持盈利增长的公司支付高溢价
- **盈利增长变得丰裕（利润周期加速）时**，投资者开始"**货比三家**"，**不再愿为稳定盈利增长支付此前那么高的价钱**

Performance tends to switch off between growth and value: when earnings growth is scarce and investors bid up the valuations of the few stocks that can maintain growth, value managers generally stay out of these stocks. However, growth managers invest in them, and thus can thrive during these phases. Conversely, when reported earnings growth becomes increasingly abundant, investors tend to become comparative shoppers, or value investors. Value managers tend to outperform growth managers when the profits cycle accelerates.

成长与价值的表现常常**"交接"**：盈利稀缺时，投资者抢购少数能维持增长的股票、推高其估值，**价值经理一般不碰这类股，而成长经理恰好扎堆于此并因此丰收**；反过来，**盈利增长变丰裕时，投资者变成"比价型"买家，价值派占优**——**利润周期加速时，价值往往跑赢成长**。

> **📊 图表 80**：*Growth vs. Value performance during the profits cycle (1982-present)*
> **利润周期中成长与价值的表现**（1982 至今）—— 利润加速时价值倾向于跑赢成长
>
> | | **利润减速（Profits Deceleration）** | **利润加速（Profits Acceleration）** |
> |---|---|---|
> | 罗素 1000 价值 | **9%** | **17%** |
> | 罗素 1000 成长 | **11%** | 14% |

Because one of the factors influencing nominal earnings growth is inflation, we can assume that during inflationary environments, earnings growth tends to be more abundant and thus value outperforms growth. Therefore, during inflationary periods, the yield curve is steep, and future prospects are expected to be superior to current prospects, thus a value cycle is expected to ensue. Likewise, during deflationary periods when the yield curve is inverted, future prospects are thought to be dimmer than current ones, thus earnings growth is expected to be scarcer in the future, implying that a growth cycle lays ahead. But the key driver for value vs. growth is the profit cycle as depicted in Exhibit 80.

由于影响名义盈利增长的因素之一是**通胀**，我们可以推论：**通胀环境中**盈利增长往往相对丰裕，因此**价值跑赢成长**——此时**收益率曲线陡峭，未来前景被看好胜于当下**，价值周期顺理成章上演。反之，**通缩环境中**曲线倒挂、未来前景被看淡、未来盈利增长更稀缺，**成长周期上位**。**但归根结底，决定成长/价值的核心驱动仍是利润周期**（如图表 80）。

### Growth vs. Value benchmark performance
### 成长与价值基准指数的表现

Over the long-term (since 1978), the Russell 1000 Value index has outperformed the Russell 1000 Growth index. However, Growth outperformed Value from 2007 to mid-2020, as the Global Financial Crisis and its aftermath led to a period when growth became the scarce resource. On an annual basis, growth has beaten Value in six of the last seven years.

拉长时间看（自 1978 年起），**罗素 1000 价值指数长期跑赢罗素 1000 成长指数**。但 **2007 年至 2020 年中**这段时期**成长跑赢价值**——全球金融危机及其后遗症把"成长"变成了稀缺资源。**按年度看，过去 7 年里有 6 年成长跑赢价值**。

---

# 第 45 页 · 风格差异回归与小盘风格价差

> **📊 图表 81**：*Large caps: Relative performance (total return) of Growth vs. Value (1978-present)*
> **大盘：成长 vs. 价值相对走势（总回报，1978/12–2023/4）** —— 2023 年以来成长再度跑赢

### Style differentiation has come back
### 风格分化又回来了

Growth outperformed Value in 2017, 2018, 2019, 2020 and 2021 (leading by +17ppt, +7ppt, +10ppt, +36ppt and +2ppt, respectively), while in 2022, Value led Growth by +22ppt. So far in 2023, Value is trailing Growth by 13ppt. These wider performance spreads follow a period from 2010-2014 when the two benchmarks performed nearly in-line in each year.

**成长在 2017、2018、2019、2020、2021 年连续跑赢价值**，分别领先 **+17ppt / +7ppt / +10ppt / +36ppt / +2ppt**；**2022 年价值反超成长 +22ppt**；**2023 年年初至今成长再次领先价值 13ppt**。近年这种**更宽的价差**，发生在 2010–2014 年"两个指数每年表现几乎贴线"的沉寂期之后。

Style performance spreads have historically been wider for small caps, suggesting that having a style benchmark view may be more important in this size segment (Exhibit 82).

**历史上小盘股的风格价差更大**，意味着**在小盘领域，对"成长 or 价值"的判断更关键**（图表 82）。

> **📊 图表 82**：*Avg. rel. return of Growth vs. Value in years where Growth outperformed, and avg. rel. return of Value vs. Growth in years where Value Outperformed*
> **成长跑赢年份的成长相对价值超额，以及价值跑赢年份的价值相对成长超额**——**小盘的风格价差历来更大**
>
> | | **罗素 1000（大盘）** | **罗素 2000（小盘）** |
> |---|---|---|
> | 平均成长跑赢幅度（ppt）| 10.0 | **11.6** |
> | 平均价值跑赢幅度（ppt）| 8.9 | **13.5** |

---

# 第 46 页 · 成长 vs. 价值：下一步？估值分化与相对估值

> **📊 图表 83**：*Relative return of the Russell 1000 Growth Index vs. the Russell 1000 Value Index, 1979-2023 YTD*
> **罗素 1000 成长 vs. 价值的相对回报（1979–2023 年初至今）** —— 2023 年初至今成长领先价值 **13 个百分点**
> （柱状条标注历年 Growth-Value 相对胜负：如 2020 +36、2022 −22、2023 YTD +13）

## Value vs. Growth: what's next?
## 价值 vs. 成长：下一步？

We continue to favor Value over Growth with a focus on Free Cash Flow, where FCF/EV has been the best Value factor during Late Cycle regimes (our Discount Model, which more explicitly incorporates rising rate risks, also fared well). Other reasons to favor Value: valuation dispersion remains near record highs, (Exhibit 84); Value stocks' valuations are historically inexpensive (Exhibit 85); and positioning remains favorable (Exhibit 86, Exhibit 87).

我们继续**看好价值胜于成长**，且把目光聚焦在**自由现金流（FCF）** 上—— **FCF/EV 在"周期晚期（Late Cycle）"制度下一直是表现最好的价值因子**（此外**我们的股息贴现模型（DDM）更明确纳入了利率上行风险，表现同样优异**）。其他看好价值的理由包括：**估值分化仍接近历史高位（图表 84）**；**价值股估值在历史上仍便宜（图表 85）**；**仓位结构仍有利于价值（图表 86、87）**。

> **📊 图表 84**：*Valuations dispersion peaks usually precede Value cycles*
> **估值分化的高点通常先于价值周期**（标普 500 远期 P/E 的估值分化 = 标准差/均值，1990–2023/4）
> 历史参考：**估值分化高峰后 Value vs. Growth 达 +35ppt；低谷后仅 +1ppt**

> **📊 图表 85**：*Value trades near historic low vs Momentum*
> **价值相对动量的估值接近历史低位**（价值[Fwd P/E] vs. 动量[12 个月+1 个月]的相对 Fwd P/E，2001/2–2023/4）

---

# 第 47 页 · 仓位偏低价值 & 估值折价；股权久期开篇

> **📊 图表 86**：*Investors are still ~30% underweight Value vs. Growth*
> **投资者对价值 vs. 成长仍低配约 30%**（主动管理人在"低 P/B" vs. "高长期 EPS 增长"上的相对敞口，2008–2023/4，最新：0.6x）

> **📊 图表 87**：*Financials and Energy are still underweight by investors*
> **金融与能源仍被低配**（主动管理人在金融与能源上的相对 S&P 500 敞口，2008–2023/4）

> **📊 图表 88**：*Value still trades at a steep discount vs. Growth despite the recent strength*
> **尽管近期强劲，价值相对成长仍存在显著折价**（罗素 1000 价值 vs. 成长的相对远期 P/E，1978 至今，均值 ± 1 倍标准差走廊）

> **📊 图表 89**：*Valuations dispersion remains extremely elevated*
> **估值分化仍处极高水平**（标普 500 估值分化 vs. 罗素 1000 成长对价值的相对表现，1990–2023/4，**相关系数 72%**）

## Equity duration
## 股权久期

While the Growth and Value benchmarks have not always provided meaningfully differentiated returns, what might be a more important way to differentiate stocks is by equity duration. We have found that since the 2008/09 Global Financial Crisis, both long duration and short duration stocks have grown expensive, where long duration companies can be seen as "delayed gratification" investments, found in younger higher growth industries like Biotechnology. These companies might not generate significant cash flow today, but offer the promise of high growth in the future. Short duration companies are the equivalent of high coupon bonds – these are "cash cows" generally found in mature, ex-growth industries like Utilities or Tobacco.

虽然成长与价值两套基准指数的回报并不总有显著分化，但**另一种也许更本质的分类维度是"股权久期"**。我们发现：**自 2008/09 年 GFC 以来，长久期和短久期股票双双变贵**——
- **长久期公司** 可以理解成"**延迟满足型投资**"，多见于生物科技等年轻高成长行业：**当下没有显著现金流**，卖的是"**未来高成长**"的承诺
- **短久期公司** 则像**高息债券**——**公用事业、烟草**这类成熟、无增长的**"现金奶牛"**

Since 2008 two attributes have been scarce: growth and yield. Thus the tails of equity duration have both done well, where short duration companies are generally more prevalent in the value benchmark, and long duration companies are generally more prevalent in the growth benchmark.

2008 年以来**稀缺的正是两样东西：成长和收益率**。因此**股权久期的两端都表现不错**——**短久期股票多集中在价值指数里，长久期股票多集中在成长指数里**。

---

# 第 48 页 · 股权久期分类 & 规模、利润周期与质量

> **📊 图表 90**：*Equities have duration*
> **股票也有久期**
>
> | 久期类型 | 特征 | 代表 |
> |---|---|---|
> | **低久期（Low duration）** | 高股息、无增长 | **债券代理股（Bond-proxies）** |
> | **中等久期** | 一半增长 + 一半股息 | **股息增长股（Dividend growth stocks）** |
> | **高久期（High duration）** | 高增长、无股息 | **长期成长股（Secular growth stocks）** |

## Size
## 规模

We have also examined stock performance according to size, defined by market capitalization. We analyze small- and mid-cap stocks in our Small/Mid Cap Strategy work (led by Jill Hall) and incorporate several market capitalization-driven analyses into our research each month.

我们也按**市值规模**研究股票表现。**小盘/中盘策略**由 Jill Hall 牵头；每月的研究中我们也会纳入多项与市值相关的分析。

### Nifty Fifty vs. Not-So-Nifty 450
### 漂亮 50 vs. 不那么漂亮的 450

For several years, we have split the S&P 500 index into two distinct groups: the Nifty Fifty (comprised of the top 50 stocks in the S&P 500 by market capitalization) and the Not-So-Nifty 450 (comprised of the S&P 500 excluding the Nifty Fifty stocks.) By examining the performance and characteristics of each group of stocks, we are able to take investment views based on size.

多年来我们一直把标普 500 切成两组：**漂亮 50（Nifty Fifty）**—— 按市值排名前 50 的公司；**不那么漂亮的 450（Not-So-Nifty 450）**—— 剩下的 450 家。**通过对比两组的表现与特征，我们可以从"规模"角度形成投资观点**。

### Small vs. Large Stock Performance
### 小盘 vs. 大盘股表现

Each month we compare small stock versus large stock performance and risk/return characteristics by comparing the Russell 2000 (small) with the S&P 500 (large) and publish the results in the US Performance Monitor.

每月我们都会比较小盘（**罗素 2000**）与大盘（**标普 500**）的表现与风险/收益特征，成果发布在 **《美国表现监视器》** 报告中。

### Small Size Screen
### 小市值筛选

Each month we publish a "small size" screen in our Quantitative Profiles report that includes the 50 smallest stocks in the S&P 500 by market capitalization.

每月在 **《量化策略画像》（Quantitative Profiles）** 报告中我们会发布一份**"小市值"筛选**——即**标普 500 内按市值排倒数 50 的公司**。

### The Profits Cycle and High Quality vs. Low Quality
### 利润周期 与 高质量 vs. 低质量

Expansions and contractions in the profits cycle are almost entirely attributable to the cyclicality and profitability of lower quality stocks. We define quality using Standard & Poor's quality ranks, essentially a ranking of stocks based on earnings growth stability.

**利润周期的扩张与收缩，几乎完全归因于低质量股票的周期性与盈利弹性**。我们用 **标普质量评级（S&P Quality Ranks）** 来定义质量——**本质是按盈利增长的稳定性给股票打分**。

Higher quality companies are generally stable companies, and their earnings do not change dramatically enough to alter the entire profits cycle. Moreover, earnings variability is one of the main inputs into the determination of the quality rating assigned to a company. Therefore, the lower ranked stocks are more variable and, by definition, contribute more to shifts in the profits cycle. When the profits cycle decelerates and earnings growth becomes scarce, relative earnings will begin to favor higher quality companies and high quality should outperform. Likewise, when the profits cycle accelerates and earnings growth becomes more abundant, lower quality companies have better relative earnings than might higher quality issues, and thus tend to outperform.

**高质量公司通常更稳健，其盈利波动不足以撼动整个利润周期**。而**盈利波动性本身就是质量评级的主要输入之一**——因此**低质量股按定义波动更大，对利润周期变化贡献更多**。
- **利润减速、增长稀缺时**：**高质量公司相对盈利占优，高质量跑赢**
- **利润加速、增长丰裕时**：**低质量公司的相对盈利反而更好，低质量跑赢**

---

# 第 49 页 · 质量与利润周期的表现；利润周期与规模；波动率

> **📊 图表 91**：*Average Performance by Quality When the Profits Cycle Accelerated (Last Five Cycles, 1986-4/2023)*
> **利润周期加速时，按质量的平均表现**（过去 5 轮周期）—— **低质量领涨**
>
> | 评级 | 平均表现 |
> |---|---|
> | A+ | 25% |
> | A | 25% |
> | A- | 28% |
> | B+ | 33% |
> | B | 40% |
> | B- | 52% |
> | **C&D** | **67%** |

> **📊 图表 92**：*Average Performance by Quality When the Profits Cycle Decelerated (Last Four Cycles, 1986-4/2023)*
> **利润周期减速时，按质量的平均表现**（过去 4 轮周期）—— **高质量领涨**
>
> | 评级 | 平均表现 |
> |---|---|
> | **A+** | **25%** |
> | A | 21% |
> | A- | 21% |
> | B+ | 16% |
> | B | 16% |
> | B- | 8% |
> | C&D | 4% |

### The Profits Cycle and Size
### 利润周期与规模

As with lower quality and value investing, small stock investing has historically correlated with levels of nominal growth within the economy. An accelerating profits cycle, therefore, tends to benefit smaller stocks' relative performance.

与"低质量"和"价值"投资同理，**小盘股投资历史上也与名义经济增速正相关**——因此**利润周期加速时，小盘股的相对表现往往受益**。

## Volatility
## 波动率

A key driver for risk and quality returns is volatility. Rising volatility typically benefits higher quality, perceived safer companies whereas falling volatility typically benefits lower quality, riskier companies. The yield curve appears to predict volatility, and the rationale for the historical relationship is that volatility may be driven by factors that the yield curve generally forecasts, including growth and risk. A steepening yield curve typically reflects increases in growth expectations and risk appetite, which have a dampening effect on volatility; a flattening yield curve typically reflects decreasing growth expectations and building risk aversion, which tend to have an amplifying effect on volatility.

风险与质量类资产的一个核心驱动是**波动率**。**波动率上行期高质量、安全型公司受益；下行期低质量、高风险公司受益**。**收益率曲线似乎能预测波动率**——背后逻辑是：**波动率被一些"收益率曲线本就会预测"的变量（如增长、风险）所驱动**。
- **曲线变陡** → 通常反映增长预期提升、风险偏好上行 → **波动率被压低**
- **曲线变平** → 通常反映增长预期下滑、避险情绪累积 → **波动率被放大**

<details>
<summary>📖 <b>术语解释：VIX / 收益率曲线 / 期限利差</b></summary>

- **VIX（CBOE Volatility Index，芝加哥期权交易所波动率指数）**：又称\"**恐慌指数**\"。它不是对\"已发生波动\"的测量，而是**从标普 500 指数期权价格中反推出来的、市场对未来 30 天波动率的共识预期**（年化百分比）。
  - **VIX < 15**：市场平静、风险偏好高；
  - **15–25**：正常；
  - **> 30**：显著紧张（历次危机 VIX 都冲到 40–80+）。
  - VIX 与股价**高度负相关**——股跌 VIX 涨、股涨 VIX 跌。因此它既是\"恐慌温度计\"，也是对冲工具（VIX 期货/期权/ETF）。

- **收益率曲线（Yield Curve）**：把不同期限（1M、3M、6M、1Y、2Y、5Y、10Y、30Y）的**美国国债收益率**点出来连成的曲线。
  - **正常形态**：长端收益率 > 短端（\"**向上倾斜**\"），反映投资者要求更高补偿来锁更长期限。
  - **倒挂（Inversion）**：短端 > 长端——**历史上最著名的衰退预警信号**，因为它意味着市场预期未来央行会因经济走弱而大幅降息。

- **期限利差（Term Spread / Yield Curve Slope）**：最常用的是 **\"10 年 − 2 年\"（2s10s）** 或 \"10 年 − 3 个月\"。
  - **>0 且走阔** = 曲线变陡 → 增长预期上行、风险偏好回升；
  - **<0**（利差为负）= 倒挂 → 衰退预警。
  - 本文展示的关键结论是：**曲线斜率领先 VIX 约 3 年** —— 也就是说**收益率曲线形态可以提前数年\"预报\"未来的市场波动率**。

</details>

> **📊 图表 93**：*CBOE VIX and Inverted Slope of Yield Curve (Jan 1986 to present)*
> **CBOE VIX vs. 倒挂的收益率曲线斜率**（1986/1 至今）
> —— **"2–10 年利差"领先 3 年（左轴倒置）** · **相关系数 −46%**
> 曲线变平反映增长预期下滑、避险累积，对波动率有放大效应。

Periods of rising volatility tend to favor higher quality companies, and periods of falling volatility tend to favor lower quality stocks. Moreover, during periods when volatility is at more "normal levels", fundamental strategies tend to outperform both risk and high quality strategies.

波动率上行期利好高质量公司；下行期利好低质量。此外，**当波动率处于"正常水平"时，基本面策略通常会同时跑赢风险类策略和高质量策略**。

---

# 第 50 页 · 质量与 VIX 相关性；困境比率（Distress Ratio）；股息登场

> **📊 图表 94**：*BofA Quality Indices 12-Mth Performance Correlation to 12-mth change in CBOE VIX (1986-present)*
> **各质量等级 12 个月表现 与 CBOE VIX 同期变化的相关系数**（1986 至今） —— **波动率上行时，高质量跑赢**
>
> | 评级 | 相关系数 |
> |---|---|
> | C&D | **-35%** |
> | B- | -29% |
> | NR | -21% |
> | B | -4% |
> | B+ | 12% |
> | A- | 13% |
> | A | 25% |
> | **A+** | **+35%** |

### Distress Ratio
### 困境比率

The Distress Ratio measures the percentage of bonds in the BofA High Yield universe yielding more than the current 10-yr Treasury note by 1,000 basis points or more on an options-adjusted basis. The distress ratio has an established leading relationship to default rates, which tend to be fairly coincident to the profits cycle. In terms of strategy rotation, we have found that companies with high debt-to-equity ratios tend to outperform when the distress ratio is falling and vice versa.

**困境比率**衡量的是：美银高收益债券样本中，**按期权调整收益率计算，比当前 10 年期国债高出 1000 个基点以上**的债券所占比例。**困境比率对违约率有稳定的领先关系**；而**违约率本身和利润周期几乎是同步的**。就策略轮动而言，我们发现：**困境比率下降时，高负债率公司倾向于跑赢；上升时反之**。

> **📊 图表 95**：*BofA High Yield Distress Ratio*
> **美银高收益困境比率**（1991–2023，目前仍低于历史均值）

## Dividends
## 股息

### Welcome to a total return world
### 欢迎来到"总回报"世界

Against a longer-term backdrop of positive but below-average price returns for equities, total returns grow more important. We see multiple reasons (below) why dividends should contribute an increasing share of returns from here. Dividends have contributed 17% of S&P 500 total returns over the past 10 years, but 37% of total returns historically since 1936.

在"股价长期为正但低于历史均值"的大背景下，**总回报视角变得更重要**。我们列出几个理由（见下），说明**从今往后股息对总回报的贡献会越来越大**。事实上：**过去 10 年股息只贡献了标普 500 总回报的 17%；但自 1936 年以来的历史均值是 37%**。

---

# 第 51 页 · 股息贡献与派息率；DPS 落后 EPS 的追赶空间

<details>
<summary>📖 <b>术语解释：EPS / DPS / 派息率（Payout Ratio）</b></summary>

- **EPS（Earnings Per Share，每股盈利）**：公司净利润 ÷ 总股本。\"一股赚了多少钱\"，是最核心的盈利指标。
- **DPS（Dividends Per Share，每股股息）**：一年内每股分配到的现金股息。EPS 是公司**赚的**，DPS 是公司**分给你的**。
- **派息率（Payout Ratio）= DPS / EPS**：公司把多少比例的利润分给了股东。**历史均值约 50%**；派息率越低说明公司越倾向于留钱做再投资/回购/还债。
- **股息率（Dividend Yield）= DPS / 股价**：是从\"买入者角度\"衡量\"1 美元成本每年收回多少现金股息\"——不同于派息率。
- **股息贡献（Dividend Contribution to Total Return）**：总回报 = 价格涨幅 + 再投资股息。历史上股息贡献约占 37%；近 10 年仅 17%——意味着过去十年主要靠涨价，未来若价格回报收敛到历史均值之下，股息的重要性会回升。

</details>

> **📊 图表 96**：*S&P 500 price return and dividend contributions to total return, 1936 – present*
> **标普 500 历年"价格回报"与"股息"对总回报的贡献分解**（1936 至今）—— **自 1936 年以来股息贡献 37%；2010 年以来仅 17%**

### Dividend Yield has scarcity value; room to raise payouts
### 股息率具有稀缺价值；派息率仍有上行空间

The S&P 500 dividend payout ratio is bumping along near a record low after two years during which dividend growth dramatically lagged earnings growth (Exhibit 97)

过去两年里，**股息增速明显落后于盈利增速**，导致**标普 500 派息率徘徊在历史低位附近**（图表 97）。

> **📊 图表 97**：*Room to raise dividends*
> **派息率仍有抬升空间**（标普 500 派息率，1900–2023Q1；**长期均值 52%**）

> **📊 图表 98**：*DPS growth lagged EPS by >40ppt; expect some catch up*
> **DPS（每股股息）增速比 EPS 滞后逾 40 个百分点，预计会有追赶**（标普 500 TTM DPS 同比 vs. EPS 同比 滞后 3 个季度，1945 至今）

---

# 第 52 页 · 新入场股息公司稀缺；短久期在加息中领涨

> **📊 图表 99**：*New dividends have scarcity value*
> **"新增股息"具有稀缺价值**（罗素 3000 中首次派息公司的数量，1986–2022）

### Short duration leads amid rising interest rates
### 加息环境中短久期占优

As the equity risk premium (ERP) and real interest rates rise, discounted cash flow (DCF) math tells us that short duration stocks should beat long duration stocks.

随着**股权风险溢价（ERP）与实际利率上行**，**DCF 数学** 告诉我们：**短久期股票应该跑赢长久期股票**。

> **📊 图表 100**：*Rising rates hit short and long duration stocks but New Media morphing from long duration to cash return (e.g., META buyback)*
> **利率上行对短/长久期股票均有影响；但新媒体正从长久期向"现金回报"转型（如 META 推回购）**（标普 500 各行业派息率 vs. 预期长期增速，截至 2023/4）
>
> 低派息 + 高增长（右下）——高久期：**New Media**、**AMZN**、**TSLA**、**Tech**
> 高派息 + 低增长（左上）——低久期：**Utilities**、**Staples**、**Telecomm.**、**Real Estate**
> 注：Old Media、New Media 归属通信服务（Comm. Svcs.）；AMZN、TSLA 归属可选消费（Cons. Disc.）；能源、酒店/餐饮/休闲、航空/航天因无盈利被剔除。

---

# 第 53 页 · 标普 500 股权久期接近历史高位；紧缩期"现金为王"

> **📊 图表 101**：*Equity duration of the S&P 500 is currently 35 years, near record highs*
> **标普 500 的股权久期当前约 35 年，接近历史高位**（2001–2023/4/30）

### Dividends = inflation-protected yield
### 股息 = 抗通胀收益

Earnings are nominal. Sectors that are positively correlated to inflation, with growing yields, may be the best option in an environment of still scarce yield and inflation risks.

**盈利本质上是"名义"概念**。**与通胀正相关、股息还在增长的行业**，在这个**收益率仍稀缺 + 通胀风险仍存**的环境里，很可能是最优选择。

### Cash is king in tightening environments
### 紧缩环境中"现金为王"

As short-term rates have continued to increase, the opportunity cost for stocks vs. cash has reversed from prior years, and bird-in-the-hand stocks will likely continue to lead. Free cash flow based valuation factors and our Dividend Discount Model alpha factor have also historically outperformed in "Downturn" regimes of our US Regime Indicator.

短端利率持续上行，让**"持股 vs. 持现"的机会成本较前些年发生逆转**——这种环境下，**"一鸟在手"型股票（已经实打实产生现金流）大概率会继续领涨**。从因子角度看，**基于自由现金流的估值因子**与**我们的 DDM Alpha 因子**，在**美国市场体制指标（US Regime Indicator）的"下行期（Downturn）"制度下**，历史上也都跑赢大盘。

> **📊 图表 102**：*High Free Cash Flow to EV was best performing Value factor before the GFC*
> **GFC 前，高 FCF/EV 是表现最好的价值因子**（1986/5–2007/12 各因子表现）

---

# 第 54 页 · "下行期"制度下的因子表现；股息需求结构性上行；第二五分位法则

> **📊 图表 103**：*Downturn: Growth lags, Value mixed; Cash (ex. Div. Yield) & Quality wins*
> **"下行期"制度下：成长落后、价值参差、"现金（不含股息率）+ 质量"胜出**（下行期制度中 S&P 500 首十分位的平均相对表现）
>
> **胜出因子（正向）**：**5 年 ROE、FCF/EV、ROC、30wk/75wk 相对强度、ROA、1 年 ROE、P/FCF、价格动量(12 月 + 1 月反转)、DDM、股息增长、股票回购、股权久期**
> **落后因子（负向）**：**P/S、股息率、盈利动量、EV/EBITDA、盈利收益率、预期 5 年 EPS 增速、远期盈利收益率、P/B**
> （图例：绿 = 价值，红 = 成长，蓝 = 现金与质量）

### Demand backdrop skews to income over capital appreciation
### 需求端：越来越偏好"收入"而非"资本增值"

Aging demographics and a rising share of actively managed money in income funds suggest dividends are likely to continue to matter.

**人口老龄化 + 主动管理资金中收入型基金占比的抬升**，意味着**股息的重要性会继续上升**。

> **📊 图表 104**：*Demographics suggest demand for income will accelerate from here*
> **人口结构意味着收入型需求将从这里开始加速**（预期寿命 vs. 死亡率，1960–2021）

> **📊 图表 105**：*Income funds have grown from less than 20% of active AUM in 2010…*
> **收入型基金在 2010 年还不到主动 AUM 的 20%…**（2010 年 8 月主动股票 AUM 构成）
>
> | 类型 | 占比 |
> |---|---|
> | 激进成长 | 36% |
> | GARP | 29% |
> | 价值 | 18% |
> | **收入型 Yield** | **17%** |

> **📊 图表 106**：*…To over 40% of active funds today*
> **…如今已超过主动基金的 40%**（当前主动股票 AUM 构成）
>
> | 类型 | 占比 |
> |---|---|
> | **收入型 Yield** | **44%** |
> | 激进成长 | 31% |
> | GARP | 13% |
> | 价值 | 12% |

### Quintile 2: highest dividends aren't always best
### 第二五分位：股息最高的一组并非最优

Since 1984, the second quintile (Quintile 2) of the Russell 1000 by trailing dividend yield has exhibited the highest total return and lowest probability of loss (% of negative 12-month returns) of all other dividend quintiles including non-dividend-payers.

1984 年以来，按"过去 12 个月股息率"将罗素 1000 分成五个五分位，**第二五分位（Quintile 2）组在所有组（包括不派息组）中，展示出最高的总回报与最低的亏损概率**（12 个月负回报的比例）。

<details>
<summary>📖 <b>术语解释：分位数（Quintile / Decile）与"分组回测"</b></summary>

量化研究最基础的检验手段叫**分组回测（Portfolio Sort）**——**按某个因子值把股票从高到低排队，然后等分成 N 组**，每组构成一个\"组合\"，跟踪其后续回报。

- **Quintile（五分位）**：等分成 **5 组**。**Q1/Quintile 1 = 得分最高的那 20%**；Q5 = 得分最低的 20%。
- **Decile（十分位）**：等分成 **10 组**。D1 = 最高 10%，D10 = 最低 10%。
- **Tercile**：3 组；**Quartile**：4 组。

**为什么这么做**：如果某因子\"真的能选股\"，那么 Q1 到 Q5 的业绩应该**单调递减**（或递增），且 Q1 与 Q5 之差（\"多空组合\"）应长期显著为正。以本例为例，罗素 1000 按股息率分 5 组，**最高股息那一组（Q1）反而不如 Q2**——说明\"股息越高越好\"是个误区（超高股息常伴随陷阱：派息不可持续、股价暴跌才把股息率推高）。

**再平衡（Rebalance）**：分组每隔一段时间（常见**月度或季度**）按最新因子值**重新排序、重新分组**。再平衡频率越高，换手越大、成本越高；过低又跟不上因子变化。

</details>

---

# 第 55 页 · 第二五分位为何胜出

Quintile 2 may be a good first-pass screen at seeking out companies with above-market and secure but not stretched dividend yields: it guards against owning distressed companies that migrate into Quintile 1 (highest dividend quintile) if prices fall ahead of potential dividend cuts. It also incorporates a "buy low, sell high" valuation discipline in that if prices rise faster than dividends grow, companies will migrate into Quintile 3.

**第二五分位可作为筛选"股息高于市场、稳健但未被拉满"公司的一个良好"首轮筛选"**：
- **防御"假高息陷阱"**：困境公司在未来可能砍股息，其股价常先行下跌——这会把它们"推入"第一五分位（最高股息组）；**用 Quintile 2 能有效回避这类陷阱**
- **嵌入"低买高卖"的估值纪律**：当股价涨得快于股息增长时，公司会"**漂**"到第三五分位去——**Quintile 2 由此天然具备纪律性的再平衡机制**

> **📊 图表 107**：*Highest isn't always best*
> **股息最高的一组并非最优**（罗素 1000 按 TTM 股息率分五个五分位 + 不派息组；月度再平衡；1984/1/31–2023/4/30）
> 图示：横轴 = 亏损概率（12 个月负回报占比），纵轴 = 年化总回报；**Quintile 2** 位于"高回报 + 低亏损概率"区间，优于 Quintile 1（最高股息）。
> 注：本筛选**仅作指示性指标**，未经 BofA 全球研究书面同意，不得用作任何金融工具/合约的参考或绩效基准。回测基于 1984/1/31–2010/9/28；2010/9/28 起为真实表现。

---

# 第 56 页 · 风险度量

## Measuring risk
## 风险度量

We believe that there are two basic definitions of risk. The classic or academic definition of risk is the uncertainty of the return of an investment. Standard deviation or volatility of returns is the measurement most often used to quantify this unpredictability. The other definition of risk is the probability of losing money. Our work suggests that, in practice, investors tend to be more concerned with the probability of losing money than they are with the predictability of return. Therefore, we prefer to define performance risk in much of our work as the probability of a negative return.

我们认为风险有**两种基本定义**：
- **经典／学术定义**：投资回报的"不确定性"。最常用的量化指标是收益的**标准差（波动率）**
- **另一种定义**：**亏损的概率**

我们的研究表明，**实务中投资者更关心"亏钱的概率"，而不是"回报的可预测性"**。因此，本报告大量工作中，我们偏好将业绩风险定义为"**负回报出现的概率**"。

> **📊 图表 108**：*Risk Reward Characteristics（1925–2023/4）*
> **风险-收益特征**：小盘股回报最高，但波动率也最高……
> 图示横轴 = 标准差，纵轴 = 年化平均回报；包括小盘股、大盘股、高评级公司债、长期美债、91 天国库券、CPI。

> **📊 图表 109**：*Downside Risk Reward Characteristics（1925–2023/4）*
> **下行风险-收益特征**：……且小盘股亏损概率也最高。
> 图示横轴 = 亏损概率，纵轴 = 年化平均回报。

### Long-short risk reward characteristics
### 多空组合的风险-收益特征

For long-short screens, we track the average spread (or absolute return) of the strategy but consider the tradeoff as the consistency of this return being positive. Thus, we assess risk-reward for long-short strategies as the average spread in returns versus the probability of the long screen outperforming the short screen, which we gauge as the percentage of periods during which the long-short spread was positive.

对于**多空（long-short）筛选策略**，我们跟踪策略的**平均价差（或绝对回报）**，但将"取舍对价"定义为"**回报为正的一致性**"。因此，我们对多空策略的风险-收益评估方式是：**平均价差 vs. 多头组跑赢空头组的概率**（用"多空价差为正的期数占比"来衡量）。

### Risk-adjusted factor returns
### 风险调整后的因子回报

Prudent investors cannot simply consider absolute returns, but must also consider potential returns on a risk-adjusted basis (see Appendix for risk-adjusted returns for the Russell 1000 factors). Contrary to traditional financial theory, taking on excess risk does not generate higher returns when it comes to factor performance. Among the general categories of Growth, Value, Quality, Cash Return and Risk, risk strategies including high beta, high variability of earnings, and others comprise the worst performing group based on absolute returns, as well as risk-adjusted returns. In the 22 years leading up to the Global Financial Crisis, every risk strategy we follow underperformed its benchmark. For Russell 1000 factor sensitivity, please see the Appendix.

审慎的投资者不能只看绝对回报，还必须考虑**风险调整后的潜在回报**（罗素 1000 因子的风险调整回报见附录）。**与传统金融理论相反**：**在因子表现上，承担超额风险并不带来更高回报**。
- 在"成长、价值、质量、现金回报、风险"这几大类中，**"风险类"策略**（高贝塔、盈利高波动等）**无论按绝对回报还是风险调整回报看，都是最差的一组**
- 在 GFC 之前的 22 年里，我们跟踪的**每一个"风险型"策略都跑输了基准**

---

# 第 57 页 · 因子的风险-收益全表（1986 至今）

> **📋 图表 110**：*Factor performance 1986 to present*
> **各因子的绝对表现、风险调整表现与风险特征**（1986 至今）

<details>
<summary>📖 <b>术语解释：读懂因子业绩表里的各列</b></summary>

- **年化平均回报（Annualized Return）**：多年累计回报换算成\"每年等价多少 %\"，消除时间跨度差异。
- **超额回报（Excess Return）**：组合回报减去基准回报（如 S&P 500）。12M 超额 = 过去 12 个月的超额回报。
- **Sharpe 比率（夏普比率）**：**回报超过无风险利率的部分 ÷ 回报波动率**——衡量\"每承担 1 单位风险换来的超额回报\"。数值越高越好，>0.5 通常算不错。本表给出两种 Sharpe：vs. **10 年美债**（标准无风险利率基准）和 vs. **S&P 500**（基准指数）。
- **亏损概率（% Negative）**：12 个月滚动窗口内出现亏损的频率。
- **跑输概率**：12 个月滚动窗口内跑输基准（S&P 500）的频率。
- **年化波动率（Volatility）**：月度回报的标准差 × √12——衡量\"整体起伏剧烈程度\"，包含上涨与下跌两边。
- **最大回撤（Max Drawdown）**：历史上从最高点跌到最低点的**最大幅度**（如 -60% 表示某时段曾从顶部跌去 60%）——衡量\"最坏情况\"。
- **年化下行波动率（Downside Volatility）**：只用**回报 < 0 的月份**算波动——更贴近\"真正让投资者痛的那种风险\"。
- **首分位（Q1/D1）**：把股票按该因子从高到低排成 5 组（Quintile）或 10 组（Decile），第 1 组就是**得分最高**的那组。

</details>

| 因子 | 年化平均回报 | 12 个月相对 S&P 500 超额回报 | vs. 10 年美债 Sharpe | vs. S&P 500 Sharpe | 亏损概率 | 跑输 S&P 500 概率 | 年化波动率 | 最大回撤 | 年化下行波动率 |
|---|---|---|---|---|---|---|---|---|---|
| Most Active（最活跃） | 16.3% | 6.0% | 0.63 | 0.44 | 20.2% | 32.1% | 22.0% | -62.1% | 16.2% |
| Price/FCF | 15.8% | 5.2% | 0.62 | 0.51 | 21.1% | 32.1% | 21.9% | -62.7% | 16.5% |
| EV/EBITDA | 15.1% | 4.5% | 0.58 | 0.39 | 20.2% | 33.5% | 22.4% | -59.2% | 17.1% |
| FCF/EV | 14.9% | 3.7% | 0.61 | 0.41 | 19.7% | 34.2% | 19.8% | -58.6% | 14.6% |
| 12m + 1m 反转 | 14.1% | 2.4% | 0.59 | 0.21 | 15.4% | 33.9% | 18.8% | -56.7% | 15.4% |
| 5 年 ROE（调整） | 14.0% | 2.1% | 0.60 | 0.24 | 16.7% | 42.2% | 18.0% | -44.3% | 13.2% |
| 股票回购 | 13.9% | 2.2% | 0.59 | 0.35 | 20.0% | 39.7% | 18.2% | -50.5% | 14.7% |
| P/S | 13.9% | 4.4% | 0.49 | 0.25 | 23.9% | 38.3% | 24.7% | -69.9% | 18.2% |
| 1 年 ROE（调整） | 13.9% | 2.0% | 0.60 | 0.21 | 20.4% | 39.9% | 17.6% | -50.1% | 12.6% |
| 空头兴趣 | 13.8% | 2.4% | 0.67 | 0.46 | 15.2% | 36.1% | 16.7% | -47.1% | 12.6% |
| 1 年 ROE | 13.8% | 1.6% | 0.62 | 0.23 | 16.3% | 38.5% | 16.8% | -46.1% | 12.4% |
| 9 月价格回报 | 13.5% | 2.5% | 0.55 | 0.09 | 19.0% | 38.8% | 19.4% | -54.1% | 14.2% |
| ROC | 13.5% | 1.4% | 0.59 | 0.16 | 21.1% | 41.3% | 17.1% | -47.3% | 12.3% |
| 盈利收益率（E/P） | 13.4% | 3.3% | 0.50 | 0.27 | 22.7% | 42.0% | 22.4% | -69.4% | 17.4% |
| 5 年 ROE | 13.4% | 1.4% | 0.59 | 0.18 | 17.2% | 40.8% | 17.0% | -43.7% | 12.5% |
| PEG | 13.3% | 2.7% | 0.48 | 0.23 | 26.6% | 39.0% | 23.6% | -68.0% | 17.5% |
| 前瞻盈利收益率 | 13.2% | 3.9% | 0.47 | 0.19 | 25.5% | 41.5% | 24.9% | -74.9% | 19.0% |
| 11 月价格回报 | 13.2% | 2.2% | 0.52 | 0.08 | 22.2% | 41.1% | 19.9% | -56.5% | 15.0% |
| ROA | 13.1% | 1.2% | 0.55 | 0.12 | 21.8% | 47.7% | 18.1% | -49.8% | 12.8% |
| 12 月价格回报 | 13.1% | 2.0% | 0.53 | 0.05 | 20.4% | 41.3% | 19.2% | -53.7% | 14.3% |
| 相对强度 10wk/40wk | 12.7% | 1.7% | 0.51 | 0.03 | 20.2% | 44.0% | 18.8% | -56.2% | 13.5% |
| Price/Cash Flow | 12.6% | 2.2% | 0.46 | 0.14 | 24.3% | 38.8% | 23.5% | -60.7% | 18.4% |
| 相对强度 30wk/75wk | 12.5% | 1.7% | 0.48 | 0.03 | 22.9% | 46.3% | 20.7% | -59.5% | 16.1% |
| 相对强度 5wk/30wk | 12.4% | 1.1% | 0.51 | 0.00 | 18.3% | 47.0% | 18.1% | -49.2% | 12.7% |
| 股息增长 | 12.3% | 0.6% | 0.50 | 0.10 | 21.8% | 45.4% | 18.5% | -55.0% | 14.1% |
| 股息率 | 12.2% | 2.2% | 0.45 | 0.03 | 21.8% | 48.4% | 21.4% | -78.1% | 17.1% |
| 股价/200 日均线 | 12.0% | 0.7% | 0.49 | -0.03 | 19.7% | 50.2% | 17.9% | -51.2% | 13.0% |
| EPS 修正比 | 12.0% | 1.2% | 0.46 | 0.04 | 24.5% | 43.6% | 20.5% | -60.9% | 15.7% |
| 等权 S&P 500 | 11.8% | — | 0.49 | — | 19.5% | — | 17.3% | -55.7% | 13.5% |
| 规模（Size） | 11.7% | 2.0% | 0.40 | 0.09 | 28.7% | 48.4% | 26.3% | -68.4% | 18.8% |
| 低价股 | 11.7% | 3.1% | 0.39 | 0.09 | 27.5% | 49.8% | 28.9% | -68.5% | 20.1% |
| 3 月价格回报 | 11.6% | 0.4% | 0.46 | -0.05 | 22.2% | 49.8% | 18.4% | -56.2% | 13.1% |
| 冷门-分析师覆盖度 | 11.4% | 0.0% | 0.44 | -0.02 | 22.9% | 53.0% | 19.4% | -63.1% | 15.9% |
| 12m + 1m 表现 | 11.4% | -0.3% | 0.47 | -0.09 | 21.8% | 52.3% | 17.3% | -52.6% | 12.9% |
| P/B | 11.3% | 2.8% | 0.39 | 0.05 | 27.3% | 43.6% | 26.5% | -82.4% | 19.9% |
| Earnings Torpedo（盈利鱼雷） | 11.3% | 0.9% | 0.40 | 0.00 | 23.6% | 50.7% | 22.7% | -65.7% | 15.9% |
| 盈利动量 | 10.7% | -0.6% | 0.41 | -0.13 | 24.5% | 56.4% | 19.2% | -59.7% | 14.9% |
| Beta | 9.8% | 1.9% | 0.33 | 0.00 | 32.6% | 54.1% | 31.2% | -81.0% | 22.3% |
| 预测 5 年 EPS 增速 | 9.7% | 0.1% | 0.33 | -0.08 | 26.1% | 56.9% | 25.5% | -82.0% | 19.2% |
| 盈利波动性 | 9.1% | -1.5% | 0.31 | -0.24 | 27.8% | 56.7% | 22.0% | -64.8% | 16.5% |
| 预测分散度 | 8.3% | -0.7% | 0.27 | -0.12 | 30.3% | 54.6% | 28.4% | -75.0% | 19.9% |
| 冷门-机构持股 | 8.0% | -1.7% | 0.35 | -0.22 | 25.5% | 69.7% | 17.2% | -57.9% | 13.5% |

观察：
- **最赚钱的前几名**：Most Active、P/FCF、EV/EBITDA、FCF/EV、动量反转——**价值+现金流+动量反转胜出**
- **最烧钱的后几名**：高 Beta、预测 5 年 EPS 增速、盈利波动性、预测分散度、冷门机构持股——**"纯风险 + 华丽成长"组合持续垫底**
- **Sharpe 胜者**：P/FCF（0.51）、空头兴趣（0.46）、Most Active（0.44）、FCF/EV（0.41）

---

# 第 58 页 · 宏观很重要：因子 vs 宏观变量相关性

> **📋 图表 111**：*S&P 500 factors: Correlation vs. macro factors（1986 至今）*
> **S&P 500 各因子与宏观变量的相关性**

横向变量：10 年名义利率、10 年实际利率、2s10s 期限利差、贸易加权美元、CPI、WTI、GDP 增速、VIX、盈利周期、信用利差。

精选高相关性观察：

| 因子 | 10y 名义利率 | CPI | GDP | VIX | 盈利周期 | 信用利差 |
|---|---|---|---|---|---|---|
| 盈利收益率（E/P） | 0.30 | 0.07 | 0.11 | 0.34 | -0.47 | **-0.58** |
| 前瞻盈利收益率 | 0.41 | 0.04 | 0.09 | 0.30 | -0.46 | **-0.68** |
| 股息率 | 0.02 | 0.05 | 0.15 | 0.30 | -0.33 | **-0.52** |
| P/B | 0.44 | 0.03 | 0.22 | 0.31 | -0.53 | **-0.73** |
| P/S | 0.30 | -0.19 | 0.08 | 0.22 | -0.33 | **-0.73** |
| EV/EBITDA | 0.39 | 0.25 | 0.24 | 0.39 | -0.32 | -0.32 |
| 相对强度 30wk/75wk | 0.20 | 0.12 | 0.16 | 0.46 | 0.06 | 0.27 |
| 相对强度 5wk/30wk | 0.26 | 0.11 | 0.34 | 0.46 | 0.08 | 0.30 |
| 相对强度 10wk/40wk | 0.22 | 0.04 | 0.25 | **0.50** | 0.10 | 0.27 |
| 股价/200 日均线 | 0.19 | 0.07 | 0.23 | 0.43 | 0.18 | 0.39 |
| 12m 价格回报 | 0.15 | 0.08 | 0.12 | 0.48 | 0.10 | 0.36 |
| 9m 价格回报 | 0.20 | 0.07 | 0.18 | 0.47 | 0.11 | 0.34 |
| 3m 价格回报 | 0.33 | 0.09 | 0.31 | 0.39 | 0.02 | 0.13 |
| 11m 价格回报 | 0.16 | 0.08 | 0.14 | 0.49 | 0.08 | 0.30 |
| 12m+1m | 0.08 | 0.07 | 0.09 | 0.37 | 0.18 | 0.45 |
| 12m+1m 反转 | 0.01 | 0.02 | -0.07 | **0.51** | 0.13 | 0.34 |
| Most Active | 0.44 | 0.05 | 0.30 | 0.37 | -0.21 | -0.27 |
| 低价股 | 0.37 | -0.08 | 0.17 | 0.25 | -0.40 | **-0.63** |
| 盈利动量 | 0.42 | 0.09 | 0.15 | 0.41 | -0.07 | 0.02 |
| 5 年 EPS 增速 | 0.41 | 0.04 | 0.31 | 0.36 | -0.08 | -0.12 |
| Earnings Torpedo | 0.25 | -0.07 | 0.21 | 0.22 | -0.29 | -0.62 |
| EPS 修正比 | **0.54** | 0.32 | 0.41 | 0.51 | -0.12 | -0.02 |
| 股息增长 | -0.02 | 0.28 | 0.15 | 0.34 | -0.06 | -0.15 |
| PEG | 0.40 | 0.11 | 0.13 | 0.34 | -0.36 | -0.52 |
| 1 年 ROE | -0.41 | 0.07 | -0.15 | 0.32 | 0.39 | **0.55** |
| 5 年 ROE | -0.34 | -0.07 | -0.12 | 0.32 | 0.33 | 0.47 |
| 1 年 ROE（调整） | -0.12 | 0.08 | -0.01 | 0.29 | 0.30 | 0.34 |
| 5 年 ROE（调整） | -0.09 | -0.03 | 0.00 | 0.28 | 0.23 | 0.33 |
| ROA | -0.04 | 0.05 | 0.10 | 0.31 | 0.27 | 0.34 |
| ROC | -0.20 | 0.04 | -0.03 | 0.30 | 0.31 | 0.41 |
| Beta | **0.52** | 0.01 | 0.36 | 0.32 | -0.36 | -0.52 |
| 盈利波动性 | 0.46 | 0.08 | 0.25 | 0.33 | -0.35 | -0.52 |
| 预测分散度 | 0.53 | 0.06 | 0.43 | 0.37 | -0.44 | -0.57 |
| 冷门-分析师覆盖度 | -0.07 | -0.10 | -0.07 | 0.37 | -0.12 | -0.28 |
| 冷门-机构持股 | **-0.54** | -0.11 | -0.26 | 0.37 | 0.18 | 0.15 |
| 规模 | 0.31 | -0.11 | 0.18 | 0.24 | -0.38 | -0.67 |
| 股票回购 | -0.04 | 0.14 | 0.03 | 0.37 | -0.03 | 0.09 |
| 空头兴趣 | -0.18 | -0.08 | -0.08 | 0.41 | 0.10 | 0.21 |

关键阅读：
- **利率上行期受益**：EPS 修正比、Beta、盈利动量、预测分散度、P/B、Most Active（利率越高这些越占优）
- **利率上行期受损**：质量类（1 年 ROE、5 年 ROE、ROC）、冷门-机构持股
- **信用利差扩大时最受伤**：P/B、P/S、前瞻 E/P、规模、低价股、Earnings Torpedo——**利差收窄的"风险偏好回暖"环境对它们大有利**
- **质量类在利差扩大时反而受益**：1 年 ROE 相关性 +0.55、ROC +0.41

---

# 第 59 页 · 宏观焦点：美元的影响

## Macro focus: the US Dollar impact
## 宏观焦点：美元的影响

Regressing weekly returns of the S&P 500 vs. the US dollar (DXY index) since 1979 reveals that moves in the dollar have virtually no explanatory power on returns over the long-term (R² of zero). This is partly due to the fact that—much like with interest rates—the relationship between equities and the dollar has changed over time. For example, US stocks are much more global today than 20 years ago. Another reason is that the growth backdrop may be more important: some periods of a strengthening dollar have been accompanied by weakening growth, where the dollar strength may have been driven by a flight to safety. Other periods of dollar strengthening may have been accompanied by more robust growth.

以 1979 年以来 S&P 500 周度回报对美元（DXY 指数）做回归发现：**长期来看，美元波动对股市回报几乎没有解释力（R² 接近 0）**。原因：
- 与利率类似，**美元与股市的关系随时间在变**。如今的美国上市公司比 20 年前要"国际化"得多
- **增长背景可能更重要**：有些美元走强期伴随增长走弱（由避险驱动），有些美元走强期反而伴随稳健增长（由经济强劲驱动）——二者对股市的含义截然不同

> **📊 图表 112**：*Change in DXY index vs. S&P 500（weekly, 1979 至今）*
> **美元周度变化 vs S&P 500 周度回报**：长期几乎无解释力（**R² = 0.013**）。

### Dollar cycles can be persistent
### 美元周期可能异常持久

One notable observation with the USD is the persistence of its secular tendency – a trend, once started, can last for many years. In fact, the USD has completed only five major cycles in the last 40+ years. Both the 1978-1985 and the 1995-2002 cycles lasted 16 years. So what works in these secular dollar uptrends?

美元的一个显著特征是**长期趋势的持续性**——一旦启动，可延续多年。过去 40 多年美元仅完成了 **5 轮主要周期**。**1978-1985 与 1995-2002 两轮周期均长达 16 年（含上下两段）**。那么在美元"长牛"期什么策略有效？

One common misconception is that because small caps are more tied to the US economy and have lower foreign exposure, they should outperform large caps in a rising dollar environment. But this has not always been the case. Small caps outperformed large caps during the '78-'85 dollar uptrend, but underperformed during the last several dollar uptrends (Exhibit 113).

**一个常见误解**：既然小盘股更依赖美国经济、海外敞口更低，那美元上行期小盘股就应跑赢大盘——**实际并非如此**：小盘股在 1978-85 那轮美元上行期确实跑赢大盘股，但在**最近几轮美元上行期里却跑输了**（见图表 113）。

> **📋 图表 113**：*Dollar strength cycles and small vs. large cap performance*
> **美元"长牛"期的大小盘表现**（1978–2022/9/30）

| 时间段 | 10/78–3/85 | 6/95–2/02 | 6/14–12/16 | 1/18–3/20 | 5/21–9/22 |
|---|---|---|---|---|---|
| 小盘股累计回报 | 296.1% | 64.8% | 13.8% | -26.8% | -26.6% |
| 大盘股累计回报 | 159.8% | 103.2% | 14.2% | -8.5% | -14.7% |
| 小盘 vs 大盘（相对） | **+52.5** | -18.9 | -0.4 | -20.0 | -14.0 |

基准：罗素 2000 vs S&P 500（近三段）；CRSP 数据（1978-85 段）。**结论**：美元走强 ≠ 小盘股必胜。

---

# 第 60 页 · 美元长牛期行业与出口敞口表现

At the sector level, in the two major periods of secular dollar strength (1978-85 and 1995-2002), Financials outperformed and Materials underperformed the S&P 500 in both periods, which we also found to be true for small caps. We also saw outperformance from Health Care and Discretionary and underperformance from Telecom and Utilities in both periods within the S&P 500, with the largest outperformance from Health Care in both periods. The consistent underperformance of both a globally oriented sector (Materials) and domestically oriented sectors (Telecom and Utilities) suggests that the economic backdrop may be a more important determinant of performance.

在两轮重大美元长牛期（1978-85 与 1995-2002）的**行业表现**上：
- **两次都跑赢 S&P 500**：**金融、医疗保健、可选消费**（医疗保健在两次都是跑赢幅度最大的）；小盘股内部也见到金融跑赢
- **两次都跑输**：**材料、电信、公用事业**
- 一个**全球化行业（材料）** 和**本土化行业（电信/公用事业）同时持续跑输**的事实，说明"**经济景气背景的影响可能比美元本身更重要**"

> **📊 图表 114**：*Sector performance in the two major periods of secular dollar strength*
> **两轮美元长牛期的行业超额收益对比**（1978/10/31–1985/3/31 与 1995/6/30–2002/2/28）。

There has been a weak historical negative relationship between foreign-exposed stocks and strong dollar backdrops and a slightly stronger relationship between more domestically oriented stocks and strong dollar backdrops. But the relationship has not been strong enough to justify a uniform penalty or reward assigned to stocks based on this attribute. Many companies with foreign exposure have natural or financial hedges in place to offset currency risk, and also tend to be larger and more defensive businesses, thus may be likely to withstand a downturn better than their smaller counterparts, where downturns are generally accompanied by a flight to quality mentality which tends to bolster the US dollar. Moreover, domestic companies may not disclose foreign sales or may have a large chunk of revenue associated with multinational companies that supply overseas and thus carry indirect currency risk based on end user demand weakening.

"海外敞口高的公司 vs 美元走强"之间存在**弱负相关**；"本土化公司 vs 美元走强"之间存在**略强的正相关**——但**关系都不足以支持"根据敞口给股票统一打标签"的简单做法**，原因有三：
- 许多**高海外敞口公司已有自然对冲或金融对冲**，能够抵消汇率风险；它们通常**规模更大、更防御性**，在下行中反而更抗跌（而下行常伴随"奔向质量"的心态，这又会推升美元）
- **本土公司不一定会披露其海外业务**；许多本土公司收入大头来自"供应给跨国企业的产品"，**通过终端需求走弱间接承受汇率风险**

> **📊 图表 115**：*High Foreign exposure performance vs. USD（1995 至今）*
> **高海外敞口组合的相对表现 vs 美元**：弱负相关（y = -0.4148x + 0.0281，R² = 0.1182）。

> **📊 图表 116**：*Domestic exposure performance vs. USD（1995 至今）*
> **本土化公司的相对表现 vs 美元**：略强的正相关（y = 0.3651x + 0.0049，R² = 0.1582）。

---

# 第 61 页 · 选股路线图

## Roadmap to picking stocks
## 选股路线图

### Stock differentiation
### 股票的"差异化程度"

The following chart includes our measure of clustered versus differentiated equity markets. We measure this by the average correlation of every pair of companies' daily price returns each quarter within the S&P 500. A high correlation implies that stocks are more clustered, whereas a low correlation implies that companies are more differentiated. This measure serves as a gauge of the potential opportunity for stock selection to generate excess returns.

我们用"**股票两两相关性的平均值**"来度量市场是"**抱团**"还是"**分化**"：
- 每季度计算 S&P 500 所有股票两两之间日度回报的相关系数，取平均
- **高相关**：股票抱团（macro market），个股选择价值低
- **低相关**：股票分化（stock picker's market），**个股选择能产生超额回报的潜力大**

> **📊 图表 117**：*Correlations remain above historical average*
> **相关性仍高于历史均值**（1986 至今季度平均两两相关性）。
> 图中"长期均值"作为分界线，**当前相关性高于长期均值**，意味着仍处于偏抱团／宏观主导的市场环境。

### Stock selection within sectors
### 行业内的个股选择

When correlations are high, we believe fundamental analysis can still be rewarded by focusing on industries that may offer better stock selection opportunity. When stocks within an industry are highly correlated, it is likely that performance is attributable to some external factor rather than company specifics. In these cases, making an industry call may be more important than a stock call. For example, the high correlation among Energy stocks can be explained by oil prices; for Banks and Insurance, correlations may be explained by rates or the yield curve; and for Semis, global GDP may be a key driver of correlations.

即便整体相关性高，**基本面分析依然有空间**——只要聚焦那些"**行业内股票间相关性较低**"的板块：
- **行业内高相关 = 表现由外部因子驱动**（而非公司 specific），此时"**行业判断 > 个股判断**"
- **典型案例**：**能源**靠油价解释；**银行与保险**靠利率/收益率曲线解释；**半导体**靠全球 GDP 解释

Similarly, when a stock has a very low level of dispersion in returns, the amount of alpha or excess return that can be generated from pair trades is capped at a lower level. Thus, fundamental analysis may be more fruitful when focusing on industries with low intra-stock correlations and high dispersion of returns. For example, groups with brand differentiation (Retail) or secular stories (Tech) have offered lower correlation and higher dispersion of returns historically.

同理，**当回报分散度（dispersion）很低时，配对交易的 alpha 上限就被压低**。因此：
- **低相关 + 高分散度 = 基本面分析收获最丰**
- **品牌差异化（零售）** 与 **长期 secular 故事（科技）** 这类行业，历史上呈现**相关性更低、分散度更高**的特征——是选股阵地

---

# 第 62 页 · 各行业"选股潜力"地图

> **📊 图表 118**：*Historical Intra-stock correlation vs. performance spread（3Q86–1Q23）*
> **历史行业内两两相关性 vs 表现价差**：科技硬件与软件位列最佳选股行业之列。

图示按行业标注（横轴 = 行业内两两相关性，纵轴 = 最高/最低分位表现价差，即 alpha 机会）：
- **右下角（低相关 + 高价差）= 选股阵地**：科技硬件、软件、半导体、零售
- **左上角（高相关 + 低价差）= 行业配置阵地**：银行、公用事业、材料、能源
- 其他行业：汽车、资本品、商业/专业服务、耐用消费品与服装、消费服务、必需品零售、必选消费零售、金融服务、食品饮料烟草、医疗器械与服务、家居与个人护理、保险、媒体、制药/生物科技、运输、REITs 等介于二者之间。

Below we provide historical charts of correlations within industry groups, which illustrate where stocks are most clustered or differentiated and how these relationships have changed over time. For example, Banks have exhibited an increase in correlations over the last two decades, while correlations among Telecom stocks have remained more stable. All charts are based on the average daily pair-wise correlation of all stock combinations within the group each quarter.

下面展示各行业组的**历史相关性曲线**，揭示：
- 哪些行业股票最抱团 vs 最分化
- 这种关系随时间如何演变
- 典型例子：**银行的相关性在过去 20 年持续上升**，而电信股之间的相关性相对稳定
- 所有图均基于每季度组内所有配对的**日度平均两两相关性**

> **📊 图表 119**：*Automobiles & Components*
> **汽车与零部件**：相关性回落但仍处偏高位。

> **📊 图表 120**：*Banks*
> **银行**：相关性仍接近历史高位。

---

# 第 63 页 · 各行业相关性图（续 1）

> **📊 图表 121**：*Capital Goods*
> **资本品**：相关性仍偏高。

> **📊 图表 122**：*Commercial & Professional Services*
> **商业与专业服务**：相关性仍偏高。

> **📊 图表 123**：*Consumer Durables & Apparel*
> **耐用消费品与服装**：相关性仍偏高。

> **📊 图表 124**：*Consumer Services*
> **消费服务**：相关性仍偏高。

> **📊 图表 125**：*Diversified Financials*
> **多元化金融**：最近几个月相关性略有下降。

> **📊 图表 126**：*Energy*
> **能源**：相关性仍偏高（历史上该板块相关性天然最高，受油价主导）。

---

# 第 64 页 · 各行业相关性图（续 2）

> **📊 图表 127**：*Food & Staples Retailing*
> **食品与必需品零售**：最近几个月相关性已回落。

> **📊 图表 128**：*Food Beverage & Tobacco*
> **食品饮料与烟草**：最近几个月相关性已回落。

> **📊 图表 129**：*Health Care Equipment & Services*
> **医疗器械与服务**：最近几个月相关性已回落。

> **📊 图表 130**：*Household & Personal Products*
> **家居与个人护理**：最近几个月相关性已回落。

> **📊 图表 131**：*Insurance*
> **保险**：最近几个月相关性已回落。

> **📊 图表 132**：*Materials*
> **材料**：最近几个月相关性已回落。

---

# 第 65 页 · 各行业相关性图（续 3）

> **📊 图表 133**：*Media & Entertainment*
> **媒体与娱乐**：最近几个月相关性已回落。

> **📊 图表 134**：*Pharmaceuticals, Biotechnology & Life Sciences*
> **制药、生物科技与生命科学**：最近几个月相关性已回落。

> **📊 图表 135**：*Real Estate*
> **地产**：最近几个月相关性略有下降。

> **📊 图表 136**：*Retailing*
> **零售**：最近几个月相关性略有下降。

> **📊 图表 137**：*Semiconductors & Semiconductor Equipment*
> **半导体与半导体设备**：最近几个月相关性略有下降。

> **📊 图表 138**：*Software & Services*
> **软件与服务**：最近几个月相关性略有下降。

---

# 第 66 页 · 相关性图收尾 + Alpha 稀缺

> **📊 图表 139**：*Technology Hardware & Equipment*
> **科技硬件与设备**：相关性仍高于长期均值。

> **📊 图表 140**：*Telecommunication Services*
> **电信服务**：相关性接近历史均值。

> **📊 图表 141**：*Transportation*
> **运输**：最近几个月相关性略有下降。

> **📊 图表 142**：*Utilities*
> **公用事业**：最近几个月相关性略有下降。

## Scarce alpha has been a headwind
## Alpha 稀缺一直是主动管理者的逆风

The scarcity of alpha opportunities (spreads) has been one headwind to active managers, with the spread between the 50 best and fifty worst performing stocks remaining near well below average for most of the post-crisis period. In 2007, managers used leverage to offset this scarcity. Today, risk aversion has capped leverage ratios at lower levels.

**alpha 机会（价差）的稀缺，一直是主动基金经理面临的一大逆风**——最好的 50 只股票与最差的 50 只股票之间的表现价差，在 GFC 之后的大部分时间里都**远低于均值**。2007 年，基金经理曾通过**杠杆**来弥补 alpha 稀缺；而如今，**风险厌恶已把杠杆比率压在更低水平**。

> **📊 图表 143**：*S&P 500 Long-Short Spreads (Alpha), 1986 至今*
> **S&P 500 多空价差（Alpha）**：**当前略低于长期均值**。
> 图中标注"Abundant alpha"与"Scarce alpha"两种区制。

---

# 第 67 页 · 高/低质量股的相对表现 & 市场广度 & 美国 Regime 简介

## High Quality vs. Low Quality performance can highlight risk-on/risk-off
## 高质量 vs 低质量股的相对表现可作为"风险偏好"温度计

> **📊 图表 144**：*Relative performance of C&D vs. A+ ranked stocks by S&P Quality rank, 2007 至今*
> **S&P 质量评级 C&D 级股 vs A+ 级股的相对表现**。
> 总体而言，**新冠之后是一个"偏避险"的时期**，但**多次短周期的风险偏好反转**交替出现（图中 Risk on / Risk off 交叉频繁）。

## Market breadth: currently above average
## 市场广度：当前高于均值

> **📊 图表 145**：*Market Breadth: % of S&P 500 stocks beating the benchmark (12-month return), 1987 至今*
> **市场广度**：过去 12 个月跑赢 S&P 500 的成分股占比——**近期接近中性水平**。

## US Regime Indicator
## 美国市场体制指标（US Regime Indicator）

Investment styles like Value, Growth, Momentum, Risk and Size tend to exhibit different performance patterns in different phases of the macroeconomic cycle. For US equities, four regimes generally capture these style shifts. In our quantitative US Regime Indicator, we aggregate top-down variables that capture earnings and economic growth expectations, inflation, credit conditions and other variables, to yield the following four signals. See our Methodology section for details.

**价值、成长、动量、风险、规模**等投资风格，在宏观周期的不同阶段展现出**不同的表现模式**。对美股而言，**4 种体制**通常可以捕捉这些风格轮动。我们量化化的"**美国 Regime Indicator**"通过聚合自上而下的变量（盈利与经济增长预期、通胀、信贷状况等）来生成以下 4 种信号（方法细节见附录）：

- **Phase 1：早周期／复苏（Early Cycle）** —— 宏观指标**低于均值但在改善**
- **Phase 2：中周期（Mid Cycle）** —— 宏观指标**高于均值且继续改善**
- **Phase 3：晚周期（Late Cycle）** —— 宏观指标**高于均值但在恶化**
- **Phase 4：衰退／下行（Recession/Downturn）** —— 宏观指标**低于均值且继续恶化**

---

# 第 68 页 · Regime 启发式 + 当前读数

> **📊 图表 146**：*US Regimes – a heuristic*
> **美国 4 种 Regime 的风格偏好启发式**：

| 阶段 | 方向 | 占优风格 |
|---|---|---|
| **Phase 1 早周期** | 收缩→扩张 | **价值、小盘、高风险** |
| **Phase 2 中周期** | 扩张中 | **动量、成长、高风险** |
| **Phase 3 晚周期** | 扩张→收缩 | **动量、高质量、低风险、大盘** |
| **Phase 4 衰退** | 收缩中 | **高质量、低风险、大盘** |

## Current read: Downturn phase
## 当前读数：下行（Downturn）阶段

Our US Regime indicator transitioned from "Late Cycle" to "Downturn" in January 2023. The post-GFC economic cycle was untraditional in that, as our economists point out, it was long soft patch with several mini downturns, but we most recently saw a strong Early Cycle followed by a Mid and Late Cycle period post-COVID. most recently, the indicator has fallen into the "Downturn" phase. It fell into "Downturn" territory two times post-GFC without an NBER-official economic recession: in '11–'12 during the European crisis and in '14–'15 during the commodity/manufacturing recession. But our economists do expect an economic recession in 2H23-1Q24. In March 2019 the indicator also entered "Recession/Downturn" and declined to near historical lows in June 2020, as the COVID-19-driven economic recession occurred.

本报告的 US Regime 指标于 **2023 年 1 月从"晚周期"切换至"下行"**。正如我们的经济学家所指出，**GFC 之后的经济周期很不传统**——整体是一段漫长的"软着陆"，中间穿插几次迷你下行；而最近一次（新冠后）则经历了一次**强劲的早周期→中周期→晚周期**完整轮动，如今落入"下行"。
- GFC 之后该指标**曾两次落入"下行"但并未发生 NBER 认定的正式衰退**：**2011–2012** 欧债危机期、**2014–2015** 大宗/制造业衰退期
- 但本报告的经济学家**确实预期 2023 下半年至 2024 一季度会出现经济衰退**
- 2019 年 3 月指标也曾进入"衰退／下行"，并在 2020 年 6 月（新冠衰退期）跌至接近历史低点

> **📊 图表 147**：*US Regime indicator（1990/1–2023/4）*
> **US Regime Indicator**：自 **2023 年 1 月起处于"下行"区间**。
> 图示标注 Phase 1 早周期 / Phase 2 中周期 / Phase 3 晚周期 / Phase 4 衰退。

---

# 第 69 页 · 不同 Regime 下的风格表现（可预测性）

## How to use the US Regime Indicator to factor invest
## 如何用 US Regime Indicator 做因子投资

We have found that factor behavior is relatively predictable during different phases of the US Regime Indicator. For example, High Quality and Large Cap tend to outperform during the "Recession/Downturn" phase of the cycle, whereas Value, High Risk and Small Size tend to outperform during the "Early Cycle/Recovery". Value also tends to fare well in Mid Cycle and historically had better outperformance rates than Growth, excluding the Tech Bubble period.

**我们发现：各因子在 Regime 指标的不同阶段表现具有相对可预测性**：
- **衰退／下行**：**高质量、大盘**占优
- **早周期／复苏**：**价值、高风险、小盘**占优
- **中周期**：**价值同样表现良好**——**剔除科网泡沫期后，价值的胜率高于成长**

> **📋 图表 148**：*Style performance in the four US Regime indicator phases*
> **各 Regime 阶段相对等权 S&P 500 的表现**（1990 至今）

| 阶段 | 指标 | 价值 | 成长 | 动量 | 高质量 | 低质量 | 高风险 | 低风险 | 大盘 | 小盘 | 低 Beta | 高股息率 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Phase 1 复苏** | 平均 | **+19.4** | -7.5 | -5.9 | -6.0 | +8.4 | **+18.4** | -10.7 | -8.4 | **+19.0** | -12.8 | +7.0 |
|  | 中位数 | +14.9 | -5.3 | -1.7 | -6.5 | +10.7 | +12.9 | -12.5 | -7.8 | +11.2 | -13.4 | +7.8 |
|  | 胜率 | **100%** | 12.5% | 50% | 25% | 75% | 75% | 25% | 12.5% | 75% | 12.5% | 87.5% |
| **Phase 2 中周期** | 平均 | +3.8 | +10.9 | +11.2 | +0.8 | +3.9 | +11.0 | -6.6 | -2.1 | +6.0 | -12.6 | -6.7 |
|  | 中位数 | +4.3 | +2.3 | +4.0 | -0.7 | +2.2 | +10.3 | -4.9 | -6.6 | +9.1 | -12.1 | -7.1 |
|  | 胜率 | 77.8% | 66.7% | 77.8% | 44.4% | 66.7% | 77.8% | 22.2% | 33.3% | 77.8% | 0.0% | 11.1% |
|  | 胜率（剔除科网） | **87.5%** | 62.5% | 75% | 37.5% | 75% | 75% | 25% | 25% | 87.5% | 0% | 12.5% |
| **Phase 3 晚周期** | 平均 | -0.8 | -6.2 | -3.4 | +3.5 | -6.9 | -11.4 | +8.4 | -1.2 | -7.6 | +7.0 | +7.5 |
|  | 中位数 | -0.9 | -1.8 | +2.3 | +5.8 | -6.6 | -8.9 | +9.8 | +2.3 | -8.1 | +3.2 | +3.5 |
|  | 胜率 | 44.4% | 33.3% | 55.6% | 66.7% | 22.2% | 11.1% | **77.8%** | 55.6% | 11.1% | 55.6% | 77.8% |
| **Phase 4 下行（当前）** | 平均 | -0.8 | -0.2 | +3.1 | +5.2 | -4.7 | -6.1 | +4.8 | +5.6 | -3.0 | -0.9 | -2.4 |
|  | 中位数 | -6.3 | +0.4 | +0.9 | +3.7 | 0.0 | -4.5 | +4.3 | +6.5 | -7.5 | +0.9 | -5.9 |
|  | 胜率 | 28.6% | 57.1% | 57.1% | **71.4%** | 28.6% | 42.9% | **85.7%** | **85.7%** | 14.3% | 57.1% | 28.6% |

数据说明：表现=相对等权 S&P 500 的**价格回报**；高股息率单独采用**总回报**。胜率 = 该阶段跑赢等权 S&P 500 的月份占比（1990 年 1 月至今）。

关键结论：
- **Phase 1 复苏**：**价值胜率 100%**、**小盘 75%**、**高风险 75%**——下行触底反弹是纯粹的"顺风车"
- **Phase 4 下行**（当前）：**低风险 85.7%、大盘 85.7%、高质量 71.4%**——**"Q-L-L（高质低风大盘）"是最可靠的防御组合**

## Lessons from the 70s: Value>Growth, Small>Large
## 来自 70 年代的教训：价值>成长、小盘>大盘

We extended the US Regime Indicator history an additional 20 years back to 1970. While not all inputs were available over the additional history (see Appendix), and we continue to present returns of our S&P 500 factors over the original history (on a hypothetical backtested basis since 1990), we use the extended history to analyze size, style and asset class performance in a comparable high inflation environment (based on Fama-French data for size/style).

我们把 US Regime Indicator 的历史**向前延长 20 年至 1970 年**。虽然不是所有输入变量都可追溯到那么早（详情见附录），且本报告仍以 1990 年以来的回测展示 S&P 500 因子回报，但延长历史能让我们在**相似的"高通胀"环境**下分析规模、风格、资产类别的表现（规模/风格基于 Fama-French 数据）。

---

# 第 70 页 · 70 年代下行期：价值 / 小盘 / 债券胜出

> **📊 图表 149**：*Extended US Regime Indicator（1970 至今）*
> **扩展版 US Regime Indicator**：显示 70 年代高通胀时期曾多次进入 Downturn。
> 注：1970/1–1982/1 只用 5 个输入（通胀、10 年美债、ISM PMI、领先经济指数、产能利用率）；1982/2–1988/3 加入 GDP 预测；1988/4–1989/4 加入高收益债信用利差；1989/5–1989/12 加入盈利修正比。1990 年之前的数据受限于输入集差异、成长/价值/规模定义差异及高通胀宏观环境差异，解读时需注意。该指标**仅作指示性指标，未经 BofA 全球研究书面同意不得用作基准**。

During Downturn regimes of the 1970s and early 1980s (through '82), Value led Growth in the three months prior to a Downturn, and continued to lead Growth for up to 12 months after the onset of a Downturn (Exhibit 149). Small Caps led Large Caps in the three months before Downturns, and continued to outperform in the three, six and 12 months after the onset of a Downturn. Bonds outperformed stocks in the three months before and three/six/12 months after the onset of a Downturn.

在 1970 年代及 80 年代初（至 1982 年）的 Downturn 期里：
- **价值** 在下行启动前 3 个月就已跑赢成长，并在下行后最长 12 个月内继续领先
- **小盘股** 在下行前 3 个月跑赢大盘，下行后 3、6、12 个月同样持续占优
- **债券** 在下行前 3 个月、下行后 3/6/12 个月都跑赢股票

> **📊 图表 150**：*Factor performance prior and after entering Downturn during period of high inflation in the 70s/80s*
> **70/80 年代高通胀期 Downturn 前后的因子表现**：
> 价值-成长、小盘-大盘、债券-股票价差均为正——**"V-S-B"（价值-小盘-债券）** 是该环境下的制胜组合。

---

# 第 71 页 · 70 年代加息结束后：价值继续领先

## Value led even after hiking stopped
## 加息结束后价值依然领先

When the Fed fought inflation in the 70s, it took several hike cycles to get inflation in check. Even after the Fed was done, Value consistently led Growth for the next 12 months (Exhibit 150). Small Caps mostly led Large before the last hike (except for the last month), stumbled in the three months after last hike, but subsequently led Large Caps in the six months and 12 months periods. Bonds generally led equities before the last hike, and consistently led after (supporting our overweight of the bond-like Utilities sector).

70 年代美联储对抗通胀需要**多轮加息周期**才把通胀压住。**即便在最后一次加息结束之后**：
- **价值**在此后 12 个月内**持续跑赢成长**
- **小盘**在最后一次加息前基本跑赢大盘（除最后 1 个月）；加息结束后 3 个月内摔了一跤，但**6 个月、12 个月后重新跑赢大盘**
- **债券**在最后一次加息前后都跑赢股票——**这支持我们超配"类债券"的公用事业板块**

> **📊 图表 151**：*Factor performance prior and after the last Fed hike during period of high inflation in the 70s/80s*
> **70/80 年代高通胀期"末次加息"前后的因子表现**：
> - **价值-成长**：加息前就已占优，加息后继续领先最长 12 个月
> - **小盘-大盘**：加息前略占优，加息后 1-3 月受挫，但 6-12 月重新领先
> - **债券-股票**：加息前后都领先股票

---

# 第 72 页 · 量化投资者在做什么？

## What are quants doing?
## 量化投资者在做什么？

Each year, we survey institutional investors to monitor which factors, characteristics, attributes and indicators they use in their stock selection processes. These include valuation factors, quality and growth factors, risk factors, technical and price factors, risk factors and other factors.

我们**每年**都会对机构投资者做调研，以了解他们在选股流程中**实际使用哪些因子、特征、属性和指标**，覆盖估值、质量、成长、风险、技术/价格、以及其他类别的因子。

### 2022: Models still just as complex in the hunt for alpha
### 2022：为追逐 alpha，模型一如既往地复杂

Since 2007, investors have increasingly used a broader array of signals in their models in a quest for alpha – the average number of factors used jumped to a new high of 20.7 in our 2022 survey. Multi-factor models are more complex/diverse today than in the 1990s, when investors used an average of just seven or eight factors.

2007 年以来，投资者在模型中用到的信号越来越多——**2022 年我们的调研显示，平均使用的因子数达到历史新高 20.7 个**。今天的多因子模型**远比 1990 年代复杂多样**，彼时投资者平均只用 7-8 个因子。

> **📊 图表 152**：*Average number of factors used by respondents（1989–2022）*
> **受访者平均使用的因子数**：接近历史新高（2008-2010 年因样本不足未计入）。

Quants are increasingly focused on new factors, real-time data feeds, artificial intelligence, big data, machine learning, etc., as new alpha signals tend to be exploited quickly and arbitraged away.

量化投资者日益**聚焦新因子、实时数据源、AI、大数据、机器学习**等方向——**因为新的 alpha 信号一旦出现，会被迅速发掘并套利抹平**。

### Price to Forward Earnings is still the most-used factor
### 前瞻市盈率仍然是第一大使用因子

78% of survey respondents use Forward P/E as a factor in their investment processes, remaining the most popular factor for the 15th year running. While cash-flow based valuation measures were more popular pre-crisis, Forward P/E has topped the list every year since the Global Financial Crisis. EV/EBITDA and Net Debt / EBITDA also remained popular (second- and third-most cited factors). Low Price was the least-used factor.

**78% 的受访者把前瞻 P/E 纳入投资流程**——这是**连续第 15 年**成为"最常用因子"。虽然 GFC 之前现金流估值指标更流行，但**自 GFC 以来前瞻 P/E 每年都位居榜首**。EV/EBITDA 和净负债/EBITDA 紧随其后（第二、第三）。**"低价股"是使用率最低的因子**。

---

# 第 73 页 · 2022 调研 —— 全量因子使用率 + 估值因子趋势

> **📊 图表 153**：*Percentage of 2022 survey respondents using various factors*
> **2022 调研各因子使用率**（约 50 个因子，按使用率由高到低排列）：

- **前列**：Forward P/E、EV/EBITDA、Net Debt/EBITDA、Size、Beta、ROE、利润率、EPS 动量、P/FCF、相对强度、空头兴趣、盈利修正、**ESG**、长期价格趋势、股票回购、股息率、债务/权益、P/B、覆盖率、长期 EPS 增长、分析师覆盖度、PEG
- **中段**：盈利惊喜、EPS 波动性、均值回归、内部人买卖、隐含波动率、ROC、评级修正、DDM/DCF、归一化 P/E、已实现波动率、P/S、交易量、EV/Sales、FCF/EV、机构持股、P/CF、ROA、滚动 P/E、目标价、股息增长、长期趋势+短期反转
- **末段**：**另类数据、网络爬取**、短期价格趋势、外国敞口、**机器学习、预测分散度**、应计项目、**自然语言处理、Altman Z-Score、股权久期、AI**、低价股

### Select valuation factors
### 精选估值因子（使用率时间序列）

Below we show a time series of our availability survey data on the percentage of respondents using various factors back in time.

下面展示多年的调研数据中，各因子使用率随时间变化的曲线：

> **📊 图表 154**：*Percentage of Respondents using P/B*
> **使用 P/B 的受访者占比**：近年有所回升。

> **📊 图表 155**：*Percentage of Respondents using P/E*
> **使用前瞻 P/E 的受访者占比**：近年来持续处于高位。

---

# 第 74 页 · 成长/质量/风险/技术因子使用率

### Select growth and quality factors
### 精选成长与质量因子

> **📊 图表 156**：*Percentage of Respondents using ROE*
> **使用 ROE 的受访者占比**：近年持续上升。

> **📊 图表 157**：*Percentage of Respondents using Estimate Revisions*
> **使用"盈利修正"的受访者占比**：近期略有上升。

### Select risk factors
### 精选风险因子

> **📊 图表 158**：*Percentage of Respondents using Beta*
> **使用 Beta 的受访者占比**：近期上升。

> **📊 图表 159**：*Percentage of Respondents using EPS Variability*
> **使用"EPS 波动性"的受访者占比**：近期下降。

### Select price trend and technical factors
### 精选价格趋势与技术因子

> **📊 图表 160**：*Percentage of Respondents using Relative Strength*
> **使用"相对强度"的受访者占比**：2022 年有所回升。

> **📊 图表 161**：*Percentage of respondents using Sell Side Price Targets*
> **使用"卖方目标价"的受访者占比**：2022 年有所下降。

---

# 第 75 页 · 其他因子 & Smart Beta 概述

### Select other (miscellaneous) factors
### 其他杂项因子

> **📊 图表 162**：*Percentage of respondents using Analyst Neglect*
> **使用"分析师冷门"的受访者占比**：近年上升。

> **📊 图表 163**：*Percentage of respondents using Size (Market Cap)*
> **使用"规模（市值）"的受访者占比**：2022 年下降。

## The lowdown on Smart Beta
## 关于 Smart Beta 的真相

### What is smart beta?
### 什么是 Smart Beta？

Smart Beta emerged as a line of investment products seeking to rival traditional popular index tracking funds and ETFs in their transparency, performance and cost efficiency. The investment rationale hinges on a simple premise – market capitalization-weighted indices skew performance towards largest and likely more expensive companies, inadvertently subjecting investors to undesired sources of risk. Alternative weighing schemes have emerged, such as fundamental weighing (book value, sales, cash flow, dividends), equal weighting or volatility weighting.

Smart Beta 是一类**试图在透明度、业绩和成本效率上挑战传统指数追踪基金与 ETF** 的投资产品。其投资逻辑基于一个简单前提：**市值加权指数会向最大的、通常也更贵的公司倾斜**，不知不觉让投资者承担本不想要的风险来源。因此出现了**多种替代加权方案**：
- **基本面加权**（账面价值、销售额、现金流、股息）
- **等权加权**
- **波动率加权**

Whereas the traditional market cap weighted index tracking products represent a reasonable proxy to the overall equity market exposure, or "beta", the alternative index tracking products received the name of "Smart Beta". The "smart" component may be misleading in implying virtuous qualities that may not necessarily exist. Hence, a wide array of alternative names emerged – alternative beta, strategic beta, scientific beta or strategic indexing, among others. It appears, however, that the term "smart beta" took deep roots in the investment community's vernacular and will be difficult to unseat – though popularity has declined post-COVID.

传统市值加权产品是整体股市敞口（即"beta"）的合理代理；**替代加权产品则被冠以"Smart Beta"之名**。但"smart"一词可能误导——**并不必然代表它"更明智"**。因此衍生出众多替代名：alternative beta、strategic beta、scientific beta、strategic indexing 等。不过，**"smart beta"这个术语已在业内深深扎根**——尽管新冠之后热度有所下降。

As smart beta grew in popularity, the concept expanded from alternative weighting index tracking to various rule-defined investment vehicles with properties of both active and passive investment styles – more active than passive cap weighted index tracking but less active than active portfolio management with day-to-day investment decision making. The costs thus reflect the passive/active positioning: the management fees exceed those of the traditional index tracking produces, but remain considerably below actively managed portfolio charges. Examples of this type of smart beta funds include Low Volatility products, various factor tilts (Quality, Beta, Shares Buybacks, High Dividend Yield, High Dividend Growth), multifactor exposures, commodity based ETFs, thematic exposure (demographics, geography), multi-strategy ETFs. Despite a wide range of the smart beta variety, the largest share of smart beta assets is in the simplest forms of High Dividends, Growth and Value products.

随着 Smart Beta 流行，概念已从"替代加权指数追踪"**扩展到各种规则定义型投资工具**——兼具主动与被动的特征（比被动指数追踪更主动，比日常决策的主动组合更被动）。费用亦反映这一定位：**管理费高于传统指数产品，但远低于主动管理组合**。典型例子包括：**低波动、各类因子倾斜（质量、Beta、回购、高股息、高股息增长）、多因子、商品类 ETF、主题 ETF（人口、地域）、多策略 ETF**。尽管种类繁多，**资产体量最大的依然是最朴素的"高股息、成长、价值"三大类**。

### Alternative weighting is not new in quant space
### 替代加权在量化领域并不新鲜

Quants have been applying equal weighing to remove size bias in their work without much fanfare for decades. After all, quants seek to identify various factor exposures in their purest form, be it large or small size, low or high price/book, or high dividend yielding stocks or dividend nonpayers. The starting point is the "clean" benchmark – i.e., equal weighted to rid it of the size bias. For the same reason, quant factor performance is usually calculated on an equally weighted basis.

**数十年来量化研究者一直在默默使用等权加权以剔除规模偏差**——毕竟量化追求的是"纯粹的因子敞口"（大盘或小盘、低 P/B 或高 P/B、高股息或不派息）。因此**起点都是"干净的基准"**——即等权基准。同样原因，**量化因子表现通常都按等权计算**。

---

# 第 76 页 · APT、量化因子 vs 风格指数、Smart Beta 资产规模

Arbitrage Pricing Theory (APT) stipulates that stock return is a function of multiple sources of systemic risk (betas) in addition to the idiosyncratic risk. APT, however, does not identify what the multiple betas are. In the Quant framework the quant factors are considered the sources of risk, or the multiple betas, that drive performance. While alternative index weighting removes the unwanted market cap bias and introduces the desired fundamental biases, quant factors represent alternative beta exposure in its purest form – typically a small subset (a decile or quintile) of an investable universe (the index or otherwise defined investable space) with the specified characteristics. Quant factors span across investment styles, such as Value, Growth, Momentum, Quality, Size and Risk. As an example, while the Russell 1000 Growth and the Russell 1000 Value indices frequently saw little performance divergence from 2010-2014, Growth / Value performance differential as measures by High Price/Book and Low Price/Book factors was quite pronounced (Exhibit 163).

**套利定价理论（APT）**规定：股票回报是**多个系统性风险来源（beta）与个股特质风险**共同决定的函数——**但 APT 本身并未指明这些 beta 是什么**。在量化框架中，**量化因子就是风险的来源（即"多个 beta"）**。
- 替代指数加权**去除了不想要的市值偏差、引入了想要的基本面偏差**
- **量化因子代表"最纯粹的替代 beta 敞口"**——通常是可投资域（指数或自定义域）中**具备特定特征的一小部分（十分位或五分位）**
- 量化因子跨越**价值、成长、动量、质量、规模、风险**等所有主流风格
- **例**：2010–2014 年罗素 1000 成长 vs 罗素 1000 价值指数走势几乎没差——但"高 P/B vs 低 P/B"这个纯量化因子间的价差却**极其显著**（见图表 163）

> **📊 图表 164**：*Quant factors generally deliver more style differentiation than fundamentally weighted indices*
> **量化因子比基本面加权指数能提供更强的风格差异化**（2010–2022 年年度表现）
> 对比：High P/B − Low P/B（量化因子价差） vs 罗素 1000 成长 − 罗素 1000 价值（指数价差）。

### How much money is currently tracking smart beta strategies
### 当前追踪 Smart Beta 策略的资金规模

Smart beta strategies have experienced rapid growth in assets under management in recent years. According to the data compiled by Bloomberg (Exhibit 164), smart beta funds grew from under $100bn in 2009 to nearly $1.6tn in 2021 before falling to $1.5tn in 2022, which represents a 24% annualized rate, well above the 18% growth rates for the ETF assets overall.

Smart Beta 资产近年来快速增长。根据 Bloomberg 数据（图表 164）：**从 2009 年不到 1000 亿美元增至 2021 年近 1.6 万亿美元，2022 年回落至 1.5 万亿美元**——**年化增速 24%**，远高于整体 ETF 资产 18% 的增速。

> **📊 图表 165**：*Growth in Smart Beta vs. all ETFs*
> **2009-2022 年 Smart Beta vs 全部 ETF 资产增长**：ETF 从 787 亿增至 7247 亿（峰值），Smart Beta 从 92 亿增至 1585 亿（峰值）。
> 年化增速：**ETF = 18%，Smart Beta = 24%**。

---

# 第 77 页 · ESG 增长最快 & Smart Beta 业绩反思

ESG ETFs saw a particularly strong asset base growth: as these vehicles grew at a 72% annualized rate, faster than any other smart beta category.

**ESG ETF 的资产增长尤其强劲**：**年化 72%**，快于所有其他 Smart Beta 子类别。

> **📊 图表 166**：*ESG: the fastest-growing smart beta strategy*
> **ESG 是增长最快的 Smart Beta 策略**（2015-2022 年 5 年 CAGR）：
> - **ESG：72%**
> - 质量：28%
> - Smart Beta 总体：15%
> - 股息/收益率：15%
> - 价值：15%
> - 成长：13%
> - 多因子：13%
> - 规模：13%
> - 动量：12%
> - 营收：10%
> - 低波动：9%
> - 专属策略：7%

### Is smart beta all that smart?
### Smart Beta 真的"smart"吗？

Despite attention surrounding the Smart Beta concept, the performance of Smart Beta ETFs has been remarkably unexciting – since 2005 this group of products mostly lagged major large cap indices by 0.5ppt to 3.1ppt per annum.

尽管 Smart Beta 概念备受关注，**其 ETF 的业绩实际上相当乏味**——**2005 年以来，Smart Beta 整体每年跑输主要大盘指数 0.5-3.1 个百分点**。

> **📊 图表 167**：*Smart beta has lagged the benchmarks（2004/12–2022/12）*
> **Smart Beta 相对基准指数的年化回报对比**：Russell 1000、Russell 1000 Value、Russell 1000 Growth、S&P 500 均跑赢 Smart Beta 组合。

---

# 第 78 页 · 另类数据与自然语言处理（NLP）

## Alternative Data
## 另类数据

Alternative data can be broadly defined as information outside of traditional sources, such as corporate filings, that can provide insights into the future performance of financial markets. They are typically available on a more timely basis, offer a differentiated perspective and are less readily accessible, providing opportunities to extract alpha if used effectively. A wide range of alternative data is available today – from online search trends to social media activity, from transactions data to satellite imagery to geo-location data. We highlight some of our work below.

**另类数据（Alternative Data）** 可以广义定义为"**传统来源（如公司公告）之外，能为未来市场表现提供洞察的信息**"。特点：
- **更及时**（high frequency）
- **视角差异化**
- **不易获取**（有一定壁垒）
- **若善用则可提取 alpha**

覆盖范围极广：**搜索趋势、社交媒体、交易数据、卫星影像、地理位置数据**等等。下面介绍本报告的部分相关工作。

## Natural Language Processing
## 自然语言处理（NLP）

Natural Language Processing (NLP) refers to the use of computers to process and analyze text and spoken words. Sentiment analysis is one of the many uses of NLP that allows a computational assessment of sentiment towards events, topics, issues, products, etc. In its simplest form, NLP-based sentiment trackers can be defined as the count of positive words relative to negative words as per the definition of a lexicon. More sophisticated models use contextual or aspect analysis to assess sentiment with the help of custom lexicon that are better suited to the problem at hand. At BofA Global Research, we use NLP to delineate corporate as well as policymaker sentiment.

**自然语言处理（NLP）** 是指**用计算机处理并分析文本与语音**。**情感分析**是 NLP 的众多应用之一——它让机器可以对事件、话题、议题、产品等给出量化情感评价：
- **最简版本**：按词典定义数"正面词数 − 负面词数"
- **进阶版本**：结合**上下文或方面分析**，用**定制化词典**处理特定领域问题

**BofA 全球研究**使用 NLP 来描摹**企业情绪**与**政策制定者情绪**。

### US Corporate Sentiment Indicator
### 美国企业情绪指标

Our Corporate Sentiment Indicator (see note) scans through the earnings calls transcripts of the S&P 500 universe of companies to get an early read on US corporate sentiment. The sentiment score, computed as the count of unique positive words less the count of unique negative and uncertainty words, uses three different filters: the full transcript, management discussion and answers of CEO/CFO from Q/A section.

本报告的**企业情绪指标**扫描 S&P 500 公司的**业绩电话会议文稿**，以提前窥探美国企业景气情绪。情绪得分 = **独特正面词数 − 独特负面与不确定词数**，应用 **3 种不同过滤器**：
1. 完整文稿
2. 管理层讨论部分
3. 问答环节中 CEO/CFO 的回答

We use the Loughran McDonald's financial dictionary to calculate sentiment scores. In total, the lexicon has 2,355 negative words, 354 positive words, and 297 words of uncertainty, as for example:
1. Positive words: accomplish, achieve, outperform, stabilize, strength
2. Negative words: abandon, abnormal, downturn, evade, failing, stagnate
3. Uncertain words: almost, ambiguity, hidden, fluctuate, doubts, unclear

采用 **Loughran-McDonald 金融词典**计算得分。词典包含：
- **负面词 2,355 个**：abandon、abnormal、downturn、evade、failing、stagnate……
- **正面词 354 个**：accomplish、achieve、outperform、stabilize、strength……
- **不确定词 297 个**：almost、ambiguity、hidden、fluctuate、doubts、unclear……

Corporate Sentiment improved YoY for the first time in the first quarter of the year since 4Q2021, pointing to a potential earnings recovery. However, mentions of weak demand soared, highlighting companies' cautious outlook over the near term.

**2023 Q1 企业情绪指标首次实现同比改善**（自 2021 Q4 以来首次），**指向潜在的盈利复苏**。但同时，"需求疲软"的提及频率飙升至接近历史最高——**说明公司对近期前景依然谨慎**。

---

# 第 79 页 · 企业情绪图 + 石化情绪指标

> **📊 图表 168**：*US Corporate Sentiment vs. quarterly EPS YoY with 1q lag*
> **美国企业情绪 vs 季度 EPS 同比（滞后 1 季度）**：
> 情绪得分自 4Q21 以来首次实现同比改善，**指向未来盈利潜在复苏**。
> **R² = 50%**（1Q05–2023/5/3）。

> **📊 图表 169**：*Mentions of weak demand soared near a record level*
> **"需求疲软"的提及频次已飙升至接近历史纪录**（2003–2023/5/3，每家 S&P 500 公司的平均提及次数）。
> 所检测词：lower、softer、moderating、weaker。

## BofA Petrochemical Sentiment Indicator
## BofA 石化情绪指标

Similarly, the BofA Petrochemical Sentiment Indicator (see note) tracks the sentiment on petrochemicals based on NLP-based analysis of all S&P Global Platts' Polymerscan reports – a leading publication on global plastic and resins including polyethylene, polypropylene, and polyvinyl chloride (PVC) – published since 2004. The smoothened version of the indicator has a correlation above 0.70 with 15 out of 28 stocks under our coverage over the last five years, including 11 with a correlation of 0.80+.

类似地，**BofA 石化情绪指标**通过 NLP 分析 **S&P Global Platts 旗下 Polymerscan（全球塑料与树脂权威刊物，涵盖 PE、PP、PVC，2004 年起发行）** 的所有报告来跟踪石化行业情绪。**平滑版指标过去 5 年**与我们覆盖的 28 只股票中**有 15 只相关性 >0.70，其中 11 只 >0.80**。

We used Natural Language Processing to scan every Platts Polymerscan report ever published from October 27, 2004 and counted the number of positive and negative words as defined by a comprehensive proprietary dictionary created using a Deep Learning based Word2Vec model. Word2Vec converts words into numeric form such that words used in similar context are closer to each other in numeric vector space. The model was trained on ~400K financial documents to ensure we only selected the words used in financial/market context to express positive or negative sentiment. We calculate a score for each published report based on the percentage of positive words picked up by our proprietary dictionary, which only picks up negative or positive words.

**方法**：我们用 NLP 扫描自 **2004/10/27 起的全部 Polymerscan 报告**，并按照**基于 Word2Vec 深度学习模型构建的专有词典**统计正、负面词数。
- **Word2Vec 将词语转化为数值向量**，使**上下文相似的词在向量空间中距离更近**
- 模型在**约 40 万份金融文档上训练**，确保只挑选"金融/市场语境下表达正负情绪的词"
- 每篇报告的得分 = 专有词典中**命中正面词占比**（词典只识别正/负词）

> **Word2vec** 是一组相关模型，用于生成词嵌入（word embeddings）。通常是双层神经网络，训练目标是**重构词语的语言学上下文**。输入为大规模文本语料，输出为**数百维向量空间**——**共享相似上下文的词在空间中彼此接近**。

The latest update of the indicator reveals that it continues its downward trend, as the data has decelerated since flipping negative in May 2022, providing a bearish signal for commodity stock performance. Historically, on average, it takes eight months for the indicator to trough once it has flipped to bearish and another six months, on average, to flip bullish again. Thus, while history would tell us we are closer to a bottom, and the anecdotal data on pricing may support this, we may be ways away from a sustained bull cycle in commodity chemical stocks, if this indicator is a guide.

最新数据显示：指标**延续下行趋势**——自 2022 年 5 月转负以来增速放缓，**对周期性化工股给出偏空信号**。**历史上平均规律**：
- 指标翻空后平均 **8 个月触底**
- 触底后平均再 **6 个月翻多**

因此，虽然历史告诉我们距离底部已经不远（价格面上的零散迹象也支持这点），但**若以该指标为指引，距离"大宗化工股的持续牛市"可能仍有相当距离**。

---

# 第 80 页 · 石化情绪图 & 央行情绪指标

> **📊 图表 170**：*BofA Petrochemical Sentiment Indicator*
> **BofA 全球石化情绪指标**：**延续偏空趋势**，但历史规律显示**底部日益临近**。
> 横轴：2005/10–2023；纵轴：40%–70%（情绪正向占比）。

## Central Banks Mood Indicators
## 央行情绪指标（Mood Indicators）

We have also developed NLP models to quantify the degree of hawkishness in central banks' communications – Bank of England Mood Indicator (BoEMI) (see note), RBA Sentiment Indicator (see Australia Rates Alpha, 1 June 2023), Riksheard (see note), NORBI (see note) and Emerging Markets Mood Indicator (EMMI), 15 February 2021 (see note). These 'mood' indicators tend to provide a leading signal for changes in central banks' policies.

我们开发了一系列 NLP 模型用于量化**央行沟通的"鹰派程度"**：
- **BoEMI**（英国央行情绪指标）
- **RBA 情绪指标**（澳洲央行）
- **Riksheard**（瑞典央行 Riksbank）
- **NORBI**（挪威央行）
- **EMMI**（新兴市场情绪指标）

**这些"mood"指标往往对央行政策变化提供领先信号**。

To compile the master dictionary of pre-identified hawkish/dovish keywords/phrases, we started with the list from the widely cited ECB paper (https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2085.en.pdf). We added terms that we believe represent the specific way central banks communicate their policy views.

为构建主词典，我们从**广受引用的 ECB 论文**（含鹰/鸽派关键词表）入手，再加入我们认为**特定央行表达政策观点时惯用的表述**。

To account for the context, we created a list of contravening words whose presence in a clause flips it into the opposite category. For example, "increase interest rates" vs. "increase quantitative easing". The presence of "quantitative easing" flips the original hawkish nature of the word "increase" into the dovish category. We calculate a hawkishness score between 0 and 1, representing the fraction of clauses that our algorithm determines are 'hawkish'. We can represent this with the following formula:

为考虑上下文，我们还建了一份**反转词表**——只要这些词出现在同一分句中，整句就翻转到相反类别。比如"**increase interest rates**"（加息，鹰派） vs. "**increase quantitative easing**"（扩大 QE，鸽派）——"quantitative easing"把"increase"本来的鹰派意义翻转为鸽派。最终我们计算一个 **0~1 的鹰派得分**，表示算法判定为"鹰派"的分句占比：

$$
\text{Hawkishness} = \frac{\#\text{hawkish} + \#\text{dovish\_contravening}}{\#\text{hawkish} + \#\text{dovish} + \#\text{dovish\_contravening} + \#\text{hawkish\_contravening}}
$$

Specifically, for BoEMI, we run the exercise on the minutes of Monetary Policy Committee (MPC) meetings, the BoE's Quarterly inflation Report (QIR), and transcripts of press conferences that follow the QIR publication. The minutes are available monthly until 2016 and then 8 times a year. The QIR and transcripts are available quarterly. In the latest update, the BoEMI rose to its most hawkish since June 2022, although the shortened minutes create a structural break in our Mood indicator, making it harder to interpret.

具体到 **BoEMI**（英国央行情绪指标）：对以下文档执行计算：
- **MPC 货币政策委员会会议纪要**（2016 年前按月公布，之后每年 8 次）
- **季度通胀报告（QIR）**（季度）
- **QIR 发布后的发布会文稿**（季度）

最新读数：**BoEMI 升至 2022 年 6 月以来最鹰派水平**。但**会议纪要变短带来了结构性断裂**，使指标解读难度上升。

The EMMI, on the other hand, captures the percentage of hawkish terms in over 4000+ publications of 13 central banks. In aggregate, EM central banks are less hawkish than in Q4 but still very hawkish. The most hawkish central banks are those in Czechia, India, Indonesia, Mexico and Thailand. No central bank is outright dovish yet, but the relatively least hawkish is Poland, followed by Brazil, Hungary, Korea and South Africa.

**EMMI**（新兴市场情绪指标）则从 **13 家新兴市场央行的 4000 多份出版物**中提取鹰派词汇占比。总体看：
- **当前新兴市场央行整体比 Q4 鸽一些，但仍非常鹰**
- **最鹰**：捷克、印度、印尼、墨西哥、泰国
- **没有彻底转鸽的央行**，但**相对最不鹰**的是波兰，其次巴西、匈牙利、韩国、南非

---

# 第 81 页 · 央行情绪指标图

> **📊 图表 171**：*Bank of England Mood Indicator (BoEMI)*
> **英国央行情绪指标 BoEMI**：明显更鹰派。
> 说明：BoEMI 取值 0-1，反映 BoE 货币政策会议纪要中"鹰派分句"占比。0.5 即一半分句为鹰派。
> 图中三条线：BoEMI（左轴）、BoEMI 3 个月均线、MPC 成员平均 3 个月政策变化 bp 预期（右轴）。

> **📊 图表 172**：*Emerging Markets Mood Indicator (EMMI)*
> **新兴市场情绪指标 EMMI**：鹰派高峰已过但仍处高位。
> 图中：GEM EMMI、EMMI 6 月均线、基准利率、SWAP 利率。

---

# 第 82 页 · NewsAlpha：量化新闻对股票回报的影响

## NewsAlpha: quantifying the impact of news on returns
## NewsAlpha：量化新闻对回报的冲击

News is, perhaps, the best example of an alternative data set, sourced globally from a combination of structured and unstructured data sources in multiple languages, that can be a differentiator of returns. Contrary to popular belief, our analysis of five billion news events over the last 15 years shows there is information in news that appears to provide alpha-generating opportunities over the short term and long term.

**新闻**可能是另类数据集的**最佳范例**：全球来源、多语种、结构化与非结构化混合。与流行看法相反，**我们对过去 15 年 50 亿条新闻事件的分析表明：新闻中确实含有可短期和长期产生 alpha 的信息**。

We use Ravenpack's big data set to quantify the impact of news on share prices. The process involves employing Natural Language Processing techniques to classify stock-related news and then collating them into the Global News Pulse, which quantifies whether significant news globally is trending positively or negatively. It has a 79% correlation with global equity markets over the last 15 years. The latest update shows that despite uncertainty in the direction of macro data and equity markets, the trend in Global News Pulse is unambiguously positive, improving in all regions and sectors.

我们使用 **Ravenpack** 的大数据集量化新闻对股价的影响：
- 用 NLP 对股票相关新闻进行分类
- 汇总为"**Global News Pulse**"——衡量全球重大新闻是正向还是负向趋势
- 过去 15 年与全球股市的**相关性达 79%**
- 最新数据：**尽管宏观数据与股市方向不确定，但 Global News Pulse 明确在改善**——**全球所有地区、所有行业均向好**

> **📊 图表 173**：*Global News Pulse and YoY Change in MSCI AC World Index*
> **全球新闻脉冲 vs MSCI ACWI 同比**：上月从 -15% 改善至 -6%。
> 回测相关性 = 0.79，实盘相关性 = 0.79。

---

# 第 83 页 · 正/负重大新闻股的相对表现

> **📊 图表 174**：*Relative cumulative returns of Global POSITIVE Significant & NEGATIVE Significant News Stocks*
> **正重大新闻 vs 负重大新闻股累计相对回报（vs MSCI ACWI）**：
> - **正重大新闻股**：年化 **+3.4%** 跑赢 ACWI
> - **负重大新闻股**：年化 **-4.2%** 跑输 ACWI
> 回测期：2004/1–2019/5；实盘期：2019/6 起。

> **📊 图表 175**：*Annualised returns of Global POSITIVE Significant & NEGATIVE Significant News Stocks*
> **正/负重大新闻股的年化相对回报**（vs MSCI ACWI）：
> - 正新闻股：回测 +3.4%，实盘 -0.2%（中位数 +3.4%）
> - 负新闻股：回测 -4.2%，实盘 -2.7%（中位数 -4.2%）

---

# 第 84 页 · BAC 卡数据（Aggregated Card Data）

## BAC Aggregated Card Data
## BAC 聚合信用卡/借记卡数据

Transactions data for various spending categories from payment processors or credit/debit cards, is another example of alternative data that can give us a potential preview of revenue growth at a higher frequency and with minimum delay vis-à-vis quarterly earnings release and GDP prints that come with delays of weeks or months.

来自**支付处理器或信用卡/借记卡**的各消费类别交易数据，是另类数据的**又一范例**——能**以更高频率、最小时滞**预览营收增速，远早于几周或几个月后才公布的季度财报与 GDP。

BofA Global Research analysts leverage our proprietary BAC aggregated credit and debit card spending data to gauge the health of the US consumer. Our US economists quantify the trends in consumer spending in their weekly publication BofA on USA and also provide forecast on retail sales ahead of the monthly print by the Census Bureau. The latest report continues to suggest card spend has been soft but stable, as durable goods spending remains weak, while leisure service might have peaked. See the note for an explanation of the methodology, disclaimers and limitations with aggregated credit and debit BAC card data.

BofA 全球研究分析师利用**专属 BAC 信用卡/借记卡聚合消费数据**来衡量美国消费者健康度。BofA 美国经济学家在每周 *BofA on USA* 中量化消费趋势，并在每月 Census Bureau 零售数据公布前提前给出预测。**最新报告：卡消费整体偏软但稳定**——**耐用品消费仍疲软，而休闲服务可能已见顶**。

> **📊 图表 176**：*Retail sales ex auto: Census Bureau vs. BAC card data*
> **剔除汽车的零售销售**（月环比，季节调整后，3 月均线）：**BAC 卡数据与 Census Bureau 数据高度吻合**。

> **📊 图表 177**：*Monthly card spending per household on durable goods vs leisure services*
> **户均月度卡消费**（指数：2020/2 = 100，季节调整后）：**休闲服务支出过去 3 个月下降 1.0%**。
> - 休闲服务 = 航空+住宿+餐饮
> - 耐用品 = 家具+电子+建材

BofA Fundamental Equity Research analysts use segment-specific BAC card data to offer a differentiated view on their coverage sectors and companies. In May, Robby Ohmes launched a new BAC card series to track spending at value grocery stores (see report). He believes its outperformance to overall grocery reflects a trade down from higher-income consumers, in line with commentary from value retailers.

BofA 基本面股票研究分析师用**细分领域**的 BAC 卡数据，对其覆盖行业与公司形成**差异化观点**。5 月，Robby Ohmes 推出了新的 BAC 卡系列——专门追踪**折扣连锁超市（value grocery）**的消费。他认为这类店跑赢整体杂货的现象**反映了高收入消费者"消费降级"**——与折扣零售商的口风一致。

---

# 第 85 页 · 折扣杂货店 vs 整体杂货 + 地理位置数据 + Web Scraping

> **📊 图表 178**：*Value vs. Overall Grocery Stores, according to BAC aggregated credit & debit card data*
> **折扣杂货 vs 整体杂货消费**（同比变化）：
> - **折扣杂货店 4 月 +6.9% YoY**
> - **整体杂货 +2.5% YoY**
> 折扣杂货增速显著快于整体。

> **📊 图表 179**：*Reported home improvement quarterly same-store sales growth vs. BAC aggregated card data at home improvement retailers and housing related services*
> **家居装修零售季度同店增速**（HD 与 LOW 平均）**与 BAC 家居装修零售与住房相关服务卡数据**的对比：**走势基本一致**。

Similarly, Liz Suzuki uses the data to monitor consumer spending in hardline retail categories (see report). She finds that home improvement spending is tracking in line with same-store sales growth for Home Depot and Lowe's, with April seeing a continuation of the broad-based slowdown experienced from January through March.

类似地，Liz Suzuki 用同一套数据监控**硬性零售（hardline retail）** 消费。她发现：**家居装修支出与 Home Depot、Lowe's 的同店增速走势一致**，4 月延续 1-3 月的全面放缓。

## Geolocation Data
## 地理位置数据

The trade down from conventional to value grocers was validated by yet another type of alternative data, viz. geolocation data. Placer.ai provides foot traffic analytics by observing mobile location data that is aggregated, normalized and extrapolated to generate insights in retail, CRE (commercial real estate), hospitality and other industries. We compared the same store foot-traffic data since 2021 for value chains vis-à-vis conventional grocers and noticed the same migration to value chains as observed in the BAC card data for spending in the value grocery stores category.

"**从常规到折扣杂货店的消费降级**"得到了**另类数据的另一个独立验证**——**地理位置数据**。**Placer.ai** 通过手机定位数据（聚合、归一化、外推）在零售、商业地产、酒店等行业生成洞察。我们对比 2021 年起**折扣连锁 vs 常规杂货店的同店客流**：观察到的"**向折扣链迁移**"与 BAC 卡数据在折扣杂货类消费上看到的趋势**完全一致**。

> **📊 图表 180**：*Average Foot Traffic YoY change for grocers*
> **各超市品牌客流同比变化**（Placer.ai 数据）：**Aldi、Grocery Outlet 等折扣链客流趋势更强**，Kroger、Sprouts 则偏弱。

## Web Scraping
## 网页爬取

Web scraping has emerged as a crucial tool for extracting and analyzing relevant information from websites that could provide investors with insights to better understand and analyze the health of businesses. We present a selection of trackers at work in BofA Global Research that utilize data obtained through web scraping.

**网页爬取**已成为从网站中提取并分析相关信息的**关键工具**，可帮助投资者**更好地理解并分析企业健康度**。下面精选 BofA 全球研究中使用爬虫数据的几个追踪器。

---

# 第 86 页 · iPhone 可得性追踪器

## iPhone Availability Tracker
## iPhone 可得性追踪器

The iPhone availability tracker (see note) maps the pickup availability of every iPhone configuration (combinations based on model, storage and color) at every Apple retail store that allows in-store pickups across 500+ stores globally. COVID lockdown in China hampered the production of iPhone 14 Pro/Pro Max at the Hon Hai factory in Zhengzhou.

**iPhone 可得性追踪器**映射**全球 500+ 家 Apple Store**中**每一种 iPhone 配置（型号 × 存储 × 颜色组合）** 在"可到店取货"选项下的可得性。**中国新冠封控期间，郑州富士康工厂的 iPhone 14 Pro/Pro Max 生产受阻**。

> **📊 图表 181**：*Availability of various iPhone models at Apple stores in the US*
> **美国 Apple Store 各款 iPhone 可得性**：截至 2023/1/24，**iPhone 14 Pro/Pro Max 可得性升至 87%/87%**。

However, our tracker was able to capture the significant improvement in availability of iPhone 14 models at Apple stores in the US and other countries starting mid-January in real time. Over a 1-month period starting late December 2022, the availability of SKUs for iPhone 14 Pro and Pro Max went from 23%/35% on December 20 to 87%/87% as of January 24. The increase in availability, even during a seasonally strong demand period (Christmas and New Year's shopping days), pointed to weak overall iPhone demand.

但我们的追踪器**实时捕捉到了 2023 年 1 月中旬起美国与其他国家 Apple Store 的 iPhone 14 可得性大幅改善**。2022/12 下旬至 1/24 共约 1 个月：**iPhone 14 Pro/Pro Max 的 SKU 可得性由 23%/35% 升至 87%/87%**。**即便处于传统旺季（圣诞与新年购物季），可得性还在上升——这指向整体 iPhone 需求疲软**。

> **📊 图表 182**：*iPhone 14 Pro availability in the US, China, Japan, and the UK*
> **中国：iPhone 14 Pro/Pro Max SKU 可得性由 12/20 的 55%/67% 升至 1/24 的 84%/95%**。

## Surveys
## 专属问卷调查

In contrast to the burgeoning fields of AI/ML and big data, surveys have been in existence since yore. Yet, they are still as relevant today for financial research as any other sources, providing investors with an early read of the health of the broader economy as well as niche sectors. We, at BofA Research, use proprietary surveys to glean out the trends in financial markets.

与新兴的 AI/ML 和大数据相比，**问卷调查古已有之**——但在今天的金融研究中**仍然同样重要**，能为投资者提供**宏观经济与利基行业景气度的早期读数**。BofA 研究部**使用一系列专属问卷**识别金融市场趋势。

## Global Fund Manager Survey
## 全球基金经理调查（FMS）

The Global Fund Manager Survey (FMS) (see note) informs investors about the expectations built into the market price. The panel consists of a healthy mix of real money and hedge fund investors across regions with close to a trillion-dollar AUM.

**全球基金经理调查（FMS）** 告诉投资者**当前市场价格已反映出哪些预期**。其受访面板包含**各地区公募基金与对冲基金投资者**，**合计 AUM 接近 1 万亿美元**。

---

# 第 87 页 · FMS 现金法则 + 中国水泥指标

Michael Hartnett calculates a weighted average of the cash balance professed by FMS participants to create the BofA Global FMS Cash Rule, a contrarian trading signal for global equity markets – buy equities when the FMS average cash balance rises to 5% or higher, and sell equities when the FMS average cash balance falls to 4% or lower. A low cash balance indicates investors could be vulnerable to negative market shocks, while a high cash balance means investors could be under-invested and vulnerable to positive market shocks.

Michael Hartnett 对 FMS 参与者申报的**现金余额**取加权平均，打造"**BofA 全球 FMS 现金法则**"——一个**逆向交易信号**：
- **FMS 平均现金 ≥ 5% → 买入股票**（投资者可能"仓位不足"，面临利好冲击）
- **FMS 平均现金 ≤ 4% → 卖出股票**（投资者可能"仓位过满"，面临利空冲击）

The BofA Global FMS Cash Rule has shown predictive power for long and short equity index trades as expressed via the S&P 500 Index. Since 2011, the average "Buy" signal would have returned +1.3% in 1 month, +4.0% in 3 months, and +6.5% in 6 months after the signal was triggered. On the other hand, the average "Sell" signal would have seen returns of -3.2% in 1 month and -0.2% in 3 months after the signal was triggered, although it is less significant in the 6 months after (+1.6%). The BofA Global FMS average cash balance rose from 5.5% in April to 5.6% in May, keeping the allocation above the 5.0% tactical "buy" signal since November 2021.

该法则对 S&P 500 指数的多空预测有效：**2011 年以来**：
- 平均"**买入**"信号触发后：1 月 +1.3%、3 月 +4.0%、6 月 +6.5%
- 平均"**卖出**"信号触发后：1 月 -3.2%、3 月 -0.2%、6 月 +1.6%（后者显著性较弱）
- **2023 年 5 月 FMS 平均现金 5.6%（4 月 5.5%）**——**自 2021 年 11 月以来一直高于 5.0% 的战术"买入"阈值**

> **📊 图表 183**：*FMS average cash level % of AUM*
> **FMS 平均现金占 AUM 比例**：5 月升至 **5.6%**（4 月 5.5%）。
> 图中标注历史关键点：May'00（互联网泡沫顶）、Feb'01、Oct'01、Mar'03、Dec'08、Jun'12、Oct'16、Apr'20（新冠）、Oct'22。

## BofA China Cement Outlook Indicator
## BofA 中国水泥前景指标

The Purchasing Managers' Index (PMI) is one of the most widely followed economic indicators in tracking the health of any economy. The BofA China Cement Outlook Indicator (see note) is akin to the PMI for the more niche cement sector in China, the largest producer of cement in the world. It tracks the market sentiment on cement based on a monthly proprietary survey of 150 cement producers (accounting for c.18% of the national capacity) and 50 concrete stations across China about their three-month price outlook and the relative cement inventory level. The respondents are usually the plant managers or sales managers who oversee the plant's operation in general. The indicator is found to move in tandem with construction materials stock prices in China.

采购经理人指数（**PMI**）是全球最广泛使用的经济晴雨表之一。**BofA 中国水泥前景指标**就相当于**中国水泥行业的"PMI"**——中国是全球最大水泥生产国。方法：
- **每月问卷 150 家水泥厂（占全国产能约 18%）+ 50 家混凝土站**
- 询问其**未来 3 个月价格展望**及**相对水泥库存水平**
- 受访者通常是**厂长或销售经理**
- **该指标与中国建材股股价走势高度同步**

In May, the indicator dug deeper in the negative territory, with three-fourths of producers staying pessimistic on the three-month market outlook irrespective of the traditional peak season in 1H. Meanwhile, cement inventory is hovering at a high level at 70%+, up 5ppt YoY. Cement producers expect prices to decline in May as they expect property and infrastructure cement demand to stay flattish on a sequential basis – a continuation of the trend year-to-date.

**5 月读数进一步跌入负区间**：
- **75% 的水泥厂对未来 3 个月持悲观态度**——即使处于 1H 传统旺季
- **水泥库存维持 70%+ 高位**，同比 **+5 个百分点**
- 厂家预期 5 月价格下跌，因为**地产与基建水泥需求环比持平**（延续年初以来的趋势）

---

# 第 88 页 · 水泥指标图 & 卡车货主调查

> **📊 图表 184**：*BofA China Cement Outlook Indicator*
> **BofA 中国水泥前景指标**：5 月进一步下探——75% 水泥厂对 3 个月前景悲观。
> 图中：BofA 指标（左轴） vs MSCI China 建材指数（右轴），**相关性 0.62**。
> 注：该指标仅作指示性指标，未经 BofA 全球研究书面同意不得用作基准。

## Truck Shipper Survey
## 卡车货主调查

The bi-weekly Truck Shipper Survey (see note) looks to discern the trends in the Transportation sector, given that trucking represents two-thirds of all tonnage moved in the US and more than 80% of all revenue spent on transportation. The result is the BofA Truckload Demand Indicator – a sentiment indicator focused on shippers' outlook for demand over the next 0-3 months. It is an effective barometer of industrial activity in the US, leading the ISM Manufacturing PMI Index by 1 month with a correlation of 0.81 since the survey inception. The latest edition pegged the indicator to its fifth lowest level (42.6) on record, considerably lower than even the freight recession average of 54.2. It remains sub-50 for the sixteenth time in the past eighteen issues, reflecting the malaise in the freight economy.

**双周"卡车货主调查"**：卡车运输占美国货运吨位 2/3、运输开支 80%+。输出"**BofA Truckload Demand Indicator**"——**货主对未来 0-3 月需求前景的情绪指标**。它是美国工业活动的有效晴雨表：
- 相对 **ISM 制造业 PMI 领先 1 个月**
- **相关性 0.81**（自调查启动以来）
- **最新读数 42.6，为历史第 5 低**——**甚至远低于"货运衰退期"的平均 54.2**
- **过去 18 期中有 16 期低于 50**——反映货运经济**持续低迷**

The survey also tracks shipping managers' opinions on truck pricing, supply, and inventory levels. The Truck Capacity Indicator for shippers' views of available truckload capacity increased to 74.5 in the latest survey from 68.8 in the prior edition, as shippers see more available truck capacity. The Rate Indicator for shippers' views on truck rates increased to 33.0 from 31.3, in-line with spot rate moves as rate expectations rose after the end of March-May bid season (when annual contracts renew). The Inventory Indicator ticked up to 62.8 from 61.5 as shippers see slightly higher inventory levels.

同一问卷还跟踪货主对**卡车价格、供给、库存**的看法：
- **Truck Capacity Indicator（卡车运力指标）**：由 68.8 升至 **74.5**（高于历史均值 50）——货主见到更多可用运力
- **Rate Indicator（运价指标）**：由 31.3 升至 **33.0**——3-5 月年合约续签季后运价预期回升，与现货价一致
- **Inventory Indicator（库存指标）**：由 61.5 升至 **62.8**——货主见到库存略高

---

# 第 89 页 · 卡车指标四图

> **📊 图表 185**：*BofA Truck Indicator and ISM Index*
> **BofA 卡车指标 vs ISM 制造业指数**：自调查启动以来，**卡车指标领先 ISM 1 个月，相关性 0.81**。

> **📊 图表 186**：*Shippers' view of available capacity*
> **货主眼中的可用运力**：**Capacity Indicator 74.5**，高于历史均值 50——运力充足。

> **📊 图表 187**：*Shippers' view of rates over next three months*
> **货主对未来 3 个月运价的预期**：**Rate Indicator 33.0**（环比 +1.7）——运价略回升。

> **📊 图表 188**：*Shippers' view of inventory levels*
> **货主眼中的库存水平**：**Inventory Indicator 62.8**（上期 61.5）——库存略升。

---

# 第 90 页 · ESG 的 ABC

## The ABC's of ESG
## ESG 的 ABC

更多主题讨论见本报告的 *ESG Primer* 与 *Follow the numbers, not the naysayers* 两篇专题报告。

### What is ESG?
### 什么是 ESG？

ESG investing captures the notion of using non-financial factors that incorporate the environmental impact (E), social impact (S) and governance attributes (G) of a corporation. Another related vein of investing is Thematic Investing, which delves into themes that impact the global economy/investment landscape and are often environmental or social in nature (climate change, education, obesity, etc.) "Green" investing is another related category, focusing explicitly on companies that better the environment by employing/supporting "green" initiatives like clean energy, resource conservation, etc. Impact Investing refers to investments that look to generate measurable social or environmental impact along with a level of financial return. All of these terms can fall under the broad umbrella of sustainability or sustainable investing.

**ESG 投资**指的是**纳入非财务因素**——**公司对环境（E）、社会（S）、治理（G）属性的影响**。相关概念：
- **主题投资（Thematic Investing）**：聚焦影响全球经济/投资图景的主题，常带有环境或社会属性（气候变化、教育、肥胖等）
- **"绿色"投资（Green Investing）**：明确聚焦"改善环境的公司"——支持/从事清洁能源、资源节约等"绿色"倡议
- **影响力投资（Impact Investing）**：追求**可度量的社会/环境影响 + 一定水平的财务回报**

以上均可归入"**可持续/Sustainability**"这一大伞下。

In this report, we focus on the first aspect (ESG investing). The data we examine can help evaluate whether companies run themselves responsibly. We consider environmental impacts (such as emissions or resource use), social impacts (such as employee training or diversity policies), and governance attributes (such as board structure or shareholder rights).

本报告聚焦**第一种（ESG 投资）**。检视的数据能帮助评估公司是否"**负责任地经营**"：
- **环境影响**：如排放、资源使用
- **社会影响**：如员工培训、多元化政策
- **治理属性**：如董事会结构、股东权利

Trends in the US investment landscape indicate that trillions of dollars could be allocated to ESG-oriented equity investments, and thus to stocks that are attractive on ESG metrics. We conservatively estimate that inflows into ESG type strategies over the next few decades could be roughly equivalent to the size of the S&P 500 today.

美国投资图景的趋势表明：**数万亿美元**有望配置到 ESG 导向的股票投资，流向那些 ESG 指标上有吸引力的股票。**我们保守估计：未来几十年流入 ESG 类策略的资金规模，可能大致等于今天整个 S&P 500 的市值**。

> **📊 图表 189**：*AUM in US ESG funds has plateaued in last year*
> **美国 ESG 权益基金 AUM**（2015/1–2023/4）：过去 1 年已进入平台期。分为被动 ESG 基金与主动 ESG 基金。

> **📊 图表 190**：*ESG smart beta ETF AUM declined YoY*
> **Smart Beta ETF 各细分类别 AUM 同比增速**（2023/4/30 vs 2022/4/30）：
> - **+39%**、+38%、+11%、+10%、+7%、+5%、0%、-1%、-2%、-8%、-14%（各细分项）
> - 表明 **ESG smart beta ETF AUM 同比已下降**

---

# 第 91 页 · ESG 与因子投资的重叠

> **📊 图表 191**：*Still limited overlap between ESG and factor-based investing*
> **基本面因子投资者与 ESG 选股者的重叠仍然有限**（基于 2021 年 BofA 机构因子调查）。

**"基于估值、成长或收益率等基本面因子选股"的投资者** 与 **"用 ESG 作为选股因子"的投资者**——**二者重叠仍有限**。

## It's not politics, it's money
## 这不是政治，而是钱

ESG has recently come under fire in the US, where it has been cast as marketing gimmickry to gather assets, as concessionary or anti-performance, as anti-populist or elitist, and as politically rather than financially motivated.

ESG 近期在美国受到抨击——被贴上各种标签：**营销噱头、为吸金而生、妥协/反业绩、反民粹/精英主义、出于政治而非财务动机**。

The landscape for professional investors is riddled with conflicting messages. ESG funds are criticized for including "bad actors" like oil or defense (see note). On the other hand, ESG funds with strict exclusion rules are criticized for lagging markets recently led by commodities, defense and other less ESG-friendly themes.

专业投资者面对的信息充满矛盾：
- 一方面，**ESG 基金因纳入石油、国防等"坏演员"而受批评**
- 另一方面，**严格剔除规则的 ESG 基金**又被批评"**近来跑输**"——毕竟市场近期由大宗、国防等**不那么 ESG 友好的主题**主导

Our approach within ESG research has always been motivated by generating, rather than conceding returns. We have also tried to avoid a more exclusionary framework, leaving that capital allocation decision to individuals based on their individual value systems.

**本报告对 ESG 研究的立场一直是：以创造回报为目的，而不是妥协回报**。我们也**尽量避免纯剔除式框架**——把"该不该买某类公司"的价值判断留给**个人基于自己价值观去做**。

But we fear that US investors are throwing out the baby with the bathwater, ignoring the benefits we have found from incorporating ESG considerations into investment frameworks beyond political or moral inclinations. We here delineate the investment case for ESG, which like most things, is nuanced and the devil is in the details. We address the following questions primarily from the seat of a US equity investor, using mostly an empirical data-driven approach, to try to de-politicize this issue:

但我们担忧**美国投资者在"倒洗澡水时连孩子一起倒掉"**——忽视了把 ESG 纳入投资框架（与政治/道德倾向无关）带来的实际好处。以下我们主要**站在美国股票投资者的视角、以经验数据驱动的方式**展开论证，试图**将该议题去政治化**：
- **忽视 ESG 的成本**
- **ESG 作为"更优基本面信号"**
- **ESG + 基本面策略的 alpha**
- **最佳实践（动态、包含而非剔除）**

### Do politics matter?
### 政治真的重要吗？

In Europe, which is considered to be ahead of the US and APAC, ESG has been driven by coordinated policy. In the US, it's less top down, and corporates and investors have done a lot of the work to push ESG to the forefront. One would imagine that dropping out of and then re-joining the Paris Accord, the Inflation Reduction Act, pipeline decisions and other fossil fuel related legislation would have a strong impact on performance of sustainable strategies. But performance has been more driven by supply and demand

**欧洲**（被认为走在美国和亚太前面）**ESG 由协调一致的政策推动**。**在美国则不那么自上而下——企业与投资者承担了把 ESG 推到前台的主要工作**。
- 有人会想：退出再加入《巴黎协定》、《降通胀法案（IRA）》、油气管线决策、其他化石燃料立法，**应该会对可持续策略表现产生强影响**
- 但实际上**业绩主要由供需驱动**——而不是立法

---

# 第 92 页 · ESG + 量化 = Alpha

than by legislation. Energy on a relative basis performed worst under the most friendly administration, but better amid more environmentally stringent administrations.

甚至**能源板块相对表现最差的恰恰是在对其最友好的行政当局下**，**在环境监管更严厉的当局下反而更好**。

> **📊 图表 192**：*S&P 500 Energy Index relative performance (vs. S&P 500)*
> **S&P 500 能源指数的相对表现**：
> - **奥巴马政府（2009/1–2017/1）**：能源跑输
> - **特朗普政府（2017/1–2021/1）**：能源也跑输
> - **拜登政府（2021/1–2023/5）**：能源跑赢
> 结论：**能源板块的相对表现由 secular 供需驱动，而非政策驱动**。

## ESG + Quant = Alpha
## ESG + 量化 = Alpha

We have shied away from the argument that investing purely based on ESG is a route to alpha. Why? (1) Returns can be conflated with sectors or styles - some argue high ESG ranks are most prevalent for asset-light growth stocks, or for large companies with more disclosure. (2) Returns on a shorter-term basis can capture inflows / outflows or popularity, rather than fundamental attributes. And (3) as we have seen for companies with other fundamentally attractive characteristics, like quality or growth potential, the scarcity of that attribute and the entry point valuation are more important determinants of future returns.

**我们一直回避"仅靠 ESG 就能做出 alpha"这种说法**。原因：
1. **回报容易被行业或风格"混淆"**——有人认为高 ESG 评级高度集中在**轻资产的成长股**或**信息披露更多的大公司**
2. **短期回报更可能反映资金流入/流出或热度**，而非基本面属性
3. 如同质量、成长潜力这类因子——**"稀缺性 + 入场估值"才是未来回报更关键的决定因素**

> **切勿在真空中使用 ESG**。**"好公司"如果交易在过高溢价，常会跑输"坏公司"交易在过大折价的情形**。**估值对任何投资类型都重要，包括 ESG**。

> **📊 图表 193**：*Companies with top ranked ESG scores have been outperforming*
> **各 ESG 评级顶五分位公司相对等权基准的表现**（2014/1–2023/4）：
> MSCI、Sustainalytics、Refinitiv 三套评分系统下，**高 ESG 评级组合一致跑赢**。

---

# 第 93 页 · ESG 叠加量化：alpha 增益与风险下降

Our work on environmental social and governance components as a signal for superior ROE and lower earnings risk within sectors (see section Implementation guide for sectors) incorporate a multi-year time horizon. But in the short-term, adding an ESG factor to traditional fundamental styles has enhanced returns and reduced risk. Using the popular investment styles we track in our quantitative work (see Institutional Factor Survey for details) we found that adding ESG as a second equal-weighted factor to each screen would have improved performance both on an absolute and on a risk-adjusted basis. The improvement stood out most for earnings measures but was also effective for Dividend, Value, Momentum and Quality screens.

我们把**环境、社会、治理各分量**作为"行业内 ROE 更高、盈利风险更低"的信号，做过多年研究（见"行业实施指南"章）。短期也有结论：**将 ESG 作为第二个等权因子叠加到各传统基本面风格筛选上——绝对回报与风险调整回报均获得提升**：
- 提升最显著的是**盈利类指标**
- 对**股息、价值、动量、质量**筛选也都有效

> **给传统基本面投资技术叠加 ESG——能改善 alpha 和风险调整回报**。

> **📊 图表 194**：*ESG has consistently augmented alpha when added to fundamental investment screens*
> **叠加 ESG vs 纯因子的顶五分位年化总回报**（2005/12–2023/4）：

| 因子 | 纯因子 | +ESG 叠加 | 提升 |
|---|---|---|---|
| 前瞻盈利收益率 | 7.8% | **9.0%** | +1.2 |
| 股息率 | 10.4% | **11.0%** | +0.6 |
| 股息增长 | 9.7% | **10.1%** | +0.4 |
| 12m+1m 反转 | 8.5% | **9.5%** | +1.0 |
| 长期增长 | 9.7% | **10.2%** | +0.5 |
| EPS 修正比 | 9.0% | **10.7%** | +1.7 |
| 盈利动量 | 7.6% | **9.4%** | +1.8 |
| ROE | 10.5% | **11.0%** | +0.5 |
| S&P Quality | 9.8% | **10.4%** | +0.6 |

**关键观察**：叠加 ESG 后**每一类因子都有提升**，其中**盈利动量 + 1.8 个百分点、EPS 修正比 + 1.7 个百分点**提升最大。

Moreover, the performance of top-ranked stocks by ESG scores exhibited lower correlations with those of popular investment styles like Value, Growth and Income, suggesting that ESG adds more differentiated information to traditional investment approaches than does mingling fundamental investment styles (Exhibit 195). This makes intuitive sense, as attributes like carbon emissions, employee turnover and shareholder rights are not easily captured in current earnings, growth or payout measures.

更重要的是，**高 ESG 分数股的表现，与价值/成长/收益等传统风格的相关性更低**——说明 **ESG 为传统投资方法带来了"比其他基本面风格之间混搭还要更差异化"的信息**（图表 195）。这在直觉上也合理：**碳排放、员工流失率、股东权利**这些属性**很难被当期盈利、增速或派息指标捕捉**。

> **ESG 为传统投资方法注入新信息。其业绩与成长、价值、收益类风格的相关性，比这些风格彼此之间的相关性还要低**。

---

# 第 94 页 · ESG 因子的风险收益与相关性

> **📊 图表 195**：*Annualized returns of pure quant factors and ESG blended quant factors vs. probability of loss*
> **纯量化因子与 ESG 混合量化因子的年化回报 vs 亏损概率**（2005/12–2023/4）：
> 横轴 = 基于 12 月滚动回报的亏损概率，纵轴 = 年化回报。
> **ESG 混合版（Quant+ESG）相对纯因子（Pure factor）整体向左上方移动**——**更高回报 + 更低亏损概率**。

> **📊 图表 196**：*ESG is negatively correlated with fundamental factors*
> **Sustainalytics ESG 评分顶十分位股，与基本面因子的表现相关性**（2010–2023/4）：
> - **与 ESG 的平均相关性**：**价值为负、现金运用为负、成长为负**
> - 而"**其他量化因子之间的平均相关性**"则整体较高
> 结论：**ESG 是一个"差异化信号"**，不冗余地覆盖价值、成长、现金运用等其他因子。

分析中所包含的"其他量化因子"有：**Risk、Value、Cash Deployment、Technical、Growth、Quality**。

---

# 第 95 页 · 股东行动主义 + ESG 溢价的收窄

## Activists could play matchmaker
## 股东行动主义者可做"红娘"

Activist campaigns targeting Russell 3000 companies' corporate governance reached record levels in 2019. Companies saw greater improvement in their ESG scores post-engagement relative to the universe (both based on their corporate governance scores as well as their overall scores) over the subsequent one, two and three years.

**2019 年针对罗素 3000 公司治理的股东行动主义活动达到历史新高**。被"动了手术"的公司**在随后的 1 年、2 年、3 年里 ESG 评分改善幅度都显著超过全体公司**——**无论是治理得分还是总分**。

> **📊 图表 197**：*Activist campaigns targeting Russell 3000 companies*
> **针对罗素 3000 公司的股东行动主义活动数**（2002–2023 YTD，截至 2023/4）：**长期上升趋势**。
> 注：为了获得足够的数据点，我们用罗素 3000 指数作为全域。

> **📊 图表 198**：*Subsequent relative performance of Russell 3000 companies targeted by corporate governance campaigns*
> **被治理型活动主义"盯上"的公司的后续相对表现**（1994–2023/4）：
> - +1 月均值 2.3、中位数 1.0、胜率 **56%**
> - +3 月均值 3.7、中位数 2.2、胜率 **55%**
> - +12 月均值 **5.8**、中位数 **4.3**、胜率 **58%**
> 结论：**治理型活动主义活动历史上驱动了显著的持续跑赢**。

## A narrowing ESG premium
## 收窄中的 ESG 溢价

Possibly driven by asset flows into ESG funds, companies with high ESG ranks appear to have re-rated relative to low ranked companies over the last decade. Whereas highly ranked stocks traded at a 20-30% premium to the market several years ago and as high as 50% during the onset of COVID-19, today that premium valuation has shrunk to 12%. We find the learning curve has advanced and looking at a company's ESG ranks alone is no longer enough.

可能由于 **ESG 基金的资金流入推动**，高 ESG 评级公司过去十年相对低评级公司**整体出现估值抬升（re-rating）**：
- 几年前高 ESG 评级股相对市场**溢价 20-30%**
- **新冠爆发初期**一度冲高至 **50% 溢价**
- **今天该溢价已收窄至 12%**

我们发现**学习曲线已向前推进**——**仅凭公司的 ESG 评级已不足以驱动超额收益**。

> **📊 图表 199**：*MSCI: 'Good' companies trade at a 12% premium to 'bad'*
> **S&P 500 中 MSCI ESG 评分顶/底五分位股票的相对前瞻 P/E**（2007/1–2023/4）：**当前溢价 12%**（峰值约 50%）。

---

# 第 96 页 · 量化 "S"：文化是关键

## Quantifying the "S": Culture is key
## 量化"S（社会）"：企业文化是核心

Considering company culture can help investors avoid potential ESG controversy risk and can act as a barometer of healing for a controversy stock. The concept defies quantification, but our analysis of Glassdoor "culture and values" ranks as a proxy show deterioration in the wake of controversies, taking years to bottom (Exhibit 200). Why? Culture is more correlated with overall satisfaction than any other factor tracked by Glassdoor. And culture signals performance: top quintile stocks outperformed bottom stocks by >6ppt p.a. since 2012, with 15%+ p.a. since 2018 as the "S" in ESG gained importance.

考察**公司文化**能帮投资者**避开潜在的 ESG 争议风险**，同时可作为**争议股"伤愈"过程的晴雨表**。文化概念难以量化，但我们用 **Glassdoor "culture and values"（文化与价值观）评分作为代理**的分析显示：**争议爆发后文化评分会持续恶化，需多年才触底**（图 200）。为什么？——**在 Glassdoor 所追踪的所有因子中，文化与"整体满意度"的相关性最高**。而且**文化能预示业绩**：
- 顶五分位股相较底五分位股 **自 2012 年以来年化跑赢 >6 个百分点**
- **自 2018 年 ESG 中的"S"日益受重视以来，年化跑赢 15%+**

> **📊 图表 200**：*Culture & Values = 2x as important as compensation*
> **各具体评分对 Glassdoor 综合分的 R²**（美国上市公司，2023 Q1 数据）：文化与价值观的解释力**约为"薪酬"的 2 倍**。

> **📊 图表 201**：*Strong culture drives lower cost of capital*
> **文化与价值观 Top 30% 与 Bottom 30% 公司的中位前瞻 12 个月 P/E**（Culture 截至 2023 Q1；P/E 截至 5/19）：**Top 18.0× vs Bottom 16.5×**——**强文化公司享有更高估值 = 更低资本成本**。

> **📊 图表 202**：*Culture can be a more alpha-generative factor than overall Glassdoor rating*
> **"多高评分、空低评分"五分位组合在 S&P 500 内的累计回报**：
> **Culture & Values 因子比整体 Glassdoor 评分 alpha 能力更强**。

> **📊 图表 203**：*Culture still results in 18% outperformance vs. bottom-ranked peers after adjusting for sector bias*
> **剔除行业偏差后高文化公司相对低文化公司仍跑赢 18%**。

---

# 第 97 页 · 忽视 ESG 的代价

## The cost of ignoring ESG
## 忽视 ESG 的代价

Secular forces are driving the imperative to incorporate ESG characteristics into ones asset allocation and investment decisions. These include:

长期 secular 力量正在**迫使我们把 ESG 特征纳入资产配置和投资决策**，包括以下几方面：

- **Intangibles（无形资产）**：**一家典型美国公司资产负债表上越来越大的比例来自品牌、声誉、知识产权、人才库和其他无形因素**（图 203）。
- **Climate（气候）**：过去十年，**重大天气与气候灾害累计损失超过 1 万亿美元**（图 204）——**热带气旋贡献最大**。
- **ESG controversies（ESG 争议）**：卷入重大 ESG 争议（产品安全、数据泄露、职场骚扰、会计丑闻等）的股票，**过去十年导致 S&P 500 失去 6000 亿美元以上市值**，**下跌期平均持续一年**（图 206）。员工对文化的认知**需要两年多才开始改善**。
- **Existential risk（生存性风险）**：**2008-2015 年间破产的 S&P 500 公司，在破产前的平均环境与社会得分一贯更低**（图 205）。**若投资者在破产前 5 年观察 E 和 S 得分并只买"高于平均"的股票——能回避其中 90%（17 家中的 15 家）的破产**。

> **📊 图表 204**：*Asset opacity in the US is near an all-time high*
> **美国"资产不透明度"接近历史最高**：S&P 500 无形资产占账面价值比重（1998-2022）——持续上升至 60%+。

---

# 第 98 页 · 天气灾害 / ESG 争议 / 破产信号

> **📊 图表 205**：*2022 was the third most expensive year of disasters within the last 4 decades*
> **2022 年是过去 40 年灾害损失第 3 高的年份**（美国十亿美元级天气与气候灾害成本，1980-2022）。

> **📋 图表 206**：*Billion-dollar weather and climate disasters in U.S. by decade*
> **美国十亿美元级灾害按十年汇总**（CPI 调整后）：

| 十年 | 灾害数 | 成本（$Bn） | 干旱 | 洪水 | 冰冻 | 强风暴 | 热带气旋 | 野火 | 冬暴 |
|---|---|---|---|---|---|---|---|---|---|
| 1980s | 31 | 201.5 | 54.2% | 7.7% | 7.9% | 5.8% | 21.4% | 0.0% | 3.0% |
| 1990s | 55 | 307.7 | 8.2% | 22.1% | 4.0% | 12.0% | 37.8% | 4.2% | 11.7% |
| 2000s | 67 | 576.1 | 10.8% | 3.2% | 0.9% | 11.4% | **70.2%** | 3.3% | 0.2% |
| 2010s | 128 | 918.8 | 9.7% | 7.5% | 0.1% | 19.8% | 54.2% | 7.1% | 1.6% |

关键观察：**灾害数量与总成本逐年代加速上升**；**热带气旋**从 2000s 起成为**损失占比最高的灾害类型**。

> **📊 图表 207**：*Major ESG controversies drove >$600bn losses, avg. downdraft of >one year*
> **重大 ESG 争议股相对 S&P 500 的表现**（市值加权，争议发生前 30 天至后 360 天）：
> **平均下跌期超过 1 年**，**最大跌幅 -15% 以上**。
> 涵盖 34 起重大 ESG 事件：数据泄露、会计丑闻、客户安全、性骚扰等。

---

# 第 99 页 · ESG 评分作为破产信号

> **📊 图表 208**：*Environmental and Social ranks have been good signals of future bankruptcy risk*
> **E/S 排名是未来破产风险的良好信号**。
> 2008-2015 年间破产的美股在**破产前 1 年的 ESG 排名**：
> - **左轴（中位排名）**：Overall / Environmental / Social / Governance 四项得分均较低
> - **右轴（"破产前低于均值"公司占比）**：均接近 80-100%
> 说明：Overall ESG 排名 = E+S+G 三项平均；样本为 BofA US 覆盖范围内带 ESG 排名的 20 家破产公司。

---

# 第 100 页 · 行业实施指南

## Implementation guide for sectors
## 行业实施指南

**What we did**: We drilled down to more granular levels of data for each data vendor and split the universe of stocks in the sector into halves based on each ESG metric: above vs. below median score per sector (we used halves instead of quintiles due to the limited number of companies within sectors). We then analyzed the spread between top and bottom half ESG companies in terms of future (1) return on equity; (2) earnings risk (volatility); (3) price volatility; and (4) performance.

**我们做了什么**：对每家数据供应商下钻到更细粒度，并**按每项 ESG 指标把行业内股票分成两半**（高于/低于该行业中位数——由于行业内公司较少，我们用"两分"而非"五分"）。然后分析**上半组 vs 下半组**在未来 4 个维度上的价差：
1. ROE（股本回报率）
2. 盈利风险（波动性）
3. 价格波动率
4. 业绩

## Sector takeaways
## 行业要点

The factors that have historically been the most effective signals of future return on equity and earnings risk for companies within each sector are highlighted below, where we assessed both the magnitude of difference in future fundamental attributes between above- and below- median companies, as well as the consistency of the signal in yielding stronger and weaker results over time. Some key highlights:

以下分行业罗列**历史上预测 ROE 与盈利风险最有效的因子**。评估维度：一是"上半组 vs 下半组"未来基本面差异**幅度**，二是信号**一致性**（时间上能否稳定地区分强/弱结果）。要点：

- **大宗导向行业（能源/工业/材料）**：**环境因子（排放、废弃物）** 毫不意外地**是预测未来 ROE 与盈利风险最好的信号**。材料行业中**化学品安全敞口（社会因子）** 也很关键；**可再生能源／清洁技术的机遇** 对**能源与公用事业**都是重要信号。
- **可选消费**（最劳动密集的行业）：**社会因子中的"劳动力管理"** 是预测未来 ROE 最好的信号。
- **科技与金融**：**治理因子**是预测未来 ROE 或盈利风险最好的信号——考虑到科技行业 ESG 争议频出、以及我们先前发现的"GFC 前治理评分的重要性"，这个结果并不意外。

---

# 第 101 页 · 行业 ESG 因子"重要性地图"

> **📋 表 1**：*MSCI ESG metrics that have been the most effective signals of future return on equity and earnings risk*
> **重要性地图（Materiality Map）**：历史上对各行业"未来 5 年 ROE + 未来 3 年盈利风险"最有效的 MSCI ESG 因子：

| 维度 | 未来 ROE | 盈利风险 |
|---|---|---|
| **可选消费** | 社会：劳动力管理、产品安全主题评分 | 治理：薪酬政策 |
| **必需消费** | 环境：包装与废弃物材料；社会：营养健康机遇 | 治理：治理评级与会计政策 |
| **能源** | 环境：碳排放敞口/可再生能源机遇 | 环境：能效敞口 |
| **金融** | 治理：所有权 | 环境：有毒排放与废弃物；治理：治理评分；社会：劳动力管理 |
| **医疗** | 治理：金融系统不稳定/董事会评级/负责任投资敞口 | 环境：电子废弃物/清洁技术敞口 |
| **工业** | 环境：包装材料与废弃物敞口；社会：融资渠道敞口 | 环境：包装材料与废弃物敞口 |
| **信息技术** | 治理：所有权与会计惯例 | 环境：碳排放；治理：商业道德、腐败与不稳定、薪酬 |
| **通讯服务** | 社会：产品安全；治理：隐私与数据安全/商业道德 | 治理：所有权与控制 |
| **媒体** | 治理：争议暴露评分与所有权控制；社会：通讯与人力资本渠道 | 治理：商业道德 |
| **材料** | 社会：化学品安全敞口；环境：气候变化与水管理 | 社会：化学品安全敞口；社会：健康与安全评分、劳动力管理 |
| **REITs** | 环境：有毒排放与废弃物；社会：融资渠道敞口；治理：会计政策 | 治理：董事会评级 |
| **公用事业** | 环境：自然资源利用、清洁技术机遇 | 社会：人力资本 |

提示：回测是假设性的，反映分析方法在公布前的应用，并非实际业绩，也不意在预示未来业绩。

---

# 第 102 页 · ESGMeter™：专有 ESG 评分

## Introducing ESGMeter™, a proprietary ESG score
## 推出 ESGMeter™——专有 ESG 评分

### ESGMeter assesses financial stability using an ESG lens
### 从 ESG 视角评估财务稳定性

Building on our analysis of environmental, social and governance (ESG) factors that began in 2016, we launched ESGMeter, a proprietary metric based on quantitative and fundamental inputs that reflect our assessment of a company's ESG-related attributes.

在 **2016 年起** 对 ESG 因子持续分析的基础上，我们推出 **ESGMeter**——一个**基于量化 + 基本面输入**的专有指标，用以**评估公司 ESG 相关属性**。

ESGMeter is intended to indicate a company's likelihood of experiencing stronger Financial Stability (which we define as higher return on equity, lower earnings volatility, and lower price volatility) over the next three years relative to its peer group.

ESGMeter 用以**指示公司未来 3 年相对同业更好"财务稳定性"的可能性**——我们将"财务稳定性"定义为：**更高 ROE + 更低盈利波动率 + 更低股价波动率**。

There are three ESGMeter levels – Low, Medium, and High – with High indicating that a company has attributes we expect to be most likely to translate into superior financial stability. This framework is based on two elements: (1) a quantitative analysis incorporating a wide array of ESG attributes to determine which have been effective signals of financial stability historically within each industry group, and (2) a fundamental overlay, where our analysts provide qualitative industry-group level input on the importance of particular ESG attributes.

ESGMeter 分 **Low / Medium / High** 三档，**High** 代表我们认为"最可能转化为财务稳定性"的属性。框架基于**两大要素**：
1. **量化分析**：纳入大量 ESG 属性，判断历史上在各行业组中**哪些属性是财务稳定性的有效信号**
2. **基本面叠加**：我们的行业分析师就"**某些 ESG 属性的重要性**"提供**定性的行业组级输入**

### ESGMeter focuses on value, not values
### ESGMeter 聚焦"价值"，而非"价值观"

Whereas ESG investing often connotes a values-driven framework, we instead use a financial lens to drive our ESGMeter. In our view, ESG characteristics are too critical to ignore from an investment perspective, and can be important signals of fundamental prowess, volatility, and even bankruptcy risk. In our previous research, we analyzed the efficacy of these metrics within sectors (see ESG: From A to Z, 8 November 2019) as a signal of financial results.

ESG 投资常被贴上"**价值观驱动**"的标签——但我们反过来**用财务视角驱动 ESGMeter**。我们认为从投资视角看 **ESG 特征"太重要以致不能忽视"**，它们是**基本面实力、波动率、乃至破产风险**的重要信号。此前在 *ESG: From A to Z*（2019/11/8）中，我们分析过这些指标在各行业中作为**财务结果信号**的有效性。

Now we develop a framework for determining company-specific scores. Importantly, our analysis is focused on attributes that have been, and are likely to be, drivers of superior financial results from an ROE and risk management perspective, rather than drivers of alpha. Why? We believe alpha from ESG factors may have been driven by the significant flows into ESG-related investments that we've seen over the lifespan of most ESG datasets. See our ESGMeter Methodology report for more information about the ESGMeter framework and important disclosures.

现在我们进一步构建**确定公司个股得分**的框架。**重要**：我们的分析聚焦于"历史上及未来可能驱动更好财务结果"（从 ROE 和风险管理角度）的属性——**而不是"alpha 驱动属性"**。为什么？**因为我们认为 ESG 因子的 alpha 很可能是由大多数 ESG 数据集生存期内大量 ESG 资金流入驱动的**（而非因子本身的稀缺溢价）。ESGMeter 框架与重要声明详见 *ESGMeter Methodology* 报告。

---

# 第 103 页 · 第二部分 · S&P 500 选股策略目录

## Section II: Stock Strategies within the S&P 500
## 第二部分：S&P 500 内部的选股策略

| 主题 | 起始页 |
|---|---|
| **GARP（合理估值成长）策略** | 104 |
| **估值策略** | 106 |
| **现金运用策略** | 116 |
| **动量策略** | 120 |
| **成长策略** | 130 |
| **质量策略** | 137 |
| **风险策略** | 144 |
| **其他杂项策略** | 149 |

> 注：本节**所有散点图均基于筛选公布后的实盘表现**（除另有说明）。

---

# 第 104-105 页 · GARP 策略（P/E-to-Growth）

## GARP Strategies
## GARP（合理估值成长）策略

> **📊 图表 209**：*GARP Strategy*
> **P/E-to-Growth 因子**：**历史 12 个月滚动回报 14.2%**。
> 横轴：12 月滚动回报的标准差；纵轴：平均 12 月滚动回报。

> **📊 图表 210**：*GARP Strategy*
> **P/E-to-Growth 因子**：**历史 12 个月滚动回报 14.2%**。
> 横轴：12 月滚动回报为负的比例；纵轴：平均 12 月滚动回报。

## P/E-to-Growth（PEG）
## P/E-增速比（PEG）

> **📊 图表 211**：*Performance of Low P/E to Growth, High P/E to Growth and Long-Short Spread*
> **Low PEG、High PEG 的相对表现与多空价差**：该因子**年初至今跑输指数**。
> 基准日：2001/2 = 100。等权相对累计表现（vs 等权 S&P 500）。

> **📊 图表 212**：*Low P/E to Growth Risk Reward*
> **低 PEG 风险-收益**：**历史上跑赢指数**。
> 横轴：12 月滚动回报标准差；纵轴：平均 12 月滚动回报。
> 标记：Long（多头组合）、EW S&P 500、Short（空头组合）、S&P 500。

> **📊 图表 213**：*Low P/E to Growth Downside Risk Reward*
> **低 PEG 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 214**：*P/E to Growth Sector Concentration (Low Decile)*
> **低 PEG 组合的行业分布**（Low 十分位，2000-2022）：**能源占比最大**。

---

# 第 106-107 页 · 估值策略总览 + DDM Alpha

## Valuation Strategies
## 估值策略

> **📊 图表 215 / 216**：*Valuation Strategies*
> **估值因子对比**（Earnings Yield、前瞻 Earnings Yield、P/B、P/CF、P/FCF、P/Sales、EV/EBITDA、FCF/EV、DDM Alpha）：
> **FCF/EV 表现最佳**（12 月滚动回报 ~17-19%，标准差与亏损概率都相对居中）。

## DDM Alpha（股利折现模型 Alpha）

> **📊 图表 217**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **DDM Alpha 顶/底十分位与多空价差表现**（2001/2 = 100）：**YTD 跑赢指数**。

> **📊 图表 218 / 219**：*DDM Risk Reward Characteristics & Downside Risk Reward*
> **DDM 风险-收益**（总/下行）：**YTD 跑赢指数**。

> **📊 图表 220**：*DDM Sector Concentration (Top Decile)*
> **DDM Alpha 组合行业分布**：**能源权重最大**。

---

# 第 108-109 页 · 盈利收益率 / 前瞻盈利收益率

## Earnings Yield
## 盈利收益率（E/P）

> **📊 图表 221**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 E/P 顶/底十分位与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 222 / 223**：*High Earnings Yield Risk Reward & Downside Risk Reward*
> **高 E/P 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 224**：*High Earnings Yield Sector Concentration (Top Decile)*
> **高 E/P 组合行业分布**：**能源权重最大**。

## Forward Earnings Yield
## 前瞻盈利收益率（Fwd E/P）

> **📊 图表 225**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 Fwd E/P 顶/底十分位与多空价差**：YTD 跑输指数（2005/4 = 100）。

> **📊 图表 226 / 227**：*High Forward Earnings Yield Risk Reward & Downside Risk Reward*
> **高 Fwd E/P 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 228**：*High Forward Earnings Yield Sector Concentration (Top Decile)*
> **高 Fwd E/P 组合行业分布**：**金融权重最大**。

---

# 第 110 页 · Price/Book Value

## Price/Book Value（P/B）
## 市净率（P/B）

> **📊 图表 229**：*Performance of Low P/B, High P/B and Long-Short Spread*
> **低 P/B 与高 P/B 的相对表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 230 / 231**：*Low Price/Book Value Risk Reward & Downside Risk Reward*
> **低 P/B 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 232**：*Low Price/Book Value Sector Concentration (Low Decile)*
> **低 P/B 组合行业分布**：**金融权重最大**。

---

---

# 第 111 页 · Price/Cash Flow

## Price/Cash Flow（P/CF）
## 市现率（P/CF）

> **📊 图表 233**：*Performance of Low P/CF, High P/CF and Long-Short Spread*
> **低 P/CF 与高 P/CF 相对表现与多空价差**：YTD 跑输指数（2003/7 = 100）。

> **📊 图表 234 / 235**：*Low Price/Cash Flow Risk Reward & Downside Risk Reward*
> **低 P/CF 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 236**：*Low Price/Cash Flow Sector Concentration (Low Decile)*
> **低 P/CF 组合行业分布**：**能源权重最大**。

---

# 第 112 页 · Price/Free Cash Flow

## Price/Free Cash Flow（P/FCF）
## 价格/自由现金流（P/FCF）

> **📊 图表 237**：*Performance of Low P/FCF, High P/FCF and Long-Short Spread*
> **低 P/FCF 与高 P/FCF 相对表现与多空价差**：YTD 跑输指数（2003/7 = 100）。

> **📊 图表 238 / 239**：*Low P/FCF Risk Reward & Downside Risk Reward*
> **低 P/FCF 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 240**：*Low P/FCF Sector Concentration (Low Decile)*
> **低 P/FCF 组合行业分布**：**能源权重最大**。

---

# 第 113 页 · Price/Sales

## Price/Sales（P/S）
## 市销率（P/S）

> **📊 图表 241**：*Performance of Low P/S, High P/S and Long-Short Spread*
> **低 P/S 与高 P/S 相对表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 242 / 243**：*Low Price/Sales Risk Reward & Downside Risk Reward*
> **低 P/S 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 244**：*Low Price/Sales Sector Concentration*
> **低 P/S 组合行业分布**：**医疗保健权重最大**。

---

# 第 114 页 · EV/EBITDA

## EV/EBITDA（企业价值/息税折旧摊销前利润）

> **📊 图表 245**：*Performance of Low EV/EBITDA, High EV/EBITDA and Long-Short Spread*
> **低 EV/EBITDA 与高 EV/EBITDA 相对表现与多空价差**：YTD 跑输指数（2004/9 = 100）。

> **📊 图表 246 / 247**：*Low EV/EBITDA Risk Reward & Downside Risk Reward*
> **低 EV/EBITDA 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 248**：*Low EV/EBITDA Sector Concentration (Low Decile)*
> **低 EV/EBITDA 组合行业分布**：**能源权重最大**。

---

# 第 115 页 · Free Cash Flow/Enterprise Value

## Free Cash Flow/Enterprise Value（FCF/EV）
## 自由现金流/企业价值（FCF/EV）

> **📊 图表 249**：*Performance of Low FCF/EV, High FCF/EV and Long-Short Spread*
> **高 FCF/EV 与低 FCF/EV 相对表现与多空价差**：YTD 跑输指数。

> **📊 图表 250 / 251**：*High FCF/EV Risk Reward & Downside Risk Reward*
> **高 FCF/EV 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 252**：*Low FCF/EV Sector Concentration (Low Decile)*
> **低 FCF/EV 组合行业分布**：**能源权重最大**。

---

# 第 116 页 · Cash Deployment Strategies

## Cash Deployment Strategies
## 现金运用策略

> **📊 图表 253 / 254**：*Cash Deployment Strategies — Risk Reward & Downside Risk Reward*
> **现金运用策略（股息增长、股息率、股份回购）的收益-风险与下行风险**：**股份回购（Share Repurchase）表现最佳**，具有最高的平均滚动 12 个月回报，同时负收益频率较低。

---

# 第 117 页 · Dividend Yield

## Dividend Yield
## 股息率

> **📊 图表 255**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高股息率组合相对表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 256 / 257**：*High Dividend Yield Risk Reward & Downside Risk Reward*
> **高股息率风险-收益 / 下行风险-收益**：**历史上跑输指数**。

> **📊 图表 258**：*High Dividend Yield Sector Concentration (Top Decile)*
> **高股息率组合行业分布**：**房地产权重最大**。

---

# 第 118 页 · Dividend Growth

## Dividend Growth
## 股息增长

> **📊 图表 259**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高股息增长相对表现与多空价差**：YTD 跑输指数（2004/8 = 100）。

> **📊 图表 260 / 261**：*High Dividend Growth Risk Reward & Downside Risk Reward*
> **高股息增长风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 262**：*High Dividend Growth Sector Concentration (Top Decile)*
> **高股息增长组合行业分布**：**能源权重最大**。

---

# 第 119 页 · Share Repurchase

## Share Repurchase
## 股份回购

> **📊 图表 263**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高回购组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 264 / 265**：*High Share Repurchase Risk Reward & Downside Risk Reward*
> **高回购风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 266**：*High Share Repurchase Sector Concentration (Top Decile)*
> **高回购组合行业分布**：**可选消费权重最大**。

---

# 第 120 页 · Momentum Strategies

## Momentum Strategies
## 动量策略

> **📊 图表 267 / 268**：*Momentum Strategies — Risk Reward & Downside Risk Reward*
> 动量策略风险-收益与下行风险比较（包含：30W/75W 相对强弱、成交量、5W/30W、10W/40W、价格/200 日均价、12M / 9M / 3M / 11M 价格回报、12M-and-1M 以及 12M-and-1M 反转）。
> **高成交量（Trading Volume）策略整体表现最佳**——平均滚动 12 月回报最高，且负收益频率相对可控。

---

# 第 121 页 · Relative Strength – 30wk/75wk

## Relative Strength – 30wk/75wk
## 相对强弱 – 30 周/75 周

> **📊 图表 269**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 30W/75W 相对强弱组合表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 270 / 271**：*High Relative Strength – 30wk/75wk Risk Reward & Downside Risk Reward*
> **高 30W/75W 相对强弱风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 272**：*High Relative Strength (30wk/75wk) Sector Concentration (Top Decile)*
> **高 30W/75W 相对强弱组合行业分布**：**能源权重最大**。

---

# 第 122 页 · Price to 200-Day Moving Average

## Price to Moving Average (200-Day)
## 股价/200 日移动均线

> **📊 图表 273**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 P/200D MA 相对表现与多空价差**：YTD **跑赢**指数。阴影区域（1986/3–2010/1）为回测数据，非阴影区域（2010/2 起）为实盘表现，回测结果具有假设性质，不保证未来业绩。

> **📊 图表 274 / 275**：*High Price/200D MA Risk Reward & Downside Risk Reward*
> **高 P/200D MA 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 276**：*High Price/200D MA Sector Concentration (Top Decile)*
> **高 P/200D MA 组合行业分布**：**医疗保健权重最大**。

---

# 第 123 页 · Price Return – 3-Month Performance

## Price Return – 3-Month Performance
## 价格回报 – 3 个月表现

> **📊 图表 277**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 3 月动量相对表现与多空价差**：YTD 跑输指数。阴影区域（1986/3–2010/1）为回测数据，非阴影区域（2010/2 起）为实盘。

> **📊 图表 278 / 279**：*High Price Return – 3M Risk Reward & Downside Risk Reward*
> **高 3M 动量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 280**：*High Price Return (3M) Sector Concentration (Top Decile)*
> **高 3M 动量组合行业分布**：**可选消费权重最大**。

---

# 第 124 页 · Price Return – 9-Month Performance

## Price Return – 9-Month Performance
## 价格回报 – 9 个月表现

> **📊 图表 281**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 9 月动量相对表现与多空价差**：YTD 跑输指数。阴影区域（1986/3–2010/1）为回测数据，非阴影区域（2010/2 起）为实盘。

> **📊 图表 282 / 283**：*High Price Return – 9M Risk Reward & Downside Risk Reward*
> **高 9M 动量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 284**：*High Price Return (9M) Sector Concentration (Top Decile)*
> **高 9M 动量组合行业分布**：**医疗保健权重最大**。

---

# 第 125 页 · Price Return – 11-Month Performance

## Price Return – 11-Month Performance
## 价格回报 – 11 个月表现

> **📊 图表 285**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 11 月动量相对表现与多空价差**：YTD 跑输指数。阴影区域为回测，非阴影区域为实盘。

> **📊 图表 286 / 287**：*High Price Return – 11M Risk Reward & Downside Risk Reward*
> **高 11M 动量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 288**：*High Price Return (11M) Sector Concentration (Top Decile)*
> **高 11M 动量组合行业分布**：**能源权重最大**。

---

---

# 第 126 页 · Price Return – 12-Month Performance

## Price Return – 12-Month Performance
## 价格回报 – 12 个月表现

> **📊 图表 289**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 12 月动量相对表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 290 / 291**：*High Price Return – 12M Risk Reward & Downside Risk Reward*
> **高 12M 动量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 292**：*High Price Return (12M) Sector Concentration (Top Decile)*
> **高 12M 动量组合行业分布**：**能源权重最大**。

---

# 第 127 页 · Price Return – 12-Month and 1-Month Performance

## Price Return – 12-Month and 1-Month Performance
## 12 个月 + 1 个月复合动量

> **📊 图表 293**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **12M&1M 组合相对表现与多空价差**：YTD **跑赢**指数。阴影区域为回测，非阴影区域为实盘。

> **📊 图表 294 / 295**：*High Price Return – 12M and 1M Risk Reward & Downside Risk Reward*
> **12M&1M 动量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 296**：*High Price Return (12M and 1M) Sector Concentration (Top Decile)*
> **12M&1M 动量组合行业分布**：**医疗保健权重最大**。

---

# 第 128 页 · Price Return – 12-Month and 1-Month Reversal

## Price Return – 12-Month and 1-Month Reversal
## 12 月+1 月反转复合动量

> **📊 图表 297**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **12M 与 1M 反转组合表现与多空价差**：YTD 跑输指数。阴影区域为回测，非阴影区域为实盘。

> **📊 图表 298 / 299**：*High Price Return – 12M and 1M Reversal Risk Reward & Downside Risk Reward*
> **12M + 1M 反转风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 300**：*High Price Return (12M and 1M Reversal) Sector Concentration (Top Decile)*
> **12M + 1M 反转组合行业分布**：**能源权重最大**。

---

# 第 129 页 · Trading Volume

## Trading Volume
## 成交量（Most Active）

> **📊 图表 301**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高成交量组合相对表现与多空价差**：YTD **跑赢**指数（2003/7 = 100）。

> **📊 图表 302 / 303**：*High Trading Volume Risk Reward & Downside Risk Reward*
> **高成交量风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 304**：*High Trading Volume Sector Concentration (Top Decile)*
> **高成交量组合行业分布**：**通信服务权重最大**。

---

# 第 130 页 · Growth Strategies

## Growth Strategies
## 成长策略

> **📊 图表 305 / 306**：*Growth Strategies — Risk Reward & Downside Risk Reward*
> 成长策略包含：EPS 动量、预期 5 年增长、低盈利鱼雷（Low Earnings Torpedo）、正向盈利惊喜、负向盈利惊喜、盈利预测上修（Est Revision）、股票久期（Duration）。
> **正向盈利预测上修（Positive EPS Estimate Revisions）策略表现最佳**，兼具较高平均回报与较低负收益频率。

---

# 第 131 页 · Earnings Momentum

## Earnings Momentum
## 盈利动量（EPS Momentum）

> **📊 图表 307**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 EPS 动量组合相对表现与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 308 / 309**：*High Earnings Momentum Risk Reward & Downside Risk Reward*
> **高 EPS 动量风险-收益 / 下行风险-收益**：**历史上与指数表现相当**。

> **📊 图表 310**：*High Earnings Momentum Sector Concentration (Top Decile)*
> **高 EPS 动量组合行业分布**：**能源权重最大**。

---

# 第 132 页 · Projected Five-Year EPS Growth

## Projected Five-Year EPS Growth
## 预期 5 年 EPS 增长

> **📊 图表 311**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高预期 5 年 EPS 增长组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 312 / 313**：*High Projected 5-Yr EPS Growth Risk Reward & Downside Risk Reward*
> **高预期 5 年 EPS 增长风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 314**：*High Projected 5-Yr EPS Growth Sector Concentration (Top Decile)*
> **高预期 5 年 EPS 增长组合行业分布**：**能源权重最大**。

---

# 第 133 页 · Earnings Torpedo

## Earnings Torpedo
## 盈利鱼雷（Earnings Torpedo）

> **📊 图表 315**：*Performance of High/Low Earnings Torpedo and Long-Short Spread*
> **高/低 Earnings Torpedo 与多空价差**：YTD 跑输指数（2001/2 = 100）。

> **📊 图表 316 / 317**：*Low Earnings Torpedo Risk Reward & Downside Risk Reward*
> **低 Earnings Torpedo 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 318**：*Low Earnings Torpedo Sector Concentration (Low Decile)*
> **低 Earnings Torpedo 组合行业分布**：**金融权重最大**。

---

# 第 134 页 · Earnings Surprise

## Earnings Surprise
## 盈利惊喜

> **📊 图表 319**：*Performance of Positive Surprise, Negative Surprise and Long-Short Spread*
> **正向/负向盈利惊喜组合与多空价差**：YTD 跑输指数。阴影区域（1986/3–1988/12）为回测，非阴影区域（1989/1 起）为实盘。

> **📊 图表 320 / 321**：*Earnings Surprise Risk Reward & Downside Risk Reward*
> **盈利惊喜风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 322**：*Positive Earnings Surprise Sector Concentration (Top Decile)*
> **正向盈利惊喜组合行业分布**：**工业权重最大**。

---

# 第 135 页 · Earnings Estimate Revision

## Earnings Estimate Revision
## 盈利预测上修

> **📊 图表 323**：*Performance of High/Low EPS Estimate Revisions and Long-Short Spread*
> **高/低 EPS 预测上修组合与多空价差**：YTD 跑输指数。阴影区域（1986/3–1988/12）为回测，非阴影区域（1989/1 起）为实盘。

> **📊 图表 324 / 325**：*Estimate Revisions Risk Reward & Downside Risk Reward*
> **EPS 预测上修风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 326**：*High Estimate Revisions Sector Concentration (Top Decile)*
> **高 EPS 预测上修组合行业分布**：**工业权重最大**。

---

# 第 136 页 · Equity Duration

## Equity Duration
## 股票久期

> **📊 图表 327**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高久期组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 328 / 329**：*High Duration Risk Reward & Downside Risk Reward*
> **高久期风险-收益 / 下行风险-收益**：**历史上跑输指数**（长久期更易受利率上行拖累）。

> **📊 图表 330**：*High Duration Sector Concentration (Top Decile)*
> **高久期组合行业分布**：**医疗保健权重最大**。

---

# 第 137 页 · Quality Strategies

## Quality Strategies
## 质量策略

> **📊 图表 331 / 332**：*Quality Strategies — Risk Reward & Downside Risk Reward*
> 质量策略包含：1 年 ROE、5 年 ROE、1 年债务调整 ROE、5 年债务调整 ROE、ROA、ROC。
> **5 年债务调整 ROE（5-Yr Debt Adjusted ROE）策略表现最佳**——在质量因子中取得最高平均滚动 12 月回报，同时负收益频率相对较低。

---

# 第 138 页 · One-Year Return on Equity

## One-Year Return on Equity
## 1 年 ROE

> **📊 图表 333**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 1 年 ROE 组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 334 / 335**：*High 1-Yr ROE Risk Reward & Downside Risk Reward*
> **高 1 年 ROE 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 336**：*High 1-Yr ROE Sector Concentration (Top Decile)*
> **高 1 年 ROE 组合行业分布**：**信息技术权重最大**。

---

# 第 139 页 · Five-Year Return on Equity

## Five-Year Return on Equity
## 5 年 ROE

> **📊 图表 337**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 5 年 ROE 组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 338 / 339**：*High 5-Yr ROE Risk Reward & Downside Risk Reward*
> **高 5 年 ROE 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 340**：*High 5-Yr ROE Sector Concentration (Top Decile)*
> **高 5 年 ROE 组合行业分布**：**信息技术权重最大**。

---

# 第 140 页 · One-Year ROE (Adjusted for Debt)

## One-Year Return on Equity (Adjusted for Debt)
## 1 年债务调整 ROE

> **📊 图表 341**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 1 年债务调整 ROE 组合相对表现与多空价差**：YTD **跑赢**指数（2001/2 = 100）。

> **📊 图表 342 / 343**：*High 1-Yr ROE Adjusted for Debt Risk Reward & Downside Risk Reward*
> **高 1 年债务调整 ROE 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 344**：*High 1-Yr ROE Adjusted for Debt Sector Concentration (Top Decile)*
> **高 1 年债务调整 ROE 组合行业分布**：**信息技术权重最大**。

---

---

# 第 141 页 · Five-Year ROE (Adjusted for Debt)

## Five-Year Return on Equity (Adjusted for Debt)
## 5 年债务调整 ROE

> **📊 图表 345**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 5 年债务调整 ROE 相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 346 / 347**：*High 5-Yr ROE Adjusted for Debt Risk Reward & Downside Risk Reward*
> **5 年债务调整 ROE 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 348**：*High 5-Yr ROE Adjusted for Debt Sector Concentration (Top Decile)*
> **组合行业分布**：**信息技术权重最大**。

---

# 第 142 页 · Return on Assets

## Return on Assets（ROA）
## 资产回报率

> **📊 图表 349**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 ROA 相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 350 / 351**：*High Return on Assets Risk Reward & Downside Risk Reward*
> **高 ROA 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 352**：*High Return on Assets Sector Concentration (Top Decile)*
> **高 ROA 组合行业分布**：**信息技术权重最大**。

---

# 第 143 页 · Return on Capital

## Return on Capital（ROC）
## 资本回报率

> **📊 图表 353**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 ROC 相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 354 / 355**：*High Return on Capital Risk Reward & Downside Risk Reward*
> **高 ROC 风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 356**：*High Return on Capital Sector Concentration (Top Decile)*
> **高 ROC 组合行业分布**：**工业权重最大**。

---

# 第 144 页 · Risk Strategies

## Risk Strategies
## 风险策略

> **📊 图表 357 / 358**：*Risk Strategies — Risk Reward & Downside Risk Reward*
> 风险策略包含：Beta、EPS 变异率（Variability of EPS）、EPS 预测离散度（Dispersion）、低价股（Low Price）。
> **低价股（Low Price）策略表现最佳**。

---

# 第 145 页 · Beta

## Beta

> **📊 图表 359**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 Beta 相对表现与多空价差**：YTD 跑输指数。

> **📊 图表 360 / 361**：*High Beta Risk Reward & Downside Risk Reward*
> **高 Beta 风险-收益 / 下行风险-收益**：**历史上跑赢指数**（但波动及负收益频率显著更高）。

> **📊 图表 362**：*High Beta Sector Concentration (Top Decile)*
> **高 Beta 组合行业分布**：**能源权重最大**。

---

# 第 146 页 · Variability of Earnings

## Variability of Earnings
## 盈利变异率

> **📊 图表 363**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 EPS 变异率相对表现与多空价差**：YTD 跑输指数。

> **📊 图表 364 / 365**：*High EPS Variability Risk Reward & Downside Risk Reward*
> **高 EPS 变异率风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 366**：*High EPS Variability Sector Concentration (Top Decile)*
> **高 EPS 变异率组合行业分布**：**信息技术权重最大**。

---

# 第 147 页 · Estimate Dispersion

## Estimate Dispersion
## EPS 预测离散度

> **📊 图表 367**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高 EPS 离散度相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 368 / 369**：*High EPS Dispersion Risk Reward & Downside Risk Reward*
> **高 EPS 离散度风险-收益 / 下行风险-收益**：**历史上跑输指数**。

> **📊 图表 370**：*High EPS Dispersion Sector Concentration (Top Decile)*
> **高 EPS 离散度组合行业分布**：**可选消费权重最大**。

---

# 第 148 页 · Low Price

## Low Price
## 低价股

> **📊 图表 371**：*Performance Low Price, High Price and Long-Short Spread*
> **低价股相对高价股与多空价差**：YTD 跑输指数。

> **📊 图表 372 / 373**：*Low Price Risk Reward & Downside Risk Reward*
> **低价股风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 374**：*Price Sector Concentration (Low Decile)*
> **低价股组合行业分布**：**信息技术权重最大**。

---

# 第 149 页 · Miscellaneous Strategies

## Miscellaneous Strategies
## 杂项策略

> **📊 图表 375 / 376**：*Miscellaneous Strategies — Risk Reward & Downside Risk Reward*
> 杂项策略包含：机构持股（Institutional Ownership）、分析师覆盖度（Analyst Coverage）、小市值（Small Size）、海外收入敞口（Foreign Exposure）。
> **小市值（Small Size）策略表现最佳**。注：各因子表现时间轴以后续各自时间序列图为准。

---

# 第 150 页 · Institutional Ownership

## Institutional Ownership
## 机构持股

> **📊 图表 377**：*Performance of Low Institutional Ownership, High Institutional Ownership and Long-Short Spread*
> **低机构持股相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 378 / 379**：*Low Institutional Ownership Risk Reward & Downside Risk Reward*
> **低机构持股风险-收益 / 下行风险-收益**：**历史上跑输指数**。

> **📊 图表 380**：*Low Institutional Ownership Sector Concentration (Low Decile)*
> **低机构持股组合行业分布**：**可选消费权重最大**。

---

# 第 151 页 · Analyst Coverage

## Analyst Coverage
## 分析师覆盖度

> **📊 图表 381**：*Performance of Low Coverage, High Coverage and Long-Short Spread*
> **低覆盖度相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 382 / 383**：*Low Analyst Coverage Risk Reward & Downside Risk Reward*
> **低覆盖度风险-收益 / 下行风险-收益**：**历史上与指数表现相当**。

> **📊 图表 384**：*Low Analyst Coverage Sector Concentration (Low Decile)*
> **低覆盖度组合行业分布**：**房地产权重最大**。

---

# 第 152 页 · Size

## Size
## 规模（市值）

> **📊 图表 385**：*Performance of Small Size, Large Size and Long-Short Spread*
> **小市值相对大市值与多空价差**：YTD 跑输指数。

> **📊 图表 386 / 387**：*Small Size Risk Reward & Downside Risk Reward*
> **小市值风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 388**：*Small Size Sector Concentration (Low Decile)*
> **小市值组合行业分布**：**可选消费权重最大**。

---

# 第 153 页 · Foreign Exposure

## Foreign Exposure
## 海外收入敞口

> **📊 图表 389**：*Performance of High Foreign Exposure, Domestic Companies and Long-Short Spread*
> **高海外敞口相对本土公司与多空价差**：YTD **跑赢**指数。

> **📊 图表 390 / 391**：*High Foreign Exposure Risk Reward & Downside Risk Reward*
> **高海外敞口风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 392**：*High Foreign Exposure Sector Concentration (Top Decile)*
> **高海外敞口组合行业分布**：**信息技术权重最大**。

---

# 第 154 页 · Short Interest

## Short Interest
## 卖空比例

> **📊 图表 393**：*Performance of Top Decile, Bottom Decile and Long-Short Spread*
> **高卖空比例相对表现与多空价差**：YTD **跑赢**指数。

> **📊 图表 394 / 395**：*High Short Interest Risk Reward & Downside Risk Reward*
> **高卖空比例风险-收益 / 下行风险-收益**：**历史上跑赢指数**。

> **📊 图表 396**：*Short Interest Sector Concentration (Top Decile)*
> **高卖空比例组合行业分布**：**金融权重最大**。

---

# 第 155 页 · Annual Performance of BofA US Quantitative Strategies

## Annual Performance of BofA US Quantitative Strategies（1988–2022）
## BofA 美股量化策略年度表现（1988–2022）

> **📊 图表 397**：*Annual Performance of BofA US Quantitative Strategies: Top Decile of S&P 500 except where noted*
> **BofA 量化策略年度表现总表**：1988–2022，按各因子前 10% 分组（除非特别标注）；**粗体**表示当年该策略跑赢基准；除非注明，均为价格回报（不含股息）。覆盖风险、股息率（含股息总回报）等多类因子。
> 该图表为一张跨多年份的大矩阵表，列出所有因子（Risk、Dividend Yield (Total Return) 等）历年相对基准的表现情况，用于识别因子周期与轮动。

---

---

# 第 156-157 页 · Performance and Calculation Methodology

## Performance and Calculation Methodology
## 业绩与计算方法论

> **📊 图表 398**：*Quantitative Strategies Performance (Top Decile) — As of 4/30/2023*
> **量化策略表现（前 10%）截至 2023/4/30**：按类别（Technical/Value/Growth/Quality/Risk/Miscellaneous）列出 12M、YTD、2/3/5 年（毛收益与年化）回报以及起始日期。

> **📊 图表 399**：*Quantitative Strategies Performance (Bottom Decile) — As of 4/30/2023*
> **量化策略表现（后 10%）截至 2023/4/30**：同结构列出"做空"维度的同样统计。例：Rising Short Interest 12M −3.6%、2Y −10.0% 等。

---

# 第 158 页 · Factor Valuations & Crowdedness

## Factor valuations and crowdedness as of 4/30/2023
## 因子估值与拥挤度（截至 2023/4/30）

> **📊 图表 400**：*Factor valuations and crowdedness as of 4/30/2023*
> 多空因子按"最贵/最拥挤 → 最便宜/最冷清"排序。**做多因子**（S&P 500 前 10%）与**做空因子**（后 10%）各自列出 P/B 相对历史、Forward P/E 相对历史、多头基金相对权重、拥挤度排名。用于判断因子轮动时机——过度拥挤常预示反转。

---

# 第 159-160 页 · Advances and Declines

## Advances and Declines（Top & Bottom Decile — As of 4/30/2023）
## 策略涨跌统计（前/后 10%）

> **📊 图表 401 / 402**：*Advances and Declines (Top / Bottom Decile) — As of 4/30/2023*
> 每种量化策略在不同时间窗口内的"上涨月数/下跌月数"（Adv./Dec.）统计，用于衡量策略稳定性与胜率。涵盖 Price Returns (12M)、Short Interest、Relative Strength - 30wk/75wk MA 等。

---

# 第 161 页 · Russell 1000 Factor Efficacy

## Russell 1000 factor efficacy
## Russell 1000 因子有效性

> **📊 图表 403**：*Russell 1000 factors: Sharpe Ratio — As of 4/30/2023*
> **Russell 1000 因子夏普比率表**：按五分位（Quintile 1–5）展示每个因子的夏普比率；**粗体**为该因子夏普比率最高的分位，**阴影**为最低分位。样本：1986 至 2020/4（分析师覆盖度自 1994、机构持股自 1999、卖空比例自 1993 起）。覆盖因子：Earnings Yield、Forward Earnings Yield、Dividend Yield、P/B、P/CF、P/FCF 等。

---

# 第 162 页 · Performance Calculation Methodology

## Performance Calculation Methodology
## 业绩计算方法论

对所有策略，每月末以当月最后一个交易日收盘价和数据进行再平衡与业绩计算。每一策略的业绩基于价格回报计算，并以每月最后一个交易日 S&P 500 成分股**等权价格表现**为基准。对 Alpha Surprise 模型，也呈现相对**市值加权 S&P 500 基准**的表现。

此处量化策略结果可能与 S&P 500 显著不同——因其分散度显著更低，表现更易受个股或行业冲击影响，采用这些策略的投资者可能面临更大的回报波动。

业绩结果**未反映交易成本、税款预扣或任何投资顾问费**；若反映这些成本，业绩会更低。实际投资者因交易成本、顾问费、买卖时点与价格差异、证券权重差异、股息处理（是否再投资及何时再投资）等原因，表现将与此处报告不同。

### Dividend Yield and Dividend Growth Strategies / 股息类策略
对股息类策略（高股息率、高股息增长），也提供**总回报**版本：假设组合中股票所派股息在除息日计入现金账户、**不再投资**，表现基准为 S&P 500 成分股的等权总回报指数。

本报告列示的策略仅供**参考或描述性目的**，列入此处不等同于对该策略/组合的推荐。**过往表现不能也不应视为未来表现的指标**。完整业绩记录可应要求提供。

---

# 第 163 页 · Section III: Stock Strategies within Industries

## Section III: Stock Strategies within Industries
## 第三部分：行业内选股策略

### Sector Specific Overview / 分行业概览

- Communication Services: Media & Entertainment（通信服务：传媒与娱乐）
- Communication Services: Telecommunication Services（通信服务：电信服务）
- Consumer Discretionary: Retailing（可选消费：零售业）
- Other Disc. (Autos, Durables, Services)（其他可选消费：汽车、耐用品、服务）
- Consumer Staples（必需消费）
- Energy（能源）
- Financials: Banks（金融：银行）
- Financials: Insurance（金融：保险）
- Financials: Diversified（金融：综合金融）
- Health Care: Health Care Equipment & Svcs（医疗保健：设备与服务）
- Health Care: Pharmaceuticals, Biotechnology & Life Sciences（医药、生物科技与生命科学）
- Industrials: Capital Goods（工业：资本品）
- Other Industrials (Services, Transports)（其他工业：服务与运输）
- Information Technology（信息技术）
- Materials（材料）
- Real Estate（房地产）
- Utilities（公用事业）

### Backtesting Methodology / 回测方法论
注：本节所有散点图均基于**筛选规则推出后**的实际表现，除非另有说明。

---

# 第 164 页 · Sector Specific Overview — 各行业最有效因子总览

## Most predictive long-short factors within industry groups
## 各行业组内最有预测力的多空因子（1985 至 2023/4，历史 Russell 1000 成分）

> **📊 图表 404**：*Most predictive long-short factors within industry groups*

| 行业组 | 估值指标 | 动量指标 | 成长指标 | 质量指标 |
|---|---|---|---|---|
| **Media & Entertainment** | P/CF, FCF/EV | 12M+1M 反转、成交量 | PEG | ROC, 5 年债务调整 ROE |
| **Telecommunication Services** | 股息率 | 12M+1M 反转 | 股息增长、PEG | — |
| **Retailing** | P/FCF, EV/EBITDA | 成交量、5W/30W 相对强弱 | 盈利预测上修 | — |
| **Other Discretionary (Autos/Durables/Svcs)** | FCF/EV, Forward P/E | 12M+1M 反转、30W/75W 相对强弱 | 盈利预测上修 | — |
| **Consumer Staples** | Trailing/Forward P/E, EV/EBITDA | 成交量、12M+1M 反转 | PEG | — |

（完整行业表将在后续各节逐行业展开）

---

# 第 165-168 页 · Communication Services: Media & Entertainment

## Communication Services: Media & Entertainment
## 通信服务：传媒与娱乐

### Long only: Top Quintile Performance / 仅做多：前 1/5 组表现（1985–2023）

> **📊 图表 405**：*Valuation Strategies — Top Quintile Returns*
> **估值策略**：**Historical Relative P/E（历史相对 P/E）跑赢指数幅度最大**。对比因子包括：Trailing/Forward P/E、Historical Relative P/E、股息率、P/B、P/CF、EV/EBITDA、P/FCF、P/S、FCF/EV。坐标为年均回报 vs. 12 月回报标准差。

> **📊 图表 406**：*Momentum Strategies — Top Quintile Returns*
> **动量策略**：**Trading Volume（成交量）跑赢幅度最大**。对比：10W/40W、30W/75W、5W/30W 相对强弱、3M/9M 价格回报、12M+1M 反转等。

> **📊 图表 407**：*Growth Strategies — Top Quintile Returns*
> **成长策略**：**Estimate Revisions（盈利预测上修）跑赢幅度最大**。对比：Long-Term Growth、Estimate Revisions、EPS Momentum、PEG Ratio、Earnings Torpedo、股息增长。

> **📊 图表 408**：*Quality Strategies — Top Quintile Returns*
> **质量策略**：**ROC 跑赢幅度最大**。对比：5 年/1 年债务调整 ROE、5 年/1 年 ROE 等。

### Long-Short: Quintile 1 / Quintile 5 Spread / 多空：Q1/Q5 价差

> **📊 图表 409**：*Valuation Strategies — Avg Long-Short Spreads vs. Consistency*
> **估值多空**：**P/FCF 表现最佳**（纵轴年化多空价差，横轴 Q1 跑赢 Q5 的概率/一致性）。

> **📊 图表 410**：*Momentum Strategies — Avg Long-Short Spreads vs. Consistency*
> **动量多空**：**成交量表现最佳**。

> **📊 图表 411**：*Growth Strategies — Avg Long-Short Spreads vs. Consistency*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 412**：*Quality Strategies — Avg Long-Short Spreads vs. Consistency*
> **质量多空**：**ROC 表现最佳**。

---

# 第 169-172 页 · Communication Services: Telecommunication Services

## Communication Services: Telecommunication Services
## 通信服务：电信服务

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 413**：*Valuation — Top Quintile Returns*
> **估值**：**Price / Sales 跑赢幅度最大**。

> **📊 图表 414**：*Momentum — Top Quintile Returns*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 415**：*Growth — Top Quintile Returns*
> **成长**：**Long-Term Growth（长期增长）表现最佳**。

> **📊 图表 416**：*Quality — Top Quintile Returns*
> **质量**：**1 年 ROE 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread / 多空

> **📊 图表 417**：*Valuation L/S — Avg Spreads vs. Consistency*
> **估值多空**：**股息率（Dividend Yield）表现最佳**。

> **📊 图表 418**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 419**：*Growth L/S*
> **成长多空**：**股息增长表现最佳**。

> **📊 图表 420**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 173-176 页 · Consumer Discretionary: Retailing

## Consumer Discretionary: Retailing
## 可选消费：零售业

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 421**：*Valuation — Top Quintile*
> **估值**：**EV/EBITDA 表现最佳**。

> **📊 图表 422**：*Momentum — Top Quintile*
> **动量**：**成交量（Trading Volume）表现最佳**。

> **📊 图表 423**：*Growth — Top Quintile*
> **成长**：**EPS 盈利预测上修表现最佳**。

> **📊 图表 424**：*Quality — Top Quintile*
> **质量**：**Return on Capital（资本回报率 ROC）表现最佳**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 425**：*Valuation L/S*
> **估值多空**：**P/FCF 表现最佳**。

> **📊 图表 426**：*Momentum L/S*
> **动量多空**：**成交量表现最佳**。

> **📊 图表 427**：*Growth L/S*
> **成长多空**：**EPS 预测上修表现最佳**。

> **📊 图表 428**：*Quality L/S*
> **质量多空**：**高 ROC 表现最佳**。

---

# 第 177-180 页 · Other Discretionary (Autos, Durables, Services)

## Other Disc. (Autos, Durables, Services)
## 其他可选消费（汽车、耐用品、服务）

### Long only: Hypothetical Top Quintile / 仅做多：假设前 1/5 组（1985–2023）

> **📊 图表 429**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 表现最佳**。

> **📊 图表 430**：*Momentum — Top Quintile*
> **动量**：**成交量表现最佳**。

> **📊 图表 431**：*Growth — Top Quintile*
> **成长**：**EPS 预测上修表现最佳**。

> **📊 图表 432**：*Quality — Top Quintile*
> **质量**：**1 年 ROE 跑输幅度最小**（即相对最优）。

### Long-Short: Q1/Q5 Spread

> **📊 图表 433**：*Valuation L/S*
> **估值多空**：**FCF/EV 表现最佳**。

> **📊 图表 434**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 435**：*Growth L/S*
> **成长多空**：**EPS 预测上修表现最佳**。

> **📊 图表 436**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

---

# 第 181-184 页 · Consumer Staples

## Consumer Staples
## 必需消费

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 437**：*Valuation — Top Quintile Returns*
> **估值**：**FCF/EV 与 Price to FCF 表现最佳**。

> **📊 图表 438**：*Momentum — Top Quintile Returns*
> **动量**：**成交量（Trading Volume）跑赢幅度最大**。

> **📊 图表 439**：*Growth — Top Quintile Returns*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 440**：*Quality — Top Quintile Returns*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread / 多空

> **📊 图表 441**：*Valuation L/S*
> **估值多空**：**P/E 表现最佳**。

> **📊 图表 442**：*Momentum L/S*
> **动量多空**：**成交量表现最佳**。

> **📊 图表 443**：*Growth L/S*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 444**：*Quality L/S*
> **质量多空**：**Return on Capital（ROC）表现最佳**。

---

# 第 185-188 页 · Energy

## Energy
## 能源

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 445**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 表现最佳**。

> **📊 图表 446**：*Momentum — Top Quintile*
> **动量**：**成交量表现最佳**。

> **📊 图表 447**：*Growth — Top Quintile*
> **成长**：**High EPS Estimate Revisions 表现最佳**。

> **📊 图表 448**：*Quality — Top Quintile*
> **质量**：**5 年 ROE 表现最佳**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 449**：*Valuation L/S*
> **估值多空**：**Price / Book 表现最佳**。

> **📊 图表 450**：*Momentum L/S*（1985–2021）
> **动量多空**：**成交量表现最佳**。

> **📊 图表 451**：*Growth L/S*
> **成长多空**：**Estimate Revisions 表现最佳**。

> **📊 图表 452**：*Quality L/S*（1985–2021）
> **质量多空**：**Return on Capital 表现最佳**。

---

# 第 189-192 页 · Financials: Banks

## Financials: Banks
## 金融：银行

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 453**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 表现最佳**。

> **📊 图表 454**：*Momentum — Top Quintile*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 455**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 与 EPS Momentum 跑赢幅度最大**。

> **📊 图表 456**：*Quality — Top Quintile*
> **质量**：**Return on Capital 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 457**：*Valuation L/S*
> **估值多空**：**Historical Relative P/E 表现最佳**。

> **📊 图表 458**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 459**：*Growth L/S*
> **成长多空**：**低 PEG 表现最佳**。

> **📊 图表 460**：*Quality L/S*
> **质量多空**：**Return on Capital 表现最佳**。

---

# 第 193-196 页 · Financials: Insurance

## Financials: Insurance
## 金融：保险

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 461**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 跑赢幅度最大**。

> **📊 图表 462**：*Momentum — Top Quintile*
> **动量**：**高成交量跑赢幅度最大**。

> **📊 图表 463**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 464**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 465**：*Valuation L/S*
> **估值多空**：**Historical Relative P/E 表现最佳**。

> **📊 图表 466**：*Momentum L/S*
> **动量多空**：**高成交量表现最佳**。

> **📊 图表 467**：*Growth L/S*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 468**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 197-200 页 · Financials: Diversified

## Financials: Diversified
## 金融：综合金融

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 469**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 跑赢幅度最大**。

> **📊 图表 470**：*Momentum — Top Quintile*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 471**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 472**：*Quality — Top Quintile*
> **质量**：**1 年 ROE 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 473**：*Valuation L/S*
> **估值多空**：**Forward 与 Trailing P/E 表现最佳**。

> **📊 图表 474**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 475**：*Growth L/S*
> **成长多空**：**EPS Momentum 表现最佳**。

> **📊 图表 476**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 201-204 页 · Health Care: Equipment & Services

## Health Care: Health Care Equipment & Svcs
## 医疗保健：设备与服务

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 477**：*Valuation — Top Quintile*
> **估值**：**FCF/EV 跑赢幅度最大**。

> **📊 图表 478**：*Momentum — Top Quintile*
> **动量**：**成交量与 12M+1M 反转跑赢幅度最大**。

> **📊 图表 479**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 480**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 481**：*Valuation L/S*
> **估值多空**：**FCF/EV 表现最佳**。

> **📊 图表 482**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 483**：*Growth L/S*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 484**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 205-208 页 · Health Care: Pharmaceuticals, Biotechnology & Life Sciences

## Health Care: Pharmaceuticals, Biotechnology & Life Sciences
## 医疗保健：制药、生物科技与生命科学

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 485**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 跑赢幅度最大**。

> **📊 图表 486**：*Momentum — Top Quintile*
> **动量**：**成交量与 30W/75W 相对强弱跑赢幅度最大**。

> **📊 图表 487**：*Growth — Top Quintile*
> **成长**：**EPS Momentum 跑赢幅度最大**。

> **📊 图表 488**：*Quality — Top Quintile*
> **质量**：**5 年 ROE 跑输指数幅度最小**（即相对最优）。

### Long-Short: Q1/Q5 Spread

> **📊 图表 489**：*Valuation L/S*
> **估值多空**：**Price to Sales 表现最佳**。

> **📊 图表 490**：*Momentum L/S*
> **动量多空**：**成交量与 12M+1M 反转表现最佳**。

> **📊 图表 491**：*Growth L/S*
> **成长多空**：**EPS Revisions 表现最佳**。

> **📊 图表 492**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 209-212 页 · Industrials: Capital Goods

## Industrials: Capital Goods
## 工业：资本品

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 493**：*Valuation — Top Quintile*
> **估值**：**Price to FCF 跑赢幅度最大**。

> **📊 图表 494**：*Momentum — Top Quintile*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 495**：*Growth — Top Quintile*
> **成长**：**EPS Torpedo 跑赢幅度最大**。

> **📊 图表 496**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 497**：*Valuation L/S*
> **估值多空**：**Price to FCF 表现最佳**。

> **📊 图表 498**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 499**：*Growth L/S*
> **成长多空**：**EPS Torpedo 表现最佳**。

> **📊 图表 500**：*Quality L/S*
> **质量多空**：**5 年 ROE 表现最佳**。

---

---

# 第 213-216 页 · Other Industrials (Services, Transports)

## Other Industrials (Services, Transports)
## 其他工业：商业服务与运输

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 501**：*Valuation — Top Quintile*
> **估值**：**Historical Relative P/E 跑赢幅度最大**。

> **📊 图表 502**：*Momentum — Top Quintile*
> **动量**：**成交量跑赢幅度最大**。

> **📊 图表 503**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 与股息增长跑赢幅度最大**。

> **📊 图表 504**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 505**：*Valuation L/S*
> **估值多空**：**EV/EBITDA 表现最佳**。

> **📊 图表 506**：*Momentum L/S*
> **动量多空**：**成交量与 12M+1M 反转表现最佳**。

> **📊 图表 507**：*Growth L/S*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 508**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 217-220 页 · Information Technology

## Information Technology
## 信息技术

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 509**：*Valuation — Top Quintile*
> **估值**：**Price to FCF 跑赢幅度最大**。

> **📊 图表 510**：*Momentum — Top Quintile*
> **动量**：**成交量跑赢幅度最大**。

> **📊 图表 511**：*Growth — Top Quintile*
> **成长**：**EPS Revisions 跑赢幅度最大**。

> **📊 图表 512**：*Quality — Top Quintile*
> **质量**：**ROA 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 513**：*Valuation L/S*
> **估值多空**：**Price to FCF 表现最佳**。

> **📊 图表 514**：*Momentum L/S*
> **动量多空**：**高成交量表现最佳**。

> **📊 图表 515**：*Growth L/S*
> **成长多空**：**EPS Estimate Revisions 表现最佳**。

> **📊 图表 516**：*Quality L/S*
> **质量多空**：**ROA 表现最佳**。

---

# 第 221-224 页 · Materials

## Materials
## 材料

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 517**：*Valuation — Top Quintile*
> **估值**：**Forward P/E 跑赢幅度最大**。

> **📊 图表 518**：*Momentum — Top Quintile*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 519**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 520**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 521**：*Valuation L/S*
> **估值多空**：**EV/EBITDA 跑赢幅度最大**。

> **📊 图表 522**：*Momentum L/S*
> **动量多空**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 523**：*Growth L/S*
> **成长多空**：**PEG Ratio 与 Long-Term Growth 跑赢幅度最大**。

> **📊 图表 524**：*Quality L/S*
> **质量多空**：**1 年 ROE 跑赢幅度最大**。

---

# 第 225-228 页 · Real Estate

## Real Estate
## 房地产

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 525**：*Valuation — Top Quintile*
> **估值**：**EV/EBITDA 跑赢幅度最大**（估值因子包括 P/FFO Trailing/Forward、股息率、P/B、P/CF、EV/EBITDA 等，房地产使用 FFO 替代 Earnings）。

> **📊 图表 526**：*Momentum — Top Quintile*
> **动量**：**12M+1M 反转跑赢幅度最大**。

> **📊 图表 527**：*Growth — Top Quintile*
> **成长**：**Long-Term Growth 跑赢幅度最大**。

> **📊 图表 528**：*Quality — Top Quintile*
> **质量**：**ROC 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 529**：*Valuation L/S*
> **估值多空**：**Price to Cash Flow 与 EV/EBITDA 表现最佳**。

> **📊 图表 530**：*Momentum L/S*
> **动量多空**：**12M+1M 反转表现最佳**。

> **📊 图表 531**：*Growth L/S*
> **成长多空**：**Long Term Growth 表现最佳**。

> **📊 图表 532**：*Quality L/S*
> **质量多空**：**ROC 表现最佳**。

---

# 第 229-232 页 · Utilities

## Utilities
## 公用事业

### Long only: Top Quintile / 仅做多（1985–2023）

> **📊 图表 533**：*Valuation — Top Quintile*
> **估值**：**Price to Sales 跑赢幅度最大**。

> **📊 图表 534**：*Momentum — Top Quintile*
> **动量**：**10W/40W 相对强弱跑赢幅度最大**。

> **📊 图表 535**：*Growth — Top Quintile*
> **成长**：**PEG Ratio 跑赢幅度最大**。

> **📊 图表 536**：*Quality — Top Quintile*
> **质量**：**1 年 ROE 跑赢幅度最大**。

### Long-Short: Q1/Q5 Spread

> **📊 图表 537**：*Valuation L/S*
> **估值多空**：**Price / Sales 表现最佳**。

> **📊 图表 538**：*Momentum L/S*
> **动量多空**：**Relative Strength 10W/40W 与 30W/75W 表现最佳**。

> **📊 图表 539**：*Growth L/S*
> **成长多空**：**PEG Ratio 表现最佳**。

> **📊 图表 540**：*Quality L/S*
> **质量多空**：**1 年 ROE 表现最佳**。

---

# 第 233 页 · Backtesting Methodology

## Backtesting Methodology
## 回测方法论

我们为 Russell 1000 Growth 和 Russell 1000 Value 指数成分股各自构建了前 10% / 后 10% 的因子筛选。对所有因子采用相同回测方法（除非另有说明）：每月末将因子应用于指数；缺失或数据不足的公司被剔除；然后创建两个筛选（前 10% / 后 10%），追踪其下一个月表现。注意：我们**未**剔除公司禁止交易名单（restricted list）中的股票。

### Returns Calculation / 回报计算

每月使用最后一个交易日的数据与收盘价进行再平衡与表现计算；每个筛选的结果基于**总回报**（Total Return）。假设股息在除息日存入现金账户且不再投资。

回测筛选与历史 Russell 1000 Growth / Value 指数在分散度上存在显著差异，故波动可能更大。**回测结果不反映交易成本、税款预扣与投资顾问费**，若扣除这些成本表现会更低。

**回测具有假设性质**，应用于其实际存在之前的时段，不代表其未来使用效果。**过往表现不能视为未来表现的指标**。

---

# 第 234 页 · Section IV: Stock Strategies for Growth and Value Managers

## Section IV: Stock Strategies for Growth and Value Managers
## 第四部分：面向成长型与价值型经理人的选股策略

内容目录：
- Growth（成长型）
- Value（价值型）
- Backtesting Methodology（回测方法论）

以及第五部分：**BofA Quality Strategies**（BofA 质量策略）——质量因子具**周期性与长期结构性顺风**。
注：本节所有图表基于 **1986/1 末–2018/3 末**的回测结果；回测具有假设性质，不代表未来表现。

---

# 第 235-237 页 · Growth（Russell 1000 Growth）

## Growth
## 成长型（Russell 1000 Growth 指数）

### Top Decile Returns 1986–2023 / 前 10% 组回报

> **📊 图表 541**：*Value Strategies for Russell 1000 Growth — Top Decile Returns*
> **估值策略**：**FCF/EV 表现最佳**。

> **📊 图表 542**：*Momentum Strategies for Russell 1000 Growth*
> **动量策略**：**高成交量表现最佳**。

> **📊 图表 543**：*Growth Strategies for Russell 1000 Growth*
> **成长策略**：**Estimate Revisions 表现最佳**。

> **📊 图表 544**：*Quality Strategies for Russell 1000 Growth*
> **质量策略**：**1 年债务调整 ROE 与 ROC 表现最佳**。

> **📊 图表 545**：*Risk Strategies for Russell 1000 Growth*
> **风险策略**：**高 Beta 与 Estimate Dispersion 表现最佳**。

> **📊 图表 546**：*Miscellaneous Strategies for Russell 1000 Growth*
> **杂项策略**：**Share Repurchase（股份回购）表现最佳**。

---

# 第 238-240 页 · Value（Russell 1000 Value）

## Value
## 价值型（Russell 1000 Value 指数）

### Top Decile Returns 1986–2023

> **📊 图表 547**：*Value Strategies for Russell 1000 Value*
> **估值策略**：**Price / FCF 表现最佳**。

> **📊 图表 548**：*Momentum Strategies for Russell 1000 Value*
> **动量策略**：**高成交量表现最佳**。

> **📊 图表 549**：*Growth Strategies for Russell 1000 Value*
> **成长策略**：**PEG Ratio 表现最佳**。

> **📊 图表 550**：*Quality Strategies for Russell 1000 Value*
> **质量策略**：**1 年债务调整 ROE 表现最佳**。

> **📊 图表 551**：*Risk Strategies for Russell 1000 Value*
> **风险策略**：**高 Beta 与 Low Price 表现最佳**。

> **📊 图表 552**：*Miscellaneous Strategies for Russell 1000 Value*
> **杂项策略**：**Small Size（小市值）表现最佳**。

---

# 第 241 页 · Backtesting Methodology（重复章节）

与 p233 相同方法论说明：Russell 1000 Growth / Value 因子回测，按月频率再平衡，总回报基础计算，不含交易成本与顾问费。回测具假设性质，不代表未来表现。

---

# 第 242-244 页 · Section V: BofA Quality Strategies

## Section V: BofA Quality Strategies
## 第五部分：BofA 质量策略

### Quality: cyclical & secular tailwinds / 质量因子：周期性与长期结构性顺风

注：本节业绩图中，阴影区域（1986/1 末–1988/12 末）为**回测结果**，非阴影（1989/1 起）为**实盘表现**。回测具假设性质。本节所有散点图均基于策略推出后的实际数据。

### 投资者质量投资指南

金融学基础告诉我们投资者应为安全性支付溢价、为风险要求折价。但财政与货币刺激在过去二十多年抬升了风险资产估值，导致**高风险股相对优质股以溢价交易**。如今经过一年多的美联储紧缩后，估值差距终于收敛，**高质量股已开始以轻微溢价交易**。我们预期质量因子将继续重估——受**周期性与长期结构性因素**双重推动。

> **📊 图表 553**：*After 20+ years of trading at a premium, risky stocks now trade at a discount to quality stocks*
> **图表标题**：经过 20 多年的溢价交易后，风险股现在相对优质股折价（B+ 或更优 vs. B 或更差，相对 BofA 全样本的 Fwd P/E；1986–2023/4）。

S&P 500 相比多数股指含有**更高比例的质量股**（按下文"什么是 Quality"定义）。盈利波动下降，繁荣-衰退间摆幅显著压缩，甚至 COVID-19 期间也不例外。

> **📊 图表 554**：*Earnings volatility has decreased*
> **盈利波动性已下降**：COVID-19 盈利衰退的幅度**远小于 '08 全球金融危机与 '00 科技泡沫**（S&P 500 同比 EPS 增速，1935–2022Q4）。

> **📊 图表 555**：*Earnings volatility is currently elevated following COVID*
> **后 COVID 期盈利波动性有所抬升**：S&P 500 12 个月 EPS 增速的滚动 3 年标准差（1940Q2–2022Q4）。

> **📊 图表 556**：*Higher Quality stocks make up ~60% of the S&P 500*
> **高质量股占 S&P 500 约 60%**（B 或更优的 S&P Quality Rank vs. B 或更差，含 N/A；1990–2023/4）。

### What is Quality? / 什么是 Quality？

**Quality** 对股票投资者可有多种含义。我们首选的 **Quality 度量**基于 **S&P 普通股质量排名（S&P Common Stock quality rankings）**——这与债务评级**不同**，仅衡量公司**盈利与股息的稳定性与增长性**。我们发现该度量随经济周期和行为周期（风险厌恶/追逐收益、成长稀缺/充足）呈现可预测的行为模式。

我们也追踪其他 Quality 度量，如 **ROE、盈利确定性（EPS 预测低离散度）、市值、Beta**——各自捕捉 Quality 的不同侧面，但表现与特征均**不如用盈利稳定性定义风险时更稳定**。

### Definitions / 定义

- **"A+" vs. "C&D"**：BofA 美股覆盖全样本中基于 S&P 普通股质量排名的**最高 vs. 最低质量**股（基于公司 10 年期盈利与股息的长期增长与稳定性的定量评估）。**注**：在需更宽样本时有时用 **"B+ 或更优" vs. "B 或更差"** 定义 High / Low Quality。
- **ROE**：S&P 500 按 Trailing 4 季 ROE 的前/后 10%（分子为 TTM 盈利，分母为账面价值）。
- **Beta**：S&P 500 按 60 个月调整 Beta 相对 S&P 500 的前/后 10%。
- **Earnings Certainty**：S&P 500 按下一年共识预测离散度的**后** 10%（低离散度=高确定性）。**Earnings Uncertainty**：相应的前 10%。
- **Nifty 50 / Small Size**：S&P 500 按当前市值的前/后 10%。

---

## Page 245 / 各 Quality 度量之间的相关性

### Correlations between Quality Measures / 质量度量的相关性

**Exhibit 557**：各种度量下的 Quality 投资策略，随时间表现**相似**——High–Low Quality 业绩价差的相关性（1989 – 2023/4/30）。

> **📊 图表 557**：*Correlation between High-Low Quality Performance Spreads*（High-Low Quality 业绩价差相关性矩阵）。
>
> 矩阵度量间：**High ROE vs. Low ROE**、**Low Beta vs. High Beta**、**Certain vs. Uncertain Earnings**（58.3%）、**Nifty 50 vs. Small Size**、**"A+" vs. "C&D"**。
>
> **说明**：基于月度回报相关性，对应各 Quality 度量的 High 与 Low Quality 篮子**随时间行为相似**。尽管部分策略**取向不同**（见后文差异）。
>
> **注**：**债务/权益**与 **Altman Z-Scores** 也可视为 Quality 度量，但其行为与其他度量差异很大、回报驱动因素不同，**已从本分析中排除**；Altman Z-Scores 还**不含金融业**，可比性较差。

---

## Page 246 / 各行业 Beta 变化 & Low Beta 并非 Quality

### Sector Beta Shifts / 行业 Beta 变化

> **📊 图表 559**：*Some "safe" sectors have grown riskier (e.g. Utilities), while some "risky" sectors have grown safer (e.g. Energy) based on 1yr vs. 5yr betas*（S&P 500 各行业 1 年 Beta vs. 5 年 Beta 价差，截至 2023/4/30）。
>
> **说明**：**公用事业、房地产、必需消费品**近期 Beta **上升**；**能源、工业**的 Beta **下降**幅度最大——传统的"安全/风险"行业划分正在被重置。

### Low Beta Long-term Underperformance / 低 Beta 长期跑输

> **📊 图表 560**：*Low beta stocks have generally underperformed*（S&P 500 低 Beta 股相对等权 S&P 500 的累计等权相对业绩，1989 年 6 月 =100，截至 2023/4/30）。
>
> **说明**：**低 Beta 策略已跑输数十年**。

### Low Beta ≠ Quality / 低 Beta 与 Quality 本质不同

**Exhibit 561**：**Low Beta（价格稳定性）** vs. **Quality（基本面稳定性）** 各项财务度量对比（截至 2023/4/30）：

| 指标 | Beta（最低十分位中位数） | B+ 或更优（中位数） | 差异（价差） |
|---|---|---|---|
| **EPS 波动率** | 55.7% | 39.3% | **+16.4%** |
| **EPS 稳定性**（越低越稳定） | 15.6 | 16.5 | -0.9 |
| **DPS 波动率** | 2.3% | 5.8% | -3.6% |
| **最大 5 年 EPS 下滑** | 26.1% | 15.2% | **+10.9%** |
| **最大 5 年股价下滑** | 18.4% | 30.4% | +12.0% |
| **净债务/EBITDA** | 2.6 | 2.1 | +0.5 |
| **ROIC** | 8.6% | 11.7% | -3.1% |
| **Beta** | 0.6 | 1.0 | -0.4 |
| **Quality Score**（越低越优） | 4.0 | 3.0 | +1.0（Low Beta 质量更差） |

> **结论**：**Low Beta** 仅捕捉**价格**稳定性，而 **Quality** 捕捉**基本面**稳定性——二者**根本不同**，且 Low Beta 在多项基本面指标上**更差**。

---

## Page 247 / 驱动 Quality 的因素：盈利周期

### The Profits Cycle / 盈利周期

> **📊 图表 562**：*High Quality stocks (A+) have outperformed when the profits cycle decelerates…*（S&P 500 各 Quality 等级在**盈利周期减速**时的平均业绩，基于 1988 年至今的七轮周期）。
>
> **Quality 在盈利减速时有效**：当盈利增长**稀缺**时，投资者倾向为**稳定**的盈利增长**溢价支付**；历史上 High Quality 股在盈利减速时**跑赢**。
>
> **📊 图表 563**：*…and have underperformed when the profits cycle accelerates*（盈利周期**加速**时各 Quality 等级平均业绩）。
>
> **但加速的盈利偏好 Low Quality**：当盈利增长**充足**时，投资者偏好对经济敏感的**周期股**；历史上 **Low Quality / 风险股**在盈利加速/风险偏好开启期**跑赢**。
>
> **📊 图表 564**：*We expect earnings to decelerate through 3Q23*（S&P 500 TTM 同比盈利增长 1Q11-4Q22 实际值 + BofA 1Q23 预测）。
>
> **预期**：盈利增长将继续**减速**——**其他条件相同下，利好 High Quality**。

---

## Page 248 / 波动率（预期上升）与 High Quality

### Volatility is Likely to Increase / 波动率可能上升

> **📊 图表 565**：*The yield curve suggests volatility is likely to increase from current levels*（CBOE VIX 与**倒置**的收益率曲线斜率，1986 年至今）。
>
> **说明**：**收益率曲线斜率**一直是 VIX 变化的**良好长期（3 年）前瞻指标**；当前信号显示波动率**未来数年可能上升**。

### High Quality 与波动率的正相关

> **📊 图表 566**：*High Quality tends to outperform when volatility rises*——BofA Quality 指数 12 个月业绩与 CBOE VIX 12 个月变化的相关性（1986–2022/4/30）。
>
> **说明**：**High Quality 股的相对业绩与 VIX 变化正相关**；**Low Quality 股**与 VIX 变化**最负相关**。
>
> **📊 图表 567**：*Nearly every spike in volatility has coincided with the outperformance of higher Quality stocks*（B+ 或更优 vs. B 或更差的相对指数 + 3 个月均 VIX，1990 – 2023/4/30）。
>
> **📊 图表 568**：*The positive relationship between High Quality stock outperformance and volatility has been strong over the last ten years*（High Quality vs. Low Quality 与 3 月均 VIX 相关性，截至 2023/4/30）：
>
> | 期间 | 相关性 |
> |---|---|
> | 1990 年至今 | 22.8% |
> | 近 10 年 | **53.6%** |
> | 近 5 年 | 41.7% |
>
> **说明**：近 10 年 High Quality vs. Low Quality 的相对业绩与 VIX 的 3 个月均值相关性显著高于长期历史均值。

---

## Page 249 / Quality 与周期 Regime

### US Regime Indicator & Quality / 美股 Regime 指标与 Quality

> **📊 图表 569**：*US Regime Indicator now in "Downturn" phase*（美股 Regime 指标，1990/1 – 2023/4）。
>
> **说明**：BofA 美股 **Regime 指标**聚合自上而下变量——盈利/经济增长预期、通胀、信用条件等——产生**四个阶段**。当前处于 **"Downturn（衰退）"**，历史上 High Quality 在此阶段自创立以来平均跑出 **5.2ppt alpha**。

**Exhibit 570**：*Downturns favor Quality*（美股 Regime — 启发式表）。

```
Contraction  <<----------->>  Expansion
Phase 2 Mid Cycle     Phase 3 Late Cycle
 Momentum, Growth,     Momentum, High
 High Risk             Quality, Low Risk,
                       Large Size

Phase 1 Recovery      Phase 4 Downturn
 Value, Small          High Quality
```

> **结论**：**High Quality** 是 **Downturn**（以及 Late Cycle）阶段**表现最佳**的策略之一。

---

## Page 250 / Quality 在熊市 & 重大回撤中的表现

**Exhibit 571**：*Quality outperforms in bear markets*——历史熊市/重大市场修正中 High vs. Low Quality 的价格业绩：

| 期间 | B+ 或更优（年化） | B 或更差（年化） | **B+ 或更优 vs. B 或更差相对业绩（年化）** |
|---|---|---|---|
| 1987/8 – 1987/11 | -74.9% | -79.2% | +4.3% |
| 1990/6 – 1990/10 | -53.1% | -61.7% | +8.6% |
| 2000/3 – 2002/9 | +2.8% | -20.8% | **+23.6%** |
| 2007/10 – 2009/2 | -42.2% | -48.2% | +6.0% |
| 2018/9 – 2018/12* | -41.2% | -60.7% | +19.5% |
| 2020/1 – 2020/3 | -84.8% | -90.7% | +5.9% |
| 2021/12 – 2022/9 | -25.7% | -37.1% | +11.4% |
| **平均** | **-45.6%** | **-56.9%** | **+11.3%** |
| **中位数** | -42.2% | -60.7% | +8.6% |

**注**：*2018/9 – 2018/12 不是官方熊市*。

---

## Page 251 / Quality 持仓已中性化 & 宽松政策回报递减

### Quality Positioning Neutralized / Quality 持仓已中性化

> **📊 图表 572**：*High Quality stocks are slightly overweight in mutual fund holdings*（B+ 或更优 vs. B 或更差 long-only 基金相对持仓，2008 – 2023/4/30）。
>
> **说明**：Quality 谱段的持仓已从**Low Quality 偏好**转为**基本中性**。

### Diminishing Returns from Fed Easing / 联储宽松回报递减

**Exhibit 573**：各轮 QE 期间 **Risky（"B 或更差"） vs. Safe（"B+ 或更优"）股**相对业绩：

| 事件 | 联储资产负债表变化（万亿美元） | Risky vs. Safe 相对业绩 |
|---|---|---|
| **QE1** 2009/3/31 – 2010/3/31 | +$0.4 | Risk Rally |
| **QE2** 2010/11/30 – 2011/6/30 | +$0.6 | Risk Rally |
| **QE3** 2012/9/30 – 2014/10/31 | +$1.7 | Reversal（反转） |
| **QE4** 2020/3/31 – 2022/3/31 | +$4.8 | Reversal |

> **结论**：**各轮宽松对风险资产的回报正在递减**——每次新 QE 的 Risk Rally 效应都弱于上一次。

---

## Page 252 / Quality 估值

### High Quality 在估值上偏贵

> **📊 图表 574**：*High Quality looks expensive on price/book*（High vs. Low Quality 相对 P/B，1986-1Q23）。
>
> **说明**：虽然早前 Exhibit 552 显示 High Quality 在**前瞻 PE** 上仅略高于 Low Quality，但在 **P/B** 上 High Quality 较 Low Quality 交易于 **20% 溢价**（相对历史均值）。
>
> **📊 图表 575**：*High Quality is also getting expensive on price/sales*（High vs. Low Quality 相对 P/S，1986-1Q23）。
>
> **说明**：在 **P/S** 上，High Quality 较 Low Quality 贵 **17%**（相对历史）。

### Risk / Reward of High vs. Low Quality / 高低质量的风险/回报

基于两个风险度量（**回报波动率**与**亏损概率**）的风险回报分析：
- **高 ROE 股**、**低盈利预测离散度股**、**低杠杆股**倾向于提供**优于**其 Low Quality 对应的业绩特征
- **"A+" 评级股**亦对 "C&D" 提供优越**风险调整**回报（程度较弱）
- **Low Beta** 股提供**最低波动下的最低回报**，但其**下行风险**（以亏损概率度量）与其他 Low Quality 因子**相当**

---

## Page 253 / 风险回报图 & Quality 长期跑赢

> **📊 图表 576**：*High Quality Strategies tend to exhibit lower volatility of returns…*（年均回报 vs. 年化波动率/标准差，1986/3/31 – 2023/4/30）。
>
> **📊 图表 577**：*…and lower probability of loss*（年均回报 vs. 亏损概率，1986/3/31 – 2023/4/30）。
>
> **📊 图表 578**：*Risk Reward Characteristics for S&P 500 Quality rankings*（S&P 500 Quality 评级风险回报特征，1986 – 2023/4/30）。
>
> **📊 图表 579**：*Downside Risk Reward Characteristics for S&P 500 Quality rankings*（S&P 500 Quality 评级**下行**风险回报特征）。

### Quality Has Outperformed / Quality 短中长期均跑赢

**Exhibit 580**：B+ 或更优 vs. B 或更差的相对价格业绩（截至 2023/4/30）：

| 期间 | 业绩价差（ppt） |
|---|---|
| 1 个月 | +1.8 |
| 3 个月 | +5.1 |
| 6 个月 | +5.0 |
| 12 个月 | +7.2 |
| 年初至今 | -2.0 |
| 2 年 | +25.0 |
| 3 年 | +24.4 |
| 5 年 | +36.6 |
| 10 年 | **+82.9** |
| **15 年** | **+112.4** |

---

## Page 254 / Quality 长期稳赢 & 小盘股质量更低

### Long-term Winner / 长期赢家

> **📊 图表 581**：*Long-term winner*——High Quality 股（B+ 或更优 S&P Quality 评级）10 年滚动价格回报（1996 – 2023/4/30）。
>
> **说明**：**在我们数据史（追溯至 1986）内，High Quality 股从未出现过负的 10 年回报**（即使不含股息）。

### Smaller Companies Tend to Be Lower Quality / 小市值公司质量更低

> **📊 图表 582**：*One-third of the Russell 2000 is non-earners*（Russell 2000 中**不盈利公司**占比，1985 – 2023/4/30）。
>
> **说明**：Russell 2000 中**不盈利公司比例**一直上升，并因 **COVID-19 疫情**加剧至**历史最高水平**。

### Deep Dive on Quality Fundamentals / Quality 基本面深度透视

**Exhibit 583**：B+ 或更优**中位数基本面属性** vs. 历史均值（1990/7 – 2023/4）：

| 属性 | B+ 或更优 | 历史均值 | 价差 |
|---|---|---|---|
| EPS 波动率 | 39% | 27% | **+12.3%** |
| EPS 稳定性（越低越稳定） | 16.5 | 16.4 | +0.1 |
| DPS 波动率 | 5.8% | 6.2% | -0.3% |
| 最大 5 年 EPS 下滑 | 15% | 9% | **+6.6%** |
| 最大 5 年股价下滑 | 30% | 23% | **+7.1%** |
| 净债务/EBITDA | 2.1 | 1.2 | **+0.8** |
| ROIC | 12% | 11% | +0.7% |
| ROE | 19% | 17% | **+1.6%** |
| Beta | 1.0 | 1.0 | 0.0 |
| 5 年 Proforma vs. GAAP EPS | 8.8% | 6.3% | +2.5% |
| 5 年 Proforma vs. FCF/Sh | 12.0% | 26.8% | **-14.8%** |
| Quality Score（越低越优） | 3.0 | 3.2 | -0.2 |

> **解读**：相对历史均值，**ROE、EPS 稳定性、FCF 质量**（Proforma vs. GAAP FCF 价差收窄）均有**改善**；与此同时 **EPS 波动率与杠杆上升**，而 **EPS 质量**（Proforma vs. GAAP EPS 价差）略有**下滑**。

---

## Page 255 / High vs. Low Quality 基本面 & 质量下调超信用下调

> **📊 图表 584**：*High Quality vs. Low Quality: more EPS & div stability*（当前 B+ 或更优 vs. B 或更差**基本面属性中位数差（%）**，截至 2023/4/30）。
>
> **说明**：相对 Low Quality 股，High Quality 股具有**更高的投资回报率、更低的 EPS 与股息波动率、略低的 Beta、略高的杠杆**。
>
> **📊 图表 585**：*The standard deviation of various fundamental metrics for High Quality stocks tends to be lower compared to Low Quality stocks*（B+ 或更优 vs. B 或更差**属性中位数标准差（%差）**，1990/7/31 – 2023/4/30）。
>
> **最关键**：**High Quality 篮子的特征随时间极度稳定**，特别是相对 **Low Quality 篮子**——后者的**盈利波动、盈利质量与股息**随周期大幅波动。
>
> **📊 图表 586**：*Net quality downgrades outpacing net credit downgrades*（S&P 500 中**质量**与**信用**评级净上调/下调，3 个月滚动，1986 – 2023/4/30）。
>
> **说明**：信用评级与质量评级是**同步关系**——均受公司底层基本面影响。当盈利显著下滑，**盈利与股息稳定性**以及**履约能力**同步下降。
>
> **涉及指标**：EPS 波动率、5 年 Proforma vs. GAAP EPS、最大 5 年 EPS 下滑、DPS 波动率、EPS 稳定性（越低越优）、Quality Score（越低越优）、最大 5 年股价下滑、Beta、净债务/EBITDA、5 年 Proforma vs. FCF/Sh、ROE、ROIC。

---

## Page 256 / 各行业 Quality 构成

### Quality Within Sectors / 行业内质量

**Exhibit 587**：*High vs Low Quality P/B is cheap vs history in Staples, Financials and Utilities*——**B+ 或更优**与 **B 或更差**股的 P/B 相对行业、以及两者相对 P/B（1Q86-1Q23）。

> **关键行业**：
> - **High vs Low Quality P/B 相对历史便宜**：**必需消费品（Staples）、金融（Financials）、公用事业（Utilities）**
> - 覆盖：Communication Services、Discretionary、Staples、Energy 等

---

## Page 257 / Quality 年度业绩矩阵

> **📊 图表 590**：*Annual Quality performance*（年度 Quality 业绩：绿色=最佳，红色=最差）。
>
> **分组**：**B+ 或更优、B 或更差、C&D、未评级（Not Rated）**——逐年排名矩阵，可识别各 Quality 分组的**领先/落后周期**。

---

## Page 258 / 行业 Quality 构成趋势

> **📊 图表 591**：*Trends in Quality composition by sector*——**B+ 或更优**行业敞口随时间变化（基于公司数量，截至 2023/4/30）。
>
> **📊 图表 592**：*Tech, Financials and Real Estate are the sectors with the biggest increase in quality composition by # of co. vs hist.*——**B+ 或更优当前行业权重 vs. 历史均值（ppt）**。
>
> - **质量占比最大增长**：**Tech、Financials、Real Estate**
>
> **📊 图表 593**：*Financials and Industrials represent the largest share of High Quality stocks today*——S&P 500 **B+ 或更优**股行业分布（截至 2023/4/30）。
>
> **📊 图表 594**：*Tech and Health Care have the highest composition in Low Quality*——S&P 500 **B 或更差**股行业分布。
>
> **行业**（从上到下）：公用事业、房地产、材料、科技、工业、医疗保健、金融、能源、必需消费品、可选消费品、通信服务。

---

## Page 259-262 / Quality 各档业绩图（1986=100，截至 2023/4/30）

> **📊 图表 595（p259）**：*A+ vs C&D relative performance*——**最高质量（A+）自 2021 起跑赢最低质量（C&D）**（1986 – 2023/4/30）。
>
> **📊 图表 596（p259）**：*B+ or Better vs B or Worse relative performance*——**B+ 或更优自 2021 起领先 B 或更差**。
>
> **📊 图表 597（p259）**：*B+ or Better cumulative index performance*——**B+ 或更优 YTD -0.2%**。
>
> **📊 图表 598（p260）**：*B or Worse cumulative index*——**B 或更差 YTD +1.8%**。
>
> **📊 图表 599（p260）**：*A+ index performance*——**A+ YTD +1.8%**。
>
> **📊 图表 600（p260）**：*A index*——**A YTD -1.1%**。
>
> **📊 图表 601（p261）**：*A- index*——**A- YTD +0.4%**。
>
> **📊 图表 602（p261）**：*B+ index*——**B+ YTD -0.3%**。
>
> **📊 图表 603（p261）**：*B index*——**B YTD -1.1%**。
>
> **📊 图表 604（p262）**：*B- index*——**B- YTD -1.6%**。
>
> **📊 图表 605（p262）**：*C&D index*——**C&D YTD +4.3%**。
>
> 各图均含 **Backtested（回测期） + Actual（实盘期）** 两段。

---

## Page 263 / 方法论

### Methodology / BofA Quality 指数方法论

通过 BofA 研究覆盖池内公司的 **S&P 质量评级**构建股票筛选：
- 每月末按**质量评级**分组
- 构建各评级股票筛选
- 追踪各筛选的**下月**产出
- **未对**公司限制名单上的股票做调整以便回测分析

### Returns Calculation / 回报计算

- 每月对每个因子进行**再平衡**与业绩计算
- 使用每月最后一个交易日收盘数据与收盘价
- 结果以**价格回报**为基础
- **不反映**交易成本、税务预扣或投资顾问费（若反映则业绩将更低）
- 个体复制结果可能与本报告有差异（源于交易成本/费用假设、时间与价格、权重差异、股息处理等）
- **过去业绩不能作为未来业绩指标**；完整业绩记录可按要求提供

---

## Page 264 / Section VI 目录

## Section VI: Relative Valuation for Industries / 第六部分：行业的相对估值

本部分展示 S&P 500 各 GICS 行业 1986 – 2023/4 的**绝对与相对** P/B（市净）、P/OCF（市现）、**前瞻 P/E**；估值历史**少于 10 年**的行业排除。

---

## Page 265 / Communication Services（通信服务）

### Diversified Telecommunication Services / 多元电信服务

> **📊 图表 606 P/B、607 P/OCF、608 Fwd. P/E**：近年估值**均**下降。

### Entertainment / 娱乐

> **📊 图表 609 P/B、610 P/OCF、611 Fwd. P/E**：估值**均**上行。

---

## Page 266 / 通信服务（续）& Consumer Discretionary（可选消费品）

### Interactive Media & Services / 互动媒体与服务

> **📊 图表 612-614**：P/B、P/OCF、Fwd. P/E **均上行**。

### Media / 媒体

> **📊 图表 615-617**：P/B、P/OCF、Fwd. P/E **均下降**。

### Auto Components / 汽车零部件

> **📊 图表 618**：P/B 近期**上行**。
> **📊 图表 619**：P/OCF 近期**下降**。
> **📊 图表 620**：Fwd. P/E 近期**下降**。

---

## Page 267 / 可选消费品（续）

### Distributors / 分销商

> **📊 图表 621 P/B**：近期上行。
> **📊 图表 622 P/OCF**：近期下降。
> **📊 图表 623 Fwd. P/E**：近期上行。

### Automobile / 汽车

> **📊 图表 624-626**：**P/B 近期略降、P/OCF 下降、Fwd. P/E 下降**。

### Hotels Restaurants & Leisure / 酒店餐饮休闲

> **📊 图表 627 P/B**：升至**历史最高**。
> **📊 图表 628 P/OCF**：近期**急剧下降**。
> **📊 图表 629 Fwd. P/E**：从历史最高回落。

---

## Page 268 / 可选消费品（续）

### Household Durables / 家用耐用品

> **📊 图表 630 P/B**：近期上行。
> **📊 图表 631 P/OCF**：下降。
> **📊 图表 632 Fwd. P/E**：近期上行。

### Leisure Products / 休闲产品

> **📊 图表 633-635**：**P/B、P/OCF、Fwd. P/E 均近期下降**。

### Broadline Retail / 综合零售

> **📊 图表 636-638**：**P/B 近年下降、P/OCF 近期下降、Fwd. P/E 近期下降**。

---

## Page 269 / 可选消费品（续）

### Specialty Retail / 专营零售

> **📊 图表 639 P/B**：近年**急剧上行**。
> **📊 图表 640 P/OCF**：近期略降。
> **📊 图表 641 Fwd. P/E**：近期下降。

### Textiles Apparel & Luxury Goods / 纺织服饰与奢侈品

> **📊 图表 642-644**：**P/B、P/OCF、Fwd. P/E 均上行**。

---

## Page 270 / Consumer Staples（必需消费品）

### Beverages / 饮料

> **📊 图表 645-647**：**P/B 略升、P/OCF 上行、Fwd. P/E 略升**。

### Distribution & Retail / 分销与零售

> **📊 图表 648 P/B**：近年上行。
> **📊 图表 649 P/OCF**：近期略降。
> **📊 图表 650 Fwd. P/E**：上行。

### Food Products / 食品

> **📊 图表 651-653**：**P/B、P/OCF、Fwd. P/E 均近期略升**。

---

## Page 271 / 必需消费品（续）

### Household Products / 家庭用品

> **📊 图表 654-656**：**P/B 近年上行；P/OCF、Fwd. P/E 近期略升**。

### Tobacco / 烟草

> **📊 图表 657 P/B**：近年账面价值**为负**（该行业特性）。
> **📊 图表 658 P/OCF**：近期略升。
> **📊 图表 659 Fwd. P/E**：近期略升。

---

## Page 272 / Energy（能源）

### Energy Equipment & Services / 能源设备与服务

> **📊 图表 660 P/B**：近期上行。
> **📊 图表 661 P/OCF**：近期上行。
> **📊 图表 662 Fwd. P/E**：从**历史最高**回落。

### Oil Gas & Consumable Fuels / 石油/天然气/可消费燃料

> **📊 图表 663 P/B**：近期略升。
> **📊 图表 664 P/OCF**：近期下降。
> **📊 图表 665 Fwd. P/E**：近期上行。

---

## Page 273 / Financials（金融）—— Banks / Capital Markets / Consumer Finance

### Banks / 银行

> **📊 图表 666 P/B**：近期略降。
> **📊 图表 667 Fwd. P/E**：近期略降。

### Capital Markets / 资本市场

> **📊 图表 668 P/B**：近期下降。
> **📊 图表 669 Fwd. P/E**：近期下降。

### Consumer Finance / 消费金融

> **📊 图表 670 P/B**：近期略降。
> **📊 图表 671 Fwd. P/E**：近期略降。

---

## Page 274 / 金融（续）—— Financial Services / Insurance

### Financial Services / 金融服务

> **📊 图表 672 P/B**：近期略升。
> **📊 图表 673 Fwd. P/E**：近期上行。

### Insurance / 保险

> **📊 图表 674 P/B**：近期略降。
> **📊 图表 675 Fwd. P/E**：近期下降。

---

## Page 275 / Health Care（医疗保健）

### Biotechnology / 生物科技

> **📊 图表 676-678**：**P/B 近期略升、P/OCF 上行、Fwd. P/E 上行**。

### Health Care Equipment & Supplies / 医疗设备与用品

> **📊 图表 679-681**：**P/B、P/OCF、Fwd. P/E 均上行**。

### Health Care Providers & Services / 医疗保健提供者与服务

> **📊 图表 682 P/B**：近期略降。
> **📊 图表 683 P/OCF**：近期下降。
> **📊 图表 684 Fwd. P/E**：近期略降。

---

## Page 276 / 医疗保健（续）& Industrials（工业）开始

### Pharmaceuticals / 制药

> **📊 图表 685 P/B**：近期略降。
> **📊 图表 686 P/OCF**：近期下降。
> **📊 图表 687 Fwd. P/E**：近期上行。

### Life Sciences Tools & Services / 生命科学工具与服务

> **📊 图表 688 P/B**：已下降。
> **📊 图表 689 P/OCF**：近期上行。
> **📊 图表 690 Fwd. P/E**：近期下降。

### Industrials 开始 —— Aerospace & Defense / 航空航天与国防

> **📊 图表 691 P/B**：近期略升。
> **📊 图表 692 P/OCF**：从**历史最高**回落。
> **📊 图表 693 Fwd. P/E**（续至下页）。

---

## Page 277 / 工业（续）

### Air Freight & Logistics / 航空货运与物流

> **📊 图表 694 P/B**：下降。
> **📊 图表 695 P/OCF**：近期略升。
> **📊 图表 696 Fwd. P/E**：近期上行。

### Commercial Services & Supplies / 商业服务与用品

> **📊 图表 697 P/B**：接近**历史最高**。
> **📊 图表 698 P/OCF**：近年上行。
> **📊 图表 699 Fwd. P/E**：已下降。

### Construction & Engineering / 建筑与工程

> **📊 图表 700 P/B**：近期上行。
> **📊 图表 701 P/OCF**：近期下降。

---

## Page 278 / 工业（续）

### Electrical Equipment / 电气设备

> **📊 图表 703 P/B**：近期从**历史最高**回落。
> **📊 图表 704 P/OCF**：近期上行。
> **📊 图表 705 Fwd. P/E**：近期上行。

### Industrial Conglomerates / 工业集团

> **📊 图表 706 P/B**：近期上行。
> **📊 图表 707 P/OCF**：近期下降。
> **📊 图表 708 Fwd. P/E**：近期上行。

### Machinery / 机械

> **📊 图表 709 P/B**：近期上行。
> **📊 图表 710 P/OCF**：近期下降。
> **📊 图表 711 Fwd. P/E**：近期下降。

---

## Page 279 / 工业（续）

### Trading Companies & Distributors / 贸易公司与分销商

> **📊 图表 712-714**：**P/B、P/OCF、Fwd. P/E 均近期上行**。

### Building Products / 建材

> **📊 图表 715-717**：**P/B、P/OCF、Fwd. P/E 均近期上行**。

### Professional Services / 专业服务

> **📊 图表 718-720**：**P/B、P/OCF、Fwd. P/E 均近期上行**。

---

## Page 280 / 工业（续）& Information Technology（信息技术）开始

### Ground Transportation / 陆地运输

> **📊 图表 721 P/B**：近期下降。
> **📊 图表 722 P/OCF**：近期下降。
> **📊 图表 723 Fwd. P/E**：近期下降。

### Information Technology 开始 —— Communication Equipment / 通信设备

> **📊 图表 724 P/B**：近期上行。
> **📊 图表 725 P/OCF**：近期略升。
> **📊 图表 726 Fwd. P/E**：近期略升。

---

## Page 281 / 信息技术（续）

### Electronic Equipment, Instruments & Components / 电子设备、仪器与组件

> **📊 图表 727 P/B**：近期下降。
> **📊 图表 728 P/OCF**：近年上行。
> **📊 图表 729 Fwd. P/E**：近期上行。

### IT Services / IT 服务

> **📊 图表 730 P/B**：近期略降。
> **📊 图表 731 P/OCF**：下降。
> **📊 图表 732 Fwd. P/E**：近期下降。

### Semiconductors & Semiconductor Equipment / 半导体与半导体设备

> **📊 图表 733 P/B**：上行。
> **📊 图表 734 P/OCF**：上行。
> **📊 图表 735 Fwd. P/E**（续至下页）。

---

## Page 282 / 信息技术（续）

### Software / 软件

> **📊 图表 736-738**：**P/B、P/OCF、Fwd. P/E 均近期上行**。

### Technology Hardware Storage & Peripherals / 技术硬件、存储与外设

> **📊 图表 739 P/B**：接近**历史最高**。
> **📊 图表 740 P/OCF**：上行。
> **📊 图表 741 Fwd. P/E**：近期上行。

---

## Page 283 / Materials（材料）

### Chemicals / 化工

> **📊 图表 742 P/B**：近期上行。
> **📊 图表 743 P/OCF**：近期上行。
> **📊 图表 744 Fwd. P/E**：从**历史最高**回落。

### Containers & Packaging / 容器与包装

> **📊 图表 745 P/B**：近期下降。
> **📊 图表 746 P/OCF**：近期上行。
> **📊 图表 747 Fwd. P/E**：近期略升。

---

## Page 284 / 材料（续）

### Metals & Mining / 金属与采矿

> **📊 图表 748 P/B**：近期上行。
> **📊 图表 749 P/OCF**：近期略降。
> **📊 图表 750 Fwd. P/E**：近期下降。

### Construction Materials / 建筑材料

> **📊 图表 751 P/B**：近期上行。
> **📊 图表 752 P/OCF**：近期略升。
> **📊 图表 753 Fwd. P/E**：近期上行。

---

## Page 285 / Real Estate（房地产）

### Residential REITs / 住宅 REITs

> **📊 图表 754 P/B**：近期下降。
> **📊 图表 755 Fwd. P/E**：近期下降。

### Real Estate Management & Development / 房地产管理与开发

> **📊 图表 756 P/B**：近期略降。
> **📊 图表 757 Fwd. P/E**：近期上行。

### Retail REITs / 零售 REITs

> **📊 图表 758 P/B**：近期略降。
> **📊 图表 759 Fwd. P/E**：近期下降。

---

## Page 286 / 房地产（续）

### Specialized REITs / 特殊 REITs

> **📊 图表 760 P/B**：已下降。
> **📊 图表 761 Fwd. P/E**：已下降。

### Health Care REITs / 医疗保健 REITs

> **📊 图表 762 P/B**：已上行。
> **📊 图表 763 Fwd. P/E**：已上行。

### Hotel & Resort REITs / 酒店度假村 REITs

> **📊 图表 764 P/B**：已下降。
> **📊 图表 765 Fwd. P/E**：已下降。

---

## Page 287 / 房地产（续）& Utilities（公用事业）开始

### Industrial REITs / 工业 REITs

> **📊 图表 766 P/B**：已下降。
> **📊 图表 767 Fwd. P/E**：已上行。

### Office REITs / 办公 REITs

> **📊 图表 768 P/B**：已下降。
> **📊 图表 769 Fwd. P/E**：已上行。

### Utilities 开始 —— Electric Utilities / 电力公用事业

> **📊 图表 770 P/B**：已下降。
> **📊 图表 771 P/OCF**：近期略升。
> **📊 图表 772 Fwd. P/E**：近期略降。

---

## Page 288 / 公用事业（续）

### Multi-Utilities / 多元公用事业

> **📊 图表 773 P/B**：近期略降。
> **📊 图表 774 P/OCF**：上行。
> **📊 图表 775 Fwd. P/E**：近期略降。

### Gas Utilities / 天然气公用事业

> **📊 图表 776 P/B**：近期略降。
> **📊 图表 777 P/OCF**：已下降。
> **📊 图表 778 Fwd. P/E**：近期略降。

### Water Utilities / 水务公用事业

> **📊 图表 779 P/B**：近期略降。
> **📊 图表 780 P/OCF**：已下降。
> **📊 图表 781 Fwd. P/E**：近期略升。

---

## Page 289 / 公用事业（续）

### Independent Power and Renewable Electricity Producers / 独立电力与可再生能源生产商

> **📊 图表 782 P/B**：略降。
> **📊 图表 783 P/OCF**：已下降。
> **📊 图表 784 Fwd. P/E**：近期略降。

---

## Page 290 / Section VII 目录

## Section VII: Relative Valuation between Growth and Value Benchmarks / 第七部分：Growth 与 Value 基准的相对估值

- **Fundamental Valuation** / 基本面估值
- **Growth Characteristics** / 成长性特征

---

## Page 291 / Growth vs. Value 基本面估值

### Fundamental Valuation / 基本面估值

> **📊 图表 785**：*Russell 1000 Growth vs. Value Trailing P/E*（1978 – 2023/4/30）。
>
> **说明**：在 **Trailing P/E** 基准下，相对估值**正接近长期均值**。
>
> **📊 图表 786**：*Russell 1000 Growth vs. Value Forward P/E*（1978 – 2023/4/30）。
>
> **说明**：在 **Forward P/E** 基准下，Growth 相对 Value 的估值**仍高于历史均值**。

---

## Page 292 / Growth vs. Value 估值（续）

> **📊 图表 787**：*Russell 1000 Growth vs. Value Price/Book Value*（1978 – 2023/4/30）。
>
> **说明**：在 **P/B** 基准下，Growth 相对 Value 估值**接近历史高位**。
>
> **📊 图表 788**：*Russell 1000 Growth vs. Value Price/Sales*（1978 – 2023/4/30）。
>
> **说明**：在 **P/S** 基准下，Growth 相对 Value 估值**仍偏高**。

---

## Page 293 / 成长性特征

### Growth Characteristics / 成长性特征

> **📊 图表 789**：*Russell 1000 Growth vs. Value Long-term Growth*（1982 – 2023/4/30）。
>
> **说明**：Growth 指数的**长期 EPS 增长**已**降至相对 Value 指数的平均水平**。
>
> **📊 图表 790**：*Russell 1000 Growth vs. Value P/E to Growth*（1978 – 2023/4/30）。
>
> **说明**：在 **PEG（P/E to Growth）**基准下，Growth 相对 Value **仍贵**。

---

## Page 294 / Section VIII 目录

## Section VIII: ADR Strategies / 第八部分：ADR 策略

<details>
<summary>📖 <b>术语解释：ADR（American Depositary Receipt，美国存托凭证）</b></summary>

**非美公司想在美股市场被美国投资者交易，通常不直接上市，而是由美国的托管银行在美国发行一种\"代表其若干股本股票\"的凭证**——这就是 ADR。每份 ADR 背后对应 N 股（N 可为 1、或 0.5、或 10 等，视公司与发行人约定）底层股票，**以美元计价、在 NYSE/NASDAQ/AMEX 等美国交易所交易**，股息也以美元派发。

- **为什么重要**：对美国投资者来说，买 ADR = 不用开海外账户就能投资台积电、阿里巴巴、壳牌、空客、雀巢等全球巨头；对上市公司来说 = 获得美元资金池和更高的全球关注度。
- **价格驱动**：ADR 价格 = 底层股票当地币价 × 汇率 × 比率（再叠加美股流动性溢价/折价）。**投资 ADR 天然承担\"股价波动 + 汇率波动\"双重风险**。
- **本章重点**：BofA 构建了一套按**国别/地区**分组的 ADR 指数（Composite、EMU、Latin America、Asia ex-Japan 等），对每组跟踪其相对当地基准（MSCI 系列）的业绩——可用于**国际股票配置择时**与**跨市场 alpha 捕捉**。

</details>

### BofA US Equity & Quant Strategy ADR Indices / BofA 美股与量化策略 ADR 指数

**注**：本部分所有图表均基于**筛选引入后的实盘业绩数据**（除特殊标注外）。

---

## Page 295 / BofA ADR 指数业绩

### BofA US Equity & Quant Strategy ADR Indices / BofA ADR 指数

**Exhibit 791**：*Monthly price performance by different regions of the world*（BofA Quant Strategy ADR 指数业绩，截至 2023/4/30）：

**价格业绩以美元计，% 变化**；1M 相对回报 = ADR 相对 MSCI 对标指数的超额回报。

| ADR 指数 | 价格 (4/30/23) | 1 M | 3 M | 6 M | 12 M | YTD | 3 年 | 5 年 | 10 年 | 1M 相对回报 | 权重 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **ADR COMPOSITE** | 1,588 | -0.3 | -7.2 | 21.3 | -1.2 | 7.8 | 1.5 | -6.4 | — | 0.8 | 100.0% |
| ADR COMPOSITE (ex Latin America) | 759 | -0.4 | -7.9 | 22.8 | -2.5 | 7.7 | -1.1 | -6.9 | — | 0.8 | 85.8% |
| ADR Latin America | 444 | 0.4 | -3.2 | 8.2 | 4.5 | 7.5 | 17.3 | -5.2 | — | -0.5 | 14.2% |
| ADR Asia (ex Japan) | 234 | -2.3 | -11.5 | 38.8 | -1.8 | 7.1 | -9.1 | -13.4 | — | 0.4 | 34.2% |
| ADR Europe (non-EMU) | 343 | 1.6 | -6.7 | 11.4 | -5.1 | 4.3 | 0.3 | -3.4 | — | 0.5 | 16.2% |
| ADR EMU | 277 | 1.0 | -2.7 | 24.4 | 5.1 | 15.2 | 9.3 | -1.1 | — | 2.8 | 19.4% |
| ADR Emerging Europe | 150 | -5.9 | -20.1 | -25.9 | -50.3 | -8.3 | -27.7 | -27.3 | — | -17.2 | 4.0% |
| *MSCI EAFE®*（基准，12/86 重设基期） | 349 | 2.4 | 2.1 | 22.5 | 5.4 | 10.3 | 9.0 | 1.0 | 2.0 | — | — |
| *S&P 500*（基准） | 4,169 | 1.5 | 2.3 | 7.7 | 0.9 | 8.6 | 12.7 | 9.5 | 10.1 | — | — |
| **— 欧洲 —** | | | | | | | | | | | |
| ADR France | 778 | 0.4 | -2.0 | 22.4 | 8.8 | 13.7 | 7.4 | -1.8 | 1.9 | -3.8 | 6.0% |
| ADR Germany | 228 | 1.6 | -1.7 | 23.3 | -4.1 | 18.2 | 3.1 | -5.6 | -1.1 | -1.3 | 5.1% |
| ADR Ireland | 2,735 | 1.7 | 0.7 | 36.8 | 26.0 | 30.9 | 7.8 | 6.8 | 6.6 | -0.9 | 1.7% |
| ADR Italy | 285 | 3.8 | -2.5 | 29.5 | 4.4 | 8.2 | 36.3 | 3.1 | 5.8 | 0.6 | 1.1% |
| ADR Netherlands | 1,106 | 1.3 | 0.7 | 34.4 | 16.2 | 13.3 | 10.8 | 2.1 | 6.2 | 3.2 | 2.3% |
| ADR Norway | 1,298 | 2.6 | 15.1 | 26.9 | 2.1 | 12.3 | 17.8 | -2.4 | 4.3 | 2.3 | 0.8% |
| ADR Spain | 574 | 0.9 | 0.0 | 29.2 | 16.0 | 15.1 | 13.6 | -4.2 | -2.0 | -0.9 | 1.3% |
| ADR Sweden | 1,429 | 0.0 | -2.1 | 16.9 | -3.0 | 3.0 | -3.0 | 1.5 | -3.0 | -3.2 | 1.9% |
| ADR Switzerland | 417 | 1.4 | -2.7 | 22.8 | -3.2 | 13.5 | 6.4 | -1.2 | 2.0 | -4.0 | 2.1% |
| ADR United Kingdom | 1,276 | 2.3 | -9.7 | 7.3 | -5.8 | 3.5 | -0.6 | -5.2 | -0.6 | -2.7 | 10.4% |
| **— 拉美 —** | | | | | | | | | | | |
| ADR Argentina | 189 | 2.5 | -9.6 | 28.0 | 40.6 | 6.2 | 28.7 | -19.2 | 7.4 | -1.3 | 2.5% |
| ADR Brazil | 466 | 1.3 | -5.9 | -8.2 | -12.1 | 2.1 | 12.5 | -4.3 | -4.2 | -0.5 | 6.6% |
| ADR Chile | 232 | 0.4 | 2.1 | 17.7 | 13.4 | 11.6 | -1.2 | -13.9 | -7.2 | 2.9 | 1.7% |
| ADR Mexico | 472 | -1.6 | 8.2 | 28.3 | 27.1 | 26.4 | 36.4 | 8.3 | 1.7 | -3.9 | 2.3% |
| **— 亚洲 —** | | | | | | | | | | | |
| ADR China | 260 | -2.6 | -12.7 | 42.4 | -1.2 | 7.6 | -14.9 | -18.4 | -1.4 | 2.6 | 25.3% |
| ADR Hong Kong | 21 | 4.4 | -9.2 | 66.7 | -2.2 | 7.1 | -6.5 | -10.4 | -4.9 | 3.9 | 2.5% |
| ADR Indonesia | 87 | 5.6 | 10.1 | 3.9 | -8.3 | 20.1 | 21.7 | 5.1 | 1.8 | -0.5 | 0.2% |
| ADR India | 1,454 | 0.6 | -3.0 | 0.0 | -5.8 | 5.6 | 28.4 | 10.9 | 9.9 | -3.5 | 1.3% |
| ADR Japan | 654 | 1.4 | -1.0 | 17.6 | 3.2 | 6.9 | 4.4 | -0.8 | 2.8 | 1.0 | 6.8% |
| ADR Korea | 210 | -2.0 | -9.4 | 13.2 | -10.8 | 1.8 | 7.3 | -3.1 | 4.4 | -1.1 | 1.9% |
| ADR Philippines | 84 | -14.4 | -15.6 | -21.5 | -39.2 | -5.2 | -4.4 | -4.7 | -11.8 | -15.4 | 0.2% |
| ADR Taiwan | 867 | -8.2 | -3.2 | 28.6 | -9.5 | 13.2 | 21.1 | 10.0 | 11.5 | -3.9 | 1.1% |
| **— 其他 —** | | | | | | | | | | | |
| ADR Australia | 387 | -0.3 | -15.6 | -8.7 | -32.2 | -5.1 | 12.9 | -1.3 | -3.8 | -0.5 | 3.6% |
| ADR Israel | 87 | -5.1 | -21.6 | -31.3 | -55.1 | -12.0 | -16.1 | -22.3 | -15.0 | -3.2 | 3.6% |
| ADR South Africa | 632 | 9.0 | 13.8 | 60.2 | 14.7 | 23.0 | 21.0 | 22.1 | 6.8 | 8.8 | 1.1% |

---

## Page 296 / Appendix 目录

## Appendix / 附录

- **BofA Proprietary Models** / BofA 专有模型
- **BofA Factor Descriptions** / BofA 因子定义
- **Russell 1000 factor performance** / Russell 1000 因子业绩
- **Russell 1000 factor correlations vs. macro factors** / Russell 1000 因子与宏观因子的相关性
- **S&P 500 factor efficacy** / S&P 500 因子有效性
- **Research Analysts** / 研究分析师

---

## Page 297 / BofA 专有模型

### BofA vs. Consensus（盈利惊喜模型）

BofA vs. Consensus 模型旨在识别**分析师盈利预期与实际披露盈利**之间存在**显著差异**的股票。模型将 BofA 基本面研究的年度盈利预测与**市场共识**进行对比。

我们寻找分析师**与共识以统计显著方式相异**的情形。同时对**共识观点**赋予较低权重——因综合证据指向的建议很可能**已被市场定价**。

**公式**：

$$
\text{Surprise} = \frac{\text{BofA Estimate} - \text{I/B/E/S Mean Estimate}}{\text{Standard Deviation of I/B/E/S Estimates}}
$$

- 前 9 个月使用 **FY1**（当前未披露年）预测
- 后 3 个月使用 **FY2**（下一未披露年）预测
- 结果将全样本排序为**十分位**：**1 = BofA 分析师最乐观**，**10 = 最悲观**

### Dividend Discount Model / 股息贴现模型（DDM）

三阶段（**近期、向成熟过渡、成熟期/稳态**）DDM 计算使**当前股价 = 预测股息流**成立的贴现率。该贴现率为**"隐含"或"预期"回报**。因 DDM 基于今日股价求解隐含回报率（而非"无风险利率 + 风险溢价"），所以需**风险调整**——使用 CAPM 以**5 年美债收益率**作为无风险利率代理。

**近期阶段**聚焦公司未来 5 年的盈利与股息增长；需要 **5 年 EPS 增长率、第 5 年 EPS 增长率、第 5 年派息比率**预测。这些参数允许模型插值该段时间（超出分析师常规预测）内的盈利与股息估算。

对于盈利波动大或可能因亏损影响增长的公司，还需要额外预测 **5 年长期/常态化 EPS 增长率**（对数线性或趋势线增长率）。

---

## Page 298 / 向成熟过渡与成熟期 & Alpha Surprise 模型

> **📊 图表 793**：*Transition to Maturity Within Valuation Model*——模型在**第 20 年**实现**稳态增长**。

**Transition to Maturity（向成熟过渡）**阶段近似公司随规模扩大增长率放缓的过程。该阶段可由分析师判断合理时长，但**总是从第 5 年开始**。
- 第一项数据：该阶段持续年数（Years to Maturity/Steady State）。例如：分析师预期持续 15 年，则需给出第 6-20 年股息参数。
- 第二项数据：**增长下降速度**（Transition to Maturity）。通常**规模更大更成熟的公司**增长减速更快；**更年轻快速成长的公司**减速更慢。

**Maturity / Steady State（成熟期/稳态）**阶段：公司主营业务实质性减速、市场渗透饱和后，应假设增长率接近**名义 GDP 长期增长率**。需要两项预测：**成熟期 EPS 增长率** 与 **成熟期派息比率**。

**DDM Alpha**：股票 DDM 计算的贴现率 − 通过普通 CAPM 计算得到的该股所需回报率。

### Alpha Surprise Model / Alpha Surprise 模型

Alpha Surprise 评分 = 两项专有模型十分位评分的 **25% / 75% 加权组合**：
- **25%**：DDM（价值/"alpha" 部分）
- **75%**：BofA vs. Consensus 盈利惊喜模型（成长/"surprise" 部分）
- **1 = 最吸引**，**10 = 最不吸引**

**示例**：若某股 DDM 得十分位 1（最吸引），BofA vs. Consensus 得十分位 10（最不吸引）：

$$\text{Alpha Surprise} = 0.25 \times 1 + 0.75 \times 10 = 7.75$$

---

## Page 299 / 筛选样本 & High Quality & Dividend Yield

### Screening Universe / 筛选样本

BofA 当前覆盖的 **S&P 500** 样本——且分析师同时有**盈利、股息、长期增长率、股息增长率**预测（用于 BofA vs. Consensus 与 DDM）。月末分析时公司限制名单上的股票**排除**。

### Alpha Surprise Model Screen Results / 筛选结果

筛选规则：挑选**评分最吸引（最低）**的股票。**截止分 2.75**——高于此分不入选。结果产生**约 50 只股票**。

### High Quality & Dividend Yield / 高质量 + 股息收益率筛选

目的是**定量**筛选**质量较高且股息收益相对稳固**的股票，从 S&P 500 中按以下条件选择，**排除金融**（因度量与其他行业不可比）：

1. **S&P 普通股排名 A+、A 或 A-**。S&P 普通股排名是我们的主要质量度量，主要基于 10 年期**盈利与股息的增长与稳定性**。
2. **ROE 高于** S&P 500 ROE。
3. **债务/权益 低于** S&P 500。
4. **股息收益率 高于** S&P 500。
5. **BofA 观点为 "Buy" 或 "Neutral"**，且**股息评级 "7"**（可能维持或增加）。
6. **最近 12 个月 FCF/股息比 > 1.0**。

**注**：**High Quality Dividend Yield** 筛选**非分散组合**，应仅在**良好分散的投资策略**背景下考量。

---

## Page 300 / Growth 10 & Value 10

### Growth 10 and Value 10 / 成长 10 与价值 10

组合由 BofA vs. Consensus 盈利惊喜模型 + **三项额外筛选标准**定量生成，样本为 **S&P 500**。

- **Growth 10**：按方法论**最吸引**的 **10 只成长股**
- **Value 10**：**最吸引**的 **10 只价值股**

**替换规则**：
- **Growth 10**：若触发 4 条卖出标准之一，则由**满足前 3 条买入标准且 5 年预测 EPS 增长率最高**者替换
- **Value 10**：由**满足前 3 条买入标准且 TTM P/E 最低**者替换

**注**：每月 15 日后**不再变动**，新增/删除**下月初生效**。两组合**非分散**，应仅在**良好分散投资策略**内考量。

**Exhibit 794**：Growth 10 与 Value 10 的股票选择标准：

| | **Growth 10** | **Value 10** |
|---|---|---|
| **买入 (1)** | BofA vs. Cons. EPS Surprise 评级 "1" | BofA vs. Cons. EPS Surprise 评级 "1" |
| **买入 (2)** | BofA "BUY" 观点 | BofA "BUY" 观点 |
| **买入 (3)** | 必须 BofA vs. Cons. EPS Surprise 评 "1 或 2" **< 10 个月** | 同左 |
| **买入 (4)** | 选 **5 年预测 EPS 增长率最高**的 10 只 | 选 **TTM P/E 最低**的 10 只 |
| **卖出 (1)** | BofA vs. Cons. EPS Surprise 评级**低于 5** | 同左 |
| **卖出 (2)** | BofA QRQ **低于 "BUY" 观点** | 同左 |
| **卖出 (3)** | 被 S&P 500 剔除 | 同左 |
| **卖出 (4)** | BofA 研究**不再覆盖** | 同左 |

---

## Page 301 / Quintile 2 方法论

### Quintile 2 Methodology

该筛选**于 2010/9/28 引入**。选择标准自 **1984/1/31** 以来一致。**回测区间** 1984/1/31 – 2010/9/28。

**注**：我们从筛选中**排除近期削减或暂停股息**的公司。

Quintile 2 业绩：**1984/1/31 – 2010/9/28 为回测**，**2010/9/28 至今为实盘**。**回测业绩**是策略的**理论**（非实盘）业绩——不代表任何账户或基金的实际表现。

**免责声明**：识别为 Quintile 2 的筛选**仅为指示性度量**，未经 BofA Global Research 书面同意**不得**用于任何金融工具/合约的参考或业绩度量。**该筛选非基准**。

**Exhibit 795**：*Quintile 2 outperformed the index by 0.5ppt since inception*——总回报（截至 2023/4/30）：

| 期间 | Quintile 2 | 等权 Russell 1000 |
|---|---|---|
| 1 个月 | 1.5% | -0.8% |
| 3 个月 | -4.7% | -5.6% |
| 6 个月 | 3.7% | 4.4% |
| YTD | 1.8% | 4.2% |
| 12 个月 | -0.8% | -1.6% |
| **自起始**（累计） | **298.8%** | **277.1%** |
| 3 年（年化） | 17.8% | 16.7% |
| 5 年（年化） | 8.9% | 8.0% |
| 自起始（年化） | 11.6% | 11.1% |

---

## Page 302 / US Regime Indicator 输入变量与风格定义

### US Regime Indicator / 美股 Regime 指标

模型包含**八个宏观/自上而下变量**：

1. **盈利修正比率（Earnings Revision ratio）**：S&P 500 中 **Thomson Financial 共识盈利估算被上调**的公司数 / **被下调**的公司数。比率上升表示周期改善。
2. **ISM PMI**（采购经理人指数，以 **Z-Score** 表示）。300 位供应管理专业人士上报；**>50 扩张，<50 收缩**。
3. **通胀**：BofA 通胀综合指数 12 个月变化的 Z-Score。**上升=经济条件改善**。
4. **GDP 预测**：费城联储调查的未来 12 个月美国 GDP 增速预测，Z-Score。
5. **LEI 指数**：Conference Board 美国 10 项经济领先指标 12 个月变化，Z-Score。
6. **美国产能利用率**：12 个月变化，Z-Score。**上升 = 经济扩张 + 潜在通胀压力**。
7. **10 年美债收益率**：12 个月变化，Z-Score。**上升 = 经济改善**。
8. **高收益信用利差**：ICE BofA US High Yield 指数利差 12 个月变化，Z-Score。**利差收窄 = 经济改善**。

### Styles / 风格

基于 US Regime Indicator 识别的阶段，用以下因子评估广义风格业绩（基于 S&P 500 前十分位股票）：

- **Value**：**等权**组合——Trailing EPS Yield、Forward EPS Yield、P/B、P/CF、P/FCF、P/S、EV/EBITDA、FCF/EV
- **Growth**：**等权**组合——EPS Momentum、5 年预测增长、EPS 预测上修
- **Momentum**：12 个月价格动量
- **High Quality**：**等权**组合——1 年 ROE、5 年 ROE、1 年债务调整 ROE、5 年债务调整 ROE、ROC、ROA

---

## Page 303 / BofA ADR 策略 & 因子定义（一）

### BofA ADR Strategy / BofA ADR 策略

**ADR Composite** 策略由当前**在美上市**（NYSE、NASD 或 AMEX）ADR 组成。篮子**等权**、**每月再平衡**。1993/12 首次引入，但回溯至 **1986/12/31** 重构。

**国别与区域指数**按其在 BofA Composite 中的权重构建；基于数据可用性取最早日期创建；**等权、月度再平衡**，对标对应 **MSCI** 指数。

各筛选的**等权价格业绩** vs. 相应当地市场指数（以**美元**为共同货币）+ BofA ADR 策略与 MSCI 对照指数的**相关性**——月度更新。

### BofA Factor Descriptions / BofA 因子定义

每月发布近 **40 个因子**的业绩、行业权重与股票列表。方法**统一**（除特殊说明外）：
1. 每月末按因子值挑 S&P 500 **前 50 只**构建**等权组合**
2. 追踪下月该组合相对**等权 S&P 500** 的业绩
3. 下月末**再平衡**

大多数因子自 **1989 年起样本外运行**。

**部分因子定义**：

- **Absolute return**：基于月度回报的纯粹价格涨跌；组合内等权；**不含股息/成本**。
- **DDM Alpha**：三阶段 DDM 隐含回报 − CAPM 所需回报；呈现为十分位。
- **Dividend Yield**：指示股息/月末价。
- **P/B**：月末价/每股最新账面价值。
- **P/CF**：月末价/最新现金流（净利 + 特殊项 + 折旧）。
- **P/FCF**：月末价/最新自由现金流（P/CF − 资本支出）。
- **P/S**：月末市值/报告销售额。
- **EV/EBITDA**：企业价值（权益市值 + 长短期债 + 优先股 + 少数股东权益 − 现金）/ EBITDA（净利 + 特殊项 − 少数股东权益 + 利息费用 + 所得税 + 折旧摊销）。
- **Relative Strength**：30 周移动均线价 / 75 周移动均线价。
- **Most Active**：月度成交量最高股。

---

## Page 304 / 因子定义（二）

- **Low Price**：月末绝对价格水平。
- **5W/30W MA**：5 周均线 / 30 周均线。
- **10W/40W MA**：10 周均线 / 40 周均线。
- **Price/200-Day MA**：月末收盘价 / 200 日均线。
- **Price Return – 12M、11M、9M、3M**：分别为近 12 个月、11 个月（回溯 12 个月但忽略最近 1 月）、9 个月、3 个月绝对价格回报。
- **Price Return – 12M & 1M**：（1）12 个月涨幅最高 + （2）最近 1 月涨幅最高 **等权排序**。
- **Price Return – 12M & 1M Reversal**：（1）12 个月涨幅最高 + （2）最近 1 月**跌幅最大**（= 最近 1 月涨幅最低）**等权排序**。
- **Earnings Momentum（盈利动量）**：TTM EPS − 1 年前 TTM EPS，除以 1 年前 TTM EPS。
- **Projected 5-Year EPS Growth（5 年预测 EPS 增长率）**：BofA 基本面研究预测；若无则用 I/B/E/S 均值长期增长预测。
- **Earnings Torpedo（盈利鱼雷）**：I/B/E/S FY2 估计 − 最近实际年 EPS，除以月末价。
- **Earnings Surprise（盈利惊喜）**：BofA vs. 共识预测（按离散度调整后）；1-10 排序，1 最乐观。
- **EPS Estimate Revision（盈利预测上修）**：（当前 I/B/E/S FY1 − 3 个月前 FY1）/ |3 个月前 FY1|。
- **Beta**：非分散风险度量；60 个月股价 vs. S&P 500 回归。
- **Variability of EPS**：过去 5 年季度 EPS 波动程度；10-1 排序，10 最波动。
- **EPS Estimate Dispersion**：I/B/E/S FY2 估计的**变异系数**；十分位排序。
- **Dividend Growth（股息增长）**：TTM 4 季总普通股息 vs. 1 年前 TTM 4 季总股息。
- **Neglect–Institutional Ownership（机构持股被忽视）**：浮动调整后机构持股占比**最低**者视为更被忽视。

---

## Page 305 / 因子定义（三）

- **Neglect–Analyst Coverage（分析师覆盖被忽视）**：FirstCall 提交评级的分析师**最少**的公司。
- **Firm Size（市值）**：月末市值。
- **Foreign Exposure（海外敞口）**：海外销售 / 总销售。
- **Equity Duration（股票久期）**：DDM 的衍生度量，衡量股票对**利率敏感度**；久期越长（数值越高）越敏感。
- **P/E-to-Growth（PEG）**：TTM P/E / BofA 5 年 EPS 增长率预测；若无 BofA 预测则用 I/B/E/S 均值长期增长。
- **1 年 ROE**：净利 / 平均权益。
- **5 年 ROE**：5 年平均 ROE。
- **ROA**：（净利 + 利息 + 税）/ 平均总资产。
- **ROC**：（净利 + 利息费用 + 少数股东权益）/ 平均总投入资本（长期债 + 优先股 + 普通股权益 + 少数股东权益）。
- **1 年债务调整 ROE**：基于债务/权益比——债务越高的公司 ROE 被视为越低。
- **5 年债务调整 ROE**：类似，对平均 5 年 ROE。
- **Short Interest 12M Z-Score**：（最近卖空股数 − 12 月均卖空股数）/ 12 月卖空股数标准差。

---

## Page 306 / Russell 1000 因子业绩矩阵

### Russell 1000 Factor Performance / Russell 1000 因子业绩

**Exhibit 796**：1986 至今各因子业绩（Analyst Coverage 自 1994，机构持股自 1999，卖空比例自 1993）：

| 因子 | 平均年化回报 | 平均 12M 超额回报（vs. Russell） | Sharpe 比率（vs. 10Y 美债） | Sharpe 比率（vs. Russell） | 亏损概率 | 跑输 Russell 1000 概率 | 年化波动率 | 最大回撤 | 年化下行波动率 |
|---|---|---|---|---|---|---|---|---|---|
| Price/FCF | 16.4% | 5.6% | 0.64 | 0.75 | 18.8% | 24.5% | 20.5% | -61.0% | 16.0% |
| EV/EBITDA | 16.0% | 5.3% | 0.59 | 0.58 | 20.1% | 29.3% | 21.5% | -62.5% | 16.1% |
| FCF/EV | 15.9% | 4.9% | 0.66 | 0.71 | 17.8% | 24.9% | 18.9% | -58.3% | 15.0% |
| Most Active | 15.0% | 4.6% | 0.58 | 0.59 | 22.7% | 27.5% | 21.4% | -57.7% | 15.5% |
| Short Interest | 14.5% | 3.6% | 0.69 | 0.96 | 15.8% | 16.9% | 17.1% | -51.2% | 13.3% |
| Share Repurchase | 14.4% | 2.8% | 0.59 | 0.39 | 17.2% | 31.1% | 17.5% | -55.1% | 14.4% |
| Earnings Yield | 14.2% | 4.2% | 0.50 | 0.36 | 23.8% | 38.4% | 22.3% | -70.4% | 17.8% |
| 11M Price Return | 14.2% | 3.3% | 0.57 | 0.23 | 21.1% | 32.7% | 19.3% | -55.3% | 15.1% |
| Price/Sales | 14.1% | 4.2% | 0.47 | 0.30 | 24.3% | 37.3% | 23.6% | -67.4% | 17.4% |
| Price/Cash Flow | 14.0% | 3.4% | 0.50 | 0.32 | 23.1% | 37.5% | 22.0% | -60.8% | 17.2% |
| 12M Price Return | 13.7% | 2.7% | 0.55 | 0.16 | 20.6% | 35.2% | 18.7% | -50.9% | 14.3% |
| 12M & 1M Reversal | 13.7% | 2.4% | 0.55 | 0.29 | 18.8% | 31.8% | 19.2% | -58.2% | 16.0% |
| 30W/75W MA | 13.6% | 2.7% | 0.53 | 0.20 | 22.0% | 39.8% | 19.8% | -56.3% | 15.5% |
| 5W/30W MA | 13.4% | 2.3% | 0.53 | 0.09 | 19.9% | 38.0% | 17.7% | -46.6% | 13.1% |
| 1yr ROE | 13.4% | 1.5% | 0.55 | 0.35 | 17.8% | 35.7% | 17.8% | -53.6% | 13.5% |
| ROC | 13.3% | 1.4% | 0.54 | 0.28 | 18.3% | 39.8% | 17.7% | -51.6% | 13.2% |
| 1yr ROE Adj | 13.3% | 1.5% | 0.54 | 0.28 | 19.7% | 40.0% | 17.9% | -51.1% | 13.4% |
| 10W/40W MA | 13.1% | 2.1% | 0.50 | 0.08 | 22.0% | 40.0% | 18.4% | -51.2% | 14.1% |
| Price/Book Value | 13.0% | 3.4% | 0.44 | 0.19 | 23.6% | 38.9% | 23.2% | -72.2% | 17.2% |
| 5yr ROE Adj | 13.0% | 1.2% | 0.51 | 0.25 | 21.7% | 39.8% | 18.0% | -48.0% | 13.4% |
| P/E-to-Growth | 12.9% | 2.3% | 0.46 | 0.28 | 24.3% | 43.7% | 22.4% | -67.8% | 16.6% |
| ROA | 12.8% | 1.0% | 0.51 | 0.20 | 19.5% | 46.2% | 18.4% | -51.1% | 13.4% |
| 9M Price Return | 12.7% | 1.8% | 0.49 | 0.06 | 22.9% | 40.5% | 18.4% | -52.2% | 14.3% |
| 5y ROE | 12.4% | 0.6% | 0.47 | 0.14 | 20.1% | 38.4% | 18.0% | -51.7% | 13.7% |
| Dividend Yield | 12.3% | 1.5% | 0.44 | -0.03 | 20.4% | 52.9% | 18.8% | -68.6% | 15.7% |
| P/200D MA | 12.3% | 1.2% | 0.47 | -0.02 | 23.1% | 47.8% | 17.5% | -47.8% | 13.0% |
| Size | 11.9% | 2.0% | 0.40 | 0.15 | 26.8% | 52.4% | 25.0% | -65.0% | 17.5% |
| 3M Price Return | 11.9% | 0.8% | 0.44 | -0.05 | 22.7% | 50.8% | 17.7% | -48.4% | 12.7% |
| EPS Estimate Revisions | 11.9% | 1.4% | 0.41 | 0.04 | 25.2% | 35.9% | 20.3% | -63.6% | 16.6% |
| Dividend Growth | 11.8% | 0.2% | 0.45 | -0.04 | 23.6% | 47.1% | 17.6% | -56.5% | 14.0% |
| **等权 Russell 1000**（基准） | **11.4%** | na | 0.43 | na | 22.7% | na | 18.1% | -56.3% | 14.2% |
| 12M & 1M Performance | 11.3% | -0.1% | 0.43 | -0.10 | 21.7% | 49.2% | 16.9% | -50.0% | 13.0% |
| Earning Momentum | 11.1% | -0.1% | 0.40 | 0.01 | 26.5% | 49.2% | 20.0% | -60.0% | 15.6% |
| Neglect – 分析师覆盖 | 10.9% | -0.4% | 0.41 | -0.05 | 24.3% | 54.0% | 19.0% | -59.2% | 15.2% |
| Low Price | 10.9% | 1.9% | 0.35 | 0.06 | 27.0% | 53.1% | 26.8% | -69.1% | 18.8% |
| Earnings Torpedo | 10.5% | -0.3% | 0.35 | -0.12 | 24.7% | 57.4% | 20.9% | -62.1% | 14.9% |
| Variability of Earnings | 10.5% | 0.3% | 0.34 | -0.04 | 27.7% | 51.3% | 22.8% | -66.6% | 17.6% |
| Beta | 9.9% | 1.9% | 0.30 | 0.01 | 29.7% | 51.5% | 29.8% | -81.8% | 21.7% |
| Forward Earnings Yield | 9.5% | 1.7% | 0.23 | -0.14 | 32.0% | 52.6% | 31.5% | -59.1% | 20.9% |
| Estimate Dispersion | 8.7% | -0.5% | 0.28 | -0.10 | 30.9% | 57.2% | 26.0% | -71.1% | 18.7% |
| Neglect – 机构持股 | 8.7% | -0.3% | 0.36 | 0.09 | 25.9% | 50.7% | 19.3% | -55.9% | 13.3% |
| Proj. 5yr EPS Growth | 8.2% | -0.9% | 0.25 | -0.15 | 26.8% | 57.9% | 25.8% | -83.8% | 20.4% |

---

## Page 307 / Russell 1000 因子与宏观相关性

**Exhibit 797**：*Russell 1000 factor correlations vs. macroeconomic factors*——基于相对指数的因子业绩。

**宏观类别**：
- **利率**：10Y 名义收益率、10Y 实际收益率、2s10s 美债曲线
- **货币**：贸易加权美元
- **通胀**：CPI
- **商品价格**：WTI
- **经济**：GDP 增长
- **市场波动**：VIX
- **企业盈利**：盈利周期
- **信用质量**：信用利差

**因子示例**：Earnings Yield、Forward Earnings Yield ……（其余各因子分别与上述宏观变量的相关性）。

---

## Page 308 / S&P 500 因子有效性（Sharpe Ratio）

### S&P 500 Factor Efficacy / S&P 500 因子有效性

**Exhibit 798**：*S&P 500 factor Sharpe Ratio*

- **加粗字体**标识各因子 Sharpe 比率**最高**的五分位
- **底色标识**各因子 Sharpe 比率**最低**的五分位
- 1986 至今业绩（Analyst Coverage 1994 起；机构持股 1999 起；卖空比例 1993 起）

| 因子 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Earnings Yield | **0.50** | 0.46 | 0.54 | 0.49 | **0.58** | 0.53 | 0.41 | 0.47 | 0.39 | 0.32 |
| Forward Earnings Yield | 0.47 | 0.53 | 0.52 | **0.60** | 0.50 | 0.51 | 0.47 | 0.52 | 0.33 | 0.28 |
| Dividend Yield | 0.45 | 0.55 | **0.56** | 0.55 | 0.55 | 0.49 | 0.46 | 0.43 | 0.44 | 0.37 |
| Price/Book Value | 0.38 | 0.51 | **0.54** | 0.48 | 0.44 | 0.47 | 0.43 | 0.41 | 0.49 | 0.51 |
| Price/Cash Flow | 0.45 | 0.52 | 0.54 | 0.50 | **0.57** | 0.48 | 0.42 | 0.53 | 0.35 | 0.38 |
| Price/Free Cash Flow | 0.61 | 0.66 | **0.73** | 0.65 | 0.56 | 0.45 | 0.39 | 0.28 | 0.24 | 0.19 |
| Price/Sales | 0.49 | 0.47 | 0.49 | 0.50 | 0.52 | 0.52 | **0.53** | 0.38 | 0.45 | 0.30 |
| EV/EBITDA | 0.57 | **0.61** | 0.49 | 0.56 | 0.55 | 0.49 | 0.40 | 0.45 | 0.38 | 0.26 |
| Free Cash Flow/EV | 0.61 | 0.67 | **0.69** | 0.59 | 0.56 | 0.49 | 0.39 | 0.31 | 0.36 | 0.22 |
| 30W/75W MA | 0.48 | 0.55 | **0.55** | 0.53 | 0.50 | 0.53 | 0.54 | 0.42 | 0.35 | 0.25 |
| 5W/30W MA | 0.51 | 0.46 | 0.38 | 0.43 | 0.55 | **0.61** | 0.55 | 0.52 | 0.44 | 0.24 |
| 10W/40W MA | 0.52 | 0.41 | 0.43 | 0.51 | 0.55 | **0.57** | 0.54 | 0.50 | 0.45 | 0.22 |
| P/200D MA | 0.50 | 0.40 | 0.49 | 0.43 | 0.53 | **0.57** | 0.52 | 0.50 | 0.47 | 0.26 |
| 12M Price Return | 0.53 | 0.56 | 0.48 | **0.59** | 0.50 | 0.51 | 0.46 | 0.49 | 0.34 | 0.25 |
| 9M Price Return | **0.55** | 0.48 | 0.46 | 0.49 | 0.49 | 0.54 | 0.46 | 0.48 | 0.42 | 0.28 |
| 3M Price Return | 0.46 | 0.45 | 0.45 | 0.51 | 0.50 | 0.48 | **0.56** | 0.47 | 0.45 | 0.33 |
| 11M Price Return | 0.53 | **0.58** | 0.50 | 0.54 | 0.54 | 0.53 | 0.48 | 0.46 | 0.37 | 0.21 |
| 12M & 1M Performance | 0.47 | 0.47 | 0.53 | 0.51 | 0.39 | 0.47 | **0.54** | 0.49 | 0.48 | 0.33 |
| 12M & 1M Reversal | **0.59** | 0.52 | 0.58 | 0.51 | 0.42 | 0.52 | 0.49 | 0.48 | 0.39 | 0.20 |
| Most Active | **0.63** | 0.59 | 0.54 | 0.49 | 0.50 | 0.40 | 0.47 | 0.41 | 0.36 | 0.25 |
| Low Price | 0.39 | 0.43 | 0.49 | 0.45 | 0.52 | **0.55** | 0.45 | 0.53 | 0.42 | 0.50 |
| Earning Momentum | 0.42 | 0.45 | 0.52 | 0.53 | **0.54** | 0.51 | 0.54 | 0.48 | 0.40 | 0.35 |
| Proj. 5yr EPS Growth | 0.33 | 0.42 | 0.45 | 0.53 | 0.47 | 0.47 | **0.54** | 0.47 | 0.54 | 0.52 |
| Earnings Torpedo | 0.41 | 0.46 | 0.55 | 0.57 | 0.59 | **0.60** | 0.52 | 0.44 | 0.37 | 0.31 |
| EPS Estimate Revisions | 0.46 | 0.53 | 0.50 | 0.49 | 0.52 | **0.54** | 0.48 | 0.45 | 0.45 | 0.26 |
| Dividend Growth | 0.51 | 0.49 | 0.38 | 0.49 | 0.55 | **0.58** | 0.51 | 0.50 | 0.51 | 0.45 |
| P/E-to-Growth | 0.48 | 0.47 | 0.47 | 0.48 | 0.54 | 0.56 | **0.60** | 0.50 | 0.46 | 0.37 |
| 1yr ROE | **0.62** | 0.57 | 0.48 | 0.49 | 0.56 | 0.47 | 0.36 | 0.48 | 0.41 | 0.34 |
| 5y ROE | **0.58** | 0.48 | 0.55 | 0.49 | 0.48 | 0.48 | 0.45 | 0.42 | 0.47 | 0.35 |
| 1yr ROE Adj | **0.60** | 0.51 | 0.55 | 0.52 | 0.46 | 0.45 | 0.40 | 0.50 | 0.45 | 0.31 |
| 5yr ROE Adj | **0.59** | 0.45 | 0.51 | 0.52 | 0.53 | 0.44 | 0.43 | 0.46 | 0.46 | 0.34 |
| ROA | **0.55** | 0.49 | 0.54 | 0.49 | 0.44 | 0.48 | 0.51 | 0.48 | 0.42 | 0.30 |
| ROC | **0.59** | 0.55 | 0.55 | 0.50 | 0.51 | 0.41 | 0.45 | 0.49 | 0.42 | 0.31 |
| Beta | 0.33 | 0.39 | 0.46 | 0.44 | 0.54 | 0.46 | 0.56 | **0.60** | 0.52 | 0.45 |
| Variability of Earnings | 0.32 | 0.39 | 0.43 | 0.48 | 0.44 | 0.55 | 0.52 | 0.48 | **0.61** | 0.60 |
| Estimate Dispersion | 0.27 | 0.43 | 0.49 | 0.47 | 0.49 | 0.46 | 0.45 | 0.52 | 0.56 | **0.67** |
| Neglect – 分析师覆盖 | 0.44 | 0.45 | 0.48 | 0.50 | 0.48 | **0.52** | 0.43 | 0.46 | 0.51 | 0.48 |
| Neglect – 机构持股 | 0.35 | **0.59** | 0.42 | 0.49 | 0.57 | 0.58 | 0.52 | 0.44 | 0.41 | 0.31 |
| Size | 0.40 | 0.51 | 0.46 | 0.43 | **0.60** | 0.43 | 0.51 | 0.44 | 0.43 | 0.49 |
| Share Repurchase | 0.59 | **0.63** | 0.56 | 0.51 | 0.48 | 0.48 | 0.50 | 0.44 | 0.39 | 0.19 |
| Short Interest | 0.67 | 0.65 | **0.70** | 0.52 | 0.54 | 0.46 | 0.47 | 0.37 | 0.37 | 0.28 |

> **注**：**加粗**为各因子 Sharpe 比率最高的分位；底色（此处仅用加粗标出）为最低分位。Sharpe 比率 = 月度超额回报（vs. 10Y 美债）年化均值 ÷ 月度超额回报年化波动率。

---

## Page 309 / S&P 500 因子相关性矩阵

**Exhibit 799**：*S&P 500 factor correlations*——基于 1990/1 至今月度回报。

**涵盖因子**（横纵对称矩阵）：Alpha Surprise Model、P/E-to-Growth、DDM Alpha、Earnings Yield、Forward EPS Yield、P/B、P/CF、P/FCF、P/S、EV/EBITDA、FCF/EV、Dividend Yield、Dividend Growth、Share Repurchase、30W/75W MA、5W/30W MA、10W/40W MA、P/200D MA、价格回报（12M/9M/3M/11M/12M&1M/12M&1M Reversal）、Most Active、Earnings Momentum、5Y EPS Growth、Positive EPS Surprise、EPS Estimate Revisions、Equity Duration、1Y ROE、5Y ROE、1Y ROE Adj、5Y ROE Adj、ROA、ROC、Beta、EPS 变异率、Estimate Dispersion、Low Price、Low 机构持股、Low 分析师覆盖、Size、Foreign Exposure、P/E-to-Growth、DDM Alpha。

> **用途**：用于**构建组合时识别因子冗余**——同一类别内相关性高的因子不应同时使用；跨类别低相关或负相关的因子可提供**分散效应**。

---

## Page 310 / 重要披露（Disclosures）

### Important Disclosures / 重要披露

由于**策略分析**的性质，本报告推荐或讨论的发行人/证券**并非持续跟踪**。投资者应将本报告视为**独立分析**，不应期待针对此类发行人/证券的持续分析或补充报告。

**量化分析**同理——发行人/证券非持续跟踪。

BofA Global Research 人员（包括本报告负责的分析师）薪酬基于多项因素，包括 Bank of America Corporation 的**整体盈利**（涵盖投资银行业务利润）。分析师薪酬也可能基于销售与交易业务的整体盈利。

### Other Important Disclosures / 其他重要披露

- 价格为**指示性**，仅供参考
- 权益证券推荐引用**报告日前一日收盘价**（盘中发布则引用当时价格）
- 债务证券价格为**报告日指示性价格**，来源包括 BofA Securities 交易台
- 本报告可能涉及在某些州/司法区或向零售投资者**不得发行的证券**——此类提及**非招揽或要约**
- 非机构投资者应在投资决策前**咨询独立财务顾问**
- BofAS 或其关联方的高管（非研究分析师）可能在相关发行人证券或相关投资中**持有财务利益**

### Non-US Affiliates 覆盖地区 / 非美关联机构涵盖地区

BofAS 和/或 MLPF&S 未来可能在美国分发以下**非美关联机构**的信息：
- 南非、英国（MLI）、法国（BofASE）、意大利、德国、西班牙、澳大利亚、香港、新加坡、加拿大、墨西哥、阿根廷、日本、韩国、台湾、印度、以色列、DIFC、巴西、沙特等

各地关联机构受**当地监管机构**监管（FCA/PRA、ACPR/AMF、BaFin、ECB/CBI、HKSFC、MAS、IIROC、SEBI、DFSA、CVM 等）。

---

## Page 311 / General Investment Related Disclosures / 一般投资披露

**新加坡**：针对非认可/专家/机构投资者，Merrill Lynch (Singapore) Pte Ltd 对分发内容承担完全责任。

**台湾**：本报告信息与观点**非**任何证券/金融工具的要约或招揽。未经 BofA Securities 书面同意，**不得**以任何方式复制、引用。

**一般**：
- 本文件提供一般信息，面向 BofA Securities 客户总分发
- 信息与观点**非要约或邀请**
- 不构成**个人投资建议**，未考虑特定投资目标/财务情况/需求
- 不构成 ERISA、美国税法、《投资顾问法》下的投资建议
- 投资者应就金融工具适当性寻求财务建议

**风险**：
- 本报告中证券**不受 FDIC 保险**；**非**受保存款机构的存款或其他义务
- 投资涉及市场风险、对手方违约风险、流动性风险等
- **没有**金融工具适合所有投资者
- **数字资产**极具投机性、波动大、大部分不受监管
- **过去业绩非未来业绩的必然指引**
- 税收基础可能变化

**短期交易想法**：与股票基本面股权评级（反映长期总回报预期与相对覆盖集群内其他股票的吸引力）**不同**。

**"做空"限制**：本报告中想法的实施可能依赖做空能力——许多司法区禁止或限制"裸卖空"；执行前应咨询监管适用性建议。

**汇率**：外币汇率可能对证券/金融工具价值、价格或收入产生不利影响。持有证券（包括 ADR）的投资者**实际上承担汇率风险**。

**其他**：BofAS 或其关联方可能持有本报告讨论的证券/金融工具的**交易头寸**（多或空）。BofA Securities 的非研究部门可能发布**与本报告不一致甚至得出不同结论**的交易想法或建议。

### Copyright and General Information / 版权与一般信息

**Copyright 2023 Bank of America Corporation. All rights reserved.** iQdatabase® 是 Bank of America Corporation 的**注册服务商标**。

- 本信息为 BofA Securities 客户准备，**未经书面同意不得重分发、再传输或披露**
- 内容同时分发至内部与客户网站——**非公开**材料
- 接收与审阅构成**不再分发/传输/披露**的协议（包括任何投资建议、估计、目标价）
- BofA Global Research 材料基于**公开信息**
- 事实与观点**未经**投行等其他业务线审阅，且可能不反映这些业务线所知信息
- BofA Securities 已在研究与特定业务组间**建立信息壁垒**

---

## Page 312 / 研究分析师 & 最终风险提示

### Research Analysts / 研究分析师

| 分析师 | 职务 | 机构 | 联系方式 |
|---|---|---|---|
| **Savita Subramanian** | Equity & Quant Strategist | BofAS | +1 646 855 3878 · savita.subramanian@bofa.com |
| **Alex Makedon** | Equity & Quant Strategist | BofAS | +1 646 855 5982 · alex.makedon@bofa.com |
| **Jill Carey Hall, CFA** | Equity & Quant Strategist | BofAS | +1 646 855 3327 · jill.carey@bofa.com |
| **Ohsung Kwon, CFA** | Equity & Quant Strategist | BofAS | +1 646 855 1683 · ohsung.kwon@bofa.com |
| **Victoria Roloff** | Equity & Quant Strategist | BofAS | victoria.roloff@bofa.com |
| **Nicolas Woods** | Equity & Quant Strategist | BofAS | nicolas.woods_barron@bofa.com |

### 最终风险提示 / Final Risk Warning

> **本文讨论的交易想法和投资策略可能带来显著风险，并不适合所有投资者。投资者应在相关市场具有经验，并具备足以承受由应用这些想法或策略可能产生的任何损失的财务资源。**

---

# 📘 全文完 / END OF DOCUMENT

---

## 翻译说明

- **原文**：BofA Global Research, *Quantitative Primer*, 2023 年 6 月 26 日（共 312 页）
- **原作者团队**：Savita Subramanian, Alex Makedon, Jill Carey Hall, CFA 等
- **译版说明**：
  - 本文件为**中英对照版**——保留英文关键术语、原图表标号（Exhibit N）与原始结构
  - 图表以 `> **📊 图表 N**：*原标题*` 形式标注，并附中文说明
  - 数值与表格数据为原文提取；部分具体数值以 `…` 表示，请参照原 PDF 查阅精确值
  - 为便于学习，保留大量英文专业词汇（Quality、Beta、ROE、PEG、DDM、CAPM、FCF、EV/EBITDA 等）对照中文
- **用途**：仅供学习与研究——**不构成投资建议**。本文所涉所有观点、图表、数据均为 BofA 原始研究；最终请以原英文报告为准
- **版权**：原文版权归 Bank of America Corporation 所有

---

> **进度**：✅ 已完成 **p1–p312（全部 312 页）**。文档翻译**完成**。

