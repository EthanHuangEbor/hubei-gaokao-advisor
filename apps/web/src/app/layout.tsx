import "./globals.css";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "湖北高考志愿冲稳保推荐",
  description: "基于湖北院校专业组口径的高考志愿推荐 MVP",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="shell">
          <nav className="nav">
            <Link className="brand" href="/">
              Hubei Gaokao Advisor
            </Link>
            <div className="nav-links">
              <Link href="/input">输入</Link>
              <Link href="/compare">对比</Link>
              <Link href="/admin">后台</Link>
            </div>
          </nav>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}

