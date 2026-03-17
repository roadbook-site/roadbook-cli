---
id: "jimeng-ai-video-crawl"
name: "jimeng-ai-video-crawl"
version: "4.0"
owner: "user"
platform: "desktop"
locale: "zh-CN"
region: "CN"
description: "爬取即梦AI网站的最近5条已生成视频"
inputs: {}
outputs: {
  "videos": "最近5条已生成的视频列表"
}
---

## 连接浏览器
**ID**: a1b2
**Description**: 通过CDP连接到端口9224上的浏览器，确认连接成功
**Locators**: `text="即梦AI"`

**Steps**:
1. `WAIT 2000`

---

## 页面加载与滚动
**ID**: 3c4d
**Description**: 等待页面完全加载，滚动页面以加载更多视频内容
**URL**: `https://jimeng.jianying.com/ai-tool/generate/`
**Locators**: `div[class*='video']`, `div:has-text('总时长')`

**Steps**:
1. `WAIT 2000`
2. `SCROLL 1000`
3. `WAIT 2000`

---

## 提取视频信息
**ID**: 5e6f
**Description**: 提取最近5条已生成的视频信息，包括标题、URL和缩略图
**URL**: `https://jimeng.jianying.com/ai-tool/generate/`
**Locators**: `div:has-text('总时长')`

**Steps**:
1. `WAIT "div:has-text('总时长')"`
2. `EXTRACT "text" FROM "div:has-text('总时长')"`

**Assertions (断言)**:
- [ ] 成功提取至少5条视频信息
- [ ] 每条视频包含标题信息
- [ ] 视频标题不为空

---

## 输出结果 (Outputs)
- **videos**: 包含5条视频信息的列表，每条视频包含id、title、url和thumbnail字段
