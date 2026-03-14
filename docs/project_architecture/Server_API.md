# Roadbook Server API Specification (v1)

本文档定义了路书 CLI 与闭源服务端之间的通信契约。

## 1. 认证 (Authentication)

CLI 使用 API Key 或 OAuth Token 进行认证。Token 应包含在请求头中。

**Header:**
`Authorization: Bearer <token>`

### 1.1 登录 (Device Flow / API Key)

*   **Endpoint**: `POST /api/v1/auth/login`
*   **Request**:
    ```json
    {
      "method": "api_key",
      "key": "sk-..."
    }
    ```
*   **Response**:
    ```json
    {
      "token": "jwt_token_...",
      "expires_in": 3600,
      "user": {
        "id": "u123",
        "username": "roadbook_dev"
      }
    }
    ```

### 1.2 用户信息

*   **Endpoint**: `GET /api/v1/auth/me`
*   **Response**:
    ```json
    {
      "id": "u123",
      "username": "roadbook_dev",
      "quota": {
        "remaining": 1000
      }
    }
    ```

## 2. 路书库 (Registry)

### 2.1 搜索路书

*   **Endpoint**: `GET /api/v1/roadbooks`
*   **Query Params**:
    *   `q`: 搜索关键词
    *   `limit`: 数量限制 (default: 10)
*   **Response**:
    ```json
    {
      "items": [
        {
          "id": "rb-amazon-v1",
          "name": "Amazon Checkout",
          "description": "Search and buy on Amazon",
          "version": "1.0.0",
          "author": "official",
          "updated_at": "2024-03-13T10:00:00Z"
        }
      ],
      "total": 1
    }
    ```

### 2.2 获取路书元数据

*   **Endpoint**: `GET /api/v1/roadbooks/{id}`
*   **Response**:
    ```json
    {
      "id": "rb-amazon-v1",
      "name": "Amazon Checkout",
      "versions": ["1.0.0", "0.9.0"],
      "latest_version": "1.0.0",
      "readme_url": "https://cdn.roadbook.ai/..."
    }
    ```

### 2.3 下载路书包

*   **Endpoint**: `GET /api/v1/roadbooks/{id}/download`
*   **Query Params**:
    *   `version`: 版本号 (Optional, default: latest)
*   **Response**:
    *   Content-Type: `application/zip`
    *   Body: Binary Zip File (包含 `roadbook.md`, `meta.yaml` 等)

### 2.4 发布路书

*   **Endpoint**: `POST /api/v1/roadbooks`
*   **Content-Type**: `multipart/form-data`
*   **Body**:
    *   `file`: roadbook.zip
    *   `meta`: JSON string (optional)
*   **Response**:
    ```json
    {
      "id": "rb-my-new-book",
      "version": "0.0.1",
      "status": "published"
    }
    ```

## 3. 运行时遥测 (Telemetry) - Optional

*   **Endpoint**: `POST /api/v1/telemetry/runs`
*   **Request**:
    ```json
    {
      "roadbook_id": "rb-amazon-v1",
      "run_id": "run_123",
      "status": "success",
      "duration_ms": 1500,
      "error": null
    }
    ```
*   **Response**: 201 Created

## 4. 错误码规范

*   `401 Unauthorized`: 未登录或 Token 过期
*   `403 Forbidden`: 无权访问该路书
*   `404 Not Found`: 路书不存在
*   `409 Conflict`: 版本冲突 (Push 时)
*   `429 Too Many Requests`: 限流
