# Blockchain Land Management System

A demonstration website for a hybrid blockchain-based land management system. This system simulates the use of blockchain technology for secure and transparent land transactions.

## Features

- **Role-based access control** with 4 user roles + guests:
  - **Admin**: Manages system overview, monitors users, approves buyer/seller accounts
  - **Government Official**: Approves land transactions and generates blockchain records
  - **Seller (Land Owner)**: Creates and posts land listings for sale
  - **Buyer**: Browses land listings and requests purchases
  - **Guest**: Views homepage and general information only

- **Simulated blockchain functionality** for demonstration purposes
- **Clean, modern UI** using Bootstrap
- **Secure authentication** with password hashing

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Open your browser and navigate to `http://127.0.0.1:5000`

## Default Users

The system automatically creates the following default users for demonstration:

- **Admin**:
  - Username: admin
  - Password: admin

- **Government Official**:
  - Username: government
  - Password: government

- **Seller**:
  - Username: seller
  - Password: seller

- **Buyer**:
  - Username: buyer
  - Password: buyer

## System Flow

1. **Signup/Login**: Users register with their desired role
2. **Admin Approval**: Admin approves Buyer/Seller accounts
3. **Seller Lists Land**: Sellers post land properties for sale
4. **Buyer Requests Purchase**: Buyers browse listings and request to buy
5. **Government Approval**: Government officials approve/reject transactions
6. **Blockchain Record**: Upon approval, a simulated blockchain record is generated
7. **Dashboard Updates**: Buyer sees purchased land, Seller sees sold land

## Project Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates for all pages
- `static/`: CSS and JavaScript files
- `land_management.db`: SQLite database (created on first run)

## Note

This is a demonstration project. The blockchain functionality is simulated for demonstration purposes only and does not involve actual blockchain technology.