"use client";

import { useEffect, useState } from "react";

import type { DataStatus, DoctorPeakProbeResult, DoctorPeakStatus } from "@hubei-gaokao-advisor/shared-types";

import {
  createParseJob,
  fetchDataStatus,
  fetchDoctorPeakStatus,
  fetchMiniMaxLogs,
  fetchParseJobs,
  fetchRawDocuments,
  runDataQuality,
  runDoctorPeakProbe,
  runHubeiDataStage,
  uploadHubeiPlan,
  type ParseJob,
  type QualityFinding,
  type RawDocument,
} from "@/lib/api";

function parseLabel(document: RawDocument) {
  if (!document.parse_summary || Object.keys(document.parse_summary).length === 0) {
    return "待解析";
  }
  if (document.parse_summary.note) {
    return document.parse_summary.note;
  }
  return `有效候选 ${document.parse_summary.valid_count ?? 0}`;
}

const DATA_KIND_LABEL: Record<string, string> = {
  real_curated: "真实",
  fixture_seed: "样例",
  mixed: "混合",
  missing: "缺失",
  incomplete: "不完整",
};

function dataKindLabel(kind?: string) {
  return kind ? DATA_KIND_LABEL[kind] ?? kind : "未知";
}

function fileSummary(status: DataStatus | null) {
  const requiredFiles = status?.data_authenticity?.required_files;
  if (requiredFiles) {
    return `${Object.values(requiredFiles).filter(Boolean).length}/${Object.keys(requiredFiles).length}`;
  }
  const total = Object.keys(status?.curated_files ?? {}).length;
  if (!total) {
    return "-";
  }
  return `${status?.curated_ready ? total : 0}/${total}`;
}

function callLabel(errorCode?: string | null) {
  return errorCode ? `fallback：${errorCode}` : "ok";
}

export function AdminClient({ initialDataStatus }: { initialDataStatus?: DataStatus | null }) {
  const [file, setFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<RawDocument[]>([]);
  const [jobs, setJobs] = useState<ParseJob[]>([]);
  const [findings, setFindings] = useState<QualityFinding[]>([]);
  const [miniMaxLogCount, setMiniMaxLogCount] = useState(0);
  const [dataStatus, setDataStatus] = useState<DataStatus | null>(initialDataStatus ?? null);
  const [doctorPeakStatus, setDoctorPeakStatus] = useState<DoctorPeakStatus | null>(null);
  const [probeResult, setProbeResult] = useState<DoctorPeakProbeResult | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [jobStatus, setJobStatus] = useState("");
  const [qualityStatus, setQualityStatus] = useState("");
  const [dataStageStatus, setDataStageStatus] = useState("");
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isQueueing, setIsQueueing] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [runningStage, setRunningStage] = useState<string | null>(null);
  const [isProbing, setIsProbing] = useState(false);
  const [diagnosticError, setDiagnosticError] = useState("");

  useEffect(() => {
    fetchRawDocuments()
      .then(setDocuments)
      .catch(() => setDocuments([]));
    fetchParseJobs()
      .then(setJobs)
      .catch(() => setJobs([]));
    fetchMiniMaxLogs()
      .then((logs) => setMiniMaxLogCount(logs.length))
      .catch(() => setMiniMaxLogCount(0));
    fetchDataStatus()
      .then(setDataStatus)
      .catch(() => undefined);
    fetchDoctorPeakStatus()
      .then(setDoctorPeakStatus)
      .catch(() => setDoctorPeakStatus(null));
  }, []);

  async function handleUpload() {
    if (!file) {
      setError("请选择 2026 招生计划文件");
      return;
    }
    setError("");
    setUploadStatus("");
    setIsUploading(true);
    try {
      const result = await uploadHubeiPlan(file);
      setUploadStatus(`${result.status} · ${result.filename}`);
      setDocuments((current) => [result, ...current.filter((item) => item.id !== result.id)]);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "上传失败");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleQueueParseJob() {
    setError("");
    setJobStatus("");
    setIsQueueing(true);
    try {
      const job = await createParseJob();
      setJobStatus(`解析任务已排队 · ${job.job_type}`);
      setJobs((current) => [job, ...current.filter((item) => item.job_id !== job.job_id)]);
    } catch (jobError) {
      setError(jobError instanceof Error ? jobError.message : "解析任务排队失败");
    } finally {
      setIsQueueing(false);
    }
  }

  async function handleQualityCheck() {
    setError("");
    setQualityStatus("");
    setIsChecking(true);
    try {
      const result = await runDataQuality();
      setFindings(result.findings);
      setQualityStatus(`质量检查完成，发现 ${result.findings.length} 项`);
    } catch (qualityError) {
      setError(qualityError instanceof Error ? qualityError.message : "数据质量检查失败");
    } finally {
      setIsChecking(false);
    }
  }

  async function handleDataStage(stage: "download" | "parse" | "quality" | "promote" | "seed") {
    setError("");
    setDataStageStatus("");
    setRunningStage(stage);
    try {
      const result = await runHubeiDataStage(stage);
      setDataStageStatus(`${stage} 完成 · ${result.status}`);
      fetchDataStatus()
        .then(setDataStatus)
        .catch(() => undefined);
    } catch (stageError) {
      setError(stageError instanceof Error ? stageError.message : `${stage} 失败`);
    } finally {
      setRunningStage(null);
    }
  }

  async function handleDoctorPeakProbe() {
    setDiagnosticError("");
    setProbeResult(null);
    setIsProbing(true);
    try {
      const result = await runDoctorPeakProbe();
      setProbeResult(result);
      fetchDoctorPeakStatus()
        .then(setDoctorPeakStatus)
        .catch(() => undefined);
    } catch (probeError) {
      setProbeResult(null);
      setDiagnosticError(probeError instanceof Error ? probeError.message : "Doctor.Peak 探测失败");
    } finally {
      setIsProbing(false);
    }
  }

  const authenticity = dataStatus?.data_authenticity;
  const realCuratedReady = Boolean(dataStatus?.real_curated_ready ?? authenticity?.real_curated_ready);
  const strictRejecting = Boolean(authenticity?.strict_real_data_required && !realCuratedReady);
  const latestError = doctorPeakStatus?.latest_call.error_code ?? doctorPeakStatus?.minimax.error_code ?? null;
  const probeError = probeResult?.error_code ?? null;

  return (
    <>
      <section className="card">
        <div className="grid cols-2">
          <div>
            <h2>Doctor.Peak / MiniMax</h2>
            <div className="summary-strip">
              <div className="summary-cell wide">
                <span className="muted">MiniMax</span>
                <strong>{doctorPeakStatus ? (doctorPeakStatus.minimax.configured ? "已配置" : "fallback") : "未加载"}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">Doctor.Peak</span>
                <strong>{doctorPeakStatus?.doctor_peak.status ?? "unknown"}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">最近调用</span>
                <strong>{doctorPeakStatus?.latest_call.request_id ? callLabel(latestError) : doctorPeakStatus ? "无记录" : "未加载"}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">探测</span>
                <strong>{probeResult ? callLabel(probeError) : "未运行"}</strong>
              </div>
            </div>
            <p className="muted">Key：{doctorPeakStatus?.minimax.masked_api_key || "未检测到"}</p>
            <p className="muted">模型：{doctorPeakStatus?.minimax.model ?? "-"} · 接口：{doctorPeakStatus?.minimax.endpoint_style ?? "-"}</p>
            <p className="muted">Base URL：{doctorPeakStatus?.minimax.base_url ?? "-"}</p>
            <p className="muted">错误：{doctorPeakStatus?.minimax.error_code ?? "无"}</p>
            {doctorPeakStatus?.minimax.error_message ? <p className="notice compact">{doctorPeakStatus.minimax.error_message}</p> : null}
            <button className="btn secondary" type="button" onClick={handleDoctorPeakProbe} disabled={isProbing}>
              {isProbing ? "探测中" : "测试 Doctor.Peak"}
            </button>
            {diagnosticError ? <p className="notice compact">{diagnosticError}</p> : null}
          </div>
          <div>
            <h2>数据真实性</h2>
            <div className="summary-strip">
              <div className="summary-cell wide">
                <span className="muted">类型</span>
                <strong>{dataKindLabel(authenticity?.dataset_kind)}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">真实 curated</span>
                <strong>{authenticity ? (realCuratedReady ? "已就绪" : "未就绪") : "未加载"}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">严格保护</span>
                <strong>{strictRejecting ? "会拒绝" : authenticity?.strict_real_data_required ? "开启" : "关闭"}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">Curated 文件</span>
                <strong>{fileSummary(dataStatus)}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">审核行</span>
                <strong>{authenticity?.approved_row_count ?? 0}/{authenticity?.pending_row_count ?? 0}</strong>
              </div>
              <div className="summary-cell wide">
                <span className="muted">样例标记</span>
                <strong>{authenticity?.fixture_marker_count ?? 0}</strong>
              </div>
            </div>
            <p className="muted">投档线 {dataStatus?.counts.admission_records ?? "-"} · 一分一段 {dataStatus?.counts.rank_segments ?? "-"} · 招生计划 {dataStatus?.counts.admission_plans ?? "-"}</p>
            {authenticity && !realCuratedReady ? (
              <div role="alert" className="notice compact">当前使用样例或未审核数据，不能作为真实填报依据。</div>
            ) : null}
            {strictRejecting ? <div role="alert" className="notice compact">严格真实数据已开启，推荐会被后端拒绝。</div> : null}
          </div>
        </div>
      </section>

      <section className="card">
      <h2>2026 招生计划上传与质量检查</h2>
      <div className="form">
        <div className="field">
          <label htmlFor="hubei-plan-upload">官方 Excel / CSV / PDF 文件</label>
          <input
            id="hubei-plan-upload"
            name="hubei-plan-upload"
            type="file"
            accept=".csv,.xlsx,.xls,.pdf,text/csv,application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>
        <div className="actions">
          <button className="btn primary" type="button" onClick={handleUpload} disabled={isUploading}>
            {isUploading ? "上传中" : "上传招生计划"}
          </button>
          <button className="btn secondary" type="button" onClick={handleQueueParseJob} disabled={isQueueing}>
            {isQueueing ? "排队中" : "排队解析任务"}
          </button>
          <button className="btn secondary" type="button" onClick={handleQualityCheck} disabled={isChecking}>
            {isChecking ? "检查中" : "运行数据质量检查"}
          </button>
        </div>
        <div className="actions data-stage-actions">
          {(["download", "parse", "quality", "promote", "seed"] as const).map((stage) => (
            <button
              className="btn secondary"
              disabled={runningStage !== null}
              key={stage}
              type="button"
              onClick={() => handleDataStage(stage)}
            >
              {runningStage === stage ? "运行中" : stage}
            </button>
          ))}
        </div>
        {uploadStatus ? <p className="muted">{uploadStatus}</p> : null}
        {jobStatus ? <p className="muted">{jobStatus}</p> : null}
        {qualityStatus ? <p className="muted">{qualityStatus}</p> : null}
        {dataStageStatus ? <p className="muted">{dataStageStatus}</p> : null}
        {error ? <p className="notice">{error}</p> : null}
      </div>

      <div className="grid cols-2">
        <div>
          <h3>原始文件队列</h3>
          <table className="table">
            <thead>
              <tr>
                <th>文件</th>
                <th>类型</th>
                <th>解析</th>
                <th>复核</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={4}>暂无上传文件</td>
                </tr>
              ) : (
                documents.map((document) => (
                  <tr key={document.id}>
                    <td>{document.filename}</td>
                    <td>{document.document_type}</td>
                    <td>{parseLabel(document)}</td>
                    <td>{document.review_status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div>
          <h3>解析任务</h3>
          <table className="table">
            <thead>
              <tr>
                <th>类型</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={2}>暂无任务</td>
                </tr>
              ) : (
                jobs.slice(0, 5).map((job) => (
                  <tr key={job.job_id}>
                    <td>{job.job_type}</td>
                    <td>{job.status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <p className="muted">MiniMax 日志 {miniMaxLogCount} 条；Doctor.Peak 仅解释，不改变排序。</p>
        </div>
      </div>

      <section>
        <h3>质量检查结果</h3>
        <table className="table">
          <thead>
            <tr>
              <th>级别</th>
              <th>对象</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            {findings.length === 0 ? (
              <tr>
                <td colSpan={3}>尚未运行</td>
              </tr>
            ) : (
              findings.slice(0, 8).map((finding, index) => (
                <tr key={`${finding.entity}-${finding.message}-${index}`}>
                  <td>{finding.severity}</td>
                  <td>{finding.entity}</td>
                  <td>{finding.message}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </section>
    </>
  );
}
