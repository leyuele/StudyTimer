import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QToolBar, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QAction, QFont, QIcon, QPainter, QColor

from models import DataManager
from main_ui import TimerWidget
from stats_widget import StatsWidget
from settings_widget import SettingsWidget

class TextIcon(QIcon):
    def __init__(self, text, color="#34495e"):
        super().__init__()
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(color))
        font = QFont("Segoe UI Symbol", 28)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        self.addPixmap(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.setWindowTitle(f"StudyTimer v{self.dm.VERSION}")
        self.setMinimumSize(900, 700)
        
        # 确保设置中有透明度选项，默认 100% (1.0)
        if "wallpaper_opacity" not in self.dm.settings:
            self.dm.settings["wallpaper_opacity"] = 100
            
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.timer_page = TimerWidget(self.dm)
        self.central_widget.addWidget(self.timer_page)

        self.stats_page = StatsWidget(self.dm)
        self.central_widget.addWidget(self.stats_page)
        self.timer_page.record_added.connect(self.stats_page.update_charts)

        self.settings_page = SettingsWidget(self.dm, self)
        self.central_widget.addWidget(self.settings_page)

        self.create_nav_bar()

    def create_nav_bar(self):
        nav_bar = QToolBar("Navigation")
        nav_bar.setMovable(False)
        nav_bar.setIconSize(QSize(40, 40))
        nav_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, nav_bar)

        timer_act = QAction(TextIcon("🕒"), "计时器", self)
        timer_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(0))
        nav_bar.addAction(timer_act)

        stats_act = QAction(TextIcon("📊"), "统计分析", self)
        stats_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(1))
        nav_bar.addAction(stats_act)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        nav_bar.addWidget(spacer)

        settings_act = QAction(TextIcon("⚙️"), "设置", self)
        settings_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(2))
        nav_bar.addAction(settings_act)

    def paintEvent(self, event):
        """手动绘制背景，解决黑屏问题并支持透明度"""
        painter = QPainter(self)
        path = self.dm.settings.get("wallpaper")
        
        # 绘制底层底色
        painter.fillRect(self.rect(), QColor("#f5f6fa"))
        
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # 缩放图片以适应窗口
                scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                
                # 设置透明度 (0.0 - 1.0)
                opacity = self.dm.settings.get("wallpaper_opacity", 100) / 100.0
                painter.setOpacity(opacity)
                
                # 居中绘制
                x = (self.width() - scaled_pixmap.width()) // 2
                y = (self.height() - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
                
        painter.end()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QToolBar { background-color: rgba(255, 255, 255, 180); border-right: 1px solid #dcdde1; padding: 10px; min-width: 100px; }
            QToolBar QToolButton { margin-bottom: 20px; border-radius: 12px; padding: 10px; color: #34495e; font-weight: bold; background: transparent; }
            QToolBar QToolButton:hover { background-color: rgba(0, 0, 0, 15); }
            
            /* 为子页面增加一层半透明蒙版，确保在有壁纸时文字依然清晰 */
            TimerWidget, SettingsWidget, StatsWidget { 
                background-color: rgba(255, 255, 255, 160); 
                border-radius: 20px; 
                margin: 15px;
            }
            
            QPushButton { border-radius: 8px; padding: 10px; font-weight: bold; background-color: #ffffff; border: 1px solid #dcdde1; color: #2c3e50; }
            QPushButton:hover { background-color: #f8f9fa; border: 1px solid #3498db; }
            QLineEdit { padding: 8px; border: 1px solid #dcdde1; border-radius: 5px; background: rgba(255, 255, 255, 220); }
            QComboBox { padding: 5px; border: 1px solid #dcdde1; border-radius: 5px; background: rgba(255, 255, 255, 220); }
            QLabel { background: transparent; color: #2c3e50; font-weight: 500; }
            QCheckBox { background: transparent; spacing: 5px; }
        """)

    def update_wallpaper(self):
        """刷新壁纸显示"""
        self.repaint()  # 使用 repaint

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
