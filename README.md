# Disaster Risk Information Management System

A comprehensive web application for managing disaster response efforts with role-based access control.

## Features

- **Role-based access**: Admin, Volunteer, and Donor roles with appropriate permissions
- **Evacuation center management**: Create and monitor evacuation centers
- **Evacuee tracking**: Register evacuees and organize them into families
- **Donation management**: Track donations from receipt to distribution
- **Inventory management**: Monitor supplies with expiration tracking for food items
- **Responsive design**: Mobile-friendly interface using Bootstrap

## Installation Guide

### Running locally with MySQL (XAMPP)

1. **Install Python 3.11**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Download the project**
   - Download all files from this Replit project

3. **Create a virtual environment** (recommended)
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

4. **Install dependencies**
   ```
   python -m pip install -r local_requirements.txt
   ```

5. **Configure MySQL in XAMPP**
   - Start XAMPP Control Panel and start Apache and MySQL
   - Open phpMyAdmin (http://localhost/phpmyadmin)
   - Create a new database named `disaster_risk_db`

6. **Update the database connection**
   - Modify `app.py` to use MySQL instead of PostgreSQL
   - Change the SQLALCHEMY_DATABASE_URI to:
     ```python
     app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://username:password@localhost/disaster_risk_db"
     ```
     (Replace username and password with your MySQL credentials, typically "root" with empty password for XAMPP)

7. **Run the application**
   ```
   python main.py
   ```

8. **Access the application**
   - Open a browser and go to http://localhost:5000
   - Register a new account or use the default admin:
     - Username: admin
     - Password: admin123

## User Roles

1. **Admin**
   - Full access to all features
   - Manage users, evacuation centers, evacuees, families, donations, and inventory

2. **Volunteer**
   - Process donations and update inventory
   - Register and manage evacuees
   - Track distribution of supplies

3. **Donor**
   - View evacuation centers
   - Make and track donations

## Contact & Support

For questions or issues, please contact the development team.