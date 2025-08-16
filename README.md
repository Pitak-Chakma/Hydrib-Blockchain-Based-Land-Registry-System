# Hydrib Land Registry System

A secure, blockchain-inspired land registry system built with Flask, featuring comprehensive property management, transaction tracking, and document storage capabilities.

## 🌟 Features

### Core Functionality
- **Land Record Management**: Create, view, and manage land property records
- **Transaction Tracking**: Complete transaction history with blockchain-inspired integrity
- **Document Management**: Secure upload and storage of property documents
- **User Management**: Role-based access control (Admin, Officer, Citizen)
- **Search & Filter**: Advanced search capabilities across all records
- **Audit Trail**: Complete audit logging for all system activities

### Security Features
- **Authentication & Authorization**: Secure login with role-based permissions
- **Data Integrity**: Blockchain-inspired hash verification
- **Input Validation**: Comprehensive server-side validation
- **Security Headers**: CSRF protection, XSS prevention, content security policy
- **Rate Limiting**: Protection against brute force attacks
- **Secure File Upload**: Validated file types and secure storage

### Performance & Monitoring
- **Database Optimization**: Indexed queries and performance monitoring
- **Health Checks**: Built-in application health monitoring
- **Logging**: Comprehensive logging with configurable levels
- **Backup System**: Automated database and file backups
- **Performance Analytics**: Query performance tracking and optimization

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- SQLite3
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Hydrib-Blockchain-Based-Land-Registry-System
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   python3 app.py
   ```

6. **Create demo accounts** (optional):
   ```bash
   python3 create_demo_accounts.py
   ```

7. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

### Demo Accounts

After running the demo account script:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| Admin | admin@landregistry.gov | admin123 | Full system access |
| Officer | officer@landregistry.gov | officer123 | Land record management |
| Citizen | citizen@example.com | citizen123 | View own properties |

## 📁 Project Structure

```
Hydrib-Blockchain-Based-Land-Registry-System/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── wsgi.py                     # WSGI entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env.production            # Production environment template
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Dashboard
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── admin_dashboard.html   # Admin dashboard
│   ├── owner_dashboard.html   # Owner dashboard
│   ├── buyer_dashboard.html   # Buyer dashboard
│   ├── register_land.html     # Land registration
│   ├── transfer_property.html # Property transfer
│   ├── upload_documents.html  # Document upload
│   └── ledger.html            # Transaction ledger
│
├── uploads/                    # Uploaded documents
│
├── utils/                      # Utility scripts
│   ├── create_demo_accounts.py # Demo account creation
│   ├── populate_db.py         # Database population
│   ├── optimize_database.py   # Database optimization
│   ├── performance_monitor.py # Performance monitoring
│   ├── backup_script.py       # Backup automation
│   ├── health_check.py        # Health monitoring
│   └── security.py            # Security utilities
│
├── deployment/                 # Deployment files
│   ├── Dockerfile             # Docker container
│   ├── docker-compose.yml     # Docker Compose setup
│   ├── nginx.conf             # Nginx configuration
│   ├── landregistry.service   # Systemd service
│   └── deploy.sh              # Deployment script
│
└── docs/                       # Documentation
    ├── README.md              # This file
    └── DEPLOYMENT.md          # Deployment guide
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_PATH=land_registry.db

# File Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Session Management
SESSION_TIMEOUT=3600  # 1 hour
SESSION_COOKIE_SECURE=False  # Set to True in production

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100 per hour

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### Production Configuration

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive setup instructions.

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with planned PostgreSQL support
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap)
- **Security**: Flask-Login, CSRF protection, bcrypt
- **Deployment**: Docker, Nginx, Gunicorn

### Database Schema

#### Core Tables

1. **users**: User accounts and authentication
2. **land_records**: Property information and ownership
3. **transactions**: Property transfer history
4. **documents**: Uploaded property documents
5. **blockchain**: Transaction integrity verification
6. **admin_notifications**: System notifications

#### Key Relationships

- Users can own multiple land records
- Land records can have multiple transactions
- Transactions can have multiple associated documents
- All transactions are recorded in the blockchain table for integrity

### Security Model

#### Role-Based Access Control

- **Admin**: Full system access, user management, system configuration
- **Officer**: Land record management, transaction processing
- **Citizen**: View own properties, submit applications

#### Data Protection

- Password hashing with bcrypt
- CSRF token validation
- Input sanitization and validation
- Secure file upload handling
- SQL injection prevention

## 🔍 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /register` - User registration (if enabled)

### Land Records
- `GET /` - Dashboard with land records overview
- `GET /register_land` - Land registration form
- `POST /register_land` - Create new land record
- `GET /transfer_property` - Property transfer form
- `POST /transfer_property` - Process property transfer

### Documents
- `GET /upload_documents` - Document upload form
- `POST /upload_documents` - Upload new document
- `GET /ledger` - View transaction ledger

### System
- `GET /health` - Health check endpoint
- `GET /admin_dashboard` - Admin dashboard (admin only)

## 📊 Monitoring

### Health Monitoring

```bash
# Check application health
curl http://localhost:5000/health

# Run comprehensive health check
python3 health_check.py

# Start health monitoring daemon
python3 health_check.py --daemon
```

### Performance Monitoring

```bash
# Run performance analysis
python3 performance_monitor.py

# View performance report
cat performance_report_*.json
```

### Log Analysis

Logs are stored in:
- Application logs: `app.log`
- Access logs: `access.log`
- Error logs: `error.log`

## 🔄 Backup & Recovery

### Automated Backups

```bash
# Run manual backup
python3 backup_script.py

# Set up automated backups (cron)
0 2 * * * /path/to/venv/bin/python /path/to/backup_script.py
```

### Backup Components

1. **Database**: Complete SQLite database
2. **Uploaded Files**: All property documents
3. **Configuration**: Environment and config files

## 🚀 Deployment

### Development

```bash
# Start development server
python3 app.py
```

### Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

#### Quick Production Setup

```bash
# Using deployment script
sudo ./deploy.sh

# Using Docker
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Ensure security best practices
- Test in multiple environments

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

1. Check the [documentation](DEPLOYMENT.md)
2. Review [common issues](DEPLOYMENT.md#troubleshooting)
3. Check application logs
4. Run health checks

### Reporting Issues

When reporting issues, please include:

- Operating system and version
- Python version
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

## 🔮 Roadmap

### Planned Features

- [ ] PostgreSQL database support
- [ ] REST API with OpenAPI documentation
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Integration with external mapping services
- [ ] Multi-language support
- [ ] Advanced workflow management
- [ ] Real-time notifications
- [ ] Blockchain integration enhancement
- [ ] Machine learning for fraud detection

### Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Enhanced security and performance monitoring
- **v1.2.0**: Production deployment tools and documentation

---

**Built with ❤️ for secure and transparent land registry management**

# Complete Cycle Walkthrough: Blockchain-Based Land Registry System
Here's a comprehensive step-by-step walkthrough of a complete cycle in your blockchain-based land registry system:

## Phase 1: System Setup & User Registration
### Step 1: Initial Access
1. 1.
   Visit Homepage : Navigate to http://127.0.0.1:5000
2. 2.
   System Overview : View the hero section explaining the blockchain land registry objectives
3. 3.
   User Registration : Click "Register" to create an account
4. 4.
   Role Selection : Choose user type (Admin, Land Owner, or Buyer)
5. 5.
   Account Creation : Complete registration with email, password, and personal details
### Step 2: Authentication
1. 1.
   Login : Use credentials to access the system
2. 2.
   Role-Based Redirect : System automatically redirects to appropriate dashboard based on user role
## Phase 2: Land Registration (Land Owner)
### Step 3: Property Registration
1. 1.
   Access Dashboard : Land owner logs in to `owner_dashboard.html`
2. 2.
   Navigate to Registration : Click "Register New Land" button
3. 3.
   Fill Property Details :
   - Property title and description
   - Khatian number and DAG number
   - Land type (residential, commercial, agricultural)
   - Market value and location details
   - Division, district, upazila, and mouza information
4. 4.
   Submit Registration : System processes the registration
### Step 4: Blockchain Recording
1. 1.
   Smart Contract Execution : System automatically creates a smart contract for the property
2. 2.
   Blockchain Entry : Transaction is recorded in the blockchain simulation
3. 3.
   Hash Generation : Unique hash is generated for the property record
4. 4.
   Database Storage : Property details are stored in the land_records table
5. 5.
   Transaction Log : Initial registration transaction is logged in the transactions table
### Step 5: Document Upload
1. 1.
   Access Upload Section : Navigate to document upload page
2. 2.
   Upload Documents : Add property deeds, surveys, or legal documents
3. 3.
   Hash Verification : System generates SHA-256 hashes for document integrity
4. 4.
   Storage : Documents are stored in the uploads/ directory with hash verification
## Phase 3: Property Transfer Process
### Step 6: Buyer Interest
1. 1.
   Buyer Dashboard : Buyer logs in and views available properties
2. 2.
   Property Search : Browse or search for specific properties
3. 3.
   View Details : Access comprehensive property information
4. 4.
   Initiate Transfer : Express interest in purchasing a property
### Step 7: Transfer Initiation (Land Owner)
1. 1.
   Transfer Request : Owner receives notification of buyer interest
2. 2.
   Access Transfer Page : Navigate to `transfer_property.html`
3. 3.
   Select Property : Choose the property to transfer
4. 4.
   Enter Buyer Details : Specify buyer information and transfer price
5. 5.
   Submit Transfer : Initiate the blockchain transfer process
### Step 8: Smart Contract Processing
1. 1.
   Contract Creation : System generates a new smart contract for the transfer
2. 2.
   Validation : Automated validation of:
   - Owner verification
   - Property ownership status
   - Legal compliance checks
3. 3.
   Consensus Simulation : System simulates blockchain consensus mechanism
4. 4.
   Status Updates : Real-time status updates throughout the process
## Phase 4: Administrative Oversight
### Step 9: Admin Review (Admin User)
1. 1.
   Admin Dashboard : Administrator accesses `admin_dashboard.html`
2. 2.
   Transaction Review : Monitor all pending and completed transactions
3. 3.
   User Management : Oversee user accounts and permissions
4. 4.
   System Statistics : View comprehensive system analytics
5. 5.
   Approval Process : Review and approve complex transactions if required
### Step 10: Transaction Completion
1. 1.
   Final Validation : Admin or automated system performs final checks
2. 2.
   Ownership Transfer : Property ownership is officially transferred
3. 3.
   Blockchain Update : New ownership record is added to the blockchain
4. 4.
   Database Updates : All relevant tables are updated:
   - land_records : Updated owner information
   - transactions : Transfer completion logged
   - blockchain : New block added with transfer data
## Phase 5: Verification & Transparency
### Step 11: Public Ledger Access
1. 1.
   Ledger Viewer : Anyone can access `ledger.html`
2. 2.
   Transaction History : View complete transaction history
3. 3.
   Search & Filter : Find specific transactions or properties
4. 4.
   Transparency : Public verification of all blockchain activities
### Step 12: Post-Transfer Activities
1. 1.
   New Owner Dashboard : Buyer (now owner) can access their updated dashboard
2. 2.
   Property Management : New owner can manage their acquired property
3. 3.
   Document Access : All property documents are transferred to new owner
4. 4.
   Future Transactions : Property is now available for future transfers
## Key Features Throughout the Cycle
- Security : SHA-256 hashing for document integrity
- Transparency : All transactions are publicly viewable
- Immutability : Blockchain simulation ensures tamper-proof records
- Role-Based Access : Different interfaces for different user types
- Real-Time Updates : Live status updates throughout all processes
- Automated Validation : Smart contracts handle compliance checking
- Audit Trail : Complete history of all property transactions
This complete cycle demonstrates how the system handles the entire lifecycle of land ownership from initial registration through transfer, with full blockchain transparency and administrative oversight.