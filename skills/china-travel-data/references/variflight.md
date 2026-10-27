# 飞常准（Variflight）

覆盖：国内航班 100%，全球 94–97%（厂商口径，时点快照，以官网为准）。

- 入口：`POST https://mcp.variflight.com/api/v1/mcp/data`
- 认证：HTTP Header `X-VARIFLIGHT-KEY`
- Key：在 https://ai.variflight.com 注册后从 `/keys` 页面获取；新账号有体验额度，用完即止
- 请求体：`{"endpoint": "<端点名>", "params": {...}}`

```bash
curl -s -X POST "https://mcp.variflight.com/api/v1/mcp/data" \
  -H "Content-Type: application/json" \
  -H "X-VARIFLIGHT-KEY: $VARIFLIGHT_KEY" \
  -d '{"endpoint":"flights","params":{"dep":"SHA","arr":"PEK","date":"{YYYY-MM-DD}"}}'
```

## 三字码规则（最容易踩错的地方）

| 端点 | 用什么码 | 示例 |
|---|---|---|
| `flights` | **机场**三字码 | `dep=SHA`（虹桥）、`arr=PEK`（首都） |
| `flight` | 航班号 | `fnum=CA1518` |
| `transfer` | **城市**三字码 | `depcity=SHA`、`arrcity=BJS` |
| `getFlightPriceByCities` | **城市**三字码 | `dep_city=SHA`、`arr_city=BJS` |
| `trainStanTicket` | 中文城市名 | `cdep=上海`、`carr=北京` |

同一城市有多个机场时，`flights` 要逐个机场查；`transfer` / 价格接口按城市聚合。

## 端点

| 端点 | 功能 | 参数 | 备注 |
|---|---|---|---|
| `flights` | 按航线查计划航班 | `dep, arr, date` | 时刻权威，用机场码 |
| `flight` | 按航班号查 | `fnum, date` | 单航班详情 |
| `transfer` | 中转方案 | `depcity, arrcity, depdate` | 时间是**含历史延误的预估**，非计划时间 |
| `happiness` | 舒适度指数 | `fnum, date` | |
| `futureAirportWeather` | 机场天气 | `code, type` | |
| `getFlightPriceByCities` | 机票价格 | `dep_city, arr_city, dep_date` | 返回各舱位价格与余位 |
| `trainStanTicket` | 火车票 | `cdep, carr, date` | 携程车次的备选通道 |

## 返回字段

`flights` 每项主要字段：

```
FlightNo              航班号
FlightCompany         航空公司全称
FlightDepcode/Arrcode 起降机场三字码
FlightDep/Arr         起降城市名
FlightDepAirport      机场名
FlightHTerminal       出发航站楼
FlightTerminal        到达航站楼
FlightDeptimePlanDate 计划起飞（YYYY-MM-DD HH:MM:SS）
FlightArrtimePlanDate 计划到达
FlightState           状态（计划 / 起飞 / 到达 / 取消 …）
StopFlag              是否经停
```

`getFlightPriceByCities` 每项含 `cabins[]`：`classname`（经济舱/公务舱…）、`cabincode`、`seatnum`（余位）、`price`（当前价）、`stprice`（标准价）、`discount`（折扣率，0.65 = 6.5 折）。

`transfer` 返回的是**方案数组的数组**：外层是方案，内层是每段航班。

**返回结构并不统一**：多数端点的 `data` 是数组，但 `trainStanTicket` 多包一层（`data.data[]`，附带 `code` / `msg`），`futureAirportWeather` 是对象（`data.current`）。按端点分别处理，不要假设一律是数组。

## 错误分层

HTTP 永远是 200，错误藏在 body：

```json
{"code": 200, "message": "Success", "data": {"error": "暂无数据", "error_code": 10}}
```

| error_code | 含义 | 常见原因 |
|---|---|---|
| 10 | 暂无数据 | 该航线当天无航班 / 日期超范围 |
| 3 | 参数格式不正确 | 三字码类型用错（机场码 vs 城市码） |

判断成功不要看 HTTP 状态码，要看 `data` 是数组还是带 `error` 的对象。

## 两个会误导人的细节

1. **`flights` 结果不按时刻排序。** 首条可能是傍晚的航班（实测首条 17:30、第二条 19:30）。问「最早一班 / 末班」必须自己取 `FlightDeptimePlanDate` 排序，不要信返回顺序。
2. **401 的报错文案指向错误的头。** key 为空或缺失时返回 `401 API key is required. Send it in the X-API-Key header`，但实际只需要 `X-VARIFLIGHT-KEY` 有值。看到这条先检查 header 值是否为空（常见于环境变量没导出），不要照着文案去加 `X-API-Key`（加了会变成 422）。只有 `Invalid API key` 才是 Key 值本身不对。

## 使用注意

- `transfer` 的时间加了历史延误修正，会偏晚；**查到路线后要用 `flights` 或 `flight` 核实每段的计划时间**。
- 免费额度是消耗型的，注意剩余额度；不要为了对比反复拉同一天的全量数据。
- 只做查询，不做下单。
