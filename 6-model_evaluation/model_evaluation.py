import sys
import os
import csv
from pathlib import Path
from datetime import datetime

import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

try:
    from ultralytics import YOLO
except ImportError:
    print("请安装ultralytics: pip install ultralytics")
    sys.exit(1)


class EvaluationWorker(QThread):
    """模型评估工作线程"""
    progress_signal = Signal(int, str)
    finished_signal = Signal(dict, list)
    error_signal = Signal(str)

    def __init__(self, model_path, image_dir, label_dir, classes, conf_threshold=0.25, iou_threshold=0.5):
        super().__init__()
        self.model_path = model_path
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.classes = classes
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

    def run(self):
        try:
            self.progress_signal.emit(0, "正在加载模型...")
            model = YOLO(self.model_path)

            image_files = sorted([
                f for f in os.listdir(self.image_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
            ])

            total_images = len(image_files)
            if total_images == 0:
                self.error_signal.emit("未在选定目录中找到图片文件")
                return

            all_predictions = []
            all_ground_truths = []

            for idx, image_file in enumerate(image_files):
                progress = int((idx / total_images) * 100)
                self.progress_signal.emit(progress, f"正在处理 {image_file} ({idx + 1}/{total_images})")

                image_path = os.path.join(self.image_dir, image_file)
                label_file = os.path.splitext(image_file)[0] + '.txt'
                label_path = os.path.join(self.label_dir, label_file)

                results = model.predict(
                    source=image_path,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False
                )

                predictions = self.parse_predictions(results[0], image_path)
                all_predictions.append(predictions)

                ground_truth = self.parse_ground_truth(label_path)
                all_ground_truths.append(ground_truth)

            self.progress_signal.emit(100, "正在计算评估指标...")

            metrics = self.calculate_metrics(all_predictions, all_ground_truths, len(self.classes))

            per_class_results = []
            for class_idx, class_name in enumerate(self.classes):
                if class_idx in metrics['per_class']:
                    class_metrics = metrics['per_class'][class_idx]
                    per_class_results.append({
                        'class_name': class_name,
                        'precision': class_metrics['precision'],
                        'recall': class_metrics['recall'],
                        'ap': class_metrics['ap'],
                        'f1': class_metrics['f1'],
                        'avg_confidence': class_metrics.get('avg_confidence', 0.0)
                    })

            self.finished_signal.emit(metrics, per_class_results)

        except Exception as e:
            self.error_signal.emit(f"评估过程中出错: {str(e)}")

    def parse_predictions(self, result, image_path):
        """解析YOLO预测结果并转换为归一化坐标"""
        predictions = []
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size

            for box, cls, conf in zip(boxes, classes, confidences):
                x1_norm = float(box[0]) / img_width
                y1_norm = float(box[1]) / img_height
                x2_norm = float(box[2]) / img_width
                y2_norm = float(box[3]) / img_height
                
                predictions.append({
                    'class': int(cls),
                    'confidence': float(conf),
                    'bbox': [x1_norm, y1_norm, x2_norm, y2_norm]
                })
        return predictions

    def parse_ground_truth(self, label_path):
        """解析YOLO格式的真实标签"""
        ground_truth = []
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        x1 = x_center - width / 2
                        y1 = y_center - height / 2
                        x2 = x_center + width / 2
                        y2 = y_center + height / 2
                        
                        ground_truth.append({
                            'class': class_id,
                            'bbox': [x1, y1, x2, y2]
                        })
        return ground_truth

    def calculate_iou(self, box1, box2):
        """计算交并比(IoU)"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def calculate_metrics(self, all_predictions, all_ground_truths, num_classes):
        """计算精确率、召回率、AP、mAP和F1分数"""
        all_detections = []
        all_gt_boxes = []
        
        for img_idx, (predictions, ground_truth) in enumerate(zip(all_predictions, all_ground_truths)):
            for pred in predictions:
                all_detections.append({
                    'class': pred['class'],
                    'confidence': pred['confidence'],
                    'bbox': pred['bbox'],
                    'image_idx': img_idx
                })
            
            for gt in ground_truth:
                all_gt_boxes.append({
                    'class': gt['class'],
                    'bbox': gt['bbox'],
                    'image_idx': img_idx,
                    'matched': False
                })
        
        all_detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        per_class_metrics = {}
        aps = []
        
        for class_idx in range(num_classes):
            class_detections = [d for d in all_detections if d['class'] == class_idx]
            class_gt = [g for g in all_gt_boxes if g['class'] == class_idx]
            
            total_gt = len(class_gt)
            
            if total_gt == 0 and len(class_detections) == 0:
                per_class_metrics[class_idx] = {
                    'precision': 0, 'recall': 0, 'ap': 0, 'f1': 0,
                    'tp': 0, 'fp': 0, 'fn': 0, 'avg_confidence': 0.0
                }
                aps.append(0)
                continue
            
            tp_fp_labels = []
            confidences = []
            
            for det in class_detections:
                best_iou = 0
                best_gt_idx = -1
                
                for gt_idx, gt in enumerate(class_gt):
                    if gt['matched']:
                        continue
                    
                    iou = self.calculate_iou(det['bbox'], gt['bbox'])
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = gt_idx
                
                if best_iou >= 0.5 and best_gt_idx >= 0:
                    tp_fp_labels.append(1)
                    class_gt[best_gt_idx]['matched'] = True
                else:
                    tp_fp_labels.append(0)
                
                confidences.append(det['confidence'])
            
            tp_cumsum = np.cumsum(tp_fp_labels)
            fp_cumsum = np.cumsum(1 - np.array(tp_fp_labels))
            
            precisions = tp_cumsum / (tp_cumsum + fp_cumsum)
            recalls = tp_cumsum / total_gt if total_gt > 0 else np.zeros_like(tp_cumsum)
            
            ap = self.calculate_ap_11point(precisions, recalls)
            aps.append(ap)
            
            tp_count = int(tp_cumsum[-1]) if len(tp_cumsum) > 0 else 0
            fp_count = len(class_detections) - tp_count
            fn_count = total_gt - tp_count
            
            precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
            recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            avg_confidence = np.mean(confidences) if len(confidences) > 0 else 0.0
            
            per_class_metrics[class_idx] = {
                'precision': precision, 'recall': recall, 'ap': ap, 'f1': f1,
                'tp': tp_count, 'fp': fp_count, 'fn': fn_count,
                'avg_confidence': avg_confidence
            }

        map_score = np.mean(aps) if aps else 0

        total_tp = sum(m['tp'] for m in per_class_metrics.values())
        total_fp = sum(m['fp'] for m in per_class_metrics.values())
        total_fn = sum(m['fn'] for m in per_class_metrics.values())
        
        all_confidences = []
        for m in per_class_metrics.values():
            if m['avg_confidence'] > 0:
                all_confidences.append(m['avg_confidence'])
        overall_avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

        return {
            'per_class': per_class_metrics,
            'mAP': map_score,
            'overall_precision': overall_precision,
            'overall_recall': overall_recall,
            'overall_f1': overall_f1,
            'overall_avg_confidence': overall_avg_confidence,
            'total_tp': total_tp,
            'total_fp': total_fp,
            'total_fn': total_fn
        }

    def calculate_ap_11point(self, precisions, recalls):
        """使用11点插值法计算AP"""
        if len(precisions) == 0 or len(recalls) == 0:
            return 0.0
        
        precisions = np.concatenate([[0], precisions, [0]])
        recalls = np.concatenate([[0], recalls, [1]])
        
        for i in range(len(precisions) - 2, -1, -1):
            precisions[i] = max(precisions[i], precisions[i + 1])
        
        ap = 0.0
        for t in np.arange(0, 1.1, 0.1):
            indices = np.where(recalls >= t)[0]
            if len(indices) > 0:
                ap += precisions[indices[0]]
        
        ap /= 11.0
        return ap


class ModelEvaluationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model_path = ""
        
        script_dir = os.path.dirname(__file__)
        default_dataset_dir = os.path.join(script_dir, "datasets_100")
        self.image_dir = os.path.join(default_dataset_dir, "images")
        self.label_dir = os.path.join(default_dataset_dir, "labels")
        
        self.classes = []
        self.evaluation_results = None
        self.per_class_results = []
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("YOLO 模型评估系统")
        self.setGeometry(100, 100, 1200, 950)
        
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("🎯 YOLO 模型评估系统")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 配置区域
        config_group = QGroupBox("⚙️ 配置设置")
        config_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #3498db; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #3498db; }")
        config_layout = QFormLayout()
        
        # 模型选择
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.setStyleSheet("QComboBox { padding: 6px; border: 2px solid #bdc3c7; border-radius: 5px; background-color: white; } QComboBox:hover { border: 2px solid #3498db; }")
        self.model_combo.currentIndexChanged.connect(self.on_model_selected)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_models)
        refresh_btn.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; border: none; padding: 8px 15px; border-radius: 5px; }")
        
        browse_btn = QPushButton("📁 浏览...")
        browse_btn.clicked.connect(self.select_model)
        browse_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; }")
        
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(refresh_btn)
        model_layout.addWidget(browse_btn)
        config_layout.addRow("模型：", model_layout)
        
        self.refresh_models()
        
        # 图片目录
        image_layout = QHBoxLayout()
        self.image_label = QLabel("未选择图片目录")
        select_image_btn = QPushButton("📂 选择图片目录")
        select_image_btn.clicked.connect(self.select_image_dir)
        select_image_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; }")
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(select_image_btn)
        config_layout.addRow("图片目录：", image_layout)
        
        # 标签目录
        label_layout = QHBoxLayout()
        self.label_label = QLabel("未选择标签目录")
        select_label_btn = QPushButton("📂 选择标签目录")
        select_label_btn.clicked.connect(self.select_label_dir)
        select_label_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; }")
        label_layout.addWidget(self.label_label)
        label_layout.addWidget(select_label_btn)
        config_layout.addRow("标签目录：", label_layout)
        
        # 置信度阈值
        conf_layout = QHBoxLayout()
        self.conf_spinbox = QDoubleSpinBox()
        self.conf_spinbox.setRange(0.01, 1.0)
        self.conf_spinbox.setValue(0.25)
        self.conf_spinbox.setSingleStep(0.05)
        conf_layout.addWidget(self.conf_spinbox)
        conf_layout.addWidget(QLabel("（0.01-1.0）"))
        config_layout.addRow("置信度阈值：", conf_layout)
        
        # IOU阈值
        iou_layout = QHBoxLayout()
        self.iou_spinbox = QDoubleSpinBox()
        self.iou_spinbox.setRange(0.01, 1.0)
        self.iou_spinbox.setValue(0.5)
        self.iou_spinbox.setSingleStep(0.05)
        iou_layout.addWidget(self.iou_spinbox)
        iou_layout.addWidget(QLabel("（0.01-1.0）"))
        config_layout.addRow("IOU 阈值：", iou_layout)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 开始评估")
        self.start_btn.clicked.connect(self.start_evaluation)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; border: none; padding: 12px 25px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #229954; } QPushButton:disabled { background-color: #95a5a6; }")
        
        self.export_btn = QPushButton("📊 导出结果")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; padding: 12px 25px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #e67e22; } QPushButton:disabled { background-color: #95a5a6; }")
        
        exit_btn = QPushButton("❌ 退出程序")
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; padding: 12px 25px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addStretch()
        control_layout.addWidget(exit_btn)
        main_layout.addLayout(control_layout)
        
        # 进度区域
        progress_group = QGroupBox("📈 评估进度")
        progress_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #9b59b6; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #9b59b6; }")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid #9b59b6; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #9b59b6; }")
        
        self.status_label = QLabel("就绪，等待开始评估")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 结果显示
        splitter = QSplitter(Qt.Vertical)
        
        metrics_group = QGroupBox("📊 总体评估指标")
        metrics_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #1abc9c; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #1abc9c; }")
        metrics_layout = QVBoxLayout()
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setFont(QFont("Consolas", 10))
        self.metrics_text.setMinimumHeight(200)
        self.metrics_text.setStyleSheet("QTextEdit { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }")
        self.metrics_text.setPlaceholderText("评估结果将显示在这里...")
        
        metrics_layout.addWidget(self.metrics_text)
        metrics_group.setLayout(metrics_layout)
        
        table_group = QGroupBox("📋 各类别详细指标")
        table_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e67e22; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #e67e22; }")
        table_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["类别名称 (Class)", "精确率 (Precision)", "召回率 (Recall)", "平均精度 (AP)", "F1 分数 (F1 Score)", "平均置信度 (Avg Confidence)"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.results_table)
        table_group.setLayout(table_layout)
        
        splitter.addWidget(metrics_group)
        splitter.addWidget(table_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        self.update_default_directories()
    
    def refresh_models(self):
        self.model_combo.clear()
        weights_dir = os.path.join(os.path.dirname(__file__), "weights")
        
        if os.path.exists(weights_dir):
            model_files = sorted([f for f in os.listdir(weights_dir) if f.endswith('.pt')])
            if model_files:
                for model_file in model_files:
                    full_path = os.path.join(weights_dir, model_file)
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    self.model_combo.addItem(f"{model_file} ({size_mb:.1f} MB)", full_path)
                self.model_combo.setCurrentIndex(0)
            else:
                self.model_combo.addItem("未在 weights/ 目录中找到模型")
        else:
            self.model_combo.addItem("未找到 weights/ 目录")
    
    def on_model_selected(self, index):
        if index >= 0:
            model_path = self.model_combo.itemData(index)
            if model_path and os.path.exists(model_path):
                self.model_path = model_path
                if hasattr(self, 'start_btn'):
                    self.check_ready_state()
    
    def update_default_directories(self):
        if os.path.exists(self.image_dir):
            self.image_label.setText(self.image_dir)
            self.image_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.image_label.setText("未选择图片目录")
            self.image_label.setStyleSheet("color: #7f8c8d;")
        
        if os.path.exists(self.label_dir):
            self.label_label.setText(self.label_dir)
            self.label_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.label_label.setText("未选择标签目录")
            self.label_label.setStyleSheet("color: #7f8c8d;")
        
        self.check_ready_state()
    
    def select_model(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择模型文件", os.path.join(os.path.dirname(__file__), "weights"), "PyTorch 模型 (*.pt)")
        if file_path:
            self.model_path = file_path
            found = False
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == file_path:
                    self.model_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                self.model_combo.addItem(f"{os.path.basename(file_path)} ({size_mb:.1f} MB) [自定义]", file_path)
                self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
            self.check_ready_state()
    
    def select_image_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择图片目录")
        if dir_path:
            self.image_dir = dir_path
            self.image_label.setText(dir_path)
            self.image_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            parent_dir = os.path.dirname(dir_path)
            potential_label_dir = os.path.join(parent_dir, "labels")
            if os.path.exists(potential_label_dir):
                self.label_dir = potential_label_dir
                self.label_label.setText(potential_label_dir)
                self.label_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.check_ready_state()
    
    def select_label_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择标签目录")
        if dir_path:
            self.label_dir = dir_path
            self.label_label.setText(dir_path)
            self.label_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.check_ready_state()
    
    def check_ready_state(self):
        ready = (self.model_path and os.path.exists(self.model_path) and
                self.image_dir and os.path.exists(self.image_dir) and
                self.label_dir and os.path.exists(self.label_dir))
        self.start_btn.setEnabled(ready)
    
    def load_classes(self):
        classes_file = os.path.join(os.path.dirname(__file__), "classes.txt")
        if os.path.exists(classes_file):
            with open(classes_file, 'r') as f:
                self.classes = [line.strip() for line in f if line.strip()]
        else:
            self.classes = ["class_0", "class_1", "class_2"]
    
    def start_evaluation(self):
        if not self.model_path or not self.image_dir or not self.label_dir:
            QMessageBox.warning(self, "警告", "请先选择模型、图片目录和标签目录！")
            return
        
        self.load_classes()
        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        conf_threshold = self.conf_spinbox.value()
        iou_threshold = self.iou_spinbox.value()
        
        self.worker = EvaluationWorker(self.model_path, self.image_dir, self.label_dir, self.classes, conf_threshold, iou_threshold)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.evaluation_finished)
        self.worker.error_signal.connect(self.evaluation_error)
        self.worker.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def evaluation_finished(self, metrics, per_class_results):
        self.evaluation_results = metrics
        self.per_class_results = per_class_results
        self.display_metrics(metrics)
        self.display_per_class_results(per_class_results)
        self.export_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.status_label.setText("✅ 评估完成！")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")
        QMessageBox.information(self, "成功", "模型评估已成功完成！")
    
    def evaluation_error(self, error_message):
        self.start_btn.setEnabled(True)
        self.status_label.setText(f"❌ 错误：{error_message}")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
        QMessageBox.critical(self, "错误", error_message)
    
    def display_metrics(self, metrics):
        debug_info = ""
        for class_idx, class_data in metrics['per_class'].items():
            class_name = self.classes[class_idx] if len(self.classes) > class_idx else f"类别 {class_idx}"
            debug_info += f"\n   {class_name}: TP={class_data['tp']}, FP={class_data['fp']}, FN={class_data['fn']}"
        
        text = f"""
╔══════════════════════════════════════════════════╗
║              模型评估结果                        ║
╚══════════════════════════════════════════════════╝

📊 总体性能指标：
   • 精确率 (Precision):     {metrics['overall_precision']:.4f}
   • 召回率 (Recall):        {metrics['overall_recall']:.4f}
   • F1 分数 (F1 Score):     {metrics['overall_f1']:.4f}
   • 平均精度 (mAP):         {metrics['mAP']:.4f}
   • 平均置信度 (Avg Conf):  {metrics['overall_avg_confidence']:.4f}

📈 检测统计信息：
   • 真正例 (TP):  {metrics['total_tp']}
   • 假正例 (FP): {metrics['total_fp']}
   • 假负例 (FN): {metrics['total_fn']}

🔍 各类别详细信息：{debug_info}

⏱️  评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.metrics_text.setText(text)
    
    def display_per_class_results(self, per_class_results):
        self.results_table.setRowCount(len(per_class_results))
        
        for row, result in enumerate(per_class_results):
            self.results_table.setItem(row, 0, QTableWidgetItem(result['class_name']))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{result['precision']:.4f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{result['recall']:.4f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result['ap']:.4f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{result['f1']:.4f}"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{result['avg_confidence']:.4f}"))
            
            for col in range(6):
                item = self.results_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
    
    def export_results(self):
        if not self.evaluation_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "导出评估结果", "", "CSV 文件 (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['指标名称', '数值'])
                    writer.writerow(['=== 总体评估指标 ===', ''])
                    writer.writerow(['精确率 (Precision)', f"{self.evaluation_results['overall_precision']:.4f}"])
                    writer.writerow(['召回率 (Recall)', f"{self.evaluation_results['overall_recall']:.4f}"])
                    writer.writerow(['F1 分数 (F1 Score)', f"{self.evaluation_results['overall_f1']:.4f}"])
                    writer.writerow(['平均精度 (mAP)', f"{self.evaluation_results['mAP']:.4f}"])
                    writer.writerow(['平均置信度 (Avg Confidence)', f"{self.evaluation_results['overall_avg_confidence']:.4f}"])
                    writer.writerow(['真正例 (TP)', self.evaluation_results['total_tp']])
                    writer.writerow(['假正例 (FP)', self.evaluation_results['total_fp']])
                    writer.writerow(['假负例 (FN)', self.evaluation_results['total_fn']])
                    writer.writerow(['', ''])
                    
                    writer.writerow(['=== 各类别详细指标 ===', ''])
                    writer.writerow(['类别名称', '精确率', '召回率', '平均精度(AP)', 'F1 分数', '平均置信度'])
                    
                    for result in self.per_class_results:
                        writer.writerow([
                            result['class_name'],
                            f"{result['precision']:.4f}",
                            f"{result['recall']:.4f}",
                            f"{result['ap']:.4f}",
                            f"{result['f1']:.4f}",
                            f"{result['avg_confidence']:.4f}"
                        ])
                
                QMessageBox.information(self, "成功", f"结果已导出到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    from PySide6.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)
    
    window = ModelEvaluationWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
