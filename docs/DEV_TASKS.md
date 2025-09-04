# 📋 开发任务单（MVP）— 家庭壁挂日历

## 0. 目标
- 实现壁挂周视图（Mon–Sun，默认 08:00–22:00，必要时扩展），按孩子分轨展示。  
- 提供统一事件添加接口（API + 表单 + CSV/ICS 导入）。  
- 壁挂端 ≤10s 内自动刷新。  

---

## 1. 技术栈
- 后端：Python FastAPI + SQLAlchemy 2.x + Pydantic v2  
- DB：PostgreSQL 16（主存储），Redis 7（可选 SSE 推送）  
- 工具：python-dateutil（RRULE/EXDATE 展开）  
- 前端：HTML/CSS/JS（响应式，后续可升级为 PWA）  
- 容器：Docker + docker-compose  

---

## 2. 数据模型

**Kid**
- id, name, color, avatar  

**Event**
- id, title, location  
- startUtc, endUtc  
- rrule (text, RFC5545)  
- exdates (jsonb[], ISO 日期/时间)  
- kidIds (jsonb[])  
- category (school/after-school/family)  
- source (manual/ics/google/outlook)  
- createdBy, updatedAt  

**索引**
- (startUtc, endUtc)  
- GIN kidIds  

---

## 3. RRULE 支持矩阵
- ✅ FREQ=DAILY/WEEKLY/MONTHLY  
- ✅ INTERVAL / BYDAY (MO–SU) / UNTIL / COUNT / EXDATE  
- ❌ 不支持 BYSETPOS、BYYEARDAY 等复杂项  
- 存储统一 UTC；按本地时区展开  

---

## 4. API 契约

### 4.1 查询事件
`GET /v1/events?start&end[&kidId]`  
- 展开 RRULE/EXDATE，返回实例化数组。  

### 4.2 创建事件
`POST /v1/events`  
Headers: `Idempotency-Key` 可选  
Body 示例：
```json
{
  "title": "钢琴课",
  "startUtc": "2025-09-02T08:00:00Z",
  "endUtc": "2025-09-02T09:00:00Z",
  "kidIds": ["kid-ming"],
  "category": "after-school",
  "rrule": "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z",
  "exdates": ["2025-10-01"],
  "source": "manual"
}
```

### 4.3 更新/删除
- `PATCH /v1/events/{id}`  
- `DELETE /v1/events/{id}`  

### 4.4 孩子管理
- `GET /v1/kids`  
- `POST /v1/kids`  

### 4.5 导入
- `POST /v1/import/csv`（multipart，含标题、时间、kidIds 等）  
- `POST /v1/import/ics`（解析 VEVENT → 调用 /v1/events）  

### 4.6 SSE 推送
- `GET /v1/events/stream`（服务端推送版本号，壁挂端收到后刷新）  

---

## 5. 前端要求（wall.html）
- 网格：7 列（Mon–Sun）× 时间轴；左侧时间刻度。  
- 默认 08:00–22:00；如有越界事件，自动扩展到最近整点（最小 06:00，最大 24:00）。  
- 分轨：孩子不同颜色，重叠事件并排/错层。  
- 字体：全局 `clamp(14px, 2vw, 24px)`；事件卡 `clamp(12px, 1.2vw, 18px)`。  
- 顶部按钮：今天/上周/下周。  
- 状态：无事件显示提示；断网显示缓存+“上次更新 HH:mm”。  
- 实时：优先 SSE，失败回退 5–10min 轮询。  

---

## 6. 样例数据

**Kids**
```json
[
  {"id":"kid-ming","name":"小明","color":"#4f46e5"},
  {"id":"kid-hong","name":"小红","color":"#ef4444"}
]
```

**Events**
```json
[
  {
    "id":"ev_piano",
    "title":"钢琴课",
    "location":"艺术中心302",
    "startUtc":"2025-09-02T08:00:00Z",
    "endUtc":"2025-09-02T09:00:00Z",
    "rrule":"FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z",
    "exdates":["2025-10-01"],
    "kidIds":["kid-ming"],
    "category":"after-school",
    "source":"manual"
  }
]
```

---

## 7. 验收标准
- ✅ 周视图正确渲染（含超时段扩展）。  
- ✅ RRULE/EXDATE 展开正确。  
- ✅ 性能：500 实例内响应 ≤150ms，渲染 ≤1s。  
- ✅ 刷新延迟 ≤10s（SSE）或 ≤10min（轮询）。  
- ✅ 断网显示缓存，联网自动更新。  
- ✅ 2–3 米远可读。  

---

## 8. 部署（Docker）
- `docker compose build`  
- `docker compose up -d`  
- 可选：`docker exec -it familycal_app python -m server.seed`  
- 访问：`http://<宿主机IP>:8000/wall`（平板添加到主屏幕）

---

## 9. Stretch 目标
- PWA（manifest.json + service-worker.js，离线可看）。  
- 反代 + HTTPS（Caddy/Traefik）。  
- 简易管理后台（admin.html）。  
- OpenAPI 文档自动生成。  
