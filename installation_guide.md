# Installation Guide - Gestionnaire de Chèques (Offline Windows Desktop)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 or later (Windows 11 recommended)
- **Python**: Python 3.11 or later
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 2 GB free space minimum
- **Disk Space**: 500 MB for application + space for data storage

### Recommended Requirements
- **Operating System**: Windows 11
- **Python**: Python 3.11.x (latest stable)
- **RAM**: 8 GB or more
- **Storage**: SSD with 5 GB+ free space
- **Excel**: Microsoft Excel 2016+ (for advanced integration)

## Installation Steps

### 1. Install Python 3.11

1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
2. Run the installer with these important options:
   - ✅ **Check "Add Python to PATH"**
   - ✅ **Check "Install for all users"**
   - ✅ **Check "Install pip"**
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### 2. Install Core Dependencies

Open Command Prompt as Administrator and run:

```cmd
# Core Flask and web framework
pip install Flask==3.0.0
pip install Flask-Login==0.6.3
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-WTF==1.2.1
pip install WTForms==3.1.1
pip install Werkzeug==3.0.1

# Database and SQLAlchemy
pip install SQLAlchemy==2.0.23
pip install email-validator==2.1.0

# Excel processing (REQUIRED)
pip install openpyxl==3.1.2

# PDF generation (REQUIRED)
pip install reportlab==4.0.7

# Task scheduling
pip install APScheduler==3.10.4

# WSGI server
pip install gunicorn==21.2.0

# Date/time utilities
pip install tzlocal==5.2
```

### 3. Install Windows-Specific Dependencies

```cmd
# Windows desktop integration
pip install pywin32==306
pip install winshell==0.6

# System monitoring
pip install psutil==5.9.6

# Image processing
pip install Pillow==10.1.0

# Configuration management
pip install python-dotenv==1.0.0
```

### 4. Install Optional Enhanced Features

```cmd
# Advanced Excel features
pip install xlsxwriter==3.1.9
pip install pandas==2.1.4

# OCR for cheque scanning
pip install pytesseract==0.3.10
pip install opencv-python==4.8.1.78

# Barcode/QR code support
pip install python-barcode==0.15.1
pip install qrcode==7.4.2

# Backup and compression
pip install py7zr==0.20.8

# Desktop notifications
pip install plyer==2.1.0

# File monitoring
pip install watchdog==3.0.0

# User interface enhancements
pip install tqdm==4.66.1
pip install colorama==0.4.6
pip install rich==13.7.0

# Advanced file operations
pip install send2trash==1.8.2
pip install pathlib2==2.3.7

# Text processing
pip install python-slugify==8.0.1
pip install python-dateutil==2.8.2

# Validation and security
pip install validators==0.22.0
pip install cryptography==41.0.8
pip install keyring==24.3.0

# Logging and monitoring
pip install loguru==0.7.2
pip install memory-profiler==0.61.0
```

### 5. Install All Dependencies at Once

Alternatively, you can install all dependencies using the provided requirements file:

```cmd
pip install -r pip_requirements.txt
```

## Application Setup

### 1. Download/Clone the Application

Place all application files in a directory, for example:
```
C:\ChequeManager\
```

### 2. Create Data Directories

The application will automatically create these directories, but you can create them manually:

```cmd
mkdir C:\ChequeManager\data
mkdir C:\ChequeManager\data\excel
mkdir C:\ChequeManager\data\uploads
mkdir C:\ChequeManager\data\exports
mkdir C:\ChequeManager\data\backups
```

### 3. Configure Environment (Optional)

Create a `.env` file in the application root:

```env
# Application Configuration
FLASK_ENV=production
SESSION_SECRET=your-secret-key-here

# Database Configuration (automatically uses SQLite)
# No configuration needed for offline mode

# Upload Configuration
MAX_CONTENT_LENGTH=16777216

# Excel Configuration
EXCEL_AUTO_BACKUP=true
EXCEL_CLEANUP_DAYS=30

# Notification Configuration
NOTIFICATION_ENABLED=true
NOTIFICATION_TIME=08:00

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=data/logs/app.log
```

## Running the Application

### 1. Start the Application

```cmd
cd C:\ChequeManager
python main.py
```

Or using gunicorn (production):

```cmd
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### 2. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

### 3. Default Login Credentials

- **Username**: admin
- **Password**: admin123

**Important**: Change these credentials immediately after first login!

## Troubleshooting

### Common Issues

#### 1. Python Not Found
```
'python' is not recognized as an internal or external command
```
**Solution**: Add Python to your PATH environment variable or reinstall Python with "Add to PATH" option.

#### 2. pip Install Errors
```
ERROR: Could not install packages due to permissions
```
**Solution**: Run Command Prompt as Administrator or use:
```cmd
pip install --user package-name
```

#### 3. Port Already in Use
```
Error: Port 5000 is already in use
```
**Solution**: Change the port or stop other applications using port 5000:
```cmd
python main.py --port 5001
```

#### 4. Excel Files Won't Open
**Solution**: Ensure Microsoft Excel is installed or use alternative Excel viewers.

#### 5. PDF Generation Errors
**Solution**: Install ReportLab properly:
```cmd
pip uninstall reportlab
pip install reportlab==4.0.7
```

### Performance Optimization

#### 1. Database Optimization
Run database optimization periodically:
- Go to Excel Manager → Statistics → Optimize Database

#### 2. Cleanup Old Files
- Go to Excel Manager → Cleanup
- Set automatic cleanup in settings

#### 3. Backup Strategy
- Enable automatic backups
- Store backups on external drive
- Test restore procedures regularly

## Advanced Configuration

### Windows Service Installation

To run as a Windows service:

1. Install additional dependencies:
```cmd
pip install python-windows-service==0.1.1
pip install pywin32-ctypes==0.2.2
```

2. Create service script:
```python
# service.py
from utils.offline_enhancements import OfflineEnhancements
# Service configuration code
```

3. Install service:
```cmd
python service.py install
python service.py start
```

### Desktop Shortcut Creation

Run the application once to automatically create a desktop shortcut, or create manually:

1. Right-click on desktop → New → Shortcut
2. Target: `python C:\ChequeManager\main.py`
3. Name: "Gestionnaire de Chèques"
4. Change icon to Excel icon for easy identification

### Auto-Start Configuration

Add to Windows startup:

1. Press `Win + R`, type `shell:startup`
2. Create a batch file `start_cheque_manager.bat`:
```batch
@echo off
cd /d C:\ChequeManager
python main.py
```
3. Place the batch file in the startup folder

## Security Considerations

### 1. Data Protection
- Regular backups to external storage
- Enable Windows BitLocker for drive encryption
- Use strong passwords for admin accounts

### 2. Network Security
- Application runs locally (offline)
- No external network access required
- Firewall rules can block port 5000 externally

### 3. Access Control
- Create separate user accounts for different roles
- Regularly review user permissions
- Log all system access and changes

## Maintenance

### Regular Tasks
1. **Weekly**: Check system performance, review logs
2. **Monthly**: Create full backup, cleanup old files
3. **Quarterly**: Update dependencies, security review
4. **Annually**: Full system backup, disaster recovery test

### Updates
Check for application updates by reviewing the GitHub repository or contact support.

### Support
For technical support or questions:
- Check the user manual
- Review log files in `data/logs/`
- Create diagnostic report using the built-in tools

## File Structure

```
C:\ChequeManager\
├── main.py                 # Application entry point
├── app.py                  # Flask application setup
├── models.py              # Database models
├── forms.py               # Web forms
├── requirements.txt       # Python dependencies
├── pip_requirements.txt   # Complete dependency list
├── installation_guide.md  # This file
├── data/                  # Data storage (auto-created)
│   ├── cheques.db        # SQLite database
│   ├── excel/            # Excel workbooks
│   ├── uploads/          # Uploaded files
│   ├── exports/          # Export files
│   ├── backups/          # Backup files
│   └── logs/            # Application logs
├── routes/               # Web routes
├── templates/           # HTML templates
├── static/             # CSS, JS, images
└── utils/              # Utility modules
```

This installation guide should help you set up the cheque management system for offline Windows desktop use. Follow the steps carefully and ensure all dependencies are properly installed for optimal performance.