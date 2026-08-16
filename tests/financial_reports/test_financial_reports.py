from financial_reports import FinancialParser, FinancialReport, ParserError
from financial_reports.field_mapping import normalize
from financial_reports.parsers._utils import (
    infer_period_type,
    parse_chinese_date,
    parse_number,
)


def test_financial_report_json_round_trip():
    report = FinancialReport(
        name_key="Tencent",
        period_end="2025-12-31",
        period_type="ANNUAL",
        announce_date="2026-03-18",
        currency="CNY",
        audited=True,
        source="pdf_hk_ifrs",
        source_file="2025Q4.pdf",
        fields={"Revenue": 100.0},
        warnings=["example"],
    )

    assert FinancialReport.from_json(report.to_json()) == report


def test_public_model_api_does_not_load_pdf_parser():
    assert FinancialReport.__module__ == "financial_reports.models"
    assert FinancialParser.__module__ == "financial_reports.parser_base"
    assert ParserError.__module__ == "financial_reports.parser_base"


def test_financial_report_normalization_helpers():
    assert normalize(" 本公司權益持有人應佔盈利 ", "HK_IFRS") == "NetIncomeAttr"
    assert parse_chinese_date("香港，二零二六年三月十八日") == "2026-03-18"
    assert parse_number("(84,071.00)") == -84071.0
    assert infer_period_type("2025-12-31") == "ANNUAL"
