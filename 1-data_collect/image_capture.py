"""
图像采集程序
使用 PySide2 + OpenCV 实现
功能：
  1. 选择图像保存目录
  2. 自动图像采集（可设置采集频率，支持启动/停止）
  3. 手动图像采集（点击按钮才保存一帧）
  4. 支持 USB 摄像头
"""

import sys
import os
import cv2
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox,
    QGroupBox, QStatusBar, QSizePolicy, QComboBox, QMessageBox,
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot
from PySide6.QtGui import QImage, QPixmap, QFont, QIcon, QPalette, QColor


# ──────────────────────────────────────────────
#  摄像头采集线程
# ──────────────────────────────────────────────
class CameraThread(QThread):
    """后台线程：持续读取摄像头帧，发出信号给主线程更新预览"""
    frame_ready = Signal(object)   # 传递 numpy ndarray

    def __init__(self, camera_index: int = 0):
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
            self.msleep(30)   # ~33 fps 预览

        self.cap.release()
        self.cap = None

    def stop(self):
        self._running = False
        self.wait(3000)


# ──────────────────────────────────────────────
#  主窗口
# ──────────────────────────────────────────────
class ImageCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像采集系统")
        self.setMinimumSize(1000, 700)

        # 状态变量
        self.save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "captures")
        self.current_frame = None          # 当前帧
        self.auto_capture_active = False   # 自动采集是否运行中
        self.camera_thread = None          # 摄像头线程
        self.auto_timer = QTimer(self)     # 自动采集定时器
        self.auto_timer.timeout.connect(self._auto_capture_frame)
        self.capture_count = 0             # 本次采集张数

        self._build_ui()
        self._apply_style()

    # ──────────── UI 构建 ────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # 左侧：预览区
        root.addWidget(self._build_preview_panel(), stretch=3)

        # 右侧：控制区
        root.addWidget(self._build_control_panel(), stretch=1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._set_status("就绪，请先启动摄像头")

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("📷  实时预览")
        title.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        layout.addWidget(title)

        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.preview_label.setStyleSheet(
            "background:#1a1a2e; border-radius:8px; color:#aaa;"
        )
        self.preview_label.setText("摄像头未启动")
        layout.addWidget(self.preview_label, stretch=1)

        # 摄像头选择 + 启动/停止
        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("摄像头索引："))
        self.cam_index_spin = QSpinBox()
        self.cam_index_spin.setRange(0, 9)
        self.cam_index_spin.setValue(0)
        self.cam_index_spin.setFixedWidth(60)
        cam_row.addWidget(self.cam_index_spin)
        cam_row.addStretch()

        self.btn_start_cam = QPushButton("▶  启动摄像头")
        self.btn_start_cam.setFixedHeight(36)
        self.btn_start_cam.clicked.connect(self._toggle_camera)
        cam_row.addWidget(self.btn_start_cam)
        layout.addLayout(cam_row)

        return panel

    def _build_control_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 保存目录 ──
        dir_group = QGroupBox("📁  保存目录")
        dir_layout = QVBoxLayout(dir_group)

        self.dir_label = QLabel(self.save_dir)
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("color:#555; font-size:11px;")
        dir_layout.addWidget(self.dir_label)

        btn_choose_dir = QPushButton("选择目录")
        btn_choose_dir.clicked.connect(self._choose_save_dir)
        dir_layout.addWidget(btn_choose_dir)
        layout.addWidget(dir_group)

        # ── 自动采集 ──
        auto_group = QGroupBox("🤖  自动采集")
        auto_layout = QGridLayout(auto_group)
        auto_layout.setColumnStretch(1, 1)

        auto_layout.addWidget(QLabel("采集频率（次/秒）："), 0, 0)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 30.0)
        self.freq_spin.setValue(1.0)
        self.freq_spin.setSingleStep(0.5)
        self.freq_spin.setDecimals(1)
        self.freq_spin.setSuffix(" fps")
        auto_layout.addWidget(self.freq_spin, 0, 1)

        self.btn_auto = QPushButton("▶  开始自动采集")
        self.btn_auto.setFixedHeight(40)
        self.btn_auto.clicked.connect(self._toggle_auto_capture)
        auto_layout.addWidget(self.btn_auto, 1, 0, 1, 2)

        self.auto_count_label = QLabel("已采集：0 张")
        self.auto_count_label.setAlignment(Qt.AlignCenter)
        auto_layout.addWidget(self.auto_count_label, 2, 0, 1, 2)
        layout.addWidget(auto_group)

        # ── 手动采集 ──
        manual_group = QGroupBox("🖐  手动采集")
        manual_layout = QVBoxLayout(manual_group)

        info = QLabel("摄像头启动后，点击下方按钮\n手动捕获并保存当前帧。")
        info.setStyleSheet("color:#666; font-size:11px;")
        info.setWordWrap(True)
        manual_layout.addWidget(info)

        self.btn_capture = QPushButton("📸  捕获图像")
        self.btn_capture.setFixedHeight(44)
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self._manual_capture)
        manual_layout.addWidget(self.btn_capture)

        self.manual_count_label = QLabel("已采集：0 张")
        self.manual_count_label.setAlignment(Qt.AlignCenter)
        manual_layout.addWidget(self.manual_count_label)
        layout.addWidget(manual_group)

        # ── 采集统计 ──
        stat_group = QGroupBox("📊  采集统计")
        stat_layout = QVBoxLayout(stat_group)
        self.stat_label = QLabel("自动：0 张\n手动：0 张\n合计：0 张")
        self.stat_label.setAlignment(Qt.AlignCenter)
        stat_layout.addWidget(self.stat_label)

        btn_open_dir = QPushButton("打开保存目录")
        btn_open_dir.clicked.connect(self._open_save_dir)
        stat_layout.addWidget(btn_open_dir)
        layout.addWidget(stat_group)

        layout.addStretch()
        return panel

    # ──────────── 摄像头控制 ────────────
    def _toggle_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        idx = self.cam_index_spin.value()
        self.camera_thread = CameraThread(idx)
        self.camera_thread.frame_ready.connect(self._on_frame)
        self.camera_thread.finished.connect(self._on_camera_stopped)
        self.camera_thread.start()
        self.btn_start_cam.setText("⏹  停止摄像头")
        self.btn_capture.setEnabled(True)
        self._set_status(f"摄像头 {idx} 已启动")

    def _stop_camera(self):
        # 先停止自动采集
        if self.auto_capture_active:
            self._stop_auto_capture()
        if self.camera_thread:
            self.camera_thread.stop()
        self.btn_start_cam.setText("▶  启动摄像头")
        self.btn_capture.setEnabled(False)
        self.preview_label.setText("摄像头已停止")
        self.preview_label.setPixmap(QPixmap())
        self.current_frame = None
        self._set_status("摄像头已停止")

    @Slot()
    def _on_camera_stopped(self):
        self.btn_start_cam.setText("▶  启动摄像头")

    @Slot(object)
    def _on_frame(self, frame):
        """收到新帧 → 更新预览"""
        self.current_frame = frame
        self._update_preview(frame)

    def _update_preview(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(pix)

    # ──────────── 自动采集 ────────────
    def _toggle_auto_capture(self):
        if self.auto_capture_active:
            self._stop_auto_capture()
        else:
            self._start_auto_capture()

    def _start_auto_capture(self):
        if not (self.camera_thread and self.camera_thread.isRunning()):
            QMessageBox.warning(self, "提示", "请先启动摄像头！")
            return
        os.makedirs(self.save_dir, exist_ok=True)
        self.auto_capture_count = 0
        interval_ms = int(1000 / self.freq_spin.value())
        self.auto_timer.start(interval_ms)
        self.auto_capture_active = True
        self.btn_auto.setText("⏹  停止自动采集")
        self.freq_spin.setEnabled(False)
        self._set_status(f"自动采集已启动，频率 {self.freq_spin.value()} fps")

    def _stop_auto_capture(self):
        self.auto_timer.stop()
        self.auto_capture_active = False
        self.btn_auto.setText("▶  开始自动采集")
        self.freq_spin.setEnabled(True)
        self._set_status(f"自动采集已停止，共采集 {self.auto_capture_count} 张")

    def _auto_capture_frame(self):
        if self.current_frame is not None:
            path = self._save_frame(self.current_frame, prefix="auto")
            self.auto_capture_count += 1
            self.auto_count_label.setText(f"已采集：{self.auto_capture_count} 张")
            self._update_stats()
            self._set_status(f"自动采集 → {os.path.basename(path)}")

    # ──────────── 手动采集 ────────────
    def _manual_capture(self):
        if self.current_frame is None:
            QMessageBox.warning(self, "提示", "摄像头未就绪，请先启动摄像头！")
            return
        os.makedirs(self.save_dir, exist_ok=True)
        path = self._save_frame(self.current_frame, prefix="manual")
        if not hasattr(self, "manual_capture_count"):
            self.manual_capture_count = 0
        self.manual_capture_count += 1
        self.manual_count_label.setText(f"已采集：{self.manual_capture_count} 张")
        self._update_stats()
        self._set_status(f"手动采集 → {os.path.basename(path)}")

    # ──────────── 工具方法 ────────────
    def _save_frame(self, frame, prefix: str = "img") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{prefix}_{ts}.jpg"
        path = os.path.join(self.save_dir, filename)
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return path

    def _choose_save_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "选择图像保存目录", self.save_dir
        )
        if d:
            self.save_dir = d
            self.dir_label.setText(d)
            self._set_status(f"保存目录已更改：{d}")

    def _open_save_dir(self):
        os.makedirs(self.save_dir, exist_ok=True)
        os.startfile(self.save_dir)

    def _set_status(self, msg: str):
        self.status_bar.showMessage(f"[{datetime.now().strftime('%H:%M:%S')}]  {msg}")

    def _update_stats(self):
        a = getattr(self, "auto_capture_count", 0)
        m = getattr(self, "manual_capture_count", 0)
        self.stat_label.setText(f"自动：{a} 张\n手动：{m} 张\n合计：{a + m} 张")

    # ──────────── 样式 ────────────
    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #f5f6fa; }
            QGroupBox {
                font: bold 12px "Microsoft YaHei";
                border: 1.5px solid #d0d7e3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 8px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #3a3a5c;
            }
            QPushButton {
                background: #4a6fa5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font: 12px "Microsoft YaHei";
            }
            QPushButton:hover { background: #3a5f95; }
            QPushButton:pressed { background: #2a4f85; }
            QPushButton:disabled { background: #b0b8c8; color: #e0e0e0; }
            QPushButton#btn_capture {
                background: #27ae60;
                font: bold 14px "Microsoft YaHei";
            }
            QPushButton#btn_capture:hover { background: #219a52; }
            QPushButton#btn_capture:disabled { background: #b0b8c8; }
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #c0c8d8;
                border-radius: 4px;
                padding: 3px 6px;
                background: #f9fafe;
            }
            QStatusBar { background: #eef0f6; font-size: 11px; color: #555; }
            QLabel { color: #2c2c54; font: 12px "Microsoft YaHei"; }
        """)
        self.btn_capture.setObjectName("btn_capture")

    # ──────────── 关闭事件 ────────────
    def closeEvent(self, event):
        if self.auto_capture_active:
            self._stop_auto_capture()
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
        event.accept()


# ──────────────────────────────────────────────
#  入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("图像采集系统")
    win = ImageCaptureApp()
    win.show()
    sys.exit(app.exec())
