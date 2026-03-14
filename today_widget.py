from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QGridLayout,
                             QButtonGroup)
from PyQt6.QtCore import Qt
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 标签颜色映射
TAG_COLORS = {
    "Study": "#3498db",  # 蓝色
    "Game": "#e74c3c",  # 红色
    "Rest": "#2ecc71",  # 绿色
    "Work": "#f1c40f",  # 黄色
    "Default": "#95a5a6"  # 灰色
}


def get_tag_color(tag, alpha=1.0):
    color = TAG_COLORS.get(tag, TAG_COLORS["Default"])
    if color.startswith('#'):
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        return (r, g, b, alpha)
    return color


class HourDetailDialog(QWidget):
    def __init__(self, hour, records, target_date, parent=None):
        super(HourDetailDialog, self).__init__(parent)
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

        self.back_btn = QPushButton("← 返回 24小时视图")
        self.back_btn.setStyleSheet("""
            QPushButton { background-color: rgba(52, 152, 219, 0.85); color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(41, 128, 185, 0.95); }
        """)
        self.back_btn.setFixedWidth(180)
        layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

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

        hour_start = datetime.combine(self.target_date, datetime.min.time()) + timedelta(hours=self.hour)
        hour_end = hour_start + timedelta(hours=1)

        intervals = [f"{i * 10}-{(i + 1) * 10}" for i in range(6)]
        # 获取所有涉及的标签
        tags = sorted(list(set(r.category for r in self.records)))
        if not tags: tags = ["Study"]

        # 准备堆叠数据：每个标签在每个时间段的秒数
        tag_data = {tag: [0.0] * 6 for tag in tags}

        for record in self.records:
            overlap_start = max(record.start_time, hour_start)
            overlap_end = min(record.end_time, hour_end)

            if overlap_end > overlap_start:
                rel_start = (overlap_start - hour_start).total_seconds()
                rel_end = (overlap_end - hour_start).total_seconds()

                for i in range(6):
                    int_start = i * 10 * 60
                    int_end = (i + 1) * 10 * 60
                    o_start = max(rel_start, int_start)
                    o_end = min(rel_end, int_end)
                    if o_end > o_start:
                        tag_data[record.category][i] += (o_end - o_start)

        # 绘图
        bottom = np.zeros(6)
        for tag in tags:
            minutes = [s / 60 for s in tag_data[tag]]
            if any(m > 0 for m in minutes):
                ax.bar(intervals, minutes, bottom=bottom, label=tag, color=get_tag_color(tag), edgecolor='white',
                       linewidth=0.5)
                bottom += minutes

        ax.set_title(f"{self.hour:02d}点的分钟级活动分布", pad=15, fontsize=12, fontweight='bold')
        ax.set_ylim(0, 11)
        ax.set_ylabel("时长 (分钟)")
        ax.legend(loc='upper right', fontsize=8)
        self.figure.tight_layout()
        self.canvas.draw()


class TodayWidget(QWidget):
    def __init__(self, data_manager, parent=None):
        super(TodayWidget, self).__init__(parent)
        self.dm = data_manager
        self.current_date = datetime.now().date()
        self.records_by_hour = {i: [] for i in range(24)}
        self.detail_view = None
        self.init_ui()
        self.update_today_stats()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_container = QWidget()
        header_container.setStyleSheet("background-color: rgba(255, 255, 255, 180); border-radius: 15px;")
        header_layout = QHBoxLayout(header_container)

        self.title_label = QLabel("今日活动统计")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

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

        self.stack = QStackedWidget()
        self.main_view = self.create_main_view()
        self.stack.addWidget(self.main_view)
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

        self.nav_grid = QWidget()
        self.nav_grid.setStyleSheet("background-color: rgba(255, 255, 255, 140); border-radius: 15px; padding: 10px;")
        grid_layout = QGridLayout(self.nav_grid)
        self.hour_buttons = []
        for i in range(24):
            btn = QPushButton(f"{i:02d}")
            btn.setFixedSize(42, 35)
            btn.clicked.connect(lambda checked, h=i: self.show_hour_detail(h))
            self.hour_buttons.append(btn)
            grid_layout.addWidget(btn, i // 12, i % 12)
        layout.addWidget(self.nav_grid)
        return widget

    def change_date(self, date):
        self.current_date = date
        self.title_label.setText("今日活动统计" if date == datetime.now().date() else "昨日活动统计")
        self.update_today_stats()
        self.back_to_main()

    def update_today_stats(self):
        day_start = datetime.combine(self.current_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        day_records = [r for r in self.dm.records if r.start_time < day_end and r.end_time > day_start]

        total_sec = 0.0
        self.records_by_hour = {i: [] for i in range(24)}

        # 准备堆叠数据
        tags = sorted(list(set(r.category for r in day_records)))
        if not tags: tags = ["Study"]
        self.hourly_tag_seconds = {tag: [0.0] * 24 for tag in tags}

        for r in day_records:
            actual_start = max(r.start_time, day_start)
            actual_end = min(r.end_time, day_end)
            total_sec += (actual_end - actual_start).total_seconds()

            if r.category not in self.hourly_tag_seconds:
                self.hourly_tag_seconds[r.category] = [0.0] * 24

            for h in range(24):
                h_start = day_start + timedelta(hours=h)
                h_end = h_start + timedelta(hours=1)
                o_start = max(actual_start, h_start)
                o_end = min(actual_end, h_end)
                if o_end > o_start:
                    self.hourly_tag_seconds[r.category][h] += (o_end - o_start).total_seconds()
                    self.records_by_hour[h].append(r)

        self.total_time_label.setText(
            f"总时长: {int(total_sec // 3600):02d}:{int((total_sec % 3600) // 60):02d}:{int(total_sec % 60):02d}")

        for i, btn in enumerate(self.hour_buttons):
            hour_total = sum(self.hourly_tag_seconds[tag][i] for tag in self.hourly_tag_seconds)
            has_data = hour_total > 0
            bg_color = 'rgba(46, 204, 113, 0.9)' if has_data else 'rgba(236, 240, 241, 0.9)'
            txt_color = 'white' if has_data else '#2c3e50'
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg_color}; color: {txt_color}; border-radius: 6px; font-weight: bold; font-size: 11px; padding: 0px; }}")

        self.update_chart()

    def update_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')
        hours = list(range(24))

        bottom = np.zeros(24)
        tags = sorted(self.hourly_tag_seconds.keys())

        for tag in tags:
            minutes = [s / 60 for s in self.hourly_tag_seconds[tag]]
            if any(m > 0 for m in minutes):
                ax.bar(hours, minutes, bottom=bottom, label=tag, color=get_tag_color(tag), edgecolor='white',
                       linewidth=0.5)
                bottom += minutes

        # 在顶部显示总时长
        for i in range(24):
            total_m = bottom[i]
            if total_m > 0:
                m = int(total_m)
                s = int((total_m - m) * 60)
                ax.text(i, total_m, f"{m:02d}:{s:02d}", ha='center', va='bottom', fontsize=8, fontweight='bold',
                        color='#2c3e50')

        ax.set_title(f"{self.current_date.strftime('%Y-%m-%d')} 活动分布", pad=15, fontweight='bold')
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h:02d}" for h in hours], fontsize=8)
        ax.set_ylim(0, 65)
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylabel("时长 (分钟)")
        ax.legend(loc='upper right', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()

    def on_chart_click(self, event):
        if event.inaxes and 0 <= round(event.xdata) <= 23:
            h = int(round(event.xdata))
            hour_total = sum(self.hourly_tag_seconds[tag][h] for tag in self.hourly_tag_seconds)
            if hour_total > 0: self.show_hour_detail(h)

    def show_hour_detail(self, hour):
        if self.detail_view:
            self.detail_view.deleteLater()
        self.detail_view = HourDetailDialog(hour, self.records_by_hour[hour], self.current_date, self)
        self.detail_view.back_btn.clicked.connect(self.back_to_main)
        self.stack.addWidget(self.detail_view)
        self.stack.setCurrentWidget(self.detail_view)

    def back_to_main(self):
        self.stack.setCurrentIndex(0)