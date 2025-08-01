# Replit.md - Gestion des Chèques (Check Management System)

## Overview

This is a Flask-based web application for managing checks and financial transactions, optimized for **offline Windows desktop use**. The system provides comprehensive functionality for tracking checks, managing clients, banks, and branches, with role-based access control and advanced Excel workbook management. The application uses a local SQLite database and features automated yearly Excel organization with 12 monthly sheets per year.

## Recent Changes (January 2025)

### ✓ Offline Desktop Optimization
- Migrated from PostgreSQL to local SQLite database for offline operation
- Configured local data storage in `/data` directory structure
- Enhanced file organization with dedicated folders for Excel, uploads, and exports

### ✓ Advanced Excel Workbook Management
- Implemented `ExcelYearlyManager` for per-year workbooks with 12 monthly sheets
- Added comprehensive Excel dashboard with file management capabilities
- Integrated database synchronization to Excel files
- Created automated backup and cleanup utilities

### ✓ Enhanced Data Management
- Added `DatabaseManager` class for advanced SQLite operations
- Implemented comprehensive backup and restore functionality
- Added diagnostic tools and system optimization features
- Enhanced PDF export capabilities with professional formatting

### ✓ Advanced Analytics & Smart Automation (Latest Update)
- Implemented comprehensive analytics engine with cheque aging analysis
- Added seasonal trends analysis and cash flow prediction
- Built advanced client risk assessment with AI-powered scoring
- Created smart automation system with duplicate detection
- Added performance metrics dashboard with KPI tracking
- Integrated advanced duplicate detection using machine learning algorithms
- Built notification system with customizable templates
- Added automated workflow management and optimization features

### ✓ Replit Environment Migration (August 2025)
- Successfully migrated from Replit Agent to standard Replit environment
- Configured PostgreSQL database integration with SQLite fallback
- Enhanced security with proper client/server separation
- Added comprehensive Flask caching and rate limiting
- Integrated advanced ML libraries (scikit-learn, pandas, numpy)
- Built executive dashboards with real-time analytics
- Implemented AI-powered automation and workflow management
- Added audit logging for compliance and security tracking

### ✓ Deposit Bank Field Enhancement (August 2025)
- Added new "Banque de dépôts – Agence" field to cheque management system
- Updated database model with deposit_branch_id foreign key relationship
- Enhanced ChequeForm with dynamic deposit bank selection dropdown
- Updated cheque creation/editing templates with new field integration
- Optimized Excel synchronization to include deposit bank information
- Created ExcelTracker model for robust sheet/row mapping system
- Implemented comprehensive optimized sync system preventing duplicate entries

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **JavaScript**: jQuery for client-side interactions
- **Icons**: Font Awesome 6.4.0
- **Styling**: Custom CSS with CSS variables for theming

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login for session management
- **Forms**: Flask-WTF with WTForms for form handling and validation
- **Security**: CSRF protection enabled, ProxyFix for deployment
- **File Handling**: Secure file uploads with size limits (16MB)

### Database Architecture
- **Default**: SQLite for development (`sqlite:///cheques.db`)
- **Production**: Configurable via `DATABASE_URL` environment variable
- **Connection Management**: Pool recycling and pre-ping for reliability

## Key Components

### 1. User Management & Authentication
- Role-based access control (admin, comptable, agent, user)
- Secure password hashing with Werkzeug
- Session management with Flask-Login
- French localization for user interface

### 2. Core Business Models
- **Banks**: Manage banking institutions
- **Branches**: Bank branches with contact information
- **Clients**: Individual persons or companies with identification
- **Cheques**: Core entity tracking amounts, dates, status, and relationships
- **Users**: System users with role-based permissions

### 3. Form Management
- Comprehensive form validation using Flask-WTF
- Dynamic client type handling (person vs company)
- File upload support for check attachments
- Multi-currency support (MAD, EUR, USD)

### 4. Export & Reporting System
- Excel export functionality with custom formatting
- PDF report generation using ReportLab
- Filtered exports by date range, bank, status
- Monthly organization in Excel files

### 5. Notification System
- Background scheduler for automated notifications
- Due date alerts (3-day advance warning)
- Rejected check notifications
- Overdue check tracking

## Data Flow

### 1. Check Lifecycle
1. **Creation**: Users create checks with client, bank, and amount information
2. **Status Tracking**: Checks progress through states (en_attente → déposé → encaissé/rejeté)
3. **Notifications**: System alerts users of upcoming due dates or issues
4. **Reporting**: Data exported for analysis and record-keeping

### 2. User Access Patterns
- **Admin**: Full system access including bank/branch management
- **Comptable/Agent**: Check and client management
- **User**: Read-only access to assigned data

### 3. File Management
- Secure file uploads to `/uploads` directory
- File type validation (PNG, JPG, JPEG, PDF)
- Automatic directory creation and management

## External Dependencies

### Python Packages
- **Flask**: Web framework and extensions (SQLAlchemy, Login, WTF)
- **APScheduler**: Background task scheduling
- **OpenPyXL**: Excel file generation and manipulation
- **ReportLab**: PDF document generation
- **Werkzeug**: WSGI utilities and security functions

### Frontend Libraries
- **Bootstrap 5.3.0**: UI framework (CDN)
- **Font Awesome 6.4.0**: Icon library (CDN)
- **jQuery**: JavaScript utilities

### Database Support
- **SQLite**: Default development database
- **PostgreSQL/MySQL**: Production database options via DATABASE_URL

## Deployment Strategy

### Configuration Management
- Environment-based configuration using `os.environ`
- Separate development and production settings
- Secure session key management
- Database URL configuration for different environments

### File Structure
- Modular route organization in `/routes` package
- Utility functions in `/utils` package
- Template inheritance with base layout
- Static assets organization (CSS, JS, uploads)

### Security Considerations
- CSRF protection enabled globally
- Secure file upload validation
- Role-based access control enforcement
- ProxyFix middleware for reverse proxy deployment

### Scalability Features
- Database connection pooling
- Background task scheduling
- Modular application structure
- Template caching support

The application follows Flask best practices with Blueprint organization, proper error handling, and comprehensive form validation. The system is designed to be maintainable and extensible, with clear separation of concerns between data models, business logic, and presentation layers.