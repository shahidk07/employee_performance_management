from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # D3.js Charts API
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # Reports Page
    path('reports/', views.reports_view, name='reports'),
    path('export/<str:export_type>/', views.export_csv_view, name='export_csv'),
    
    # Settings Page
    path('settings/', views.settings_view, name='admin_settings'),
    path('settings/user/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    path('settings/user/<int:user_id>/status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Department CRUD
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Employee CRUD
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # Project CRUD
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    
    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/check-in/', views.attendance_check_in, name='attendance_check_in'),
    path('attendance/check-out/', views.attendance_check_out, name='attendance_check_out'),
    
    # Performance Reviews
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/create/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
    
    # Leave Requests
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/<str:action>/', views.leave_action, name='leave_action'),
]
