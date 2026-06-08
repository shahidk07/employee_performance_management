# Employee Performance Management System (EPMS) - Project Requirements

This document preserves the official specifications and scope of the Employee Performance Management System.

## Core Architecture

### Authentication & Authorization
* Login Page
* Logout Functionality
* Forgot Password Page
* Password Reset Workflow (with SMTP Email Integration)
* Change Password Page
* Session-Based Authentication
* Role-Based Access Control

### User Roles
* **Admin:** Full system oversight, configurations, user management, and audit logs.
* **Manager:** Manage department staff, project assignments, attendance reviews, leave requests, and performance evaluations.
* **Employee:** Mark attendance, apply for leaves, view assigned projects, and read performance reviews.

### Dashboard UIs
* Role-specific dashboard views.
* Key performance indicator (KPI) cards.
* Recent activities feed.
* Quick actions panel.

## Database Models

### UserProfile
* User (One-to-One)
* Role (ADMIN, MANAGER, EMPLOYEE)
* Profile Picture
* Phone Number
* Address

### Department
* Name
* Code (Unique)
* Description
* Manager (Foreign Key to User)

### Employee
* User (One-to-One)
* Employee ID (Unique)
* Full Name
* Email
* Phone Number
* Department (Foreign Key to Department)
* Designation
* Date Joined
* Salary
* Status (Active/Inactive)
* Profile Picture

### Project
* Name
* Description
* Start Date
* End Date
* Status (Planning, Active, Completed, On Hold)
* Manager (Foreign Key to User)
* Members (Many-to-Many to Employee)

### Attendance
* Employee (Foreign Key to Employee)
* Date
* Check-In Time
* Check-Out Time
* Status (Present, Absent, Leave, Half Day)

### LeaveRequest
* Employee (Foreign Key to Employee)
* Leave Type (Casual Leave, Sick Leave, Earned Leave)
* Start Date
* End Date
* Status (Pending, Approved, Rejected)
* Reason
* Actioned By (Foreign Key to User)
* Actioned Date
* Approval Date

### PerformanceReview
* Employee (Foreign Key to Employee)
* Reviewer (Foreign Key to User)
* Review Date
* Productivity Score (1 to 5 Stars)
* Attendance Score (1 to 5 Stars)
* Teamwork Score (1 to 5 Stars)
* Communication Score (1 to 5 Stars)
* Technical Skills Score (1 to 5 Stars)
* Overall Performance Score (Average)
* Comments

### ActivityLog
* User (Foreign Key to User)
* Action
* Timestamp
* Details

## Operational Modules

### Employee Management
* Add, Edit, Delete Employees.
* Employee Profile and Detail Views.
* Live filterable search and sorting using DataTables.

### Department Management
* Create, Edit, Delete Departments.
* Department details and employee directory.

### Attendance Management
* Mark Attendance (Check-in/Check-out).
* Daily attendance grids and filterable history.

### Project Management
* Create, Edit, Delete Projects.
* Member assignment and status tracking (Not Started, In Progress, Completed).

### Leave Management
* Apply for leaves.
* Approvals and rejections workflow.
* Personal leave tracking.

## Analytics & Visualizations

### D3.js Charts
1. **Department Distribution:** Donut chart of staff allocation.
2. **Attendance Trends:** 30-day percentage line chart.
3. **Monthly Attendance:** Grouped bar chart (Present vs. Absent vs. Half Day vs. Leave).
4. **Performance Trends:** Timeline score chart.
5. **Project Progress:** Status distribution horizontal bar chart.
6. **Organization Hierarchy:** Collapsible node-link tree chart.
7. **Performance Comparison:** Multi-bar radar comparison of employee core metrics.

### Reporting & Exports
* Generate Employee, Attendance, Leave, Performance, and Department reports.
* Download reports, employee records, and reviews as **CSV** files.

## Polish & Security
* CSRF and session validations.
* SweetAlert2 confirmation prompts and success toasts.
* DataTables pagination.
* Breadcrumbs navigation.
* Responsive sidebar and top navbar layout.
