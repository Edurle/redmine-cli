# Redmine CLI

Redmine 命令行管理工具，支持任务、项目、用户和工时管理。

## 安装

```bash
git clone git@github.com:Edurle/redmine-cli.git
cd redmine-cli
conda create -n redmine-cli python=3.12 -y
conda run -n redmine-cli pip install -e .
```

验证安装：
```bash
conda run -n redmine-cli redmine --help
```

## 配置

### 方式一：配置文件（推荐）

```bash
redmine config init
```

编辑 `~/.redmine-cli/config.toml`：

```toml
default_profile = "work"

[profiles.work]
url = "http://your-redmine-server"
api_key = "your-api-key"
```

### 方式二：环境变量

```bash
export REDMINE_URL="http://your-redmine-server"
export REDMINE_API_KEY="your-api-key"
```

### 获取 API Key

1. 登录 Redmine 网页端
2. 进入 **我的帐号**（右上角）
3. 右侧栏找到 **API 访问键**，点击 **显示** 并复制

### 验证连接

```bash
redmine config test
```

## 使用示例

```bash
# 查看分配给我的任务
redmine my-issues

# 查看任务详情
redmine issues show 12345

# 创建任务
redmine issues create -s "任务标题" -p project-id --start-date 2026-04-08

# 更新任务状态
redmine issues update 12345 --status 2 --comment "开始处理"

# 记录工时
redmine time log -i 12345 -h 2.5 -c "完成开发"

# 查看项目列表
redmine projects list

# 查看项目成员
redmine projects members project-identifier

# 查看当前用户
redmine users me

# JSON 输出（适合脚本处理）
redmine my-issues --format json
```

## 所有命令

```
redmine config [show|init|test]        配置管理
redmine my-issues                      我的任务

redmine issues list                    列出任务（支持筛选）
redmine issues show ISSUE_ID           查看任务详情
redmine issues create                  创建任务
redmine issues update ISSUE_ID         更新任务
redmine issues comment ISSUE_ID        添加评论
redmine issues delete ISSUE_ID         删除任务

redmine projects list                  列出项目
redmine projects show PROJECT_ID       查看项目详情
redmine projects members PROJECT_ID    查看项目成员

redmine users me                       当前用户信息

redmine time list                      查看工时记录
redmine time log                       记录工时
redmine time activities                查看活动类型
```

## 开发

```bash
conda run -n redmine-cli pip install -e ".[dev]"
conda run -n redmine-cli pytest           # 运行测试
conda run -n redmine-cli ruff check src/  # 代码检查
```

## 技术栈

- Python 3.12
- [Typer](https://typer.tiangolo.com/) - CLI 框架
- [httpx](https://www.python-httpx.org/) - HTTP 客户端
- [Pydantic](https://docs.pydantic.dev/) - 数据模型
- [Rich](https://rich.readthedocs.io/) - 终端输出
