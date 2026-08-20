from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import datetime


# ─── Custom User Manager ────────────────────────────────────────────────────

class UserManager(BaseUserManager):

    def create_student(self, email, matric_number, name, department, level, password):
        if not matric_number:
            raise ValueError("Matric number is required")
        if not email:
            raise ValueError("Email is required")
        user = self.model(
            email=self.normalize_email(email),
            matric_number=matric_number.upper(),
            name=name,
            department=department,
            level=level,
            role='student',
            is_approved=False,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_admin(self, email, name, password):
        if not email:
            raise ValueError("Email is required")
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            role='admin',
            is_approved=True,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.model(
            email=self.normalize_email(email),
            name=extra_fields.get('name', 'Super Admin'),
            role='admin',
            is_approved=True,
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ─── Custom User Model ───────────────────────────────────────────────────────

class User(AbstractBaseUser):
    ROLE_CHOICES = (('student', 'Student'), ('admin', 'Admin'))
    LEVEL_CHOICES = (
        ('100', '100 Level'), ('200', '200 Level'),
        ('300', '300 Level'), ('400', '400 Level'),
        ('500', '500 Level'), ('PG', 'Postgraduate'),
    )

    email          = models.EmailField(unique=True, null=True, blank=True)
    matric_number  = models.CharField(max_length=20, unique=True, null=True, blank=True)
    name           = models.CharField(max_length=150)
    department     = models.CharField(max_length=100, blank=True)
    level          = models.CharField(max_length=10, choices=LEVEL_CHOICES, blank=True)
    role           = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    is_approved    = models.BooleanField(default=False)
    date_joined    = models.DateTimeField(default=timezone.now)
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    is_superuser   = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


# ─── Book ────────────────────────────────────────────────────────────────────

class Book(models.Model):
    CATEGORY_CHOICES = (
        ('Education', 'Education'), ('Finances', 'Finances'),
        ('Wealth', 'Wealth'), ('Mindset', 'Mindset'),
        ('Science', 'Science'), ('Arts', 'Arts'),
        ('Technology', 'Technology'), ('General', 'General'),
    )

    FORMAT_CHOICES = (
        ('Hard Copy', 'Hard Copy'),
        ('Soft Copy', 'Soft Copy'),
        ('Both', 'Both')
    )

    title       = models.CharField(max_length=200)
    author      = models.CharField(max_length=100)
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    format      = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='Both')
    faculty     = models.CharField(max_length=100, blank=True, null=True)
    department  = models.CharField(max_length=100, blank=True, null=True)
    level       = models.CharField(max_length=10, choices=User.LEVEL_CHOICES, blank=True, null=True)
    quantity    = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    soft_copy   = models.FileField(upload_to='books/soft_copies/', null=True, blank=True)
    external_drive_link = models.URLField(blank=True, null=True, help_text="For files > 10MB. Paste Google Drive link here.")
    added_on    = models.DateTimeField(default=timezone.now)

    @property
    def available_copies(self):
        borrowed = self.borrowrecord_set.filter(status='borrowed').count()
        return self.quantity - borrowed

    @property
    def is_available(self):
        if self.format == 'Soft Copy':
            return False
        return self.available_copies > 0

    def __str__(self):
        return f"{self.title} — {self.author}"


# ─── Borrow Record ────────────────────────────────────────────────────────────

class BorrowRecord(models.Model):
    STATUS_CHOICES = (('borrowed', 'Borrowed'), ('returned', 'Returned'))

    student     = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    book        = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(default=timezone.now)
    due_date    = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed')

    BORROW_DAYS = 14
    FINE_PER_DAY = 50  # Naira

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.borrow_date + datetime.timedelta(days=self.BORROW_DAYS)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == 'borrowed':
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def fine_amount(self):
        return self.days_overdue * self.FINE_PER_DAY

    def __str__(self):
        return f"{self.student.name} — {self.book.title}"
