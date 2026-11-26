# 电子元器件分拣系统 - 数字孪生

基于 Vue 3、Three.js 和 Element Plus 的电子元器件分拣 3D 数字孪生可视化系统。

## 功能特性

- **3D 可视化**: 实时 3D 动画展示完整分拣流程
- **完整工作流程**: 
  - 传送带送货
  - 高清摄像头识别
  - 机械臂分拣到不同通道
  - 取货并装载到货车
- **交互控制**: 开始、暂停、继续、停止功能
- **实时统计**: 按类型跟踪已分拣元器件
- **美观界面**: 现代化的明亮界面，使用 Element Plus

## 元器件类型

- **电容** (蓝色) - 圆柱形元器件
- **端子** (绿色) - 矩形元器件  
- **连接器** (橙色) - L 形元器件

## 技术栈

- **前端框架**: Vue 3
- **3D 图形**: Three.js
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite

## 安装

```bash
npm install
```

## 开发

```bash
npm run dev
```

应用将自动在 http://localhost:3000 打开

## 构建

```bash
npm run build
```

## 预览生产构建

```bash
npm run preview
```

## 项目结构

```
vision_sort_system_v_lingma/
├── src/
│   ├── components/        # Vue 组件
│   ├── store/            # Pinia 状态管理
│   │   └── system.js     # 系统状态管理
│   ├── three/            # Three.js 场景实现
│   │   └── SortingScene.js
│   ├── App.vue           # 主应用组件
│   ├── main.js           # 应用入口
│   └── style.css         # 全局样式
├── index.html
├── package.json
└── vite.config.js
```

## 使用说明

1. 点击 **开始** 按钮启动分拣模拟
2. 观看元器件被生成并通过所有阶段处理
3. 使用 **暂停** 暂时停止模拟
4. 使用 **继续** 从暂停状态继续
5. 点击 **停止** 重置系统

## 系统要求

- 支持 WebGL 的现代浏览器
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
