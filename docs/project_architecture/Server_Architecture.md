# Roadbook Server Architecture Design

本服务器 (Roadbook Server) 旨在成为所有探险家 (Agents) 的**全球指挥中心 (Global Command Center)**。它不仅是路书的存储库，更是连接分散探险行动的中枢神经。

## 1. 核心隐喻与职责 (Core Metaphor & Responsibilities)

| 组件 | 核心隐喻 | 职责描述 |
| :--- | :--- | :--- |
| **Server** | **Expedition HQ (探险总部)** | 管理所有**探险手记 (Roadbooks)** 的归档、版本控制与分发。它是唯一可信的真理来源 (Single Source of Truth)。 |
| **Registry** | **Archive (档案馆)** | 存储经过验证的路书包。支持按标签、作者、场景进行索引与检索。 |
| **Auth** | **Permit Office (通行证处)** | 核发探险许可 (API Key / Token)。管理探险家身份与权限。 |
| **Telemetry** | **Mission Control (任务监控)** | 接收来自前线 (CLI) 的运行报告。统计路书的成功率、耗时与错误模式，为路书的优化提供数据支持。 |

## 2. 技术栈选型 (Technology Stack)

为了与 CLI (Python) 保持语言一致性，降低维护成本，服务端同样采用 Python 生态。

*   **框架**: **FastAPI** (高性能，原生支持 AsyncIO，自动生成 OpenAPI 文档)。
*   **数据库**: 
    *   **PostgreSQL** (生产环境): 存储元数据、用户信息、运行日志。
        *   **pgvector Extension**: **关键选型理由**。原生支持向量存储与相似度搜索，无需引入额外的向量数据库 (如 Milvus/Pinecone) 即可实现 **RAG (检索增强生成)**。
            *   场景：根据用户意图搜索最匹配的路书。
            *   场景：检索历史报错日志，寻找相似问题的解决方案。
    *   **SQLite** (开发/测试): 轻量级，易于快速启动。
    *   **ORM**: **SQLAlchemy (Async)** + **Alembic** (迁移管理)。
*   **存储**:
    *   **Local Filesystem** (MVP): 直接存储路书 Zip 包。
    *   **S3 Compatible Object Storage** (进阶): MinIO / AWS S3，用于存储大规模路书文件。
*   **认证**: **OAuth2 (Password Flow) + JWT**。支持 API Key 长期访问。
*   **部署**: **Docker + Docker Compose**。

## 3. 系统架构 (System Architecture)

```mermaid
graph TD
    subgraph Client [Client Side]
        CLI[Roadbook CLI]
        Agent[Agent Runtime]
    end

    subgraph Server [Server Side (FastAPI)]
        Gateway[API Gateway / Nginx]
        
        subgraph Services
            AuthService[Auth Service]
            RegistryService[Registry Service]
            TelemetryService[Telemetry Service]
        end
        
        subgraph DataLayer
            DB[(PostgreSQL)]
            Storage[File Storage / S3]
        end
    end

    CLI -->|Login/Pull/Push| Gateway
    Agent -->|Report Telemetry| Gateway
    
    Gateway --> AuthService
    Gateway --> RegistryService
    Gateway --> TelemetryService
    
    AuthService --> DB
    RegistryService --> DB
    RegistryService --> Storage
    TelemetryService --> DB
```

## 4. 模块设计 (Module Design)

### 4.1 目录结构
```text
server/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py       # 登录、注册、Token
│   │   │   ├── roadbooks.py  # 增删改查、上传下载
│   │   │   └── telemetry.py  # 运行日志上报
│   ├── core/
│   │   ├── config.py         # 环境变量配置
│   │   ├── security.py       # JWT, Password Hash
│   │   └── db.py             # 数据库连接
│   ├── models/               # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── roadbook.py
│   │   └── run_log.py
│   ├── schemas/              # Pydantic Schemas (DTO)
│   ├── services/             # 业务逻辑层
│   │   ├── storage.py        # 文件存储抽象
│   │   └── ...
│   └── main.py               # App 入口
├── alembic/                  # 数据库迁移
├── tests/                    # 单元测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### 4.2 核心数据模型 (Database Schema)

*   **Users Table**:
    *   `id`: UUID
    *   `username`: String (Unique)
    *   `email`: String (Unique)
    *   `hashed_password`: String
    *   `is_active`: Boolean
    *   `api_key`: String (Optional, for headless usage)

*   **Roadbooks Table**:
    *   `id`: String (e.g., "rb-amazon-checkout") - Primary Key
    *   `name`: String
    *   `description`: Text
    *   `author_id`: UUID (FK -> Users.id)
    *   `is_public`: Boolean (Default: True)
    *   `created_at`: DateTime
    *   `updated_at`: DateTime

*   **RoadbookVersions Table**:
    *   `id`: Integer (Auto Increment)
    *   `roadbook_id`: String (FK -> Roadbooks.id)
    *   `version`: String (e.g., "1.0.0")
    *   `file_path`: String (Storage path)
    *   `created_at`: DateTime
    *   `changelog`: Text

*   **RunLogs Table** (Telemetry):
    *   `id`: UUID
    *   `user_id`: UUID (FK -> Users.id, nullable)
    *   `roadbook_id`: String (FK -> Roadbooks.id)
    *   `roadbook_version`: String
    *   `status`: Enum (success, failed)
    *   `duration_ms`: Integer
    *   `error_message`: Text (Nullable)
    *   `timestamp`: DateTime

## 5. 交互流程 (Interaction Flows)

### 5.1 发布流程 (Publish)
1.  **CLI**: 用户执行 `roadbook publish .`
2.  **CLI**: 检查 `roadbook.yaml` 中的 `id` 和 `version`。
3.  **CLI**: 将当前目录打包为 `roadbook.zip`。
4.  **CLI**: 发送 `POST /api/v1/roadbooks` (Multipart) 带上 Token。
5.  **Server**: 验证权限 -> 检查版本是否存在 -> 保存文件到 Storage -> 写入 Database -> 返回成功。

### 5.2 安装流程 (Install)
1.  **CLI**: 用户执行 `roadbook install rb-amazon-checkout`。
2.  **CLI**: 发送 `GET /api/v1/roadbooks/rb-amazon-checkout/download`。
3.  **Server**: 返回 Zip 文件流。
4.  **CLI**: 解压至 `~/.roadbook/books/rb-amazon-checkout/`。

### 5.3 搜索流程 (Search)
1.  **CLI**: 用户执行 `roadbook search amazon`。
2.  **CLI**: 发送 `GET /api/v1/roadbooks?q=amazon`。
3.  **Server**: 查询 Database (Like query or Full-text search) -> 返回列表。
4.  **CLI**: 渲染表格展示结果。

## 6. 未来规划 (Future Roadmap)

*   **Web UI**: 提供可视化界面浏览路书、查看统计报表。
*   **RBAC**: 更细粒度的权限控制 (Team/Organization)。
*   **Webhooks**: 路书更新时通知下游系统。
*   **AI Analysis**: 服务端分析失败日志，自动建议路书修复方案。
