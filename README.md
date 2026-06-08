# 今天吃啥（飞书版）

一个帮助你和团队解决「今天吃什么」世纪难题的小应用。通过飞书机器人实现随机抽餐厅功能。

## 功能特性

- 🍜 **随机抽取**：在飞书中发送「吃啥」「抽签」「抽奖」等关键词，机器人随机推荐一家餐厅
- 📋 **餐厅管理**：支持通过 API 添加、编辑、删除餐厅
- 🗳️ **投票功能**：支持为餐厅投票，查看热门餐厅
- 📊 **抽奖记录**：记录每次抽奖结果，查看历史
- 🎴 **飞书卡片**：精美的交互式卡片展示结果

## 项目结构

```
backend/
├── app/
│   ├── main.py                  # FastAPI 主入口
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   ├── models.py                # SQLAlchemy ORM 模型
│   ├── schemas.py               # Pydantic 数据模型
│   ├── repo/                    # 数据访问层
│   │   ├── restaurant_repo.py
│   │   ├── vote_repo.py
│   │   └── lottery_repo.py
│   ├── service/                 # 业务逻辑层
│   │   ├── restaurant_service.py
│   │   ├── vote_service.py
│   │   └── lottery_service.py
│   └── router/                  # 路由层
│       ├── restaurant_router.py
│       ├── vote_router.py
│       ├── lottery_router.py
│       └── feishu_router.py
├── alembic/                     # 数据库迁移
├── seed_data.py                 # 初始化数据脚本
├── requirements.txt             # Python 依赖
└── .env                         # 环境变量
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

修改 `.env` 文件中的飞书应用配置：

```
DATABASE_URL=sqlite:///./jintianchisha.db
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_VERIFICATION_TOKEN=your_verification_token
FEISHU_ENCRYPT_KEY=your_encrypt_key
```

### 3. 初始化种子数据

```bash
python seed_data.py
```

### 4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 `http://localhost:8000/docs` 查看 API 文档。

### 5. 配置飞书 Webhook

在飞书开发者后台配置消息推送地址：

```
POST http://your-server:8000/api/feishu/webhook
```

## 飞书机器人使用指南

在飞书群中或私聊机器人时，可以使用以下关键词：

| 关键词 | 功能 |
|-------|------|
| 吃啥 / 抽签 / 随便 / 抽奖 / 抽 | 随机抽取一家餐厅 |
| 列表 / 餐厅 / 菜单 | 查看所有餐厅 |
| 帮助 / help / ? | 获取使用指南 |

## API 接口

### 餐厅管理
- `GET /api/restaurants` - 获取餐厅列表
- `GET /api/restaurants/{id}` - 获取单个餐厅
- `POST /api/restaurants` - 新增餐厅
- `PUT /api/restaurants/{id}` - 更新餐厅
- `DELETE /api/restaurants/{id}` - 删除餐厅

### 投票
- `POST /api/votes` - 投票
- `GET /api/votes/user/{user_id}` - 查看用户投票记录
- `GET /api/votes/top` - 热门餐厅排行

### 抽奖
- `POST /api/lottery/draw` - 抽取餐厅
- `GET /api/lottery/history` - 抽奖历史

### 飞书
- `POST /api/feishu/webhook` - 飞书消息回调
- `POST /api/feishu/events` - 飞书事件回调
