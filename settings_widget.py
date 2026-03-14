import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QLineEdit, QCheckBox, QMessageBox,
                             QSlider, QDialog, QScrollArea, QFrame, QInputDialog)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import (QPixmap, QPainter, QPen, QColor, QBrush,
                         QCursor)


class ImageCropper(QDialog):
    """仿QQ/微信截图：直接在对话框上绘制，实现外部暗化+选区高亮，增加滚动支持以适配长图"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("裁剪壁纸 - 拖动鼠标选择区域")
        self.setModal(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # 加载原始图片
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            QMessageBox.warning(self, "错误", "图片加载失败！")
            self.reject()
            return

        # 限制显示尺寸，避免窗口过大
        screen = self.screen().availableGeometry()
        max_w, max_h = int(screen.width() * 0.8), int(screen.height() * 0.7)

        self.display_pixmap = self.original_pixmap.scaled(
            max_w, max_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.scale_w = self.original_pixmap.width() / self.display_pixmap.width()
        self.scale_h = self.original_pixmap.height() / self.display_pixmap.height()

        # 图片在绘图区域中的位置
        self.pic_rect = QRect(0, 0, self.display_pixmap.width(), self.display_pixmap.height())

        # 裁剪状态变量
        self.start_point = QPoint(0, 0)
        self.end_point = QPoint(0, 0)
        self.selection_rect = QRect()
        self.is_selecting = False
        self.min_size = 40
        self.use_full_image = False

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 提示信息
        tip = QLabel("✨ 操作：拖动鼠标选择区域 | 选区高亮，其他区域暗化")
        tip.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(tip)

        # 绘图区域（使用 ScrollArea 包裹以防万一）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = QLabel()
        self.canvas.setFixedSize(self.display_pixmap.size())
        self.canvas.installEventFilter(self)

        self.scroll_area.setWidget(self.canvas)
        main_layout.addWidget(self.scroll_area)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.apply_full_btn = QPushButton("📄 直接应用")
        self.confirm_crop_btn = QPushButton("✂️ 确认裁剪")
        self.cancel_btn = QPushButton("❌ 取消")

        for btn in [self.apply_full_btn, self.confirm_crop_btn, self.cancel_btn]:
            btn.setMinimumHeight(40)
            btn.setStyleSheet("font-weight: bold; border-radius: 5px; padding: 5px 15px;")

        self.apply_full_btn.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; border-radius: 5px;")
        self.confirm_crop_btn.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold; border-radius: 5px;")
        self.cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; border-radius: 5px;")

        self.apply_full_btn.clicked.connect(self._on_apply_full)
        self.confirm_crop_btn.clicked.connect(self._on_accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_full_btn)
        btn_layout.addWidget(self.confirm_crop_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def eventFilter(self, obj, event):
        if obj == self.canvas:
            if event.type() == event.Type.MouseButtonPress:
                self.start_point = event.pos()
                self.selection_rect = QRect()
                self.is_selecting = True
                self.canvas.update()
                return True
            elif event.type() == event.Type.MouseMove and self.is_selecting:
                self.end_point = event.pos()
                # 限制在图片范围内
                self.end_point.setX(max(0, min(self.end_point.x(), self.pic_rect.width())))
                self.end_point.setY(max(0, min(self.end_point.y(), self.pic_rect.height())))
                self.selection_rect = QRect(self.start_point, self.end_point).normalized()
                self.canvas.update()
                return True
            elif event.type() == event.Type.MouseButtonRelease:
                self.is_selecting = False
                return True
            elif event.type() == event.Type.Paint:
                painter = QPainter(self.canvas)
                # 1. 绘制图片
                painter.drawPixmap(0, 0, self.display_pixmap)

                # 2. 绘制暗化遮罩
                mask_color = QColor(0, 0, 0, 150)
                if self.selection_rect.isValid():
                    # 复杂的遮罩绘制，避开选区
                    painter.setBrush(QBrush(mask_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    # 上
                    painter.drawRect(0, 0, self.pic_rect.width(), self.selection_rect.top())
                    # 下
                    painter.drawRect(0, self.selection_rect.bottom(), self.pic_rect.width(),
                                     self.pic_rect.height() - self.selection_rect.bottom())
                    # 左
                    painter.drawRect(0, self.selection_rect.top(), self.selection_rect.left(),
                                     self.selection_rect.height())
                    # 右
                    painter.drawRect(self.selection_rect.right(), self.selection_rect.top(),
                                     self.pic_rect.width() - self.selection_rect.right(), self.selection_rect.height())

                    # 3. 绘制选区边框
                    border_pen = QPen(QColor("#3498db"), 2, Qt.PenStyle.SolidLine)
                    painter.setPen(border_pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(self.selection_rect)
                else:
                    # 全图暗化
                    painter.fillRect(self.pic_rect, mask_color)
                return True
        return super().eventFilter(obj, event)

    def _on_apply_full(self):
        self.use_full_image = True
        self.accept()

    def _on_accept(self):
        if not self.selection_rect.isValid() or self.selection_rect.width() < self.min_size:
            QMessageBox.warning(self, "提示", "请选择有效的裁剪区域！")
            return
        self.use_full_image = False
        self.accept()

    def get_cropped_pixmap(self):
        if self.use_full_image:
            return self.original_pixmap

        real_rect = QRect(
            int(self.selection_rect.x() * self.scale_w),
            int(self.selection_rect.y() * self.scale_h),
            int(self.selection_rect.width() * self.scale_w),
            int(self.selection_rect.height() * self.scale_h)
        )
        return self.original_pixmap.copy(real_rect)


class SettingsWidget(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.dm = data_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background-color: rgba(255, 255, 255, 180); border-radius: 20px;")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        # 1. 壁纸设置
        content_layout.addWidget(self.create_section_title("🖼️ 壁纸与外观"))
        wp_layout = QHBoxLayout()
        self.wp_label = QLabel(f"当前壁纸: {os.path.basename(self.dm.settings.get('wallpaper', '默认'))}")
        wp_btn = QPushButton("选择并裁剪壁纸")
        wp_btn.clicked.connect(self.choose_and_crop_wallpaper)
        wp_layout.addWidget(self.wp_label)
        wp_layout.addWidget(wp_btn)
        content_layout.addLayout(wp_layout)

        content_layout.addWidget(QLabel("壁纸显示浓度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.dm.settings.get("wallpaper_opacity", 1.0) * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)

        opacity_info_layout = QHBoxLayout()
        opacity_info_layout.addWidget(self.opacity_slider)
        self.opacity_val_label = QLabel(f"{self.opacity_slider.value()}%")
        opacity_info_layout.addWidget(self.opacity_val_label)
        content_layout.addLayout(opacity_info_layout)

        # 2. 标签管理
        content_layout.addWidget(self.create_section_title("🏷️ 标签管理"))
        self.tag_list_label = QLabel(f"当前标签: {', '.join(self.dm.settings.get('tags', []))}")
        self.tag_list_label.setWordWrap(True)
        content_layout.addWidget(self.tag_list_label)

        tag_btn_layout = QHBoxLayout()
        add_tag_btn = QPushButton("新增标签")
        del_tag_btn = QPushButton("删除标签")
        add_tag_btn.clicked.connect(self.add_tag)
        del_tag_btn.clicked.connect(self.delete_tag)
        tag_btn_layout.addWidget(add_tag_btn)
        tag_btn_layout.addWidget(del_tag_btn)
        content_layout.addLayout(tag_btn_layout)

        # 3. 个性化标语
        content_layout.addWidget(self.create_section_title("✍️ 个性化标语"))
        slogan_layout = QHBoxLayout()
        self.slogan_edit = QLineEdit(self.dm.settings.get("slogan", ""))
        self.show_slogan_cb = QCheckBox("显示")
        self.show_slogan_cb.setChecked(self.dm.settings.get("show_slogan", True))
        save_slogan_btn = QPushButton("保存")
        save_slogan_btn.clicked.connect(self.save_slogan)
        slogan_layout.addWidget(self.slogan_edit)
        slogan_layout.addWidget(self.show_slogan_cb)
        slogan_layout.addWidget(save_slogan_btn)
        content_layout.addLayout(slogan_layout)

        # 4. 数据管理
        content_layout.addWidget(self.create_section_title("💾 数据管理"))
        db_layout = QHBoxLayout()
        export_btn = QPushButton("导出记录 (JSON)")
        import_btn = QPushButton("导入记录 (JSON)")
        export_btn.clicked.connect(self.export_records)
        import_btn.clicked.connect(self.import_records)
        db_layout.addWidget(export_btn)
        db_layout.addWidget(import_btn)
        content_layout.addLayout(db_layout)

        content_layout.addStretch()
        version_label = QLabel(f"软件版本: v{self.dm.VERSION}")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        content_layout.addWidget(version_label)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def create_section_title(self, text):
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px;")
        return label

    def choose_and_crop_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择壁纸", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            cropper = ImageCropper(file_path, self)
            if cropper.exec() == QDialog.DialogCode.Accepted:
                cropped_pixmap = cropper.get_cropped_pixmap()
                save_path = os.path.join(os.getcwd(), "current_wallpaper.png")
                cropped_pixmap.save(save_path, "PNG")
                self.dm.settings["wallpaper"] = save_path
                self.dm.save_data()
                self.wp_label.setText(f"当前壁纸: {os.path.basename(save_path)}")
                self.settings_changed.emit()

    def update_opacity(self, value):
        self.dm.settings["wallpaper_opacity"] = value / 100.0
        self.opacity_val_label.setText(f"{value}%")
        self.dm.save_data()
        self.settings_changed.emit()

    def add_tag(self):
        tag, ok = QInputDialog.getText(self, "新增标签", "请输入标签名称:")
        if ok and tag:
            tags = self.dm.settings.get("tags", [])
            if tag not in tags:
                tags.append(tag)
                self.dm.settings["tags"] = tags
                self.dm.save_data()
                self.tag_list_label.setText(f"当前标签: {', '.join(tags)}")
                self.settings_changed.emit()

    def delete_tag(self):
        tags = self.dm.settings.get("tags", [])
        if len(tags) <= 1:
            QMessageBox.warning(self, "提示", "至少需要保留一个标签")
            return
        tag, ok = QInputDialog.getItem(self, "删除标签", "请选择要删除的标签:", tags, 0, False)
        if ok and tag:
            tags.remove(tag)
            self.dm.settings["tags"] = tags
            self.dm.save_data()
            self.tag_list_label.setText(f"当前标签: {', '.join(tags)}")
            self.settings_changed.emit()

    def save_slogan(self):
        self.dm.settings["slogan"] = self.slogan_edit.text()
        self.dm.settings["show_slogan"] = self.show_slogan_cb.isChecked()
        self.dm.save_data()
        self.settings_changed.emit()
        QMessageBox.information(self, "成功", "设置已保存")

    def export_records(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出记录", "study_records.json", "JSON (*.json)")
        if path:
            self.dm.export_data(path)
            QMessageBox.information(self, "成功", f"数据已导出至: {path}")

    def import_records(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入记录", "", "JSON (*.json)")
        if path:
            if self.dm.import_data(path):
                self.tag_list_label.setText(f"当前标签: {', '.join(self.dm.settings.get('tags', []))}")
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", "数据导入成功")
            else:
                QMessageBox.warning(self, "错误", "数据导入失败")