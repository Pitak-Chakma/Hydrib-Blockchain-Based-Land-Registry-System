## Hydrib Blockchain-Based Land Registry System Workflow
### System Overview
This is a blockchain-based land registry system for Bangladesh that digitizes land ownership records and transactions. The system uses Flask (Python) with SQLite database and implements a simple blockchain for transaction integrity.

### User Roles & Workflow
1. Government Official (Admin)

- Manages and approves/rejects land transactions
- Oversees system operations
- Views all pending transactions and system statistics
2. Landowner

- Registers new land properties
- Initiates property transfers/sales
- Views their owned properties and transaction history
3. Buyer

- Browses available properties
- Initiates purchase requests
- Tracks their purchase transactions
### Core Workflow Process
1. 1.
   Land Registration : Landowners register their properties with details like plot number, area, location, etc.
2. 2.
   Property Listing : Registered properties become available for potential buyers
3. 3.
   Purchase Initiation : Buyers can initiate purchase requests for available properties
4. 4.
   Government Approval : Admin reviews and approves/rejects transactions
5. 5.
   Blockchain Recording : Approved transactions are recorded on the blockchain for immutability
6. 6.
   Ownership Transfer : Upon approval, ownership is transferred to the buyer
## Demo Instructions
### Prerequisites
The Flask application is already running on http://127.0.0.1:5001

### Demo Accounts (Ready to Use)
- Government Official : admin@hydrib.gov.bd / admin123
- Landowner : owner@example.com / owner123
- Buyer : buyer@example.com / buyer123
### Step-by-Step Demo
Step 1: Admin Dashboard

1. 1.
   Visit http://127.0.0.1:5001
2. 2.
   Login as admin: admin@hydrib.gov.bd / admin123
3. 3.
   View the admin dashboard showing:
   - System statistics (total lands, users, transactions)
   - Pending transactions for approval
   - Admin controls
Step 2: Landowner Experience

1. 1.
   Logout and login as landowner: owner@example.com / owner123
2. 2.
   View existing properties (2 sample properties are already registered)
3. 3.
   Try registering a new land property:
   - Click "Register New Land"
   - Fill in property details (plot number, area, location, etc.)
   - Submit the registration
Step 3: Buyer Experience

1. 1.
   Logout and login as buyer: buyer@example.com / buyer123
2. 2.
   Browse available properties
3. 3.
   Initiate a purchase:
   - Select a property
   - Fill in purchase details (payment method, transfer date)
   - Submit purchase request
Step 4: Transaction Approval

1. 1.
   Login back as admin: admin@hydrib.gov.bd / admin123
2. 2.
   View the new pending transaction
3. 3.
   Approve or reject the transaction
4. 4.
   Observe how the blockchain records the transaction
Step 5: Verify Blockchain

1. 1.
   Check the ledger/blockchain view to see recorded transactions
2. 2.
   Verify transaction immutability and transparency
### Sample Data Available
- Property 1 : PLT-1111 (111.0 acres, residential, owned by user ID 2)
- Property 2 : PLT-2222 (1.5 acres, residential in Dhaka, owned by user ID 2)
### Key Features to Test
- Security : Role-based access control
- Blockchain : Immutable transaction records
- File Upload : Document management for properties
- Real-time Updates : Dashboard updates after transactions
- Data Validation : Input validation and sanitization