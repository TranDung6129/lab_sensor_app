from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSpinBox,
                           QDoubleSpinBox, QGroupBox, QCheckBox, QTableWidget,
                           QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SpreadsheetScreen(QWidget):
    """Spreadsheet analysis screen with data grid and analysis tools."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.data = None
        
        # Initialize UI
        self.setup_ui()
        
        logger.info("SpreadsheetScreen initialized")

    def setup_ui(self):
        """Setup the spreadsheet screen UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Data grid
        grid_frame = QFrame()
        grid_frame.setObjectName("gridFrame")
        grid_frame.setStyleSheet("""
            QFrame#gridFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        grid_layout.addWidget(self.table)
        
        # Controls panel
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_frame.setStyleSheet("""
            QFrame#controlsFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        controls_frame.setFixedWidth(300)
        
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # Data import/export
        io_group = QGroupBox("Data I/O")
        io_layout = QVBoxLayout(io_group)
        
        import_btn = QPushButton("Import Data")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        import_btn.clicked.connect(self.import_data)
        io_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export Data")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        export_btn.clicked.connect(self.export_data)
        io_layout.addWidget(export_btn)
        
        controls_layout.addWidget(io_group)
        
        # Analysis tools
        analysis_group = QGroupBox("Analysis Tools")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Statistics
        stats_btn = QPushButton("Calculate Statistics")
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        stats_btn.clicked.connect(self.show_statistics)
        analysis_layout.addWidget(stats_btn)
        
        # Filter
        filter_btn = QPushButton("Apply Filter")
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        filter_btn.clicked.connect(self.apply_filter)
        analysis_layout.addWidget(filter_btn)
        
        # Correlation
        correlation_btn = QPushButton("Calculate Correlation")
        correlation_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        correlation_btn.clicked.connect(self.calculate_correlation)
        analysis_layout.addWidget(correlation_btn)
        
        controls_layout.addWidget(analysis_group)
        
        # Add spacer
        controls_layout.addStretch()
        
        # Add frames to content layout
        content_layout.addWidget(grid_frame)
        content_layout.addWidget(controls_frame)
        
        layout.addLayout(content_layout)

    def create_toolbar(self):
        """Create the toolbar with data selection and controls."""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setStyleSheet("""
            QFrame#toolbar {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Data source selection
        source_label = QLabel("Data Source:")
        layout.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Live Data", "Recorded Data", "Imported Data"])
        layout.addWidget(self.source_combo)
        
        # Add spacer
        layout.addStretch()
        
        # Control buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(refresh_btn)
        
        return toolbar

    def import_data(self):
        """Import data from file."""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Import Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
            )
            
            if file_name:
                if file_name.endswith('.csv'):
                    self.data = pd.read_csv(file_name)
                else:
                    self.data = pd.read_excel(file_name)
                    
                self.update_table()
                logger.info(f"Data imported from {file_name}")
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to import data: {str(e)}")

    def export_data(self):
        """Export data to file."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Export Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx)"
            )
            
            if file_name:
                if file_name.endswith('.csv'):
                    self.data.to_csv(file_name, index=False)
                else:
                    self.data.to_excel(file_name, index=False)
                    
                logger.info(f"Data exported to {file_name}")
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

    def update_table(self):
        """Update the table with current data."""
        if self.data is None:
            return
            
        # Clear existing data
        self.table.clear()
        
        # Set column count and headers
        self.table.setColumnCount(len(self.data.columns))
        self.table.setHorizontalHeaderLabels(self.data.columns)
        
        # Set row count
        self.table.setRowCount(len(self.data))
        
        # Fill data
        for i in range(len(self.data)):
            for j in range(len(self.data.columns)):
                value = str(self.data.iloc[i, j])
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, j, item)
                
        # Resize columns to content
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def show_statistics(self):
        """Show statistical analysis of the data."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data to analyze")
            return
            
        try:
            stats = self.data.describe()
            
            # Create statistics window
            stats_window = QMessageBox(self)
            stats_window.setWindowTitle("Statistical Analysis")
            
            # Format statistics as text
            stats_text = "Statistical Analysis:\n\n"
            for col in stats.columns:
                stats_text += f"{col}:\n"
                for idx, val in stats[col].items():
                    stats_text += f"{idx}: {val:.4f}\n"
                stats_text += "\n"
                
            stats_window.setText(stats_text)
            stats_window.exec_()
            
            logger.info("Statistical analysis completed")
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            QMessageBox.critical(self, "Error", f"Failed to calculate statistics: {str(e)}")

    def apply_filter(self):
        """Apply filter to the data."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data to filter")
            return
            
        try:
            # Get selected columns
            selected_columns = [self.table.horizontalHeaderItem(i).text() 
                              for i in range(self.table.columnCount())
                              if self.table.horizontalHeaderItem(i) is not None]
            
            if not selected_columns:
                QMessageBox.warning(self, "Warning", "No columns selected")
                return
                
            # Apply moving average filter
            window_size = 5  # Default window size
            for col in selected_columns:
                if pd.api.types.is_numeric_dtype(self.data[col]):
                    self.data[col] = self.data[col].rolling(window=window_size, center=True).mean()
                    
            self.update_table()
            logger.info("Filter applied to data")
        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply filter: {str(e)}")

    def calculate_correlation(self):
        """Calculate correlation between columns."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data to analyze")
            return
            
        try:
            # Get numeric columns
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) < 2:
                QMessageBox.warning(self, "Warning", "Need at least 2 numeric columns for correlation")
                return
                
            # Calculate correlation matrix
            corr_matrix = self.data[numeric_cols].corr()
            
            # Create correlation window
            corr_window = QMessageBox(self)
            corr_window.setWindowTitle("Correlation Analysis")
            
            # Format correlation matrix as text
            corr_text = "Correlation Matrix:\n\n"
            for i in range(len(numeric_cols)):
                for j in range(len(numeric_cols)):
                    corr_text += f"{numeric_cols[i]} vs {numeric_cols[j]}: {corr_matrix.iloc[i,j]:.4f}\n"
                corr_text += "\n"
                
            corr_window.setText(corr_text)
            corr_window.exec_()
            
            logger.info("Correlation analysis completed")
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to calculate correlation: {str(e)}")

    def closeEvent(self, event):
        """Handle widget close event."""
        event.accept() 