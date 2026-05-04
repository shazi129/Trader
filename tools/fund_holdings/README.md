# 巴菲特持仓分析工具

本工具用于获取和分析巴菲特（伯克希尔·哈撒韦）的13F持仓数据，并可视化展示持仓趋势。

## 功能说明

1. **数据获取**：从SEC EDGAR官方API获取最新的13F持仓报告
2. **数据解析**：解析XML格式的持仓数据
3. **趋势分析**：分析各股票持仓数量随时间的变化趋势
4. **可视化展示**：生成持仓趋势图表

## 使用方法

### 1. 准备工作

确保安装了所需依赖库：

```bash
pip install requests pandas matplotlib
```

### 2. 运行工具

```bash
python holdings_trend.py
```

### 3. 查看结果

工具将：
- 自动从SEC获取最新的持仓数据
- 生成持仓趋势图表保存为 `buffett_holdings_trend.png`
- 在控制台显示统计信息

## 文件结构

- `holdings_trend.py` - 主程序文件
- `data/` - 存放获取到的持仓数据（CSV格式）
- `buffett_holdings_trend.png` - 生成的持仓趋势图

## 注意事项

1. 工具会自动从SEC EDGAR获取最新数据，可能需要网络连接
2. 由于SEC API限制，请求频率不宜过高
3. 工具会自动保存数据到本地，下次运行时优先使用本地数据