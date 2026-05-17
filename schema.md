# 书单地图 — JSON Schema (v1.0)

本文件定义 Agent 输出的 JSON 格式契约。项目网页侧 `werearchAgentParser` 严格按本 schema 解析。

## 1. 顶层结构

```json
{
  "$schema": "weread-export/v1",
  "version": "1.0",
  "source": "weread",
  "exportedAt": "2026-05-17T02:36:00+08:00",
  "books": [ /* BookEntry[] */ ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `$schema` | string | 否 | 固定 `"weread-export/v1"`,便于未来版本识别 |
| `version` | string | 是 | 当前固定 `"1.0"` |
| `source` | string | 是 | 固定 `"weread"`,项目据此打 `platform: 'weread'` 标签 |
| `exportedAt` | string (ISO 8601) | 是 | Agent 生成此文件的时间 |
| `books` | BookEntry[] | 是 | 书籍列表 |

## 2. BookEntry 结构

```json
{
  "weread_bookId": "858742",
  "title": "作为意志和表象的世界",
  "author": "叔本华",
  "nationalityCode": "DE",
  "cover": "https://cdn.weread.qq.com/weread/cover/42/YueWen_858742/t6_YueWen_858742.jpg",
  "weread_category": "哲学宗教-哲学著作",
  "category": "哲学",
  "readDate": "2026-01-12T20:04:51+08:00",
  "finishReading": false,
  "secret": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `weread_bookId` | string | 否 | 留存,便于反查或拼接 `weread://reading?bId=...` 跳转链接 |
| `title` | string | **是** | 落到 `Book.title` |
| `author` | string | **是** | **保留原文**(含 `[美]` 前缀),项目侧能识别 |
| `nationalityCode` | string (ISO 3166-1 alpha-2) | **强烈推荐** | 首作者的国籍 ISO 代码;提供后项目跳过 Wikidata 查询 |
| `cover` | string (URL) | 推荐 | 微信读书 CDN URL(外链稳定),项目直接当 `Book.cover` 存 URL |
| `weread_category` | string | 否 | 保留原始 `"大类-小类"`,可缺省 |
| `category` | string | 推荐 | 项目 `BookCategory` 之一,见 §3;缺省则项目兜底用 `inferCategory(title)` |
| `readDate` | string (ISO 8601) | 推荐 | 缺省则项目用当前时间 |
| `finishReading` | boolean | 否 | 项目首版**暂未使用**,但仍建议保留以便未来扩展 |
| `secret` | boolean | 否 | 同上 |

## 3. 项目 BookCategory 枚举

```
小说 | 科幻 | 悬疑 | 恐怖 | 推理 | 奇幻 | 文学 | 散文 | 戏剧 | 诗歌
传记 | 历史 | 哲学 | 社科 | 经济 | 管理 | 心理 | 科技 | 艺术 | 生活
绘本 | 漫画 | 其他
```

详细映射规则见 `category-mapping.md`。

## 4. 完整示例

```json
{
  "$schema": "weread-export/v1",
  "version": "1.0",
  "source": "weread",
  "exportedAt": "2026-05-17T02:36:00+08:00",
  "books": [
    {
      "weread_bookId": "858742",
      "title": "作为意志和表象的世界",
      "author": "叔本华",
      "nationalityCode": "DE",
      "cover": "https://cdn.weread.qq.com/weread/cover/42/YueWen_858742/t6_YueWen_858742.jpg",
      "weread_category": "哲学宗教-哲学著作",
      "category": "哲学",
      "readDate": "2026-01-12T20:04:51+08:00",
      "finishReading": false,
      "secret": false
    },
    {
      "weread_bookId": "26859515",
      "title": "沙丘六部曲(电影《沙丘2》原著小说)",
      "author": "[美]弗兰克·赫伯特",
      "nationalityCode": "US",
      "cover": "https://cdn.weread.qq.com/weread/cover/61/yuewen_26859515/t6_yuewen_268595151708661295.jpg",
      "weread_category": "精品小说-科幻小说",
      "category": "科幻",
      "readDate": "2025-11-20T08:00:00+08:00",
      "finishReading": true,
      "secret": false
    }
  ]
}
```

## 5. 软降级规则

项目侧 `werearchAgentParser` 对缺失字段做以下处理:

| 缺失字段 | 项目侧行为 |
|---------|-----------|
| `nationalityCode` | 走原有 `queryAuthorInfo` 链路(前缀解析 → cache → static → Wikidata → UNKNOWN) |
| `nationalityCode` 不在国家库 | 标 UNKNOWN(地图上"待补充") |
| `category` | 走 `inferCategory(title, weread_category)` 兜底 |
| `readDate` | 用当前时间 |
| `cover` | 走 `getBookCover()` 自动查 |

任一书条目校验失败不会中断整体导入,错误会列在导入结果的 `errors[]` 里。

## 6. 重复导入

项目侧靠 `uniqueKey = "title::authorName"`(小写去空格)做唯一索引。
Agent 每次可以全量导出,重复的书自动跳过(返回时计入 `skipped` 而非 `failed`)。
