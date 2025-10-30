# 🎮 MineHost 服务器自动监控系统

一个可部署在 HuggingFace Spaces 的 Docker 应用，自动监控 MineHost Minecraft 服务器状态，当服务器停止时自动启动，并提供实时控制台功能。

## ✨ 功能特性

- 🔄 **自动监控**：每分钟自动检查服务器状态
- 🚀 **自动启动**：检测到服务器停止时自动发送启动请求
- 🤖 **机器人挂机**：自动加入服务器的假人机器人，保持服务器在线
- 🖥️ **实时控制台**：通过 WebSocket 实时查看服务器控制台输出
- ⌨️ **命令执行**：直接在网页中发送 Minecraft 服务器命令
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
| `MINEHOST_COOKIE` | ✅ | MineHost 网站的 Cookie（用于启动服务器和发送命令） | `XXXXXXXXXXXXXXX` |
| `MINEHOST_SERVER_ID` | ✅ | 服务器 ID | `XXXXXX` |
| `WEB_PASSWORD` | ❌ | 网页访问密码 | `admin`（默认值） |
| `CHECK_INTERVAL` | ❌ | 检查间隔（秒） | `60`（默认值，即 1 分钟） |
| `SECRET_KEY` | ❌ | Flask 密钥 | 随机字符串 |
| `BOT_USERNAME` | ❌ | 机器人用户名 | `WakeUpBot`（默认值） |
| `BOT_AUTO_JOIN` | ❌ | 机器人自动加入 | `true`（默认值） |

#### 如何获取 `MINEHOST_COOKIE`？

1. 在浏览器中登录 [MineHost](https://www.minehost.io/)
2. 按 F12 打开开发者工具
3. 切换到 "Network" (网络) 标签
4. 刷新页面
5. 点击任意请求，在 "Headers" 中找到 "Cookie"
6. 复制整个 Cookie 字符串（通常是 `SSESS...=...` 的格式）

#### 如何获取 `MINEHOST_SERVER_ID`？

从您的服务器 URL 中获取，例如：
- URL: `https://www.minehost.io/server/XXXXXX/console`
- Server ID: `XXXXXX`

**注意**：Cookie 可能会过期，如果发现无法启动服务器或发送命令，请重新获取 Cookie。

## 🏠 本地运行

### 使用 Docker（推荐）

```bash
# 构建镜像
docker build -t minehost-monitor .

# 运行容器
docker run -d -p 7860:7860 \
  -e MINEHOST_COOKIE="your_cookie_here" \
  -e MINEHOST_SERVER_ID="XXXXXX" \
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
$env:MINEHOST_SERVER_ID="XXXXXX"
$env:WEB_PASSWORD="your_password"

# 设置环境变量（Linux/Mac）
export MINEHOST_COOKIE="your_cookie_here"
export MINEHOST_SERVER_ID="XXXXXX"
export WEB_PASSWORD="your_password"

# 运行应用
python app.py
```

访问 `http://localhost:7860` 即可查看界面。

## 📖 使用说明

### 登录

首次访问会要求输入密码，密码为环境变量 `WEB_PASSWORD` 设置的值（默认：`admin`）。

### 界面说明

#### 1. 服务器状态
- 显示当前服务器状态（运行中/已停止/错误）
- 显示服务器 IP 地址

#### 2. 统计信息
- 自动启动次数
- 最后检查时间

#### 3. 控制面板
- 🚀 **手动启动服务器**：立即发送启动请求
- ⏸️ **暂停自动检查**：临时停止自动监控
- 🔄 **立即检查状态**：手动触发一次状态检查

#### 4. 机器人控制 ⭐ 新功能
- **状态显示**：显示机器人在线/离线/连接中状态
- **手动控制**：
  - ▶️ **加入服务器**：手动让机器人加入服务器
  - ⏹️ **离开服务器**：让机器人离开服务器
  - 🔄 **自动加入开关**：切换服务器启动后自动加入功能
- **自动加入**：服务器启动后，机器人自动加入并保持在线
- **自动重连**：如果连接断开，自动尝试重连（最多 3 次）
- **离线模式**：支持离线（盗版）服务器，无需正版账号

#### 5. 服务器控制台
- **实时日志显示**：当服务器运行时，自动连接并显示控制台输出
- **命令执行**：在输入框中输入 Minecraft 命令（如 `list`, `help`, `stop`, `op <player>` 等）
- **连接状态**：显示控制台连接状态（已连接/未连接/连接中）
- **自动重连**：如果连接断开，会自动尝试重新连接
- **终端风格**：黑色背景，绿色文字，模拟真实终端体验

#### 6. 操作日志
- 实时显示所有操作和事件
- 不同级别的日志用不同颜色标识

### 机器人使用说明

机器人功能允许您在服务器中放置一个假人（机器人），保持服务器在线状态。

**特点**：
- 使用离线模式连接，无需正版 Minecraft 账号
- 自定义机器人用户名（默认：`WakeUpBot`）
- 服务器启动后自动加入（可关闭）
- 连接断开后自动重连
- 实时显示机器人状态

**使用方法**：
1. 确保服务器处于运行状态
2. 点击"▶️ 加入服务器"按钮，机器人将连接到服务器
3. 机器人成功加入后，状态会显示为"在线"
4. 如果启用"自动加入"，服务器启动后机器人会自动加入
5. 点击"⏹️ 离开服务器"可以让机器人断开连接

**注意事项**：
- 机器人仅支持离线模式服务器
- 如果服务器是正版验证，机器人将无法加入
- 机器人会在服务器停止时自动断开连接
- 可以在环境变量中自定义机器人用户名

### 控制台使用示例

当服务器运行时，控制台会自动连接。您可以输入以下常用命令：

```
list                    # 查看在线玩家列表
help                    # 查看所有可用命令
op <玩家名>             # 给玩家管理员权限
deop <玩家名>           # 取消玩家管理员权限
gamemode creative <玩家名>  # 切换游戏模式
time set day            # 设置时间为白天
weather clear           # 设置天气为晴天
say <消息>              # 向所有玩家发送消息
kick <玩家名>           # 踢出玩家
ban <玩家名>            # 封禁玩家
stop                    # 停止服务器
```

### 工作原理

#### 自动监控
1. 应用启动后，每隔 `CHECK_INTERVAL` 秒（默认 60 秒）自动检查服务器状态
2. 如果检测到服务器状态为 `stopped`，自动发送启动请求
3. 所有操作都会记录到日志中

#### 控制台连接
1. 当检测到服务器状态变为 `running` 时，自动连接控制台
2. 通过 WebSocket 连接到 `wss://logs.minehost.io/`，实时接收服务器日志
3. 当服务器停止时，自动断开控制台连接
4. 如果连接意外断开，会在 5 秒后自动重连

#### 命令执行
1. 用户在控制台输入框输入命令
2. 前端发送到后端 API `/api/console-command`
3. 后端构造完整的 HTTP 请求发送到 MineHost API
4. 命令执行结果会通过 WebSocket 显示在控制台中

## 🏗️ 项目结构

```
MineHost-WakeUp/
├── app.py                  # Flask 主应用（包含控制台 API）
├── config.py               # 配置管理
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 配置
├── .dockerignore          # Docker 忽略文件
├── .gitignore             # Git 忽略文件
├── templates/
│   ├── login.html         # 登录页面
│   └── index.html         # 主界面（包含控制台）
└── static/
    ├── style.css          # 样式文件（包含控制台样式）
    └── script.js          # 前端脚本（包含 WebSocket 逻辑）
```

## 🛠️ 技术栈

- **后端**：Flask (Python)
- **定时任务**：APScheduler
- **实时通信**：WebSocket
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
2. **Cookie 有效期**：MineHost 的 Cookie 可能会过期，如果启动或命令执行失败，请重新获取
3. **检查频率**：不建议将检查间隔设置得太短，以免给服务器造成压力
4. **网络延迟**：启动请求和命令执行可能需要一些时间才能生效，请耐心等待
5. **控制台权限**：某些命令可能需要管理员权限才能执行
6. **WebSocket 连接**：控制台功能需要稳定的网络连接
7. **机器人限制**：机器人仅支持离线模式（盗版）服务器，正版服务器需要微软账号认证
8. **服务器白名单**：如果服务器开启了白名单，需要先将机器人用户名添加到白名单

## 🐛 故障排除

### 无法启动服务器

- 检查 `MINEHOST_COOKIE` 是否正确配置
- 检查 Cookie 是否已过期（重新获取）
- 检查 `MINEHOST_SERVER_ID` 是否正确

### 无法登录

- 检查 `WEB_PASSWORD` 环境变量是否正确
- 尝试使用默认密码 `admin`

### 控制台无法连接

- 确认服务器状态为"运行中"
- 检查网络连接是否稳定
- 查看操作日志中的错误信息
- 确认 Cookie 是否有效

### 命令发送失败

- 检查 `MINEHOST_COOKIE` 是否有效
- 确认命令格式正确
- 查看控制台错误信息

### 机器人无法加入

- 确认服务器是离线模式
- 检查服务器地址是否正确
- 查看操作日志中的错误信息
- 如果服务器开启白名单，先添加机器人用户名
- 检查服务器是否允许新玩家加入

### 状态显示错误

- 检查网络连接
- 查看操作日志中的错误信息

## 📝 更新日志

### v3.0.0 (2025-10-30)

- ✨ **新增**：Minecraft 机器人挂机功能
- ✨ **新增**：自动加入服务器保持在线
- ✨ **新增**：机器人状态监控和控制
- ✨ **新增**：支持离线模式服务器
- 🔧 **改进**：自动重连机制（最多 3 次）
- 🔧 **改进**：服务器启动后延迟加入
- 🤖 **配置**：可自定义机器人用户名
- 🤖 **配置**：可开关自动加入功能

### v2.0.0 (2025-10-30)

- ✨ **新增**：实时服务器控制台功能
- ✨ **新增**：通过 WebSocket 实时查看服务器日志
- ✨ **新增**：在线执行 Minecraft 命令
- ✨ **新增**：终端风格的控制台界面
- 🔧 **改进**：优化了状态检查逻辑
- 🔧 **改进**：添加了自动重连机制

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

