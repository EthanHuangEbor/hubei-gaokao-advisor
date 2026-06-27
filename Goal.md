你是本项目的首席全栈工程师、数据工程师、爬虫工程师、推荐算法工程师和产品架构师。请从零构建一个面向湖北高考生的“高考志愿冲稳保推荐系统”MVP。

项目第一阶段只做湖北省，不做全国。核心场景是：湖北普通类考生输入 2026 年高考成绩、全省位次、首选科目、再选科目和个人偏好后，系统基于湖北省 2023、2024、2025 近三年公开投档线、一分一段、院校专业组录取情况，以及 2026 年当年招生计划变化，生成“冲、稳、保、垫”志愿建议，并调用 MiniMax API 生成可解释建议。

一、项目定位

项目名称：hubei-gaokao-advisor

第一省份：湖北省

第一批次范围：

- 普通类
- 本科普通批
- 首选物理
- 首选历史
- 平行志愿
- 院校专业组口径

暂不覆盖：

- 艺术类
- 体育类
- 技能高考
- 强基计划
- 综合评价
- 军警院校
- 高校专项
- 免费医学生
- 港澳独立招生
- 专科批

这些内容可以预留数据结构和扩展接口，但 MVP 不做推荐。

二、必须遵守的湖北口径

1. 湖北新高考推荐的基本单元不是“学校”，而是“院校专业组”。
2. 不得把“高校最低线”“学校投档线”“院校专业组投档线”“专业录取最低线”混用。
3. admission_records 的主键粒度必须是：
   year + province + batch + category + first_subject + university_code + major_group_code
4. major_group_code 必须作为核心字段进入推荐算法、前端卡片和来源追溯。
5. 一个高校可能有多个专业组，每个专业组有不同选科要求、招生计划、投档线、最低位次和风险等级。
6. 湖北普通类平行志愿推荐结果必须最终能生成“院校专业组志愿草表”，不是只生成学校名单。
7. 结果页必须提示：最终填报应以湖北省考试院、湖北省招办、湖北招生考试网、湖北省招生数智综合平台和高校招生章程为准。

三、合规与隐私边界

1. 不得抓取、存储、展示任何可识别到个人考生的数据，包括姓名、身份证号、准考证号、14 位高考报名号、手机号、录取通知截图、社交平台录取截图、个人录取去向等。
2. 用户输入页不得要求姓名、身份证、准考证号、手机号、高考报名号。
3. “同省同名次考生去向”必须实现为“同省、同科类/首选科目、同位次区间的公开聚合录取去向或可达院校专业组统计”，不得实现为个人级追踪。
4. 对低样本区间启用 k-anonymity，默认 k=20。低于 k 的位次区间不得展示具体去向，只能显示“样本不足”。
5. 如果无法从官方公开数据中得到真实“去向分布”，系统必须命名为“同位次区间可达院校专业组统计”或“同位次区间历史投档参考”，不得谎称为真实个人去向。
6. 不得自动化登录需要考生账号的网站，不得要求用户提供湖北招生平台账号、密码、身份证后五位、报名号或短信验证码。
7. 对登录态系统中的招生计划数据，只允许以下方式进入系统：
   - 官方公开下载文件
   - 官方公开网页
   - 项目管理员手动上传的官方 PDF、Excel、CSV
   - 用户自行导出的非敏感志愿草表文件
8. 所有数据必须保留 source_url、source_name、source_type、fetched_at、published_at、parser_version、confidence_score、license_note、review_status。
9. MiniMax API 调用不得发送个人身份信息。只允许发送省份、年份、首选科目、再选科目、成绩、位次、偏好、推荐项和必要解释上下文。
10. 产品必须显著展示免责声明：本系统仅基于公开历史数据、当年招生计划和规则模型进行估计，不构成录取承诺。

四、先检索、安装和审计 GitHub Skills

在写业务代码前，先执行 Skill 检索和审计。

必须检索 GitHub 上可用的软件开发类 Codex/Agent Skills，至少覆盖：

1. codebase analysis / architecture audit
2. FastAPI / API design
3. Next.js / React / frontend testing
4. Playwright e2e testing
5. data pipeline / ETL / scraping
6. security audit / secrets scanning
7. docs generation / README generation
8. CI repair / PR review
9. Python data validation
10. SQLAlchemy/PostgreSQL migration

请生成 docs/skill-audit.md，记录：

- repo
- skill name
- URL
- license
- stars
- last updated
- intended use
- commercial suitability
- security concern
- adopted / not adopted
- adoption method：install / copy with attribution / learn only / reject

只允许集成 license 明确且可商用的 skill。license 不明确的，只能学习思想，不能复制文件。

五、使用 GitHub 女娲 Skill 生成 Doctor.Peak

本项目需要内置一个业务卖点：Doctor.Peak 志愿顾问 Skill。

Doctor.Peak 是本产品自有的虚拟业务顾问，不得冒充任何真实公众人物，不得使用张雪峰姓名、肖像、声音、口头禅或授权暗示。

请优先安装并调用 GitHub 女娲 skill：

- repo: https://github.com/alchaincyf/nuwa-skill
- install command: npx skills add alchaincyf/nuwa-skill

操作要求：

1. 先审计 nuwa-skill 的 license、README、SKILL.md、脚本行为和安全风险。
2. 如果 license 明确为 MIT 或其他可商用协议，允许安装到 Codex skills 目录。
3. 使用女娲 skill 生成一个“主题型业务 Skill”，不是人物仿真 Skill。
4. 生成目标：
   Doctor.Peak：湖北高考志愿就业导向顾问 Skill
5. Doctor.Peak 的能力边界：
   - 基于公开数据和系统结构化推荐结果进行解释
   - 强调学校、专业、城市、就业、考研、行业周期之间的取舍
   - 对高学费、中外合作、民办、冷门专业、专业组陷阱、选科限制、体检限制、单科限制给出红旗提示
   - 对“只看名校不看专业”“只看热门专业不看分数风险”“不服从调剂”等行为给出风险提示
   - 生成家长版解释和学生版解释
   - 不能承诺录取
   - 不能使用个人隐私数据
   - 不能冒充真实人物
6. 生成后的 Doctor.Peak skill 保存到：
   .agents/skills/doctor-peak/SKILL.md
7. 同步创建业务提示词：
   services/llm/prompts/doctor_peak.md
8. 如果 nuwa-skill 安装失败或无法运行，请手动创建 Doctor.Peak Skill，但 docs/skill-audit.md 中必须记录失败原因和替代方案。
9. 如果 GitHub 上已经存在可安装的 Doctor.Peak 成品 skill，只有在 license 明确、内容合规、无侵权公众人物仿真、无恶意脚本时才允许安装；否则必须本地生成。

六、技术栈

采用 monorepo：

- 前端：Next.js + TypeScript + shadcn/ui + TanStack Query
- 后端：FastAPI + Pydantic v2 + SQLAlchemy 2.x
- 数据库：PostgreSQL
- 向量检索：pgvector
- 缓存和任务队列：Redis + Celery 或 RQ
- 爬虫：Scrapy + Playwright
- 数据解析：pandas、openpyxl、PyMuPDF、BeautifulSoup、lxml
- PDF 表格解析：预留 Camelot/Tabula 适配器
- 图片表格解析：仅作为低置信度候选，必须进入人工复核队列
- 测试：pytest、ruff、mypy、Playwright
- 部署：Docker Compose
- LLM：MiniMax OpenAI-compatible API，默认 MiniMax-M3

七、仓库结构

请创建如下结构：

hubei-gaokao-advisor/
  apps/
    web/
    api/
    worker/
  packages/
    shared-types/
  services/
    crawler/
      adapters/
        hubei/
          hubei_admission_line_adapter.py
          hubei_rank_segment_adapter.py
          hubei_plan_adapter.py
          hubei_source_discovery.py
        static_csv_adapter.py
        html_table_adapter.py
        pdf_table_adapter.py
      pipelines/
      quality/
    parser/
    recommender/
      hubei_rules.py
      admission_risk_model.py
      volunteer_plan_builder.py
      backtest.py
    llm/
      minimax_client.py
      advice_orchestrator.py
      prompts/
        doctor_peak.md
        recommendation_json_schema.md
    compliance/
      pii_redactor.py
      k_anonymity.py
      source_audit.py
      crawler_policy.py
  db/
    migrations/
    seeds/
  data/
    raw/
    normalized/
    fixtures/
      hubei/
  docs/
    product-requirements.md
    architecture.md
    hubei-data-source-registry.md
    recommendation-formula.md
    minimax-integration.md
    doctor-peak-skill.md
    compliance.md
    skill-audit.md
    backtest-report.md
  .agents/
    skills/
      github-skill-hunter/
      hubei-data-pipeline/
      admission-risk-model/
      minimax-advisor/
      doctor-peak/
      privacy-compliance-audit/
  docker-compose.yml
  README.md

八、湖北官方数据源优先级

请将湖北省官方和准官方公开数据源作为第一优先级。先建立 source registry，不要直接写死单页爬虫。

首批数据源包括但不限于：

1. 湖北省教育考试院
   https://www.hbea.edu.cn/

2. 湖北招生考试网
   https://www.hbksw.com/

3. 湖北省教育厅高校招生专栏
   https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/

4. 湖北省招生数智综合平台
   https://zspt.hubzs.com.cn/

5. 湖北招生考试网：2023--2025 年各批次各类投档线合集
   https://www.hbksw.com/info/38/1771.html

6. 湖北招生考试网：2023 年各批次各类投档线合集
   https://www.hbksw.com/info/38/1770.html

7. 湖北招生考试网：2024 年各批次各类投档线合集
   https://www.hbksw.com/info/38/1768.html

8. 湖北招生考试网：2023-2026 年湖北省普通高校招生排序成绩一分一段表统计表
   https://www.hbksw.com/info/38/1746.html

9. 湖北招生考试网：2023 年普通高校招生排序成绩一分一段统计表
   https://www.hbksw.com/info/5/1304.html

10. 湖北招生考试网：2024 年普通高校招生排序成绩一分一段统计表
   https://www.hbksw.com/info/38/1748.html

11. 湖北招生考试网：2025 年普通高校招生排序成绩一分一段统计表
   https://www.hbksw.com/info/38/1845.html

12. 湖北招生考试网：“计划查询与志愿填报辅助系统”开通及操作指南
   https://www.hbksw.com/info/11/1803.html

13. 湖北省教育厅：2025 年湖北省普通高校阳光招生政策暨志愿填报问答
   https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202506/t20250618_5697087.shtml

数据抓取策略：

1. 对公开 HTML 表格优先使用 pandas.read_html / BeautifulSoup / lxml 解析。
2. 对 PDF 文件使用 PyMuPDF 提取文本，必要时使用表格解析器。
3. 对图片型一分一段表或图片型投档线，只做 OCR 候选，不直接入正式库。必须进入人工复核表 raw_document_reviews。
4. 对动态页面使用 Playwright，但必须遵守 robots.txt、访问频率和来源网站条款。
5. 对登录后才能访问的计划查询系统，不得模拟用户登录，不得使用考生账号。应提供管理员上传官方计划文件的入口。
6. 每个 parser 必须输出 confidence_score。低于 0.85 的数据不得用于正式推荐，只能进入 review 队列。
7. 所有原始文件保存到 data/raw 或对象存储，并计算 sha256_hash。

九、数据模型

请设计 PostgreSQL 表，至少包括：

- provinces
- hubei_subject_types
- universities
- university_aliases
- majors
- major_categories
- major_groups
- admission_plans
- admission_records
- rank_segments
- same_rank_reference_groups
- destination_aggregates
- data_sources
- raw_documents
- parse_jobs
- raw_document_reviews
- data_quality_reports
- user_profiles
- recommendation_runs
- recommendation_items
- volunteer_plans
- volunteer_plan_items
- llm_advice_logs
- compliance_audit_logs
- skill_registry
- skill_audit_logs

关键字段要求：

admission_records:

- id
- year
- province = 湖北
- batch
- category = 普通类
- first_subject = physics / history
- second_subject_requirement
- university_code
- university_name
- major_group_code
- major_group_name
- admission_category
- min_score
- min_rank
- plan_seats
- source_id
- source_url
- confidence_score
- parser_version
- created_at

admission_plans:

- id
- year
- province
- batch
- category
- first_subject
- second_subject_requirement
- university_code
- university_name
- major_group_code
- major_group_name
- major_code
- major_name
- plan_seats
- tuition
- schooling_years
- campus
- is_sino_foreign
- is_private
- notes
- physical_limit_note
- single_subject_limit_note
- source_id
- confidence_score

rank_segments:

- id
- year
- province
- category
- first_subject
- score
- same_score_count
- cumulative_rank
- rank_start
- rank_end
- source_id
- confidence_score

same_rank_reference_groups:

- id
- target_year
- history_year
- province
- first_subject
- candidate_rank
- rank_window_start
- rank_window_end
- university_code
- university_name
- major_group_code
- major_group_name
- min_score
- min_rank
- rank_gap
- reference_type = observed_min_rank_nearby / estimated_available_group
- confidence_score

user_profiles:

- id UUID
- province
- year
- first_subject
- second_subjects JSON
- score
- rank
- batch
- preferences JSON
- created_at

不得保存姓名、身份证、准考证、手机号、报名号。

十、湖北数据导入与解析任务

请实现以下 adapters：

1. HubeiSourceDiscovery

职责：

- 从湖北招生考试网和湖北省教育厅公开页面发现链接
- 识别“2023 年投档线”“2024 年投档线”“2025 年投档线”“一分一段”“招生计划”“阳光招生问答”等数据源
- 写入 data_sources
- 不直接抓取登录态页面

2. HubeiAdmissionLineAdapter

职责：

- 解析 2023、2024、2025 湖北本科普通批首选物理/首选历史平行志愿投档线
- 标准化为 admission_records
- 必须解析到：
  year
  batch
  first_subject
  university_code
  university_name
  major_group_code
  major_group_name
  min_score
  min_rank
  plan_seats 如果公开表中有
  notes
  source_url
  confidence_score

3. HubeiRankSegmentAdapter

职责：

- 解析 2023、2024、2025、2026 湖北普通类一分一段表
- 标准化为 rank_segments
- 2026 一分一段用于当前考生输入校验和分数位次换算
- 2023–2025 一分一段用于历史等位分换算和回测

4. HubeiPlanAdapter

职责：

- 读取 2026 年湖北招生计划
- 优先支持管理员上传官方 Excel / CSV / PDF
- 不自动登录计划查询系统
- 标准化为 admission_plans
- 必须保留专业组、专业、选科、计划数、学费、校区、备注、限制条件

5. StaticCsvHubeiFixtureAdapter

职责：

- 提供虚构但格式真实的湖北样例数据
- 在没有真实数据文件时保证系统可以运行 demo
- 样例不得包含真实个人考生信息

十一、推荐算法

实现 HubeiAdmissionRiskModel。

输入：

- candidate.year
- candidate.province = 湖北
- candidate.first_subject
- candidate.second_subjects
- candidate.score
- candidate.rank
- candidate.batch
- candidate.preferences
- admission_records_2023_2025
- rank_segments_2023_2026
- current_year_admission_plans
- historical_plans 如果可用
- same_rank_reference_groups

硬过滤：

1. 省份不匹配，剔除。
2. 批次不匹配，剔除。
3. 首选科目不匹配，剔除。
4. 再选科目要求不满足，剔除。
5. 学费超过用户上限，剔除。
6. 用户不接受中外合作，剔除中外合作项目。
7. 用户不接受民办，剔除民办院校。
8. 体检限制不满足，剔除或强警示。
9. 单科限制不满足，剔除或强警示。
10. 数据置信度低于阈值，默认不进入推荐池。

核心指标：

- rank_gap = candidate_rank - historical_min_rank_median
  注意：湖北位次数值越小越好，因此 rank_gap <= 0 表示考生位次优于历史最低位次。
- rank_gap_ratio = rank_gap / candidate_rank
- min_rank_3y = [2023_min_rank, 2024_min_rank, 2025_min_rank]
- min_score_3y = [2023_min_score, 2024_min_score, 2025_min_score]
- volatility_score = std(min_rank_3y) / mean(min_rank_3y)
- plan_change_ratio = current_plan_seats / max(last_year_plan_seats, 1) - 1
- seat_abs_change = current_plan_seats - last_year_plan_seats
- group_change_flag = stable / split / merged / new_group / removed_group / unknown
- subject_requirement_change_flag
- same_rank_hit_count
- same_rank_reference_confidence
- preference_match_score
- restriction_penalty
- data_confidence_score

概率估计初版：

1. 先根据 rank_gap_ratio 得到 base_probability。
2. 再加入 plan_change_ratio 修正。
3. 再加入 volatility_score 惩罚。
4. 再加入专业组变化惩罚。
5. 再加入偏好匹配加分。
6. 再加入数据置信度折扣。
7. 输出 probability_band，不输出精确录取概率。

分档规则：

- 冲：adjusted_probability in [0.20, 0.45)
- 稳：adjusted_probability in [0.45, 0.75)
- 保：adjusted_probability in [0.75, 0.92)
- 垫：adjusted_probability >= 0.92

志愿数量建议：

为湖北本科普通批生成 45 个院校专业组志愿草表建议，默认比例：

- 冲：8–10 个
- 稳：16–18 个
- 保：12–14 个
- 垫：3–5 个

如果推荐池不足，自动调整比例并说明原因。

十二、同位次区间参考逻辑

实现 SameRankReferenceBuilder。

不要构造个人去向。

对某个湖北考生 rank R：

1. 根据首选科目和批次过滤 2023–2025 数据。
2. 设置动态 rank_window：
   - R <= 5000：±300
   - 5000 < R <= 20000：±800
   - 20000 < R <= 60000：±1500
   - R > 60000：±3000
3. 找出历史年份中 min_rank 落在窗口附近的院校专业组。
4. 标记为 same_rank_reference_groups。
5. 该统计只能叫“同位次区间历史可达专业组参考”，不得叫“同名次考生真实去向”。
6. 如果有公开聚合录取去向数据，才允许生成 destination_aggregates。
7. 所有参考项都必须带 confidence_score 和 source_url。

十三、MiniMax API 集成

实现 services/llm/minimax_client.py。

环境变量：

- MINIMAX_API_KEY
- MINIMAX_BASE_URL，默认 https://api.minimax.io/v1
- MINIMAX_MODEL，默认 MiniMax-M3
- MINIMAX_API_STYLE，默认 responses，可选 responses / chat_completions
- MINIMAX_TIMEOUT_SECONDS，默认 30

优先实现 OpenAI-compatible Responses API：

POST /v1/responses

请求要求：

- model = MiniMax-M3
- temperature = 0.2
- reasoning.effort = none
- stream = false
- output format 必须尽量约束为 JSON
- 输入中不得包含姓名、身份证、准考证、手机号、高考报名号
- 输入中不得包含原始完整用户画像，只传必要推荐上下文

如果 Responses API 不可用，再 fallback 到 Chat Completions 兼容接口。

MiniMax 输出 JSON schema：

{
  "summary": "string",
  "overall_strategy": "string",
  "doctor_peak_view": "string",
  "items": [
    {
      "major_group_id": "string",
      "tier": "冲|稳|保|垫",
      "why": "string",
      "main_risks": ["string"],
      "plan_change_explanation": "string",
      "rank_explanation": "string",
      "employment_angle": "string",
      "parent_explanation": "string",
      "student_explanation": "string",
      "next_checks": ["string"]
    }
  ],
  "risks": ["string"],
  "parent_talking_points": ["string"],
  "student_talking_points": ["string"],
  "next_checks": ["string"],
  "disclaimer": "string"
}

失败处理：

1. MiniMax API key 缺失时，系统仍可完成推荐。
2. MiniMax 调用失败时，返回 deterministic fallback explanation。
3. fallback explanation 由规则模板生成，不得影响推荐排序。
4. 记录 llm_advice_logs：
   - request_id
   - model
   - endpoint_style
   - latency_ms
   - token_usage
   - input_redacted_hash
   - output_json
   - error_code
   - created_at
5. 不记录完整敏感输入。

十四、Doctor.Peak 业务提示词

创建 services/llm/prompts/doctor_peak.md。

内容要求：

Doctor.Peak 是一个虚拟的、就业导向的湖北高考志愿解释顾问。它不是真实人物，不模仿真实公众人物，不使用任何真实公众人物姓名、肖像、声音或授权暗示。

Doctor.Peak 的决策风格：

1. 数据优先，不凭感觉推荐。
2. 湖北口径优先，始终围绕“院校专业组”解释。
3. 就业导向，但不简单鼓吹热门专业。
4. 解释学校、城市、专业、就业、考研之间的取舍。
5. 对以下情况必须主动提示风险：
   - 只冲名校，忽略专业组和选科限制
   - 不服从专业调剂
   - 高学费和中外合作
   - 民办本科
   - 专业组内包含用户强烈排斥的专业
   - 专业组冷热极不均衡
   - 近三年位次波动大
   - 当年计划明显缩招
   - 新增专业组，无历史投档线
   - 体检、单科、外语语种限制
   - 城市和就业方向冲突
6. 不能承诺录取。
7. 不能替代湖北省招办、高校招生办和高中老师意见。
8. 输出必须是 JSON，不得输出散文式长文。
9. 对家长说话要强调风险、成本、就业和兜底。
10. 对学生说话要强调兴趣、学习难度、专业路径和长期发展。

十五、API 路由

FastAPI 路由：

GET /health

GET /api/hubei/sources
POST /api/hubei/sources/discover
POST /api/hubei/parse-jobs
GET /api/hubei/parse-jobs
GET /api/hubei/data-quality
POST /api/hubei/data-quality/run

GET /api/provinces
GET /api/universities
GET /api/majors
GET /api/hubei/rank-segments
GET /api/hubei/admission-records
GET /api/hubei/admission-plans

POST /api/recommendations/run
GET /api/recommendations/{run_id}
GET /api/recommendations/{run_id}/volunteer-plan
POST /api/recommendations/{run_id}/llm-advice

GET /api/admin/raw-documents
GET /api/admin/raw-documents/{id}
POST /api/admin/raw-documents/{id}/review
POST /api/admin/upload/hubei-plan
POST /api/admin/upload/hubei-admission-records

GET /api/skills
POST /api/skills/audit
GET /api/skills/doctor-peak

十六、前端页面

实现以下页面：

1. /

产品介绍：

- 湖北高考志愿冲稳保推荐
- 基于 2023–2025 湖北公开投档线
- 支持 2026 当年招生计划对比
- Doctor.Peak 就业导向解释
- 不承诺录取

2. /input

字段：

- year，默认 2026
- province，固定湖北
- batch，默认本科普通批
- category，普通类
- first_subject：物理 / 历史
- second_subjects：化学、生物、政治、地理中选择
- score
- rank
- preferred_cities
- avoid_cities
- preferred_majors
- avoid_majors
- max_tuition
- accept_private_college
- accept_sino_foreign
- accept_adjustment
- physical_limits
- single_subject_limits
- priority_strategy：
  school_first / major_first / city_first / employment_first / balanced

3. /result/[runId]

展示：

- 总体策略
- 冲稳保垫数量
- Doctor.Peak 总评
- 45 个院校专业组志愿卡片
- 每个卡片展示：
  university_name
  major_group_code
  major_group_name
  included_majors
  current_plan_seats
  last_year_plan_seats
  plan_change_ratio
  min_rank_2023
  min_rank_2024
  min_rank_2025
  min_score_2023
  min_score_2024
  min_score_2025
  rank_gap
  volatility_score
  risk_level
  estimated_probability_band
  reasons
  warnings
  source_links
  doctor_peak_explanation

4. /compare

支持用户对比多个志愿方案：

- 学校优先方案
- 专业优先方案
- 城市优先方案
- 就业优先方案
- 均衡方案

5. /admin

后台：

- 数据源列表
- 数据源发现
- 爬虫任务
- 原始文件
- 解析结果
- 人工复核
- 数据质量报告
- 2026 招生计划上传
- Doctor.Peak Skill 状态
- MiniMax 调用日志

十七、数据质量检查

实现 quality checks：

1. admission_records 中 year 必须为 2023、2024、2025。
2. 湖北本科普通批必须区分首选物理和首选历史。
3. major_group_code 不得为空。
4. min_rank 必须为正整数。
5. min_score 必须在 0–750 之间。
6. 同一 year + first_subject + university_code + major_group_code 不得重复。
7. 同一专业组如果 min_rank 与 min_score 显著不匹配，标记异常。
8. 2026 admission_plans 必须有 major_group_code、major_name、plan_seats。
9. OCR 数据默认 review_status=pending。
10. confidence_score < 0.85 的数据不得进入推荐池。
11. source_url 不得为空。
12. rank_segments 必须覆盖足够分数段，否则警告。

十八、回测

实现 backtest.py。

目标：

用 2023、2024 数据预测 2025 湖北本科普通批投档结果。

步骤：

1. 对 2025 年若干位次样本生成推荐。
2. 判断推荐项在 2025 真实投档线中是否落入对应风险区间。
3. 输出：
   - 冲档命中率
   - 稳档命中率
   - 保档安全率
   - 垫档安全率
   - 数据缺失率
   - 因计划变化导致的误差案例
   - 因专业组拆分/合并导致的误差案例
4. 生成 docs/backtest-report.md。
5. 没有回测结果前，前端不得展示“准确率”营销词。

十九、测试

至少实现：

后端测试：

- test_hubei_subject_filter.py
- test_major_group_required.py
- test_rank_gap.py
- test_plan_change_ratio.py
- test_volatility_score.py
- test_hard_filter_subject_requirement.py
- test_private_college_filter.py
- test_sino_foreign_filter.py
- test_k_anonymity.py
- test_same_rank_reference_builder.py
- test_minimax_client_mock.py
- test_doctor_peak_json_schema.py
- test_recommendation_run_api.py

前端测试：

- Playwright：输入湖北物理类考生信息 -> 生成推荐 -> 查看结果页
- Playwright：切换历史类 -> 推荐结果不混入物理类
- Playwright：不接受中外合作 -> 结果不出现中外合作项目
- Playwright：admin 上传招生计划 -> 数据质量检查

质量工具：

- ruff
- mypy
- pytest
- eslint
- typecheck
- playwright
- GitHub Actions CI

二十、fixtures

创建 data/fixtures/hubei/：

- hubei_sample_universities.csv
- hubei_sample_major_groups.csv
- hubei_sample_majors.csv
- hubei_sample_admission_records_2023.csv
- hubei_sample_admission_records_2024.csv
- hubei_sample_admission_records_2025.csv
- hubei_sample_rank_segments_2023.csv
- hubei_sample_rank_segments_2024.csv
- hubei_sample_rank_segments_2025.csv
- hubei_sample_rank_segments_2026.csv
- hubei_sample_admission_plans_2026.csv
- hubei_sample_same_rank_reference_groups.csv

fixtures 可以使用虚构高校和虚构专业组，但字段必须贴近湖北真实格式。例如：

- HBA001 湖北样例大学
- HBA001-01 物理+化学专业组
- HBA001-02 物理+不限专业组
- HBA002-03 历史+不限专业组

不得包含真实个人考生信息。

二十一、文档

生成：

- README.md
- docs/product-requirements.md
- docs/architecture.md
- docs/hubei-data-source-registry.md
- docs/recommendation-formula.md
- docs/minimax-integration.md
- docs/doctor-peak-skill.md
- docs/compliance.md
- docs/skill-audit.md
- docs/backtest-report.md
- docs/data-quality-rules.md
- docs/crawler-policy.md

README 必须包含：

- 本地启动
- Docker Compose
- 环境变量
- 如何导入湖北 fixtures
- 如何上传湖北 2026 招生计划
- 如何运行推荐
- 如何启用 MiniMax
- MiniMax key 缺失时的 fallback
- 如何安装/审计女娲 skill
- Doctor.Peak 的合规边界

二十二、环境变量

创建 .env.example：

DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/hubei_gaokao
REDIS_URL=redis://redis:6379/0
MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_MODEL=MiniMax-M3
MINIMAX_API_STYLE=responses
MINIMAX_TIMEOUT_SECONDS=30
ENABLE_LLM_ADVICE=true
ENABLE_DOCTOR_PEAK=true
ENABLE_NUWA_SKILL_INSTALL=false
DATA_CONFIDENCE_THRESHOLD=0.85
K_ANONYMITY_MIN_SAMPLE=20
APP_ENV=development

二十三、交付顺序

请严格按以下顺序执行：

第一阶段：Skill 审计与项目骨架

1. 检索 GitHub 软件开发类 skills。
2. 审计 nuwa-skill。
3. 生成 docs/skill-audit.md。
4. 安装或本地创建必要 skills。
5. 创建 monorepo、Docker Compose、基础前后端。

第二阶段：湖北数据模型与 fixtures

1. 创建数据库 schema。
2. 创建湖北 fixtures。
3. 实现导入命令。
4. 实现数据质量检查。

第三阶段：湖北数据源发现与解析

1. 实现 HubeiSourceDiscovery。
2. 实现 HubeiAdmissionLineAdapter。
3. 实现 HubeiRankSegmentAdapter。
4. 实现 HubeiPlanAdapter。
5. 支持管理员上传官方计划文件。
6. 所有低置信度解析进入人工复核。

第四阶段：推荐算法

1. 实现 HubeiAdmissionRiskModel。
2. 实现 SameRankReferenceBuilder。
3. 实现 VolunteerPlanBuilder。
4. 生成 45 个院校专业组草表。
5. 实现 2025 回测。

第五阶段：MiniMax 与 Doctor.Peak

1. 实现 minimax_client.py。
2. 实现 doctor_peak.md。
3. 使用女娲 skill 生成 .agents/skills/doctor-peak/SKILL.md。
4. 实现 advice_orchestrator.py。
5. MiniMax 失败时 fallback。

第六阶段：前端

1. 输入页。
2. 结果页。
3. 方案对比页。
4. 后台页。
5. 数据来源和免责声明展示。

第七阶段：测试、CI、文档

1. pytest。
2. ruff。
3. mypy。
4. Playwright。
5. GitHub Actions。
6. 完整文档。
7. 修复所有错误。

二十四、验收标准

运行 docker compose up 后：

1. web 可访问。
2. api /health 返回 ok。
3. 可以导入湖北 fixtures。
4. 可以上传湖北招生计划样例文件。
5. 可以输入一个湖北 2026 物理类考生，生成冲稳保垫结果。
6. 可以输入一个湖北 2026 历史类考生，生成冲稳保垫结果。
7. 物理类推荐不会混入历史类专业组。
8. 历史类推荐不会混入物理类专业组。
9. 选科不满足的专业组被剔除。
10. 不接受中外合作时，中外合作专业组被剔除。
11. 不接受民办时，民办院校被剔除。
12. 推荐结果以院校专业组为单位。
13. 每个推荐项显示近三年最低分、最低位次、计划变化、风险解释、数据来源。
14. Doctor.Peak 能输出 JSON 解释。
15. MiniMax key 缺失时系统仍可运行。
16. low sample 区间不展示具体去向。
17. pytest 通过。
18. ruff 通过。
19. mypy 通过。
20. Playwright 基础流程通过。
21. docs 完整。
22. skill-audit.md 完整记录女娲 skill 和其他 GitHub skills 的采用情况。

二十五、重要实现原则

1. 优先做可运行 MVP，不要只写空架构。
2. 数据必须可追溯。
3. 推荐必须可解释。
4. LLM 只做解释层，不做最终排序裁决。
5. 湖北院校专业组是第一建模单位。
6. 没有官方公开数据支持的结论，必须标记为 estimated 或 low_confidence。
7. 不要为了演示效果编造真实高校数据。
8. 不要绕过登录、验证码、账号体系。
9. 不要保存任何非必要个人信息。
10. 不要把 Doctor.Peak 写成真实人物仿真。
11. 不要把“同位次参考”包装成“真实考生去向”。
12. 最终以工程可运行、数据可审计、推荐可解释为目标。

请现在开始执行。不要只输出方案，请创建可运行代码、测试和文档。