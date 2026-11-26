"""
YOLOv8 模型训练脚本
支持GPU/CPU训练，可配置训练轮数等参数
数据集格式：YOLO格式（txt标签文件）
"""

import argparse
import os
import sys
from pathlib import Path

# 禁用 ultralytics 的自动下载检查
os.environ['YOLO_DOWNLOAD_CHECK'] = 'False'

# 检查并导入ultralytics
try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 未安装 ultralytics 库")
    print("请运行: pip install ultralytics")
    sys.exit(1)


def create_dataset_yaml(dataset_root, classes_file):
    """
    创建YOLO数据集配置文件（基于划分的数据集结构）
    
    Args:
        dataset_root: 数据集根目录
        classes_file: 类别文件路径 
     
    Returns:
        yaml文件路径
    """
    # 读取类别名称
    with open(classes_file, 'r', encoding='utf-8') as f:
        classes = [line.strip() for line in f if line.strip()]
    
    # 检查是否存在已划分的目录结构
    images_dir = os.path.join(dataset_root, 'images')
    has_split_structure = (
        os.path.exists(os.path.join(images_dir, 'train')) and
        os.path.exists(os.path.join(images_dir, 'val'))
    )
    
    if has_split_structure:
        # 使用划分后的目录结构（使用绝对路径）
        yaml_content = f"""# YOLOv8 数据集配置文件（已划分训练集/验证集/测试集）
# 自动生成

# 数据集根目录（绝对路径）
path: {dataset_root}

# 训练集、验证集和测试集路径（相对于path）
train: images/train
val: images/val
test: images/test

# 类别数量
nc: {len(classes)}

# 类别名称
names: {classes}
"""
    else:
        # 使用未划分的目录结构（向后兼容）
        yaml_content = f"""# YOLOv8 数据集配置文件（未划分）
# 自动生成

# 数据集路径（相对于此yaml文件的路径）
path: {dataset_root}

# 训练集和验证集图像路径
train: images
val: images

# 类别数量
nc: {len(classes)}

# 类别名称
names: {classes}
"""
    
    # 保存yaml文件到datasets目录
    yaml_path = os.path.join(dataset_root, 'dataset.yaml')
    print(f"保存数据集配置文件: {yaml_path}")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"✓ 数据集配置文件已创建: {yaml_path}")
    print(f"  类别数量: {len(classes)}")
    print(f"  类别列表: {', '.join(classes[:5])}{'...' if len(classes) > 5 else ''}")
    
    return yaml_path


def train_yolo_model(
    data_yaml,
    epochs=100,
    batch=16,
    imgsz=640,
    device='cuda',
    model_name='yolov8n.pt',
    save_dir='models',
    lr0=0.01,
    patience=50,
    workers=8,
    optimizer='SGD',
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3.0,
    augment=True,
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=0.0,
    translate=0.1,
    scale=0.5,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.0,
    copy_paste=0.0,
):
    """
    训练YOLOv8模型
    
    Args:
        data_yaml: 数据集配置文件路径
        epochs: 训练轮数
        batch: 批次大小
        imgsz: 图像尺寸
        device: 训练设备 ('cuda', 'cpu', 或 '0', '0,1,2,3' 等多GPU)
        model_name: 预训练模型名称 (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)
        save_dir: 模型保存目录
        lr0: 初始学习率
        patience: 早停耐心值（epochs）
        workers: 数据加载工作线程数
        optimizer: 优化器 ('SGD', 'Adam', 'AdamW')
        momentum: SGD动量
        weight_decay: 权重衰减
        warmup_epochs: 预热轮数
        augment: 是否使用数据增强
        hsv_h: HSV色调增强
        hsv_s: HSV饱和度增强
        hsv_v: HSV明度增强
        degrees: 旋转角度
        translate: 平移
        scale: 缩放
        shear: 剪切
        perspective: 透视
        flipud: 垂直翻转概率
        fliplr: 水平翻转概率
        mosaic: Mosaic增强概率
        mixup: MixUp增强概率
        copy_paste: CopyPaste增强概率
    
    Returns:
        训练结果对象
    """
    
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    print("=" * 60)
    print("YOLOv8 模型训练")
    print("=" * 60)
    print(f"数据集配置: {data_yaml}")
    print(f"预训练模型: {model_name}")
    print(f"训练轮数: {epochs}")
    print(f"批次大小: {batch}")
    print(f"图像尺寸: {imgsz}")
    print(f"训练设备: {device}")
    print(f"保存目录: {save_dir}")
    print(f"学习率: {lr0}")
    print(f"优化器: {optimizer}")
    print("=" * 60)
    
    # 加载预训练模型
    print("\n[1/3] 加载预训练模型...")
    
    model_dir = os.path.dirname(os.path.abspath(__file__))
    local_model_path = os.path.join(model_dir, model_name)
    
    if os.path.exists(local_model_path):
        model_path = local_model_path
        print(f"✓ 使用本地模型: {model_path}")
    else:
        model_path = model_name
        print(f"使用模型: {model_path}")
    
    model = YOLO(model_path)
    
    # 开始训练
    print("\n[2/3] 开始训练...")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=save_dir,
        name='train',
        exist_ok=True,
        pretrained=True,
        optimizer=optimizer,
        lr0=lr0,
        patience=patience,
        workers=workers,
        momentum=momentum,
        weight_decay=weight_decay,
        warmup_epochs=warmup_epochs,
        
        # 数据增强参数
        augment=augment,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
        degrees=degrees,
        translate=translate,
        scale=scale,
        shear=shear,
        perspective=perspective,
        flipud=flipud,
        fliplr=fliplr,
        mosaic=mosaic,
        mixup=mixup,
        copy_paste=copy_paste,
        
        # 其他参数
        verbose=True,
        plots=True,  # 生成训练图表
        save=True,   # 保存检查点
    )
    
    # 训练完成
    print("\n[3/3] 训练完成！")
    print("=" * 60)
    print(f"最佳模型保存在: {os.path.join(save_dir, 'train', 'weights', 'best.pt')}")
    print(f"最后模型保存在: {os.path.join(save_dir, 'train', 'weights', 'last.pt')}")
    print(f"训练图表保存在: {os.path.join(save_dir, 'train')}")
    print("=" * 60)
    
    return results


def main():
    """主函数 - 解析命令行参数并启动训练"""
    
    parser = argparse.ArgumentParser(
        description='YOLOv8 模型训练脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用GPU训练100轮
  python train.py --device cuda --epochs 100
  
  # 使用CPU训练50轮，批次大小为8
  python train.py --device cpu --epochs 50 --batch 8
  
  # 使用特定GPU，更大的图像尺寸
  python train.py --device 0 --epochs 200 --imgsz 1280 --batch 32
  
  # 使用不同的预训练模型
  python train.py --model yolov8s.pt --epochs 150
        """
    )
    
    # 基本参数
    parser.add_argument('--device', type=str, default='cuda',
                        help='训练设备: cuda, cpu, 或 GPU编号 (如 0, 0,1,2,3)')
    parser.add_argument('--epochs', type=int, default=1000,
                        help='训练轮数 (默认: 100)')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小 (默认: 16)')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='图像尺寸 (默认: 640)')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                        help='预训练模型: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt')
    
    # 数据集参数
    parser.add_argument('--data-dir', type=str, default='datasets',
                        help='数据集根目录 (默认: datasets)')
    parser.add_argument('--images-dir', type=str, default='images',
                        help='图像子目录 (默认: images)')
    parser.add_argument('--labels-dir', type=str, default='labels',
                        help='标签子目录 (默认: labels)')
    parser.add_argument('--classes-file', type=str, default=None,
                        help='类别文件路径 (默认: datasets/classes.txt)')
    
    # 训练超参数
    parser.add_argument('--lr', type=float, default=0.01,
                        help='初始学习率 (默认: 0.01)')
    parser.add_argument('--optimizer', type=str, default='SGD',
                        help='优化器: SGD, Adam, AdamW (默认: SGD)')
    parser.add_argument('--momentum', type=float, default=0.937,
                        help='SGD动量 (默认: 0.937)')
    parser.add_argument('--weight-decay', type=float, default=0.0005,
                        help='权重衰减 (默认: 0.0005)')
    parser.add_argument('--patience', type=int, default=50,
                        help='早停耐心值 (默认: 50)')
    parser.add_argument('--warmup-epochs', type=float, default=3.0,
                        help='预热轮数 (默认: 3.0)')
    
    # 保存参数
    parser.add_argument('--save-dir', type=str, default='models',
                        help='模型保存目录 (默认: models)')
    
    # 数据增强参数
    parser.add_argument('--no-augment', action='store_true',
                        help='禁用数据增强')
    parser.add_argument('--fliplr', type=float, default=0.5,
                        help='水平翻转概率 (默认: 0.5)')
    parser.add_argument('--flipud', type=float, default=0.0,
                        help='垂直翻转概率 (默认: 0.0)')
    parser.add_argument('--mosaic', type=float, default=1.0,
                        help='Mosaic增强概率 (默认: 1.0)')
    parser.add_argument('--mixup', type=float, default=0.0,
                        help='MixUp增强概率 (默认: 0.0)')
    
    # 其他参数
    parser.add_argument('--workers', type=int, default=8,
                        help='数据加载工作线程数 (默认: 8)')
    
    args = parser.parse_args()
    
    model_dir = os.path.dirname(os.path.abspath(__file__))
    if args.model == 'yolov8n.pt' and not os.path.exists(args.model):
        args.model = os.path.join(model_dir, 'yolov8n.pt')
        if not os.path.exists(args.model):
            print(f"错误: 模型文件不存在: {args.model}")
            sys.exit(1)
    
    # 确定类别文件路径
    if args.classes_file is None:
        args.classes_file = os.path.join(args.data_dir,  'classes.txt')
    
    print(args.classes_file)
    # 检查文件和目录是否存在
    if not os.path.exists(args.classes_file):
        print(f"错误: 类别文件不存在: {args.classes_file}")
        sys.exit(1)
    
    images_path = os.path.join(args.data_dir, args.images_dir)
    if not os.path.exists(images_path):
        print(f"错误: 图像目录不存在: {images_path}")
        sys.exit(1)
    
    # 创建或使用已有的数据集配置文件
    dataset_root = os.path.abspath(args.data_dir)
    print(f"数据集根目录: {dataset_root}")
    
    # 检查是否存在已划分的数据集配置文件
    split_yaml_path = os.path.join(dataset_root, 'dataset_split.yaml')
    yaml_path = os.path.join(dataset_root, 'dataset.yaml')
    
    if os.path.exists(split_yaml_path):
        # 使用已划分的数据集配置文件
        yaml_path = split_yaml_path
        print(f"\n✓ 发现已划分的数据集配置文件: {yaml_path}")
        print("  将使用独立的训练集、验证集和测试集")
    elif os.path.exists(yaml_path):
        # 使用已有的数据集配置文件
        print(f"\n✓ 使用现有的数据集配置文件: {yaml_path}")
    else:
        # 创建新的数据集配置文件
        print(f"\n⚠ 未找到数据集配置文件，正在基于划分的数据集创建...")
        yaml_path = create_dataset_yaml(dataset_root, args.classes_file)

    print(f"\n使用的数据集配置文件: {yaml_path}")
    
    # 开始训练
    try:
        results = train_yolo_model(
            data_yaml=yaml_path,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            model_name=args.model,
            save_dir=args.save_dir,
            lr0=args.lr,
            patience=args.patience,
            workers=args.workers,
            optimizer=args.optimizer,
            momentum=args.momentum,
            weight_decay=args.weight_decay,
            warmup_epochs=args.warmup_epochs,
            augment=not args.no_augment,
            fliplr=args.fliplr,
            flipud=args.flipud,
            mosaic=args.mosaic,
            mixup=args.mixup,
        )
        
        print("\n✓ 训练成功完成！")
        return 0
        
    except Exception as e:
        print(f"\n✗ 训练失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
