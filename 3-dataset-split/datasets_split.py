"""
数据集划分脚本
将数据集划分为训练集、验证集和测试集
"""

import os
import shutil
import random
from pathlib import Path


def split_dataset(
    dataset_root,
    output_dir=None,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    seed=42
):
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
        各集合的文件数量统计
    """
    # 设置随机种子以保证可重复性
    random.seed(seed)
    
    # 验证比例总和
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "比例总和必须等于1.0"
    
    # 获取图像和标签目录
    images_dir = os.path.join(dataset_root, 'images')
    labels_dir = os.path.join(dataset_root, 'labels')
    
    if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
        raise FileNotFoundError(f"图像或标签目录不存在: {images_dir} 或 {labels_dir}")
    
    # 获取所有图像文件（包括子目录中的文件）
    image_files = []
    for root, dirs, files in os.walk(images_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                # 保存相对路径以处理子目录结构
                rel_path = os.path.relpath(os.path.join(root, f), images_dir)
                image_files.append(rel_path)
    
    if not image_files:
        raise ValueError(f"在 {images_dir} 中未找到图像文件")
    
    print(f"找到 {len(image_files)} 张图像")
    
    # 随机打乱文件列表
    random.shuffle(image_files)
    
    # 计算划分点
    total = len(image_files)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)
    # 测试集数量为剩余部分
    test_count = total - train_count - val_count
    
    print(f"\n数据集划分:")
    print(f"  训练集: {train_count} 张 ({train_count/total*100:.1f}%)")
    print(f"  验证集: {val_count} 张 ({val_count/total*100:.1f}%)")
    print(f"  测试集: {test_count} 张 ({test_count/total*100:.1f}%)")
    
    # 划分文件列表
    train_files = image_files[:train_count]
    val_files = image_files[train_count:train_count + val_count]
    test_files = image_files[train_count + val_count:]
    
    # 设置输出目录（如果未指定，则使用 dataset_root_split）
    if output_dir is None:
        base_name = os.path.basename(os.path.normpath(dataset_root))
        output_dir = os.path.join(os.path.dirname(dataset_root), f"{base_name}_split")
    
    print(f"\n输出目录: {output_dir}")
    
    # 创建输出目录结构
    output_images_dir = os.path.join(output_dir, 'images')
    output_labels_dir = os.path.join(output_dir, 'labels')
    
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(output_images_dir, split), exist_ok=True)
        os.makedirs(os.path.join(output_labels_dir, split), exist_ok=True)
    
    # 定义复制文件的函数（替代原来的移动）
    def copy_files(file_list, split_name):
        moved_count = 0
        for img_rel_path in file_list:
            # 构建源文件路径
            img_src = os.path.join(images_dir, img_rel_path)
            
            # 获取对应的标签文件（扩展名可能不同）
            base_name = Path(img_rel_path).stem
            label_file = None
            
            # 在原始labels目录中查找对应的标签文件
            for root, dirs, files in os.walk(labels_dir):
                for f in files:
                    if Path(f).stem == base_name and f.endswith('.txt'):
                        label_file = os.path.join(root, f)
                        break
                if label_file:
                    break
            
            if label_file is None:
                print(f"  警告: 未找到 {img_rel_path} 对应的标签文件，跳过")
                continue
            
            # 计算目标路径（保持原始文件名）
            img_filename = os.path.basename(img_rel_path)
            img_dst = os.path.join(output_images_dir, split_name, img_filename)
            
            # 复制图像文件
            shutil.copy2(img_src, img_dst)
            
            # 复制标签文件
            label_filename = os.path.basename(label_file)
            label_dst = os.path.join(output_labels_dir, split_name, label_filename)
            shutil.copy2(label_file, label_dst)
            
            moved_count += 1
        
        return moved_count
    
    # 复制文件到对应目录
    print("\n开始划分数据...")
    train_moved = copy_files(train_files, 'train')
    print(f"✓ 训练集: 已复制 {train_moved} 对文件")
    
    val_moved = copy_files(val_files, 'val')
    print(f"✓ 验证集: 已复制 {val_moved} 对文件")
    
    test_moved = copy_files(test_files, 'test')
    print(f"✓ 测试集: 已复制 {test_moved} 对文件")
    
    # 复制类别文件
    classes_file = os.path.join(dataset_root, 'classes.txt')
    if os.path.exists(classes_file):
        shutil.copy2(classes_file, os.path.join(output_dir, 'classes.txt'))
        print(f"✓ 类别文件已复制: classes.txt")
    
    print("\n✓ 数据集划分完成！")
    print(f"✓ 原始数据保持不变: {dataset_root}")
    print(f"✓ 新数据集已保存到: {output_dir}")
    
    return {
        'train': train_moved,
        'val': val_moved,
        'test': test_moved,
        'total': train_moved + val_moved + test_moved
    }

 
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO数据集划分工具')
    parser.add_argument('--data-dir', type=str, default='datasets_200',
                        help='数据集根目录 (默认: datasets_100)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='输出目录路径 (默认: data_dir_split)')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                        help='训练集比例 (默认: 0.7)')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                        help='验证集比例 (默认: 0.15)')
    parser.add_argument('--test-ratio', type=float, default=0.15,
                        help='测试集比例 (默认: 0.15)')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子 (默认: 42)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("YOLO 数据集划分工具")
    print("=" * 60)
    print(f"数据集目录: {args.data_dir}")
    print(f"划分比例: {args.train_ratio}:{args.val_ratio}:{args.test_ratio}")
    print("=" * 60)
    
    try:
        # 执行数据集划分
        output_dir = args.output_dir
        if output_dir is None:
            base_name = os.path.basename(os.path.normpath(args.data_dir))
            output_dir = os.path.join(os.path.dirname(args.data_dir), f"{base_name}_split")
        
        stats = split_dataset(
            dataset_root=args.data_dir,
            output_dir=output_dir,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
            seed=args.seed
        )
        
        print("\n" + "=" * 60)
        print("划分结果汇总:")
        print(f"  总文件数: {stats['total']}")
        print(f"  训练集: {stats['train']}")
        print(f"  验证集: {stats['val']}")
        print(f"  测试集: {stats['test']}")
        print("=" * 60)
        print(f"\n✓ 数据集已保存到: {output_dir}")
        print(f"\n请使用数据配置文件进行训练")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 数据集划分失败: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
