# 📈 周度销售数据对比分析工具

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg) ![Flask](https://img.shields.io/badge/Flask-2.x-green.svg) ![Pandas](https://img.shields.io/badge/Pandas-1.x-orange.svg) ![Nginx](https://img.shields.io/badge/Nginx-gray.svg) ![Gunicorn](https://img.shields.io/badge/Gunicorn-informational) ![Status](https://img.shields.io/badge/status-active-success.svg)

一个高效、自动化的Web应用，旨在简化销售团队的周度数据整合与分析流程。用户只需上传三份标准的Excel报表，即可一键生成按区域经理聚合的销售覆盖率报告，并能直观对比上周与本周的数据表现。

---

## 🚀 项目亮点

- **自动化处理**: 告别手动VLOOKUP和数据透视表，一键完成数据合并、清洗和聚合。
- **用户友好**: 简洁明了的Web界面，只需三步即可完成操作：选择文件 -> 开始处理 -> 保存结果。
- **实时对比**: 在同一视图中清晰展示上周与本周的汇总数据，便于快速洞察趋势变化。
- **持久化存储**: 所有处理记录均被保存，可随时按月份回溯查看历史明细数据。
- **异步处理**: 后端采用异步任务处理数据，即使用户关闭页面，数据处理也不会中断。
- **生产级部署**: 采用 Nginx + Gunicorn + Systemd 的标准部署架构，确保服务7x24小时稳定可靠。

---

## 🛠️ 技术栈

这个项目采用了前后端分离的现代Web应用架构。

- **后端 (Backend)**:
  - **框架**: [Flask](https://flask.palletsprojects.com/)
  - **数据处理**: [Pandas](https://pandas.pydata.org/) & [Numpy](https://numpy.org/)
  - **Excel读取引擎**: [Calamine](https://github.com/pwwang/calamine-python) (通过 `pandas` 调用，性能优异)
  - **WSGI服务器**: [Gunicorn](https://gunicorn.org/)

- **前端 (Frontend)**:
  - **原生三件套**: HTML, CSS, JavaScript
  - **UI框架**: [Bootstrap 5](https://getbootstrap.com/) (用于快速构建美观的响应式界面)

- **部署 (Deployment)**:
  - **Web服务器/反向代理**: [Nginx](https://www.nginx.com/)
  - **进程守护**: Systemd (Linux系统服务)
  - **跨域解决方案**: [Flask-CORS](https://flask-cors.readthedocs.io/)

---

## 📋 功能列表

- [x] **文件上传**: 支持同时上传销售订单、多形态价格、区域经理三份核心报表。
- [x] **数据聚合**: 自动按“区域”和“大区经理”进行分组，计算订单总数、交货总数。
- [x] **覆盖率计算**: 自动计算各区域的销售覆盖率，并以百分比格式化显示。
- [x] **周度汇总视图**: 在主页并排展示上周和本周的最终分析结果。
- [x] **历史记录查询**: 提供弹窗，可按月份筛选和查看过往每一次处理的详细记录。
- [x] **异步任务状态**: 前端轮询查询后端任务状态，实时反馈处理进度。

---

## ⚙️ 如何在本地运行

如果你想在自己的电脑上运行这个项目进行开发或测试，请遵循以下步骤：

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your-github-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **创建并激活Python虚拟环境**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **运行后端开发服务器**
    ```bash
    python backend.py
    ```
    应用将在 `http://127.0.0.1:5000` 上启动。

5.  **访问应用**
    在你的浏览器中打开 `http://127.0.0.1:5000` 即可开始使用！

---

## 📜 未来可以优化的方向

- [ ] **用户认证系统**: 增加登录功能，区分不同用户的操作和数据。
- [ ] **数据可视化**: 使用 Chart.js 或 ECharts 将结果以图表形式展示，更具洞察力。
- [ ] **文件模板校验**: 在后端增加对上传Excel文件的列名和格式的校验，提供更友好的错误提示。
- [ ] **配置灵活性**: 将Excel的列名、Sheet名等配置移入一个独立的`config.ini`文件，方便非开发人员调整。

---

*该项目由 [Your Name] 创建。*
