import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFileDialog, QInputDialog, QLineEdit, QComboBox)
from PyQt6.QtCore import QTimer, Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QFont
from datetime import datetime
from models import DataManager


class TimerWidget(QWidget):
    record_added = pyqtSignal()

    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.is_running = False
        self.start_time = None
        self.init_ui()

    def init_ui(self):
        # 主布局居中对齐
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(10)

        # 1. 标语部分 (恢复斜体，极简背景)
        self.slogan_label = QLabel(self.dm.settings.get("slogan", "保持专注"))
        self.slogan_label.setStyleSheet("""
            font-size: 24px; 
            color: #2c3e50; 
            font-family: 'Microsoft YaHei'; 
            font-style: italic;
            margin-bottom: 40px;
            background-color: rgba(255, 255, 255, 60);
            padding: 8px 20px;
            border-radius: 15px;
        """)
        self.slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slogan_label.setVisible(self.dm.settings.get("show_slogan", True))
        main_layout.addWidget(self.slogan_label)

        # 2. 核心计时显示 (占据视觉中心)
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            font-size: 110px; 
            font-weight: bold; 
            color: #2c3e50; 
            background-color: rgba(255, 255, 255, 120); 
            border-radius: 30px; 
            padding: 20px 60px;
            margin: 10px;
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label)

        # 3. 极简透明标签选择器
        tag_container = QHBoxLayout()
        tag_container.addStretch()

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(120)
        self.tag_combo.setMinimumHeight(30)
        # 极简透明样式：无边框感，仅保留淡文字和底线
        self.tag_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                color: #34495e;
                font-weight: 500;
                padding: 2px 10px;
                border: none;
                border-bottom: 1px solid rgba(52, 152, 219, 100);
                background-color: rgba(255, 255, 255, 40);
                border-radius: 0px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #3498db;
                border: 1px solid #dcdde1;
            }
        """)
        self.refresh_tags()
        tag_container.addWidget(self.tag_combo)
        tag_container.addStretch()
        main_layout.addLayout(tag_container)

        # 4. 状态提示
        self.status_label = QLabel("准备开始计时...")
        self.status_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-top: 20px; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 5. 操作按钮 (圆润、现代)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.start_btn = QPushButton("开始计时")
        self.start_btn.setFixedSize(160, 55)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; 
                color: white; 
                border-radius: 27px; 
                font-size: 18px; 
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.start_btn.clicked.connect(self.toggle_timer)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(160, 55)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                border-radius: 27px; 
                font-size: 18px; 
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_timer)

        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()

        main_layout.addSpacing(30)
        main_layout.addLayout(btn_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)

    def refresh_tags(self):
        current_text = self.tag_combo.currentText()
        self.tag_combo.clear()
        tags = self.dm.settings.get("tags", ["Study", "Game", "Rest", "Work"])
        self.tag_combo.addItems(tags)
        if current_text in tags:
            self.tag_combo.setCurrentText(current_text)

    def toggle_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = datetime.now()
            self.timer.start(1000)
            self.start_btn.setText("计时中...")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.tag_combo.setEnabled(False)
            self.status_label.setText(f"当前活动: {self.tag_combo.currentText()}")

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            end_time = datetime.now()

            # 记录时间
            self.dm.add_record(self.start_time, end_time, self.tag_combo.currentText())

            self.time_label.setText("00:00:00")
            self.start_btn.setText("开始计时")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.tag_combo.setEnabled(True)
            duration = str(end_time - self.start_time).split('.')[0]
            self.status_label.setText(f"本次时长: {duration}")
            self.record_added.emit()

    def update_display(self):
        elapsed = datetime.now() - self.start_time
        self.time_label.setText(str(elapsed).split('.')[0])