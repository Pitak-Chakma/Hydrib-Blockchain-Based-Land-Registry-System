# 🏢 Hydrib: Blockchain-Based Land Registry System

A modern demonstration platform showcasing a hybrid blockchain-based land registry and management system. Hydrib simulates the secure, transparent, and efficient process of land transactions using blockchain technology.

## 🌟 Key Features

- **🔐 Role-Based Access Control** with 4 user roles + guests:
  - **👑 Admin**: System oversight, user management, and account approval
  - **🏛️ Government Official**: Transaction verification and blockchain record generation
  - **🏡 Seller (Land Owner)**: Property listing and sales management
  - **🔍 Buyer**: Property browsing and purchase requests
  - **👥 Guest**: Public information access only

- **⛓️ Simulated Blockchain Integration** for secure transaction records
- **📱 Responsive UI** built with Bootstrap for all devices
- **🔒 Secure Authentication** with password hashing via Werkzeug
- **📊 Role-Specific Dashboards** for streamlined user experiences

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Security**: Werkzeug for password hashing

## 📋 System Architecture

### Database Models
- **User**: Account management with role-based permissions
- **Land**: Property listings with details and ownership information
- **Transaction**: Purchase records with blockchain integration

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Hydrib-Blockchain-Based-Land-Registry-System.git
   cd Hydrib-Blockchain-Based-Land-Registry-System
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - The database will be automatically initialized with default users

## 👤 Default User Accounts

The system automatically creates these accounts for demonstration:

| Role | Username | Password | Description |
|------|----------|----------|--------------|
| 👑 Admin | admin | admin | System administration |
| 🏛️ Government | government | government | Transaction approval |
| 🏡 Seller | seller | seller | Property listing |
| 🔍 Buyer | buyer | buyer | Property purchasing |

## 🔄 System Workflow

1. **User Registration & Authentication**
   - New users register with their desired role
   - Admin and Government roles are auto-approved
   - Buyer and Seller accounts require admin approval

2. **Property Management**
   - Sellers can add land listings with details and pricing
   - Properties are displayed to potential buyers

3. **Transaction Process**
   - Buyers browse available properties and request purchases
   - Sellers receive notifications of purchase requests
   - Government officials review and approve/reject transactions
   - Upon approval, a blockchain record is generated

4. **Record Keeping**
   - All approved transactions are recorded with blockchain IDs
   - Ownership transfers are tracked in the system
   - Public transaction records are viewable on the homepage

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Project dependencies
├── instance/              # Database storage
│   └── land_management.db # SQLite database
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
└── templates/             # HTML templates
    ├── base.html          # Base template with common elements
    ├── index.html         # Homepage
    ├── login.html         # Authentication
    ├── signup.html        # Registration
    ├── add_land.html      # Property listing form
    └── *_dashboard.html   # Role-specific dashboards
```

## 📝 Development Notes

- This is a demonstration project showcasing the concept of blockchain in land registry
- The blockchain functionality is simulated for educational purposes
- For production use, integration with an actual blockchain network would be required

## 🔮 Future Enhancements

- Integration with real blockchain networks (Ethereum, Hyperledger)
- Digital document storage and verification
- Mobile application development
- Advanced property search and filtering
- Payment gateway integration

## 📄 License

This project is available for educational and demonstration purposes.

---

*Hydrib - Transforming land registry with blockchain technology*