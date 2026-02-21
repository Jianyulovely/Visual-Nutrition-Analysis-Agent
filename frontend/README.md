# 前端代码说明文档 - Vision Analysis Agent

## 项目概述

这是一个基于**微信小程序**开发的饮食营养分析前端应用。用户可以上传美食图片，系统通过后端AI视觉分析模型识别菜品成分，并返回详细的营养分析结果。

## 技术栈

| 项目 | 说明 |
|------|------|
| 框架 | 微信小程序原生框架 |
| UI | 微信小程序原生组件 + WXSS样式 |
| 图表 | Canvas 2D API (饼图绘制) |
| 网络 | wx.request / wx.uploadFile |

## 项目目录结构

```
frontend/miniprogram/
├── app.js                    # 小程序入口文件
├── app.json                  # 小程序全局配置
├── app.wxss                  # 全局样式
├── sitemap.json              # 站点地图配置
├── project.config.json       # 项目配置
├── utils/
│   └── api.js                # API请求封装
├── pages/
│   ├── index/                # 首页
│   │   ├── index.js
│   │   ├── index.wxml
│   │   ├── index.wxss
│   │   └── index.json
│   └── analyze/              # 分析页面
│       ├── analyze.js
│       ├── analyze.wxml
│       ├── analyze.wxss
│       └── analyze.json
└── images/                   # 图标资源
    ├── home.svg / home.png
    ├── analyze.svg / analyze.png
    └── ...
```
