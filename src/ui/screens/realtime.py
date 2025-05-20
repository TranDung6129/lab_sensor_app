import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSlider,
                           QSpinBox, QDoubleSpinBox, QGroupBox, QDialog,
                           QListWidget, QListWidgetItem, QDialogButtonBox,
                           QInputDialog, QMessageBox, QSizePolicy, QSpacerItem,
                           QFileDialog)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea
import logging
from typing import Dict, List
from .realtime_plot_manager import RealtimePlotManager

logger = logging.getLogger(__name__)

class SelectDataKeyDialog(QDialog):
    """Dialog để chọn các kênh dữ liệu cho một biểu đồ."""
    def __init__(self, available_data_keys: Dict[str, str],
                 selected_keys: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn Kênh Dữ Liệu")
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        # Sắp xếp available_data_keys theo key (tên hiển thị)
        sorted_keys = sorted(available_data_keys.items())

        for display_name, data_key in sorted_keys:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, data_key) # Lưu data_key thực tế
            self.list_widget.addItem(item)
            if data_key in selected_keys:
                item.setSelected(True)
        
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_data_keys(self) -> List[str]:
        return [self.list_widget.item(i).data(Qt.UserRole) 
                for i in range(self.list_widget.count()) if self.list_widget.item(i).isSelected()]

class RealtimeScreen(QWidget):
    """Realtime data visualization screen with time-series plots."""
    
    # Mapping từ tên hiển thị sang data_key kỹ thuật
    CHANNEL_TO_DATA_KEY = {
        "Acceleration X": "accX",
        "Acceleration Y": "accY",
        "Acceleration Z": "accZ",
        "Angular Velocity X": "gyroX",
        "Angular Velocity Y": "gyroY",
        "Angular Velocity Z": "gyroZ",
        "Angle X": "angleX",
        "Angle Y": "angleY",
        "Angle Z": "angleZ"
    }
    
    def __init__(self, processor, sensor_manager):
        super().__init__()
        self.processor = processor
        self.sensor_manager = sensor_manager
        self.current_sensor_id = None
        self.available_data_keys_for_sensor: Dict[str, str] = {}

        self.setup_ui()
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_plots_data)
        self.ui_update_interval = 100
        self.update_timer.start(self.ui_update_interval)
        
        self.sensor_list_check_timer = QTimer(self)
        self.sensor_list_check_timer.timeout.connect(self.update_sensor_selection_combo)
        self.sensor_list_check_timer.start(2000)

        logger.info("RealtimeScreen initialized.")
        self.update_sensor_selection_combo()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0,0,0,0)

        toolbar_layout.addWidget(QLabel("Cảm biến:"))
        self.sensor_selection_combo = QComboBox()
        self.sensor_selection_combo.setMinimumWidth(200)
        self.sensor_selection_combo.currentTextChanged.connect(self.on_sensor_selected)
        toolbar_layout.addWidget(self.sensor_selection_combo)
        
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        self.add_plot_button = QPushButton("Thêm Biểu Đồ Mới")
        self.add_plot_button.clicked.connect(self.add_new_plot_interactive)
        toolbar_layout.addWidget(self.add_plot_button)

        self.manage_plots_button = QPushButton("Quản Lý Biểu Đồ")
        self.manage_plots_button.clicked.connect(self.open_plot_management_dialog)
        toolbar_layout.addWidget(self.manage_plots_button)
        
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        self.save_layout_button = QPushButton("Lưu Layout")
        self.save_layout_button.clicked.connect(self.save_current_layout)
        toolbar_layout.addWidget(self.save_layout_button)

        self.load_layout_button = QPushButton("Tải Layout")
        self.load_layout_button.clicked.connect(self.load_saved_layout)
        toolbar_layout.addWidget(self.load_layout_button)
        
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar_widget)

        self.dock_area = DockArea()
        main_layout.addWidget(self.dock_area)
        
        self.plot_manager = RealtimePlotManager(self.dock_area)

    def update_sensor_selection_combo(self):
        if not self.sensor_manager:
            logger.warning("SensorManager not available in RealtimeScreen.")
            self.sensor_selection_combo.clear()
            self.sensor_selection_combo.setEnabled(False)
            return

        active_sensors_info = self.sensor_manager.get_all_sensor_info()
        
        current_selected_id = self.sensor_selection_combo.currentData()
        
        new_sensor_ids = {s_info['id'] for s_info in active_sensors_info}
        old_sensor_ids = {self.sensor_selection_combo.itemData(i) for i in range(self.sensor_selection_combo.count())}

        if new_sensor_ids == old_sensor_ids and len(active_sensors_info) == self.sensor_selection_combo.count():
            return

        logger.debug(f"Updating sensor selection combobox. Found {len(active_sensors_info)} sensors.")
        self.sensor_selection_combo.blockSignals(True)
        self.sensor_selection_combo.clear()
        
        if not active_sensors_info:
            self.sensor_selection_combo.addItem("Không có cảm biến nào", None)
            self.sensor_selection_combo.setEnabled(False)
            self.current_sensor_id = None
            self.available_data_keys_for_sensor.clear()
            self.plot_manager.remove_all_plots()
        else:
            self.sensor_selection_combo.setEnabled(True)
            for sensor_info_dict in active_sensors_info:
                sensor_id = sensor_info_dict['id']
                sensor_name = sensor_info_dict.get('name', sensor_id)
                self.sensor_selection_combo.addItem(f"{sensor_name} ({sensor_id})", sensor_id)
            
            if current_selected_id and current_selected_id in new_sensor_ids:
                idx = self.sensor_selection_combo.findData(current_selected_id)
                if idx != -1:
                    self.sensor_selection_combo.setCurrentIndex(idx)
                else:
                    self.sensor_selection_combo.setCurrentIndex(0)
            elif self.sensor_selection_combo.count() > 0:
                 self.sensor_selection_combo.setCurrentIndex(0)
        
        self.sensor_selection_combo.blockSignals(False)
        if self.sensor_selection_combo.count() > 0 and self.sensor_selection_combo.currentData() is not None:
            self.on_sensor_selected(self.sensor_selection_combo.currentText())
        elif not active_sensors_info:
             self.on_sensor_selected("")

    def on_sensor_selected(self, selected_text: str):
        new_sensor_id = self.sensor_selection_combo.currentData()
        logger.info(f"Sensor selected in RealtimeScreen: '{selected_text}', ID: {new_sensor_id}")

        if self.current_sensor_id == new_sensor_id and new_sensor_id is not None:
            logger.debug(f"Sensor '{new_sensor_id}' already selected. No change needed.")
            return

        self.current_sensor_id = new_sensor_id
        self.available_data_keys_for_sensor.clear()

        if self.current_sensor_id and self.sensor_manager and self.processor:
            sensor_instance = self.sensor_manager.get_sensor_instance(self.current_sensor_id)
            if sensor_instance and hasattr(sensor_instance, 'get_available_data_keys'):
                data_keys_from_sensor = sensor_instance.get_available_data_keys()
                self.available_data_keys_for_sensor = {key: key for key in data_keys_from_sensor}
                logger.debug(f"Available data keys for sensor '{self.current_sensor_id}': {self.available_data_keys_for_sensor}")
            else:
                 logger.warning(f"Sensor instance for '{self.current_sensor_id}' not found or has no get_available_data_keys method.")
        
        self.plot_manager.remove_all_plots()
        self.update_plots_data()
        
    def add_default_plot_for_new_sensor(self):
        if not self.current_sensor_id or not self.available_data_keys_for_sensor:
            return

        default_plot_id = f"plot_{self.current_sensor_id}_default"
        default_title = f"Dữ liệu Cảm biến {self.sensor_selection_combo.currentText()}"
        
        created_plot = self.plot_manager.create_plot(default_plot_id, default_title)
        if created_plot:
            keys_to_plot = list(self.available_data_keys_for_sensor.values())[:3]
            for data_key in keys_to_plot:
                display_name = data_key
                self.plot_manager.add_curve(default_plot_id, data_key, display_name, y_label=f"{data_key}")
            logger.info(f"Added default plot '{default_plot_id}' for sensor '{self.current_sensor_id}'.")

    def add_new_plot_interactive(self):
        if not self.current_sensor_id:
            QMessageBox.warning(self, "Chưa chọn cảm biến", "Vui lòng chọn một cảm biến trước khi thêm biểu đồ.")
            return
            
        plot_id_suggestion = f"plot_{self.current_sensor_id}_{len(self.plot_manager.get_all_plot_ids()) + 1}"
        plot_id, ok = QInputDialog.getText(self, "Tạo Biểu Đồ Mới", "Nhập ID cho biểu đồ mới:", text=plot_id_suggestion)
        if ok and plot_id:
            if plot_id in self.plot_manager.get_all_plot_ids():
                QMessageBox.warning(self, "Lỗi", f"Plot ID '{plot_id}' đã tồn tại.")
                return

            plot_title, ok_title = QInputDialog.getText(self, "Tên Biểu Đồ", "Nhập tên (tiêu đề) cho biểu đồ:", text=f"Biểu đồ cho {plot_id}")
            if not ok_title or not plot_title:
                plot_title = plot_id

            existing_docks = self.plot_manager.get_all_plot_ids()
            relative_dock_id = None
            position = 'bottom'

            if existing_docks:
                relative_dock_id = existing_docks[-1]

            created_plot_widget = self.plot_manager.create_plot(plot_id, plot_title, position, 
                                                                self.plot_manager.get_dock_by_id(relative_dock_id) if relative_dock_id else None)
            
            if created_plot_widget:
                self.configure_plot_curves(plot_id)
            else:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo plot '{plot_id}'.")
        else:
            logger.debug("Add new plot cancelled by user or no ID entered.")

    def configure_plot_curves(self, plot_id: str):
        if not self.current_sensor_id or not self.available_data_keys_for_sensor:
            return

        dialog = SelectDataKeyDialog(self.available_data_keys_for_sensor, [], self)
        if dialog.exec_() == QDialog.Accepted:
            selected_keys = dialog.get_selected_data_keys()
            if selected_keys:
                for data_key in selected_keys:
                    display_name = data_key
                    self.plot_manager.add_curve(plot_id, data_key, display_name, y_label=f"{data_key}")
                logger.info(f"Added curves to plot '{plot_id}': {selected_keys}")
            else:
                logger.warning(f"No data keys selected for plot '{plot_id}'")
                self.plot_manager.remove_plot(plot_id)

    def open_plot_management_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Quản Lý Biểu Đồ")
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for plot_id in self.plot_manager.get_all_plot_ids():
            dock = self.plot_manager.get_dock_by_id(plot_id)
            if dock:
                item = QListWidgetItem(dock.title())
                item.setData(Qt.UserRole, plot_id)
                list_widget.addItem(item)

        layout.addWidget(list_widget)

        button_layout = QHBoxLayout()
        remove_button = QPushButton("Xóa Biểu Đồ")
        remove_button.clicked.connect(lambda: self.remove_selected_plot_from_dialog(list_widget, lambda: self.open_plot_management_dialog()))
        button_layout.addWidget(remove_button)

        restore_button = QPushButton("Khôi Phục Biểu Đồ")
        restore_button.clicked.connect(lambda: self.restore_selected_plot_from_dialog(list_widget, lambda: self.open_plot_management_dialog()))
        button_layout.addWidget(restore_button)

        layout.addLayout(button_layout)

        close_button = QPushButton("Đóng")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec_()

    def remove_selected_plot_from_dialog(self, list_widget: QListWidget, refresh_callback):
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn biểu đồ cần xóa.")
            return

        for item in selected_items:
            plot_id = item.data(Qt.UserRole)
            self.plot_manager.remove_plot(plot_id)
            list_widget.takeItem(list_widget.row(item))

        refresh_callback()

    def restore_selected_plot_from_dialog(self, list_widget: QListWidget, refresh_callback):
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn biểu đồ cần khôi phục.")
            return

        for item in selected_items:
            plot_id = item.data(Qt.UserRole)
            dock = self.plot_manager.get_dock_by_id(plot_id)
            if dock:
                dock.show()

        refresh_callback()

    def update_plots_data(self):
        if not self.current_sensor_id or not self.processor:
            return

        sensor_data = self.processor.get_sensor_data(self.current_sensor_id)
        if not sensor_data:
            return

        for plot_id in self.plot_manager.get_all_plot_ids():
            plot = self.plot_manager.get_plot_by_id(plot_id)
            if plot:
                for curve_id in self.plot_manager.get_curve_ids_for_plot(plot_id):
                    if curve_id in sensor_data:
                        data = sensor_data[curve_id]
                        if len(data) > 0:
                            self.plot_manager.update_curve_data(plot_id, curve_id, data)

    def save_current_layout(self):
        if not self.current_sensor_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn cảm biến trước khi lưu layout.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu Layout",
            f"layout_{self.current_sensor_id}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            self.plot_manager.save_layout(file_path)

    def load_saved_layout(self):
        if not self.current_sensor_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn cảm biến trước khi tải layout.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Tải Layout",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            self.plot_manager.load_layout(file_path)

    def closeEvent(self, event):
        self.update_timer.stop()
        self.sensor_list_check_timer.stop()
        super().closeEvent(event) 