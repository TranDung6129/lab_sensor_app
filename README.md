# Lab Sensor Application

A PyQt5-based application for sensor data acquisition, visualization, and analysis.

## Features

- Real-time sensor data acquisition
- Data visualization and analysis
- Configurable storage options (HDF5, SQLite, PostgreSQL)
- Plugin system for extensibility
- Modern and intuitive user interface

## Requirements

- Python 3.8 or higher
- PyQt5
- NumPy
- Pandas
- H5Py
- Matplotlib
- SciPy

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lab_sensor_app
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Activate the virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the application:
```bash
python src/main.py
```

## Configuration

The application settings can be configured through the Settings page. The configuration is saved in `config.json` in the project root directory.

## Development

- The main application code is in the `src` directory
- UI components are in `src/ui`
- Core functionality is in `src/core`
- Plugins can be added in `src/plugin`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
