import { AlertTriangle, ExternalLink } from "lucide-react";
import { fetchRun } from "@/lib/api";

const TIERS = ["\u51b2", "\u7a33", "\u4fdd", "\u57ab"] as const;
const T = {
  resultTitle: "\u63a8\u8350\u7ed3\u679c",
  doctorPeakSummary: "Doctor.Peak \u603b\u8bc4",
  fallbackAdvice: "\u672c\u6b21\u63a8\u8350\u5df2\u751f\u6210\u7ed3\u6784\u5316\u89c4\u5219\u7ed3\u679c\uff0c\u8bf7\u7ed3\u5408\u62db\u751f\u7ae0\u7a0b\u548c\u5b98\u65b9\u53d1\u5e03\u6570\u636e\u590d\u6838\u3002",
  overallStrategy: "\u6574\u4f53\u7b56\u7565",
  doctorPeakView: "Doctor.Peak \u89c6\u89d2",
  riskPrompt: "\u98ce\u9669\u63d0\u793a\uff1a",
  parentPrompt: "\u5bb6\u957f\u6c9f\u901a\uff1a",
  studentPrompt: "\u5b66\u751f\u6c9f\u901a\uff1a",
  nextChecks: "\u4e0b\u4e00\u6b65\u6838\u9a8c\uff1a",
  resultUnavailable: "\u7ed3\u679c\u6682\u4e0d\u53ef\u7528",
  retryHint: "\u8bf7\u786e\u8ba4 API \u670d\u52a1\u5df2\u542f\u52a8\uff0c\u5e76\u91cd\u65b0\u4ece\u8f93\u5165\u9875\u751f\u6210\u63a8\u8350\u3002",
  majorGroup: "\u9662\u6821\u4e13\u4e1a\u7ec4",
  rank3y: "\u8fd1\u4e09\u5e74\u4f4d\u6b21",
  score3y: "\u8fd1\u4e09\u5e74\u5206\u6570",
  planChange: "\u8ba1\u5212\u53d8\u5316",
  rankGap: "\u4f4d\u6b21\u5dee",
  volatility: "\u6ce2\u52a8\u7cfb\u6570",
  probabilityBand: "\u6982\u7387\u6863",
  risk: "\u98ce\u9669",
  groupChange: "\u4e13\u4e1a\u7ec4\u53d8\u5316",
  subjectChange: "\u9009\u79d1\u53d8\u5316",
  sameRankReference: "\u540c\u4f4d\u6b21\u53c2\u8003",
  itemsConfidence: "\u9879\uff0c\u7f6e\u4fe1",
  preferenceMatch: "\u504f\u597d\u5339\u914d",
  dataConfidence: "\u6570\u636e\u7f6e\u4fe1\u5ea6",
  doctorPeakItem: "Doctor.Peak\uff1a",
  reasons: "\u7406\u7531\uff1a",
  warnings: "\u7ea2\u65d7\uff1a",
  sourceTrace: "\u6765\u6e90\u8ffd\u6eaf\uff1a",
  source: "\u6765\u6e90",
  listSeparator: "\u3001",
  semicolon: "\uff1b",
  arrow: "\u2192",
  leftParen: "\uff08",
  rightParen: "\uff09",
  comma: "\uff0c",
};

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function decimal(value: number) {
  return Number.isFinite(value) ? value.toFixed(2) : "-";
}

function nonEmptyStrings(values: unknown) {
  return Array.isArray(values) ? values.filter((value): value is string => typeof value === "string" && value.trim().length > 0) : [];
}

function joinAdvice(values: string[]) {
  return values.join(T.semicolon);
}

export default async function ResultPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  try {
    const run = await fetchRun(runId);
    const advice = run.doctor_peak_advice;
    const risks = nonEmptyStrings(advice?.risks);
    const parentPoints = nonEmptyStrings(advice?.parent_talking_points);
    const studentPoints = nonEmptyStrings(advice?.student_talking_points);
    const nextChecks = nonEmptyStrings(advice?.next_checks);

    return (
      <div className="grid">
        <section>
          <h1>{T.resultTitle}</h1>
          <p className="lead">{run.strategy_note}</p>
          <div className="check-row">
            {TIERS.map((tier) => (
              <span key={tier} className={`tier ${tier}`}>
                {tier} {run.tier_counts[tier] ?? 0}
              </span>
            ))}
          </div>
        </section>
        <div className="notice">
          <AlertTriangle size={18} /> {run.disclaimer}
        </div>
        <section className="card">
          <h2>{T.doctorPeakSummary}</h2>
          <p>{advice?.summary ?? T.fallbackAdvice}</p>
          <div className="grid cols-2">
            {advice?.overall_strategy ? (
              <div>
                <strong>{T.overallStrategy}</strong>
                <p className="muted">{advice.overall_strategy}</p>
              </div>
            ) : null}
            {advice?.doctor_peak_view ? (
              <div>
                <strong>{T.doctorPeakView}</strong>
                <p className="muted">{advice.doctor_peak_view}</p>
              </div>
            ) : null}
          </div>
          {risks.length ? <p><strong>{T.riskPrompt}</strong>{joinAdvice(risks)}</p> : null}
          {parentPoints.length ? <p><strong>{T.parentPrompt}</strong>{joinAdvice(parentPoints)}</p> : null}
          {studentPoints.length ? <p><strong>{T.studentPrompt}</strong>{joinAdvice(studentPoints)}</p> : null}
          {nextChecks.length ? <p><strong>{T.nextChecks}</strong>{joinAdvice(nextChecks)}</p> : null}
          {advice?.disclaimer ? <p className="muted">{advice.disclaimer}</p> : null}
        </section>
        <section className="grid">
          {run.items.map((item, index) => (
            <article className="card" key={`${item.major_group_code}-${index}`}>
              <div className="check-row">
                <span className={`tier ${item.tier}`}>{item.tier}</span>
                <strong>{index + 1}. {item.university_name}</strong>
                <span>{T.majorGroup} {item.major_group_code}</span>
              </div>
              <h3>{item.major_group_name}</h3>
              <p className="muted">{item.included_majors.join(T.listSeparator)}</p>
              <table className="table">
                <tbody>
                  <tr>
                    <th>{T.rank3y}</th>
                    <td>{item.min_rank_2023 ?? "-"} / {item.min_rank_2024 ?? "-"} / {item.min_rank_2025 ?? "-"}</td>
                    <th>{T.score3y}</th>
                    <td>{item.min_score_2023 ?? "-"} / {item.min_score_2024 ?? "-"} / {item.min_score_2025 ?? "-"}</td>
                  </tr>
                  <tr>
                    <th>{T.planChange}</th>
                    <td>{item.last_year_plan_seats} {T.arrow} {item.current_plan_seats}{T.leftParen}{percent(item.plan_change_ratio)}{T.comma}{item.seat_abs_change >= 0 ? "+" : ""}{item.seat_abs_change}{T.rightParen}</td>
                    <th>{T.rankGap}</th>
                    <td>{item.rank_gap}{T.leftParen}{percent(item.rank_gap_ratio)}{T.rightParen}</td>
                  </tr>
                  <tr>
                    <th>{T.volatility}</th>
                    <td>{decimal(item.volatility_score)}</td>
                    <th>{T.probabilityBand}</th>
                    <td>{item.estimated_probability_band}</td>
                  </tr>
                  <tr>
                    <th>{T.risk}</th>
                    <td>{item.risk_level}</td>
                    <th>{T.groupChange}</th>
                    <td>{item.group_change_flag}</td>
                  </tr>
                  <tr>
                    <th>{T.subjectChange}</th>
                    <td>{item.subject_requirement_change_flag}</td>
                    <th>{T.sameRankReference}</th>
                    <td>{item.same_rank_hit_count} {T.itemsConfidence} {decimal(item.same_rank_reference_confidence)}</td>
                  </tr>
                  <tr>
                    <th>{T.preferenceMatch}</th>
                    <td>{decimal(item.preference_match_score)}</td>
                    <th>{T.dataConfidence}</th>
                    <td>{decimal(item.data_confidence_score)}</td>
                  </tr>
                </tbody>
              </table>
              <p><strong>{T.doctorPeakItem}</strong>{item.doctor_peak_explanation}</p>
              <p><strong>{T.reasons}</strong>{item.reasons.join(T.semicolon)}</p>
              {item.warnings.length ? <p><strong>{T.warnings}</strong>{item.warnings.join(T.semicolon)}</p> : null}
              <div>
                <strong>{T.sourceTrace}</strong>
                <div className="check-row">
                  {item.source_links.map((link) => (
                    <a className="btn secondary" href={link} key={link} rel="noreferrer" target="_blank">
                      {T.source} <ExternalLink size={16} />
                    </a>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>
    );
  } catch {
    return (
      <div className="card">
        <h1>{T.resultUnavailable}</h1>
        <p className="muted">{T.retryHint}</p>
      </div>
    );
  }
}