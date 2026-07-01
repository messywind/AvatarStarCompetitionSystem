# 百变兵团选花杯 · 报名系统

游戏战队报名与赛事对阵系统。技术栈：**Vue 3 + Vite**（前端）、**FastAPI**（后端）、**MySQL**（数据库）。

## 功能概览

三个前端入口 + 两类用户（普通用户 / 管理员），账号需注册。

| 模块 | 路由 | 权限 | 说明 |
| --- | --- | --- | --- |
| 首页 | `/` | 公开 | 赛事介绍、规则说明 |
| 报名端 | `/signup` | 登录用户 | 提交战队报名、查看/撤回自己的战队 |
| 赛事浏览端 | `/browse` | 公开（无需登录） | 展示已审核通过的战队 + 对阵图晋级情况 |
| 管理端 | `/admin` | 管理员 | 浏览/编辑/删除/审核所有战队、配置对阵图 |
| 登录 / 注册 | `/login` `/register` | 公开 | 账号注册与登录 |

### 报名表单与校验规则
- 字段：**队伍名称、队长、参赛选手称呼及职业、替补、作战宣言**
- 职业四种：**生化 / 突击 / 护卫 / 重装**
- 校验（前端实时提示 + 后端强制）：
  - 正式队员**严格 5 人**
  - 每种职业**至少 1 人、至多 2 人**（即 2+1+1+1）
  - 替补**数量不限**
- 提交后状态为「审核中」，管理员通过后才出现在浏览端。

### 对阵图
管理端可按已通过的战队**自动生成 16/8/4/2 强骨架**，或手动增删轮次与对局、指定每局胜者；浏览端以电竞风格对阵图展示晋级情况（胜者高亮）。

---

## 运行方式

## Docker 部署

服务器安装好 Docker 和 Docker Compose 后，可以用这一套命令部署：

```bash
git clone git@github.com:messywind/AvatarStarCompetitionSystem.git
cd AvatarStarCompetitionSystem

cp .env.production.example .env
nano .env

docker compose up -d --build
```

`.env` 里至少要改这些值：

```bash
MYSQL_ROOT_PASSWORD=一个强 root 密码
DB_PASSWORD=一个强数据库用户密码
SECRET_KEY=一长串随机密钥
ADMIN_PASSWORD=管理员初始密码
HTTP_PORT=39217
VITE_BASE_PATH=/avatarstar/
CORS_ORIGINS=http://服务器IP或域名:39217
```

启动后访问：

- 前端：`http://服务器IP:39217/avatarstar/`
- 健康检查：`http://服务器IP:39217/avatarstar/api/health`
- API 文档：`http://服务器IP:39217/avatarstar/docs`

如果使用 IP `45.202.249.207`，则 `.env` 中可设置：

```bash
HTTP_PORT=39217
VITE_BASE_PATH=/avatarstar/
CORS_ORIGINS=http://45.202.249.207:39217
```

注意：`CORS_ORIGINS` 只能写 `协议 + IP/域名 + 端口`，不要写 `/avatarstar`。

常用运维命令：

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f mysql
docker compose down
docker compose down -v  # 会删除 MySQL 数据，谨慎使用
```

MySQL 数据保存在 Docker volume `avatarstarcompetitionsystem_mysql_data` 中，正常 `docker compose down` 不会删库。

### 1. 准备 MySQL
需要一个可连接的 MySQL 服务（8.0+）。数据库会在后端启动时自动创建，无需手动建库。

本机未安装 MySQL 时，任选其一：
```bash
# Homebrew
brew install mysql && brew services start mysql
# 或 Docker
docker run -d --name avatarstar-mysql -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=avatarstar mysql:8
```

### 2. 后端（FastAPI）
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # 按需修改数据库账号密码 / SECRET_KEY
python -m uvicorn app.main:app --reload --port 8000
```
- 启动时自动：创建数据库与数据表、创建管理员账号（默认 `admin` / `admin123`，见 `.env`）。
- API 文档：http://127.0.0.1:8000/docs
- （可选）灌入演示战队：`python seed.py`

### 3. 前端（Vue 3）
```bash
cd frontend
npm install
npm run dev
```
打开 http://localhost:5173 。开发服务器已把 `/api` 代理到 `http://127.0.0.1:8000`。

### 默认账号
| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 普通用户 | 自行注册 | — |

---

## 项目结构
```
backend/
  app/
    main.py            # 应用入口、CORS、启动初始化、管理员引导
    config.py          # 环境配置（.env）
    database.py        # SQLAlchemy 引擎/会话、自动建库
    models.py          # User / Team / Player / Setting 模型
    schemas.py         # Pydantic 校验（含阵容规则）
    auth.py deps.py     # JWT、密码哈希、权限依赖
    routers/
      auth.py          # 注册 / 登录 / me
      teams.py         # 用户提交/查看/撤回战队
      admin.py         # 管理员 CRUD、审核、对阵图配置
      public.py        # 公开的已审核战队 + 对阵图
  seed.py              # 演示数据
frontend/
  src/
    views/             # Home / Login / Register / SignUp / Browse / Admin
    components/        # RosterEditor（阵容编辑）/ Bracket（对阵图）
    stores/auth.js     # Pinia 登录态
    api/index.js       # axios 实例 + token 拦截器
    roster.js          # 前端阵容校验规则
```

## API 一览
| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 公开 | 注册 |
| POST | `/api/auth/login` | 公开 | 登录 |
| GET | `/api/auth/me` | 登录 | 当前用户 |
| POST | `/api/teams` | 登录 | 提交战队 |
| GET | `/api/teams/mine` | 登录 | 我的战队 |
| DELETE | `/api/teams/{id}` | 本人/管理员 | 撤回/删除 |
| GET | `/api/admin/teams` | 管理员 | 全部战队（可按状态筛选） |
| PUT | `/api/admin/teams/{id}` | 管理员 | 编辑战队 |
| PATCH | `/api/admin/teams/{id}/review` | 管理员 | 审核 |
| DELETE | `/api/admin/teams/{id}` | 管理员 | 删除 |
| GET/PUT | `/api/admin/bracket` | 管理员 | 读取/保存对阵图 |
| GET | `/api/public/teams` | 公开 | 已通过审核的战队 |
| GET | `/api/public/bracket` | 公开 | 对阵图 + 战队名映射 |
