# A股选股系统

**热点驱动 + 产业链分析 + 多维筛选**

A股选股系统是一款基于模块化Agent架构的自动化选股工具。系统每日自动扫描市场热度最高的板块，分析其上下游产业链关系，在产业链中筛选出技术面/基本面/资金面综合评分最高的股票，并生成Obsidian格式的Markdown报告。

## 核心功能

### 热点驱动
资金流向 + 互联网热度双轮驱动，捕捉有机构布局+舆论发酵的板块。

- 板块资金流向采集（Tushare Pro API）
- 互联网热度数据接入（预留接口）
- 综合评分 = 0.6 x 资金分 + 0.4 x 热度分

### 产业链定位
自动拆解热门板块的上下游关系，在产业链中寻找强势标的。

- 板块成分股获取
- 产业链位置识别（上游/中游/下游）
- 产业地位加权评分

### 综合评分
技术面40% + 基本面30% + 资金面30% 加权评分体系。

| 维度 | 权重 | 评分因素 |
|------|------|----------|
| 技术面 | 40% | 涨跌幅(25%) + 量比(25%) + 趋势(50%) |
| 基本面 | 30% | 业绩增速(40%) + 估值合理度(30%) + 成长性(30%) |
| 资金面 | 30% | 主力净流入(50%) + 筹码集中度(50%) |

### 每日报告
自动生成格式化报告，存入Obsidian便于追踪和二次分析。

---

## 系统架构

### Agent流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    定时触发 (每日收盘后)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DataCollectorAgent                        │
│  - 收集当日板块资金流向 (Tushare)                              │
│  - 收集热度数据 (预留接口)                                     │
│  - 数据写入共享消息队列                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SectorAnalyzerAgent                       │
│  - 消费消息队列数据                                           │
│  - 综合资金+热度评分，输出热门板块Top5                          │
│  - 推送至板块分析消息队列                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ChainAnalyzerAgent                        │
│  - 消费板块分析结果                                           │
│  - 分析板块内个股的产业链位置                                   │
│  - 输出产业链上下游关系                                        │
│  - 推送至选股Agent消息队列                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    StockScreenerAgent                        │
│  - 消费产业链分析结果                                         │
│  - 按技术面40%+基本面30%+资金面30%综合评分                       │
│  - 筛选出强势股Top10                                          │
│  - 推送至报告生成                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ObsidianReportAgent                       │
│  - 消费选股结果                                              │
│  - 生成Markdown报告                                          │
│  - 写入 选股报告/YYYY-MM-DD.md                               │
└─────────────────────────────────────────────────────────────┘
```

### 消息队列

| 队列名 | 生产者 | 消费者 | 数据内容 |
|--------|--------|--------|----------|
| raw_market_data | DataCollector | SectorAnalyzer | 板块资金流向 + 热度原始数据 |
| sector_analysis | SectorAnalyzer | ChainAnalyzer | 热门板块Top5 + 评分详情 |
| chain_analysis | ChainAnalyzer | StockScreener | 产业链上下游关系 + 个股分类 |
| final_stocks | StockScreener | ObsidianReport | 强势股Top10 + 评分详情 |

---

## 安装

### 环境要求

- Python 3.10+
- Tushare Pro API Token

### 安装步骤

1. **克隆项目**

```bash
cd stock_selector
```

2. **创建虚拟环境（推荐）**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件或设置环境变量：

```bash
# Tushare Pro API Token
export TUSHARE_TOKEN="your_tushare_token_here"

# Obsidian Vault路径
export OBSIDIAN_VAULT_PATH="~/Documents/vault"
```

---

## 使用

### 命令行使用

```bash
# 运行今日选股
python main.py

# 指定日期运行
python main.py --date 20240417
```

### Python API使用

```python
from stock_selector.main import run_pipeline

# 运行完整流水线
result = run_pipeline(trade_date="20240417")

if result['success']:
    print(f"完成！耗时: {result['duration_seconds']}秒")
    for agent_result in result['summary']['agent_results']:
        print(f"  - {agent_result['agent']}: {'成功' if agent_result['success'] else '失败'}")
```

### 输出示例

```
Pipeline completed successfully!
Trade date: 20240417
Duration: 12.34s
Agents completed: 5

报告已生成: ~/Documents/vault/选股报告/2024-04-17.md
```

---

## 项目结构

```
stock_selector/
├── main.py                     # 命令行入口脚本
├── requirements.txt            # Python依赖
│
├── stock_selector/              # 主包
│   ├── __init__.py
│   │
│   ├── agents/                  # Agent模块
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Agent基类，定义标准接口
│   │   ├── data_collector.py    # DataCollectorAgent - 数据采集
│   │   ├── sector_analyzer.py   # SectorAnalyzerAgent - 板块分析
│   │   ├── chain_analyzer.py    # ChainAnalyzerAgent - 产业链分析
│   │   ├── stock_screener.py    # StockScreenerAgent - 选股
│   │   └── obsidian_report.py   # ObsidianReportAgent - 报告生成
│   │
│   ├── queue/                   # 消息队列模块
│   │   ├── __init__.py
│   │   └── memory_queue.py      # 内存队列实现（线程安全）
│   │
│   ├── data_sources/            # 数据源模块
│   │   ├── __init__.py
│   │   └── tushare_client.py    # Tushare Pro API封装
│   │
│   ├── scorers/                 # 评分器模块
│   │   ├── __init__.py
│   │   ├── sector_scorer.py     # 板块热度评分
│   │   ├── chain_scorer.py      # 产业链评分
│   │   └── stock_scorer.py      # 个股综合评分
│   │
│   ├── config/                  # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py          # 配置管理（数据类）
│   │
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       └── date_utils.py        # 日期工具函数
│
└── tests/                       # 测试目录
    ├── __init__.py
    ├── test_main.py             # 流水线集成测试
    │
    ├── agents/
    │   ├── test_base_agent.py
    │   ├── test_data_collector.py
    │   ├── test_sector_analyzer.py
    │   ├── test_chain_analyzer.py
    │   ├── test_stock_screener.py
    │   └── test_obsidian_report.py
    │
    ├── config/
    │   └── test_settings.py
    │
    ├── queue/
    │   └── test_memory_queue.py
    │
    ├── data_sources/
    │   └── test_tushare_client.py
    │
    ├── scorers/
    │   ├── test_sector_scorer.py
    │   ├── test_chain_scorer.py
    │   └── test_stock_scorer.py
    │
    └── utils/
        └── test_date_utils.py
```

---

## 配置

### 配置项说明

编辑 `stock_selector/config/settings.py` 或设置环境变量：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `tushare_token` | (内置Token) | Tushare Pro API Token |
| `obsidian_vault_path` | `~/Documents/vault` | Obsidian仓库路径 |
| `top_sectors_count` | `5` | 热门板块数量 |
| `top_stocks_count` | `10` | 入选股票数量 |
| `fund_flow_weight` | `0.6` | 板块资金流向权重 |
| `heat_weight` | `0.4` | 板块热度权重 |
| `tech_weight` | `0.4` | 个股技术面权重 |
| `fundamental_weight` | `0.3` | 个股基本面权重 |
| `money_weight` | `0.3` | 个股资金面权重 |
| `upstream_weight` | `1.2` | 产业链上游权重 |
| `midstream_weight` | `1.0` | 产业链中游权重 |
| `downstream_weight` | `0.8` | 产业链下游权重 |

### 环境变量配置

```bash
export TUSHARE_TOKEN="your_token_here"
export OBSIDIAN_VAULT_PATH="/path/to/vault"
```

---

## 数据流

### 消息队列机制

系统采用内存消息队列实现Agent间的解耦通信：

```
DataCollector  ──put──>  raw_market_data  ──get──>  SectorAnalyzer
SectorAnalyzer ──put──>  sector_analysis  ──get──>  ChainAnalyzer
ChainAnalyzer ──put──>  chain_analysis   ──get──>  StockScreener
StockScreener ──put──>  final_stocks     ──get──>  ObsidianReport
```

每个Agent：
- 从输入队列获取数据（无数据时阻塞等待）
- 处理数据后发送到输出队列
- 支持多生产者多消费者模式

### 数据处理流程

1. **数据采集**: Tushare API获取板块资金流向
2. **板块评分**: 综合资金+热度计算板块评分，输出Top5
3. **产业链分析**: 获取板块成分股，识别产业链位置
4. **个股筛选**: 获取个股行情/基本面/资金面数据，计算综合评分
5. **报告生成**: 生成格式化Markdown报告

---

## 测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定模块测试

```bash
# Agent测试
pytest tests/agents/ -v

# 评分器测试
pytest tests/scorers/ -v

# 队列测试
pytest tests/queue/ -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=stock_selector --cov-report=term-missing
```

### 覆盖率要求

- 分支覆盖率: >= 80%
- 函数覆盖率: >= 80%
- 行覆盖率: >= 80%

---

## 定时任务

### Windows (任务计划程序)

```cmd
schtasks /create /tn "A股选股" /tr "python stock_selector\main.py" /sc daily /st 15:30
```

### Linux/Mac (crontab)

```bash
# 编辑crontab
crontab -e

# 每日15:30执行（工作日）
30 15 * * 1-5 cd /path/to/stock_selector && python main.py >> logs/pipeline.log 2>&1
```

---

## Obsidian报告格式

报告保存在 `{ObsidianVault}/选股报告/YYYY-MM-DD.md`

```markdown
# 选股报告 - 2024-04-17

> 生成时间: 2024-04-17 17:30:00

## 热门板块

| 排名 | 板块名称 | 资金热度 | 互联网热度 | 综合分 |
|:---:|:--------|:--------|:---------|:------:|
| 1 | AI芯片 | 95.2 | 88.5 | 92.5 |
| ... | ... | ... | ... | ... |

## 强势股池

### 综合评分Top10

| 排名 | 股票名称 | 代码 | 综合分 | 技术信号 | 资金信号 |
|:---:|:--------|:-----|:------:|:--------|:--------|
| 1 | XXX股份 | 600000 | 85.5 | 突破 | 主力净流入 |
| ... | ... | ... | ... | ... | ... |

---
> 本报告由自动化选股系统生成，仅供参考，不构成投资建议。
```

---

## 扩展开发

### 添加新的数据源

1. 在 `data_sources/` 创建新的客户端类
2. 实现数据获取接口
3. 在 `DataCollectorAgent` 中集成

### 添加新的评分维度

1. 在 `scorers/` 创建新的评分器类
2. 实现评分逻辑
3. 在对应的Agent中集成

### 切换消息队列实现

当前使用内存队列（开发环境）。生产环境可切换到Redis队列：

1. 实现 `queue/redis_queue.py`
2. 在 `queue/__init__.py` 中导出RedisQueue

---

## 依赖

| 包 | 版本 | 说明 |
|-----|------|------|
| tushare | >=1.4.0 | A股数据接口 |
| pandas | >=2.0.0 | 数据处理 |
| requests | >=2.31.0 | HTTP请求 |
| python-dateutil | >=2.8.0 | 日期处理 |
| pytest | >=8.0.0 | 测试框架 |

---

## License

MIT License

---

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。股票市场有风险，投资需谨慎。系统生成的选股结果仅供参考，不保证收益。
