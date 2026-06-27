import { ArrowRight, Database, FileWarning, GraduationCap } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div>
          <h1>湖北高考志愿冲稳保推荐</h1>
          <p className="lead">
            面向湖北普通类本科普通批，按“院校专业组”口径生成冲、稳、保、垫志愿草表。
            系统基于 2023-2025 公开投档线、2026 招生计划样例和规则模型，Doctor.Peak 只做可解释建议。
          </p>
          <div className="actions">
            <Link className="btn primary" href="/input">
              开始测算 <ArrowRight size={18} />
            </Link>
            <Link className="btn secondary" href="/admin">
              查看数据源 <Database size={18} />
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <span>本科普通批 · 平行志愿</span>
          <strong>45</strong>
          <span>院校专业组草表建议</span>
        </div>
      </section>
      <section className="grid cols-3">
        <div className="card">
          <GraduationCap size={26} />
          <h3>湖北口径</h3>
          <p className="muted">首选物理/历史分流，推荐单位始终是院校专业组。</p>
        </div>
        <div className="card">
          <Database size={26} />
          <h3>数据追溯</h3>
          <p className="muted">每个推荐项显示近三年位次、计划变化、置信度和来源。</p>
        </div>
        <div className="card">
          <FileWarning size={26} />
          <h3>不承诺录取</h3>
          <p className="muted">推荐是估计，不替代湖北官方平台和高校招生章程。</p>
        </div>
      </section>
    </>
  );
}

