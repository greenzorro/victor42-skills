# 携程火车票（PC 端 SSR）

无需 Key、无反爬签名。数据来自页面内嵌的 `__NEXT_DATA__`。

## 车次列表

```
GET https://trains.ctrip.com/webapp/train/list?ticketType=0&dStation={出发城市}&aStation={到达城市}&dDate={YYYY-MM-DD}&rDate=&trainsType=&hubCityName=&highSpeedOnly=0
```

| 参数 | 说明 | 示例 |
|---|---|---|
| `ticketType` | 票种：0 单程 / 1 往返 / 2 中转 | `0` |
| `dStation` | 出发城市（中文，URL 编码） | `上海` |
| `aStation` | 到达城市（中文，URL 编码） | `北京` |
| `dDate` | 出发日期 | `{YYYY-MM-DD}` |
| `rDate` | 返程日期（往返时用） | |
| `trainsType` | 车型：空=全部，`G`=高铁 | |
| `hubCityName` | 中转城市 | |
| `highSpeedOnly` | 只看高铁动车：0 否 / 1 是 | `0` |

站名用**中文城市名**，不是电报码。

## 解析

```python
import urllib.request, urllib.parse, re, json

def query_trains(departure, arrival, date):
    params = urllib.parse.urlencode({
        "ticketType": "0", "dStation": departure, "aStation": arrival,
        "dDate": date, "rDate": "", "trainsType": "",
        "hubCityName": "", "highSpeedOnly": "0",
    })
    url = f"https://trains.ctrip.com/webapp/train/list?{params}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        html = resp.read().decode("utf-8")
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return None                       # 页面结构变了
    data = json.loads(match.group(1))
    return data["props"]["pageProps"]["initialState"]["trainSearchInfo"]["trainInfoList"]
```

取不到 `__NEXT_DATA__` 就当作「已改版」处理，不要返回空列表——两者含义完全不同。

## 车次字段

| 字段 | 说明 |
|------|------|
| `trainNumber` | 车次号，如 G2 |
| `departureStationName` / `arrivalStationName` | 出发/到达站名，如 上海虹桥、北京南 |
| `departureTime` / `arrivalTime` | 出发/到达时刻，如 06:43、11:32 |
| `duration` | 历时文本，如 4时49分 |
| `runTime` | 运行分钟数，如 289 |
| `isStartStation` / `isEndStation` | 是否始发 / 终到 |
| `isBookable` / `isSaleStop` | 是否可预订 / 是否停售 |
| `isFuXingTrain` | 是否复兴号 |
| `startPrice` | 最低票价（**元**） |
| `preSaleDay` / `preSaleTime` | 预售天数 / 放票时刻 |
| `seatItemInfoList` | 座位信息数组 |

## 座位字段（`seatItemInfoList[]`）

| 字段 | 说明 |
|------|------|
| `seatName` | 二等座 / 一等座 / 商务座 / 无座 / 软卧 等 |
| `seatPrice` | 票价（**元**） |
| `seatBookable` | 是否可购买 |
| `seatInventory` | 余票数量（仅可购时有效） |
| `discountRate` | 折扣率，0.91 = 9.1 折 |
| `forecastSeatPriceList` | 学生票 / 儿童票预估价 |

**单位统一是元。** 不要按「分」换算。

## 已知的坑

1. **超出预售期返回空列表**，不是错误。空列表要解读为「还没放票」，而不是「没有车」。
2. **依赖 `__NEXT_DATA__` 结构**，携程改版就失效。先用一个已知有车的日期自检，再判断是没票还是解析坏了。
3. **站名要中文城市名**。写「上海」而不是「SHH」。
4. **只读查询**，不涉及登录、不下单；不要带登录态 Cookie 去做批量抓取。

## 补充：站名与电报码映射

```
GET https://kyfw.12306.cn/otn/resources/js/framework/station_name.js
```

无反爬保护，可直连获取全国三千多个站点的站名↔电报码对照表。需要精确到具体车站（虹桥 vs 上海站）时用得上。
