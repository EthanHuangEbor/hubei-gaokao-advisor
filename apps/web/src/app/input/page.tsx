"use client";

import { Send, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import type { RecommendationRequest } from "@hubei-gaokao-advisor/shared-types";
import { runRecommendation } from "@/lib/api";

const secondOptions = [
  ["chemistry", "化学"],
  ["biology", "生物"],
  ["politics", "政治"],
  ["geography", "地理"],
];

export default function InputPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [secondSubjects, setSecondSubjects] = useState<string[]>(["chemistry", "biology"]);
  const [firstSubject, setFirstSubject] = useState<"physics" | "history">("physics");
  const [acceptPrivate, setAcceptPrivate] = useState(true);
  const [acceptSino, setAcceptSino] = useState(true);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const payload: RecommendationRequest = {
      year: 2026,
      province: "湖北",
      batch: "本科普通批",
      category: "普通类",
      first_subject: firstSubject,
      second_subjects: secondSubjects,
      score: Number(data.get("score") || 600),
      rank: Number(data.get("rank") || 26000),
      preferred_cities: splitList(String(data.get("preferred_cities") || "")),
      avoid_cities: splitList(String(data.get("avoid_cities") || "")),
      preferred_majors: splitList(String(data.get("preferred_majors") || "")),
      avoid_majors: splitList(String(data.get("avoid_majors") || "")),
      max_tuition: Number(data.get("max_tuition") || 60000),
      accept_private_college: acceptPrivate,
      accept_sino_foreign: acceptSino,
      accept_adjustment: Boolean(data.get("accept_adjustment")),
      priority_strategy: String(data.get("priority_strategy") || "balanced") as RecommendationRequest["priority_strategy"],
    };
    try {
      const run = await runRecommendation(payload);
      router.push(`/result/${run.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid cols-2">
      <section>
        <h1>输入考生信息</h1>
        <p className="lead">
          这里只需要成绩、位次、选科和偏好；不会收集姓名、身份证、准考证号、手机号或报名号。
        </p>
        <div className="notice">
          <ShieldCheck size={18} /> 个人身份信息不会进入 MiniMax 调用或本地推荐记录。
        </div>
      </section>
      <form className="card form" onSubmit={submit}>
        <div className="grid cols-2">
          <div className="field">
            <label>首选科目</label>
            <select value={firstSubject} onChange={(event) => setFirstSubject(event.target.value as "physics" | "history")}>
              <option value="physics">物理</option>
              <option value="history">历史</option>
            </select>
          </div>
          <div className="field">
            <label>位次</label>
            <input name="rank" type="number" defaultValue={firstSubject === "physics" ? 26000 : 18000} min={1} />
          </div>
          <div className="field">
            <label>成绩</label>
            <input name="score" type="number" defaultValue={firstSubject === "physics" ? 610 : 585} min={0} max={750} />
          </div>
          <div className="field">
            <label>最高学费</label>
            <input name="max_tuition" type="number" defaultValue={60000} min={0} />
          </div>
        </div>
        <div className="field">
          <label>再选科目</label>
          <div className="check-row">
            {secondOptions.map(([value, label]) => (
              <label key={value}>
                <input
                  type="checkbox"
                  checked={secondSubjects.includes(value)}
                  onChange={(event) =>
                    setSecondSubjects((current) =>
                      event.target.checked ? [...current, value] : current.filter((item) => item !== value),
                    )
                  }
                />
                {label}
              </label>
            ))}
          </div>
        </div>
        <div className="grid cols-2">
          <div className="field">
            <label>偏好城市</label>
            <input name="preferred_cities" placeholder="武汉,宜昌" />
          </div>
          <div className="field">
            <label>回避城市</label>
            <input name="avoid_cities" placeholder="可留空" />
          </div>
          <div className="field">
            <label>偏好专业</label>
            <input name="preferred_majors" placeholder="计算机,法学" />
          </div>
          <div className="field">
            <label>回避专业</label>
            <input name="avoid_majors" placeholder="土木" />
          </div>
        </div>
        <div className="grid cols-2">
          <div className="field">
            <label>优先策略</label>
            <select name="priority_strategy" defaultValue="balanced">
              <option value="balanced">均衡</option>
              <option value="school_first">学校优先</option>
              <option value="major_first">专业优先</option>
              <option value="city_first">城市优先</option>
              <option value="employment_first">就业优先</option>
            </select>
          </div>
          <div className="field">
            <label>录取规则偏好</label>
            <div className="check-row">
              <label>
                <input type="checkbox" defaultChecked name="accept_adjustment" /> 接受调剂
              </label>
              <label>
                <input type="checkbox" checked={acceptPrivate} onChange={(event) => setAcceptPrivate(event.target.checked)} /> 接受民办
              </label>
              <label>
                <input type="checkbox" checked={acceptSino} onChange={(event) => setAcceptSino(event.target.checked)} /> 接受中外合作
              </label>
            </div>
          </div>
        </div>
        {error ? <p className="notice">{error}</p> : null}
        <button className="btn primary" disabled={loading} type="submit">
          {loading ? "生成中" : "生成推荐"} <Send size={18} />
        </button>
      </form>
    </div>
  );
}

function splitList(value: string): string[] {
  return value
    .split(/[,\s，、]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

