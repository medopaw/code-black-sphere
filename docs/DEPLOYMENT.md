# 部署指南

本文档提供了在线判题工具的部署说明。

## 系统要求

- Docker 20.10.0 或更高版本
- Docker Compose 2.0.0 或更高版本
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

## 部署步骤

1. 克隆代码仓库：
   ```bash
   git clone <repository-url>
   cd code-black-sphere
   ```

2. 配置环境变量：
   - 复制 `.env.example` 到 `.env`
   - 根据需要修改环境变量

3. 构建和启动服务：
   ```bash
   docker-compose up -d
   ```

4. 初始化数据库：
   ```bash
   docker-compose exec backend flask db upgrade
   ```

5. 访问应用：
   - 前端：http://localhost
   - 后端 API：http://localhost:5000

## 环境变量配置

在 `.env` 文件中配置以下环境变量：

- `FLASK_APP`: Flask 应用名称
- `FLASK_ENV`: 环境（development/production）
- `DATABASE_URL`: 数据库连接 URL
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥

## 维护说明

### 更新应用

1. 拉取最新代码：
   ```bash
   git pull
   ```

2. 重新构建和启动服务：
   ```bash
   docker-compose up -d --build
   ```

### 查看日志

```bash
# 查看所有服务的日志
docker-compose logs

# 查看特定服务的日志
docker-compose logs frontend
docker-compose logs backend
```

### 备份数据

数据库文件位于 `instance/app.db`，建议定期备份此文件。

## 故障排除

1. 如果服务无法启动，检查日志：
   ```bash
   docker-compose logs
   ```

2. 如果数据库连接失败：
   - 检查数据库文件权限
   - 确保数据库文件未被锁定

3. 如果前端无法访问后端 API：
   - 检查 Nginx 配置
   - 确保后端服务正常运行

## 安全注意事项

1. 生产环境部署时：
   - 修改默认端口
   - 配置 SSL/TLS
   - 设置强密码
   - 限制数据库访问

2. 定期更新：
   - 更新 Docker 镜像
   - 更新依赖包
   - 更新系统补丁 
