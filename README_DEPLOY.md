# Codex 控制台部署与 CPA 对接指南

本文档详细介绍了 Codex 系统（注册机）如何与 **CPAMC (CLI Proxy API Management Control)** 进行对接，以及如何配置自动化账号同步流程。

## 1. 快速部署 (注册机端)

### 环境要求
- Python 3.10+
- 建议使用虚拟环境 (`venv` 或 `conda`)

### 安装步骤
1. 克隆仓库并进入目录。
2. 安装依赖：`pip install -r requirements.txt`。
3. 创建 `.env` 文件（可参考 `.env.example`）：
   ```env
   APP_HOST=0.0.0.0
   APP_PORT=1455
   APP_ACCESS_PASSWORD=你的访问密码
   APP_DATABASE_URL=sqlite:///./codex.db
   ```
4. 启动服务：`python webui.py`。
5. 访问 `http://你的IP:1455` 登录后台。

---

## 2. CPA (CPAMC) 对接流程详解

**CPA (Codex Protocol API)** 是一种将注册机产出的账号自动同步到管理平台的协议。通过对接 CPAMC，您可以实现“注册即上线”，无需手动导出导入。

### 第一步：获取 CPAMC 接口信息
CPAMC 运行在 8317 端口（默认），其对接接口为 `/v0/management/auth-files`。

### 第二步：配置 CPA API Token (关键)
> [!IMPORTANT]
> **切勿直接复制配置文件中的密文！**
> 如果 CPAMC 的 `config.yaml` 中 `secret-key` 显示为 `$2a$10$...`，这是哈希后的密文，无法直接使用。

1. **重置明文**：停止 CPAMC 服务，将 `secret-key` 修改为一个简单的明文（如 `Abc123456`）。
2. **重启服务**：CPAMC 启动后会再次加密该字符串，此时您刚才设置的 `Abc123456` 即为有效的 **API Token**。

### 第三步：在控制台添加服务
1. 进入注册机后台 -> **系统设置** -> **上传**。
2. 点击 **“添加服务”**：
   - **名称**：例如 `主力代号-CPAMC`。
   - **API URL**：填入管理端地址，例如 `http://35.223.135.254:8317`。
   - **API Token**：填入您在第二步中设置的**明文密钥**。
3. 点击 **“测试连接”**，显示“连接成功”即可保存。

---

## 3. 自动化任务配置

为了让注册成功的账号自动上传：
1. 发起 **“注册任务”** 或 **“批量注册”** 时。
2. 在任务参数面板中，勾选 **“自动上传到 CPA”**。
3. 您可以在 **“CPA 服务 ID”** 中指定特定的服务，或留空让系统自动选择第一个可用的。

## 4. 故障排查

- **连接成功，但 API Token 无效**：确认填入的是明文密码，而非 `$2a$` 开头的哈希值。
- **401 Unauthorized**：Token 密钥不匹配。
- **404 Not Found**：请检查 API URL 是否正确（确保基础 URL 和端口无误）。
- **投递失败**：检查 CPAMC 是否开启了远程访问：`allow-remote: true`。

---

## 5. 远端同步

完成配置后，请确保执行以下操作以保持代码最新：
```bash
git add .
git commit -m "docs: 补充部署手册与 CPA 对接指南"
git push origin main
```
