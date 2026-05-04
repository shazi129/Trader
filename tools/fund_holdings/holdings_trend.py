"""
巴菲特持仓趋势分析工具
- 从SEC EDGAR获取历史持仓数据
- 分析并可视化各股票持仓变化趋势
"""

import sys
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ---------- 常量 ----------
# 伯克希尔·哈撒韦 CIK
BERKSHIRE_CIK = "0001067983"

# SEC EDGAR API 基础 URL
EDGAR_BASE = "https://data.sec.gov/submissions"
EDGAR_ARCHIVE = "https://www.sec.gov/Archives/edgar/data"

# 请求头（EDGAR 要求提供 User-Agent）
HEADERS = {
    "User-Agent": "BuffettHoldingsTrend/1.0 (contact: user@example.com)"
}


def _request(url, headers=None, timeout=30):
    """
    简单的 HTTP 请求，不包含重试机制
    
    Args:
        url: 请求 URL
        headers: 请求头
        timeout: 超时秒数
        
    Returns:
        requests.Response 对象，失败返回 None
    """
    try:
        resp = requests.get(url, headers=headers or HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None


def get_recent_filings(cik: str = BERKSHIRE_CIK, count: int = 10) -> list:
    """
    获取伯克希尔最近的 13F 申报列表

    Args:
        cik: CIK 编号
        count: 返回最近多少条申报

    Returns:
        申报信息列表，每条包含 filingDate, formType, accessionNumber 等
    """
    url = f"{EDGAR_BASE}/CIK{cik}.json"
    try:
        resp = _request(url)
        if not resp:
            print("获取申报列表失败")
            return []
        data = resp.json()

        # EDGAR API 返回结构: filings.recent 是 dict of lists
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        film_numbers = recent.get("filmNumber", [])

        filings = []
        for i in range(len(forms)):
            if "13F" in forms[i]:
                try:
                    ak = accession_numbers[i]
                    cik_clean = cik.lstrip('0')
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{ak}/{ak}-index.htm"
                    filings.append({
                        "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                        "report_date": report_dates[i] if i < len(report_dates) else "",
                        "form": forms[i],
                        "accession_number": ak,
                        "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                        "filing_url": filing_url,
                    })
                except IndexError:
                    print(f"索引访问错误，跳过第 {i} 条记录")
                    continue

        # 按申报日期倒序，取最近的 count 条
        filings.sort(key=lambda x: x["filing_date"], reverse=True)
        return filings[:count]

    except Exception as e:
        print(f"获取申报列表失败: {e}")
        return []


def parse_holdings_from_xml(xml_content: str, report_date: str) -> pd.DataFrame:
    """
    从 XML 内容解析持仓数据
    
    Args:
        xml_content: XML 内容
        report_date: 报告日期
        
    Returns:
        DataFrame 包含持仓明细
    """
    try:
        # 解析 XML
        root = ET.fromstring(xml_content)
        
        # 查找持仓信息所在的节点
        holdings = []
        
        # 尝试不同的节点结构来找到持仓数据
        for elem in root.iter():
            if elem.tag.endswith('infoTable') or elem.tag.endswith('infotable'):
                holding = {}
                for child in elem:
                    # 处理常见字段
                    if child.tag == 'nameOfIssuer':
                        holding['证券名称'] = child.text
                    elif child.tag == 'titleOfClass':
                        holding['证券类别'] = child.text
                    elif child.tag == 'cusip':
                        holding['CUSIP'] = child.text
                    elif child.tag == 'value':
                        holding['持仓价值(USD)'] = child.text
                    elif child.tag == 'sshPrnamt':
                        holding['数量'] = child.text
                    elif child.tag == 'sshPrnamtType':
                        holding['数量类型'] = child.text
                    elif child.tag == 'investmentDiscretion':
                        holding['投资决策'] = child.text
                    elif child.tag == 'otherManager':
                        holding['其他管理者'] = child.text
                        
                if holding:
                    holding['报告日期'] = report_date
                    holdings.append(holding)
        
        # 如果没有找到持仓数据，返回空DataFrame
        if not holdings:
            print("未找到持仓数据")
            return pd.DataFrame()
        
        df = pd.DataFrame(holdings)
        return df
        
    except Exception as e:
        print(f"解析XML失败: {e}")
        return pd.DataFrame()


def get_holdings_from_filing(accession_number: str, cik: str = BERKSHIRE_CIK) -> pd.DataFrame:
    """
    从指定的 13F 申报中获取持仓数据
    
    Args:
        accession_number: 申报编号
        cik: CIK 编号

    Returns:
        DataFrame 包含持仓明细
    """
    try:
        # 构造XML文件的URL
        cik_clean = cik.lstrip('0')
        # 尝试使用不同的XML格式
        xml_urls = [
            f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_number}/{accession_number}-xslForm13F_X01.xml",
            f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_number}/{accession_number}-xslForm13F_X02.xml"
        ]
        
        df = pd.DataFrame()
        for xml_url in xml_urls:
            print(f"正在获取持仓数据: {xml_url}")
            resp = _request(xml_url)
            if resp:
                xml_content = resp.text
                # 解析XML获取持仓数据
                df = parse_holdings_from_xml(xml_content, "")
                if not df.empty:
                    break
        
        if df.empty:
            print("获取持仓XML失败")
            
        return df
        
    except Exception as e:
        print(f"获取持仓数据失败: {e}")
        return pd.DataFrame()


def load_holding_data_from_csv(data_dir: str) -> List[pd.DataFrame]:
    """
    从CSV文件加载持仓数据
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        持仓数据DataFrame列表
    """
    holdings = []
    data_path = Path(data_dir)
    
    # 查找所有持仓数据文件
    csv_files = data_path.glob("buffett_13f_holdings_*.csv")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding="utf-8-sig")
            # 尝试解析报告日期
            if "报告日期" in df.columns:
                df["报告日期"] = pd.to_datetime(df["报告日期"])
            holdings.append(df)
            print(f"已加载 {csv_file.name}")
        except Exception as e:
            print(f"加载 {csv_file.name} 失败: {e}")
    
    return holdings


def analyze_holding_trend(holdings_data: List[pd.DataFrame]) -> Dict:
    """
    分析持仓趋势
    
    Args:
        holdings_data: 持仓数据列表
        
    Returns:
        持仓趋势分析结果
    """
    # 合并所有数据
    all_data = pd.concat(holdings_data, ignore_index=True)
    
    # 如果没有"证券名称"列，尝试从其他列提取
    if "证券名称" not in all_data.columns:
        if "nameOfIssuer" in all_data.columns:
            all_data["证券名称"] = all_data["nameOfIssuer"]
        elif "Name of Issuer" in all_data.columns:
            all_data["证券名称"] = all_data["Name of Issuer"]
    
    # 如果没有"数量"列，尝试从其他列提取
    if "数量" not in all_data.columns:
        if "sshPrnamt" in all_data.columns:
            all_data["数量"] = all_data["sshPrnamt"]
        elif "Shr / Put Or Call" in all_data.columns:
            all_data["数量"] = all_data["Shr / Put Or Call"]
    
    # 如果没有"报告日期"列，尝试从其他列提取
    if "报告日期" not in all_data.columns:
        if "report_date" in all_data.columns:
            all_data["报告日期"] = all_data["report_date"]
        elif "filing_date" in all_data.columns:
            all_data["报告日期"] = all_data["filing_date"]
    
    # 如果没有"持仓价值"列，尝试从其他列提取
    if "持仓价值(USD)" not in all_data.columns:
        if "value" in all_data.columns:
            all_data["持仓价值(USD)"] = all_data["value"]
        elif "Value" in all_data.columns:
            all_data["持仓价值(USD)"] = all_data["Value"]
    
    # 按证券名称和报告日期分组，计算总持仓量
    if "证券名称" in all_data.columns and "数量" in all_data.columns and "报告日期" in all_data.columns:
        # 转换数量为数值型
        all_data["数量"] = pd.to_numeric(all_data["数量"], errors='coerce')
        all_data = all_data.dropna(subset=["数量"])
        
        # 按证券名称和报告日期分组
        trend_data = all_data.groupby(["证券名称", "报告日期"])["数量"].sum().reset_index()
        
        # 按证券名称分组，按报告日期排序
        trend_data = trend_data.sort_values(["证券名称", "报告日期"])
        
        # 生成趋势分析
        trend_analysis = {}
        for stock_name in trend_data["证券名称"].unique():
            stock_data = trend_data[trend_data["证券名称"] == stock_name].copy()
            stock_data = stock_data.sort_values("报告日期")
            trend_analysis[stock_name] = stock_data
            
        return trend_analysis
    
    return {}


def plot_holding_trend(trend_analysis: Dict, top_n: int = 10):
    """
    绘制持仓趋势图
    
    Args:
        trend_analysis: 持仓趋势分析结果
        top_n: 显示前N只股票
    """
    if not trend_analysis:
        print("没有可绘制的趋势数据")
        return
    
    # 获取前N只股票
    stocks = list(trend_analysis.keys())[:top_n]
    
    # 创建图表
    plt.figure(figsize=(15, 10))
    
    for stock in stocks:
        data = trend_analysis[stock]
        if not data.empty:
            plt.plot(data["报告日期"], data["数量"], marker='o', label=stock, linewidth=2)
    
    plt.title('巴菲特持仓趋势分析', fontsize=16, fontweight='bold')
    plt.xlabel('报告日期', fontsize=12)
    plt.ylabel('持仓数量', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 设置x轴日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('buffett_holdings_trend.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("持仓趋势图已保存为 buffett_holdings_trend.png")


def main():
    """
    主函数
    """
    print("=" * 60)
    print("巴菲特持仓趋势分析工具")
    print("=" * 60)
    
    # 获取数据目录路径
    data_dir = str(Path(__file__).parent / "data")
    
    # 首先检查是否存在CSV文件
    try:
        holdings_data = load_holding_data_from_csv(data_dir)
        
        if holdings_data:
            print(f"从CSV文件加载到 {len(holdings_data)} 个持仓数据文件")
        else:
            print("未找到CSV文件，正在从网络获取数据...")
            
            # 获取最近的申报
            print("\n正在获取 13F 申报列表..")
            filings = get_recent_filings(count=5)
            
            if filings:
                print(f"\n获取到 {len(filings)} 条申报记录:")
                for i, filing in enumerate(filings, 1):
                    print(f"{i}. 申报日期: {filing['filing_date']}")
                    print(f"   报告期: {filing['report_date']}")
                    print(f"   表格类型: {filing['form']}")
                    print(f"   申报编号: {filing['accession_number']}")
                    print()
                
                # 尝试获取持仓数据
                print("正在获取持仓数据...")
                holdings = []
                for i, filing in enumerate(filings):
                    print(f"处理第 {i+1} 条申报: {filing['report_date']}")
                    df = get_holdings_from_filing(filing['accession_number'])
                    if not df.empty:
                        df['报告日期'] = filing['report_date']
                        holdings.append(df)
                        print(f"获取到 {len(df)} 条持仓记录")
                        print()
                
                # 保存持仓数据
                if holdings:
                    print("正在保存持仓数据...")
                    save_holdings_to_csv(holdings, output_dir=data_dir)
                    holdings_data = holdings
                else:
                    print("未获取到持仓数据")
                    return
            else:
                print("未获取到申报数据")
                return
                
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return
    
    # 分析持仓趋势
    print("正在分析持仓趋势...")
    trend_analysis = analyze_holding_trend(holdings_data)
    
    if trend_analysis:
        # 绘制趋势图
        print("正在绘制持仓趋势图...")
        plot_holding_trend(trend_analysis, top_n=10)
        
        # 显示统计信息
        print("\n持仓统计信息:")
        print("-" * 40)
        for stock, data in list(trend_analysis.items())[:5]:  # 只显示前5只
            if not data.empty:
                first_value = data["数量"].iloc[0] if len(data) > 0 else 0
                last_value = data["数量"].iloc[-1] if len(data) > 0 else 0
                print(f"{stock}: 初始持仓 {first_value:,.0f} → 最终持仓 {last_value:,.0f}")
        
        print("\n完成！")
    else:
        print("未找到有效的持仓数据用于分析")


def save_holdings_to_csv(holdings: list, output_dir: str = ".") -> None:
    """
    将持仓数据保存为 CSV 文件

    Args:
        holdings: 持仓 DataFrame 列表
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, df in enumerate(holdings):
        if not df.empty:
            report_date = df['报告日期'].iloc[0] if '报告日期' in df.columns else f"holding_{i}"
            file_name = f"buffett_13f_holdings_{report_date}.csv"
            df.to_csv(output_path / file_name, index=False, encoding="utf-8-sig")
            print(f"已保存持仓数据: {output_path / file_name}")


if __name__ == "__main__":
    main()