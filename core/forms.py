from django import forms
from django.contrib.auth.models import User
from .models import Department, Employee, Project, PerformanceReview, LeaveRequest, UserProfile
from django.core.exceptions import ValidationError

class EmployeeForm(forms.ModelForm):
    # User model fields to create user simultaneously
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}), required=False, help_text="Leave blank to keep current password (when editing).")
    role = forms.ChoiceField(choices=(('EMPLOYEE', 'Employee'), ('MANAGER', 'Manager')), widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))

    class Meta:
        model = Employee
        fields = ['employee_id', 'full_name', 'email', 'phone_number', 'department', 'designation', 'date_joined', 'salary', 'status', 'profile_picture']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'full_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'department': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'designation': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'date_joined': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'salary': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['role'].initial = self.instance.user.userprofile.role
            # If editing, username field should be readonly to prevent collisions
            self.fields['username'].disabled = True
            # Password not strictly required when editing
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.instance.pk: # Only check on creation
            if User.objects.filter(username=username).exists():
                raise ValidationError("Username already exists.")
        return username

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        qs = Employee.objects.filter(employee_id=employee_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Employee ID already exists.")
        return employee_id

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        if self.instance.pk:
            # Edit Flow
            employee = super().save(commit=False)
            user = employee.user
            user.email = cleaned_data.get('email')
            name_parts = cleaned_data.get('full_name').split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            pwd = cleaned_data.get('password')
            if pwd:
                user.set_password(pwd)
            user.save()
            
            # Save role
            profile = user.userprofile
            profile.role = cleaned_data.get('role')
            if employee.profile_picture:
                profile.profile_picture = employee.profile_picture
            profile.phone_number = employee.phone_number
            profile.save()
            
            if commit:
                employee.save()
            return employee
        else:
            # Create Flow
            name_parts = cleaned_data.get('full_name').split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=cleaned_data.get('username'),
                password=cleaned_data.get('password'),
                email=cleaned_data.get('email'),
                first_name=first_name,
                last_name=last_name
            )
            
            # Update user profile role
            profile = user.userprofile
            profile.role = cleaned_data.get('role')
            profile.phone_number = cleaned_data.get('phone_number')
            if cleaned_data.get('profile_picture'):
                profile.profile_picture = cleaned_data.get('profile_picture')
            profile.save()
            
            employee = super().save(commit=False)
            employee.user = user
            if commit:
                employee.save()
            return employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'manager': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter managers to ADMIN or MANAGER roles
        self.fields['manager'].queryset = User.objects.filter(userprofile__role__in=['ADMIN', 'MANAGER'])


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'manager', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'manager': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'members': forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'size': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(userprofile__role__in=['ADMIN', 'MANAGER'])
        self.fields['members'].queryset = Employee.objects.filter(status='ACTIVE')


class PerformanceReviewForm(forms.ModelForm):
    SCORE_CHOICES = [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)]

    productivity_score = forms.ChoiceField(choices=SCORE_CHOICES, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    attendance_score = forms.ChoiceField(choices=SCORE_CHOICES, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    teamwork_score = forms.ChoiceField(choices=SCORE_CHOICES, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    communication_score = forms.ChoiceField(choices=SCORE_CHOICES, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    technical_skills_score = forms.ChoiceField(choices=SCORE_CHOICES, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))

    class Meta:
        model = PerformanceReview
        fields = ['employee', 'productivity_score', 'attendance_score', 'teamwork_score', 'communication_score', 'technical_skills_score', 'comments']
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Provide detailed performance feedback...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # If reviewer is a Manager (not Admin), restrict employee dropdown to their department
        if user and user.userprofile.role == 'MANAGER':
            try:
                manager_employee = user.employee_profile
                self.fields['employee'].queryset = Employee.objects.filter(department=manager_employee.department, status='ACTIVE')
            except Exception:
                self.fields['employee'].queryset = Employee.objects.filter(status='ACTIVE')
        else:
            self.fields['employee'].queryset = Employee.objects.filter(status='ACTIVE')


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise ValidationError("Start date cannot be after the end date.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}))

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()

        # Also sync employee profile if it exists
        try:
            employee = user.employee_profile
            employee.full_name = f"{user.first_name} {user.last_name}".strip()
            employee.email = user.email
            employee.phone_number = profile.phone_number
            if profile.profile_picture:
                employee.profile_picture = profile.profile_picture
            employee.save()
        except Employee.DoesNotExist:
            pass

        if commit:
            profile.save()
        return profile
