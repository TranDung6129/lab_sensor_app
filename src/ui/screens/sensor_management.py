from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QLineEdit, QFormLayout, QMessageBox,
                           QGroupBox, QDialog, QDialogButtonBox, QHeaderView,
                           QSpacerItem, QSizePolicy, QGridLayout, QTextEdit,
                           QMenu, QAction, QSplitter) # Thêm QMenu, QAction, QSplitter
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal # Thêm QPoint và pyqtSignal
from PyQt5.QtGui import QIcon # Tùy chọn: thêm icon cho action
import logging
import psutil
import json # Để hiển thị dữ liệu raw
import uuid # Để tạo ID tự động
import pyqtgraph as pg # Để vẽ đồ thị

logger = logging.getLogger(__name__)

# --- Dialog Chi tiết Cảm biến (SensorDetailDialog) ---
class SensorDetailDialog(QDialog):
    """Dialog to display detailed sensor information, including raw data."""
    def __init__(self, sensor_info, sensor_data_raw, parent=None):
        super().__init__(parent)
        sensor_name = sensor_info.get('config', {}).get('name', sensor_info.get('id', 'N/A'))
        self.setWindowTitle(f"Chi tiết Cảm biến: {sensor_name}")
        self.setMinimumSize(550, 450)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.addRow("ID Cảm biến:", QLabel(str(sensor_info.get('id', 'N/A'))))
        form_layout.addRow("Tên Cảm biến:", QLabel(str(sensor_name)))
        form_layout.addRow("Loại Cảm biến:", QLabel(str(sensor_info.get('type', 'N/A'))))
        form_layout.addRow("Trạng thái:", QLabel("Đã kết nối" if sensor_info.get('connected') else "Chưa kết nối"))
        
        config = sensor_info.get('config', {})
        form_layout.addRow("Giao thức:", QLabel(str(config.get('protocol', 'N/A'))))
        form_layout.addRow("Cổng/Địa chỉ:", QLabel(str(config.get('port_address', 'N/A'))))
        
        for key, value in config.items():
            if key not in ['protocol', 'port_address', 'name']:
                 form_layout.addRow(f"Cấu hình ({key}):", QLabel(str(value)))
        layout.addLayout(form_layout)

        data_group = QGroupBox("Dữ liệu Raw Gần nhất")
        data_layout = QVBoxLayout(data_group)
        self.raw_data_display = QTextEdit()
        self.raw_data_display.setReadOnly(True)
        self.raw_data_display.setFontFamily("Courier New") # Font cho dữ liệu raw
        
        if sensor_data_raw:
            try:
                # Hiển thị dạng JSON đẹp
                pretty_json = json.dumps(sensor_data_raw, indent=4, ensure_ascii=False)
                self.raw_data_display.setText(pretty_json)
            except TypeError:
                self.raw_data_display.setText(str(sensor_data_raw)) # Nếu không phải dict/list
        else:
            self.raw_data_display.setText("Không có dữ liệu gần nhất hoặc cảm biến chưa kết nối.")
            
        data_layout.addWidget(self.raw_data_display)
        layout.addWidget(data_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

# --- Dialog Thêm Cảm biến (AddSensorDialog) ---
class AddSensorDialog(QDialog):
    """Dialog for adding and configuring a new sensor."""
    def __init__(self, sensor_manager, parent=None):
        super().__init__(parent)
        self.sensor_manager = sensor_manager
        self.setWindowTitle("Thêm Cảm biến Mới")
        self.setMinimumWidth(450)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout() # Dùng form layout chính

        # Tên cảm biến
        self.sensor_name_input = QLineEdit()
        self.sensor_name_input.setPlaceholderText("Ví dụ: Cảm biến nhiệt phòng lab")
        self.form_layout.addRow("Tên Cảm biến (*):", self.sensor_name_input)

        # ID Cảm biến
        self.sensor_id_input = QLineEdit()
        self.sensor_id_input.setPlaceholderText("Để trống để tự tạo ID duy nhất")
        self.form_layout.addRow("ID Cảm biến:", self.sensor_id_input)

        # Loại cảm biến
        self.sensor_type_combo = QComboBox()
        if self.sensor_manager:
            self.sensor_type_combo.addItems(self.sensor_manager.get_available_sensor_types())
        self.sensor_type_combo.currentTextChanged.connect(self._update_specific_config_fields)
        self.form_layout.addRow("Loại Cảm biến (*):", self.sensor_type_combo)

        # Giao thức kết nối
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["UART", "TCP/IP", "UDP", "Bluetooth", "Mock"]) 
        self.protocol_combo.currentTextChanged.connect(self._update_connection_fields)
        self.form_layout.addRow("Giao thức Kết nối (*):", self.protocol_combo)
        
        # GroupBox cho cấu hình kết nối (động)
        self.connection_details_group = QGroupBox("Chi tiết Kết nối Giao thức")
        self.connection_details_layout = QFormLayout()
        self.connection_details_group.setLayout(self.connection_details_layout)
        self.form_layout.addRow(self.connection_details_group)

        # GroupBox cho cấu hình đặc thù của loại cảm biến (động)
        self.specific_config_group = QGroupBox("Cấu hình Đặc thù Loại Cảm biến")
        self.specific_config_layout = QFormLayout()
        self.specific_config_group.setLayout(self.specific_config_layout)
        self.form_layout.addRow(self.specific_config_group)
        
        # Tốc độ lấy mẫu chung
        self.sampling_rate_input = QLineEdit()
        self.sampling_rate_input.setPlaceholderText("Ví dụ: 100 (Hz), nếu cảm biến hỗ trợ")
        self.form_layout.addRow("Tốc độ lấy mẫu (Hz):", self.sampling_rate_input)

        self.layout.addLayout(self.form_layout)

        # Nút OK và Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_and_validate)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.current_connection_widgets = {}
        self.current_specific_config_widgets = {}

        self._update_connection_fields() # Khởi tạo các trường kết nối
        self._update_specific_config_fields() # Khởi tạo các trường cấu hình đặc thù

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout) # Đệ quy xóa layout con

    def _update_connection_fields(self):
        self._clear_layout(self.connection_details_layout)
        self.current_connection_widgets.clear()
        protocol = self.protocol_combo.currentText()

        if protocol == "UART":
            self.port_input = QLineEdit()
            self.port_input.setPlaceholderText("Ví dụ: COM3 hoặc /dev/ttyUSB0")
            self.connection_details_layout.addRow("Cổng COM (*):", self.port_input)
            self.current_connection_widgets['port'] = self.port_input
            
            self.baudrate_input = QComboBox()
            self.baudrate_input.addItems(["9600", "19200", "38400", "57600", "115200"])
            self.baudrate_input.setCurrentText("115200")
            self.connection_details_layout.addRow("Tốc độ Baud (*):", self.baudrate_input)
            self.current_connection_widgets['baudrate'] = self.baudrate_input
        elif protocol in ["TCP/IP", "UDP"]:
            self.ip_address_input = QLineEdit()
            self.ip_address_input.setPlaceholderText("Ví dụ: 192.168.1.100")
            self.connection_details_layout.addRow("Địa chỉ IP (*):", self.ip_address_input)
            self.current_connection_widgets['ip_address'] = self.ip_address_input
            
            self.port_number_input = QLineEdit()
            self.port_number_input.setPlaceholderText("Ví dụ: 8080")
            self.connection_details_layout.addRow("Cổng (*):", self.port_number_input)
            self.current_connection_widgets['port_number'] = self.port_number_input
        elif protocol == "Bluetooth":
            self.mac_address_input = QLineEdit()
            self.mac_address_input.setPlaceholderText("Ví dụ: 00:1A:2B:3C:4D:5E")
            self.connection_details_layout.addRow("Địa chỉ MAC (*):", self.mac_address_input)
            self.current_connection_widgets['mac_address'] = self.mac_address_input
        elif protocol == "Mock":
             self.connection_details_layout.addRow(QLabel("Cảm biến Mock không yêu cầu chi tiết kết nối."))
        self.connection_details_group.setVisible(self.connection_details_layout.rowCount() > 0)


    def _update_specific_config_fields(self):
        self._clear_layout(self.specific_config_layout)
        self.current_specific_config_widgets.clear()
        sensor_type = self.sensor_type_combo.currentText()

        if sensor_type == "accelerometer":
            self.accel_range_input = QComboBox()
            self.accel_range_input.addItems(["±2g", "±4g", "±8g", "±16g"])
            self.specific_config_layout.addRow("Dải đo (Range):", self.accel_range_input)
            self.current_specific_config_widgets['range'] = self.accel_range_input
        elif sensor_type == "temperature":
            self.temp_unit_input = QComboBox()
            self.temp_unit_input.addItems(["Celsius", "Fahrenheit", "Kelvin"])
            self.specific_config_layout.addRow("Đơn vị (Unit):", self.temp_unit_input)
            self.current_specific_config_widgets['unit'] = self.temp_unit_input
        # Thêm các loại cảm biến khác nếu có
        self.specific_config_group.setVisible(self.specific_config_layout.rowCount() > 0)


    def accept_and_validate(self):
        if not self.sensor_name_input.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên Cảm biến.")
            return
        # Thêm các kiểm tra khác cho các trường bắt buộc dựa trên protocol
        protocol = self.protocol_combo.currentText()
        if protocol == "UART":
            if not self.current_connection_widgets['port'].text().strip():
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Cổng COM cho UART.")
                return
        elif protocol in ["TCP/IP", "UDP"]:
            if not self.current_connection_widgets['ip_address'].text().strip() or \
               not self.current_connection_widgets['port_number'].text().strip():
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ IP và Cổng.")
                return
        # ... các kiểm tra khác ...
        self.accept()


    def get_sensor_config(self):
        sensor_name = self.sensor_name_input.text().strip()
        sensor_id = self.sensor_id_input.text().strip()
        if not sensor_id:
            sensor_id = f"{self.sensor_type_combo.currentText().upper()}_{uuid.uuid4().hex[:6].upper()}"

        config = {
            "name": sensor_name,
            "protocol": self.protocol_combo.currentText()
        }

        protocol = config["protocol"]
        if protocol == "UART":
            config['port_address'] = self.current_connection_widgets['port'].text().strip()
            config['baudrate'] = int(self.current_connection_widgets['baudrate'].currentText())
        elif protocol in ["TCP/IP", "UDP"]:
            ip = self.current_connection_widgets['ip_address'].text().strip()
            port_num = self.current_connection_widgets['port_number'].text().strip()
            config['port_address'] = f"{ip}:{port_num}"
        elif protocol == "Bluetooth":
            config['port_address'] = self.current_connection_widgets['mac_address'].text().strip()
        
        sensor_type = self.sensor_type_combo.currentText()
        if sensor_type == "accelerometer" and 'range' in self.current_specific_config_widgets:
            config["range"] = self.current_specific_config_widgets['range'].currentText()
        elif sensor_type == "temperature" and 'unit' in self.current_specific_config_widgets:
            config["unit"] = self.current_specific_config_widgets['unit'].currentText()

        sr_text = self.sampling_rate_input.text().strip()
        if sr_text:
            try:
                config["sampling_rate"] = float(sr_text)
            except ValueError:
                # Bỏ qua nếu không hợp lệ, hoặc thông báo lỗi nếu đây là trường bắt buộc
                logger.warning(f"Giá trị tốc độ lấy mẫu không hợp lệ: {sr_text}")
        
        return sensor_id, self.sensor_type_combo.currentText(), config


# --- Màn hình Quản lý Cảm biến Chính (SensorManagementScreen) ---
class SensorManagementScreen(QWidget):
    sensor_selected = pyqtSignal(str)  # Signal emitted when a sensor is selected
    
    def __init__(self, sensor_manager, sensor_processor):
        super().__init__()
        self.sensor_manager = sensor_manager
        self.sensor_processor = sensor_processor
        
        self.cpu_data = []
        self.mem_data = []
        self.time_data = []
        self.max_data_points = 100 # Số điểm dữ liệu hiển thị trên đồ thị

        self.setup_ui()
        self.update_sensors_table()

        self.resource_update_timer = QTimer(self)
        self.resource_update_timer.timeout.connect(self.update_resource_graphs_and_stats)
        self.resource_update_timer.start(1000) # Cập nhật mỗi giây cho đồ thị tài nguyên

        self.table_update_timer = QTimer(self) # Timer riêng cho bảng
        self.table_update_timer.timeout.connect(self.update_sensors_table_if_needed)
        self.table_update_timer.start(2500)


    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Nút "Thêm Cảm biến" ở trên cùng
        add_sensor_button = QPushButton(QIcon.fromTheme("list-add"), "Thêm Cảm biến Mới") # Tùy chọn icon
        add_sensor_button.setStyleSheet("padding: 8px 15px; font-size: 14px; background-color: #27ae60; color: white; border-radius: 3px;")
        add_sensor_button.clicked.connect(self.open_add_sensor_dialog)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(add_sensor_button)
        top_bar_layout.addStretch()
        main_layout.addLayout(top_bar_layout)

        # Sử dụng QSplitter để chia màn hình
        splitter = QSplitter(Qt.Vertical)

        # Phần bảng danh sách cảm biến
        sensors_list_group = QGroupBox("Danh sách Cảm biến")
        sensors_list_layout = QVBoxLayout(sensors_list_group)
        self.sensors_table = QTableWidget()
        self.sensors_table.setColumnCount(6)
        self.sensors_table.setHorizontalHeaderLabels(["Tên Cảm biến", "ID", "Loại", "Giao thức", "Trạng thái", "Hành động"])
        self.sensors_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sensors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sensors_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sensors_table.setContextMenuPolicy(Qt.CustomContextMenu) # Bật context menu
        self.sensors_table.customContextMenuRequested.connect(self.show_table_context_menu)
        sensors_list_layout.addWidget(self.sensors_table)
        splitter.addWidget(sensors_list_group)

        # Phần đồ thị và thống kê
        resources_stats_group = QGroupBox("Tài nguyên Hệ thống và Thống kê Cảm biến")
        resources_stats_layout = QGridLayout(resources_stats_group) # Sử dụng GridLayout

        # Đồ thị CPU
        self.cpu_plot_widget = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot_widget.setLabel('left', '% CPU')
        self.cpu_plot_widget.setLabel('bottom', 'Thời gian (s)')
        self.cpu_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot_widget.plot(pen='r')
        resources_stats_layout.addWidget(self.cpu_plot_widget, 0, 0)

        # Đồ thị Memory
        self.mem_plot_widget = pg.PlotWidget(title="Memory Usage (%)")
        self.mem_plot_widget.setLabel('left', '% RAM')
        self.mem_plot_widget.setLabel('bottom', 'Thời gian (s)')
        self.mem_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.mem_curve = self.mem_plot_widget.plot(pen='b')
        resources_stats_layout.addWidget(self.mem_plot_widget, 0, 1)

        # Thống kê cảm biến (dạng label)
        stats_frame = QFrame()
        stats_layout = QFormLayout(stats_frame)
        self.connected_sensors_label = QLabel("0")
        self.data_rate_label = QLabel("0 FPS") # Hoặc "0 Data Points/s"
        stats_layout.addRow("Số cảm biến đã kết nối:", self.connected_sensors_label)
        stats_layout.addRow("Tốc độ dữ liệu tổng hợp:", self.data_rate_label)
        resources_stats_layout.addWidget(stats_frame, 1, 0, 1, 2) # Kéo dài qua 2 cột đồ thị

        splitter.addWidget(resources_stats_group)
        
        splitter.setSizes([int(self.height() * 0.4), int(self.height() * 0.6)]) # Tỷ lệ ban đầu

        main_layout.addWidget(splitter)

    def open_add_sensor_dialog(self):
        dialog = AddSensorDialog(self.sensor_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            sensor_id, sensor_type, config = dialog.get_sensor_config()
            logger.debug(f"Dialog accepted. Adding sensor with ID: {sensor_id}, Type: {sensor_type}, Config: {config}")
            
            if self.sensor_manager and sensor_id in self.sensor_manager.sensors:
                 QMessageBox.warning(self, "Lỗi", f"ID Cảm biến '{sensor_id}' đã tồn tại. Vui lòng chọn ID khác.")
                 return

            if self.sensor_manager:
                if self.sensor_manager.add_sensor(sensor_id, config.get('name', sensor_id), sensor_type, config):
                    if self.sensor_processor:
                        sensor_info_for_processor = self.sensor_manager.get_sensor_info(sensor_id)
                        self.sensor_processor.add_sensor(sensor_id, sensor_info_for_processor)
                    self.update_sensors_table()
                    QMessageBox.information(self, "Thành công", f"Đã thêm cảm biến '{config.get('name', sensor_id)}'.")
                else:
                    QMessageBox.warning(self, "Lỗi", f"Không thể thêm hoặc kết nối cảm biến '{config.get('name', sensor_id)}'. Kiểm tra logs.")
            else:
                QMessageBox.critical(self, "Lỗi nghiêm trọng", "SensorManager chưa được khởi tạo.")
        else:
            logger.debug("AddSensorDialog cancelled by user.")


    def show_table_context_menu(self, position: QPoint):
        selected_items = self.sensors_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row() # Lấy hàng của item đầu tiên được chọn
        sensor_id_item = self.sensors_table.item(row, 1) # ID ở cột 1
        if not sensor_id_item:
            return
        
        sensor_id = sensor_id_item.text()

        menu = QMenu()
        # icon_detail = QIcon.fromTheme("document-properties") # Tùy chọn
        detail_action = QAction("Xem Chi tiết", self) # Thêm icon nếu muốn: QAction(icon_detail, "Xem Chi tiết", self)
        detail_action.triggered.connect(lambda: self.show_sensor_detail_for_id(sensor_id))
        menu.addAction(detail_action)
        
        # Thêm action "Xóa"
        # icon_delete = QIcon.fromTheme("edit-delete") # Tùy chọn
        delete_action = QAction("Xóa Cảm biến", self)
        delete_action.triggered.connect(lambda: self.remove_sensor(sensor_id))
        menu.addAction(delete_action)

        menu.exec_(self.sensors_table.viewport().mapToGlobal(position))

    def show_sensor_detail_for_id(self, sensor_id: str):
        if self.sensor_manager and sensor_id in self.sensor_manager.sensors:
            sensor_instance = self.sensor_manager.sensors[sensor_id]
            sensor_info = sensor_instance.get_sensor_info()
            sensor_data_raw = sensor_instance.last_data 
                                     
            dialog = SensorDetailDialog(sensor_info, sensor_data_raw, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thông tin cho cảm biến ID: {sensor_id}")

    def remove_sensor(self, sensor_id: str):
        sensor_info = self.sensor_manager.get_sensor_info(sensor_id) if self.sensor_manager else {}
        sensor_name = sensor_info.get('config', {}).get('name', sensor_id)
        
        reply = QMessageBox.question(self, 'Xác nhận Xóa', 
                                     f"Bạn có chắc chắn muốn xóa cảm biến '{sensor_name}' (ID: {sensor_id}) không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        if self.sensor_manager:
            if self.sensor_manager.remove_sensor(sensor_id):
                if self.sensor_processor:
                    self.sensor_processor.remove_sensor(sensor_id)
                self.update_sensors_table()
                QMessageBox.information(self, "Thành công", f"Đã xóa cảm biến '{sensor_name}'.")
            else:
                QMessageBox.warning(self, "Lỗi", f"Không thể xóa cảm biến '{sensor_id}'.")
        else:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", "SensorManager chưa được khởi tạo.")

    def update_sensors_table_if_needed(self):
        if not self.sensor_manager: return
        
        current_ids_in_table = {self.sensors_table.item(row, 1).text() for row in range(self.sensors_table.rowCount())}
        manager_ids = set(self.sensor_manager.sensors.keys())

        if current_ids_in_table != manager_ids:
            self.update_sensors_table()
            return

        for row in range(self.sensors_table.rowCount()):
            sensor_id = self.sensors_table.item(row, 1).text()
            sensor = self.sensor_manager.sensors.get(sensor_id)
            if sensor:
                current_status_in_table = self.sensors_table.item(row, 4).text()
                actual_status = "Đã kết nối" if sensor.connected else "Chưa kết nối"
                if current_status_in_table != actual_status:
                    self.update_sensors_table()
                    return
    
    def update_sensors_table(self):
        if not self.sensor_manager:
            self.sensors_table.setRowCount(0)
            return
            
        self.sensors_table.setRowCount(0) 
        
        for sensor_id, sensor_instance in self.sensor_manager.sensors.items():
            sensor_info = sensor_instance.get_sensor_info()
            config = sensor_info.get('config', {})
            row = self.sensors_table.rowCount()
            self.sensors_table.insertRow(row)
            
            self.sensors_table.setItem(row, 0, QTableWidgetItem(str(config.get('name', sensor_id))))
            self.sensors_table.setItem(row, 1, QTableWidgetItem(str(sensor_id)))
            self.sensors_table.setItem(row, 2, QTableWidgetItem(str(sensor_info.get('type', 'N/A'))))
            self.sensors_table.setItem(row, 3, QTableWidgetItem(str(config.get('protocol', 'N/A'))))
            
            status = "Đã kết nối" if sensor_instance.connected else "Chưa kết nối"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.darkGreen if sensor_instance.connected else Qt.red)
            self.sensors_table.setItem(row, 4, status_item)
            
            # Không thêm nút Xóa trực tiếp vào bảng nữa, dùng context menu
            # Để giữ cột "Hành động" cho trực quan, có thể để trống hoặc một label nhỏ
            action_placeholder = QLabel("...") 
            action_placeholder.setAlignment(Qt.AlignCenter)
            self.sensors_table.setCellWidget(row, 5, action_placeholder)


        self.sensors_table.resizeColumnsToContents()
        self.sensors_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sensors_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        # Connect selection changed signal
        self.sensors_table.itemSelectionChanged.connect(self.on_sensor_selection_changed)

    def on_sensor_selection_changed(self):
        """Handle sensor selection change in the table."""
        selected_items = self.sensors_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            sensor_id_item = self.sensors_table.item(row, 1)
            if sensor_id_item:
                sensor_id = sensor_id_item.text()
                self.sensor_selected.emit(sensor_id)

    def update_resource_graphs_and_stats(self):
        # Cập nhật đồ thị tài nguyên
        current_time = len(self.time_data) # Đơn giản hóa trục x là số điểm dữ liệu
        
        self.cpu_data.append(psutil.cpu_percent())
        self.mem_data.append(psutil.virtual_memory().percent)
        self.time_data.append(current_time)

        if len(self.time_data) > self.max_data_points:
            self.time_data.pop(0)
            self.cpu_data.pop(0)
            self.mem_data.pop(0)
        
        self.cpu_curve.setData(self.time_data, self.cpu_data)
        self.mem_curve.setData(self.time_data, self.mem_data)

        # Cập nhật thống kê cảm biến
        if self.sensor_manager:
            connected_count = sum(1 for s in self.sensor_manager.sensors.values() if s.connected)
            self.connected_sensors_label.setText(str(connected_count))
        
        if self.sensor_processor:
            # Giả sử sensor_processor có phương thức get_aggregate_fps() hoặc tương tự
            # Nếu không, bạn cần tính toán dựa trên logic cập nhật dữ liệu
            fps = self.sensor_processor.get_fps() # Sử dụng lại get_fps nếu nó là tổng hợp
            self.data_rate_label.setText(f"{fps:.1f} FPS")


    def closeEvent(self, event):
        self.resource_update_timer.stop()
        self.table_update_timer.stop()
        event.accept()