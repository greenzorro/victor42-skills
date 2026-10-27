# 高德 Web 服务 API

- 入口：`https://restapi.amap.com/v3/{服务路径}`
- 认证：URL 参数 `key=xxx`（在 https://console.amap.com 申请「Web 服务」类型 Key）
- 坐标系：**GCJ-02**，经纬度一律写作 `经度,纬度`（先经度后纬度）
- 成功判定：`status=1`；失败 `status=0`，读 `info` 与 `infocode`

## 能力与配额（个人开发者）

> 下列数字是 2026-10 的快照，平台会调整，**以控制台 https://console.amap.com 的实际额度为准**。

| 能力 | 典型配额 |
|---|---|
| 地理编码 / 逆地理编码 | 5000 次/天 |
| POI 检索（关键字 / 周边） | **100 次/天** |
| 路径规划（驾车/步行/公交） | 5000 次/天 |
| 天气查询 | 5000 次/天 |
| 地图瓦片 | 不消耗配额 |

每日 0:00 重置，超限按阶梯计费。以上配额与计费规则同属快照，以控制台为准。

## 端点

### 地理编码：地址 → 坐标

```
GET /v3/geocode/geo?address={地址}&city={城市}&key={key}
```

返回 `geocodes[]`，关键字段：`formatted_address`、`province`、`city`、`district`、`adcode`、`location`（`经度,纬度`）、`level`。

**`level` 就是精度自述**：`省` / `市` / `区县` / `开发区` / `乡镇` / `村庄` / `兴趣点` / `门牌号`。要 POI 级坐标时先看这个字段，不要假设它准确。

### 逆地理编码：坐标 → 地址

```
GET /v3/geocode/regeo?location={经度,纬度}&extensions=base&key={key}
```

返回 `regeocode.formatted_address`，行政区划在 `regeocode.addressComponent`（`province` / `city` / `district` / `township` / `adcode`）。

### POI 关键字检索

```
GET /v3/place/text?keywords={关键词}&city={城市}&citylimit=true&offset={条数}&page=1&key={key}
```

返回 `count`（总数）与 `pois[]`：`name`、`type`、`address`、`location`、`adcode`、`cityname`、`adname`、`tel`。

### POI 周边检索

```
GET /v3/place/around?location={经度,纬度}&radius={米}&keywords={关键词}&types={类型码}&offset={条数}&key={key}
```

结果比 `place/text` 多一个 `distance`（米）。

### 路径规划

```
GET /v3/direction/driving?origin={经度,纬度}&destination={经度,纬度}&extensions=base&key={key}
GET /v3/direction/walking?origin=...&destination=...&key={key}
GET /v3/direction/transit/integrated?city={城市}&origin=...&destination=...&key={key}
```

- 驾车 / 步行：`route.paths[0].distance`（米）、`route.paths[0].duration`（秒）
- 公交地铁：`route.transits[0]`，含 `distance`、`duration`、换乘段
- 骑行是 v4 接口，路径不同：`https://restapi.amap.com/v4/direction/bicycling`，返回 `data.paths[]`

### 天气

```
GET /v3/weather/weatherInfo?city={城市名或 adcode}&extensions=base|all&key={key}
```

- `base`：`lives[]`，实时天气（`weather`、`temperature`、`winddirection`、`windpower`、`humidity`、`reporttime`）
- `all`：`forecasts[].casts[]`，未来 3–4 天（`dayweather`、`nightweather`、`daytemp`、`nighttemp`）

## 地图瓦片

```
https://wprd0{s}.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=8
```

- `subdomains`：`1234`（取模轮询）
- `style=8` 标准地图（`6` 卫星影像、`7` 路网注记）
- HTTPS + 允许跨域，可直接作为 Leaflet / MapLibre / OpenLayers 的 XYZ 图层
- 不带 Key、不消耗配额
- 非官方直连方式，高德可能调整；正式商用请用官方地图 JS SDK

## 已知的坑

1. **地理编码不给你 POI 坐标**。`中山陵` 用 `geocode` 只会得到城市或门牌级结果；景点坐标走 `place/text`。
2. **`address` 配 `city` 传短地名会报 30001**。如 `address=中山陵&city=南京` → `ENGINE_RESPONSE_DATA_ERROR`；把城市写进地址（`南京市中山陵`）或直接改用 POI 检索。
3. **地址首字会被当成独立地名**。`南京中山陵` 可能匹配到广东中山（adcode 442000），务必核对返回的 `adcode` 与 `city`。
4. **POI 按热度排序，不按相关性**。同名 POI 里搜索量高的会顶到前面，连锁店尤其明显；用 `city`、`citylimit`、`types` 一起收窄。
5. **`types` 不只是过滤，还会改变排序逻辑**。加上它之后结果顺序会和纯关键字检索不同。
6. **`city` 接受县级行政区名**，直接写区县名即可。
7. **`citylimit` 与 `keywords` 是两个独立维度**。往关键词里塞地理词（`南京中山陵`）会破坏模糊匹配，正确做法是关键词只放 POI 名。
8. **POI 注册名可能与常用名不同**。使用者说的名字与高德库里的名称经常不一致，检索不到时换官方名或拆分关键词再试。

## 最小可用请求

```bash
# POI 坐标 + 到某点的车程
curl -s "https://restapi.amap.com/v3/place/text?keywords=中山陵&city=南京&citylimit=true&offset=5&key=$AMAP_KEY"
curl -s "https://restapi.amap.com/v3/direction/driving?origin=118.79,32.06&destination=118.85,32.05&key=$AMAP_KEY"
```
