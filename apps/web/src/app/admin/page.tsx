import { fetchDataStatus, fetchHubeiSources } from "@/lib/api";

import { AdminClient } from "./admin-client";

export default async function AdminPage() {
  const [sources, dataStatus] = await Promise.all([
    fetchHubeiSources().catch(() => []),
    fetchDataStatus().catch(() => null),
  ]);
  return (
    <div className="grid">
      <section className="result-header">
        <div>
          <h1>数据后台</h1>
          <p className="lead">公开数据源、raw/candidate/curated 三层构建、人工复核、质量检查和 MiniMax 日志的管理入口。</p>
        </div>
        <div className="notice compact">OCR 候选默认 pending，不会直接进入推荐。</div>
      </section>

      <section className="summary-strip">
        <div className="summary-cell wide">
          <span className="muted">运行数据</span>
          <strong>{dataStatus?.runtime_source ?? "unknown"}</strong>
        </div>
        <div className="summary-cell wide">
          <span className="muted">Curated</span>
          <strong>{dataStatus?.curated_ready ? "ready" : "fixture fallback"}</strong>
        </div>
        <div className="summary-cell wide">
          <span className="muted">投档线</span>
          <strong>{dataStatus?.counts.admission_records ?? "-"}</strong>
        </div>
        <div className="summary-cell wide">
          <span className="muted">一分一段</span>
          <strong>{dataStatus?.counts.rank_segments ?? "-"}</strong>
        </div>
        <div className="summary-cell wide">
          <span className="muted">招生计划</span>
          <strong>{dataStatus?.counts.admission_plans ?? "-"}</strong>
        </div>
      </section>

      <div className="grid cols-3">
        {[
          "source registry",
          "raw documents",
          "parse jobs",
          "OCR review queue",
          "curated status",
          "quality reports",
          "MiniMax logs",
          "Doctor.Peak status",
          "2026 plan upload",
        ].map((item) => (
          <div className="card" key={item}>
            <h3>{item}</h3>
            <p className="muted">v0.2 workflow</p>
          </div>
        ))}
      </div>

      <AdminClient />

      <section className="card table-card">
        <h2>Source registry</h2>
        <table className="table">
          <thead>
            <tr>
              <th>名称</th>
              <th>数据类型</th>
              <th>来源类型</th>
              <th>状态</th>
              <th>链接</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.source_id}>
                <td>{source.title ?? source.source_name ?? source.source_id}</td>
                <td>{source.data_type ?? "-"}</td>
                <td>{source.source_type}</td>
                <td>{source.status ?? source.review_status ?? "-"}</td>
                <td><a href={source.source_url} rel="noreferrer" target="_blank">打开</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="notice compact">登录态数据不得自动抓取；2026 招生计划优先通过管理员上传官方文件进入人工复核队列。</div>
    </div>
  );
}