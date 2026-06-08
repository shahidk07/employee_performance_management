from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Employee(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.CharField(max_length=100)
    date_joined = models.DateField()
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


class Project(models.Model):
    STATUS_CHOICES = (
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    members = models.ManyToManyField(Employee, related_name='projects', blank=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
        ('HALF_DAY', 'Half Day'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.status})"


class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews_written')
    review_date = models.DateField(auto_now_add=True)
    
    productivity_score = models.IntegerField(default=5)
    attendance_score = models.IntegerField(default=5)
    teamwork_score = models.IntegerField(default=5)
    communication_score = models.IntegerField(default=5)
    technical_skills_score = models.IntegerField(default=5)
    overall_score = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate overall score as average of the five scores
        total = (self.productivity_score + self.attendance_score + 
                 self.teamwork_score + self.communication_score + 
                 self.technical_skills_score)
        self.overall_score = round(total / 5.0, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review for {self.employee.full_name} - Overall Score: {self.overall_score}"


class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = (
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('EARNED', 'Earned Leave'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField()
    actioned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actioned_leaves')
    actioned_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_leave_type_display()} ({self.status})"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} @ {self.timestamp}"


from django.contrib.auth.signals import user_logged_in, user_logged_out

def log_activity(user, action, details=None):
    if user and user.is_authenticated:
        ActivityLog.objects.create(user=user, action=action, details=details)

# Signals to ensure UserProfile creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    log_activity(user, 'Login', 'User logged in successfully.')

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    log_activity(user, 'Logout', 'User logged out successfully.')
