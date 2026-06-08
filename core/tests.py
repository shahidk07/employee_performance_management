from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import PermissionDenied
import datetime
from core.models import UserProfile, Department, Employee, Attendance, LeaveRequest, PerformanceReview, ActivityLog

class EPMSTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create department
        self.dept = Department.objects.create(
            name='Test Engineering',
            code='TENG',
            description='Test department description.'
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            username='admin_user',
            password='testpassword123',
            email='admin@test.com'
        )
        self.admin_profile = self.admin_user.userprofile
        self.admin_profile.role = 'ADMIN'
        self.admin_profile.save()

        # Create Manager
        self.mgr_user = User.objects.create_user(
            username='mgr_user',
            password='testpassword123',
            email='mgr@test.com'
        )
        self.mgr_profile = self.mgr_user.userprofile
        self.mgr_profile.role = 'MANAGER'
        self.mgr_profile.save()
        self.mgr_employee = Employee.objects.create(
            user=self.mgr_user,
            employee_id='MGR-TEST',
            full_name='Test Manager',
            email='mgr@test.com',
            department=self.dept,
            designation='Lead Tester',
            date_joined=datetime.date.today(),
            salary=80000.00
        )

        # Create Employee
        self.emp_user = User.objects.create_user(
            username='emp_user',
            password='testpassword123',
            email='emp@test.com'
        )
        self.emp_profile = self.emp_user.userprofile
        self.emp_profile.role = 'EMPLOYEE'
        self.emp_profile.save()
        self.emp_employee = Employee.objects.create(
            user=self.emp_user,
            employee_id='EMP-TEST',
            full_name='Test Employee',
            email='emp@test.com',
            department=self.dept,
            designation='QA Tester',
            date_joined=datetime.date.today(),
            salary=50000.00
        )

    def test_profile_signal_creation(self):
        """Test that UserProfile is automatically created when User is saved."""
        new_user = User.objects.create_user(username='new_user', password='password123')
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())
        self.assertEqual(new_user.userprofile.role, 'EMPLOYEE') # default

    def test_anonymous_redirect_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_role_based_page_restriction(self):
        """Test that role restrictions are enforced (e.g. employee cannot create department)."""
        # Login as Employee
        self.client.login(username='emp_user', password='testpassword123')
        
        # Employee should see dashboard, but get PermissionDenied on department create
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('department_create'))
        self.assertEqual(response.status_code, 403) # raises PermissionDenied which returns 403 Forbidden

    def test_admin_access_allowed(self):
        """Test that administrator can access department creation page."""
        self.client.login(username='admin_user', password='testpassword123')
        response = self.client.get(reverse('department_create'))
        self.assertEqual(response.status_code, 200)

    def test_employee_check_in(self):
        """Test that check_in registers attendance logs correctly."""
        self.client.login(username='emp_user', password='testpassword123')
        
        # Verify no check-in logs exist for today yet
        today = datetime.date.today()
        self.assertFalse(Attendance.objects.filter(employee=self.emp_employee, date=today).exists())
        
        # Post check-in
        response = self.client.post(reverse('attendance_check_in'))
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        
        # Verify check-in log is created
        self.assertTrue(Attendance.objects.filter(employee=self.emp_employee, date=today).exists())
        attendance = Attendance.objects.get(employee=self.emp_employee, date=today)
        self.assertIsNotNone(attendance.check_in)
        self.assertIn(attendance.status, ['PRESENT', 'LATE'])

    def test_performance_review_overall_score(self):
        """Test that overall score is auto-calculated on save."""
        review = PerformanceReview.objects.create(
            employee=self.emp_employee,
            reviewer=self.mgr_user,
            productivity_score=4,
            attendance_score=5,
            teamwork_score=3,
            communication_score=4,
            technical_skills_score=4,
            comments="Good job"
        )
        self.assertEqual(review.overall_score, 4.00)

    def test_activity_logging_on_login(self):
        """Test that ActivityLog registers logins correctly."""
        ActivityLog.objects.all().delete()
        self.client.login(username='admin_user', password='testpassword123')
        self.assertTrue(ActivityLog.objects.filter(action='Login', user=self.admin_user).exists())

    def test_password_reset_request(self):
        """Test that the password reset request works and sends mail."""
        from django.core import mail
        response = self.client.post(reverse('password_reset'), {'email': 'admin@test.com'})
        # Should redirect to password reset done
        self.assertEqual(response.status_code, 302)
        # Should send 1 email
        self.assertEqual(len(mail.outbox), 1)
