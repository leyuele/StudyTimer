import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QLineEdit, QCheckBox, QMessageBox,
                             QSlider, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import (QPixmap, QPainter, QPen, QColor, QBrush,
                         QCursor, QPaintEvent)


class ImageCropper(QDialog):
    """仿QQ/微信截图：直接在对话框上绘制，实现外部暗化+选区高亮"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("裁剪壁纸 - 拖动鼠标选择区域")
        self.setModal(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        # 加载原始图片并缩放至合适显示尺寸
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            QMessageBox.warning(self, "错误", "图片加载失败！")
            self.reject()
            return
        max_display = QSize(1200, 800)
        self.display_pixmap = self.original_pixmap.scaled(
            max_display,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.scale_w = self.original_pixmap.width() / self.display_pixmap.width()
        self.scale_h = self.original_pixmap.height() / self.display_pixmap.height()

        # 图片在窗口中的绘制区域（居中，顶部留出边距）
        self.pic_rect = QRect(0, 0, self.display_pixmap.width(), self.display_pixmap.height())

        # 裁剪状态变量
        self.start_point = QPoint(0, 0)
        self.end_point = QPoint(0, 0)
        self.selection_rect = QRect()
        self.is_selecting = False
        self.min_size = 40

        # 标记是否使用全图（直接应用）
        self.use_full_image = False

        self.init_ui()

    def init_ui(self):
        # 窗口大小 = 图片区域 + 底部按钮区域
        self.setFixedSize(
            self.display_pixmap.width() + 40,
            self.display_pixmap.height() + 120
        )
        # 图片区域位置：距顶部20像素，水平居中
        self.pic_rect.moveCenter(self.rect().center())
        self.pic_rect.moveTop(20)

        # 使用布局放置提示和按钮（确保在图片区域下方）
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 弹簧，将按钮推到底部
        layout.addStretch()

        # 操作提示
        tip = QLabel("✨ 操作：拖动鼠标选择区域 | 选区高亮，其他区域暗化 | 最小40x40像素")
        tip.setStyleSheet("color: #3498db; font-size: 12px; font-weight: 500;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tip)

        # 按钮布局
        btn_layout = QHBoxLayout()

        # 直接应用按钮（使用整张图片）
        self.apply_full_btn = QPushButton("📄 直接应用")
        self.apply_full_btn.setToolTip("使用整张图片作为壁纸（无需裁剪）")
        self.apply_full_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.apply_full_btn.clicked.connect(self._on_apply_full)
        btn_layout.addWidget(self.apply_full_btn)

        btn_layout.addStretch()

        # 确认裁剪按钮
        self.confirm_crop_btn = QPushButton("✂️ 确认裁剪")
        self.confirm_crop_btn.setToolTip("应用选中的裁剪区域")
        self.confirm_crop_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.confirm_crop_btn.clicked.connect(self._on_accept)
        btn_layout.addWidget(self.confirm_crop_btn)

        btn_layout.addStretch()

        # 取消按钮
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def paintEvent(self, event):
        """自定义绘制：图片 → 暗化遮罩 → 选区高亮 + 边框/控制点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 绘制图片
        painter.drawPixmap(self.pic_rect, self.display_pixmap)

        # 2. 如果有选区，先绘制选区内容
        if self.selection_rect.isValid():
            # 绘制选区内容（从原始图片中复制）
            painter.drawPixmap(
                self.selection_rect,
                self.display_pixmap,
                self.selection_rect.translated(-self.pic_rect.topLeft())
            )

            # 绘制选区高亮效果（轻微提亮）
            highlight_color = QColor(255, 255, 255, 30)
            painter.fillRect(self.selection_rect, highlight_color)

        # 3. 绘制暗化遮罩（覆盖整个图片区域，半透明黑色）
        # 但要跳过选区部分
        mask_color = QColor(0, 0, 0, 180)  # 半透明度180，增强对比度
        painter.setBrush(QBrush(mask_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # 绘制四个角落的遮罩
        # 左上角
        painter.drawRect(
            self.pic_rect.left(),
            self.pic_rect.top(),
            self.pic_rect.width(),
            self.selection_rect.top() - self.pic_rect.top()
        )
        # 左下角
        painter.drawRect(
            self.pic_rect.left(),
            self.selection_rect.bottom(),
            self.pic_rect.width(),
            self.pic_rect.bottom() - self.selection_rect.bottom()
        )
        # 左侧
        painter.drawRect(
            self.pic_rect.left(),
            self.selection_rect.top(),
            self.selection_rect.left() - self.pic_rect.left(),
            self.selection_rect.height()
        )
        # 右侧
        painter.drawRect(
            self.selection_rect.right(),
            self.selection_rect.top(),
            self.pic_rect.right() - self.selection_rect.right(),
            self.selection_rect.height()
        )

        # 4. 绘制选区边框（蓝色实线）
        if self.selection_rect.isValid():
            border_pen = QPen(QColor("#3498db"), 2, Qt.PenStyle.SolidLine)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.selection_rect.adjusted(0, 0, -1, -1))

            # 5. 绘制四角和四边控制点（蓝色小方块）
            handle_size = 8
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#3498db")))
            # 四角控制点
            corners = [
                self.selection_rect.topLeft(),
                self.selection_rect.topRight(),
                self.selection_rect.bottomLeft(),
                self.selection_rect.bottomRight()
            ]
            for p in corners:
                painter.drawRect(
                    p.x() - handle_size // 2,
                    p.y() - handle_size // 2,
                    handle_size,
                    handle_size
                )
            # 四边中点控制点
            mid_points = [
                QPoint(self.selection_rect.center().x(), self.selection_rect.top()),
                QPoint(self.selection_rect.center().x(), self.selection_rect.bottom()),
                QPoint(self.selection_rect.left(), self.selection_rect.center().y()),
                QPoint(self.selection_rect.right(), self.selection_rect.center().y())
            ]
            for p in mid_points:
                painter.drawRect(
                    p.x() - handle_size // 2,
                    p.y() - handle_size // 2,
                    handle_size,
                    handle_size
                )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 仅在图片区域内开始选择
            if self.pic_rect.contains(event.pos()):
                self.start_point = event.pos()
                self.end_point = self.start_point
                self.is_selecting = True
                self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting and event.buttons() == Qt.MouseButton.LeftButton:
            # 限制结束点在图片区域内
            self.end_point = event.pos()
            self.end_point.setX(max(self.pic_rect.left(), min(self.end_point.x(), self.pic_rect.right())))
            self.end_point.setY(max(self.pic_rect.top(), min(self.end_point.y(), self.pic_rect.bottom())))

            # 计算并规范化选区，确保在图片区域内
            rect = QRect(self.start_point, self.end_point).normalized()
            rect = rect.intersected(self.pic_rect)
            if rect.width() < self.min_size:
                rect.setWidth(self.min_size)
            if rect.height() < self.min_size:
                rect.setHeight(self.min_size)
            rect = rect.intersected(self.pic_rect)  # 再次确保不超出
            self.selection_rect = rect
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = False
            if self.selection_rect.isValid() and (
                    self.selection_rect.width() < self.min_size or self.selection_rect.height() < self.min_size):
                self.selection_rect = QRect()  # 太小则取消选区
            self.update()

    def _on_apply_full(self):
        """直接应用整张图片（无需裁剪）"""
        self.use_full_image = True
        self.accept()

    def _on_accept(self):
        """确认裁剪 - 需要有效选区"""
        if not self.selection_rect.isValid() or self.selection_rect.width() < self.min_size:
            QMessageBox.warning(self, "提示", "请先选择有效的裁剪区域（最小40x40）！\n或直接点击「直接应用」使用整张图片。")
            return
        self.use_full_image = False
        self.accept()

    def get_cropped_pixmap(self):
        """将选中的区域映射回原始图片尺寸并裁剪"""
        # 如果选择了直接应用，返回原图
        if self.use_full_image:
            return self.original_pixmap

        if not self.selection_rect.isValid():
            return self.original_pixmap

        # 将对话框坐标的选区转换为相对于图片区域的坐标
        local_rect = self.selection_rect.translated(-self.pic_rect.topLeft())
        # 映射到原始图片坐标
        real_x = int(local_rect.x() * self.scale_w)
        real_y = int(local_rect.y() * self.scale_h)
        real_w = int(local_rect.width() * self.scale_w)
        real_h = int(local_rect.height() * self.scale_h)
        real_rect = QRect(real_x, real_y, real_w, real_h).intersected(self.original_pixmap.rect())
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

        # 标题
        title_label = QLabel("设置中心")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 壁纸与外观
        wallpaper_section = QVBoxLayout()
        wp_title = QLabel("壁纸与外观")
        wp_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        wallpaper_section.addWidget(wp_title)

        # 选择壁纸按钮
        path_layout = QHBoxLayout()
        current_wp = self.dm.settings.get('wallpaper', '无')
        self.wallpaper_label = QLabel(f"当前壁纸: {os.path.basename(current_wp) if current_wp else '无'}")
        self.wallpaper_label.setStyleSheet("color: #7f8c8d;")
        wallpaper_btn = QPushButton("选择并裁剪壁纸")
        wallpaper_btn.setFixedWidth(150)
        wallpaper_btn.clicked.connect(self.choose_and_crop_wallpaper)
        path_layout.addWidget(self.wallpaper_label)
        path_layout.addWidget(wallpaper_btn)
        wallpaper_section.addLayout(path_layout)

        # 壁纸透明度
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

        # 个性化标语
        slogan_section = QVBoxLayout()
        sl_title = QLabel("个性化标语")
        sl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        slogan_section.addWidget(sl_title)

        slogan_input_layout = QHBoxLayout()
        self.slogan_edit = QLineEdit(self.dm.settings.get("slogan", "保持专注，更进一步"))
        self.show_slogan_cb = QCheckBox("显示")
        self.show_slogan_cb.setChecked(self.dm.settings.get("show_slogan", True))
        save_slogan_btn = QPushButton("保存")
        save_slogan_btn.setFixedWidth(80)
        save_slogan_btn.clicked.connect(self.save_slogan)
        slogan_input_layout.addWidget(self.slogan_edit)
        slogan_input_layout.addWidget(self.show_slogan_cb)
        slogan_input_layout.addWidget(save_slogan_btn)
        slogan_section.addLayout(slogan_input_layout)

        # 新增：标语样式设置（正体/斜体）
        slogan_style_layout = QHBoxLayout()
        slogan_style_layout.addWidget(QLabel("标语样式:"))

        self.italic_cb = QCheckBox("使用斜体")
        self.italic_cb.setChecked(self.dm.settings.get("slogan_italic", True))
        self.italic_cb.setToolTip("勾选使用斜体，取消勾选使用正体")
        slogan_style_layout.addWidget(self.italic_cb)

        slogan_style_layout.addStretch()
        slogan_section.addLayout(slogan_style_layout)

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

        # 版本信息
        layout.addStretch()
        version_label = QLabel(f"StudyTimer v{self.dm.VERSION}")
        version_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def choose_and_crop_wallpaper(self):
        """选择图片并调用裁剪器，保存裁剪后的壁纸"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择壁纸图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_path:
            return
        # 实例化裁剪器
        cropper = ImageCropper(file_path, self)
        if cropper.exec() == QDialog.DialogCode.Accepted:
            # 获取裁剪后的图片
            cropped_pix = cropper.get_cropped_pixmap()
            if cropped_pix.isNull():
                QMessageBox.warning(self, "错误", "裁剪失败，图片无效！")
                return
            # 保存裁剪后的壁纸（同目录下current_wallpaper.png）
            save_dir = os.path.dirname(os.path.abspath(self.dm.storage_path))
            if not save_dir:
                save_dir = os.getcwd()
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, "current_wallpaper.png")
            # 覆盖保存
            if cropped_pix.save(save_path, "PNG", quality=95):
                self.dm.settings["wallpaper"] = save_path
                self.dm.settings["wallpaper_opacity"] = self.dm.settings.get("wallpaper_opacity", 100)
                self.dm.save_data()
                self.wallpaper_label.setText(f"当前壁纸: current_wallpaper.png")
                if hasattr(self.main_window, 'update_wallpaper'):
                    self.main_window.update_wallpaper()
                else:
                    self.main_window.repaint()
                QMessageBox.information(self, "成功", "壁纸裁剪并设置完成！")
            else:
                QMessageBox.warning(self, "错误", "壁纸保存失败，请检查目录权限！")

    def update_opacity(self, value):
        """更新壁纸透明度"""
        self.dm.settings["wallpaper_opacity"] = value
        self.opacity_val_label.setText(f"{value}%")
        self.dm.save_data()
        self.main_window.update()

    def save_slogan(self):
        """保存标语设置"""
        self.dm.settings["slogan"] = self.slogan_edit.text().strip()
        self.dm.settings["show_slogan"] = self.show_slogan_cb.isChecked()
        self.dm.settings["slogan_italic"] = self.italic_cb.isChecked()  # 保存斜体设置
        self.dm.save_data()
        # 实时更新计时器页面的标语
        self.main_window.timer_page.slogan_label.setText(self.dm.settings["slogan"])
        self.main_window.timer_page.slogan_label.setVisible(self.dm.settings["show_slogan"])
        # 更新标语样式
        self._update_slogan_style()
        QMessageBox.information(self, "提示", "标语设置已保存！")

    def _update_slogan_style(self):
        """更新标语的字体样式（正体/斜体）"""
        is_italic = self.dm.settings.get("slogan_italic", True)
        slogan_label = self.main_window.timer_page.slogan_label

        # 获取当前样式表
        current_style = slogan_label.styleSheet()

        # 构建新的样式表，根据设置添加或移除 font-style
        if is_italic:
            font_style = "font-style: italic;"
        else:
            font_style = "font-style: normal;"

        # 更新样式
        slogan_label.setStyleSheet(f"""
            font-size: 28px; 
            color: #2c3e50; 
            font-family: 'Microsoft YaHei'; 
            {font_style}
            margin-bottom: 30px;
            background-color: rgba(255, 255, 255, 120);
            padding: 10px;
            border-radius: 10px;
        """)

    def export_records(self):
        """导出学习记录"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出记录", "study_timer_records.json",
            "JSON 文件 (*.json)"
        )
        if file_path:
            self.dm.export_data(file_path)
            QMessageBox.information(self, "成功", f"数据已导出至：{file_path}")

    def import_records(self):
        """导入学习记录"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入记录", "",
            "JSON 文件 (*.json)"
        )
        if file_path:
            if self.dm.import_data(file_path):
                QMessageBox.information(self, "成功", "数据导入成功！")
                # 刷新统计页面
                self.main_window.stats_page.update_charts()
            else:
                QMessageBox.warning(self, "错误", "导入失败！请检查文件格式是否正确。")