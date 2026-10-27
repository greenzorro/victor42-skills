# 飞常准 Key 自助开通（接口直连）

免费额度是消耗型的。额度用尽又不想付费时，可以用接口直连自助开通新账号——比在网页上点流程快，也便于自动化。

**前提**：你需要一个自己能收信的邮箱域名，且它支持通配前缀转发（Cloudflare Email Routing 这类即可）。下面的 `{your-domain}`、`{word1}`、`{word2}` 都自己替换。

**适用范围**：自建测试账号、额度轮换。不要用它做账号共享或转卖；平台条款自行评估，触发风控时停下来找人工。

## 1. 邮箱格式

```
{service}-{word1}-{word2}@{your-domain}
```

`{word1}` `{word2}` 取两个随机英文词，不关联服务、不记录序号——避免形成可被识别的命名规律。

## 2. 提交注册（接口直连，无浏览器）

```
POST https://ai.variflight.com/api/v1/platform/auth/register
Content-Type: application/json

{"username": "vik_xxx_2026", "email": "vik-variflight-xxx-yyy@your-domain",
 "password": "<自定强密码>", "phone": "", "company_name": ""}
```

`phone` 与 `company_name` 可以留空。

## 3. 取激活码

注册后邮箱会收到激活链接，链接里带 `code=xxxxxxxx`。

- **有 GUI**：本地模式下用 `chrome-devtools` 这类 MCP 连上浏览器读收件箱，自动提取 `code`。
- **无 GUI**（无头云节点）：不必卡住——把邮箱收到的链接或 `code` 人工复制给 Agent，继续后面两步。这一步不是阻断点。

## 4. 激活账号

```
GET https://ai.variflight.com/api/v1/platform/auth/activate?email={email}&code={code}
```

## 5. 登录取 JWT

```
POST https://ai.variflight.com/api/v1/platform/auth/login
Content-Type: application/x-www-form-urlencoded

username={username}&password={password}
```

返回体里取 `access_token`。

## 6. 创建 API Key

```
POST https://ai.variflight.com/api/v1/platform/api-keys/
Authorization: Bearer {access_token}
Content-Type: application/json

{"key_name": "my-key"}
```

返回 46 位 Key，形如 `sk-...`。存进你自己的密钥管理，不要写进代码或文档。

## 风险与降级

这套流程来自对前端包的分析，**属于非公开接口，随时可能变**：

| 风险 | 表现 | 应对 |
|---|---|---|
| 人机验证 | 直连 POST 返回 403 / 422 | 改用网页端注册，不硬试 |
| 域名风控 | 同一邮箱后缀被防刷拦截 | 换邮箱域名或等待，别密集重试 |
| 契约变更 | 路由改名、要动态签名头 | 以网页端流程为准重新对齐 |

**通用降级：接口失败就转浏览器注册**，保持流程不中断；连续失败两次以上就停下来交回给人，别把风控刷成硬封。
