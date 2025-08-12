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

### ✓ Date Format Enhancement (August 2025)
- Implemented custom date field formatting to display dd/mm/yyyy format
- Created CustomDateField class with proper date parsing and display
- Added JavaScript date formatting helpers for consistent user experience
- Updated all form date fields to use the new formatting system
- Enhanced form validation to accept both dd/mm/yyyy and yyyy-mm-dd formats
- Fixed HTML5 date input compatibility by using text inputs with validation
- Added real-time input formatting with auto-slash insertion
- Implemented auto-select date functionality with quick date selection options

### ✓ Deposit Bank Field Enhancement (August 2025)
- Added new "Banque de dépôts – Agence" field to cheque management system
- Updated database model with deposit_branch_id foreign key relationship
- Enhanced ChequeForm with dynamic deposit bank selection dropdown
- Updated cheque creation/editing templates with new field integration
- Optimized Excel synchronization to include deposit bank information
- Created ExcelTracker model for robust sheet/row mapping system
- Implemented comprehensive optimized sync system preventing duplicate entries

### ✓ Executable (.exe) Build Configuration (August 2025)
- Created comprehensive build system for Windows executable generation
- Implemented desktop_main.py entry point for standalone application
- Configured PyInstaller, auto-py-to-exe, and cx_Freeze build options
- Added SQLite database configuration for offline desktop usage
- Created detailed build guide with multiple construction methods
- Prepared portable application structure with local data storage

### ✓ Depositor Management & Auto-Sheet Optimization (August 2025)
- Created comprehensive depositor management system with CRUD operations
- Implemented DepositorForm for managing depositor information (person/company/agent)
- Added depositor search, filtering, and risk assessment capabilities
- Built AutoSheetCreator optimization for automatic monthly sheet creation
- Enhanced cheque creation to automatically generate all 12 monthly sheets per year
- Integrated depositor relationship tracking with cheques and deposit logs
- Created responsive templates for depositor list, form, and detail views

### ✓ Modal Integration & Enhanced User Experience (August 2025)
- Successfully integrated modal popups for creating new clients and depositors from cheque form
- Built comprehensive AJAX endpoints for seamless client/depositor creation without page refresh
- Enhanced modal forms with full field validation and dynamic type handling
- Integrated depositor statistics and analytics into main dashboard
- Created detailed APP_DESCRIPTION.md with complete system documentation
- Completed migration from Replit Agent to standard Replit environment with full functionality

### ✓ Priority Performance & Security Optimizations (August 2025)
- **Performance Boosters**: Redis caching, database indexing, lazy loading, compression
- **Security Enhancements**: Two-Factor Authentication (2FA), audit trail, data encryption
- **AI/ML Intelligence**: Fraud detection, cash flow prediction, smart recommendations
- **Progressive Web App (PWA)**: Offline functionality, real-time notifications, app installation
- **Advanced Analytics**: Real-time metrics, performance monitoring, intelligent insights
- **Caching System**: Flask-Caching with Redis backend for optimized query performance
- **Rate Limiting**: Advanced rate limiting with adaptive thresholds based on user behavior
- **Background Processing**: WebSocket integration for real-time updates and notifications

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **JavaScript**: jQuery for client-side interactions, performance optimizations
- **Icons**: Font Awesome 6.4.0
- **Styling**: Custom CSS with CSS variables for theming
- **PWA Features**: Service Worker, offline functionality, app installation
- **Performance**: Lazy loading, debounced search, intersection observer
- **Real-time**: WebSocket connections for live notifications

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login with 2FA support
- **Forms**: Flask-WTF with WTForms for form handling and validation
- **Security**: CSRF protection, security headers, session validation, data encryption
- **File Handling**: Secure file uploads with size limits (16MB)
- **Performance**: Flask-Compress, Flask-Caching, Flask-Limiter
- **Real-time**: Flask-SocketIO for WebSocket connections
- **AI/ML**: Fraud detection, cash flow prediction, recommendation engine
- **Audit**: Comprehensive audit logging for all system actions

### Database Architecture
- **Default**: SQLite for development (`sqlite:///cheques.db`)
- **Production**: Configurable via `DATABASE_URL` environment variable
- **Connection Management**: Pool recycling and pre-ping for reliability

## Key Components

### 1. User Management & Authentication
- Role-based access control (admin, comptable, agent, user)
- Secure password hashing with Werkzeug
- Two-Factor Authentication (2FA) with QR codes
- Session management with Flask-Login and integrity validation
- Comprehensive audit logging
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

### 5. Notification System & Real-time Features
- Background scheduler for automated notifications
- Real-time WebSocket notifications
- PWA push notifications support
- Due date alerts (3-day advance warning)
- Rejected check notifications
- Overdue check tracking
- Fraud detection alerts

### 6. AI/ML Intelligence System
- **Fraud Detection**: Machine learning model for anomaly detection
- **Cash Flow Prediction**: 30-day financial forecasting
- **Risk Assessment**: Automated client risk scoring
- **Smart Recommendations**: AI-powered action suggestions
- **Client Segmentation**: Behavioral clustering analysis

### 7. Performance Optimization
- **Caching**: Redis-based query caching with intelligent invalidation
- **Lazy Loading**: On-demand chart and data loading
- **Compression**: Gzip compression for all responses
- **Rate Limiting**: Adaptive rate limiting based on user behavior
- **Background Processing**: Async task processing

### 8. Progressive Web App (PWA)
- **Offline Functionality**: Service Worker for offline access
- **App Installation**: Native app-like installation
- **Background Sync**: Offline form submission queuing
- **Push Notifications**: Real-time system alerts
- **Performance Monitoring**: Client-side performance tracking

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
- **Flask**: Web framework and extensions (SQLAlchemy, Login, WTF, Compress, SocketIO)
- **Performance**: Flask-Caching, Flask-Limiter, Redis
- **Security**: Cryptography, PyOTP (2FA), QRCode generation
- **AI/ML**: scikit-learn for machine learning models
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