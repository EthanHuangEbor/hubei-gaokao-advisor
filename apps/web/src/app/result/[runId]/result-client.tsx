"use client";

import { AlertTriangle, Download, ExternalLink, Filter, Info } from "lucide-react";
import { useMemo, useState } from "react";

import type { DataStatus, RecommendationRun, RecommendationTrace, Tier } from "@hubei-gaokao-advisor/shared-types";

const TIERS: Tier[] = ["冲", "稳", "保", "垫"];
const TIER_LABEL: Record<string, string> = {
  all: "全部",
  冲: "冲",
  稳: "稳",
  保: "保",
  垫: "垫",
};

interface ResultClientProps {
  run: RecommendationRun;
  dataStatus?: DataStatus | null;
  trace?: RecommendationTrace | null;
  exportUrl: string;
}

function percent(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "未评分";
}

function decimal(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

function list(values: string[] | undefined) {
  return values?.length ? values.join("；") : "-";
}

function planChangeText(item: RecommendationRun["items"][number]) {
  if (item.plan_status === "missing_current_plan" || item.plan_change_ratio === null) {
    return "2026 计划缺失，计划变化评分关闭";
  }
  const sign = item.seat_abs_change >= 0 ? "+" : "";
  return `${item.last_year_plan_seats} → ${item.current_plan_seats}（${percent(item.plan_change_ratio)}，${sign}${item.seat_abs_change}）`;
}

function nonEmptyStrings(values: unknown) {
  return Array.isArray(values) ? values.filter((value): value is string => typeof value === "string" && value.trim().length > 0) : [];
}

export function ResultClient({ run, dataStatus, trace, exportUrl }: ResultClientProps) {
  const [tierFilter, setTierFilter] = useState<"all" | Tier>("all");
  const advice = run.doctor_peak_advice;
  const visibleItems = useMemo(
    () => (tierFilter === "all" ? run.items : run.items.filter((item) => item.tier === tierFilter)),
    [run.items, tierFilter],
  );
  const warnings = new Set<string>(trace?.warnings ?? []);
  if (run.items.some((item) => item.plan_status === "missing_current_plan")) {
    warnings.add("2026 招生计划缺失，专业明细和计划变化需导入后复核");
  }
  const risks = nonEmptyStrings(advice?.risks);
  const nextChecks = nonEmptyStrings(advice?.next_checks);

  return (
    <div className="grid">
      <section className="result-header">
        <div>
          <h1>推荐结果</h1>
          <p className="lead">{run.strategy_note}</p>
        </div>
        <a className="btn primary" href={exportUrl}>
          <Download size={18} /> CSV 导出
        </a>
      </section>

      <section className="summary-strip">
        {TIERS.map((tier) => (
          <div className="summary-cell" key={tier}>
            <span className={`tier ${tier}`}>{tier}</span>
            <strong>{run.tier_counts[tier] ?? 0}</strong>
          </div>
        ))}
        <div className="summary-cell wide">
          <span className="muted">数据</span>
          <strong>{String(dataStatus?.runtime_source ?? trace?.data_quality?.plan_status ?? "unknown")}</strong>
        </div>
        <div className="summary-cell wide">
          <span className="muted">候选池</span>
          <strong>{trace?.pool_counts?.final_plan ?? run.items.length}/{trace?.pool_counts?.after_subject_filter ?? "-"}</strong>
        </div>
      </section>

      {warnings.size ? (
        <div className="notice compact">
          <AlertTriangle size={18} /> {[...warnings].join("；")}
        </div>
      ) : null}

      <section className="card">
        <h2>Doctor.Peak 总评</h2>
        <p>{advice?.summary ?? "本次推荐已生成结构化规则结果，请结合招生章程和官方发布数据复核。"}</p>
        {advice?.doctor_peak_view ? <p className="muted">{advice.doctor_peak_view}</p> : null}
        {risks.length ? <p><strong>风险提示：</strong>{list(risks)}</p> : null}
        {nextChecks.length ? <p><strong>下一步核验：</strong>{list(nextChecks)}</p> : null}
      </section>

      <section className="result-toolbar">
        <div className="check-row">
          <Filter size={18} />
          {["all", ...TIERS].map((tier) => (
            <button
              className={`btn ${tierFilter === tier ? "primary" : "secondary"}`}
              key={tier}
              type="button"
              onClick={() => setTierFilter(tier as "all" | Tier)}
            >
              {TIER_LABEL[tier]}
            </button>
          ))}
        </div>
      </section>

      <section className="card table-card">
        <h2>45 个院校专业组志愿表</h2>
        <table className="table result-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>档位</th>
              <th>院校专业组</th>
              <th>历史位次</th>
              <th>计划状态</th>
              <th>主要理由</th>
            </tr>
          </thead>
          <tbody>
            {visibleItems.map((item) => (
              <tr key={`${item.position}-${item.major_group_code}`}>
                <td>{item.position}</td>
                <td><span className={`tier ${item.tier}`}>{item.tier}</span></td>
                <td>
                  <strong>{item.university_name}</strong>
                  <div className="muted">{item.major_group_code} · {item.major_group_name}</div>
                  <div className="muted">波动系数 {decimal(item.volatility_score)} · 专业组变化 {item.group_change_flag} · 来源追溯</div>
                  <details>
                    <summary>展开详情</summary>
                    <div className="details-grid">
                      <span>专业：{item.included_majors.join("、")}</span>
                      <span>三年分数：{item.min_score_2023 ?? "-"} / {item.min_score_2024 ?? "-"} / {item.min_score_2025 ?? "-"}</span>
                      <span>计划变化：{planChangeText(item)}</span>
                      <span>位次差：{item.rank_gap}（{percent(item.rank_gap_ratio)}）</span>
                      <span>波动系数：{decimal(item.volatility_score)}</span>
                      <span>专业组变化：{item.group_change_flag}</span>
                      <span>偏好：城市 {decimal(item.city_match_score)} / 专业 {decimal(item.major_match_score)} / 就业 {decimal(item.employment_preference_score)}</span>
                      <span>限制风险：{decimal(item.restriction_risk_score)}</span>
                      <span>同位次参考：{item.same_rank_hit_count} 项，置信 {decimal(item.same_rank_reference_confidence)}</span>
                    </div>
                    {item.doctor_peak_explanation ? <p><strong>Doctor.Peak：</strong>{item.doctor_peak_explanation}</p> : null}
                    {item.main_warnings.length ? <p><strong>警告：</strong>{list(item.main_warnings)}</p> : null}
                    <strong>来源追溯：</strong>
                    <div className="check-row">
                      {item.source_links.map((link) => (
                        <a className="btn secondary" href={link} key={link} rel="noreferrer" target="_blank">
                          来源 <ExternalLink size={16} />
                        </a>
                      ))}
                    </div>
                  </details>
                </td>
                <td>{item.min_rank_2023 ?? "-"} / {item.min_rank_2024 ?? "-"} / {item.min_rank_2025 ?? "-"}</td>
                <td>{item.plan_status === "ready" ? planChangeText(item) : "缺 2026 计划"}</td>
                <td>{list(item.main_reasons)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {process.env.NODE_ENV !== "production" && trace ? (
        <details className="card">
          <summary><Info size={16} /> Dev trace</summary>
          <pre className="trace-json">{JSON.stringify(trace, null, 2)}</pre>
        </details>
      ) : null}

      <div className="notice compact">{run.disclaimer}</div>
    </div>
  );
}