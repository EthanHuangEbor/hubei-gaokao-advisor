import { API_BASE } from "@/lib/api";

import { AdminClient } from "./admin-client";

async function getSources() {
  try {
    const response = await fetch(`${API_BASE}/api/hubei/sources`, { cache: "no-store" });
    return response.ok ? response.json() : [];
  } catch {
    return [];
  }
}

export default async function AdminPage() {
  const sources: Array<Record<string, string | number>> = await getSources();
  return (
    <div className="grid">
      <section>
        <h1>数据后台</h1>
        <p className="lead">公开数据源、解析任务、人工复核、质量检查和 MiniMax 日志的管理入口。</p>
      </section>
      <div className="grid cols-3">
        {["数据源发现", "解析任务", "人工复核", "质量报告", "招生计划上传", "Doctor.Peak 状态"].map((item) => (
          <div className="card" key={item}>
            <h3>{item}</h3>
            <p className="muted">MVP API 已预留接口。</p>
          </div>
        ))}
      </div>
      <AdminClient />
      <section className="card">
        <h2>首批数据源</h2>
        <table className="table">
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={String(source.source_id)}>
                <td>{String(source.source_name)}</td>
                <td>{String(source.source_type)}</td>
                <td>{String(source.review_status)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <div className="notice">登录态数据不得自动抓取；2026 招生计划优先通过管理员上传官方文件进入人工复核队列。</div>
    </div>
  );
}
