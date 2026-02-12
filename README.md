# EHS管理系统（前后端一体）

本项目包含：
- 前端：单页管理界面（首页看板、隐患、特殊作业、异常事件、LOTO、安全连锁、人员管理）
- 后端：Python 标准库 HTTP 服务 + SQLite API（隐患提交/台账、安全连锁申请/台账、首页KPI）

## 一键部署（服务器端）

```bash
chmod +x deploy.sh
./deploy.sh
```

默认监听 `8000` 端口，部署后访问：
- `http://<服务器IP>:8000`

## 本地开发启动

```bash
python app.py
```

## API

- `GET /api/dashboard`
- `GET /api/hazards`
- `POST /api/hazards`
- `GET /api/interlocks`
- `POST /api/interlocks`
