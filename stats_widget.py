import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

# 配置中文字体，解决截图中的“口口口”乱码问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题

class StatsWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 顶部筛选栏
        filter_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["最近一周", "最近一月", "最近一年"])
        self.period_combo.currentIndexChanged.connect(self.update_charts)
        filter_layout.addWidget(QLabel("时间范围:"))
        filter_layout.addWidget(self.period_combo)

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["折线图 (趋势)", "条形图 (每日时长)", "饼图 (类别占比)"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_charts)
        filter_layout.addWidget(QLabel("图表类型:"))
        filter_layout.addWidget(self.chart_type_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 图表容器
        self.figure = Figure(figsize=(8, 6), dpi=100)
        # 设置画布背景色，使其与 UI 融合
        self.figure.patch.set_facecolor('#f5f6fa')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.update_charts()

    def update_charts(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#ffffff') # 设置绘图区背景为白色

        # 获取数据并转换为 DataFrame
        if not self.dm.records:
            ax.text(0.5, 0.5, "暂无数据，快去开始计时吧！", ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return

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

        # 根据筛选条件过滤数据
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
            ax.text(0.5, 0.5, "所选范围内无数据", ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return

        # 绘制图表
        chart_type = self.chart_type_combo.currentText()
        if "条形图" in chart_type:
            daily = df.groupby('date')['duration'].sum()
            daily.plot(kind='bar', ax=ax, color='#3498db', edgecolor='white')
            ax.set_title("每日学习时长 (小时)", pad=20)
            ax.set_ylabel("时长 (h)")
            ax.set_xlabel("日期")
            plt.setp(ax.get_xticklabels(), rotation=45)
        elif "饼图" in chart_type:
            cat_data = df.groupby('category')['duration'].sum()
            cat_data.plot(kind='pie', ax=ax, autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c', '#f1c40f'], startangle=90)
            ax.set_title("学习类别分布", pad=20)
            ax.set_ylabel("")
        elif "折线图" in chart_type:
            daily = df.groupby('date')['duration'].sum()
            # 确保日期连续显示
            daily = daily.asfreq('D').fillna(0)
            daily.plot(kind='line', ax=ax, marker='o', color='#9b59b6', linewidth=2, markersize=8)
            ax.set_title("学习时长趋势", pad=20)
            ax.set_ylabel("时长 (h)")
            ax.set_xlabel("日期")
            ax.grid(True, linestyle='--', alpha=0.6)

        self.figure.tight_layout()
        self.canvas.draw()
