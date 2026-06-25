# SecurePaste 前端演示

这是由 Rigor Frontend Engineer 生成的**完整前端页面**。

## 预览方式

1. **直接双击打开**
   ```bash
   # macOS
   open index.html
   
   # Linux
   xdg-open index.html
   
   # Windows
   start index.html
   ```

2. **本地服务器预览**
   ```bash
   cd ~/Rigor-main/examples/secure-paste/demo
   python3 -m http.server 8080
   # 浏览器访问: http://localhost:8080
   ```

3. **Demo 模式 (模拟查看流程)**
   ```
   http://localhost:8080/index.html?demo=1
   ```
   输入密码 `demo` 即可查看模拟的阅后即焚效果。

## 功能特性

| 功能 | 状态 |
|------|------|
| 创建页面（代码输入 + 选项） | ✅ |
| 密码保护弹窗 | ✅ |
| 阅后即焚提示 | ✅ |
| 语法高亮 (Highlight.js) | ✅ |
| 暗色 Cyberpunk 主题 | ✅ |
| 响应式设计 (手机/平板) | ✅ |
| 复制内容按钮 | ✅ |

## 设计风格

* **主题**: 深色 Cyberpunk（蓝紫渐变）
* **动效**: 背景光晕脉冲动画
* **字体**: 等宽代码字体 + 系统默认字体
* **图标**: Emoji（零依赖）
