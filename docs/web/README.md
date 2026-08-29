# OpenStarry Code 文档网站

这是 OpenStarry Code 的在线 API 文档，采用 Tenacity 视觉风格（白色毛玻璃 + 浅蓝到粉色渐变）。

## 访问方式

在浏览器中打开：
```
file:///d:/openstarry-code/docs/web/index.html
```

或者使用本地服务器：
```bash
cd d:\openstarry-code\docs\web
python -m http.server 8000
```
然后访问 `http://localhost:8000`

## 页面结构

- **index.html** - 快速开始、安装指南、基础配置
- **api.html** - Provider、Skills、Protocol、Gateway API 完整文档
- **plugins.html** - 插件系统架构、市场对比、六层优先级说明
- **plugin-dev.html** - 插件开发指南（Skill、Python/Java/Go 扩展）

## 视觉特性

- ✨ 白色毛玻璃效果（75% 透明度）
- 🌈 浅蓝到粉色渐变背景
- 🎯 圆角卡片设计
- 📱 响应式布局
- 🔗 锚点导航
- 📋 代码一键复制
- 🎨 标签页切换

## 技术栈

- 纯静态 HTML + CSS + JavaScript
- 无需构建工具，直接打开即可使用
- 参考 lua.styles.wtf 的文档结构
- 对标 VS Code Extensions 和 IntelliJ IDEA Plugin Repository
