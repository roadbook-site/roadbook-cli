# Roadbook Server Handoff 文档

**日期**: 2026-03-15
**作者**: Trae AI Pair Programmer
**状态**: 基础架构已完成，数据库已连接，DAO层已就绪

本文档旨在总结 Roadbook Server 目前的开发进度、已完成的工作、测试方法以及下一步的待办事项，方便后续开发人员接手推进。

---

## 1. 项目概况与架构

### 1.1 核心架构
*   **Web 框架**: FastAPI (Python)
*   **数据库**: PostgreSQL 16 (运行于 Docker)
*   **向量扩展**: `pgvector` (已启用，用于支持 RAG)
*   **ORM**: SQLAlchemy (AsyncIO) + Alembic (待配置迁移)
*   **部署环境**:
    *   Server: 本地 Windows 开发环境 (端口 8090)
    *   Database: 远程服务器 `small` (192.168.0.106) 上的 Docker 容器

### 1.2 目录结构关键点
*   `server/app/core/`: 核心配置 (Config, Database Connection)
*   `server/app/models/`: SQLAlchemy 数据模型 (Roadbook, User)
*   `server/app/schemas/`: Pydantic 数据验证模型
*   `server/app/crud/`: 数据访问层 (DAO)，封装了数据库操作
*   `server/app/api/`: API 路由定义

---

## 2. 已完成工作 (Completed Work)

### 2.1 数据库建设
*   **远程部署**: 在 `small` 机器上通过 Docker 部署了 PostgreSQL 数据库，并映射端口 5432。
*   **pgvector 支持**: 数据库已安装并启用 `pgvector` 扩展，`Roadbook` 模型中已添加 `embedding` 字段 (Vector(1536))。
*   **连接配置**: 服务端 `.env` 已更新为连接远程数据库。
*   **密码哈希**: 引入 `argon2-cffi` 替代 `bcrypt`，解决了 Windows 下 `passlib` 的兼容性问题。

### 2.2 服务端开发
*   **基础 CRUD**: 实现了通用的 `CRUDBase` 类，减少了重复代码。
*   **业务 DAO**:
    *   `CRUDRoadbook`: 支持路书的增删改查。
    *   `CRUDUser`: 支持用户的创建（自动哈希密码）和查询。
*   **API 接口**:
    *   `GET /api/v1/roadbooks/`: 获取路书列表
    *   `POST /api/v1/roadbooks/`: 创建/更新路书元数据
    *   `POST /api/v1/roadbooks/{id}/content`: 上传路书内容包 (zip)
    *   `GET /api/v1/roadbooks/{id}/content`: 下载路书内容包
*   **初始化脚本**: 编写了 `server/scripts/init_db.py`，用于创建初始管理员用户。

### 2.3 客户端集成
*   **CLI 命令**:
    *   `roadbook remote list`: 列出远程路书。
    *   `roadbook push <id>`: 将本地路书打包 (zip) 并推送至服务器。
    *   `roadbook pull <id>`: 从服务器拉取路书并解压到本地。
*   **配置管理**: 客户端支持配置 `server_url` 和 `token` (目前 token 尚未完全验证)。

---

## 3. 测试指南 (How to Test)

### 3.1 启动服务端
在 `server` 目录下运行：
```powershell
# 激活虚拟环境 (如果未激活)
# .venv\Scripts\Activate.ps1

# 启动服务器 (端口 8090)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```
*注意：由于之前端口 8000-8003 被僵尸进程占用，目前默认使用 **8090** 端口。*

### 3.2 验证数据库连接与初始化
运行初始化脚本创建管理员用户：
```powershell
python -m scripts.init_db
```
若成功，将输出 `User 'admin' created successfully` 或 `User 'admin' already exists`。

### 3.3 客户端功能测试
在 `client/src` 目录下运行：
```powershell
# 1. 设置临时路书主目录
$env:ROADBOOK_HOME = "c:\code_dev\roadbook\temp_test_home"

# 2. 创建一个测试路书
mkdir -p $env:ROADBOOK_HOME\books\test-book
# 创建 roadbook.md (必须包含 Frontmatter)
Set-Content -Path "$env:ROADBOOK_HOME\books\test-book\roadbook.md" -Value "---\nname: Test Book\nid: test-book\nversion: 1.0\n---\n# Hello" -Encoding UTF8

# 3. 配置服务器地址 (只需运行一次)
python -c "from roadbook.core.config import save_config; save_config({'server_url': 'http://localhost:8090', 'token': 'test-token'})"

# 4. 推送路书
python -m roadbook.cli push test-book

# 5. 查看远程列表
python -m roadbook.cli remote list
```

---

## 4. 未完成事项 (Pending Tasks)

### 4.1 用户认证与授权 (High Priority)
*   **现状**: `Roadbook` 创建接口目前硬编码 `author="admin"`。
*   **待办**:
    *   实现 `/api/v1/auth/login` 接口，验证用户名密码并颁发 JWT Token。
    *   完善 `get_current_user` 依赖项，解析 JWT 并获取当前用户。
    *   在 `create_roadbook` 等接口中替换硬编码的 author，使用当前登录用户 ID。

### 4.2 RAG 与向量检索 (Core Feature)
*   **现状**: 数据库已支持 `vector` 类型，模型已有 `embedding` 字段。
*   **待办**:
    *   集成 OpenAI 或其他 Embedding API。
    *   在路书上传/更新时，自动计算内容的 Embedding 并存入数据库。
    *   实现 `/api/v1/search` 接口，支持基于向量相似度的语义搜索。

### 4.3 数据库迁移 (Maintenance)
*   **现状**: 目前依靠 `Base.metadata.create_all` 在启动时创建表。
*   **待办**:
    *   初始化 Alembic (`alembic init alembic`)。
    *   配置 `alembic.ini` 连接远程数据库。
    *   生成初始迁移脚本，后续通过 Alembic 管理数据库变更。

### 4.4 代码优化
*   **客户端**: 完善 `push` 命令的错误处理（例如服务端返回 401/403 时的提示）。
*   **服务端**: 完善文件上传的大小限制和类型检查。

---

## 5. 相关资源
*   **API 文档**: 启动服务后访问 [http://localhost:8090/docs](http://localhost:8090/docs)
*   **数据库管理**: 可通过 SSH 连接 `small` 机器使用 `docker exec -it roadbook-db psql ...` 管理。
