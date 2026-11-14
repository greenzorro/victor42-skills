# 同程程心（Tongcheng Chengxin）

同程旅行的资源网关。国内源里唯一能拿到**结构化长途客运班次**的接口，同时补上景区门票与开放时间。

## 定位

补充源，不是主力：

- **长途客运**：唯一不可替代项（`/busResource`）
- **景区门票 / 开放时间 / 建议游玩时长**：辅助（`/sceneryResource`）
- **低价目的地探索**：开放式发现（`/flightResource` + `lowPrice`）；权威全量时刻与机型仍用飞常准
- **火车票**：兜底；余票与预售期以携程 SSR 为主
- **酒店**：只到酒店级起步价、设施、口碑与地标距离；分房型比价不在这里

## 网关与调用

```
POST https://wx.17u.cn/skills/gateway/api/v1/gateway/<endpoint>
```

必需请求头：

```
Authorization: Bearer {your_api_key}
Origin: https://www.ly.com
Referer: https://www.ly.com/
Content-Type: application/json
```

请求体必须带 `"version": "1.0.0"`，与业务参数同级。

## 认证：激活码

- 形态：`tc-` 前缀、46 字符的静态码，不是 JWT
- 获取：同程旅行 App，或微信小程序（微信 → 我 → 服务 → 火车票机票 / 酒店民宿），顶部搜索「程心激活码」
- 配额与有效期由服务端托管：HTTP 响应头不返回 `X-RateLimit-*` / `X-Quota-*`，网关也没有余额或到期查询接口
- 失效表现：激活码过期、额度耗尽或未授权时，业务层返回 `code: 3`；此时按上面的路径重新申领
- 不带 `Authorization` 头时回落到匿名试用额度
- 另有官方 OAuth CLI（`@tongcheng/tc-chengxin-cli`，经 `/api/v1/oauth/cli/*` 签发短期 `access_token`），直连 JSON 接口不需要它

Key 从环境变量读（如 `CHENGXIN_API_KEY`），不要写进代码、对话或共享文档。

## 端点

| 端点 | 功能 | 核心参数 |
|---|---|---|
| `/busResource` | 长途汽车 / 客运班次、时刻、历时、票价、余票 | `departure`、`destination`（或 `departureStation`、`arrivalStation`）、`extra` |
| `/sceneryResource` | 景区详情、门票价、开放时间、建议游玩时长、经纬度、票务明细 | `destination`、`extra` |
| `/flightResource` | 航班、中转、特价；只传 `departure` + `lowPrice: true` 可发现低价目的地 | `departure`、`destination`、`flightNumber`、`lowPrice`（bool）、`extra`、`query` |
| `/hotelResource` | 酒店检索、参考起步价、设施、口碑标签、地标距离 | `destination`、`query`（含地标 / 预算 / 日期的完整自然语言）、`extra` |
| `/trainResource` | 车次、历时、参考价、席别余票 | `departure`、`destination`（或站名、车次） |
| `/trafficResource` | 未指定交通方式时综合返回火车 / 机票 / 汽车 / 市内接驳 | `departure`、`destination`、`extra` |

**禁调 `/travelResource`**：一键生成完整行程的打包接口。它会把行程判断替你做完，越过使用者该自己下的那些步骤。

## 响应结构

双层信封：

```json
{"code": 0, "message": "success", "data": {"code": "0", "data": { ... }}}
```

- 外层 `code` 与内层 `data.code` 都是状态位；业务数据在 `data.data`
- `0` / `"0"` 成功，`1` / `"1"` 无匹配结果，`3` 鉴权 / 配置 / 额度异常
- 外层成功不等于内层成功，两层都要判

## 关键字段

- **客运** `busDataList[].busList[]`：`coachNo`、`depCityName` / `arrCityName`、`depStationName` / `arrStationName`、`depDateTime`、`depTime`、`arrTime`、`runTimeMinutes`、`coachType`、`price`、`leftTicketNum`
- **景区** `sceneryDataList[].sceneryList[]`（及 `needExtend`）：`resourceId`、`name`、`cityName`、`star`、`score`、`commentNum`、`price`、`isFree`、`openTime`、`playTime`、`bestPlayTime`、`describe`、`rankTitle`、`address`、`lat`、`lon`、`facilityList`、`trafficList`、`ticketEntityList`
- **航班** `flightDataList[].flightList[]`：常规航线按「最便宜 3 条」「最短耗时 3 条」「综合推荐最多 40 条」分组，无分页。可用字段：`flightNo`、`airlineName`、`depAirportName` / `depAirportTerminal`、`arrAirportName` / `arrAirportTerminal`、`depDate`、`depTime`、`arrDate`、`arrTime`、`runTime`、`price`（单一最低起步参考价）、`tripType`、`directFlag`、`segmentList`（联程）。**恒为 `null`**：`aircraft`、`productList`（多舱位报价）、`discount`、`airportTax`、`adultSurcharge`、`isCodeShareFlight`、`flightRealtimeType`
- **低价模式**（`lowPrice: true` 且不传 `destination`）：`flightNo` 为 `null`，返回 `arrName`、`depDate`、`week`、`price`、`originPrice`、`discount`
- **酒店** `hotelDataList[].hotelList[]`（单次最多 20 家，无分页）：`resourceId`、`name`、`image`、`price`（当晚起步参考价）、`dailyPrices[]`、`star`、`starLevel`、`score`、`commentNum`、`distance`、`describe`、`recommendReasons`、`cityName`、`countyName`、`bdName`、`address`、`lat`、`lon`、`phoneNumber`、`openYear`、`decorYear`、`facilities`、`hotelExtra`、`roomType`（仅房型名称 JSON 字符串）、`commentTag[]`、`sceneCommentPhrase[]`
- **火车** `trainDataList[].trainList[]`：`trainNo`、`trainType`、`depStationName` / `arrStationName`、`depDate`、`depTime`、`arrDate`、`arrTime`、`runTime`、`price`、`ticketList`、`limiter`

## 坑

- **酒店地标筛选必须写进 `query`**：只传 `destination` + `extra`（如 `"外滩附近"`）时位置词会被忽略（`pageDataList[].keyword` 为空），直接返回机场周边默认推荐。把完整自然语言写进 `query`，如 `"上海外滩附近的酒店，2026-11-20入住，2026-11-21离店"`
- **`extra` 是自然语言约束**：可传 `"明天"`、`"最早 直飞"`、`"适合亲子 免费"`
- **城市名直接传中文**：`"上海"`、`"苏州"`，不需要三字码或电报码
- **景区开放时间不等于当日实时开放状态**：`openTime` 是常规营业信息，节假日临时闭园、限流预约要另向官方渠道确认
- **航班无分页、无多舱位**：单次最多 40 条综合推荐，要「最早 / 最便宜」自己排序；需要机型、经停、退改与行李规则时换飞常准
- **坐标精度**：景区经纬度可用于预览，但空间聚类与驾车距离仍以高德为准（两源坐标精度与坐标系不同）

## 示例

```python
import json, os, urllib.request

API_KEY = os.environ["CHENGXIN_API_KEY"]
BASE = "https://wx.17u.cn/skills/gateway/api/v1/gateway"

def query_tongcheng(endpoint: str, params: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{endpoint.lstrip('/')}",
        data=json.dumps({**params, "version": "1.0.0"}, ensure_ascii=False).encode(),
        headers={
            "Content-Type": "application/json",
            "Origin": "https://www.ly.com",
            "Referer": "https://www.ly.com/",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        outer = json.loads(resp.read().decode())
    inner = outer.get("data") or {}
    if inner.get("code") in (0, "0"):
        return inner.get("data") or {}
    raise RuntimeError(f"tongcheng error: {inner.get('code')} / {inner.get('message')}")
```

```bash
curl -s -X POST "https://wx.17u.cn/skills/gateway/api/v1/gateway/busResource" \
  -H "Authorization: Bearer $CHENGXIN_API_KEY" \
  -H "Origin: https://www.ly.com" -H "Referer: https://www.ly.com/" \
  -H "Content-Type: application/json" \
  -d '{"departure":"昆明","destination":"大理","version":"1.0.0"}'
```
