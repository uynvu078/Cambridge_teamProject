# User Management System

## Overview
The User Management System is a web-based application that enables administrators to manage users, roles, and access permissions efficiently. This project integrates Office365 authentication using Microsoft Graph API and includes role-based access control (RBAC).

## Step by Step Feature

### **1. Authentication** 
- Users can authenticate using their Office365 credentials via Microsoft OAuth.
- Secure login and logout system implemented with Django Allauth.

### **2. User Management (CRUD)**
- Administrators can **Create, Read, Update, and Delete (CRUD)** user accounts.
- User attributes include:
  - **Username**
  - **Email**
  - **Role** (Admin, Basic User)
  - **Status** (Active/Inactive)
- Restriction applied: Non-admin users cannot create or edit user roles.

### **3. Role-Based Access Control (RBAC)**
- Different user roles with varying levels of access.
- **Administrators** can assign and modify roles.
- Users with "basicuser" role are restricted from accessing admin functions.
- Role validation added to user forms to prevent unauthorized modifications.

### **4. User Deactivation (Pending)**
- Administrators will be able to deactivate user accounts.
- Deactivated users should not be able to log in or access system resources.
- System will provide a mechanism for reactivating user accounts when needed.

### **5. UI Improvements & Pagination**
- Enhanced **user list page** with:
  - **Search functionality** (by username or role)
  - **Filtering options** (by role: Admin, Basic User)
  - **Pagination** (10 users per page for better performance)
- **Styled tables & buttons** for better user experience.

## Repository Links
- **GitHub Repository:** [https://github.com/uynvu078/Cambridge_teamProject.git]
- **GitHub Project Board:** [https://github.com/users/uynvu078/projects/6)]

## Contributors
- Uyen Vu
- Colton Richie
- Patrick Do
- Rianice Cuebas-Blanco

