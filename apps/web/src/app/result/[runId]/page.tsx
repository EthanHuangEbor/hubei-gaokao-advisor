import { fetchDataStatus, fetchRecommendationTrace, fetchRun, recommendationExportUrl } from "@/lib/api";

import { ResultClient } from "./result-client";

export default async function ResultPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  try {
    const run = await fetchRun(runId);
    const [dataStatus, trace] = await Promise.all([
      fetchDataStatus().catch(() => null),
      fetchRecommendationTrace(runId).catch(() => null),
    ]);
    return <ResultClient run={run} dataStatus={dataStatus} trace={trace} exportUrl={recommendationExportUrl(runId)} />;
  } catch {
    return (
      <div className="card">
        <h1>结果暂不可用</h1>
        <p className="muted">请确认 API 服务已启动，并重新从输入页生成推荐。</p>
      </div>
    );
  }
}