# 小径·书单地图 AI Skill

让 AI Agent 帮你把微信读书书架画成世界地图——每本书按作者出生国钉在地球上,一眼看到你的阅读足迹。

配套网页:[https://book-map-visualization.vercel.app](https://book-map-visualization.vercel.app)

---

## 安装

```bash
git clone https://github.com/Trentct/xiaojing-map.git ~/.claude/skills/xiaojing-map
```

> Cursor 用户可换成 `~/.cursor/skills-cursor/xiaojing-map`,或 Codex 用户换 `~/.codex/skills/xiaojing-map`——目录由你的 Agent 工具决定。

## 依赖

本 skill 依赖[微信读书官方 skill `weread-skills`](https://cdn.weread.qq.com/skills/weread-skills.zip) 来调微信读书 API。先装它:

```bash
curl -fL https://cdn.weread.qq.com/skills/weread-skills.zip -o /tmp/weread-skills.zip \
  && unzip -o /tmp/weread-skills.zip -d ~/.claude/skills/
```

## 配置

在微信读书 App「我 → AI 助手」生成你的 API Key,然后:

```bash
export WEREAD_API_KEY=wrk-你的key
```

(建议写进 `~/.zshrc` / `~/.bashrc` 以便长期生效。)

## 使用

在 Cursor / Claude Code / Codex 里对 AI 说一句:

> 用 xiaojing-map 生成我的书单地图

AI 会自动完成:

1. 调 weread-skills 拉你的微信读书书架
2. 推断每位作者的国籍 + 映射分类
3. 生成压缩后的一键链接
4. 自动打开浏览器,地图自动渲染

---

## 文件说明

| 文件 | 作用 |
|------|------|
| [SKILL.md](./SKILL.md) | Agent 入口,声明工作流与依赖 |
| [schema.md](./schema.md) | 与书单地图网页对接的 JSON 契约 |
| [nationality-prompt.md](./nationality-prompt.md) | 推作者国籍的 prompt 模板 |
| [category-mapping.md](./category-mapping.md) | 微信读书分类 → 项目分类映射规则 |
| [scripts/make-url.py](./scripts/make-url.py) | 把 JSON 编码成一键链接的脚本 |

---

## 相关项目

- **书单地图网页**:[Trentct/book-map-visualization](https://github.com/Trentct/book-map-visualization) — 接收 skill 输出的网页端
- **weread-skills**:微信读书官方 Agent skill

## License

MIT
