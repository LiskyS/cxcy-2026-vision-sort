"""
YOLOv8 模型推理GUI程序
使用 PySide6 实现
功能：选择模型、选择图片、推理、显示结果、保存结果
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox, QLineEdit,
    QGroupBox, QStatusBar, QSplitter, QFrame, QSizePolicy,
    QScrollArea, QTextEdit, QProgressBar, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QPoint, Slot
from PySide6.QtGui import QPixmap, QImage, QIcon, QFont, QColor, QPainter, QPen
from ultralytics import YOLO


class CameraThread(QThread):
    """摄像头采集线程"""
    frame_ready = Signal(object)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._running = False
        self.cap = None
        
    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._running = True
        
        while self._running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
            self.msleep(30)
        
        self.cap.release()
        self.cap = None
    
    def stop(self):
        self._running = False
        self.wait(3000)


class InferenceThread(QThread):
    """推理线程"""
    finished = Signal(object, object)
    error = Signal(str)
    
    def __init__(self, model_path, image_path, conf_threshold):
        super().__init__()
        self.model_path = model_path
        self.image_path = image_path
        self.conf_threshold = conf_threshold
        
    def run(self):
        try:
            model = YOLO(self.model_path)
            results = model(self.image_path, conf=self.conf_threshold)
            image = cv2.imread(self.image_path)
            self.finished.emit(image, results)
        except Exception as e:
            self.error.emit(str(e))


class CameraInferenceThread(QThread):
    """摄像头实时推理线程"""
    frame_processed = Signal(object, object)
    error = Signal(str)
    finished = Signal()
    
    def __init__(self, model_path, conf_threshold):
        super().__init__()
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self._running = False
        self.current_frame = None
        self.model = None
        
    def run(self):
        try:
            self.model = YOLO(self.model_path)
            self._running = True
            
            while self._running:
                if self.current_frame is not None:
                    results = self.model(self.current_frame, conf=self.conf_threshold, verbose=False)
                    annotated_frame = results[0].plot()
                    self.frame_processed.emit(annotated_frame, results)
                self.msleep(30)
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def set_frame(self, frame):
        self.current_frame = frame
    
    def stop(self):
        self._running = False
        self.wait(3000)


class InferenceGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv8 模型推理系统")
        self.setMinimumSize(1400, 900)
        
        self.current_model = None
        self.current_image = None
        self.current_results = None
        self.current_image_path = None
        self.classes = []
        
        # 摄像头相关
        self.camera_thread = None
        self.camera_inference_thread = None
        self.camera_active = False
        
        # 加载类别文件
        self._load_classes()
        
        self._init_ui()
        self._apply_style()
        
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧：控制面板
        left_panel = self._build_left_panel()
        left_panel.setFixedWidth(280)
        main_layout.addWidget(left_panel)
        
        # 右侧：结果显示
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._set_status("就绪")
        
    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title = QLabel("🎯 YOLOv8 推理系统")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 5px;")
        layout.addWidget(title)
        
        # 模型选择
        model_group = QGroupBox("📁 模型选择")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(5)
        
        self.model_combo = QComboBox()
        self.model_combo.addItem("自动检测")
        self._load_models()
        self.model_combo.currentIndexChanged.connect(self._on_model_selected)
        model_layout.addWidget(QLabel("选择模型："))
        model_layout.addWidget(self.model_combo)
        
        self.model_path_label = QLabel("未选择")
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        model_layout.addWidget(self.model_path_label)
        
        layout.addWidget(model_group)
        
        # 图片选择
        img_group = QGroupBox("📷 图片选择")
        img_layout = QVBoxLayout(img_group)
        img_layout.setSpacing(5)
        
        self.image_combo = QComboBox()
        self.image_combo.addItem("选择图片...")
        self._load_images()
        self.image_combo.currentIndexChanged.connect(self._on_image_selected)
        img_layout.addWidget(QLabel("选择图片："))
        img_layout.addWidget(self.image_combo)
        
        self.btn_browse = QPushButton("📂 浏览...")
        self.btn_browse.setFixedHeight(25)
        self.btn_browse.clicked.connect(self._browse_image)
        img_layout.addWidget(self.btn_browse)
        
        self.image_path_label = QLabel("未选择")
        self.image_path_label.setWordWrap(True)
        self.image_path_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        img_layout.addWidget(self.image_path_label)
        
        layout.addWidget(img_group)
        
        # 摄像头控制
        cam_group = QGroupBox("📹 摄像头控制")
        cam_layout = QVBoxLayout(cam_group)
        cam_layout.setSpacing(5)
        
        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("摄像头："))
        self.cam_index_spin = QSpinBox()
        self.cam_index_spin.setRange(0, 9)
        self.cam_index_spin.setValue(0)
        self.cam_index_spin.setFixedWidth(50)
        cam_row.addWidget(self.cam_index_spin)
        cam_row.addStretch()
        cam_layout.addLayout(cam_row)
        
        self.btn_start_cam = QPushButton("▶ 启动摄像头")
        self.btn_start_cam.setFixedHeight(30)
        self.btn_start_cam.clicked.connect(self._toggle_camera)
        cam_layout.addWidget(self.btn_start_cam)
        
        self.cam_status_label = QLabel("摄像头未启动")
        self.cam_status_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        cam_layout.addWidget(self.cam_status_label)
        
        layout.addWidget(cam_group)
        
        # 推理模式选择
        mode_group = QGroupBox("🎯 推理模式")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(5)
        
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("推理来源："))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["图片文件", "摄像头画面"])
        self.mode_combo.setCurrentText("图片文件")
        self.mode_combo.setFixedWidth(160)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)
        
        layout.addWidget(mode_group)
        
        # 推理参数
        param_group = QGroupBox("⚙️ 推理参数")
        param_layout = QVBoxLayout(param_group)
        param_layout.setSpacing(5)
        
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度："))
        self.conf_spin = QComboBox()
        self.conf_spin.addItems(["0.25", "0.30", "0.40", "0.50", "0.60", "0.70", "0.80", "0.90", "0.95"])
        self.conf_spin.setCurrentText("0.25")
        self.conf_spin.setFixedWidth(160)
        conf_layout.addWidget(self.conf_spin)
        conf_layout.addStretch()
        param_layout.addLayout(conf_layout)
        
        layout.addWidget(param_group)
        
        # 按钮区域
        btn_group = QGroupBox("🚀 操作")
        btn_layout = QVBoxLayout(btn_group)
        btn_layout.setSpacing(6)
        
        self.btn_inference = QPushButton("🔍 开始推理")
        self.btn_inference.setFixedHeight(35)
        self.btn_inference.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.btn_inference.clicked.connect(self._run_inference)
        btn_layout.addWidget(self.btn_inference)
        
        self.btn_stop_inference = QPushButton("⏹ 停止推理")
        self.btn_stop_inference.setFixedHeight(30)
        self.btn_stop_inference.setEnabled(False)
        self.btn_stop_inference.clicked.connect(self._stop_inference)
        btn_layout.addWidget(self.btn_stop_inference)
        
        self.btn_save = QPushButton("💾 保存结果")
        self.btn_save.setFixedHeight(30)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_result)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_exit = QPushButton("❌ 退出程序")
        self.btn_exit.setFixedHeight(30)
        self.btn_exit.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_exit)
        
        layout.addWidget(btn_group)
        
        layout.addStretch()
        
        return panel
    
    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 图片显示区域
        img_view_group = QGroupBox("👁️ 图片预览")
        img_view_layout = QVBoxLayout(img_view_group)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setMaximumHeight(500)
        self.image_label.setStyleSheet("background: #f5f6fa; border-radius: 8px;")
        self.image_label.setText("等待图片...")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("border: none;")
        
        img_view_layout.addWidget(scroll_area)
        layout.addWidget(img_view_group, stretch=1)
        
        # 结果显示区域
        result_group = QGroupBox("📊 推理结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Consolas", 9))
        self.result_text.setMaximumHeight(150)
        self.result_text.setStyleSheet("""
            background: #1e1e2e;
            color: #d4d4d4;
            border-radius: 6px;
            padding: 8px;
        """)
        self.result_text.setText("推理结果将显示在这里...")
        
        result_layout.addWidget(self.result_text)
        layout.addWidget(result_group)
        
        return panel
    
    def _load_models(self):
        """加载模型文件"""
        weights_dir = Path(__file__).parent / "weights"
        if weights_dir.exists():
            for pt_file in weights_dir.glob("*.pt"):
                self.model_combo.addItem(pt_file.name, str(pt_file))
    
    def _load_classes(self):
        """加载类别文件"""
        classes_file = Path(__file__).parent / "classes.txt"
        if classes_file.exists():
            with open(classes_file, 'r', encoding='utf-8') as f:
                self.classes = [line.strip() for line in f if line.strip()]
    
    def _load_images(self):
        """加载图片文件"""
        images_dir = Path(__file__).parent / "images"
        if images_dir.exists():
            for img_file in sorted(images_dir.glob("*.jpg")):
                self.image_combo.addItem(img_file.name, str(img_file))
    
    def _on_model_selected(self, index):
        if index > 0:
            model_path = self.model_combo.itemData(index)
            self.model_path_label.setText(f"✓ {model_path}")
        else:
            self.model_path_label.setText("未选择")
    
    def _on_image_selected(self, index):
        if index > 0:
            img_path = self.image_combo.itemData(index)
            self.image_path_label.setText(f"✓ {img_path}")
            self._display_image(img_path)
        else:
            self.image_path_label.setText("未选择")
    
    def _browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.image_combo.addItem(os.path.basename(file_path), file_path)
            self.image_combo.setCurrentIndex(self.image_combo.count() - 1)
            self.image_path_label.setText(f"✓ {file_path}")
    
    def _display_image(self, image_path):
        """显示图片"""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
        
        scaled_pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.current_image_path = image_path
    
    def _run_inference(self):
        """运行推理"""
        mode = self.mode_combo.currentText()
        
        if mode == "图片文件":
            self._run_image_inference()
        elif mode == "摄像头画面":
            self._run_camera_inference()
    
    def _run_image_inference(self):
        """运行图片文件推理"""
        # 如果摄像头正在运行，先停止
        if self.camera_thread and self.camera_thread.isRunning():
            self._stop_camera()
        
        if not self.current_image_path:
            self._set_status("请先选择图片！", error=True)
            return
        
        # 获取模型路径
        model_index = self.model_combo.currentIndex()
        if model_index > 0:
            model_path = self.model_combo.itemData(model_index)
        else:
            weights_dir = Path(__file__).parent / "weights"
            model_files = list(weights_dir.glob("*.pt"))
            if model_files:
                model_path = str(model_files[0])
            else:
                self._set_status("未找到模型文件", error=True)
                return
        
        conf_threshold = float(self.conf_spin.currentText())
        
        # 禁用按钮
        self.btn_inference.setEnabled(False)
        self.btn_inference.setText("⏳ 推理中...")
        self.btn_stop_inference.setEnabled(True)
        
        # 启动推理线程
        self.inference_thread = InferenceThread(model_path, self.current_image_path, conf_threshold)
        self.inference_thread.finished.connect(self._on_inference_finished)
        self.inference_thread.error.connect(self._on_inference_error)
        self.inference_thread.start()
        
        self._set_status("正在推理图片...")
    
    def _run_camera_inference(self):
        """运行摄像头实时推理"""
        # 检查摄像头是否已启动
        if not self.camera_thread or not self.camera_thread.isRunning():
            self._set_status("请先点击'▶ 启动摄像头'按钮！", error=True)
            return
        
        # 如果实时推理已启动，先停止
        if self.camera_inference_thread and self.camera_inference_thread.isRunning():
            self._stop_camera_inference()
        
        # 获取模型路径
        model_index = self.model_combo.currentIndex()
        if model_index > 0:
            model_path = self.model_combo.itemData(model_index)
        else:
            weights_dir = Path(__file__).parent / "weights"
            model_files = list(weights_dir.glob("*.pt"))
            if model_files:
                model_path = str(model_files[0])
            else:
                self._set_status("未找到模型文件", error=True)
                return
        
        conf_threshold = float(self.conf_spin.currentText())
        
        # 禁用开始推理按钮，启用停止推理按钮
        self.btn_inference.setEnabled(False)
        self.btn_stop_inference.setEnabled(True)
        
        # 启动实时推理线程
        self.camera_inference_thread = CameraInferenceThread(model_path, conf_threshold)
        self.camera_inference_thread.frame_processed.connect(self._on_camera_inference_result)
        self.camera_inference_thread.error.connect(self._on_camera_inference_error)
        self.camera_inference_thread.start()
        
        self._set_status("实时推理已启动")
    
    def _on_inference_finished(self, image, results):
        """推理完成"""
        self.current_results = results
        self.current_image = image
        
        # 显示原始图片
        self._display_image(self.current_image_path)
        
        # 绘制结果
        annotated_frame = results[0].plot()
        self._display_annotated_image(annotated_frame)
        
        # 显示结果文本
        self._display_results_text(results)
        
        # 恢复按钮
        self.btn_inference.setEnabled(True)
        self.btn_inference.setText("🔍 开始推理")
        self.btn_stop_inference.setEnabled(False)
        self.btn_save.setEnabled(True)
        
        self._set_status(f"推理完成，检测到 {len(results[0].boxes)} 个目标")
    
    def _stop_inference(self):
        """停止推理"""
        mode = self.mode_combo.currentText()
        
        if mode == "摄像头画面":
            if self.camera_inference_thread and self.camera_inference_thread.isRunning():
                self._stop_camera_inference()
        
        self.btn_inference.setEnabled(True)
        self.btn_inference.setText("🔍 开始推理")
        self.btn_stop_inference.setEnabled(False)
        self._set_status("推理已停止")
    
    def _on_inference_error(self, error_msg):
        """推理出错"""
        self.btn_inference.setEnabled(True)
        self.btn_inference.setText("🔍 开始推理")
        self._set_status(f"推理失败: {error_msg}", error=True)
    
    def _display_annotated_image(self, annotated_frame):
        """显示带标注的图片"""
        rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        scaled_pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def _display_results_text(self, results):
        """显示结果文本"""
        result = results[0]
        text = "推理结果\n" + "=" * 60 + "\n"
        
        if len(result.boxes) == 0:
            text += "\n未检测到任何目标\n"
        else:
            text += f"{'序号':<6} {'类别':<15} {'置信度':<10} {'边界框'}\n"
            text += "-" * 60 + "\n"
            
            for i, box in enumerate(result.boxes, 1):
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()
                
                class_name = self.classes[class_id] if class_id < len(self.classes) else f"Class {class_id}"
                
                text += f"{i:<6} {class_name:<15} {conf:<10.3f} [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]\n"
        
        text += "=" * 60 + "\n"
        text += f"共检测到 {len(result.boxes)} 个目标\n"
        
        self.result_text.setText(text)
    
    # ──────────── 摄像头控制 ────────────
    def _toggle_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self._stop_camera()
        else:
            self._start_camera()
    
    def _start_camera(self):
        idx = self.cam_index_spin.value()
        self.camera_thread = CameraThread(idx)
        self.camera_thread.frame_ready.connect(self._on_camera_frame)
        self.camera_thread.finished.connect(self._on_camera_stopped)
        self.camera_thread.start()
        self.btn_start_cam.setText("⏹ 停止摄像头")
        self.cam_status_label.setText("摄像头已启动")
        self._set_status(f"摄像头 {idx} 已启动")
    
    def _stop_camera(self):
        if self.camera_inference_thread and self.camera_inference_thread.isRunning():
            self._stop_camera_inference()
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        self.btn_start_cam.setText("▶ 启动摄像头")
        self.cam_status_label.setText("摄像头未启动")
        self.image_label.setText("等待图片...")
        self._set_status("摄像头已停止")
    
    @Slot()
    def _on_camera_stopped(self):
        self.btn_start_cam.setText("▶ 启动摄像头")
    
    @Slot(object)
    def _on_camera_frame(self, frame):
        if self.camera_inference_thread and self.camera_inference_thread.isRunning():
            self.camera_inference_thread.set_frame(frame)
        else:
            self._display_image_from_array(frame)
    
    def _display_image_from_array(self, frame):
        """从numpy数组显示图片"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        scaled_pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def _toggle_camera_inference(self):
        if self.camera_inference_thread and self.camera_inference_thread.isRunning():
            self._stop_camera_inference()
        else:
            self._start_camera_inference()
    
    def _start_camera_inference(self):
        if not self.camera_thread or not self.camera_thread.isRunning():
            self._set_status("请先启动摄像头！", error=True)
            return
        
        model_index = self.model_combo.currentIndex()
        if model_index > 0:
            model_path = self.model_combo.itemData(model_index)
        else:
            weights_dir = Path(__file__).parent / "weights"
            model_files = list(weights_dir.glob("*.pt"))
            if model_files:
                model_path = str(model_files[0])
            else:
                self._set_status("未找到模型文件", error=True)
                return
        
        conf_threshold = float(self.conf_spin.currentText())
        
        self.camera_inference_thread = CameraInferenceThread(model_path, conf_threshold)
        self.camera_inference_thread.frame_processed.connect(self._on_camera_inference_result)
        self.camera_inference_thread.error.connect(self._on_camera_inference_error)
        self.camera_inference_thread.start()
        
        self.btn_start_cam.setText("⏹ 停止实时推理")
        self.cam_status_label.setText("实时推理中...")
        self._set_status("实时推理已启动")
    
    def _stop_camera_inference(self):
        if self.camera_inference_thread:
            self.camera_inference_thread.stop()
            self.camera_inference_thread = None
        # 不改变摄像头按钮状态，只重置推理状态
        self.cam_status_label.setText("摄像头已启动")
        self._set_status("实时推理已停止")
    
    @Slot(object, object)
    def _on_camera_inference_result(self, annotated_frame, results):
        self._display_image_from_array(annotated_frame)
        self._display_results_text(results)
    
    def _on_camera_inference_error(self, error_msg):
        self._set_status(f"实时推理失败: {error_msg}", error=True)
    
    def _save_result(self):
        """保存结果"""
        if self.current_results is None:
            self._set_status("没有可保存的结果", error=True)
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", "Image Files (*.jpg *.png *.bmp)"
        )
        if output_path:
            annotated_frame = self.current_results[0].plot()
            cv2.imwrite(output_path, annotated_frame)
            self._set_status(f"结果已保存到: {output_path}")
    
    def _set_status(self, message, error=False):
        """设置状态栏消息"""
        self.status_bar.showMessage(message, 5000)
        if error:
            self.status_bar.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.status_bar.setStyleSheet("color: #27ae60; font-weight: bold;")
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f6fa;
            }
            QGroupBox {
                font: bold 12px "Microsoft YaHei";
                border: 2px solid #d0d7e3;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #3a3a5c;
            }
            QPushButton {
                background: #4a6fa5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font: 12px "Microsoft YaHei";
            }
            QPushButton:hover {
                background: #3a5f95;
            }
            QPushButton:pressed {
                background: #2a4f85;
            }
            QPushButton:disabled {
                background: #b0b8c8;
                color: #e0e0e0;
            }
            QComboBox {
                border: 2px solid #d0d7e3;
                border-radius: 6px;
                padding: 6px 10px;
                background: #f9fafe;
                min-height: 32px;
            }
            QComboBox:hover {
                border-color: #4a6fa5;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                selection-background-color: #4a6fa5;
            }
            QLineEdit {
                border: 2px solid #d0d7e3;
                border-radius: 6px;
                padding: 6px 10px;
                background: #f9fafe;
            }
            QLineEdit:focus {
                border-color: #4a6fa5;
            }
            QLabel {
                color: #2c2c54;
                font: 12px "Microsoft YaHei";
            }
            QScrollArea {
                background: #f5f6fa;
            }
            QTextEdit {
                background: #1e1e2e;
                color: #d4d4d4;
                border-radius: 6px;
                padding: 10px;
            }
        """)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("YOLOv8 推理系统")
    
    window = InferenceGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
