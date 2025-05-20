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
        self.selected_sensor_id = None  # Initialize selected_sensor_id
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
        
        # Combo box chọn kênh dữ liệu
        self.data_key_combo = QComboBox()
        self.data_key_combo.currentTextChanged.connect(self.on_data_key_changed)
        control_layout.addWidget(QLabel("Chọn kênh dữ liệu:"))
        control_layout.addWidget(self.data_key_combo)
        
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
            
        # Tự động chọn item đầu tiên nếu chưa có lựa chọn
        if self.sensor_combo.count() > 0 and not self.selected_sensor_id:
            self.sensor_combo.setCurrentIndex(0)  # Điều này sẽ trigger on_sensor_changed
        elif self.selected_sensor_id:  # Khôi phục lựa chọn trước đó
            index = self.sensor_combo.findData(self.selected_sensor_id)
            if index != -1:
                self.sensor_combo.setCurrentIndex(index)
            else:  # Sensor cũ không còn, reset
                self.selected_sensor_id = None
                self.data_key_combo.clear()
                if self.sensor_combo.count() > 0:
                    self.sensor_combo.setCurrentIndex(0)

    def on_sensor_changed(self, sensor_text):
        """Xử lý khi người dùng chọn cảm biến khác."""
        if not sensor_text:
            return
            
        sensor_id = self.sensor_combo.currentData()
        self.selected_sensor_id = sensor_id
        
        # Cập nhật data_key_combo
        self.data_key_combo.clear()
        if sensor_id and self.sensor_processor:
            available_keys = self.sensor_processor.data_keys_by_sensor.get(sensor_id, [])
            self.data_key_combo.addItems(available_keys)
            
            if self.data_key_combo.count() > 0:
                self.data_key_combo.setCurrentIndex(0)  # Trigger on_data_key_changed
            else:
                self.selected_data_key = None
                self.update_plot()  # Cập nhật đồ thị (sẽ rỗng)
        else:
            self.selected_data_key = None
            self.update_plot()

    def on_data_key_changed(self, data_key_text):
        """Xử lý khi người dùng chọn kênh dữ liệu khác."""
        if not data_key_text:
            self.selected_data_key = None
        else:
            self.selected_data_key = data_key_text
            
        self.update_plot()

    def on_time_range_changed(self, time_range):
        """Xử lý khi người dùng thay đổi khoảng thời gian."""
        self.update_plot()

    def update_data(self):
        """Cập nhật dữ liệu từ cảm biến."""
        if not self.sensor_manager:
            return
            
        current_time = datetime.now()
        time_diff = (current_time - self.last_update).total_seconds()
        
        # Cập nhật danh sách cảm biến nếu có thay đổi
        if len(self.sensor_manager.sensors) != self.sensor_combo.count():
            self.update_sensor_list()
        
        # Cập nhật thống kê tổng hợp
        self.update_summary_stats()
        
        self.last_update = current_time

    def update_plot(self):
        """Cập nhật đồ thị với dữ liệu mới."""
        if not self.sensor_processor or not self.selected_sensor_id or not self.selected_data_key:
            self.plot_curve.setData([], [])
            self.min_label.setText("N/A")
            self.max_label.setText("N/A")
            self.avg_label.setText("N/A")
            self.std_label.setText("N/A")
            return

        # Xác định khoảng thời gian từ time_range_combo
        sensor_config = self.sensor_processor.active_sensors_config.get(self.selected_sensor_id, {}).get('config', {})
        sampling_rate = sensor_config.get('sampling_rate', 200)  # Mặc định 200Hz

        time_range_text = self.time_range_combo.currentText()
        num_points = self.max_data_points  # Mặc định
        if time_range_text == "1 phút":
            num_points = 1 * 60 * sampling_rate
        elif time_range_text == "5 phút":
            num_points = 5 * 60 * sampling_rate
        elif time_range_text == "15 phút":
            num_points = 15 * 60 * sampling_rate
        elif time_range_text == "30 phút":
            num_points = 30 * 60 * sampling_rate
        elif time_range_text == "1 giờ":
            num_points = 60 * 60 * sampling_rate

        # Giới hạn số điểm dữ liệu
        num_points = min(num_points, self.max_data_points)

        times, values = self.sensor_processor.get_data_for_display(
            self.selected_sensor_id,
            self.selected_data_key,
            num_points=int(num_points)
        )

        if times and values:
            times_array = np.array(times)
            values_array = np.array(values)
            self.plot_curve.setData(times_array, values_array)

            self.min_label.setText(f"{np.min(values_array):.2f}")
            self.max_label.setText(f"{np.max(values_array):.2f}")
            self.avg_label.setText(f"{np.mean(values_array):.2f}")
            self.std_label.setText(f"{np.std(values_array):.2f}")
        else:
            self.plot_curve.setData([], [])
            self.min_label.setText("N/A")
            self.max_label.setText("N/A")
            self.avg_label.setText("N/A")
            self.std_label.setText("N/A")

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