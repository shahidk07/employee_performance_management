import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Department, Employee, Project, Attendance, PerformanceReview, LeaveRequest, ActivityLog
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds the database with departments, users, projects, attendance logs, reviews, leaves, and activity logs.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # 1. Clean existing records
        ActivityLog.objects.all().delete()
        LeaveRequest.objects.all().delete()
        PerformanceReview.objects.all().delete()
        Attendance.objects.all().delete()
        Project.objects.all().delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

        # Create fresh superuser
        admin_user = User.objects.create_superuser(
            username='admin',
            email='viperoflegendkiller@gmail.com',
            password='admin12345',
            first_name='System',
            last_name='Admin'
        )
        self.stdout.write('Created fresh superuser (admin/admin12345).')

        # Ensure admin UserProfile is ADMIN role
        admin_profile = admin_user.userprofile
        admin_profile.role = 'ADMIN'
        admin_profile.phone_number = '+1555111222'
        admin_profile.address = '100 Head Office Blvd, Metropolis'
        admin_profile.save()

        # 2. Create Users & Profiles
        # Manager
        mgr_user = User.objects.create_user(
            username='manager',
            email='manager@epms.com',
            password='manager12345',
            first_name='Alex',
            last_name='Manager'
        )
        mgr_profile = mgr_user.userprofile
        mgr_profile.role = 'MANAGER'
        mgr_profile.phone_number = '+1555000101'
        mgr_profile.address = '456 Manager Lane, Suburbia'
        mgr_profile.save()

        # Employee
        emp_user = User.objects.create_user(
            username='employee',
            email='employee@epms.com',
            password='employee12345',
            first_name='John',
            last_name='Employee'
        )
        emp_profile = emp_user.userprofile
        emp_profile.role = 'EMPLOYEE'
        emp_profile.phone_number = '+1555000202'
        emp_profile.address = '789 Worker Way, City Center'
        emp_profile.save()

        # Extra Employee 2
        emp2_user = User.objects.create_user(
            username='employee2',
            email='sarah@epms.com',
            password='employee12345',
            first_name='Sarah',
            last_name='Developer'
        )
        emp2_profile = emp2_user.userprofile
        emp2_profile.role = 'EMPLOYEE'
        emp2_profile.phone_number = '+1555000303'
        emp2_profile.address = '321 Tech Blvd, Innovate District'
        emp2_profile.save()

        self.stdout.write('Created Users (admin, manager, employee, employee2).')

        # 3. Create Departments
        eng_dept = Department.objects.create(
            name='Engineering',
            code='ENG',
            description='Software engineering, QA, and platform infrastructure.',
            manager=mgr_user
        )
        sales_dept = Department.objects.create(
            name='Sales & Marketing',
            code='SAL',
            description='Client acquisitions, advertising, and marketing.',
            manager=admin_user
        )
        self.stdout.write('Created Departments (Engineering, Sales).')

        # 4. Create Employee profiles
        mgr_employee = Employee.objects.create(
            user=mgr_user,
            employee_id='MGR-001',
            full_name='Alex Manager',
            email='manager@epms.com',
            phone_number='+1555000101',
            department=eng_dept,
            designation='Engineering Lead',
            date_joined=datetime.date(2025, 1, 15),
            salary=95000.00,
            status='ACTIVE'
        )

        emp_employee = Employee.objects.create(
            user=emp_user,
            employee_id='EMP-101',
            full_name='John Employee',
            email='employee@epms.com',
            phone_number='+1555000202',
            department=eng_dept,
            designation='Software Engineer',
            date_joined=datetime.date(2025, 6, 1),
            salary=75000.00,
            status='ACTIVE'
        )

        emp2_employee = Employee.objects.create(
            user=emp2_user,
            employee_id='EMP-102',
            full_name='Sarah Developer',
            email='sarah@epms.com',
            phone_number='+1555000303',
            department=eng_dept,
            designation='Senior QA Tester',
            date_joined=datetime.date(2025, 9, 1),
            salary=82000.00,
            status='ACTIVE'
        )
        self.stdout.write('Created Employee profiles.')

        # 5. Create Projects
        epms_project = Project.objects.create(
            name='EPMS Integration',
            description='Build and deploy the Employee Performance Management System.',
            start_date=datetime.date(2026, 5, 1),
            end_date=datetime.date(2026, 7, 30),
            status='ACTIVE',
            manager=mgr_user
        )
        epms_project.members.add(emp_employee)
        epms_project.members.add(emp2_employee)

        analytics_project = Project.objects.create(
            name='Enterprise Data Analytics',
            description='Analyze department health matrices and feed visualization nodes.',
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 12, 15),
            status='PLANNING',
            manager=admin_user
        )
        self.stdout.write('Created Projects.')

        # 6. Create Attendance Logs (simulate last 20 work days)
        today = timezone.localdate()
        for i in range(20, 0, -1):
            date = today - datetime.timedelta(days=i)
            if date.weekday() in [5, 6]: # Skip weekends
                continue
            
            # Manager Attendance
            Attendance.objects.create(
                employee=mgr_employee,
                date=date,
                check_in=datetime.time(8, 55),
                check_out=datetime.time(17, 30),
                status='PRESENT'
            )
            
            # Employee 1 Attendance (mix Present, Half day, Absent)
            status1 = 'PRESENT'
            check_in1 = datetime.time(9, 0)
            if i in [3, 13]:
                status1 = 'ABSENT'
                check_in1 = None
            elif i == 7:
                status1 = 'HALF_DAY'
                check_in1 = datetime.time(9, 10)
            
            Attendance.objects.create(
                employee=emp_employee,
                date=date,
                check_in=check_in1,
                check_out=datetime.time(17, 0) if status1 == 'PRESENT' else (datetime.time(13, 0) if status1 == 'HALF_DAY' else None),
                status=status1
            )

            # Employee 2 Attendance
            status2 = 'PRESENT'
            check_in2 = datetime.time(8, 45)
            if i == 11:
                status2 = 'LEAVE'
                check_in2 = None

            Attendance.objects.create(
                employee=emp2_employee,
                date=date,
                check_in=check_in2,
                check_out=datetime.time(17, 15) if status2 == 'PRESENT' else None,
                status=status2
            )

        self.stdout.write('Simulated Attendance Logs.')

        # 7. Create Performance Reviews (using new 1-5 metrics)
        PerformanceReview.objects.create(
            employee=emp_employee,
            reviewer=mgr_user,
            productivity_score=4,
            attendance_score=3,
            teamwork_score=5,
            communication_score=4,
            technical_skills_score=4,
            comments='John has shown excellent code contributions and fast integration with the backend stack. Proactive team player. Needs to improve attendance score slightly.'
        )
        
        PerformanceReview.objects.create(
            employee=emp2_employee,
            reviewer=mgr_user,
            productivity_score=5,
            attendance_score=5,
            teamwork_score=4,
            communication_score=4,
            technical_skills_score=5,
            comments='Sarah performed outstandingly on QA framework design. Excellent diligence, superb timekeeping, and complete ownership of testing workflows.'
        )

        PerformanceReview.objects.create(
            employee=emp_employee,
            reviewer=admin_user,
            productivity_score=5,
            attendance_score=4,
            teamwork_score=4,
            communication_score=5,
            technical_skills_score=5,
            comments='John performed outstandingly on the EPMS architecture prototype! He demonstrated complete ownership and solved complex security protocols.'
        )
        self.stdout.write('Created Performance Reviews.')

        # 8. Create Leave Requests
        LeaveRequest.objects.create(
            employee=emp_employee,
            leave_type='CASUAL',
            start_date=today - datetime.timedelta(days=12),
            end_date=today - datetime.timedelta(days=11),
            status='APPROVED',
            reason='Family gathering.',
            actioned_by=mgr_user,
            actioned_date=today - datetime.timedelta(days=15),
            approval_date=today - datetime.timedelta(days=15)
        )
        
        LeaveRequest.objects.create(
            employee=emp2_employee,
            leave_type='SICK',
            start_date=today + datetime.timedelta(days=5),
            end_date=today + datetime.timedelta(days=6),
            status='PENDING',
            reason='Medical checkup.',
        )
        self.stdout.write('Created Leave Requests.')

        # 9. Create Activity Logs
        ActivityLog.objects.create(user=admin_user, action='Login', details='Admin logged in successfully.')
        ActivityLog.objects.create(user=admin_user, action='Employee Created', details='Created profile for John Employee.')
        ActivityLog.objects.create(user=admin_user, action='Employee Created', details='Created profile for Sarah Developer.')
        ActivityLog.objects.create(user=mgr_user, action='Project Created', details='Created project EPMS Integration.')
        ActivityLog.objects.create(user=mgr_user, action='Review Submitted', details='Submitted performance review for John Employee.')
        ActivityLog.objects.create(user=mgr_user, action='Review Submitted', details='Submitted performance review for Sarah Developer.')
        self.stdout.write('Created Activity Logs.')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
