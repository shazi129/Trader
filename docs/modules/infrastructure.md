# infrastructure 使用说明

`infrastructure` 是跨领域的技术基础设施。目前只提供最小 SQLite 能力。它不知道
什么是 K 线、量化特征或财务字段，也不拥有任何业务表。

```text
infrastructure.sqlite.SQLiteRepository
            ▲
            │ 继承
   ┌────────┼─────────────┐
   │        │             │
行情仓储   特征仓储      财报仓储
```

## 公开接口

```python
from infrastructure.sqlite import SQLiteRepository, default_db_path
```

`default_db_path()` 返回：

```text
<Trader>/database/stock_data.db
```

`SQLiteRepository` 提供：

| 方法 | 作用 |
|---|---|
| `ensure_table(...)` | 创建表、补充新列、创建索引 |
| `upsert(table, row)` | 单行插入或冲突更新 |
| `upsert_many(table, rows)` | 同列集合批量 UPSERT |
| `scalar(sql, params)` | 读取单个标量 |
| `close()` | 提交并关闭连接 |
| context manager | `with` 生命周期管理 |

领域查询应写在各自 Repository 中，不应让工具层直接调用 `cursor`。

## 创建领域仓储

```python
from pathlib import Path
from infrastructure.sqlite import SQLiteRepository


class ResearchNoteRepository(SQLiteRepository):
    TABLE = "research_note"

    def __init__(self, db_path: str | Path | None = None):
        super().__init__(db_path)
        self.ensure_table(
            self.TABLE,
            {
                "Symbol": "TEXT NOT NULL",
                "Date": "DATE NOT NULL",
                "Content": "TEXT",
            },
            primary_key=("Symbol", "Date"),
            indexes=(("idx_research_note_date", ("Date",)),),
        )

    def save_note(self, symbol: str, date: str, content: str):
        self.upsert(self.TABLE, {
            "Symbol": symbol,
            "Date": date,
            "Content": content,
        })

    def get_notes(self, symbol: str) -> list[dict]:
        rows = self.cursor.execute(
            f"SELECT Symbol,Date,Content FROM {self.TABLE} "
            "WHERE Symbol=? ORDER BY Date",
            (symbol,),
        ).fetchall()
        return [dict(row) for row in rows]
```

实际项目中，示例类应放在拥有 research note 的业务域，而不是放进
`infrastructure/`。

## Schema 行为

`ensure_table()` 会：

1. 执行 `CREATE TABLE IF NOT EXISTS`；
2. 通过 `PRAGMA table_info` 检查现有列；
3. 对缺少的声明列执行 `ALTER TABLE ADD COLUMN`；
4. 创建声明的索引；
5. 提交事务。

它只支持向前增加列，不处理：

- 删除列；
- 重命名列；
- 修改已有列类型或约束；
- 数据回填；
- 跨表迁移。

这些变化需要领域自己提供显式迁移脚本，并在执行破坏性操作前备份数据库。

新增列时，自动迁移只取声明中的基础类型。例如 `REAL NOT NULL DEFAULT 0` 在
`ALTER TABLE` 阶段只会使用 `REAL`，所以对存量表增加强约束应使用专门迁移。

## UPSERT 语义

底层使用：

```sql
INSERT ... ON CONFLICT DO UPDATE SET ...
```

冲突时只更新本次 row 提供的列，不会像 `INSERT OR REPLACE` 那样先删除整行。因此
财报局部重新解析时，不会清空本次未提供的历史字段。

`upsert_many()` 假设所有 row 使用第一行相同的 key 集合。字段集合不一致的数据应
先归一化，或逐条调用领域仓储方法。

## 事务与连接生命周期

推荐：

```python
with ResearchNoteRepository("tmp/research.db") as repository:
    repository.save_note("Tencent", "2026-08-20", "example")
```

当前实现中 `upsert()`、`upsert_many()` 和 `ensure_table()` 都会主动 commit。
`with` 正常退出时也会提交，随后关闭连接。

注意：

- SQLite 连接默认只应在创建它的线程中使用；
- 当前 journal mode 为 `DELETE`，不适合多个进程高并发写入；
- Repository 实例不要作为全局永久单例跨线程共享；
- 外部注入 Repository 时，由创建者负责关闭；
- 批量任务应尽量复用同一个 Repository，避免频繁建连。

## 安全边界

表名、列名和索引名通过字符串拼接进入 SQL，必须来自代码中的固定常量。用户输入
只能作为 `?` 参数值，不能直接作为标识符传给 `ensure_table()` 或拼进查询。

`FeatureRepository.cross_section_rank()` 会先用 `FEATURE_KEYS` 校验动态列名，
这是处理动态标识符时应遵循的模式。

## 领域所有权

| 领域 | Repository | 业务表 |
|---|---|---|
| 行情 | `MarketDataRepository` | `kline_daily` |
| 量化特征 | `FeatureRepository` | `quant_feature_daily` |
| 财报 | `FinancialReportRepository` | `financial_report` |

禁止重新创建一个集中了解所有表的数据库类。跨领域用例应由 application service
或 `tools` 编排多个 Repository，而不是让一个 Repository 查询别人的表。

## 测试

Repository 测试必须使用临时数据库：

```python
def test_repository(tmp_path):
    path = tmp_path / "trader.db"
    with ResearchNoteRepository(path) as repository:
        ...
```

不要让自动测试修改 `database/stock_data.db`。

相关文档：[数据表](../data_schema.md)、[架构](../architecture.md)。
