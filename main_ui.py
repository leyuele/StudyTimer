import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QFileDialog, QInputDialog, QLineEdit)
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
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 根据设置决定斜体或正体
        is_italic = self.dm.settings.get("slogan_italic", True)
        font_style = "font-style: italic;" if is_italic else "font-style: normal;"

        self.slogan_label = QLabel(self.dm.settings.get("slogan", "保持专注"))
        self.slogan_label.setStyleSheet(f"""
            font-size: 28px; 
            color: #2c3e50; 
            font-family: 'Microsoft YaHei'; 
            {font_style}
            margin-bottom: 30px;
            background-color: rgba(255, 255, 255, 120);
            padding: 10px;
            border-radius: 10px;
        """)
        self.slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slogan_label.setVisible(self.dm.settings.get("show_slogan", True))
        layout.addWidget(self.slogan_label)

        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            font-size: 80px; 
            font-weight: bold; 
            color: #2c3e50; 
            background-color: rgba(255, 255, 255, 180); 
            border-radius: 20px; 
            padding: 40px;
            margin: 20px;
        """)
        layout.addWidget(self.time_label)

        self.status_label = QLabel("准备开始学习...")
        self.status_label.setStyleSheet("font-size: 16px; color: #7f8c8d; margin-top: 10px;")
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始计时")
        self.start_btn.setFixedSize(120, 50)
        self.start_btn.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 25px; font-size: 18px;")
        self.start_btn.clicked.connect(self.toggle_timer)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(120, 50)
        self.stop_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 25px; font-size: 18px;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_timer)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)

    def toggle_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = datetime.now()
            self.timer.start(1000)
            self.start_btn.setText("计时中...")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"开始时间: {self.start_time.strftime('%H:%M:%S')}")
        
    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            end_time = datetime.now()
            
            # 记录时间
            self.dm.add_record(self.start_time, end_time)
            
            self.time_label.setText("00:00:00")
            self.start_btn.setText("开始计时")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText(f"上次学习时长: {str(end_time - self.start_time).split('.')[0]}")
            self.record_added.emit()

    def update_display(self):
        elapsed = datetime.now() - self.start_time
        self.time_label.setText(str(elapsed).split('.')[0])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.setWindowTitle(f"学习时间记录器 v{self.dm.VERSION}")
        self.resize(800, 600)
        self.init_ui()
        self.apply_wallpaper()

    def init_ui(self):
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.timer_page = TimerWidget(self.dm)
        self.central_widget.addWidget(self.timer_page)

        # 导航栏
        nav_bar = self.addToolBar("Navigation")
        nav_bar.setMovable(False)
        
        timer_act = nav_bar.addAction("计时器")
        timer_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(0))
        
        stats_act = nav_bar.addAction("统计分析")
        # stats_act.triggered.connect(...) # 待实现

        settings_act = nav_bar.addAction("设置")
        # settings_act.triggered.connect(...) # 待实现

    def apply_wallpaper(self):
        path = self.dm.settings.get("wallpaper")
        if path and os.path.exists(path):
            palette = QPalette()
            pixmap = QPixmap(path).scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(pixmap))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
