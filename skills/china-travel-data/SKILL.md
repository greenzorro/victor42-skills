---
name: china-travel-data
description: Use when an agent needs live China travel data — geocoding, POI search, driving routes and map tiles (高德 Amap), flight schedules, transfers and fares (飞常准 Variflight), high-speed rail tickets (携程 Ctrip), weather and city coordinates (Open-Meteo) — or the planning order and mode trade-offs behind a trip. Triggers on 查航班 / 查火车票 / 查天气 / 查景点坐标 / 查驾车距离 / 行程该先定什么. Not for generating a full itinerary or shortlisting attractions.
---

# 国内旅行数据源

## 这个 skill 做什么

给 Agent 一套能直接调用的国内旅行数据接入说明：四个源、各自的端点与参数、认证方式、配额、已知的坑、返回字段。

提供两样东西：**数据源怎么接**，以及**行程该按什么顺序定、两种模式怎么选**。

## 这个 skill 不做什么

不给完整的攻略产出流程：候选池净化规则、游玩时长估算、空间分组、攻略文档结构都不在范围内。

**硬边界：数据层只回答「用哪个源、怎么调、结果长什么样、会踩什么坑」；规划层只到「先定什么、后定什么、选哪种模式」，再往下的具体判断交给使用者。**

这条线落在哪：给规划**顺序**、模式**公式**、以及已查到的事实数据；不给点名景点、不给到小时的日程、不替人挑餐厅。用户说「你自己定就行」也不放宽。

## 四个源

| 源 | 能回答什么 | 认证 | 参考 |
|---|---|---|---|
| 高德 Web 服务 | 地址↔坐标、POI 检索、驾车/步行/公交路线与距离、实时天气、地图瓦片 | `key` 参数 | `references/amap.md` |
| 飞常准 | 计划航班、航班号查询、中转方案、机票价格 | `X-VARIFLIGHT-KEY` 头 | `references/variflight.md` |
| 携程 SSR | 车次、时刻、历时、余票、票价 | 无 | `references/ctrip-train.md` |
| Open-Meteo | 天气预报、城市地理编码、历史天气、空气质量 | 无 | `references/open-meteo.md` |

另有两条：`references/planning-basis.md`（两种旅行模式、规划顺序、三条判断）、`references/variflight-key-provisioning.md`（额度耗尽后自助开通 Key）。

## 组合姿势

按**查询**组合，不按**行程**组合：

- 只知道地名，要坐标 → 高德 `geocode`（或 Open-Meteo 地理编码）
- 要景点这类 POI 的精确坐标 → 高德 `place/text`，不要用 `geocode`
- 要两点之间的车程 → 高德 `direction/driving`
- 只要航班时刻 → 飞常准 `flights`
- 要中转方案 → 飞常准 `transfer`，再用 `flights` 核实每段计划时间
- 要机票价格 → 飞常准 `getFlightPriceByCities`
- 要高铁票 → 携程车次列表（飞常准 `trainStanTicket` 可作备选）
- 要某地某几天的天气 → Open-Meteo：先 `geocoding-api` 拿坐标，再 `forecast`
- 要把坐标画成可交互地图 → 高德瓦片（不吃配额），配你自己的前端

## 运行前提

只要有 `curl` 或 `python3` 即可，不需要安装任何包。本文示例用 `curl`；Windows 下把 `curl` 换成 `curl.exe` 或用 `Invoke-RestMethod`。

## Key 与配额

- **高德**：在 https://console.amap.com 申请「Web 服务」类型 Key。POI 检索是唯一紧张的一项（快照约 100 次/天，详见 `references/amap.md`），其余能力宽松得多。
- **飞常准**：在 https://ai.variflight.com 注册，Key 在 `/keys` 页。新账号有体验额度，用完即止。
- **携程 / Open-Meteo**：无需 Key。

> 具体配额、体验额度、预报窗口都是平台政策，会变。本文提到的数字是 2026-10 的快照，**以官方控制台与文档为准**。

Key 从环境变量读，不要写进代码、对话或共享文档。额度耗尽时如实告知使用者，不要用共享/借用账号绕过。

## 五条通用纪律

1. **先查坐标，再查别的**。不要使用模型记忆里的经纬度，也不要猜城市中心点。
2. **三个源三种地名习惯**：携程用中文城市名（`上海`）、飞常准用三字码（`SHA`/`BJS`）、Open-Meteo 用英文或拼音（`Nanjing`）。传错不一定报错，可能只是查不到。
3. **坐标系不要混**：高德返回 GCJ-02；Open-Meteo 与 OSM 是 WGS-84。两者差 100–700 米，叠在同一张地图上会偏。
4. **失败先读错误码**。四个源都有「HTTP 200 + 业务错误」的情况，见各参考文件的错误分层。
5. **别信返回顺序**。航班列表不按时刻排、POI 按热度排、车次按发车排。凡是要「最早 / 最便宜 / 最近」，自己排序再回答。

## 不做的事

- 不抓大众点评 / 小红书 / 微信：没有面向个人开发者的公开 API，风控严格，也没有稳定的批量路径。
- 不共享 Key、不绕过验证码、不转卖账号。额度轮换见 `references/variflight-key-provisioning.md`，仅限自建测试账号。
- 不替代使用者做行程判断：数据可以给全、顺序可以给对，结论由人下。

## 参考文件

- `references/amap.md` — 高德：端点、参数、配额、POI 排序陷阱、瓦片
- `references/variflight.md` — 飞常准：端点、三字码规则、错误分层
- `references/ctrip-train.md` — 携程：车次列表 URL、`__NEXT_DATA__` 解析、字段表
- `references/open-meteo.md` — Open-Meteo：地理编码、预报变量、预报窗口
- `references/planning-basis.md` — 规划地基：两模式公式、规划顺序、三条判断
- `references/variflight-key-provisioning.md` — 飞常准 Key 自助开通：接口直连、激活、风控与降级
