import sys
import os
import glob
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QLabel, QTableWidget, QTableWidgetItem, QStatusBar,
    QGridLayout, QComboBox, QFrame, QSizePolicy
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QColor, QPalette, QFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from ultralytics import YOLO

class InferenceThread(QThread):
    progress_updated = Signal(int, str)
    inference_completed = Signal(dict)
    inference_stopped = Signal()
    
    def __init__(self, model, image_paths):
        super().__init__()
        self.model = model
        self.image_paths = image_paths
        self.stopped = False
    
    def run(self):
        results = {}
        total_images = len(self.image_paths)
        
        for i, image_path in enumerate(self.image_paths):
            if self.stopped:
                self.inference_stopped.emit()
                return
            
            self.progress_updated.emit(i + 1, os.path.basename(image_path))
            
            try:
                result = self.model(image_path)
                
                for r in result:
                    for c in r.boxes.cls:
                        class_id = int(c)
                        class_name = self.model.names[class_id]
                        conf = float(r.boxes.conf[0])
                        
                        if class_name not in results:
                            results[class_name] = {
                                'confidences': [],
                                'count': 0
                            }
                        
                        results[class_name]['confidences'].append(conf)
                        results[class_name]['count'] += 1
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
        
        self.inference_completed.emit(results)
    
    def stop(self):
        self.stopped = True

class ConfidenceStatsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("模型置信度统计")
        self.setGeometry(100, 100, 1000, 900)
        self.setMinimumSize(800, 600)
        
        # Set modern light theme with professional look
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 245))
        palette.setColor(QPalette.WindowText, QColor(30, 30, 40))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 250))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(30, 30, 40))
        palette.setColor(QPalette.Text, QColor(30, 30, 40))
        palette.setColor(QPalette.Button, QColor(240, 240, 245))
        palette.setColor(QPalette.ButtonText, QColor(30, 30, 40))
        palette.setColor(QPalette.BrightText, QColor(220, 53, 69))
        palette.setColor(QPalette.Link, QColor(41, 128, 185))
        self.setPalette(palette)
        
        # Set font
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.setFont(font)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(12)
        
        # Control panel with frame
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_frame.setFrameShadow(QFrame.Raised)
        control_frame.setStyleSheet("QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; }")
        
        control_layout = QGridLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(10)
        
        # Model selection
        model_label = QLabel("模型文件:")
        model_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        control_layout.addWidget(model_label, 0, 0)
        
        self.model_path = os.path.join(os.getcwd(), "weights", "best.pt")
        if not os.path.exists(self.model_path):
            weight_files = glob.glob(os.path.join(os.getcwd(), "weights", "*.pt"))
            if weight_files:
                self.model_path = weight_files[0]
        
        self.model_combo = QComboBox()
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_combo.setStyleSheet("QComboBox { padding: 6px; border: 1px solid #ddd; border-radius: 4px; }")
        self.model_combo.currentIndexChanged.connect(self.on_model_combo_changed)
        self.update_model_combo()
        control_layout.addWidget(self.model_combo, 0, 1)
        
        self.model_button = QPushButton("浏览...")
        self.model_button.setStyleSheet("QPushButton { padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5; }")
        self.model_button.clicked.connect(self.browse_model)
        control_layout.addWidget(self.model_button, 0, 2)
        
        # Image directory selection
        image_label = QLabel("图片目录:")
        image_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        control_layout.addWidget(image_label, 1, 0)
        
        self.image_dir = os.path.join(os.getcwd(), "images_10")
        self.image_dir_label = QLabel(self.image_dir)
        self.image_dir_label.setWordWrap(True)
        self.image_dir_label.setStyleSheet("QLabel { border: 1px solid #ddd; border-radius: 4px; padding: 6px; background-color: #f9f9f9; }")
        control_layout.addWidget(self.image_dir_label, 1, 1)
        
        self.image_button = QPushButton("浏览...")
        self.image_button.setStyleSheet("QPushButton { padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5; }")
        self.image_button.clicked.connect(self.browse_images)
        control_layout.addWidget(self.image_button, 1, 2)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.start_button = QPushButton("开始推理")
        self.start_button.setStyleSheet("QPushButton { padding: 8px 16px; border: none; border-radius: 4px; background-color: #3498db; color: white; font-weight: 500; }")
        self.start_button.clicked.connect(self.start_inference)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setStyleSheet("QPushButton { padding: 8px 16px; border: none; border-radius: 4px; background-color: #e74c3c; color: white; font-weight: 500; }")
        self.stop_button.clicked.connect(self.stop_inference)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.export_button = QPushButton("导出结果")
        self.export_button.setStyleSheet("QPushButton { padding: 8px 16px; border: none; border-radius: 4px; background-color: #2ecc71; color: white; font-weight: 500; }")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        self.exit_button = QPushButton("退出")
        self.exit_button.setStyleSheet("QPushButton { padding: 8px 16px; border: none; border-radius: 4px; background-color: #95a5a6; color: white; font-weight: 500; }")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        
        control_layout.addLayout(button_layout, 2, 0, 1, 3)
        
        self.layout.addWidget(control_frame)
        
        # Progress bar section
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_frame.setFrameShadow(QFrame.Raised)
        progress_frame.setStyleSheet("QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; }")
        
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(15, 15, 15, 15)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #ddd; border-radius: 4px; text-align: center; }")
        progress_layout.addWidget(self.progress_bar)
        
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; }")
        progress_layout.addWidget(self.current_file_label)
        
        self.layout.addWidget(progress_frame)
        
        # Results section with frame
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.StyledPanel)
        results_frame.setFrameShadow(QFrame.Raised)
        results_frame.setStyleSheet("QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; }")
        
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(15, 15, 15, 15)
        results_layout.setSpacing(12)
        
        # Results table
        table_label = QLabel("统计结果")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        results_layout.addWidget(table_label)
        
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["类别", "平均置信度", "最大置信度", "检测数量"])
        self.table_widget.setStyleSheet("QTableWidget { border: 1px solid #ddd; border-radius: 4px; }")
        self.table_widget.setMinimumHeight(200)
        results_layout.addWidget(self.table_widget)
        
        # Chart
        chart_label = QLabel("置信度分布")
        chart_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        results_layout.addWidget(chart_label)
        
        self.figure, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)
        
        self.layout.addWidget(results_frame)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Model loading
        self.model = None
        self.load_model()
        
        # Thread
        self.inference_thread = None
        
        # Results
        self.results = {}
    
    def update_model_combo(self):
        self.model_combo.clear()
        weight_files = glob.glob(os.path.join(os.getcwd(), "weights", "*.pt"))
        for file in weight_files:
            self.model_combo.addItem(os.path.basename(file), file)
        
        if weight_files:
            self.model_path = weight_files[0]
    
    def browse_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", os.path.join(os.getcwd(), "weights"), "Model files (*.pt)"
        )
        if file_path:
            self.model_path = file_path
            self.load_model()
    
    def on_model_combo_changed(self, index):
        if index >= 0:
            self.model_path = self.model_combo.itemData(index)
            self.load_model()
    
    def browse_images(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择图片目录", os.path.join(os.getcwd(), "images")
        )
        if directory:
            self.image_dir = directory
            self.image_dir_label.setText(self.image_dir)
    
    def load_model(self):
        self.status_bar.showMessage("正在加载模型...")
        try:
            self.model = YOLO(self.model_path)
            self.status_bar.showMessage(f"模型加载成功: {os.path.basename(self.model_path)}")
        except Exception as e:
            self.status_bar.showMessage(f"模型加载失败: {str(e)}")
    
    def start_inference(self):
        if not self.model:
            self.status_bar.showMessage("请先加载模型")
            return
        
        # Get image paths
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(glob.glob(os.path.join(self.image_dir, ext)))
        
        if not image_paths:
            self.status_bar.showMessage("未找到图片文件")
            return
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        self.progress_bar.setMaximum(len(image_paths))
        self.progress_bar.setValue(0)
        self.current_file_label.setText("")
        
        # Clear previous results
        self.results = {}
        self.table_widget.setRowCount(0)
        self.ax.clear()
        self.canvas.draw()
        
        # Start thread
        self.inference_thread = InferenceThread(self.model, image_paths)
        self.inference_thread.progress_updated.connect(self.update_progress)
        self.inference_thread.inference_completed.connect(self.on_inference_completed)
        self.inference_thread.inference_stopped.connect(self.on_inference_stopped)
        self.inference_thread.start()
    
    def stop_inference(self):
        if self.inference_thread:
            self.inference_thread.stop()
    
    def update_progress(self, progress, current_file):
        self.progress_bar.setValue(progress)
        self.current_file_label.setText(f"正在处理: {current_file}")
    
    def on_inference_completed(self, results):
        self.results = results
        self.display_results()
        self.update_ui_after_inference()
    
    def on_inference_stopped(self):
        self.status_bar.showMessage("推理已停止")
        self.update_ui_after_inference()
    
    def update_ui_after_inference(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(len(self.results) > 0)
    
    def display_results(self):
        # Clear table
        self.table_widget.setRowCount(0)
        
        # Prepare data for chart
        class_names = []
        avg_confidences = []
        
        # Fill table
        for class_name, data in self.results.items():
            avg_conf = sum(data['confidences']) / len(data['confidences'])
            max_conf = max(data['confidences'])
            count = data['count']
            
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            
            self.table_widget.setItem(row_position, 0, QTableWidgetItem(class_name))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem(f"{avg_conf:.4f}"))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem(f"{max_conf:.4f}"))
            self.table_widget.setItem(row_position, 3, QTableWidgetItem(str(count)))
            
            class_names.append(class_name)
            avg_confidences.append(avg_conf)
        
        # Update chart with modern styling
        self.ax.clear()
        
        # Set Chinese font for matplotlib
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文显示
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # Set modern color scheme
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c']
        
        # Create bars with professional styling
        bars = self.ax.bar(class_names, avg_confidences, color=colors[:len(class_names)], 
                          edgecolor='white', linewidth=1.5, alpha=0.8)
        
        # Set labels and title with modern font
        self.ax.set_xlabel('类别', fontsize=11, fontweight='500')
        self.ax.set_ylabel('平均置信度', fontsize=11, fontweight='500')
        self.ax.set_title('各类别平均置信度分布', fontsize=12, fontweight='bold')
        self.ax.set_ylim(0, 1)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.02, f'{height:.3f}',
                        ha='center', va='bottom', fontsize=9, fontweight='500')
        
        # Add grid for better readability
        self.ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Remove top and right spines for cleaner look
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        # Set tick parameters
        self.ax.tick_params(axis='both', which='major', labelsize=10)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.status_bar.showMessage(f"推理完成，共检测到 {len(self.results)} 个类别")
    
    def export_results(self):
        if not self.results:
            return
        
        data = []
        for class_name, result in self.results.items():
            avg_conf = sum(result['confidences']) / len(result['confidences'])
            max_conf = max(result['confidences'])
            min_conf = min(result['confidences'])
            count = result['count']
            
            data.append({
                '类别': class_name,
                '平均置信度': avg_conf,
                '最大置信度': max_conf,
                '最小置信度': min_conf,
                '检测数量': count
            })
        
        df = pd.DataFrame(data)
        
        # 打开文件保存对话框
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", os.path.join(os.getcwd(), "statistics_result.csv"), "CSV files (*.csv)"
        )
        
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            self.status_bar.showMessage(f"结果已导出到: {output_path}")
        else:
            self.status_bar.showMessage("导出已取消")

if __name__ == "__main__":
    # 设置系统编码
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    app = QApplication(sys.argv)
    window = ConfidenceStatsApp()
    window.show()
    sys.exit(app.exec())