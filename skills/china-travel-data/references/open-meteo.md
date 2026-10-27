# Open-Meteo

完全匿名、无需 Key、无配额限制（官方未给定值，实践中 QPS ≤ 10 足够稳）。文档：https://open-meteo.com/en/docs

| API | 用途 |
|---|---|
| `api.open-meteo.com/v1/forecast` | 未来约 16 天逐日 / 逐时天气（窗口长度以官方文档为准） |
| `geocoding-api.open-meteo.com/v1/search` | 城市名 → 经纬度 |
| `archive-api.open-meteo.com/v1/archive` | 1940 年至今的历史天气 |
| `air-quality-api.open-meteo.com/v1/air-quality` | PM2.5、臭氧等空气质量 |

## 地理编码

```
GET https://geocoding-api.open-meteo.com/v1/search?name={CITY}&count=1&language=zh&format=json
```

- `name`：**优先英文或拼音**（`Nanjing` 而非 `南京`），中文名有时直接查不到
- `count`、`language`（`zh`/`en`）、`countryCode`（如 `CN`，用于收窄同名地点）
- 返回 `results[]`：`name`、`country`、`admin1`、`latitude`、`longitude`、`timezone`、`population`

## 天气预报

```
GET https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily={VARS}&timezone=Asia/Shanghai&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

常用 `daily` 变量：

| 变量 | 含义 |
|---|---|
| `temperature_2m_max` / `temperature_2m_min` | 最高 / 最低气温（℃） |
| `precipitation_probability_max` | 降水概率（%） |
| `precipitation_sum` | 降水量（mm） |
| `windspeed_10m_max` | 最大风速（km/h） |

需要逐小时时加 `hourly=temperature_2m,precipitation_probability,precipitation`。

返回结构是**列式**的：`daily.time[]` 与各变量数组按下标对齐，组装时注意不要错位。

## 已知的坑

1. **地名歧义**。同名地点跨省跨国很常见（`南京` 在江苏和云南都有，`Paris` 在法国和肯塔基都有），返回顺序不稳定。做法：加 `countryCode=CN`，或用英文/拼音，或先 `geocode` 确认再传 `--lat/--lon` 等价坐标。
2. **预报窗口约 16 天**（以官方文档为准）。超出范围会报 `Parameter 'start_date' is out of allowed range`；不要当成「没有天气数据」。
3. **过去日期要走 archive API**，`forecast` 不返回历史。
4. **坐标系是 WGS-84**。与高德的 GCJ-02 混用做地图叠加会偏 100–700 米；只查天气不受影响（气象数据是网格化的）。
5. **时区要显式传**。默认按坐标推断；跨时区比对时传 `timezone=Asia/Shanghai` 保持一致。

## 最小可用请求

```bash
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Nanjing&count=1&language=zh&format=json"
curl -s "https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Shanghai&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}"
```
