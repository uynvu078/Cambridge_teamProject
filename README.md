# User Management System - Team Cambridge
Welcome to our project repository!


## How to Access Web Application with Docker
1. Install Docker and Docker Compose
2. Clone the repository at https://uynvu078.github.io/Cambridge_teamProject/
3. In cmd prompt change directories to the clone
4. Enter "cp .env.example .env" (Linux/macOS) or "copy .env.example .env" (Windows)
5. Then enter "docker-compose build" and then "docker-compose up"
6. Once running go to the url: http://localhost:8000/
7. Want access to a basic account, create a new user
8. Want access to an admin account- Username: admin   Password: adminpassword


## Overview
A web-based **User Management System** that leverages **Office 365 authentication** and provides **role-based access control (RBAC)**, user management, and security features.

---

## Features
- **Office 365 Authentication** - Users log in with their Microsoft accounts.  
- **User Management (CRUD)** - Admins can create, read, update, and delete user accounts.  
- **Role-Based Access Control (RBAC)** - Assign different roles (Admin, Basic User).  
- **User Deactivation & Reactivation** - Admins can disable and enable accounts.  
- **Secure Password Management** - Uses Django authentication best practices.  
- **Intuitive UI** - Clean and user-friendly login and dashboard interface.  

---

## Tech Stack
- **Backend**: Django, Python  
- **Frontend**: HTML, CSS  
- **Database**: PostgreSQL  
- **Authentication**: Microsoft Graph API (Office 365 OAuth)  
- **Version Control**: Git & GitHub  

---

This project is licensed under the MIT License - see the COPYRIGHT.md file for details.
