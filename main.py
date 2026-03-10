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

        # 性能优化：二级缓存机制
        self._cached_wallpaper_path = None
        self._cached_original_pixmap = None  # 内存原图缓存
        self._cached_scaled_pixmap = None  # 内存缩放图缓存
        self._last_paint_size = QSize()  # 上次渲染的尺寸

        if "wallpaper_opacity" not in self.dm.settings:
            self.dm.settings["wallpaper_opacity"] = 100

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # 计时器页面
        self.timer_page = TimerWidget(self.dm)
        self.central_widget.addWidget(self.timer_page)

        # 统计分析页面
        self.stats_page = StatsWidget(self.dm)
        self.central_widget.addWidget(self.stats_page)
        self.timer_page.record_added.connect(self.stats_page.update_charts)

        # 今日统计页面
        from today_widget import TodayWidget
        self.today_page = TodayWidget(self.dm)
        self.central_widget.addWidget(self.today_page)
        self.timer_page.record_added.connect(self.today_page.update_today_stats)

        # 设置页面
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

        today_act = QAction(TextIcon("📅"), "今日", self)
        today_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(2))
        nav_bar.addAction(today_act)

        stats_act = QAction(TextIcon("📊"), "统计分析", self)
        stats_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(1))
        nav_bar.addAction(stats_act)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        nav_bar.addWidget(spacer)

        settings_act = QAction(TextIcon("⚙️"), "设置", self)
        settings_act.triggered.connect(lambda: self.central_widget.setCurrentIndex(3))
        nav_bar.addAction(settings_act)

    def paintEvent(self, event):
        """优化后的高性能背景绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. 绘制底色
        painter.fillRect(self.rect(), QColor("#f5f6fa"))

        path = self.dm.settings.get("wallpaper")
        if path and os.path.exists(path):
            # 只有路径变化才从磁盘重新加载原图
            if path != self._cached_wallpaper_path or self._cached_original_pixmap is None:
                self._cached_original_pixmap = QPixmap(path)
                self._cached_wallpaper_path = path
                self._cached_scaled_pixmap = None  # 路径变了，缩放缓存失效

            if self._cached_original_pixmap and not self._cached_original_pixmap.isNull():
                # 只有窗口大小变化才重新执行缩放（最耗性能的操作）
                if self.size() != self._last_paint_size or self._cached_scaled_pixmap is None:
                    self._cached_scaled_pixmap = self._cached_original_pixmap.scaled(
                        self.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._last_paint_size = self.size()

                # 直接绘制缩放好的内存位图，极速切换
                opacity = self.dm.settings.get("wallpaper_opacity", 100) / 100.0
                painter.setOpacity(opacity)

                x = (self.width() - self._cached_scaled_pixmap.width()) // 2
                y = (self.height() - self._cached_scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, self._cached_scaled_pixmap)

        painter.end()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QToolBar { background-color: rgba(255, 255, 255, 180); border-right: 1px solid #dcdde1; padding: 10px; min-width: 100px; }
            QToolBar QToolButton { margin-bottom: 20px; border-radius: 12px; padding: 10px; color: #34495e; font-weight: bold; background: transparent; }
            QToolBar QToolButton:hover { background-color: rgba(0, 0, 0, 15); }

            TimerWidget, SettingsWidget, StatsWidget, TodayWidget { 
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
        """强制清除缓存并刷新壁纸显示"""
        self._cached_wallpaper_path = None
        self._cached_original_pixmap = None
        self._cached_scaled_pixmap = None
        self.update()  # 触发 paintEvent 重新加载图片


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())