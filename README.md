# 🎮 MineHost 服务器自动监控系统

一个可部署在 HuggingFace Spaces 的 Docker 应用，自动监控 MineHost Minecraft 服务器状态，当服务器停止时自动启动。

## ✨ 功能特性

- 🔄 **自动监控**：每分钟自动检查服务器状态
- 🚀 **自动启动**：检测到服务器停止时自动发送启动请求
- 🎨 **可视化界面**：现代化的 Web 界面，实时显示服务器状态
- 📊 **统计信息**：显示自动启动次数、最后检查时间等
- 📝 **操作日志**：记录所有操作和事件，保存最近 100 条
- 🔐 **密码保护**：简单的密码认证保护您的控制面板
- ⚙️ **手动控制**：支持手动启动服务器、暂停/恢复自动检查
- 🐳 **Docker 部署**：完全容器化，易于部署

## 🚀 快速开始

### 在 HuggingFace Spaces 部署

1. 访问 [HuggingFace Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 选择 **Docker** 作为 Space SDK
4. 上传本项目的所有文件
5. 在 Settings 中配置环境变量（见下方）
6. 等待构建完成，即可访问

### 环境变量配置

在 HuggingFace Spaces 的 Settings → Variables and secrets 中添加以下环境变量：

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `MINEHOST_COOKIE` | ✅ | MineHost 网站的 Cookie（用于启动服务器） | `XXXXXXXX` |
| `MINEHOST_SERVER_ID` | ✅ | 服务器 ID | `XXXXXXXX` |
| `WEB_PASSWORD` | ✅ | 网页访问密码 | `admin`（默认值） |
| `CHECK_INTERVAL` | ✅ | 检查间隔（秒） | `60`（默认值，即 1 分钟） |
| `SECRET_KEY` | ✅ | Flask 密钥 | 随机字符串 |

#### 如何获取 `MINEHOST_COOKIE`？

1. 在浏览器中登录 [MineHost](https://www.minehost.io/)
2. 按 F12 打开开发者工具
3. 切换到 "Network" (网络) 标签
4. 刷新页面
5. 点击任意请求，在 "Headers" 中找到 "Cookie"
6. 复制整个 Cookie 字符串（通常是 `SSESS...=...` 的格式）

**注意**：Cookie 可能会过期，如果发现无法启动服务器，请重新获取 Cookie。

## 🏠 本地运行

### 使用 Docker（推荐）

```bash
# 构建镜像
docker build -t minehost-monitor .

# 运行容器
docker run -d -p 7860:7860 \
  -e MINEHOST_COOKIE="your_cookie_here" \
  -e MINEHOST_SERVER_ID="181408" \
  -e WEB_PASSWORD="your_password" \
  --name minehost-monitor \
  minehost-monitor
```

### 使用 Python

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量（Windows PowerShell）
$env:MINEHOST_COOKIE="your_cookie_here"
$env:MINEHOST_SERVER_ID="181408"
$env:WEB_PASSWORD="your_password"

# 设置环境变量（Linux/Mac）
export MINEHOST_COOKIE="your_cookie_here"
export MINEHOST_SERVER_ID="181408"
export WEB_PASSWORD="your_password"

# 运行应用
python app.py
```

访问 `http://localhost:7860` 即可查看界面。

## 📖 使用说明

### 登录

首次访问会要求输入密码，密码为环境变量 `WEB_PASSWORD` 设置的值（默认：`admin123`）。

### 界面说明

- **服务器状态**：显示当前服务器状态（运行中/已停止/错误）
- **统计信息**：显示自动启动次数和最后检查时间
- **控制面板**：
  - 🚀 手动启动服务器：立即发送启动请求
  - ⏸️ 暂停自动检查：临时停止自动监控
  - 🔄 立即检查状态：手动触发一次状态检查
- **操作日志**：实时显示所有操作和事件

### 工作原理

1. 应用启动后，每隔 `CHECK_INTERVAL` 秒（默认 60 秒）自动检查服务器状态
2. 如果检测到服务器状态为 `stopped`，自动发送启动请求
3. 所有操作都会记录到日志中
4. 网页界面每 5 秒自动刷新一次状态

## 🏗️ 项目结构

```
MineHost-WakeUp/
├── app.py                  # Flask 主应用
├── config.py               # 配置管理
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 配置
├── .dockerignore          # Docker 忽略文件
├── .gitignore             # Git 忽略文件
├── templates/
│   ├── login.html         # 登录页面
│   └── index.html         # 主界面
└── static/
    ├── style.css          # 样式文件
    └── script.js          # 前端脚本
```

## 🛠️ 技术栈

- **后端**：Flask (Python)
- **定时任务**：APScheduler
- **前端**：原生 HTML/CSS/JavaScript
- **部署**：Docker
- **平台**：HuggingFace Spaces

## 🔧 高级配置

### 修改检查间隔

默认每 60 秒检查一次。要修改间隔，设置 `CHECK_INTERVAL` 环境变量（单位：秒）。

例如，改为每 30 秒检查一次：
```bash
CHECK_INTERVAL=30
```

### 修改服务器 ID

如果要监控不同的服务器，修改 `MINEHOST_SERVER_ID` 环境变量：
```bash
MINEHOST_SERVER_ID=your_server_id
```

## ⚠️ 注意事项

1. **Cookie 安全**：不要将 Cookie 暴露在公开的仓库中，务必使用环境变量配置
2. **Cookie 有效期**：MineHost 的 Cookie 可能会过期，如果启动失败，请重新获取
3. **检查频率**：不建议将检查间隔设置得太短，以免给服务器造成压力
4. **网络延迟**：启动请求可能需要一些时间才能生效，请耐心等待

## 🐛 故障排除

### 无法启动服务器

- 检查 `MINEHOST_COOKIE` 是否正确配置
- 检查 Cookie 是否已过期（重新获取）
- 检查服务器 ID 是否正确

### 无法登录

- 检查 `WEB_PASSWORD` 环境变量是否正确
- 尝试使用默认密码 `admin`

### 状态显示错误

- 检查网络连接
- 查看操作日志中的错误信息

## 📝 更新日志

### v1.0.0 (2025-10-30)

- ✨ 初始版本发布
- 🔄 自动监控和启动功能
- 🎨 现代化 Web 界面
- 📝 操作日志系统
- 🐳 Docker 支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

⭐ 如果这个项目对你有帮助，请给个 Star！

