# 数据集划分工具使用说明 - datasets_split.py

## 📋 概述

`datasets_split.py` 是一个用于YOLO格式数据集划分的Python脚本。它能够自动将原始数据集按照指定比例划分为训练集、验证集和测试集，同时保持原始数据不变。

---

## ✨ 主要特性

- ✅ **保护原始数据** - 使用文件复制而非移动，确保原始数据完整
- ✅ **支持嵌套结构** - 自动处理子目录中的图片和标签
- ✅ **输出隔离** - 生成独立的新目录（默认添加 `_split` 后缀）
- ✅ **完整性保证** - 自动复制 `classes.txt` 类别文件
- ✅ **灵活配置** - 支持自定义划分比例、输出目录和随机种子
- ✅ **智能匹配** - 自动匹配图片和对应的标签文件

---

## 🚀 快速开始

### 基础用法

```bash
cd 3-dataset-split
python datasets_split.py --data-dir datasets_100
```

这将会：
1. 读取 `datasets_100` 目录中的所有图片和标签
2. 按 70:15:15 的比例划分
3. 创建新目录 `datasets_100_split`
4. 复制文件到对应的 train/val/test 子目录

---

## 📖 详细参数说明

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--data-dir` | str | `datasets_200` | 原始数据集根目录路径 |
| `--output-dir` | str | `None` | 输出目录路径（默认自动生成） |
| `--train-ratio` | float | `0.7` | 训练集比例（0-1之间） |
| `--val-ratio` | float | `0.15` | 验证集比例（0-1之间） |
| `--test-ratio` | float | `0.15` | 测试集比例（0-1之间） |
| `--seed` | int | `42` | 随机种子（保证可重复性） |

---

## 💡 使用示例

### 示例1：使用默认设置

```bash
# 使用默认比例 70:15:15，输出到 datasets_200_split
python datasets_split.py --data-dir datasets_200
```

### 示例2：自定义划分比例

```bash
# 80:10:10 划分
python datasets_split.py \
    --data-dir datasets_200 \
    --train-ratio 0.8 \
    --val-ratio 0.1 \
    --test-ratio 0.1
```

### 示例3：指定输出目录

```bash
# 输出到自定义目录
python datasets_split.py \
    --data-dir datasets_200 \
    --output-dir my_custom_dataset
```

### 示例4：调整随机种子

```bash
# 使用不同的随机种子获得不同的划分结果
python datasets_split.py \
    --data-dir datasets_200 \
    --seed 123
```

### 示例5：极端情况 - 无测试集

```bash
# 只划分训练集和验证集（90:10:0）
python datasets_split.py \
    --data-dir datasets_200 \
    --train-ratio 0.9 \
    --val-ratio 0.1 \
    --test-ratio 0.0
```

### 示例6：Windows路径示例

```bash
# Windows环境下使用完整路径
python datasets_split.py ^
    --data-dir "D:\datasets\my_data" ^
    --output-dir "D:\datasets\my_data_split"
```

### 示例7：Linux/Mac路径示例

```bash
# Linux/Mac环境下使用完整路径
python datasets_split.py \
    --data-dir "/home/user/datasets/my_data" \
    --output-dir "/home/user/datasets/my_data_split"
```

---

## 📁 输入数据结构

### 原始数据集要求

```
datasets_200/
├── classes.txt              # 必需：类别定义文件
├── images/                  # 必需：图片目录
│   ├── img1.jpg
│   ├── img2.png
│   └── ... (支持子目录)
└── labels/                  # 必需：标签目录
    ├── img1.txt
    ├── img2.txt
    └── ... (支持子目录)
```

### classes.txt 格式

```
capacitor
connector
terminal
```

每行一个类别名称，类别ID从0开始自动编号。

---

## 📂 输出数据结构

执行完成后，生成的目录结构如下：

```
datasets_200_split/
├── classes.txt              # 从原始数据复制
├── images/                  # 图片文件
│   ├── train/              # 训练集图片 (140张)
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   ├── val/                # 验证集图片 (30张)
│   │   ├── img141.jpg
│   │   └── ...
│   └── test/               # 测试集图片 (30张)
│       ├── img171.jpg
│       └── ...
└── labels/                  # 标签文件
    ├── train/              # 训练集标签 (140个)
    │   ├── img001.txt
    │   └── ...
    ├── val/                # 验证集标签 (30个)
    │   ├── img141.txt
    │   └── ...
    └── test/               # 测试集标签 (30个)
        ├── img171.txt
        └── ...
```

---

## 📊 控制台输出示例

```
============================================================
YOLO 数据集划分工具
============================================================
数据集目录: datasets_200
划分比例: 0.7:0.15:0.15
============================================================
找到 200 张图像

数据集划分:
  训练集: 140 张 (70.0%)
  验证集: 30 张 (15.0%)
  测试集: 30 张 (15.0%)

输出目录: datasets_200_split

开始划分数据...
✓ 训练集: 已复制 140 对文件
✓ 验证集: 已复制 30 对文件
✓ 测试集: 已复制 30 对文件
✓ 类别文件已复制: classes.txt

✓ 数据集划分完成！
✓ 原始数据保持不变: datasets_200
✓ 新数据集已保存到: datasets_200_split

============================================================
划分结果汇总:
  总文件数: 200
  训练集: 140
  验证集: 30
  测试集: 30
============================================================

✓ 数据集已保存到: datasets_200_split

请使用数据配置文件进行训练
============================================================
```

---

## 🔧 高级用法

### 在Python脚本中调用

```python
import os
from datasets_split import split_dataset

# 基本用法
stats = split_dataset(
    dataset_root='datasets_200',
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    seed=42
)

print(f"训练集: {stats['train']}")
print(f"验证集: {stats['val']}")
print(f"测试集: {stats['test']}")

# 自定义输出目录
stats = split_dataset(
    dataset_root='datasets_200',
    output_dir='custom_output',
    train_ratio=0.8,
    val_ratio=0.2,
    test_ratio=0.0,
    seed=123
)
```

### 批量处理多个数据集

```python
import os
from datasets_split import split_dataset

datasets = ['datasets_100', 'datasets_200', 'datasets_300']

for dataset in datasets:
    print(f"\n处理 {dataset}...")
    try:
        stats = split_dataset(
            dataset_root=dataset,
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
            seed=42
        )
        print(f"✓ {dataset} 处理完成")
    except Exception as e:
        print(f"✗ {dataset} 处理失败: {e}")
```

---

## ⚙️ 编程接口

### 函数签名

```python
def split_dataset(
    dataset_root: str,
    output_dir: str = None,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> dict:
    """
    将数据集划分为训练集、验证集和测试集
    
    Args:
        dataset_root: 数据集根目录路径
        output_dir: 输出目录路径 (默认: dataset_root_split)
        train_ratio: 训练集比例 (默认0.7)
        val_ratio: 验证集比例 (默认0.15)
        test_ratio: 测试集比例 (默认0.15)
        seed: 随机种子 (默认42)
    
    Returns:
        字典 {'train': int, 'val': int, 'test': int, 'total': int}
    """
```

---

## ⚠️ 注意事项

### 1. 比例总和必须为1

```python
# ✓ 正确
--train-ratio 0.7 --val-ratio 0.15 --test-ratio 0.15

# ✗ 错误 - 会抛出异常
--train-ratio 0.8 --val-ratio 0.2 --test-ratio 0.1
```

### 2. 必需的文件和目录

- ✅ `classes.txt` 文件必须存在
- ✅ `images/` 目录必须存在且包含图片
- ✅ `labels/` 目录必须存在且包含对应的标签文件

### 3. 文件格式支持

支持的图片格式：
- `.jpg` / `.jpeg`
- `.png`
- `.bmp`

标签文件格式：
- `.txt` (YOLO格式)

### 4. 标签文件匹配

脚本会自动匹配图片和标签：
- `img001.jpg` → `img001.txt`
- 支持不同扩展名（如 `.JPG` → `.txt`）

### 5. 重复执行

可以多次执行脚本，每次都会覆盖之前的输出目录。如果想保留历史版本，请使用不同的 `--output-dir`。

---

## 🐛 常见问题

### Q1: 提示"未找到标签文件"？

**原因**: 图片和标签文件名不匹配  
**解决**: 确保每个图片都有对应的标签文件

```
img001.jpg → img001.txt  ✓
img002.jpg → img003.txt  ✗ (文件名不匹配)
```

### Q2: 如何验证划分结果？

**方法**: 检查输出目录中的文件数量

```bash
# 统计各集合的文件数
ls datasets_200_split/images/train/ | wc -l  # 应该是140
ls datasets_200_split/images/val/ | wc -l    # 应该是30
ls datasets_200_split/images/test/ | wc -l   # 应该是30
```

### Q3: 能否只划分部分数据？

**回答**: 可以，先创建一个包含部分数据的临时目录，然后对该目录执行脚本

### Q4: 随机种子有什么作用？

**回答**: 随机种子确保每次运行得到相同的划分结果。使用相同的 `--seed` 值，无论运行多少次，划分结果都一致。

### Q5: 如何处理大数据集？

**建议**: 
- 增加 `--workers` 参数（如果未来支持多线程）
- 确保有足够的磁盘空间（需要双倍空间用于复制）
- 考虑使用SSD提高IO速度

---

## 📝 最佳实践

### 1. 保持一致性

在项目中使用固定的划分比例，便于对比实验结果。

```bash
# 推荐：团队统一标准
--train-ratio 0.7 --val-ratio 0.15 --test-ratio 0.15
```

### 2. 记录随机种子

记录使用的随机种子，确保实验可复现。

```bash
# 在实验记录中保存
python datasets_split.py --data-dir datasets_200 --seed 42
```

### 3. 验证输出

划分完成后，检查文件数量和分布是否合理。

```bash
# 快速验证
tree datasets_200_split/
```

### 4. 备份重要数据

虽然脚本不会修改原始数据，但建议在处理前备份重要数据。

### 5. 命名规范

使用清晰的目录命名，如 `datasets_200_train70_val15_test15`

---

## 🔄 与其他工具配合

### 1. 与训练脚本配合

```bash
# 步骤1: 划分数据集
python datasets_split.py --data-dir datasets_200

# 步骤2: 训练模型
cd ../4-model_training
python train.py --data-dir ../3-dataset-split/datasets_200_split --epochs 100
```

### 2. 与推理脚本配合

```bash
# 使用测试集进行推理验证
python inference.py \
    --model models/best.pt \
    --source datasets_200_split/images/test/
```

---

## 📚 相关文档

- [Ultralytics YOLOv8 官方文档](https://docs.ultralytics.com/)
- [数据集使用说明](../4-model_training/datasets_100_split/README.md)
- 项目根目录的其他文档

---

## 📞 技术支持

如遇到问题，请检查：
1. Python版本 >= 3.7
2. 已安装必要的依赖库
3. 路径是否正确（使用绝对路径更可靠）
4. 文件权限是否足够

---

**最后更新**: 2024  
**脚本版本**: v1.0  
**适用平台**: Windows / Linux / macOS