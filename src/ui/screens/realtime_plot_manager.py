import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
from PyQt5.QtWidgets import QWidget, QApplication
from typing import Dict, List, Optional, Tuple, Union
import json
import os
import logging
import time

logger = logging.getLogger(__name__)

class RealtimePlotManager:
    def __init__(self, dock_area: DockArea):
        self.dock_area = dock_area
        self.plots: Dict[str, pg.PlotWidget] = {}
        self.curves: Dict[str, Dict[str, pg.PlotDataItem]] = {}
        self.docks: Dict[str, Dock] = {}
        
        self.colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (255, 165, 0), (128, 0, 128)
        ]
        self.max_displayed_points = 1000 # Có thể điều chỉnh
        self._removed_plots_info: Dict[str, Dict] = {} # Lưu thông tin dock đã đóng

        pg.setConfigOptions(
            antialias=True,
            background='k',
            foreground='w',
            leftButtonPan=False,
        )
        logger.info("RealtimePlotManager initialized.")

    def create_plot(self, plot_id: str, title: str, position: str = 'bottom', 
                    relative_to_dock: Optional[Dock] = None) -> Optional[pg.PlotWidget]:
        if plot_id in self.plots:
            logger.warning(f"Plot '{plot_id}' already exists. Returning existing plot.")
            return self.plots[plot_id]

        try:
            dock = Dock(title, closable=True, autoOrientation=False)
            dock.setObjectName(f"dock_{plot_id}")
            
            plot_widget = pg.PlotWidget(title=title)
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.setLabel('bottom', 'Thời gian (s)')
            # plot_widget.setLabel('left', 'Giá trị') # Sẽ set khi thêm curve đầu tiên
            plot_widget.addLegend(offset=(-10, 10))
            
            font = plot_widget.getAxis('bottom').label.font()
            font.setPointSize(10)
            plot_widget.getAxis('bottom').label.setFont(font)
            plot_widget.getAxis('left').label.setFont(font)
            
            dock.addWidget(plot_widget)

            if relative_to_dock and isinstance(relative_to_dock, Dock):
                self.dock_area.addDock(dock, position, relative_to_dock)
            else:
                self.dock_area.addDock(dock, position)
            
            self.plots[plot_id] = plot_widget
            self.docks[plot_id] = dock
            self.curves[plot_id] = {}
            
            # Kết nối signal sigClosed của Dock
            dock.sigClosed.connect(lambda d=dock, pid=plot_id: self._handle_dock_closed(d, pid))
            
            logger.info(f"Plot '{plot_id}' created with title '{title}'.")
            return plot_widget
        except Exception as e:
            logger.error(f"Error creating plot '{plot_id}': {e}", exc_info=True)
            return None

    def _handle_dock_closed(self, closed_dock: Dock, plot_id: str):
        logger.info(f"Dock '{plot_id}' (name: {closed_dock.name()}) was closed by user.")
        if plot_id in self.plots:
            # Lưu thông tin cần thiết để khôi phục
            plot_widget = self.plots[plot_id]
            curves_in_plot = list(self.curves.get(plot_id, {}).keys()) # Các data_key đang vẽ trên plot này
            y_label = plot_widget.getAxis('left').labelText

            self._removed_plots_info[plot_id] = {
                'title': closed_dock.name(),
                'y_label': y_label,
                'curves_data_keys': curves_in_plot,
                # 'position_info': self.dock_area.saveState()['docks'].get(closed_dock.name()) # Thử lấy vị trí
            }
            # Xóa khỏi các dict quản lý active
            del self.plots[plot_id]
            del self.docks[plot_id]
            if plot_id in self.curves:
                del self.curves[plot_id]
            logger.debug(f"Information for closed plot '{plot_id}' stored for potential restoration.")
        else:
            logger.warning(f"Closed dock for plot_id '{plot_id}' not found in active plots dict.")

    def add_curve(self, plot_id: str, curve_id: str, name: str, y_label: str = "Giá trị") -> Optional[pg.PlotDataItem]:
        if plot_id not in self.plots:
            logger.error(f"Plot '{plot_id}' does not exist. Cannot add curve '{curve_id}'.")
            return None
        
        plot_widget = self.plots[plot_id]
        if not self.curves[plot_id]: # Nếu đây là curve đầu tiên của plot, set Y label
            plot_widget.setLabel('left', y_label)

        if curve_id in self.curves[plot_id]:
            logger.warning(f"Curve '{curve_id}' already exists in plot '{plot_id}'.")
            return self.curves[plot_id][curve_id]

        color_idx = len(self.curves[plot_id]) % len(self.colors)
        color = self.colors[color_idx]
        pen = pg.mkPen(color=color, width=2)
        
        try:
            curve = plot_widget.plot([], [], name=name, pen=pen, antialias=True)
            curve.opts['curve_id'] = curve_id # Lưu để nhận dạng
            self.curves[plot_id][curve_id] = curve
            logger.info(f"Curve '{curve_id}' (name: '{name}') added to plot '{plot_id}'.")
            return curve
        except Exception as e:
            logger.error(f"Error adding curve '{curve_id}' to plot '{plot_id}': {e}", exc_info=True)
            return None

    def update_curve_data(self, plot_id: str, curve_id: str, x_data: List[float], y_data: List[float]):
        if plot_id not in self.curves or curve_id not in self.curves[plot_id]:
            return

        curve = self.curves[plot_id][curve_id]
        plot_widget = self.plots[plot_id]
        
        if not x_data or not y_data:
            curve.setData([], [])
            return

        # Giới hạn số điểm dữ liệu để tránh chậm
        if len(x_data) > self.max_displayed_points:
            x_data = x_data[-self.max_displayed_points:]
            y_data = y_data[-self.max_displayed_points:]
            
        curve.setData(x_data, y_data)
        # AutoRange có thể nặng, xem xét chỉ gọi khi cần
        # plot_widget.enableAutoRange('xy', True) 

    def remove_curve(self, plot_id: str, curve_id: str):
        if plot_id in self.curves and curve_id in self.curves[plot_id]:
            curve_item = self.curves[plot_id].pop(curve_id)
            if plot_id in self.plots:
                self.plots[plot_id].removeItem(curve_item)
                logger.info(f"Curve '{curve_id}' removed from plot '{plot_id}'.")
            if not self.curves[plot_id]: # Nếu không còn curve nào trên plot
                self.plots[plot_id].setLabel('left', 'Giá trị') # Reset Y label
                # self.plots[plot_id].legend.clear() # Cân nhắc xóa legend nếu không còn item
        else:
            logger.warning(f"Curve '{curve_id}' not found in plot '{plot_id}' for removal.")
            
    def get_plot_by_id(self, plot_id: str) -> Optional[pg.PlotWidget]:
        return self.plots.get(plot_id)

    def get_dock_by_id(self, plot_id: str) -> Optional[Dock]:
        return self.docks.get(plot_id)
        
    def get_all_plot_ids(self) -> List[str]:
        return list(self.plots.keys())

    def get_curves_for_plot(self, plot_id: str) -> Dict[str, pg.PlotDataItem]:
        return self.curves.get(plot_id, {})
        
    def clear_all_curves_data(self):
        for plot_id in self.curves:
            for curve_id in self.curves[plot_id]:
                self.curves[plot_id][curve_id].setData([], [])
        logger.info("All curves data cleared.")

    def remove_all_plots(self):
        # Tạo bản sao của danh sách các plot ID để tránh lỗi thay đổi dict khi lặp
        plot_ids_to_remove = list(self.docks.keys())
        for plot_id in plot_ids_to_remove:
            self.remove_plot_and_dock(plot_id) # Gọi hàm xóa cả dock
        logger.info("All plots and their docks removed.")

    def remove_plot_and_dock(self, plot_id: str):
        if plot_id in self.docks:
            dock_to_remove = self.docks.pop(plot_id)
            if plot_id in self.plots:
                plot_widget = self.plots.pop(plot_id)
                # Quan trọng: phải xóa widget khỏi dock trước khi xóa dock
                if dock_to_remove.widgets: # kiểm tra dock có widget không
                    for w in dock_to_remove.widgets: # lặp qua list widget
                        if w == plot_widget:
                            w.setParent(None) # gỡ plot_widget ra khỏi dock
                            plot_widget.deleteLater() # xóa hẳn plot_widget
                            break # thoát vòng lặp khi tìm thấy
            if plot_id in self.curves:
                del self.curves[plot_id]
            
            try:
                # dock_to_remove.close() # Đóng dock sẽ tự động xóa nó khỏi DockArea
                # Hoặc nếu không tự xóa, có thể cần gọi:
                if self.dock_area and hasattr(self.dock_area, 'removeDock'):
                     self.dock_area.removeDock(dock_to_remove)
                dock_to_remove.deleteLater() # Xóa dock widget
                logger.info(f"Plot and Dock '{plot_id}' removed.")
            except Exception as e:
                logger.error(f"Error removing dock '{plot_id}': {e}", exc_info=True)
        else:
            logger.warning(f"Plot '{plot_id}' not found for removal.")

    def get_removed_plots_info(self) -> Dict[str, Dict]:
        return self._removed_plots_info

    def restore_plot(self, plot_id: str, position: str = 'bottom',
                     relative_to_plot_id: Optional[str] = None) -> bool:
        if plot_id not in self._removed_plots_info:
            logger.warning(f"No information to restore plot '{plot_id}'.")
            return False

        plot_info = self._removed_plots_info.pop(plot_id) # Lấy và xóa khỏi danh sách đã xóa
        title = plot_info['title']
        y_label = plot_info.get('y_label', 'Giá trị')
        curve_data_keys = plot_info.get('curves_data_keys', [])
        
        relative_dock = None
        if relative_to_plot_id and relative_to_plot_id in self.docks:
            relative_dock = self.docks[relative_to_plot_id]
            
        created_plot_widget = self.create_plot(plot_id, title, position, relative_dock)
        if created_plot_widget:
            created_plot_widget.setLabel('left', y_label) # Khôi phục Y label
            # Khôi phục các curves
            for data_key in curve_data_keys:
                # Bạn cần một cách để lấy lại "name" của curve, ví dụ từ sensor_processor
                # Hoặc lưu 'name' trong _removed_plots_info
                curve_name = data_key # Tạm thời dùng data_key làm name
                self.add_curve(plot_id, data_key, curve_name, y_label)
            logger.info(f"Plot '{plot_id}' restored.")
            return True
        else:
            # Nếu không tạo được, thêm lại vào _removed_plots_info để thử lại sau
            self._removed_plots_info[plot_id] = plot_info
            logger.error(f"Failed to restore plot '{plot_id}'.")
            return False
            
    def save_layout(self, filename: str):
        try:
            state = self.dock_area.saveState()
            # Lưu thêm thông tin về các plots và curves đang active
            active_plots_config = {}
            for plot_id, plot_widget in self.plots.items():
                dock = self.docks[plot_id]
                active_plots_config[plot_id] = {
                    'title': dock.name(), # Hoặc plot_widget.titleLabel.text
                    'y_label': plot_widget.getAxis('left').labelText,
                    'curves': {
                        curve_id: curve.name() # curve.opts.get('name')
                        for curve_id, curve in self.curves.get(plot_id, {}).items()
                    }
                    # Thêm thông tin vị trí của dock nếu cần thiết và có thể lấy được
                }
            
            full_config = {
                'dock_state': state,
                'active_plots_config': active_plots_config
            }
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(full_config, f, indent=4)
            logger.info(f"Realtime layout state saved to {filename}.")
        except Exception as e:
            logger.error(f"Error saving realtime layout state: {e}", exc_info=True)

    def load_layout(self, filename: str) -> bool:
        if not os.path.exists(filename):
            logger.error(f"Layout file not found: {filename}")
            return False
        try:
            with open(filename, 'r') as f:
                full_config = json.load(f)
            
            dock_state = full_config.get('dock_state')
            active_plots_config = full_config.get('active_plots_config', {})

            if not dock_state:
                logger.error("Invalid layout file: 'dock_state' is missing.")
                return False

            # Xóa layout cũ
            self.remove_all_plots()
            QApplication.processEvents() # Đảm bảo các widget cũ được xóa hẳn

            self.dock_area.restoreState(dock_state)
            
            # Khôi phục lại internal state dựa trên active_plots_config và dock_state
            # Điều này quan trọng vì restoreState chỉ khôi phục widget, không khôi phục logic của PlotManager
            
            # Bước 1: Tìm lại các Docks và PlotWidgets từ DockArea
            temp_docks = {} # dock_name_from_state -> Dock object
            all_found_docks_in_area = self.dock_area.findAll(type='dock')

            for dock_name_in_state, dock_widget_from_area in all_found_docks_in_area.items():
                temp_docks[dock_name_in_state] = dock_widget_from_area

            # Bước 2: Map lại với active_plots_config
            for plot_id, config in active_plots_config.items():
                dock_title_from_config = config['title']
                # Tìm dock tương ứng trong temp_docks bằng title
                # Lưu ý: Tên dock trong state có thể khác với title hiển thị, thường là dock.name()
                # Chúng ta cần một cách map plot_id (key của active_plots_config) với dock_name trong state
                # Cách đơn giản nhất là giả sử plot_id chính là tên của dock khi save (dock.name())
                
                target_dock_name_in_state = dock_title_from_config # Hoặc một key khác nếu bạn lưu tên state của dock
                
                if target_dock_name_in_state in temp_docks:
                    dock = temp_docks[target_dock_name_in_state]
                    if dock.widgetCount() > 0 and isinstance(dock.widgets[0], pg.PlotWidget):
                        plot_widget = dock.widgets[0]
                        
                        # Cập nhật lại dicts của PlotManager
                        self.docks[plot_id] = dock
                        self.plots[plot_id] = plot_widget
                        self.curves[plot_id] = {} # Khởi tạo

                        # Khôi phục title và label
                        dock.setTitle(config['title']) # Cập nhật lại title cho dock
                        plot_widget.setTitle(config['title'])
                        plot_widget.setLabel('left', config.get('y_label', 'Giá trị'))
                        plot_widget.addLegend(offset=(-10, 10)) # Đảm bảo legend có
                        
                        # Kết nối lại sigClosed
                        dock.sigClosed.connect(lambda d=dock, pid=plot_id: self._handle_dock_closed(d, pid))

                        # Khôi phục các curves
                        for curve_id, curve_name in config.get('curves', {}).items():
                            self.add_curve(plot_id, curve_id, curve_name, config.get('y_label', 'Giá trị'))
                        logger.info(f"Restored plot '{plot_id}' and its curves from layout.")
                    else:
                        logger.warning(f"Dock '{target_dock_name_in_state}' for plot_id '{plot_id}' does not contain a PlotWidget or is empty after restore.")
                else:
                    logger.warning(f"Dock with title/name '{target_dock_name_in_state}' for plot_id '{plot_id}' not found in restored DockArea state. Plot may not be fully restored.")
            
            logger.info(f"Realtime layout state loaded from {filename}.")
            return True
        except Exception as e:
            logger.error(f"Error loading realtime layout state: {e}", exc_info=True)
            self.remove_all_plots() # Dọn dẹp nếu có lỗi
            return False 