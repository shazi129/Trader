# -*- coding: utf-8 -*-
"""财报 PDF 入库工具。

用法
====

::

    # 解析单个 PDF（落盘 JSON，不入库；干跑/调试）
    python -m tools.financial_fetcher.financial_fetcher parse \\
        --file tools/financial_fetcher/腾讯/2025Q3.pdf --stock Tencent

    # 解析整个文件夹下的所有 PDF（默认入库 + 落盘 JSON）
    python -m tools.financial_fetcher.financial_fetcher run \\
        --folder tools/financial_fetcher/腾讯 --stock Tencent

    # 干跑模式（只解析、落盘 JSON、不入库）
    python -m tools.financial_fetcher.financial_fetcher run \\
        --folder tools/financial_fetcher/腾讯 --stock Tencent --dry-run

    # 跳过已入库（按 PeriodEnd 判断），仅处理新增 PDF
    python -m tools.financial_fetcher.financial_fetcher run \\
        --folder tools/financial_fetcher/腾讯 --stock Tencent --skip-existing

约定
====

文件夹下 PDF 命名 ``{period}.pdf``（如 ``2025Q3.pdf``），其中 ``period``
匹配 ``\\d{4}Q[1-4]``，将作为 ``period_hint`` 传给解析器（用于早期格式
PDF 没有标准"截至XX止"句式时的兜底）。

中间产物 ``parsed/{stock}_{period}.json`` 会保留每份解析后的字段 dict +
warnings 列表，便于人工 review 和 git diff 跟踪映射变更。
"""

from __future__ import annotations

import argparse
import re
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional

# 让脚本既能 ``python -m tools.financial_fetcher.financial_fetcher`` 也能直跑
_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from database.stock_db_utils import StockDB  # noqa: E402
from quote_api.financial import (  # noqa: E402
    ParserFactory,
    FinancialReport,
    ParserError,
)
from utils.logger import get_logger  # noqa: E402

_log = get_logger(__name__)

PARSED_DIR = _THIS_DIR / "parsed"
_PERIOD_RE = re.compile(r"^(\d{4}Q[1-4])", re.IGNORECASE)


# ===========================================================================
# 单文件 / 单文件夹处理
# ===========================================================================

def parse_one(pdf_path: Path, name_key: str,
              parsed_dir: Optional[Path] = None) -> Optional[FinancialReport]:
    """解析单份 PDF → 返回 FinancialReport（同时落盘 JSON 中间产物）。

    解析失败返回 None（不抛异常，便于批量调用方继续处理其它 PDF）。
    """
    parser = ParserFactory.detect(pdf_path)
    if parser is None:
        _log.warning("[%s] no parser available", pdf_path.name)
        return None

    # 从文件名抽取 period_hint（"2025Q3.pdf" → "2025Q3"）
    m = _PERIOD_RE.match(pdf_path.stem)
    period_hint = m.group(1).upper() if m else None

    try:
        report = parser.parse(pdf_path, name_key, period_hint=period_hint)
    except ParserError as e:
        _log.error("[%s] parse failed: %s", pdf_path.name, e)
        return None
    except Exception as e:  # noqa: BLE001
        _log.exception("[%s] unexpected parse error: %s", pdf_path.name, e)
        return None

    # 落盘 JSON 中间产物
    if parsed_dir is not None:
        out = parsed_dir / f"{name_key}_{pdf_path.stem}.json"
        try:
            report.dump(out)
        except Exception as e:  # noqa: BLE001
            _log.warning("[%s] dump json failed: %s", pdf_path.name, e)

    return report


def run_folder(folder: Path, name_key: str, *,
               db_path: Optional[str] = None,
               dry_run: bool = False,
               skip_existing: bool = False,
               parsed_dir: Optional[Path] = None) -> tuple[int, int]:
    """批处理 ``folder`` 下所有 PDF；返回 ``(success, failed)``。"""
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        _log.warning("[%s] no PDF found", folder)
        return 0, 0

    parsed_dir = parsed_dir or PARSED_DIR
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # 已入库的 PeriodEnd 集合（用于 --skip-existing）
    existing: set[str] = set()
    if skip_existing and not dry_run:
        with closing(StockDB(db_path)) as db:
            rows = db.get_financial_reports(name_key)
            existing = {r["PeriodEnd"] for r in rows}
        _log.info("[%s] DB 已有 %d 份报告", name_key, len(existing))

    success = 0
    failed = 0
    parsed_reports: list[FinancialReport] = []

    for pdf in pdfs:
        report = parse_one(pdf, name_key, parsed_dir=parsed_dir)
        if report is None:
            failed += 1
            continue

        if skip_existing and report.period_end in existing:
            _log.info("[%s] skip (already in DB): %s",
                      pdf.name, report.period_end)
            continue

        parsed_reports.append(report)
        success += 1
        _log.info(
            "[%s] OK: period_end=%s announce=%s type=%s fields=%d warnings=%d",
            pdf.name, report.period_end, report.announce_date,
            report.period_type, len(report.fields), len(report.warnings),
        )

    if parsed_reports and not dry_run:
        with closing(StockDB(db_path)) as db:
            db.write_financial_reports_many(parsed_reports)
        _log.info("[%s] 入库完成: %d 份", name_key, len(parsed_reports))
    elif dry_run:
        _log.info("[%s] dry-run 模式，跳过入库（共 %d 份解析成功）",
                  name_key, success)

    return success, failed


# ===========================================================================
# CLI
# ===========================================================================

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="财报 PDF 入库工具（支持港股 IFRS 业绩公告）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # parse: 单文件，调试用
    p_parse = sub.add_parser("parse", help="解析单个 PDF，仅落盘 JSON 不入库")
    p_parse.add_argument("--file", required=True, help="PDF 路径")
    p_parse.add_argument("--stock", required=True,
                         help="name_key（如 Tencent）")

    # run: 批量
    p_run = sub.add_parser("run", help="批量解析文件夹下所有 PDF + 入库")
    p_run.add_argument("--folder", required=True, help="PDF 所在文件夹")
    p_run.add_argument("--stock", required=True,
                       help="name_key（如 Tencent）")
    p_run.add_argument("--db", help="数据库路径（默认 database/stock_data.db）")
    p_run.add_argument("--dry-run", action="store_true",
                       help="只解析 + 落盘 JSON，不入库")
    p_run.add_argument("--skip-existing", action="store_true",
                       help="已入库的 PeriodEnd 跳过（按报告期判断）")
    return p


def main() -> int:
    args = _build_parser().parse_args()
    if args.cmd == "parse":
        rep = parse_one(Path(args.file), args.stock,
                        parsed_dir=PARSED_DIR)
        if rep is None:
            return 1
        print(f"OK: {args.file}")
        print(f"  period_end={rep.period_end}  announce={rep.announce_date}")
        print(f"  type={rep.period_type}  currency={rep.currency}  "
              f"audited={rep.audited}")
        print(f"  fields={len(rep.fields)}  warnings={len(rep.warnings)}")
        return 0

    if args.cmd == "run":
        ok, fail = run_folder(
            Path(args.folder), args.stock,
            db_path=args.db,
            dry_run=args.dry_run,
            skip_existing=args.skip_existing,
        )
        print(f"\nSummary: success={ok}  failed={fail}")
        return 0 if fail == 0 else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
