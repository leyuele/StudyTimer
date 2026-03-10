import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QPushButton, QStackedWidget, QGridLayout,
                             QScrollArea, QFrame, QSizePolicy, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def to_rgba(color_str, alpha=1.0):
    if isinstance(color_str, tuple):
        return color_str
    if color_str.startswith('#'):
        r = int(color_str[1:3], 16) / 255.0
        g = int(color_str[3:5], 16) / 255.0
        b = int(color_str[5:7], 16) / 255.0
        return (r, g, b, alpha)
    return color_str


class HourDetailDialog(QWidget):
    def __init__(self, hour, records, target_date, parent=None):
        super().__init__(parent)
        self.hour = hour
        self.records = records
        self.target_date = target_date
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title_container = QWidget()
        title_container.setStyleSheet("background-color: rgba(255, 255, 255, 180); border-radius: 15px; padding: 10px;")
        title_layout = QVBoxLayout(title_container)

        date_str = self.target_date.strftime("%m月%d日")
        title = QLabel(f"{date_str} {self.hour:02d}:00 - {self.hour:02d}:59 详细分布")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        layout.addWidget(title_container)

        back_btn = QPushButton("← 返回 24小时视图")
        back_btn.setStyleSheet("""
            QPushButton { background-color: rgba(52, 152, 219, 0.85); color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(41, 128, 185, 0.95); }
        """)
        back_btn.setFixedWidth(180)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.back_btn = back_btn

        chart_container = QWidget()
        chart_container.setStyleSheet("background-color: rgba(255, 255, 255, 160); border-radius: 20px; padding: 15px;")
        chart_layout = QVBoxLayout(chart_container)
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_container)

        self.plot_minute_detail()

    def plot_minute_detail(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')
        intervals = [f"{i * 10}-{(i + 1) * 10}" for i in range(6)]
        # 统计每个10分钟区间内的秒数
        seconds_data = [0] * 6
        for record in self.records:
            start_min, end_min = record.start_time.minute, record.end_time.minute
            start_sec, end_sec = record.start_time.second, record.end_time.second

            # 简化计算：将起始和结束时间都转为该小时内的总秒数
            rec_start_total = start_min * 60 + start_sec
            rec_end_total = end_min * 60 + end_sec

            for i in range(6):
                interval_start = i * 10 * 60
                interval_end = (i + 1) * 10 * 60
                # 计算交集秒数
                overlap_start = max(rec_start_total, interval_start)
                overlap_end = min(rec_end_total, interval_end)
                if overlap_end > overlap_start:
                    seconds_data[i] += (overlap_end - overlap_start)

        # 转换为分钟数值供绘图
        minutes_plot_data = [s / 60 for s in seconds_data]
        colors = [to_rgba('#3498db') if s > 0 else (0.74, 0.76, 0.78, 0.3) for s in seconds_data]
        bars = ax.bar(intervals, minutes_plot_data, color=colors, edgecolor='white', linewidth=1)

        # 在柱子上方显示时长标签 (MM:SS 格式)
        for bar, total_sec in zip(bars, seconds_data):
            if total_sec > 0:
                height = bar.get_height()
                m = int(total_sec // 60)
                s = int(total_sec % 60)
                label = f"{m:02d}:{s:02d}"
                ax.text(bar.get_x() + bar.get_width() / 2., height, label,
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color='#2c3e50')

        ax.set_title(f"{self.hour:02d}点的分钟级学习分布", pad=15, fontsize=12, fontweight='bold')
        # 纵轴显示分钟，最大10分钟
        ax.set_ylim(0, max(minutes_plot_data + [11]))
        ax.set_ylabel("学习时长 (分钟)")
        self.figure.tight_layout()
        self.canvas.draw()


class TodayWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.current_date = datetime.now().date()
        self.hourly_records = {i: [] for i in range(24)}
        self.init_ui()
        self.update_today_stats()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部：标题 + 日期切换 + 总时长
        header_container = QWidget()
        header_container.setStyleSheet("background-color: rgba(255, 255, 255, 180); border-radius: 15px;")
        header_layout = QHBoxLayout(header_container)

        self.title_label = QLabel("今日学习统计")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 日期切换按钮组
        date_btn_layout = QHBoxLayout()
        self.yesterday_btn = QPushButton("昨天")
        self.today_btn = QPushButton("今天")
        for btn in [self.yesterday_btn, self.today_btn]:
            btn.setCheckable(True)
            btn.setFixedSize(70, 35)
            btn.setStyleSheet("""
                QPushButton { background-color: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 6px; font-weight: bold; }
                QPushButton:checked { background-color: #3498db; color: white; border: none; }
                QPushButton:hover:!checked { background-color: #dcdde1; }
            """)
        self.today_btn.setChecked(True)
        self.yesterday_btn.clicked.connect(lambda: self.change_date(datetime.now().date() - timedelta(days=1)))
        self.today_btn.clicked.connect(lambda: self.change_date(datetime.now().date()))

        self.date_group = QButtonGroup(self)
        self.date_group.addButton(self.yesterday_btn)
        self.date_group.addButton(self.today_btn)

        date_btn_layout.addWidget(self.yesterday_btn)
        date_btn_layout.addWidget(self.today_btn)
        header_layout.addLayout(date_btn_layout)

        header_layout.addSpacing(20)
        self.total_time_label = QLabel("总时长: 00:00:00")
        self.total_time_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #27ae60; background: rgba(255,255,255,0.5); padding: 8px 15px; border-radius: 10px;")
        header_layout.addWidget(self.total_time_label)
        layout.addWidget(header_container)

        # 图表区域
        self.stack = QStackedWidget()
        self.main_view = self.create_main_view()
        self.stack.addWidget(self.main_view)
        self.detail_view = None
        layout.addWidget(self.stack)

    def create_main_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        chart_container = QWidget()
        chart_container.setStyleSheet("background-color: rgba(255, 255, 255, 160); border-radius: 20px; padding: 15px;")
        chart_layout = QVBoxLayout(chart_container)
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_chart_click)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_container)

        # 24小时网格导航
        self.nav_grid = QWidget()
        self.nav_grid.setStyleSheet("background-color: rgba(255, 255, 255, 140); border-radius: 15px; padding: 10px;")
        grid_layout = QGridLayout(self.nav_grid)
        self.hour_buttons = []
        for i in range(24):
            btn = QPushButton(f"{i:02d}")
            btn.setFixedSize(42, 35)  # 增加高度，防止数字上下遮挡
            btn.clicked.connect(lambda checked, h=i: self.show_hour_detail(h))
            self.hour_buttons.append(btn)
            grid_layout.addWidget(btn, i // 12, i % 12)
        layout.addWidget(self.nav_grid)
        return widget

    def change_date(self, date):
        self.current_date = date
        self.title_label.setText("今日学习统计" if date == datetime.now().date() else "昨日学习统计")
        self.update_today_stats()
        self.back_to_main()

    def update_today_stats(self):
        records = [r for r in self.dm.records if r.start_time.date() == self.current_date]
        total_sec = sum((r.end_time - r.start_time).total_seconds() for r in records)
        self.total_time_label.setText(
            f"总时长: {int(total_sec // 3600):02d}:{int((total_sec % 3600) // 60):02d}:{int(total_sec % 60):02d}")

        self.hourly_records = {i: [] for i in range(24)}
        for r in records: self.hourly_records[r.start_time.hour].append(r)

        for i, btn in enumerate(self.hour_buttons):
            has_data = len(self.hourly_records[i]) > 0
            bg_color = 'rgba(46, 204, 113, 0.9)' if has_data else 'rgba(236, 240, 241, 0.9)'
            txt_color = 'white' if has_data else '#2c3e50'
            btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: {bg_color}; 
                    color: {txt_color}; 
                    border-radius: 6px; 
                    font-weight: bold; 
                    border: 1px solid rgba(0,0,0,0.1);
                    padding: 0px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: #3498db; color: white; }}
            """)
        self.update_chart()

    def update_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')
        hours = list(range(24))
        # 统计每个小时内的总秒数
        hourly_seconds = [sum((r.end_time - r.start_time).total_seconds() for r in self.hourly_records[h]) for h in
                          hours]
        # 转换为分钟数值供绘图
        minutes_plot_data = [s / 60 for s in hourly_seconds]
        colors = [to_rgba('#3498db') if s > 0 else (0.74, 0.76, 0.78, 0.3) for s in hourly_seconds]
        bars = ax.bar(hours, minutes_plot_data, color=colors, edgecolor='white', linewidth=1)

        # 在柱子上方显示时长标签 (MM:SS 格式)
        for bar, total_sec in zip(bars, hourly_seconds):
            if total_sec > 0:
                height = bar.get_height()
                m = int(total_sec // 60)
                s = int(total_sec % 60)
                label = f"{m:02d}:{s:02d}"
                ax.text(bar.get_x() + bar.get_width() / 2., height, label,
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color='#2c3e50')

        ax.set_title(f"{self.current_date.strftime('%Y-%m-%d')} 24小时分布", pad=15, fontweight='bold')
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h:02d}" for h in hours], fontsize=8)

        # 优化坐标轴范围
        max_min = max(minutes_plot_data + [12])
        ax.set_ylim(0, max_min)
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylabel("学习时长 (分钟)")

        ax.axvspan(6, 18, alpha=0.05, color='#f1c40f')  # 白天高亮
        self.figure.tight_layout()
        self.canvas.draw()

    def on_chart_click(self, event):
        if event.inaxes and 0 <= round(event.xdata) <= 23:
            h = int(round(event.xdata))
            if self.hourly_records[h]: self.show_hour_detail(h)

    def show_hour_detail(self, hour):
        if not self.hourly_records[hour]: return
        if self.detail_view: self.detail_view.deleteLater()
        self.detail_view = HourDetailDialog(hour, self.hourly_records[hour], self.current_date, self)
        self.detail_view.back_btn.clicked.connect(self.back_to_main)
        self.stack.addWidget(self.detail_view)
        self.stack.setCurrentWidget(self.detail_view)

    def back_to_main(self):
        self.stack.setCurrentIndex(0)