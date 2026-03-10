import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QLineEdit, QCheckBox, QMessageBox, 
                             QSlider, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QRegion

class ImageCropper(QDialog):
    """截图式图片裁剪对话框：背景变暗，选区变亮"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("裁剪壁纸 - 拖动鼠标划定亮区")
        self.setModal(True)
        self.original_pixmap = QPixmap(image_path)
        
        # 限制显示大小，自适应屏幕
        screen_size = QSize(1000, 700)
        self.display_pixmap = self.original_pixmap.scaled(screen_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.scale_factor = self.original_pixmap.width() / self.display_pixmap.width()
        
        self.selection_rect = QRect()
        self.start_point = QPoint()
        self.is_selecting = False
        
        self.init_ui()
        # 设置固定大小以适应缩放后的图片
        self.setFixedSize(self.display_pixmap.width() + 40, self.display_pixmap.height() + 100)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_label = QLabel()
        self.image_label.setPixmap(self.display_pixmap)
        self.image_label.setCursor(Qt.CursorShape.CrossCursor)
        # 启用鼠标追踪，让重绘更流畅
        self.image_label.setMouseTracking(True)
        layout.addWidget(self.image_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def mousePressEvent(self, event):
        # 坐标转换，确保相对于 image_label
        local_pos = self.image_label.mapFrom(self, event.pos())
        if self.image_label.rect().contains(local_pos):
            self.start_point = local_pos
            self.selection_rect = QRect(self.start_point, QSize())
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            local_pos = self.image_label.mapFrom(self, event.pos())
            # 限制在图片矩形内
            clamped_x = max(0, min(local_pos.x(), self.image_label.width()))
            clamped_y = max(0, min(local_pos.y(), self.image_label.height()))
            
            self.selection_rect = QRect(self.start_point, QPoint(clamped_x, clamped_y)).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # 坐标原点移至图片标签位置
        painter.translate(self.image_label.pos())
        
        # 1. 绘制一层半透明黑色遮罩覆盖全图
        overlay_color = QColor(0, 0, 0, 160)
        painter.fillRect(self.image_label.rect(), overlay_color)
        
        # 2. 如果有选区，将选区部分“挖亮”
        if not self.selection_rect.isNull():
            # 使用 CompositionMode_Source 绘制原始图片的一部分到选区
            # 或者更简单的：清除遮罩，露出底图
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # 3. 绘制亮区的蓝色虚线边框
            painter.setPen(QPen(QColor("#3498db"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(self.selection_rect)
            
            # 4. 在角上画小方块增强“截图感”
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#3498db")))
            handle_size = 6
            for point in [self.selection_rect.topLeft(), self.selection_rect.topRight(), 
                          self.selection_rect.bottomLeft(), self.selection_rect.bottomRight()]:
                painter.drawRect(QRect(point.x()-handle_size//2, point.y()-handle_size//2, handle_size, handle_size))

    def get_cropped_pixmap(self):
        if self.selection_rect.isNull() or self.selection_rect.width() < 10:
            return self.original_pixmap
        
        # 映射回原始大图的坐标系
        real_rect = QRect(
            int(self.selection_rect.x() * self.scale_factor),
            int(self.selection_rect.y() * self.scale_factor),
            int(self.selection_rect.width() * self.scale_factor),
            int(self.selection_rect.height() * self.scale_factor)
        )
        return self.original_pixmap.copy(real_rect)

class SettingsWidget(QWidget):
    def __init__(self, data_manager, main_window):
        super().__init__()
        self.dm = data_manager
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        title_label = QLabel("设置中心")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 壁纸配置区域
        wallpaper_section = QVBoxLayout()
        wp_title = QLabel("壁纸与外观")
        wp_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        wallpaper_section.addWidget(wp_title)

        path_layout = QHBoxLayout()
        self.wallpaper_label = QLabel(f"当前壁纸: {os.path.basename(self.dm.settings.get('wallpaper', '默认'))}")
        self.wallpaper_label.setStyleSheet("color: #7f8c8d;")
        wallpaper_btn = QPushButton("选择并裁剪壁纸")
        wallpaper_btn.setFixedWidth(150)
        wallpaper_btn.clicked.connect(self.choose_and_crop_wallpaper)
        path_layout.addWidget(self.wallpaper_label)
        path_layout.addWidget(wallpaper_btn)
        wallpaper_section.addLayout(path_layout)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("壁纸显示浓度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(self.dm.settings.get("wallpaper_opacity", 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        self.opacity_val_label = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_val_label.setFixedWidth(40)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_val_label)
        wallpaper_section.addLayout(opacity_layout)
        
        layout.addLayout(wallpaper_section)

        # 标语设置
        slogan_section = QVBoxLayout()
        sl_title = QLabel("个性化标语")
        sl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        slogan_section.addWidget(sl_title)

        slogan_input_layout = QHBoxLayout()
        self.slogan_edit = QLineEdit(self.dm.settings.get("slogan", "保持专注"))
        self.show_slogan_cb = QCheckBox("显示")
        self.show_slogan_cb.setChecked(self.dm.settings.get("show_slogan", True))
        save_slogan_btn = QPushButton("保存")
        save_slogan_btn.setFixedWidth(80)
        save_slogan_btn.clicked.connect(self.save_slogan)
        slogan_input_layout.addWidget(self.slogan_edit)
        slogan_input_layout.addWidget(self.show_slogan_cb)
        slogan_input_layout.addWidget(save_slogan_btn)
        slogan_section.addLayout(slogan_input_layout)
        layout.addLayout(slogan_section)

        # 数据管理
        data_section = QVBoxLayout()
        dt_title = QLabel("数据管理")
        dt_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        data_section.addWidget(dt_title)

        io_layout = QHBoxLayout()
        export_btn = QPushButton("导出记录 (JSON)")
        export_btn.clicked.connect(self.export_records)
        import_btn = QPushButton("导入记录 (JSON)")
        import_btn.clicked.connect(self.import_records)
        io_layout.addWidget(export_btn)
        io_layout.addWidget(import_btn)
        data_section.addLayout(io_layout)
        layout.addLayout(data_section)

        layout.addStretch()
        version_label = QLabel(f"StudyTimer v{self.dm.VERSION}")
        version_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def choose_and_crop_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择原始图片", "", "图片文件 (*.png *.jpg *.jpeg)")
        if file_path:
            cropper = ImageCropper(file_path, self)
            if cropper.exec() == QDialog.DialogCode.Accepted:
                cropped_pixmap = cropper.get_cropped_pixmap()
                save_path = os.path.join(os.path.dirname(self.dm.storage_path), "current_wallpaper.png")
                cropped_pixmap.save(save_path, "PNG")
                
                self.dm.settings["wallpaper"] = save_path
                self.dm.save_data()
                self.wallpaper_label.setText(f"当前壁纸: 已裁剪图片")
                self.main_window.update()

    def update_opacity(self, value):
        self.dm.settings["wallpaper_opacity"] = value
        self.opacity_val_label.setText(f"{value}%")
        self.dm.save_data()
        self.main_window.update()

    def save_slogan(self):
        self.dm.settings["slogan"] = self.slogan_edit.text()
        self.dm.settings["show_slogan"] = self.show_slogan_cb.isChecked()
        self.dm.save_data()
        self.main_window.timer_page.slogan_label.setText(self.slogan_edit.text())
        self.main_window.timer_page.slogan_label.setVisible(self.show_slogan_cb.isChecked())
        QMessageBox.information(self, "提示", "设置已保存")

    def export_records(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出记录", "study_records.json", "JSON 文件 (*.json)")
        if file_path:
            self.dm.export_data(file_path)
            QMessageBox.information(self, "成功", f"数据已成功导出到: {file_path}")

    def import_records(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入记录", "", "JSON 文件 (*.json)")
        if file_path:
            if self.dm.import_data(file_path):
                QMessageBox.information(self, "成功", "数据导入成功！")
            else:
                QMessageBox.warning(self, "错误", "导入失败，请检查文件格式。")
