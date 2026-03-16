---
id: "rb-jimeng-video-v1"
name: "Jimeng Video Downloader"
version: "4.0"
owner: "trae_user"
platform: "desktop"
locale: "zh-CN"
description: "访问即梦AI视频生成页面，加载并提取最新5条视频的下载链接"
outputs:
  video_urls: "视频链接列表"
---

## 访问主页
**ID**: 1001
**Description**: 打开即梦AI视频生成页面并等待加载。
**URL**: `https://jimeng.jianying.com/ai-tool/generate/?type=video&workspace=0`

**Steps**:
1. `GOTO "https://jimeng.jianying.com/ai-tool/generate/?type=video&workspace=0"`
2. `WAIT "networkidle"`
3. `WAIT "video"`

---

## 加载视频
**ID**: 1002
**Description**: 滚动页面以触发视频懒加载，确保至少加载5条视频。
**URL**: `type=video`

**Steps**:
1. `SCROLL "bottom"`
2. `WAIT 2000`
3. `SCROLL "bottom"`
4. `WAIT 2000`

---

## 提取链接
**ID**: 1003
**Description**: 提取页面中前5个视频的源地址。

**Steps**:
1. `EXTRACT "src" FROM "video" LIMIT 5`
