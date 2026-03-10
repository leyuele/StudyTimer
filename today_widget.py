import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QPushButton, QStackedWidget, QGridLayout,
                             QScrollArea, QFrame, QSizePolicy)
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


# 辅助函数：将颜色转换为 matplotlib 可用的格式
def to_rgba(color_str, alpha=1.0):
    """将颜色字符串或元组转换为 matplotlib 可用的 RGBA"""
    if isinstance(color_str, tuple):
        return color_str
    # 处理十六进制颜色
    if color_str.startswith('#'):
        r = int(color_str[1:3], 16) / 255.0
        g = int(color_str[3:5], 16) / 255.0
        b = int(color_str[5:7], 16) / 255.0
        return (r, g, b, alpha)
    return color_str


class HourDetailDialog(QWidget):
    """显示某个小时的详细分钟分布（弹窗/页面）"""

    def __init__(self, hour, records, parent=None):
        super().__init__(parent)
        self.hour = hour
        self.records = records  # 该小时内的所有记录
        self.init_ui()

    def init_ui(self):
        # 设置透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题 - 半透明背景
        title_container = QWidget()
        title_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180);
            border-radius: 15px;
            padding: 10px;
        """)
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel(f"{self.hour:02d}:00 - {self.hour:02d}:59 详细分布")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        layout.addWidget(title_container)

        # 返回按钮 - 毛玻璃效果
        back_btn = QPushButton("← 返回24小时视图")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 152, 219, 0.85);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { 
                background-color: rgba(41, 128, 185, 0.95);
            }
        """)
        back_btn.setFixedWidth(160)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.back_btn = back_btn

        # 图表容器 - 半透明背景
        chart_container = QWidget()
        chart_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 20px;
            padding: 15px;
        """)
        chart_layout = QVBoxLayout(chart_container)

        # 图表
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.figure.patch.set_facecolor('none')  # 透明背景
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_container)

        # 统计信息 - 半透明背景
        info_container = QWidget()
        info_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180);
            border-radius: 10px;
            padding: 10px;
        """)
        info_layout = QHBoxLayout(info_container)
        info_layout.setContentsMargins(15, 10, 15, 10)

        total_minutes = sum((r.end_time - r.start_time).total_seconds() / 60 for r in self.records)

        total_label = QLabel(f"该小时总学习时长: {int(total_minutes)} 分钟")
        total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60; background: transparent;")

        count_label = QLabel(f"学习次数: {len(self.records)} 次")
        count_label.setStyleSheet("font-size: 14px; color: #34495e; background: transparent;")

        info_layout.addWidget(total_label)
        info_layout.addWidget(count_label)
        info_layout.addStretch()
        layout.addWidget(info_container)

        self.plot_minute_detail()

    def plot_minute_detail(self, chart_type='bar'):
        """绘制该小时的分钟分布（10分钟为一个区间）"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')  # 透明背景

        # 初始化6个区间（0-10, 10-20, 20-30, 30-40, 40-50, 50-60）
        intervals = [f"{i * 10}-{(i + 1) * 10}" for i in range(6)]
        minutes_data = [0] * 6

        # 统计每个10分钟区间的学习时长
        for record in self.records:
            start_min = record.start_time.minute
            end_min = record.end_time.minute

            # 计算跨越的区间
            start_interval = start_min // 10
            end_interval = end_min // 10

            for i in range(start_interval, min(end_interval + 1, 6)):
                # 计算在该区间内的实际分钟数
                interval_start = max(i * 10, start_min)
                interval_end = min((i + 1) * 10, end_min)
                if interval_end > interval_start:
                    minutes_data[i] += (interval_end - interval_start)

        # 使用正确的颜色格式（元组）
        colors = [to_rgba('#3498db') if m > 0 else (0.74, 0.76, 0.78, 0.5) for m in minutes_data]

        if chart_type == 'bar':
            bars = ax.bar(intervals, minutes_data, color=colors, edgecolor='white', linewidth=1.5)
            ax.set_ylabel("学习时长 (分钟)", fontsize=11)
            ax.set_xlabel("时间段", fontsize=11)

            # 在柱子上显示数值
            for bar, val in zip(bars, minutes_data):
                if val > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{int(val)}',
                            ha='center', va='bottom', fontsize=10, fontweight='bold')
        else:  # line
            ax.plot(intervals, minutes_data, marker='o', color='#9b59b6',
                    linewidth=2, markersize=8)
            ax.fill_between(range(len(intervals)), minutes_data, alpha=0.3, color='#9b59b6')
            ax.set_ylabel("学习时长 (分钟)", fontsize=11)
            ax.set_xlabel("时间段", fontsize=11)
            ax.grid(True, linestyle='--', alpha=0.4)

        ax.set_title(f"{self.hour:02d}:00 时段的分钟级学习分布", pad=15, fontsize=14, fontweight='bold',
                     color='#2c3e50')
        ax.set_ylim(0, max(minutes_data + [10]))

        # 设置坐标轴颜色
        ax.tick_params(colors='#2c3e50')
        ax.xaxis.label.set_color('#2c3e50')
        ax.yaxis.label.set_color('#2c3e50')

        self.figure.tight_layout()
        self.canvas.draw()


class TodayWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.current_chart_type = 'bar'  # 'bar' 或 'line'
        self.hourly_records = {}  # 存储每小时的学习记录
        self.init_ui()
        self.update_today_stats()

    def init_ui(self):
        # 设置透明背景，让壁纸显示出来
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部标题和统计 - 使用半透明容器
        header_container = QWidget()
        header_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180);
            border-radius: 15px;
            padding: 5px;
        """)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("今日学习统计")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 今日总时长显示
        self.total_time_label = QLabel("今日总时长: 00:00:00")
        self.total_time_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #27ae60;
            background-color: rgba(255, 255, 255, 120);
            padding: 12px 25px;
            border-radius: 12px;
            border: 2px solid rgba(39, 174, 96, 0.3);
        """)
        header_layout.addWidget(self.total_time_label)

        layout.addWidget(header_container)

        # 图表控制栏 - 半透明背景
        control_container = QWidget()
        control_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 12px;
            padding: 5px;
        """)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(15, 10, 15, 10)

        control_layout.addWidget(QLabel("图表类型:"))
        self.chart_combo = QComboBox()
        self.chart_combo.addItems(["柱形图 (24小时分布)", "折线图 (趋势变化)"])
        self.chart_combo.currentIndexChanged.connect(self.on_chart_type_changed)
        self.chart_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(52, 152, 219, 0.3);
                border-radius: 6px;
                padding: 5px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: rgba(52, 152, 219, 0.6);
            }
        """)
        control_layout.addWidget(self.chart_combo)

        control_layout.addStretch()

        # 提示文字
        tip_label = QLabel("💡 点击图表中的柱子/节点可查看该小时的详细分钟分布")
        tip_label.setStyleSheet("color: #7f8c8d; font-size: 12px; background: transparent;")
        control_layout.addWidget(tip_label)

        layout.addWidget(control_container)

        # 使用堆叠部件切换视图
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        # 主视图（24小时分布）
        self.main_view = self.create_main_view()
        self.stack.addWidget(self.main_view)

        # 详情视图（某小时的分钟分布）
        self.detail_view = None  # 动态创建

        layout.addWidget(self.stack)

    def create_main_view(self):
        """创建主视图（24小时分布图）"""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 图表容器 - 半透明背景
        chart_container = QWidget()
        chart_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 20px;
            padding: 15px;
        """)
        chart_layout = QVBoxLayout(chart_container)

        # 图表
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.figure.patch.set_facecolor('none')  # 透明背景
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.mpl_connect('button_press_event', self.on_chart_click)
        chart_layout.addWidget(self.canvas)

        layout.addWidget(chart_container)

        # 24小时快速导航 - 半透明背景
        nav_container = QWidget()
        nav_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 140);
            border-radius: 15px;
            padding: 10px;
        """)
        nav_layout = QGridLayout(nav_container)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(15, 15, 15, 15)

        self.hour_buttons = []
        for i in range(24):
            btn = QPushButton(f"{i:02d}")
            btn.setFixedSize(45, 35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(236, 240, 241, 0.9);
                    border: 1px solid rgba(189, 195, 199, 0.3);
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                QPushButton:hover { 
                    background-color: rgba(52, 152, 219, 0.9); 
                    color: white;
                    border-color: rgba(52, 152, 219, 0.6);
                }
                QPushButton:disabled { 
                    background-color: rgba(189, 195, 199, 0.5);
                    color: rgba(127, 140, 141, 0.8);
                }
            """)
            btn.clicked.connect(lambda checked, h=i: self.show_hour_detail(h))
            self.hour_buttons.append(btn)
            nav_layout.addWidget(btn, i // 12, i % 12)

        layout.addWidget(nav_container)

        return widget

    def on_chart_type_changed(self, index):
        """切换图表类型"""
        self.current_chart_type = 'bar' if index == 0 else 'line'
        self.update_chart()

    def update_today_stats(self):
        """更新今日统计数据"""
        today = datetime.now().date()
        today_records = [r for r in self.dm.records if r.start_time.date() == today]

        # 计算总时长
        total_seconds = sum((r.end_time - r.start_time).total_seconds() for r in today_records)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        self.total_time_label.setText(f"今日总时长: {hours:02d}:{minutes:02d}:{seconds:02d}")

        # 按小时分组
        self.hourly_records = {i: [] for i in range(24)}
        for record in today_records:
            hour = record.start_time.hour
            self.hourly_records[hour].append(record)

        # 更新小时按钮状态（有数据的显示不同颜色）
        for i, btn in enumerate(self.hour_buttons):
            if self.hourly_records[i]:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(46, 204, 113, 0.9);
                        color: white;
                        border: 1px solid rgba(39, 174, 96, 0.4);
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover { 
                        background-color: rgba(39, 174, 96, 1.0);
                        border-color: rgba(39, 174, 96, 0.8);
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(236, 240, 241, 0.9);
                        border: 1px solid rgba(189, 195, 199, 0.3);
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        color: #2c3e50;
                    }
                    QPushButton:hover { 
                        background-color: rgba(52, 152, 219, 0.9); 
                        color: white;
                        border-color: rgba(52, 152, 219, 0.6);
                    }
                    QPushButton:disabled { 
                        background-color: rgba(189, 195, 199, 0.5);
                    }
                """)

        self.update_chart()

    def update_chart(self):
        """更新24小时分布图表"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')  # 透明背景

        # 准备数据（每个小时的学习分钟数）
        hours = list(range(24))
        minutes = []
        for h in range(24):
            total_min = sum((r.end_time - r.start_time).total_seconds() / 60
                            for r in self.hourly_records[h])
            minutes.append(total_min)

        # 使用正确的颜色格式（元组）
        colors = [to_rgba('#3498db') if m > 0 else (0.74, 0.76, 0.78, 0.5) for m in minutes]

        if self.current_chart_type == 'bar':
            bars = ax.bar(hours, minutes, color=colors, edgecolor='white', linewidth=1.5)
            ax.set_xlabel("小时", fontsize=12, color='#2c3e50')
            ax.set_ylabel("学习时长 (分钟)", fontsize=12, color='#2c3e50')

            # 在柱子上显示数值（只显示有数据的）
            for bar, val in zip(bars, minutes):
                if val > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{int(val)}',
                            ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2c3e50')
        else:  # line
            # 只显示有数据的小时点，或者显示所有点但用不同颜色
            ax.plot(hours, minutes, marker='o', color='#9b59b6',
                    linewidth=2, markersize=6)

            # 高亮有数据的点
            active_hours = [h for h, m in zip(hours, minutes) if m > 0]
            active_mins = [m for m in minutes if m > 0]
            if active_hours:
                ax.scatter(active_hours, active_mins, color='#e74c3c', s=100, zorder=5)

            ax.set_xlabel("小时", fontsize=12, color='#2c3e50')
            ax.set_ylabel("学习时长 (分钟)", fontsize=12, color='#2c3e50')
            ax.grid(True, linestyle='--', alpha=0.4)

        ax.set_title("今日24小时学习时长分布", pad=20, fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h:02d}" for h in hours], rotation=45, color='#2c3e50')
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(0, max(minutes + [10]))

        # 设置坐标轴颜色
        ax.tick_params(colors='#2c3e50')
        ax.spines['bottom'].set_color('#2c3e50')
        ax.spines['top'].set_color('#2c3e50')
        ax.spines['left'].set_color('#2c3e50')
        ax.spines['right'].set_color('#2c3e50')

        # 添加背景色区分白天和夜晚（使用十六进制颜色，matplotlib 会自动处理）
        ax.axvspan(6, 18, alpha=0.08, color='#f1c40f', label='白天')
        ax.axvspan(18, 23, alpha=0.08, color='#34495e', label='晚上')
        ax.axvspan(0, 6, alpha=0.08, color='#34495e')

        ax.legend(loc='upper right', framealpha=0.8)
        self.figure.tight_layout()
        self.canvas.draw()

    def on_chart_click(self, event):
        """处理图表点击事件"""
        if event.inaxes is None:
            return

        # 获取点击的小时
        if self.current_chart_type == 'bar':
            # 对于柱形图，获取最近的柱子
            hour = int(round(event.xdata))
        else:
            # 对于折线图，获取最近的点
            hour = int(round(event.xdata))

        if 0 <= hour <= 23 and self.hourly_records.get(hour):
            self.show_hour_detail(hour)

    def show_hour_detail(self, hour):
        """显示指定小时的详细视图"""
        if not self.hourly_records.get(hour):
            return

        # 创建详情视图
        if self.detail_view:
            self.stack.removeWidget(self.detail_view)
            self.detail_view.deleteLater()

        self.detail_view = HourDetailDialog(hour, self.hourly_records[hour], self)
        self.detail_view.back_btn.clicked.connect(self.back_to_main)
        self.detail_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.stack.addWidget(self.detail_view)
        self.stack.setCurrentWidget(self.detail_view)

        # 切换图表类型按钮也应用到详情页
        if self.chart_combo.currentIndex() == 1:  # 折线图
            self.detail_view.plot_minute_detail('line')

    def back_to_main(self):
        """返回主视图"""
        self.stack.setCurrentIndex(0)
        self.update_today_stats()  # 刷新数据