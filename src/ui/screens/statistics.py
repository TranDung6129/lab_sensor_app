from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QFormLayout,
                           QGroupBox, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class StatisticsScreen(QWidget):
    def __init__(self, sensor_manager, sensor_processor):
        super().__init__()
        self.sensor_manager = sensor_manager
        self.sensor_processor = sensor_processor
        
        # Khởi tạo dữ liệu cho đồ thị
        self.max_data_points = 1000  # Số điểm dữ liệu tối đa hiển thị
        self.time_data = []
        self.sensor_data = {}  # Lưu trữ dữ liệu theo sensor_id
        self.last_update = datetime.now()
        self.selected_data_key = None  # Initialize selected_data_key
        
        self.setup_ui()
        
        # Timer để cập nhật dữ liệu
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Cập nhật mỗi giây

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Tạo tab widget để chứa các loại thống kê khác nhau
        self.tab_widget = QTabWidget()
        
        # Tab 1: Thống kê thời gian thực
        realtime_tab = QWidget()
        realtime_layout = QVBoxLayout(realtime_tab)
        
        # Phần chọn cảm biến và thời gian
        control_group = QGroupBox("Điều khiển")
        control_layout = QHBoxLayout()
        
        # Combo box chọn cảm biến
        self.sensor_combo = QComboBox()
        self.sensor_combo.currentTextChanged.connect(self.on_sensor_changed)
        control_layout.addWidget(QLabel("Chọn cảm biến:"))
        control_layout.addWidget(self.sensor_combo)
        
        # Combo box chọn khoảng thời gian
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["1 phút", "5 phút", "15 phút", "30 phút", "1 giờ"])
        self.time_range_combo.currentTextChanged.connect(self.on_time_range_changed)
        control_layout.addWidget(QLabel("Khoảng thời gian:"))
        control_layout.addWidget(self.time_range_combo)
        
        control_group.setLayout(control_layout)
        realtime_layout.addWidget(control_group)
        
        # Phần đồ thị
        plot_group = QGroupBox("Đồ thị dữ liệu")
        plot_layout = QVBoxLayout()
        
        # Tạo đồ thị
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Giá trị')
        self.plot_widget.setLabel('bottom', 'Thời gian')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen='b')
        
        plot_layout.addWidget(self.plot_widget)
        plot_group.setLayout(plot_layout)
        realtime_layout.addWidget(plot_group)
        
        # Phần thống kê
        stats_group = QGroupBox("Thống kê")
        stats_layout = QFormLayout()
        
        self.min_label = QLabel("0")
        self.max_label = QLabel("0")
        self.avg_label = QLabel("0")
        self.std_label = QLabel("0")
        
        stats_layout.addRow("Giá trị nhỏ nhất:", self.min_label)
        stats_layout.addRow("Giá trị lớn nhất:", self.max_label)
        stats_layout.addRow("Giá trị trung bình:", self.avg_label)
        stats_layout.addRow("Độ lệch chuẩn:", self.std_label)
        
        stats_group.setLayout(stats_layout)
        realtime_layout.addWidget(stats_group)
        
        # Thêm tab vào tab widget
        self.tab_widget.addTab(realtime_tab, "Thời gian thực")
        
        # Tab 2: Thống kê tổng hợp
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # Thêm các widget cho thống kê tổng hợp
        summary_group = QGroupBox("Thống kê tổng hợp")
        summary_form = QFormLayout()
        
        self.total_sensors_label = QLabel("0")
        self.active_sensors_label = QLabel("0")
        self.total_data_points_label = QLabel("0")
        self.avg_data_rate_label = QLabel("0 FPS")
        
        summary_form.addRow("Tổng số cảm biến:", self.total_sensors_label)
        summary_form.addRow("Số cảm biến đang hoạt động:", self.active_sensors_label)
        summary_form.addRow("Tổng số điểm dữ liệu:", self.total_data_points_label)
        summary_form.addRow("Tốc độ dữ liệu trung bình:", self.avg_data_rate_label)
        
        summary_group.setLayout(summary_form)
        summary_layout.addWidget(summary_group)
        
        self.tab_widget.addTab(summary_tab, "Tổng hợp")
        
        main_layout.addWidget(self.tab_widget)
        
        # Cập nhật danh sách cảm biến
        self.update_sensor_list()

    def update_sensor_list(self):
        """Cập nhật danh sách cảm biến trong combo box."""
        if not self.sensor_manager:
            return
            
        current_sensor = self.sensor_combo.currentText()
        self.sensor_combo.clear()
        
        for sensor_id, sensor in self.sensor_manager.sensors.items():
            sensor_name = sensor.get_sensor_info().get('config', {}).get('name', sensor_id)
            self.sensor_combo.addItem(f"{sensor_name} ({sensor_id})", sensor_id)
            
        # Khôi phục lựa chọn trước đó nếu có
        if current_sensor:
            index = self.sensor_combo.findText(current_sensor)
            if index >= 0:
                self.sensor_combo.setCurrentIndex(index)

    def on_sensor_changed(self, sensor_text):
        """Xử lý khi người dùng chọn cảm biến khác."""
        if not sensor_text:
            return
            
        sensor_id = self.sensor_combo.currentData()
        if sensor_id in self.sensor_data:
            self.update_plot(sensor_id)
        else:
            self.sensor_data[sensor_id] = []

    def on_time_range_changed(self, time_range):
        """Xử lý khi người dùng thay đổi khoảng thời gian."""
        self.update_plot(self.sensor_combo.currentData())

    def update_data(self):
        """Cập nhật dữ liệu từ cảm biến."""
        if not self.sensor_manager:
            return
            
        current_time = datetime.now()
        time_diff = (current_time - self.last_update).total_seconds()
        
        # Cập nhật danh sách cảm biến nếu có thay đổi
        if len(self.sensor_manager.sensors) != self.sensor_combo.count():
            self.update_sensor_list()
        
        # Cập nhật dữ liệu cho cảm biến đang được chọn
        sensor_id = self.sensor_combo.currentData()
        if sensor_id and sensor_id in self.sensor_manager.sensors:
            sensor = self.sensor_manager.sensors[sensor_id]
            if sensor.connected and sensor.last_data is not None:
                # Thêm dữ liệu mới
                self.sensor_data.setdefault(sensor_id, []).append({
                    'timestamp': current_time,
                    'value': sensor.last_data
                })
                
                # Giới hạn số lượng điểm dữ liệu
                if len(self.sensor_data[sensor_id]) > self.max_data_points:
                    self.sensor_data[sensor_id] = self.sensor_data[sensor_id][-self.max_data_points:]
                
                self.update_plot(sensor_id)
        
        # Cập nhật thống kê tổng hợp
        self.update_summary_stats()
        
        self.last_update = current_time

    def update_plot(self, sensor_id):
        """Cập nhật đồ thị với dữ liệu mới."""
        if not self.sensor_processor:
            return
        times, values = self.sensor_processor.get_data_for_display(sensor_id, self.selected_data_key, num_points=1000)
        if times and values:
            # Chuyển đổi times và values thành numpy array
            times_array = np.array(times)
            values_array = np.array(values)
            self.plot_curve.setData(times_array, values_array)
        else:
            self.plot_curve.setData([], [])
        
        # Cập nhật thống kê
        if values:
            self.min_label.setText(f"{min(values):.2f}")
            self.max_label.setText(f"{max(values):.2f}")
            self.avg_label.setText(f"{np.mean(values):.2f}")
            self.std_label.setText(f"{np.std(values):.2f}")

    def update_summary_stats(self):
        """Cập nhật thống kê tổng hợp."""
        if not self.sensor_manager:
            return
            
        total_sensors = len(self.sensor_manager.sensors)
        active_sensors = sum(1 for s in self.sensor_manager.sensors.values() if s.connected)
        
        total_data_points = sum(len(data) for data in self.sensor_data.values())
        
        # Tính tốc độ dữ liệu trung bình
        if self.sensor_processor:
            avg_data_rate = self.sensor_processor.get_fps()
        else:
            avg_data_rate = 0
            
        # Cập nhật labels
        self.total_sensors_label.setText(str(total_sensors))
        self.active_sensors_label.setText(str(active_sensors))
        self.total_data_points_label.setText(str(total_data_points))
        self.avg_data_rate_label.setText(f"{avg_data_rate:.1f} FPS")

    def closeEvent(self, event):
        """Xử lý khi đóng màn hình."""
        self.update_timer.stop()
        event.accept() 