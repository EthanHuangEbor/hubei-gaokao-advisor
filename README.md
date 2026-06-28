# Hubei Gaokao Advisor

湖北高考志愿冲稳保推荐 MVP，按“院校专业组”口径生成本科普通批平行志愿草表。规则模型负责排序，Doctor.Peak/MiniMax 只负责解释。

## 本地运行

准备依赖：

```powershell
npm install
python -m pip install -e .
```

如果 `npm run api` 没有找到正确的 Python，可先指定：

```powershell
$env:PYTHON="C:\Path\To\python.exe"
```

启动 API 和 Web：

```powershell
npm run api
npm run dev:web
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

`.env.example` 是环境变量清单。当前 API 读取启动进程里的环境变量；在 PowerShell 中请先设置 `$env:...`，再启动 `npm run api`。

## 关键环境变量

MiniMax：

- `MINIMAX_API_KEY`: MiniMax API key，缺失时使用确定性 fallback。
- `MINIMAX_BASE_URL`: 默认 `https://api.minimax.io/v1`。
- `MINIMAX_MODEL`: 默认 `MiniMax-M3`。
- `MINIMAX_API_STYLE`: 默认 `responses`，可改 `chat_completions`。
- `MINIMAX_TIMEOUT_SECONDS`: 默认 `30`。
- `ENABLE_LLM_ADVICE` / `ENABLE_DOCTOR_PEAK`: 本地开关，默认按 `.env.example`。

数据安全：

- `APP_ENV=production`: 生产模式，要求真实审核后的 curated 数据。
- `REQUIRE_REAL_DATA=true`: 严格模式，真实 curated 未就绪时推荐接口返回 `503 real_data_required`。
- `ALLOW_FIXTURE_DATA=true`: 仅本地演示允许 fixture/demo 数据，前端会显示演示数据警告。

## 状态自检

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/api/data/status
curl.exe http://127.0.0.1:8000/api/admin/doctor-peak/status
curl.exe -X POST http://127.0.0.1:8000/api/admin/doctor-peak/test
```

看数据是否可用于真实运行时，以 `/api/data/status` 的 `real_curated_ready` 和 `data_authenticity.dataset_kind` 为准；不要只看 `data/curated/hubei` 里是否有 CSV。

## MiniMax 与 Doctor.Peak

如果状态里显示 `missing_api_key` 或推荐结果里出现 fallback，通常是 API 进程启动时没有读到 `MINIMAX_API_KEY`。修复方式是在启动 API 前设置环境变量并重启 API：

```powershell
$env:MINIMAX_API_KEY="your_key"
npm run api
```

Doctor.Peak 的边界固定：只解释已经排序好的推荐结果，不改变排名，不承诺录取，不接收姓名、身份证号、考生号、手机号等 PII。

## 湖北真实数据工作流

完整流程是：source registry -> download -> parse -> quality -> manual review/approve -> promote -> seed。

```powershell
npm run data:hubei:download
npm run data:hubei:parse
npm run data:hubei:quality
# 人工复核候选 CSV；只有可信行可标记 review_status=approved
npm run data:hubei:promote
npm run db:seed:hubei
```

不用 npm scripts 时的 Python 等价命令：

```powershell
python -m services.data.hubei.build_dataset --download
python -m services.data.hubei.build_dataset --parse
python -m services.data.hubei.build_dataset --quality
python -m services.data.hubei.build_dataset --promote
python -m services.data.hubei.seed_db --curated-dir data/curated/hubei
```

当前项目允许本地 fixture/demo 回退，但 production 或 `REQUIRE_REAL_DATA=true` 会拒绝 fixture-backed 推荐。官方原始图片/PDF/HTML 只保留在本地或构建工件中；可提交的运行时数据是审核后的 curated CSV。

更多细节见：

- `docs/operations/minimax-and-data.md`
- `data/curated/hubei/README.md`
- `docs/minimax-integration.md`
- `docs/crawler-policy.md`
- `docs/data-quality-rules.md`

## Docker Compose

```powershell
docker compose up --build
```

## 质量检查

```powershell
npm run test:py
npm run lint:py
npm run typecheck:py
npm run lint:web
npm run build:web
npm run test:e2e
```

Playwright E2E 会在需要时启动本地 FastAPI 服务和 Next.js dev server。
