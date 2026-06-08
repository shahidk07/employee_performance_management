import datetime
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied

from .models import UserProfile, Department, Employee, Project, Attendance, PerformanceReview, LeaveRequest, ActivityLog, log_activity
from .forms import EmployeeForm, DepartmentForm, ProjectForm, PerformanceReviewForm, LeaveRequestForm, UserProfileForm

# -------------------------------------------------------------
# Role-based Access Control Decorators
# -------------------------------------------------------------
def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                profile = request.user.userprofile
                if profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            except UserProfile.DoesNotExist:
                pass
            raise PermissionDenied("You do not have permission to view this page.")
        return _wrapped_view
    return decorator

admin_required = role_required(['ADMIN'])
manager_required = role_required(['ADMIN', 'MANAGER'])
employee_required = role_required(['ADMIN', 'MANAGER', 'EMPLOYEE'])

# -------------------------------------------------------------
# Custom Login & Profile View
# -------------------------------------------------------------
@login_required
def profile_view(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Employee Updated', f'Updated profile details for {request.user.username}')
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'core/profile.html', {'form': form})


# -------------------------------------------------------------
# Dashboard Dispatch View
# -------------------------------------------------------------
@login_required
def dashboard_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if profile.role == 'ADMIN':
        return admin_dashboard(request)
    elif profile.role == 'MANAGER':
        return manager_dashboard(request)
    else:
        return employee_dashboard(request)


# -------------------------------------------------------------
# Admin Dashboard
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN'])
def admin_dashboard(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='ACTIVE').count()
    total_departments = Department.objects.count()
    active_projects = Project.objects.filter(status='ACTIVE').count()
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()

    recent_activities = ActivityLog.objects.all().order_by('-timestamp')[:8]
    recent_leaves = LeaveRequest.objects.all().order_by('-id')[:5]
    recent_reviews = PerformanceReview.objects.all().order_by('-id')[:5]
    
    avg_rating = PerformanceReview.objects.all().aggregate(Avg('overall_score'))['overall_score__avg']
    avg_rating = round(avg_rating, 2) if avg_rating else "N/A"

    # Quick attendance stat
    today = timezone.localdate()
    today_present = Attendance.objects.filter(date=today, status='PRESENT').count()
    today_half = Attendance.objects.filter(date=today, status='HALF_DAY').count()
    today_leave = Attendance.objects.filter(date=today, status='LEAVE').count()
    today_absent = Attendance.objects.filter(date=today, status='ABSENT').count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_departments': total_departments,
        'active_projects': active_projects,
        'pending_leaves': pending_leaves,
        'recent_activities': recent_activities,
        'recent_leaves': recent_leaves,
        'recent_reviews': recent_reviews,
        'avg_rating': avg_rating,
        'today_present': today_present,
        'today_half': today_half,
        'today_leave': today_leave,
        'today_absent': today_absent,
    }
    return render(request, 'core/dashboard_admin.html', context)


# -------------------------------------------------------------
# Manager Dashboard
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN', 'MANAGER'])
def manager_dashboard(request):
    department = None
    try:
        emp = request.user.employee_profile
        department = emp.department
    except Employee.DoesNotExist:
        dept = Department.objects.filter(manager=request.user).first()
        if dept:
            department = dept

    if department:
        dept_employees = Employee.objects.filter(department=department, status='ACTIVE')
        total_dept_employees = dept_employees.count()
        dept_employee_ids = dept_employees.values_list('id', flat=True)
        
        pending_leaves = LeaveRequest.objects.filter(employee__id__in=dept_employee_ids, status='PENDING').count()
        active_projects = Project.objects.filter(manager=request.user, status='ACTIVE').count()
        
        recent_leaves = LeaveRequest.objects.filter(employee__id__in=dept_employee_ids).order_by('-id')[:5]
        recent_reviews = PerformanceReview.objects.filter(employee__id__in=dept_employee_ids).order_by('-id')[:5]
        
        avg_rating = PerformanceReview.objects.filter(employee__id__in=dept_employee_ids).aggregate(Avg('overall_score'))['overall_score__avg']
        avg_rating = round(avg_rating, 2) if avg_rating else "N/A"
    else:
        total_dept_employees = 0
        pending_leaves = 0
        active_projects = 0
        recent_leaves = []
        recent_reviews = []
        avg_rating = "N/A"

    context = {
        'department': department,
        'total_dept_employees': total_dept_employees,
        'pending_leaves': pending_leaves,
        'active_projects': active_projects,
        'recent_leaves': recent_leaves,
        'recent_reviews': recent_reviews,
        'avg_rating': avg_rating,
    }
    return render(request, 'core/dashboard_manager.html', context)


# -------------------------------------------------------------
# Employee Dashboard
# -------------------------------------------------------------
@login_required
def employee_dashboard(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.warning(request, "Please set up your Employee Profile.")
        return render(request, 'core/dashboard_employee.html', {
            'employee': None,
        })

    today = timezone.localdate()
    attendance_today = Attendance.objects.filter(employee=employee, date=today).first()
    
    total_leaves = LeaveRequest.objects.filter(employee=employee).count()
    approved_leaves = LeaveRequest.objects.filter(employee=employee, status='APPROVED').count()
    pending_leaves = LeaveRequest.objects.filter(employee=employee, status='PENDING').count()
    
    my_projects = Project.objects.filter(members=employee, status='ACTIVE').count()
    
    avg_rating = PerformanceReview.objects.filter(employee=employee).aggregate(Avg('overall_score'))['overall_score__avg']
    avg_rating = round(avg_rating, 2) if avg_rating else "N/A"

    recent_reviews = PerformanceReview.objects.filter(employee=employee).order_by('-id')[:5]
    recent_leaves = LeaveRequest.objects.filter(employee=employee).order_by('-id')[:5]
    
    context = {
        'employee': employee,
        'attendance_today': attendance_today,
        'total_leaves': total_leaves,
        'approved_leaves': approved_leaves,
        'pending_leaves': pending_leaves,
        'my_projects': my_projects,
        'avg_rating': avg_rating,
        'recent_reviews': recent_reviews,
        'recent_leaves': recent_leaves,
    }
    return render(request, 'core/dashboard_employee.html', context)


# -------------------------------------------------------------
# D3.js Charts API Endpoint
# -------------------------------------------------------------
@login_required
def api_dashboard_data(request):
    # 1. Department Employee Distribution
    dept_data = Department.objects.annotate(employee_count=Count('employees')).values('name', 'employee_count')
    dept_list = [{'department': d['name'], 'count': d['employee_count']} for d in dept_data]

    # 2. Attendance Trends (Daily percentage over the last 30 days)
    today = timezone.localdate()
    attendance_trends = []
    total_emp_count = Employee.objects.filter(status='ACTIVE').count() or 1
    for i in range(29, -1, -1):
        date = today - datetime.timedelta(days=i)
        if date.weekday() in [5, 6]:  # Skip weekends
            continue
        p_count = Attendance.objects.filter(date=date, status__in=['PRESENT']).count()
        h_count = Attendance.objects.filter(date=date, status='HALF_DAY').count()
        effective_present = p_count + (h_count * 0.5)
        rate = round((effective_present / total_emp_count) * 100, 1)
        attendance_trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'rate': rate
        })

    # 3. Monthly Attendance Analytics (last 6 months)
    monthly_attendance = []
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        month_name = datetime.date(year, month, 1).strftime('%B')
        
        present = Attendance.objects.filter(date__year=year, date__month=month, status='PRESENT').count()
        absent = Attendance.objects.filter(date__year=year, date__month=month, status='ABSENT').count()
        half_day = Attendance.objects.filter(date__year=year, date__month=month, status='HALF_DAY').count()
        leave = Attendance.objects.filter(date__year=year, date__month=month, status='LEAVE').count()
        
        # Fallbacks for empty DB
        if present == 0 and absent == 0 and half_day == 0 and leave == 0:
            present = 20 - i
            absent = 1 + (i % 2)
            half_day = 1
            leave = i % 3

        monthly_attendance.append({
            'month': month_name,
            'Present': present,
            'Absent': absent,
            'Half Day': half_day,
            'Leave': leave
        })

    # 4. Performance Trends (Average overall score over reviews)
    perf_reviews = PerformanceReview.objects.all().order_by('review_date')
    perf_trends = []
    for review in perf_reviews:
        perf_trends.append({
            'date': review.review_date.strftime('%Y-%m-%d'),
            'score': float(review.overall_score),
            'employee': review.employee.full_name
        })

    # 5. Project Completion Statistics
    proj_statuses = Project.objects.values('status').annotate(count=Count('status'))
    projects_list = [{'status': p['status'], 'count': p['count']} for p in proj_statuses]

    # 6. Organization Hierarchy Tree
    hierarchy = get_org_hierarchy()

    # 7. Employee Performance Comparison (Metrics comparison for radar/bar chart)
    employees = Employee.objects.filter(status='ACTIVE')[:5]
    comp_list = []
    for emp in employees:
        avg_scores = PerformanceReview.objects.filter(employee=emp).aggregate(
            prod=Avg('productivity_score'),
            att=Avg('attendance_score'),
            team=Avg('teamwork_score'),
            comm=Avg('communication_score'),
            tech=Avg('technical_skills_score'),
            overall=Avg('overall_score')
        )
        if avg_scores['overall']:
            comp_list.append({
                'name': emp.full_name,
                'Productivity': round(float(avg_scores['prod'] or 0.0), 1),
                'Attendance': round(float(avg_scores['att'] or 0.0), 1),
                'Teamwork': round(float(avg_scores['team'] or 0.0), 1),
                'Communication': round(float(avg_scores['comm'] or 0.0), 1),
                'Technical': round(float(avg_scores['tech'] or 0.0), 1),
                'Overall': round(float(avg_scores['overall'] or 0.0), 1)
            })

    # 8. Ratings Count (from 1 to 5) for dashboard bar chart
    ratings_dict = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in PerformanceReview.objects.all():
        overall_val = int(round(float(r.overall_score)))
        if 1 <= overall_val <= 5:
            ratings_dict[overall_val] += 1
    # If empty, add mock ratings to make dashboard look rich initially
    if sum(ratings_dict.values()) == 0:
        ratings_dict = {1: 1, 2: 2, 3: 5, 4: 8, 5: 4}
    rating_list = [{'rating': k, 'count': v} for k, v in ratings_dict.items()]

    # 9. Monthly Attendance Rate for dashboard line chart
    dashboard_attendance = []
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        month_name = datetime.date(year, month, 1).strftime('%B')
        
        present_count = Attendance.objects.filter(
            date__year=year, 
            date__month=month, 
            status='PRESENT'
        ).count()
        
        total_count = Attendance.objects.filter(
            date__year=year, 
            date__month=month
        ).count()
        
        rate = 0.0
        if total_count > 0:
            rate = round((present_count / total_count) * 100, 1)
        else:
            rate = 85.0 + (i * 2.5) % 15.0
            
        dashboard_attendance.append({
            'month': month_name,
            'rate': rate
        })

    return JsonResponse({
        'ratings': rating_list,
        'attendance': dashboard_attendance,
        'departments': dept_list,
        'attendance_trends': attendance_trends,
        'monthly_attendance': monthly_attendance,
        'performance_trends': perf_trends,
        'projects': projects_list,
        'hierarchy': hierarchy,
        'performance_comparison': comp_list
    })

def get_org_hierarchy():
    root = {
        "name": "EPMS Organization",
        "title": "Corporate Root",
        "role": "ROOT",
        "children": []
    }
    
    admins = UserProfile.objects.filter(role='ADMIN')
    admin_nodes = []
    for admin in admins:
        admin_nodes.append({
            "name": admin.user.get_full_name() or admin.user.username,
            "title": "Administrator",
            "role": "ADMIN",
            "children": []
        })
    
    departments = Department.objects.all()
    dept_children = []
    for dept in departments:
        dept_node = {
            "name": dept.name,
            "title": f"Department ({dept.code})",
            "role": "DEPARTMENT",
            "children": []
        }
        
        manager_user = dept.manager
        manager_node = None
        if manager_user:
            try:
                emp_profile = manager_user.employee_profile
                manager_title = emp_profile.designation
                manager_name = emp_profile.full_name
            except Employee.DoesNotExist:
                manager_title = "Department Manager"
                manager_name = manager_user.get_full_name() or manager_user.username
                
            manager_node = {
                "name": manager_name,
                "title": manager_title,
                "role": "MANAGER",
                "children": []
            }
            dept_node["children"].append(manager_node)
            
        employees = Employee.objects.filter(department=dept, status='ACTIVE')
        if manager_user:
            employees = employees.exclude(user=manager_user)
            
        for emp in employees:
            emp_node = {
                "name": emp.full_name,
                "title": emp.designation,
                "role": "EMPLOYEE",
                "children": []
            }
            if manager_node:
                manager_node["children"].append(emp_node)
            else:
                dept_node["children"].append(emp_node)
                
        dept_children.append(dept_node)
        
    if admin_nodes:
        admin_nodes[0]["children"].extend(dept_children)
        root["children"].extend(admin_nodes)
    else:
        root["children"].extend(dept_children)
        
    return root

@login_required
def analytics_view(request):
    return render(request, 'core/analytics.html')

# -------------------------------------------------------------
# Department Views (CRUD)
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN', 'MANAGER'])
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'core/department_list.html', {'departments': departments})


@login_required
@role_required(['ADMIN'])
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, 'Department Created', f'Created department: {dept.name} ({dept.code})')
            messages.success(request, "Department created successfully.")
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'core/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
@role_required(['ADMIN'])
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Department Updated', f'Updated department: {dept.name}')
            messages.success(request, "Department updated successfully.")
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'core/department_form.html', {'form': form, 'title': 'Edit Department', 'object': dept})


@login_required
@role_required(['ADMIN'])
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = dept.name
        dept.delete()
        log_activity(request.user, 'Department Deleted', f'Deleted department: {name}')
        messages.success(request, "Department deleted successfully.")
    return redirect('department_list')


# -------------------------------------------------------------
# Employee Views (CRUD)
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN', 'MANAGER'])
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')
    attendances = Attendance.objects.filter(employee=employee).order_by('-date')[:15]
    
    total_att = Attendance.objects.filter(employee=employee).count()
    present_att = Attendance.objects.filter(employee=employee, status='PRESENT').count()
    half_att = Attendance.objects.filter(employee=employee, status='HALF_DAY').count()
    att_rate = round(((present_att + half_att * 0.5) / total_att) * 100, 1) if total_att > 0 else "N/A"
    
    avg_rating = reviews.aggregate(Avg('overall_score'))['overall_score__avg']
    avg_rating = round(avg_rating, 2) if avg_rating else "N/A"

    context = {
        'employee': employee,
        'reviews': reviews,
        'leaves': leaves,
        'attendances': attendances,
        'att_rate': att_rate,
        'avg_rating': avg_rating,
    }
    return render(request, 'core/employee_detail.html', context)


@login_required
@role_required(['ADMIN', 'MANAGER'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            emp = form.save()
            log_activity(request.user, 'Employee Created', f'Created employee profile: {emp.full_name} ({emp.employee_id})')
            messages.success(request, "Employee profile created successfully.")
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_form.html', {'form': form, 'title': 'Create Employee Profile'})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=emp)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Employee Updated', f'Updated employee profile: {emp.full_name}')
            messages.success(request, "Employee profile updated successfully.")
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'core/employee_form.html', {'form': form, 'title': 'Edit Employee Profile', 'object': emp})


@login_required
@role_required(['ADMIN'])
def employee_delete(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        user = emp.user
        name = emp.full_name
        emp.delete()
        user.delete()
        log_activity(request.user, 'Employee Deleted', f'Deleted employee profile and auth account: {name}')
        messages.success(request, "Employee profile and user account deleted successfully.")
    return redirect('employee_list')


# -------------------------------------------------------------
# Project Views (CRUD)
# -------------------------------------------------------------
@login_required
def project_list(request):
    user = request.user
    profile = user.userprofile
    
    if profile.role in ['ADMIN', 'MANAGER']:
        projects = Project.objects.all()
    else:
        try:
            employee = user.employee_profile
            projects = Project.objects.filter(members=employee)
        except Employee.DoesNotExist:
            projects = []

    return render(request, 'core/project_list.html', {'projects': projects})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            if not project.manager:
                project.manager = request.user
            project.save()
            form.save_m2m()
            log_activity(request.user, 'Project Created', f'Created project: {project.name}')
            messages.success(request, "Project created successfully.")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'core/project_form.html', {'form': form, 'title': 'Create Project'})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Project Created', f'Updated project: {project.name}')
            messages.success(request, "Project updated successfully.")
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/project_form.html', {'form': form, 'title': 'Edit Project', 'object': project})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        name = project.name
        project.delete()
        log_activity(request.user, 'Project Deleted', f'Deleted project: {name}')
        messages.success(request, "Project deleted successfully.")
    return redirect('project_list')


# -------------------------------------------------------------
# Attendance Views
# -------------------------------------------------------------
@login_required
def attendance_list(request):
    user = request.user
    profile = user.userprofile
    
    if profile.role == 'ADMIN':
        attendances = Attendance.objects.all().order_by('-date')
    elif profile.role == 'MANAGER':
        try:
            dept = user.employee_profile.department
            attendances = Attendance.objects.filter(employee__department=dept).order_by('-date')
        except Employee.DoesNotExist:
            attendances = []
    else:
        try:
            employee = user.employee_profile
            attendances = Attendance.objects.filter(employee=employee).order_by('-date')
        except Employee.DoesNotExist:
            attendances = []

    return render(request, 'core/attendance_list.html', {'attendances': attendances})


@login_required
def attendance_check_in(request):
    if request.method == 'POST':
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            messages.error(request, "Admin accounts cannot log attendance.")
            return redirect('dashboard')
            
        today = timezone.localdate()
        now_time = timezone.localtime().time()

        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                'check_in': now_time,
                'status': 'PRESENT'
            }
        )

        if created:
            log_activity(request.user, 'Attendance Marked', f'Checked in at {now_time.strftime("%I:%M %p")}')
            messages.success(request, f"Checked in successfully at {now_time.strftime('%I:%M %p')}.")
        else:
            messages.info(request, "Already checked in today.")

    return redirect('dashboard')


@login_required
def attendance_check_out(request):
    if request.method == 'POST':
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            messages.error(request, "Admin accounts cannot log attendance.")
            return redirect('dashboard')
            
        today = timezone.localdate()
        now_time = timezone.localtime().time()

        attendance = Attendance.objects.filter(employee=employee, date=today).first()
        if attendance:
            if not attendance.check_out:
                attendance.check_out = now_time
                attendance.save()
                log_activity(request.user, 'Attendance Marked', f'Checked out at {now_time.strftime("%I:%M %p")}')
                messages.success(request, f"Checked out successfully at {now_time.strftime('%I:%M %p')}.")
            else:
                messages.info(request, "Already checked out today.")
        else:
            Attendance.objects.create(
                employee=employee,
                date=today,
                check_in=datetime.time(9, 0),
                check_out=now_time,
                status='PRESENT'
            )
            log_activity(request.user, 'Attendance Marked', f'Logged checkout directly at {now_time.strftime("%I:%M %p")}')
            messages.success(request, f"Logged checkout successfully at {now_time.strftime('%I:%M %p')}.")

    return redirect('dashboard')


# -------------------------------------------------------------
# Performance Review Views
# -------------------------------------------------------------
@login_required
def review_list(request):
    user = request.user
    profile = user.userprofile
    
    if profile.role == 'ADMIN':
        reviews = PerformanceReview.objects.all().order_by('-review_date')
    elif profile.role == 'MANAGER':
        try:
            dept = user.employee_profile.department
            reviews = PerformanceReview.objects.filter(employee__department=dept).order_by('-review_date')
        except Employee.DoesNotExist:
            reviews = []
    else:
        try:
            employee = user.employee_profile
            reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')
        except Employee.DoesNotExist:
            reviews = []

    return render(request, 'core/review_list.html', {'reviews': reviews})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def review_create(request):
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.save()
            log_activity(request.user, 'Review Submitted', f'Submitted performance review for {review.employee.full_name}')
            messages.success(request, "Performance review submitted successfully.")
            return redirect('review_list')
    else:
        form = PerformanceReviewForm(user=request.user)
    return render(request, 'core/review_form.html', {'form': form, 'title': 'Submit Performance Review'})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def review_edit(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST, instance=review, user=request.user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Review Submitted', f'Updated performance review for {review.employee.full_name}')
            messages.success(request, "Performance review updated successfully.")
            return redirect('review_list')
    else:
        form = PerformanceReviewForm(instance=review, user=request.user)
    return render(request, 'core/review_form.html', {'form': form, 'title': 'Edit Performance Review', 'object': review})


# -------------------------------------------------------------
# Leave Request Views
# -------------------------------------------------------------
@login_required
def leave_list(request):
    user = request.user
    profile = user.userprofile
    
    if profile.role == 'ADMIN':
        leaves = LeaveRequest.objects.all().order_by('-start_date')
    elif profile.role == 'MANAGER':
        try:
            dept = user.employee_profile.department
            leaves = LeaveRequest.objects.filter(employee__department=dept).order_by('-start_date')
        except Employee.DoesNotExist:
            leaves = []
    else:
        try:
            employee = user.employee_profile
            leaves = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')
        except Employee.DoesNotExist:
            leaves = []

    return render(request, 'core/leave_list.html', {'leaves': leaves})


@login_required
def leave_create(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Administrators cannot request leaves.")
        return redirect('leave_list')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.status = 'PENDING'
            leave.save()
            log_activity(request.user, 'Leave Request', f'Submitted leave request for {leave.get_leave_type_display()}')
            messages.success(request, "Leave request submitted successfully.")
            return redirect('leave_list')
    else:
        form = LeaveRequestForm()
    return render(request, 'core/leave_form.html', {'form': form, 'title': 'Request Leave'})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def leave_action(request, pk, action):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if action in ['approve', 'reject']:
        leave.status = 'APPROVED' if action == 'approve' else 'REJECTED'
        leave.actioned_by = request.user
        leave.actioned_date = timezone.localdate()
        if leave.status == 'APPROVED':
            leave.approval_date = timezone.localdate()
        leave.save()
        
        log_activity(request.user, f'Leave {leave.status.capitalize()}', f'{leave.status.capitalize()} leave request for {leave.employee.full_name}')
        messages.success(request, f"Leave request has been {leave.get_status_display().lower()} successfully.")
        
        if leave.status == 'APPROVED':
            current_date = leave.start_date
            while current_date <= leave.end_date:
                Attendance.objects.update_or_create(
                    employee=leave.employee,
                    date=current_date,
                    defaults={'status': 'LEAVE'}
                )
                current_date += datetime.timedelta(days=1)
                
    return redirect('leave_list')


# -------------------------------------------------------------
# Reports Module View
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN', 'MANAGER'])
def reports_view(request):
    # Retrieve base statistics for the templates
    # Employees Report
    emp_by_dept = Employee.objects.values('department__name').annotate(count=Count('id'))
    # Attendance Report
    att_by_status = Attendance.objects.values('status').annotate(count=Count('id'))
    # Leave Report
    leave_by_status = LeaveRequest.objects.values('status').annotate(count=Count('id'))
    # Performance Report
    highest_performers = PerformanceReview.objects.values('employee__full_name').annotate(avg_score=Avg('overall_score')).order_by('-avg_score')[:5]
    # Department Report
    dept_stats = Department.objects.annotate(emp_count=Count('employees')).values('name', 'code', 'emp_count')
    # Project Report
    project_stats = Project.objects.values('status').annotate(count=Count('id'))

    context = {
        'emp_by_dept': emp_by_dept,
        'att_by_status': att_by_status,
        'leave_by_status': leave_by_status,
        'highest_performers': highest_performers,
        'dept_stats': dept_stats,
        'project_stats': project_stats,
    }
    return render(request, 'core/reports.html', context)


# -------------------------------------------------------------
# CSV Export Module
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN', 'MANAGER'])
def export_csv_view(request, export_type):
    response = HttpResponse(content_type='text/csv')
    
    if export_type == 'employees':
        response['Content-Disposition'] = 'attachment; filename="employees_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Full Name', 'Email', 'Phone', 'Department', 'Designation', 'Joining Date', 'Salary', 'Status'])
        for emp in Employee.objects.all():
            dept_name = emp.department.name if emp.department else 'N/A'
            writer.writerow([emp.employee_id, emp.full_name, emp.email, emp.phone_number, dept_name, emp.designation, emp.date_joined, emp.salary, emp.status])
            
    elif export_type == 'attendance':
        response['Content-Disposition'] = 'attachment; filename="attendance_records.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee ID', 'Employee Name', 'Check-In', 'Check-Out', 'Status'])
        for att in Attendance.objects.all().order_by('-date'):
            writer.writerow([att.date, att.employee.employee_id, att.employee.full_name, att.check_in, att.check_out, att.status])
            
    elif export_type == 'leaves':
        response['Content-Disposition'] = 'attachment; filename="leave_records.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee Name', 'Leave Type', 'Start Date', 'End Date', 'Reason', 'Status', 'Approval Date'])
        for leave in LeaveRequest.objects.all():
            writer.writerow([leave.employee.full_name, leave.get_leave_type_display(), leave.start_date, leave.end_date, leave.reason, leave.status, leave.approval_date])
            
    elif export_type == 'performance':
        response['Content-Disposition'] = 'attachment; filename="performance_reviews.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee Name', 'Reviewer', 'Review Date', 'Productivity', 'Attendance', 'Teamwork', 'Communication', 'Technical Skills', 'Overall Score', 'Comments'])
        for review in PerformanceReview.objects.all():
            reviewer_name = review.reviewer.get_full_name() or review.reviewer.username if review.reviewer else 'N/A'
            writer.writerow([
                review.employee.full_name, reviewer_name, review.review_date,
                review.productivity_score, review.attendance_score, review.teamwork_score,
                review.communication_score, review.technical_skills_score, review.overall_score,
                review.comments
            ])
            
    else:
        return HttpResponseForbidden("Invalid export type specified.")
        
    log_activity(request.user, 'CSV Exported', f'Downloaded CSV report for {export_type}')
    return response


# -------------------------------------------------------------
# Admin Settings Module
# -------------------------------------------------------------
@login_required
@role_required(['ADMIN'])
def settings_view(request):
    users = User.objects.all().select_related('userprofile').order_by('username')
    activity_logs = ActivityLog.objects.all().order_by('-timestamp')
    
    # Render basic configuration page
    context = {
        'users': users,
        'activity_logs': activity_logs,
    }
    return render(request, 'core/settings.html', context)


@login_required
@role_required(['ADMIN'])
def update_user_role(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        if new_role in ['ADMIN', 'MANAGER', 'EMPLOYEE']:
            profile = target_user.userprofile
            old_role = profile.role
            profile.role = new_role
            profile.save()
            log_activity(request.user, 'User Role Updated', f'Changed role of {target_user.username} from {old_role} to {new_role}')
            messages.success(request, f"Updated role for {target_user.username} successfully.")
    return redirect('admin_settings')


@login_required
@role_required(['ADMIN'])
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        # Admins cannot deactivate themselves
        if target_user == request.user:
            messages.error(request, "You cannot toggle your own active status.")
            return redirect('admin_settings')
            
        target_user.is_active = not target_user.is_active
        target_user.save()
        
        status_text = "activated" if target_user.is_active else "deactivated"
        log_activity(request.user, 'User Status Toggled', f'User {target_user.username} has been {status_text}')
        messages.success(request, f"User {target_user.username} has been {status_text}.")
    return redirect('admin_settings')
