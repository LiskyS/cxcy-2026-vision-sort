# YOLOv8 模型训练工具使用说明 - train.py

## 📋 概述

`train.py` 是一个基于 Ultralytics YOLOv8 的模型训练脚本，支持灵活的参数配置、GPU/CPU训练，以及自动的数据集配置文件生成。

---

## ✨ 主要特性

- ✅ **智能YAML配置** - 自动检测数据集结构并生成配置文件
- ✅ **绝对路径支持** - 避免路径解析错误（符合项目规范）
- ✅ **多GPU支持** - 支持单卡/多卡分布式训练
- ✅ **灵活参数配置** - 50+可配置训练参数
- ✅ **数据增强** - 内置Mosaic、MixUp等增强技术
- ✅ **早停机制** - 自动监控验证集指标
- ✅ **检查点保存** - 自动保存最佳模型和最新模型
- ✅ **可视化图表** - 自动生成训练曲线和混淆矩阵

---

## 🚀 快速开始

### 基础用法

```bash
cd 4-model_training
python train.py --data-dir datasets_100_split --epochs 100
```

这将会：
1. 自动检测数据集结构
2. 生成或加载 `dataset.yaml` 配置文件
3. 使用默认参数训练YOLOv8n模型100轮
4. 保存训练结果到 `models/` 目录

---

## 📖 详细参数说明

### 基本参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--device` | str | `cuda` | 训练设备: `cuda`, `cpu`, 或GPU编号如 `0`, `0,1,2,3` |
| `--epochs` | int | `1000` | 训练轮数 |
| `--batch` | int | `16` | 批次大小 |
| `--imgsz` | int | `640` | 图像尺寸（像素） |
| `--model` | str | `yolov8n.pt` | 预训练模型: `yolov8n/s/m/l/x.pt` |

### 数据集参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--data-dir` | str | `datasets` | 数据集根目录路径 |
| `--images-dir` | str | `images` | 图像子目录名称 |
| `--labels-dir` | str | `labels` | 标签子目录名称 |
| `--classes-file` | str | `None` | 类别文件路径（默认: data_dir/classes.txt） |

### 训练超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--lr` | float | `0.01` | 初始学习率 |
| `--optimizer` | str | `SGD` | 优化器: `SGD`, `Adam`, `AdamW` |
| `--momentum` | float | `0.937` | SGD动量 |
| `--weight-decay` | float | `0.0005` | 权重衰减 |
| `--patience` | int | `50` | 早停耐心值（轮数） |
| `--warmup-epochs` | float | `3.0` | 学习率预热轮数 |

### 保存参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--save-dir` | str | `models` | 模型和结果保存目录 |

### 数据增强参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--no-augment` | flag | - | 禁用数据增强 |
| `--fliplr` | float | `0.5` | 水平翻转概率 |
| `--flipud` | float | `0.0` | 垂直翻转概率 |
| `--mosaic` | float | `1.0` | Mosaic增强概率 |
| `--mixup` | float | `0.0` | MixUp增强概率 |

### 其他参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--workers` | int | `8` | 数据加载工作线程数 |

---

## 💡 使用示例

### 示例1：使用默认设置快速测试

```bash
# 快速测试训练（10轮）
python train.py --data-dir datasets_100_split --epochs 10 --batch 8
```

### 示例2：标准训练（推荐配置）

```bash
# 标准训练100轮
python train.py \
    --data-dir datasets_100_split \
    --epochs 100 \
    --batch 16 \
    --imgsz 640 \
    --device cuda \
    --patience 50
```

### 示例3：使用CPU训练

```bash
# CPU训练（适合无GPU环境）
python train.py \
    --data-dir datasets_100_split \
    --device cpu \
    --epochs 100 \
    --batch 8
```

### 示例4：多GPU分布式训练

```bash
# 使用GPU 0和1训练
python train.py \
    --data-dir datasets_100_split \
    --device 0,1 \
    --epochs 100 \
    --batch 32
```

### 示例5：使用更大的图像尺寸

```bash
# 高分辨率图像训练
python train.py \
    --data-dir datasets_100_split \
    --imgsz 1280 \
    --epochs 100 \
    --batch 8
```

### 示例6：调整学习率和优化器

```bash
# 使用Adam优化器和较低的学习率
python train.py \
    --data-dir datasets_100_split \
    --optimizer Adam \
    --lr 0.001 \
    --epochs 100
```

### 示例7：启用强数据增强

```bash
# 启用MixUp增强
python train.py \
    --data-dir datasets_100_split \
    --mixup 0.1 \
    --mosaic 1.0 \
    --fliplr 0.5 \
    --epochs 200
```

### 示例8：禁用数据增强（基线训练）

```bash
# 不使用任何数据增强
python train.py \
    --data-dir datasets_100_split \
    --no-augment \
    --epochs 100
```

### 示例9：长时间训练（500轮）

```bash
# 深度训练，增加耐心值
python train.py \
    --data-dir datasets_100_split \
    --epochs 500 \
    --patience 100 \
    --batch 16
```

### 示例10：使用不同的预训练模型

```bash
# 使用YOLOv8s（更大的模型）
python train.py \
    --data-dir datasets_100_split \
    --model yolov8s.pt \
    --epochs 100
```

### 示例11：自定义保存目录

```bash
# 保存到指定目录
python train.py \
    --data-dir datasets_100_split \
    --save-dir experiments/exp001 \
    --epochs 100
```

### 示例12：Windows完整路径示例

```bash
# 使用Windows绝对路径
python train.py ^
    --data-dir "D:\projects\datasets\datasets_100_split" ^
    --epochs 100 ^
    --save-dir "D:\projects\models\model_v1"
```

### 示例13：Linux/Mac完整路径示例

```bash
# 使用Linux/Mac绝对路径
python train.py \
    --data-dir "/home/user/datasets/datasets_100_split" \
    --epochs 100 \
    --save-dir "/home/user/models/model_v1"
```

---

## 📁 输入数据结构

### 必需的数据集结构

```
datasets_100_split/
├── classes.txt              # 必需：类别定义
├── dataset.yaml            # 可选：会自动生成
├── images/
│   ├── train/              # 训练集图片
│   ├── val/                # 验证集图片
│   └── test/               # 测试集图片（可选）
└── labels/
    ├── train/              # 训练集标签
    ├── val/                # 验证集标签
    └── test/               # 测试集标签（可选）
```

### classes.txt 格式

```
capacitor
connector
terminal
```

每行一个类别名称，ID从0开始自动分配。

---

## 📂 输出结果结构

训练完成后，结果保存在以下位置：

```
models/
└── train/
    ├── weights/
    │   ├── best.pt          # 最佳模型（验证集mAP最高）
    │   └── last.pt          # 最后一轮模型
    ├── results.csv          # 训练指标CSV文件
    ├── results.png          # 训练曲线图
    ├── confusion_matrix.png # 混淆矩阵
    ├── F1_curve.png        # F1分数曲线
    ├── PR_curve.png        # 精确率-召回率曲线
    ├── P_curve.png         # 精确率曲线
    ├── R_curve.png         # 召回率曲线
    └── args.yaml           # 训练参数记录
```

---

## 📊 控制台输出示例

```
============================================================
YOLOv8 模型训练
============================================================
数据集配置: datasets_100_split/dataset.yaml
预训练模型: yolov8n.pt
训练轮数: 100
批次大小: 16
图像尺寸: 640
训练设备: cuda
保存目录: models
学习率: 0.01
优化器: SGD
============================================================

[1/3] 加载预训练模型...
✓ 使用本地模型: D:\competition\competition_2026_cxcy\4-model_training\yolov8n.pt

[2/3] 开始训练...
Ultralytics YOLOv8.0.123  Python-3.9.0 torch-2.0.0 CUDA:0 (NVIDIA GeForce RTX 3090, 24576MiB)

epoch   train/box_loss  train/cls_loss  train/dfl_loss  metrics/precision(mAP50)  metrics/recall  metrics/mAP50-95  val/box_loss  val/cls_loss  val/dfl_loss  lr/pg0  lr/pg1  lr/pg2
1/100      1.2345          2.3456          1.4567          0.234                  0.456           0.123           1.3456        2.4567        1.5678        0.01    0.01    0.01
2/100      1.1234          2.1234          1.3456          0.345                  0.567           0.234           1.2345        2.3456        1.4567        0.01    0.01    0.01
...

[3/3] 训练完成！
============================================================
最佳模型保存在: models/train/weights/best.pt
最后模型保存在: models/train/weights/last.pt
训练图表保存在: models/train
============================================================
```

---

## 🔧 高级用法

### 在Python脚本中调用

```python
import sys
import os
from train import train_yolo_model, create_dataset_yaml

# 方法1: 直接训练
results = train_yolo_model(
    data_yaml='datasets_100_split/dataset.yaml',
    epochs=100,
    batch=16,
    imgsz=640,
    device='cuda',
    model_name='yolov8n.pt',
    save_dir='models'
)

# 方法2: 先创建配置再训练
yaml_path = create_dataset_yaml(
    dataset_root='datasets_100_split',
    classes_file='datasets_100_split/classes.txt'
)

results = train_yolo_model(
    data_yaml=yaml_path,
    epochs=100,
    batch=16
)
```

### 批量实验

```python
import os

# 不同参数的批量实验
configs = [
    {'epochs': 100, 'batch': 16, 'lr': 0.01},
    {'epochs': 100, 'batch': 8, 'lr': 0.001},
    {'epochs': 200, 'batch': 16, 'lr': 0.01},
]

for i, config in enumerate(configs):
    print(f"\n运行实验 {i+1}...")
    os.system(f"""
        python train.py \\
            --data-dir datasets_100_split \\
            --epochs {config['epochs']} \\
            --batch {config['batch']} \\
            --lr {config['lr']} \\
            --save-dir experiments/exp_{i+1}
    """)
```

---

## ⚙️ 编程接口

### 主训练函数

```python
def train_yolo_model(
    data_yaml: str,
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = 'cuda',
    model_name: str = 'yolov8n.pt',
    save_dir: str = 'models',
    lr0: float = 0.01,
    patience: int = 50,
    workers: int = 8,
    optimizer: str = 'SGD',
    momentum: float = 0.937,
    weight_decay: float = 0.0005,
    warmup_epochs: float = 3.0,
    augment: bool = True,
    hsv_h: float = 0.015,
    hsv_s: float = 0.7,
    hsv_v: float = 0.4,
    degrees: float = 0.0,
    translate: float = 0.1,
    scale: float = 0.5,
    shear: float = 0.0,
    perspective: float = 0.0,
    flipud: float = 0.0,
    fliplr: float = 0.5,
    mosaic: float = 1.0,
    mixup: float = 0.0,
    copy_paste: float = 0.0,
) -> Results:
    """
    训练YOLOv8模型
    
    Returns:
        Ultralytics训练结果对象
    """
```

### YAML配置生成函数

```python
def create_dataset_yaml(
    dataset_root: str,
    classes_file: str
) -> str:
    """
    创建YOLO数据集配置文件
    
    Args:
        dataset_root: 数据集根目录
        classes_file: 类别文件路径
    
    Returns:
        生成的YAML文件路径
    """
```

---

## 🎯 模型选择指南

### YOLOv8 模型对比

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|--------|------|------|---------|
| yolov8n.pt | 3.2M | 最快 | 中等 | 快速原型、边缘设备 |
| yolov8s.pt | 11.2M | 快 | 良好 | 平衡性能和速度 |
| yolov8m.pt | 25.9M | 中 | 优秀 | 精度优先 |
| yolov8l.pt | 43.7M | 慢 | 很好 | 高精度需求 |
| yolov8x.pt | 68.2M | 最慢 | 最佳 | 最高精度需求 |

### 显存需求参考

以 batch=16, imgsz=640 为例：

| 模型 | GPU显存需求 |
|------|------------|
| yolov8n | ~4GB |
| yolov8s | ~6GB |
| yolov8m | ~10GB |
| yolov8l | ~14GB |
| yolov8x | ~20GB |

---

## ⚠️ 注意事项

### 1. 路径配置

**重要**: `dataset.yaml` 中的 `path` 字段必须使用**绝对路径**！

如果使用相对路径遇到错误：
```
FileNotFoundError: Dataset '...' images not found, missing path 'images\val'
```

请重新生成YAML配置文件，确保使用绝对路径。

### 2. 显存不足解决方案

如果遇到 `CUDA out of memory` 错误：

```bash
# 方案1: 减小batch size
python train.py --data-dir datasets_100_split --batch 4

# 方案2: 减小图像尺寸
python train.py --data-dir datasets_100_split --imgsz 416

# 方案3: 使用更小的模型
python train.py --data-dir datasets_100_split --model yolov8n.pt

# 方案4: 组合使用
python train.py --data-dir datasets_100_split --batch 4 --imgsz 416 --model yolov8n.pt
```

### 3. 训练速度慢

```bash
# 增加数据加载线程
python train.py --data-dir datasets_100_split --workers 16

# 使用多GPU
python train.py --data-dir datasets_100_split --device 0,1
```

### 4. 文件缺失检查

确保数据集包含：
- ✅ `classes.txt` 文件
- ✅ `images/train/` 和 `images/val/` 目录
- ✅ `labels/train/` 和 `labels/val/` 目录
- ✅ 对应的图片和标签文件

### 5. 比例总和验证

如果手动修改划分比例，确保：
```python
train_ratio + val_ratio + test_ratio = 1.0
```

---

## 🐛 常见问题

### Q1: 提示 "Dataset error: images not found"？

**原因**: YAML配置文件中的路径不正确  
**解决**: 
1. 检查 `dataset.yaml` 中的 `path` 是否为绝对路径
2. 确认 `images/train` 和 `images/val` 目录存在
3. 重新运行脚本自动生成配置

### Q2: CUDA Out of Memory？

**解决**:
```bash
# 减小batch size
--batch 4

# 减小图像尺寸
--imgsz 416

# 使用更小模型
--model yolov8n.pt
```

### Q3: 训练很慢？

**优化**:
```bash
# 增加workers
--workers 16

# 使用GPU
--device cuda

# 多GPU
--device 0,1
```

### Q4: 如何继续训练？

**方法**: 修改代码加载 `last.pt` 而非 `yolov8n.pt`

```python
model = YOLO('models/train/weights/last.pt')
results = model.train(resume=True)
```

### Q5: 如何评估模型？

**方法**: 使用验证集

```python
from ultralytics import YOLO
model = YOLO('models/train/weights/best.pt')
metrics = model.val(data='datasets_100_split/dataset.yaml')
print(f"mAP50: {metrics.box.map50:.4f}")
```

### Q6: 如何选择最佳模型？

**回答**: 脚本自动保存两个模型：
- `best.pt`: 验证集mAP最高的模型（推荐使用）
- `last.pt`: 最后一轮的模型

### Q7: 训练中断了怎么办？

**解决**: 从最后一个检查点继续

```python
model = YOLO('models/train/weights/last.pt')
results = model.train(resume=True)
```

---

## 📊 性能优化建议

### 1. 数据准备

- ✓ 使用SSD存储数据集
- ✓ 预处理图像为统一尺寸
- ✓ 提前划分好train/val/test

### 2. 硬件配置

- ✓ 使用高性能GPU（RTX 3090, A100等）
- ✓ 充足的RAM（建议16GB+）
- ✓ 多GPU并行训练

### 3. 参数调优

```bash
# 推荐的起始配置
python train.py \
    --data-dir datasets_100_split \
    --epochs 100 \
    --batch 16 \
    --imgsz 640 \
    --device cuda \
    --optimizer SGD \
    --lr 0.01 \
    --patience 50 \
    --workers 8
```

---

## 🔄 完整工作流程

### 步骤1: 准备数据集

```bash
cd 3-dataset-split
python datasets_split.py --data-dir datasets_200
```

### 步骤2: 训练模型

```bash
cd ../4-model_training
python train.py --data-dir ../3-dataset-split/datasets_200_split --epochs 100
```

### 步骤3: 评估模型

```python
from ultralytics import YOLO
model = YOLO('models/train/weights/best.pt')
metrics = model.val()
print(metrics.box.map50)
```

### 步骤4: 推理测试

```python
results = model('path/to/test/image.jpg')
results[0].show()
```

---

## 📚 相关文档

- [数据集划分工具文档](../3-dataset-split/README.md)
- [数据集使用说明](datasets_100_split/README.md)
- [Ultralytics官方文档](https://docs.ultralytics.com/)
- [YOLOv8训练指南](https://docs.ultralytics.com/modes/train/)

---

## 📞 技术支持

### 环境要求

- Python >= 3.7
- PyTorch >= 1.13
- Ultralytics YOLOv8
- CUDA >= 11.7 (GPU训练)

### 安装依赖

```bash
pip install ultralytics
pip install torch torchvision torchaudio
```

### 版本信息

- **脚本版本**: v1.0
- **最后更新**: 2024
- **适用平台**: Windows / Linux / macOS

---

**祝您训练顺利！** 🚀