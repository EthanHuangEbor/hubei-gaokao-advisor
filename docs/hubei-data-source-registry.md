# Hubei Data Source Registry

Official and quasi-official public sources are first priority. Login-only systems are never crawled automatically.

| source | URL | type | policy |
|---|---|---|---|
| 湖北省教育考试院 | https://www.hbea.edu.cn/ | official_home | public pages only |
| 湖北招生考试网 | https://www.hbksw.com/ | quasi_official_home | public pages only |
| 湖北省教育厅高校招生专栏 | https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/ | official_topic | public pages only |
| 湖北省招生数智综合平台 | https://zspt.hubzs.com.cn/ | official_platform | manual only; no login automation |
| 2023-2025 年各批次各类投档线合集 | https://www.hbksw.com/info/38/1771.html | admission_lines | parse only public downloads/pages |
| 2023 年各批次各类投档线合集 | https://www.hbksw.com/info/38/1770.html | admission_lines | parse only public downloads/pages |
| 2024 年各批次各类投档线合集 | https://www.hbksw.com/info/38/1768.html | admission_lines | parse only public downloads/pages |
| 2023-2026 年湖北一分一段表统计表 | https://www.hbksw.com/info/38/1746.html | rank_segments | parse public tables/files |
| 2023 年普通高校招生排序成绩一分一段统计表 | https://www.hbksw.com/info/5/1304.html | rank_segments | parse public tables/files |
| 2024 年普通高校招生排序成绩一分一段统计表 | https://www.hbksw.com/info/38/1748.html | rank_segments | parse public tables/files |
| 2025 年普通高校招生排序成绩一分一段统计表 | https://www.hbksw.com/info/38/1845.html | rank_segments | parse public tables/files |
| 计划查询与志愿填报辅助系统开通及操作指南 | https://www.hbksw.com/info/11/1803.html | admission_plan_guide | guide/reference only; plan data enters through admin upload |
| 2025 年阳光招生政策暨志愿填报问答 | https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202506/t20250618_5697087.shtml | policy_qa | reference only |

`HubeiSourceDiscovery` seeds these sources and can classify public HTML links by title into admission lines, rank segments, plan guides, policy Q&A, or public pages. External hosts and login links are excluded from auto-discovery.

No parser may simulate candidate login, enter captcha, or request account credentials.
