# 技术设计文档：在线判题工具

## 1. 引言

### 1.1. 项目概述

本项目旨在开发一个在线判题工具，该工具允许用户管理候选人、创建和编辑题目、运行候选人提交的代码针对测试用例进行评测，并利用大语言模型（LLM）对代码质量进行评估和打分。工具将以 Web 应用的形式呈现，提供直观易用的用户界面。

### 1.2. 目标

- 提供一个平台，方便对候选人的编程能力进行评估。
- 实现自动化的测试用例执行和结果反馈。
- 集成大语言模型，提供代码质量分析和评分。
- 支持题目的灵活管理，包括创建、编辑、导入和导出。
- 保证用户数据的持久化存储和状态恢复。

## 2. 系统架构

### 2.1. 前端 (Frontend)

- **技术选型**: React
- **职责**: 用户界面展示、用户交互处理、向后端发送请求、展示后端返回数据、状态管理。

### 2.2. 后端 (Backend)

- **技术选型建议**:
    - **Node.js (Express.js / NestJS)**: 对于 I/O 密集型操作和前端技术栈 (React) 有较好的一致性，JavaScript 全栈开发体验流畅。Express.js 轻量灵活，NestJS 功能更完善，结构化更强。
    - **Python (Flask / Django)**: Python 社区庞大，拥有丰富的库。
        - **Flask**: 轻量级框架，灵活性高，上手快，适合小型到中型项目或 API 开发。对于本项目，如果追求快速开发和简洁，Flask 是一个不错的选择。
        - **Django**: "Batteries-included" 框架，功能全面（如 ORM, Admin 后台），开发效率高，适合大型复杂项目。对于本项目，如果未来有较多功能扩展或需要强大的后台管理，Django 也是一个可选项，但初期可能略显重。
    - **选择考量**: 经过讨论，我们决定选用 **Flask** 作为后端框架。它轻量、灵活，适合快速迭代，且能很好地满足本项目 API 服务和与 LLM 交互的核心需求。
- **职责**: 处理前端请求、业务逻辑处理（用户管理、题目管理、代码执行、与 LLM API 交互）、数据库操作、API 接口提供。

### 2.3. 数据库 (Database)

- **技术选型**: SQLite (根据用户要求)。
- **职责**: 存储所有持久化数据，包括候选人信息、题目信息、测试用例、答题记录、大模型评价、用户设置等。

### 2.4. API 接口 (API Endpoints)

- 后端将提供 RESTful API 供前端调用，用于数据交互和功能操作。

## 3. 用户界面 (UI) 设计

### 3.1. 主页面布局

- **左侧边栏**: 
    - **候选人列表**: 显示已存在的候选人名称。
    - **新建候选人按钮**: 点击后弹出输入框，输入候选人名称创建新候选人。
- **右侧主区域**: 
    - **判题界面 (Tabs)**: 以 Tab 形式展示，每个 Tab 对应一道题目。

### 3.2. 判题界面 (Tabs)

- **Tab 行为**:
    - **新建 Tab**: 按钮触发，需选择题目。
    - **关闭 Tab**: 每个 Tab 右上角有关闭按钮。若只有一个 Tab，则不显示关闭按钮。
    - **默认 Tab**: 若无已打开 Tab（首次加载），自动打开默认题目（可在设置中配置）。
    - **Tab 状态保持**: 切换候选人或题目 Tab 时，Tab 内的元素状态（如代码、滚动位置）应被保留。实现方式：所有打开的 Tab 的 DOM 元素实际存在于页面中，通过 CSS 控制显示/隐藏，而非销毁和重建。
    - **Tab 标题**: 显示题目名称。

### 3.3. 题目 Tab 内容 (自上而下)

1.  **题目描述**:
    -   可点击展开/收起。
    -   显示题目详细内容。
    -   渲染 markdown 内容
2.  **答题代码区**:
    -   支持多种编程语言（如 Python, JavaScript, Java, C++）。
    -   提供语法高亮功能 (例如使用 Monaco Editor, CodeMirror, or Prism.js)。
    -   用户可在此区域粘贴或编写代码。
    -   下方有“运行测试并评估”按钮。
3.  **测试用例及运行结果**:
    -   以列表形式展示每个测试用例。
    -   每项测试用例包括：
        -   参数名和参数值对 (JSON 格式)。
        -   预期结果 (JSON 基本数据类型)。
        -   运行状态：是否通过测试 (布尔值)。
        -   若未通过：显示实际输出、编译错误或运行时错误信息。
4.  **大模型生成的点评内容**:
    -   显示 LLM 对代码的评估、建议和分数。
    -   **流式显示**: 内容从 LLM API 流式返回时，实时更新显示区域，而非等待完整响应。


### 3.4. 题目编辑界面

-   **入口**: 
    -   Setting 界面：新建题目、编辑已有题目。
    -   判题 Tab 内：编辑当前题目按钮。
-   **组成部分**:
    1.  **题目名称编辑框**: 文本输入框。
    2.  **题目描述编辑框**: Markdown 编辑器。
    3.  **测试用例编辑区**:
        -   列表形式展示测试用例。
        -   每条测试用例可编辑参数 (JSON格式)、预期输出 (JSON格式)。
        -   支持添加新的测试用例、删除已有测试用例。
    4.  **大模型 Prompt 编辑框**: 文本区域，用于编辑发送给 LLM 的 Prompt 模板。
-   **保存按钮**: 点击后保存所有编辑内容到数据库。

### 3.5. 设置界面 (Settings Interface)

-   **默认题目设置**: 下拉选择或输入框指定默认打开的题目。
-   **题目管理**: 
    -   列表显示所有题目。
    -   新建题目按钮 (跳转到题目编辑界面)。
    -   编辑题目按钮 (跳转到题目编辑界面)。
    -   删除题目按钮。
-   **题目导入/导出**:
    -   **导出**: 按钮触发，将所有题目（名称、描述、测试用例、LLM Prompt）导出为一个 JSON 文件。
    -   **导入**: 文件选择框，选择 JSON 文件导入。导入前弹窗确认。导入逻辑：
        -   若题目名称已存在，则覆盖。
        -   若题目名称不存在，则新增。
-   **API Key 管理**:
    -   输入框供用户输入 DeepSeek API Key。
    -   保存按钮，将 API Key 加密后存入数据库。

## 4. 数据模型 (SQLite 数据库表结构)

### 4.1. `candidates` 表

-   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
-   `name` (TEXT, NOT NULL, UNIQUE)
-   `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### 4.2. `problems` 表

-   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
-   `title` (TEXT, NOT NULL, UNIQUE) - 题目名称
-   `description` (TEXT) - 题目描述 (Markdown)
-   `llm_prompt` (TEXT) - 大模型评估用的 Prompt 模板
-   `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)
-   `updated_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### 4.3. `test_cases` 表

-   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
-   `problem_id` (INTEGER, FOREIGN KEY REFERENCES `problems(id)` ON DELETE CASCADE)
-   `input_params` (TEXT) - JSON 字符串，表示参数名和参数值对，例如 `{"n": 10, "arr": [1,2,3]}`
-   `expected_output` (TEXT) - JSON 字符串，表示预期结果，例如 `"hello"` 或 `123` 或 `[1,2]`
-   `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### 4.4. `submissions` 表 (候选人的答题记录)

-   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
-   `candidate_id` (INTEGER, FOREIGN KEY REFERENCES `candidates(id)` ON DELETE CASCADE)
-   `problem_id` (INTEGER, FOREIGN KEY REFERENCES `problems(id)` ON DELETE CASCADE)
-   `language` (TEXT) - 提交代码的语言 (e.g., 'python', 'javascript')
-   `code` (TEXT) - 候选人提交的代码
-   `test_results` (TEXT) - JSON 字符串，存储每个测试用例的运行结果 (通过/失败，实际输出，错误信息)
-   `llm_review` (TEXT) - 大模型返回的点评内容
-   `submitted_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### 4.5. `candidate_problem_tabs` 表 (记录候选人打开的题目 Tab)

-   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
-   `candidate_id` (INTEGER, FOREIGN KEY REFERENCES `candidates(id)` ON DELETE CASCADE)
-   `problem_id` (INTEGER, FOREIGN KEY REFERENCES `problems(id)` ON DELETE CASCADE)
-   `tab_order` (INTEGER) - Tab 的显示顺序 (可选，用于恢复顺序)
-   UNIQUE (`candidate_id`, `problem_id`)

### 4.6. `settings` 表 (应用设置)

-   `key` (TEXT, PRIMARY KEY) - 设置项的键 (e.g., 'deepseek_api_key', 'default_problem_id')
-   `value` (TEXT) - 设置项的值

## 5. 核心功能实现细节

### 5.1. 候选人管理

-   **创建**: 前端发送候选人名称，后端存入 `candidates` 表。
-   **列表**: 后端提供 API 返回所有候选人。
-   **切换**: 前端切换候选人时，重新加载该候选人关联的 `candidate_problem_tabs`，并恢复各 Tab 的状态（代码、滚动等，前端状态管理）。

### 5.2. 题目管理 (CRUD)

-   **创建/编辑**: 通过题目编辑界面，后端保存/更新 `problems` 表和关联的 `test_cases` 表。
-   **读取**: 后端提供 API 获取题目列表和单个题目详情（包括测试用例）。
-   **删除**: 后端删除 `problems` 表记录及关联的 `test_cases`。

### 5.3. Tab 管理

-   **状态存储**: 当候选人打开或关闭一个题目的 Tab 时，更新 `candidate_problem_tabs` 表。
-   **状态恢复**: 用户切换到某候选人时，后端查询 `candidate_problem_tabs` 表，前端根据返回的题目 ID 列表打开相应的 Tab。
-   **UI 实现**: 前端维护一个所有已打开 Tab 的组件实例列表，通过 CSS `display: none/block` 控制显隐，以保持内部状态。

### 5.4. 代码评测 (运行测试用例)

1.  **代码执行环境与沙箱**:
    -   **必要性**: 即使用户是自己粘贴代码，如果代码来源不可控或包含复杂操作（如文件系统、网络访问），直接在服务器上执行仍有风险。沙箱提供了一个隔离的环境，可以限制代码的权限，防止恶意代码破坏服务器或泄露数据。
    -   **对于本项目**: 由于代码是用户自己粘贴，主要用于个人评估或辅助开发，风险相对较低。
        -   **简单方案 (无沙箱/轻度沙箱)**: 可以直接在服务器上执行代码，但需要严格控制执行权限（例如，以低权限用户运行），并限制可用的系统调用、执行时间和资源消耗。对于 Python，可以使用 `subprocess` 模块，并注意安全参数。对于其他语言，也有类似的执行方式。这种方案实现简单，但安全性较低。还需实现超时控制，防止无限循环等恶意行为。
        -   **推荐方案 (使用沙箱)**:
            -   **Docker 容器**: 这是目前最流行和成熟的方案。为每种语言准备一个包含运行环境的 Docker 镜像。每次执行代码时，启动一个临时的、资源受限的 Docker 容器来运行代码。执行完毕后销毁容器。
                -   **优点**: 安全性高，环境隔离好，易于管理不同语言的依赖，可以方便地限制CPU、内存、执行时间。
                -   **缺点**: 实现相对复杂，需要 Docker 环境支持，会有一定的性能开销（容器启动时间）。有许多现成的开源库（如 `docker-py` for Python）可以帮助与 Docker API 交互。
            -   **其他沙箱技术**: 例如使用 `ptrace` (Linux) 进行系统调用拦截，或者特定语言的沙箱库 (如 Python 的 `RestrictedPython`，但可能功能受限较多，且不一定支持所有语言特性)。
    -   **决策建议**:
        -   为了确保安全性和环境隔离，同时简化开发，我们决定**采用现成的开源判题 Docker 框架作为执行沙箱**。这类框架（如 Judge0, Piston API 等）通常已经解决了环境配置、资源限制、安全隔离等复杂问题。
        -   **优点**: 安全性高，环境隔离好，易于管理不同语言的依赖，可以方便地限制CPU、内存、执行时间，并且社区成熟，有较多实践案例可供参考。
        -   **实现考量**: 需要调研并选择一个合适的开源 Docker 判题框架，并将其集成到我们的后端服务中。后端服务将负责调用该框架提供的 API 来执行用户代码并获取结果。

2.  **语言选择与执行框架**:
    -   前端界面应提供语言选择器（例如下拉菜单），允许用户指定提交代码的语言。`submissions` 表中的 `language` 字段将记录此选择。
    -   后端根据选择的语言和代码内容，动态构建执行命令。不同语言的执行框架示例：
        -   **Python**: 直接使用 `python script_name.py` 执行。输入参数可以通过命令行参数或 stdin 传递。
        -   **JavaScript (Node.js)**: 使用 `node script_name.js` 执行。输入参数处理方式类似 Python。
        -   **Java**: 需要编译和运行。例如，如果主类是 `Main`，则 `javac Main.java && java Main`。输入参数可以通过 stdin 传递。
        -   **C++**: 需要编译和运行。例如，`g++ main.cpp -o main_executable && ./main_executable`。输入参数可以通过 stdin 传递。
    -   代码文件会临时存储在服务器上（或在沙箱容器内），执行完毕后可删除。

3.  **评测流程**: 
    a.  前端将代码、选择的语言、选定题目的 `problem_id` 发送给后端。
    b.  后端根据 `problem_id` 获取所有 `test_cases`。
    c.  对于每个测试用例：
        i.  根据所选语言，准备执行命令（参考上述“语言选择与执行框架”），并将测试用例的 `input_params` 作为输入（例如，通过 stdin 或将参数写入临时文件供代码读取）。
        ii. 在执行环境中运行代码（参见上面的“代码执行环境与沙箱”部分）。
        iii.捕获 stdout, stderr, exit code, 以及执行时间、内存消耗等（如果可能）。
        iv. 对比实际输出与 `expected_output`。
    d.  汇总所有测试用例的结果，并存储在 `submissions` 表的 `test_results` 字段中。
    e.  在测试用例执行完成后，如果本次操作是由“运行测试并评估”按钮触发，则自动进行大模型代码审查。
    f.  返回结果给前端。

4.  **按钮状态**: “运行测试并评估”按钮在执行期间应为禁用状态。

### 5.5. 大模型代码审查 (DeepSeek API)

1.  **触发**: 通过点击“运行测试并评估”按钮，在运行测试用例完成后自动触发。
2.  **API Key**: 后端从 `settings` 表获取用户配置的 DeepSeek API Key。
3.  **Prompt 构建**: 使用 `problems` 表中存储的 `llm_prompt` 模板，结合用户代码、题目信息以及**测试用例的运行结果**，构建发送给 DeepSeek API 的 Prompt。
4.  **API 调用**: 后端向 DeepSeek API 发送请求，并指定使用流式响应 (streaming)。
5.  **流式处理**: 
    a.  后端接收到 API 的流式数据块 (chunks)。
    b.  通过 Server-Sent Events (SSE) 或 WebSockets 将数据块实时推送到前端。
    c.  前端接收到数据块后，追加到点评显示区域。
6.  **结果存储**: 完整点评内容和评分存入 `submissions` 表。
7.  **按钮状态**: “运行测试并评估”按钮在请求期间应为禁用状态。

### 5.6. 题目导入/导出

-   **导出**: 
    -   后端查询所有 `problems` 及其关联的 `test_cases`。
    -   构建 JSON 结构：`[{ "title": "...
