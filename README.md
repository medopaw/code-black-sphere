# code-black-sphere

"code-black-sphere" 是一个在线判题工具。该项目旨在为用户提供一个提交代码并获得自动评测结果的平台。

## 项目状态

本项目目前正在开发中。有关开发计划和设计规范的更多详细信息，请参阅 [PLAN.md](PLAN.md) 和 [docs/DESIGN.md](docs/DESIGN.md)。

## 开始使用

### 环境要求

- Python >=3.12.1

### 安装与运行

1.  **克隆仓库:**
    ```bash
    git clone <repository-url>
    cd code-black-sphere
    ```

2.  **设置虚拟环境并安装依赖:**
    本项目使用 `uv` 进行包管理。
    ```bash
    # 创建虚拟环境 (如果还没有)
    python -m venv .venv
    source .venv/bin/activate  # Windows 用户请使用 `source .venv\Scripts\activate`

    # 使用 uv 安装依赖
    # pyproject.toml 文件中已列出依赖项
    uv pip install -e .
    # 或者，如果您有 uv.lock 文件并希望同步:
    # uv pip sync uv.lock
    ```

3.  **设置环境变量:**
    在项目根目录创建一个 `.env` 文件，并添加必要的配置 (例如，数据库URL, 密钥)。示例:
    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    SECRET_KEY='your_secret_key'
    DATABASE_URL='postgresql://user:password@host:port/database'
    ```

4.  **初始化和迁移数据库 (如果使用 Flask-Migrate):**
    ```bash
    flask db init  # 首次运行时执行
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

5.  **运行应用:**
    ```bash
    uv run python run.py
    ```
    应用应该可以通过 `http://127.0.0.1:5000` (或配置的地址) 访问。

## 项目结构

```
code-black-sphere/
├── .venv/                  # 虚拟环境
├── app/                    #主要的 Flask 应用
│   ├── __init__.py         # 应用工厂
│   ├── auth/               # 认证蓝图 (表单, 路由)
│   ├── main/               # 主要应用蓝图 (路由)
│   ├── models.py           # 数据库模型
│   ├── templates/          # HTML 模板
│   └── config.py           # 配置文件
├── docs/                   # 项目文档
│   ├── DESIGN.md
│   └── DEVPLAN.md
├── instance/               # 实例文件夹 (例如 SQLite 数据库文件)
│   └── app.db
├── migrations/             # 数据库迁移文件
├── .gitignore
├── .python-version
├── PLAN.md                 # 项目整体计划
├── README.md               # 本文件
├── pyproject.toml          # 项目元数据和依赖
├── run.py                  # 运行 Flask 应用的脚本
└── uv.lock                 # uv 锁文件
```

## 如何贡献

请参阅 [PLAN.md](PLAN.md) 获取任务列表和贡献指南。

## 许可证

(请在此处指定您项目的许可证, 例如 MIT 许可证)
