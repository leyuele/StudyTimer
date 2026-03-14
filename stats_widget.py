import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QFrame
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 标签颜色映射 (与 today_widget 保持一致)
TAG_COLORS = {
    "Study": "#3498db",  # 蓝色
    "Game": "#e74c3c",  # 红色
    "Rest": "#2ecc71",  # 绿色
    "Work": "#f1c40f",  # 黄色
    "Default": "#95a5a6"  # 灰色
}


class StatsWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 顶部筛选栏容器
        filter_container = QFrame()
        filter_container.setStyleSheet(
            "background-color: rgba(255, 255, 255, 180); border-radius: 15px; padding: 10px;")
        filter_layout = QHBoxLayout(filter_container)

        # 时间范围
        filter_layout.addWidget(QLabel("📅 时间范围:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["最近一周", "最近一月", "最近一年"])
        self.period_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 5px;")
        self.period_combo.currentIndexChanged.connect(self.update_charts)
        filter_layout.addWidget(self.period_combo)

        # 图表类型
        filter_layout.addWidget(QLabel("📊 图表类型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["堆叠条形图 (每日活动)", "饼图 (活动占比)", "折线图 (趋势分析)"])
        self.chart_type_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 5px;")
        self.chart_type_combo.currentIndexChanged.connect(self.update_charts)
        filter_layout.addWidget(self.chart_type_combo)

        filter_layout.addStretch()
        layout.addWidget(filter_container)

        # 图表容器
        chart_container = QFrame()
        chart_container.setStyleSheet("background-color: rgba(255, 255, 255, 160); border-radius: 20px; padding: 15px;")
        chart_layout = QVBoxLayout(chart_container)

        self.figure = Figure(figsize=(10, 7), dpi=100)
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_container)

        self.update_charts()

    def update_charts(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('none')

        if not self.dm.records:
            ax.text(0.5, 0.5, "暂无数据，快去开始计时吧！", ha='center', va='center', fontsize=14, color='#7f8c8d')
            self.canvas.draw()
            return

        # 准备数据
        data = []
        for r in self.dm.records:
            duration = (r.end_time - r.start_time).total_seconds() / 3600  # 小时
            data.append({
                "date": r.start_time.date(),
                "duration": duration,
                "category": r.category
            })

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        # 过滤数据
        now = datetime.now()
        period = self.period_combo.currentText()
        if period == "最近一周":
            start_date = now - timedelta(days=7)
        elif period == "最近一月":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=365)

        df = df[df['date'] >= pd.to_datetime(start_date.date())]

        if df.empty:
            ax.text(0.5, 0.5, "所选范围内无数据", ha='center', va='center', fontsize=14, color='#7f8c8d')
            self.canvas.draw()
            return

        chart_type = self.chart_type_combo.currentText()

        if "堆叠条形图" in chart_type:
            # 透视表：日期为索引，类别为列
            pivot_df = df.pivot_table(index='date', columns='category', values='duration', aggfunc='sum').fillna(0)

            # 补齐缺失日期
            all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            pivot_df = pivot_df.reindex(all_dates, fill_value=0)

            # 绘图
            colors = [TAG_COLORS.get(cat, TAG_COLORS["Default"]) for cat in pivot_df.columns]
            pivot_df.plot(kind='bar', stacked=True, ax=ax, color=colors, edgecolor='white', linewidth=0.5)

            ax.set_title("每日活动时长分布", pad=20, fontweight='bold')
            ax.set_ylabel("时长 (小时)")
            ax.set_xlabel("日期")
            ax.set_xticklabels([d.strftime('%m-%d') for d in pivot_df.index], rotation=45)
            ax.legend(title="活动类别", bbox_to_anchor=(1.05, 1), loc='upper left')

        elif "饼图" in chart_type:
            cat_data = df.groupby('category')['duration'].sum()
            colors = [TAG_COLORS.get(cat, TAG_COLORS["Default"]) for cat in cat_data.index]

            wedges, texts, autotexts = ax.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%',
                                              colors=colors, startangle=90,
                                              wedgeprops={'edgecolor': 'white', 'linewidth': 1})
            plt.setp(autotexts, size=10, weight="bold", color="white")
            ax.set_title("活动类别总时长占比", pad=20, fontweight='bold')

        elif "折线图" in chart_type:
            daily_total = df.groupby('date')['duration'].sum()
            all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            daily_total = daily_total.reindex(all_dates, fill_value=0)

            ax.plot(daily_total.index, daily_total.values, marker='o', color='#3498db', linewidth=3, markersize=8,
                    label="总时长")
            ax.fill_between(daily_total.index, daily_total.values, alpha=0.2, color='#3498db')

            ax.set_title("活动时长变化趋势", pad=20, fontweight='bold')
            ax.set_ylabel("时长 (小时)")
            ax.set_xlabel("日期")
            ax.set_xticks(daily_total.index[::max(1, len(daily_total) // 7)])  # 稀疏显示刻度
            ax.set_xticklabels([d.strftime('%m-%d') for d in daily_total.index[::max(1, len(daily_total) // 7)]],
                               rotation=45)
            ax.grid(True, linestyle='--', alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()