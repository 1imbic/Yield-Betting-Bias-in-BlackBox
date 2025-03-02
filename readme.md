# 一款基于价值投注的小黑盒赚币工具

## YBB(Yield Betting Bias in BlackBox)

---

这是一个用于分析电竞比赛赔率并基于 Kelly 公式分配投注金额的 Python 工具。
它可以从[指定网站](https://cyber-ggbet.com/)抓取赔率数据，计算相关指标，并在图形界面中展示分析结果。
readme写于1.0.3,先已更新到1.1.0

## 功能特性

- **赔率抓取**：从指定 URL（如 `cyber-ggbet.com`）抓取队伍赔率数据。
- **赔率分析**：计算胜率、期望收益、收益方差、Kelly 比例和小黑盒抽成。
- **Kelly 分配**：根据 Kelly 值分配总投注金额（coins），每注上限 5000。
- **GUI 展示**：通过图形界面显示分析结果和分配方案。

## 依赖安装

### 前提条件

- Python 3.8 或更高版本
- Google Chrome 浏览器（用于 Selenium 抓取数据）

### 安装步骤

1. 克隆或下载本项目到本地：

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. 创建并激活虚拟环境（推荐）：

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 安装 Chrome WebDriver：
   - 下载与 Chrome 浏览器版本匹配的 [ChromeDriver](https://sites.google.com/chromium.org/driver/)。
   - 将 `chromedriver` 可执行文件放入项目目录，或添加到系统 `PATH` 中。

## 使用指南

### 运行程序

1. 确保所有依赖已安装。
2. 在项目目录下运行主程序：

   ```bash
   python main.py
   ```

### 操作步骤

1. **输入 URL**：
   - 在主界面输入赔率数据源 URL（默认已填入示例 URL）。
   - 点击“获取/检查赔率数据”按钮，程序将抓取数据并保存到 `Odds_Data` 文件夹。

2. **分析赔率**：
   - 点击“分析赔率”按钮，打开新窗口。
   - 在每个队伍的输入框中填入“小黑盒赔率”，按回车键计算并更新表格。

3. **Kelly 分析**：
   - 点击“Kelly 分析”按钮，打开新窗口。
   - 输入总 coins 数量（如 25000），按回车键查看按 Kelly 值分配的结果。
   - 结果将保存到 `Ky_<原文件名>.csv` 中。

## 文件结构

```bash
project-directory/
├── main.py                  # 主程序入口
├── fetch_odds.py            # 赔率抓取模块
├── data_processor.py        # 数据处理模块
├── odds_gui.py              # 赔率分析 GUI
├── kelly_processor.py       # Kelly 分配模块
├── requirements.txt         # 依赖列表
├── README.md                # 项目说明文档
├── Odds_Data/               # 存储赔率数据和结果的文件夹
```

## 示例数据

输入 `coins = 25000`，程序将基于 Kelly 值分配投注金额，结果类似：

| Team            | Kelly | Allocated_Coins |
|-----------------|-------|-----------------|
| PaiN Gaming     | 0.78  | 5000.00         |
| Eternal Fire    | 0.60  | 5000.00         |
| FURIA Esports   | 0.47  | 5000.00         |
| M80             | 0.26  | 2932.54         |
| ...             | ...   | ...             |

## 注意事项

- 确保网络连接正常以抓取赔率数据。
- 如果程序未响应，检查 ChromeDriver 是否正确安装或 URL 是否有效。
- Kelly 值为 0 的队伍不会出现在分配结果中。

## 贡献

欢迎提交问题或改进建议！请创建 Issue 或 Pull Request。

## 许可证

本项目采用 MIT 许可证，详情见 `LICENSE` 文件。

### 验证安装和运行

用户按照 README 中的步骤操作后，应该能：

- 成功安装依赖。
- 运行 `python main.py` 并看到主界面。
- 输入示例 URL 和 coins 值，获得预期输出。

如果有其他需求（如添加更多说明或调整格式），请告诉我！
