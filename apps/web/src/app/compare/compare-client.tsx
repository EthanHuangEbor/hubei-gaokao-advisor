"use client";

import Link from "next/link";
import { useState } from "react";
import type { RecommendationRequest, RecommendationRun } from "@hubei-gaokao-advisor/shared-types";
import { runRecommendation } from "@/lib/api";

const strategies: Array<{
  code: RecommendationRequest["priority_strategy"];
  name: string;
  description: string;
}> = [
  { code: "school_first", name: "学校优先", description: "更重视学校层次，但会提示专业组内冷门专业和调剂风险。" },
  { code: "major_first", name: "专业优先", description: "更重视专业匹配，弱化纯学校名气带来的冲动选择。" },
  { code: "city_first", name: "城市优先", description: "更重视城市产业、生活半径和家庭成本。" },
  { code: "employment_first", name: "就业优先", description: "更重视行业周期、技能迁移和考研/就业路径。" },
  { code: "balanced", name: "均衡方案", description: "在学校、专业、城市、风险之间做默认折中。" },
];

function basePayload(strategy: RecommendationRequest["priority_strategy"]): RecommendationRequest {
  return {
    year: 2026,
    province: "湖北",
    batch: "本科普通批",
    category: "普通类",
    first_subject: "physics",
    second_subjects: ["chemistry", "biology"],
    score: 610,
    rank: 26000,
    preferred_cities: strategy === "city_first" ? ["武汉", "宜昌"] : [],
    avoid_cities: [],
    preferred_majors: strategy === "major_first" || strategy === "employment_first" ? ["计算机", "电子信息"] : [],
    avoid_majors: [],
    max_tuition: 60000,
    accept_private_college: true,
    accept_sino_foreign: true,
    accept_adjustment: true,
    priority_strategy: strategy,
  };
}

export function CompareClient() {
  const [runs, setRuns] = useState<Array<{ strategy: (typeof strategies)[number]; run: RecommendationRun }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generateAll() {
    setLoading(true);
    setError("");
    try {
      const results = await Promise.all(
        strategies.map(async (strategy) => ({ strategy, run: await runRecommendation(basePayload(strategy.code)) })),
      );
      setRuns(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "方案生成失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid">
      <section>
        <h1>方案对比</h1>
        <p className="lead">用同一名湖北 2026 物理类样例考生生成五类策略，比较冲稳保垫结构和首个院校专业组。</p>
        <div className="actions">
          <button className="btn primary" type="button" onClick={generateAll} disabled={loading}>
            {loading ? "生成中" : "生成五类方案"}
          </button>
        </div>
        {error ? <p className="notice">{error}</p> : null}
      </section>

      <div className="grid cols-3">
        {strategies.map((strategy) => (
          <div className="card" key={strategy.code}>
            <h3>{strategy.name}</h3>
            <p className="muted">{strategy.description}</p>
          </div>
        ))}
      </div>

      {runs.length ? (
        <section className="grid cols-2">
          {runs.map(({ strategy, run }) => {
            const first = run.items[0];
            return (
              <article className="card" key={strategy.code}>
                <h2>{strategy.name}</h2>
                <p className="muted">{strategy.description}</p>
                <div className="check-row">
                  {(["冲", "稳", "保", "垫"] as const).map((tier) => (
                    <span className={`tier ${tier}`} key={tier}>{tier} {run.tier_counts[tier] ?? 0}</span>
                  ))}
                </div>
                {first ? (
                  <table className="table">
                    <tbody>
                      <tr>
                        <th>首位院校专业组</th>
                        <td>{first.university_name} {first.major_group_code}</td>
                      </tr>
                      <tr>
                        <th>风险/计划变化</th>
                        <td>{first.risk_level} / {Math.round(first.plan_change_ratio * 100)}%</td>
                      </tr>
                      <tr>
                        <th>推荐口径</th>
                        <td>院校专业组，不输出学校名单</td>
                      </tr>
                    </tbody>
                  </table>
                ) : <p className="notice">该策略下推荐池不足。</p>}
                <Link className="btn secondary" href={`/result/${run.run_id}`}>查看结果</Link>
              </article>
            );
          })}
        </section>
      ) : null}

      <div className="notice">任何方案都不能只输出学校名单，最终必须落到院校专业组志愿草表。</div>
    </div>
  );
}
