# MiniMax 与真实湖北数据运维手册

本文面向本地开发、演示环境和上线前数据准备。代码排序由规则模型完成，Doctor.Peak/MiniMax 只输出解释 JSON。

## 本地运行与配置

安装依赖：

```powershell
npm install
python -m pip install -e .
```

启动服务：

```powershell
npm run api
npm run dev:web
```

如果 API 端口不是默认值，Web 启动前设置：

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
```

MiniMax 环境变量必须在 API 进程启动前可见：

```powershell
$env:MINIMAX_API_KEY="your_key"
$env:MINIMAX_BASE_URL="https://api.minimax.io/v1"
$env:MINIMAX_MODEL="MiniMax-M3"
$env:MINIMAX_API_STYLE="responses"
$env:MINIMAX_TIMEOUT_SECONDS="30"
npm run api
```

数据模式变量：

```powershell
$env:APP_ENV="development"
$env:ALLOW_FIXTURE_DATA="true"
$env:REQUIRE_REAL_DATA="false"
```

上线或严格验收时：

```powershell
$env:APP_ENV="production"
$env:REQUIRE_REAL_DATA="true"
```

验证端点：

```powershell
curl.exe http://127.0.0.1:8000/api/data/status
curl.exe http://127.0.0.1:8000/api/admin/doctor-peak/status
curl.exe -X POST http://127.0.0.1:8000/api/admin/doctor-peak/test
```

`/api/data/status` 应重点看 `real_curated_ready`、`data_authenticity.dataset_kind`、`contains_fixture_rows`、`fixture_marker_count`。`/api/admin/doctor-peak/status` 应重点看 `minimax.configured`、`masked_api_key`、`model`、`endpoint_style` 和 `latest_call.error_code`。

## MiniMax fallback 说明

`fallback` 或 `missing_api_key` 不代表排序失败。它表示 MiniMax 没有成功产出解释，系统会使用确定性 JSON fallback 保持页面可用，且不改变推荐排名。

常见原因：

- API 启动时没有 `MINIMAX_API_KEY`。
- 只改了 `.env` 文件，但当前 API 进程没有加载或重启。
- 在另一个 PowerShell 窗口设置了环境变量。
- `MINIMAX_BASE_URL`、`MINIMAX_MODEL` 或 `MINIMAX_API_STYLE` 与供应商配置不一致。
- 网络超时、代理拦截或 MiniMax 返回 401/403/5xx。

修复步骤：

1. 在启动 API 的同一个 shell 中设置 `MINIMAX_API_KEY`。
2. 重启 `npm run api`。
3. 打开 `/api/admin/doctor-peak/status`，确认 `configured=true` 且 key 只显示掩码。
4. 调用 `/api/admin/doctor-peak/test`。该探针只发送省份、年份、科类、分数/位次区间和样例推荐项，不发送姓名、手机号、身份证号、考生号或其他 PII。

Doctor.Peak 永远是 explanation-only：它可以解释冲稳保、位次差、计划变化和限制条件，但不能新增、删除、重排推荐项。

## 真实湖北数据工作流

数据入口是 `data/source_registry/hubei_sources.yaml`。只允许官方公开网页/下载、审核上传的官方 CSV/Excel/PDF，以及本地非敏感志愿草表文件；禁止登录考生系统、绕过验证码或请求账号密码。

标准流程：

1. Registry: 维护 source id、URL、parser、raw_subdir、license_note、是否需要人工审核。
2. Download: 下载允许的公开来源到 `data/raw/hubei`，并写入 sha256 manifest。
3. Parse: 解析到候选 CSV。官方 parser 产生的行默认 `review_status=pending`。
4. Quality: 检查 provenance、fixture marker、重复、rank segment 单调性和必填字段。
5. Manual review/approve: 人工核对来源、字段、sha256、OCR/表格转写结果；只有可信行可改为 `review_status=approved`。
6. Promote: 仅将 `approved`、`confidence_score >= 0.85`、无 fixture marker、provenance 完整的候选行写入 `data/curated/hubei`。
7. Seed: 校验 curated CSV 并写入/准备运行时数据库种子。

npm 命令：

```powershell
npm run data:hubei:download
npm run data:hubei:parse
npm run data:hubei:quality
npm run data:hubei:promote
npm run db:seed:hubei
```

Python 等价命令：

```powershell
python -m services.data.hubei.build_dataset --download
python -m services.data.hubei.build_dataset --parse
python -m services.data.hubei.build_dataset --quality
python -m services.data.hubei.build_dataset --promote
python -m services.data.hubei.seed_db --curated-dir data/curated/hubei
```

一键构建可用：

```powershell
npm run data:hubei:build
python -m services.data.hubei.build_dataset --download --parse --quality --promote
```

注意：当前 build 仍会维护 fixture seed 的格式化路径，真实候选行进入 `data/candidate/hubei_real` 后，必须通过人工审核、质量检查和完整三类数据检查才会覆盖 curated。以 `/api/data/status.real_curated_ready=true` 作为上线判断。

## 真实性政策

- Fixtures/demo 数据只用于本地流程和 UI 验证，不是生产数据。
- `APP_ENV=production` 或 `REQUIRE_REAL_DATA=true` 时，真实 curated 未就绪会让推荐接口返回 `503 real_data_required`。
- 官方原始图片、PDF、HTML、manifest 和 OCR 中间结果只保留本地或 CI/artifact，不作为普通源码提交。
- OCR 输出默认 pending，不得直接进入生产推荐。
- 可提交的 curated CSV 必须包含来源 URL、source_type、raw_document_sha256、parser_name、parser_version、parse_confidence、confidence_score、license_note、review_status、reviewer。
- curated CSV 不得含 fixture/demo marker，不得含考生个人身份信息。
- 提交前运行 quality/promote/seed，并用 `/api/data/status` 复核 `real_curated_ready`。

## 故障排查

`Failed to fetch`：

- 确认 `npm run api` 正在 `127.0.0.1:8000` 或 `localhost:8000`。
- 确认 Web 的 `NEXT_PUBLIC_API_BASE_URL` 指向同一个 API。
- 检查浏览器控制台是否是 CORS、端口、HTTPS/HTTP 混用或 API 进程退出。

`503 real_data_required`：

- 查看 `/api/data/status`。
- 如果 `dataset_kind=fixture_seed` 或 `contains_fixture_rows=true`，说明仍是 demo/fixture 数据。
- 若只是本地演示，设置 `ALLOW_FIXTURE_DATA=true` 且不要设置 `REQUIRE_REAL_DATA=true`。
- 若是生产验收，必须完成真实数据 review -> promote -> seed，并重启或触发 API reload。

MiniMax 401/403：

- 检查 API key 是否属于 MiniMax 当前项目。
- 检查 `MINIMAX_BASE_URL`、`MINIMAX_MODEL`、`MINIMAX_API_STYLE`。
- 确认状态端点只显示 masked key，不要把真实 key 写入日志或文档。

MiniMax timeout：

- 临时增大 `MINIMAX_TIMEOUT_SECONDS`。
- 检查代理、防火墙、DNS 和供应商状态。
- timeout 只影响解释，推荐排序仍由规则模型生成。

curated 文件陈旧：

- 重新执行 `npm run data:hubei:parse`、`npm run data:hubei:quality`、人工审核、`npm run data:hubei:promote`、`npm run db:seed:hubei`。
- 如果 `/api/data/status` 仍旧显示旧 counts，重启 API 或调用 Admin 数据 seed 操作触发 reload。
- 如果 `fixture_marker_count > 0`，不要上线；从真实 approved 候选行重新 promote。

OCR review queue：

- 可查看 `GET /api/hubei/ocr-review-queue`。
- 当前策略是 OCR 候选默认 pending；人工核对官方原图/PDF 后才可进入 approved 候选 CSV。
