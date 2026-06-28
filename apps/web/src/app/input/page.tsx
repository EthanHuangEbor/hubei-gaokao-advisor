"use client";

import { AlertTriangle, CheckCircle2, GraduationCap, Send, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import type { DataStatus, RecommendationRequest, RankSegment } from "@hubei-gaokao-advisor/shared-types";

import { fetchDataStatus, fetchRankSegments, runRecommendation } from "@/lib/api";

const secondOptions = [
  ["chemistry", "化学"],
  ["biology", "生物"],
  ["politics", "政治"],
  ["geography", "地理"],
] as const;

const steps = [
  { title: "考试信息", icon: GraduationCap },
  { title: "偏好权重", icon: SlidersHorizontal },
  { title: "限制条件", icon: ShieldCheck },
];

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

export default function InputPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [secondSubjects, setSecondSubjects] = useState<string[]>(["chemistry", "biology"]);
  const [firstSubject, setFirstSubject] = useState<"physics" | "history">("physics");
  const [score, setScore] = useState(610);
  const [rank, setRank] = useState(26000);
  const [acceptPrivate, setAcceptPrivate] = useState(true);
  const [acceptSino, setAcceptSino] = useState(true);
  const [rankSegments, setRankSegments] = useState<RankSegment[]>([]);
  const [dataStatus, setDataStatus] = useState<DataStatus | null>(null);

  useEffect(() => {
    fetchRankSegments()
      .then(setRankSegments)
      .catch(() => setRankSegments([]));
    fetchDataStatus()
      .then(setDataStatus)
      .catch(() => setDataStatus(null));
  }, []);

  const rankWarning = useMemo(() => {
    const segment = rankSegments.find(
      (item) => item.year === 2026 && item.first_subject === firstSubject && item.score === score,
    );
    if (!segment) {
      return "";
    }
    if (rank < segment.rank_start || rank > segment.rank_end) {
      return `2026 一分一段中，${score} 分对应约 ${segment.rank_start}-${segment.rank_end} 位；当前位次 ${rank} 需要复核。`;
    }
    return "";
  }, [firstSubject, rank, rankSegments, score]);
  const authenticity = dataStatus?.data_authenticity;
  const realCuratedReady = Boolean(dataStatus?.real_curated_ready ?? authenticity?.real_curated_ready);
  const strictRejecting = Boolean(authenticity?.strict_real_data_required && !realCuratedReady);

  function handleFirstSubject(value: "physics" | "history") {
    setFirstSubject(value);
    if (value === "physics") {
      setScore(610);
      setRank(26000);
      setSecondSubjects((current) => (current.includes("chemistry") ? current : ["chemistry", ...current]));
    } else {
      setScore(585);
      setRank(18000);
      setSecondSubjects((current) => current.filter((item) => item !== "chemistry"));
    }
  }

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
      score,
      rank,
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
    <div className="grid">
      <section className="input-header">
        <div>
          <h1>输入考生信息</h1>
          <p className="lead">这里只处理成绩、位次、选科和偏好；不会收集姓名、身份证、准考证号、手机号或报名号。</p>
        </div>
        <div className="notice compact">
          <ShieldCheck size={18} /> 个人身份信息不会进入 MiniMax 调用或本地推荐记录。
        </div>
      </section>

      <div className="step-flow">
        {steps.map(({ title, icon: Icon }, index) => (
          <div className="step-pill" key={title}>
            <Icon size={16} /> {index + 1}. {title}
          </div>
        ))}
      </div>

      {!realCuratedReady && authenticity ? (
        <div role="alert" className="notice compact">
          <AlertTriangle size={18} /> 当前数据不是真实 curated（{dataKindLabel(authenticity.dataset_kind)}），不能作为真实填报依据。请先在后台完成官方数据入库。
        </div>
      ) : null}
      {strictRejecting ? (
        <div role="alert" className="notice compact">
          <AlertTriangle size={18} /> 严格真实数据已开启，当前生成会被后端拒绝。
        </div>
      ) : null}

      <form className="form" onSubmit={submit}>
        <section className="card form-section">
          <h2>1. 考试信息</h2>
          <div className="grid cols-3">
            <div className="field">
              <label>首选科目</label>
              <select value={firstSubject} onChange={(event) => handleFirstSubject(event.target.value as "physics" | "history")}>
                <option value="physics">物理</option>
                <option value="history">历史</option>
              </select>
            </div>
            <div className="field">
              <label>成绩</label>
              <input name="score" type="number" value={score} min={0} max={750} onChange={(event) => setScore(Number(event.target.value || 0))} />
            </div>
            <div className="field">
              <label>位次</label>
              <input name="rank" type="number" value={rank} min={1} onChange={(event) => setRank(Number(event.target.value || 1))} />
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
          {rankWarning ? (
            <p className="notice compact">
              <AlertTriangle size={18} /> {rankWarning}
            </p>
          ) : (
            <p className="muted inline-status"><CheckCircle2 size={16} /> 成绩与位次未触发 2026 一分一段异常提醒。</p>
          )}
        </section>

        <section className="card form-section">
          <h2>2. 偏好权重</h2>
          <div className="grid cols-2">
            <div className="field">
              <label>偏好城市</label>
              <input name="preferred_cities" placeholder="武汉, 宜昌" />
            </div>
            <div className="field">
              <label>回避城市</label>
              <input name="avoid_cities" placeholder="可留空" />
            </div>
            <div className="field">
              <label>偏好专业</label>
              <input name="preferred_majors" placeholder="计算机, 法学" />
            </div>
            <div className="field">
              <label>回避专业</label>
              <input name="avoid_majors" placeholder="土木" />
            </div>
          </div>
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
        </section>

        <section className="card form-section">
          <h2>3. 限制条件</h2>
          <div className="grid cols-2">
            <div className="field">
              <label>最高学费</label>
              <input name="max_tuition" type="number" defaultValue={60000} min={0} />
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
          {error ? <p className="notice compact">{error}</p> : null}
          <button className="btn primary" disabled={loading} type="submit">
            {loading ? "生成中" : "生成推荐"} <Send size={18} />
          </button>
        </section>
      </form>
    </div>
  );
}

function splitList(value: string): string[] {
  return value
    .split(/[,，、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}
