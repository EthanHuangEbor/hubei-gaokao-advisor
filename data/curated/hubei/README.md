# Hubei Curated CSV Policy

本目录是运行时优先读取的湖北 curated CSV 层。文件存在不等于真实数据就绪；上线判断以 `/api/data/status.real_curated_ready` 和 `data_authenticity.dataset_kind` 为准。

## 文件清单

- `admission_records_2023_2025.csv`: 2023-2025 本科普通批投档线/录取记录。
- `rank_segments_2023_2026.csv`: 2023-2026 一分一段或位次段。
- `admission_plans_2026.csv`: 2026 院校专业组招生计划。

当前仓库可能包含 v0.2 fixture seed 行，用于格式、接口和演示流程验证。进入真实生产前，必须由官方公开来源或人工审核上传来源生成的 approved 行替换。

## 可提交要求

提交 curated CSV 前必须满足：

- 三个 CSV 都存在且 schema 可被 `services.data.hubei.curated_loader` 读取。
- 每行 `review_status=approved`，并有 `reviewer`。
- 每行保留 `source_id`、`source_url`、`source_type`、`raw_document_sha256`、`parser_name`、`parser_version`、`parse_confidence`、`confidence_score`、`license_note`。
- 不含 `fixture`、`static_csv_seed`、`curated-fixture-seed`、样例大学等 demo marker。
- 不含姓名、身份证号、考生号、手机号等 PII。
- OCR/图片/PDF 转写行已经人工核对；未核对的行仍留在 candidate/raw 工件中，不能 promote。
- 质量检查无 error，`/api/data/status.real_curated_ready=true`。

## 更新流程

```powershell
npm run data:hubei:download
npm run data:hubei:parse
npm run data:hubei:quality
# 人工审核 data/candidate/hubei_real 下候选 CSV，可信行标记 review_status=approved
npm run data:hubei:promote
npm run db:seed:hubei
curl.exe http://127.0.0.1:8000/api/data/status
```

Python 等价命令：

```powershell
python -m services.data.hubei.build_dataset --download
python -m services.data.hubei.build_dataset --parse
python -m services.data.hubei.build_dataset --quality
python -m services.data.hubei.build_dataset --promote
python -m services.data.hubei.seed_db --curated-dir data/curated/hubei
```

`data/raw/hubei`、`data/candidate/*`、OCR 中间文件和官方原始图片/PDF 默认是本地或 artifact-only，不作为普通源码提交。只提交通过审核、可追溯、无 PII 的 curated CSV。
