import sys
import logging
from PyQt5.QtWidgets import QApplication
from core.sensor_processor import SensorProcessor
from core.sensor_manager import SensorManager
from ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting application")
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Initialize core components
    processor = SensorProcessor()
    sensor_manager = SensorManager(processor)
    
    # Create and show main window
    window = MainWindow(processor, sensor_manager)
    window.show()
    logger.info("Main window displayed")
    
    try:
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 