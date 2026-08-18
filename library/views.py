from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
import datetime

from .models import User, Book, BorrowRecord
from .forms import (
    StudentSignupForm, StudentLoginForm, AdminLoginForm,
    BookForm, BorrowForm, StudentBorrowForm, EditStudentForm,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_logged_in_user(request):
    uid = request.session.get('user_id')
    if uid:
        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            pass
    return None

def require_student(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_logged_in_user(request)
        if not user or user.role != 'student':
            return redirect('home')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper

def require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_logged_in_user(request)
        if not user or user.role != 'admin':
            return redirect('home')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Home ────────────────────────────────────────────────────────────────────

def home(request):
    user = get_logged_in_user(request)
    if user:
        if user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('student_dashboard')
    return render(request, 'library/home.html')


# ─── Student Auth ────────────────────────────────────────────────────────────

def student_signup(request):
    user = get_logged_in_user(request)
    if user:
        return redirect('home')
    form = StudentSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        new_user = User.objects.create_student(
            matric_number=d['matric_number'],
            name=d['name'],
            department=d['department'],
            level=d['level'],
            password=d['password'],
        )
        messages.success(request, f"Account created! Welcome, {new_user.name}. Please log in.")
        return redirect('student_login')
    return render(request, 'library/student_signup.html', {'form': form})


def student_login(request):
    user = get_logged_in_user(request)
    if user:
        return redirect('home')
    form = StudentLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        matric = form.cleaned_data['matric_number'].upper()
        password = form.cleaned_data['password']
        try:
            user = User.objects.get(matric_number=matric, role='student')
            if user.check_password(password):
                request.session['user_id'] = user.pk
                messages.success(request, f"Welcome back, {user.name}!")
                return redirect('student_dashboard')
            else:
                messages.error(request, "Incorrect password.")
        except User.DoesNotExist:
            messages.error(request, "No student found with that matric number.")
    return render(request, 'library/student_login.html', {'form': form})


def admin_login(request):
    user = get_logged_in_user(request)
    if user:
        return redirect('home')
    form = AdminLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        try:
            user = User.objects.get(email=email, role='admin')
            if user.check_password(password):
                request.session['user_id'] = user.pk
                messages.success(request, f"Welcome, {user.name}!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Incorrect password.")
        except User.DoesNotExist:
            messages.error(request, "No admin account found with that email.")
    return render(request, 'library/admin_login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('home')


# ─── Student Dashboard & Views ───────────────────────────────────────────────

@require_student
def student_dashboard(request):
    student = request.current_user
    active_borrows = BorrowRecord.objects.filter(student=student, status='borrowed').select_related('book')
    history = BorrowRecord.objects.filter(student=student).order_by('-borrow_date').select_related('book')
    overdue = [b for b in active_borrows if b.is_overdue]

    ctx = {
        'user': student,
        'active_borrows': active_borrows,
        'history': history,
        'overdue_count': len(overdue),
        'total_borrowed': history.count(),
    }
    return render(request, 'library/student_dashboard.html', ctx)


@require_student
def browse_books(request):
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
    if category:
        books = books.filter(category=category)
    categories = Book.CATEGORY_CHOICES
    ctx = {'books': books, 'q': q, 'category': category, 'categories': categories, 'user': request.current_user}
    return render(request, 'library/browse_books.html', ctx)


@require_student
def student_borrow(request, book_id):
    student = request.current_user
    book = get_object_or_404(Book, pk=book_id)

    # Check if student already has this book
    already = BorrowRecord.objects.filter(student=student, book=book, status='borrowed').exists()
    if already:
        messages.error(request, "You already have this book borrowed.")
        return redirect('browse_books')

    if book.available_copies <= 0:
        messages.error(request, "No copies available right now.")
        return redirect('browse_books')

    if request.method == 'POST':
        due = timezone.now().date() + datetime.timedelta(days=14)
        BorrowRecord.objects.create(
            student=student,
            book=book,
            borrow_date=timezone.now().date(),
            due_date=due,
        )
        messages.success(request, f'"{book.title}" borrowed! Return by {due.strftime("%d %b %Y")}.')
        return redirect('student_dashboard')

    return render(request, 'library/confirm_borrow.html', {'book': book, 'user': student})


@require_student
def student_return(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, student=request.current_user, status='borrowed')
    if request.method == 'POST':
        record.status = 'returned'
        record.return_date = timezone.now().date()
        record.save()
        messages.success(request, f'"{record.book.title}" returned successfully.')
        return redirect('student_dashboard')
    return render(request, 'library/confirm_return.html', {'record': record, 'user': request.current_user})


# ─── Admin Dashboard & Views ─────────────────────────────────────────────────

@require_admin
def admin_dashboard(request):
    admin = request.current_user
    total_books    = Book.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_borrowed = BorrowRecord.objects.filter(status='borrowed').count()
    total_returned = BorrowRecord.objects.filter(status='returned').count()
    overdue_list   = [r for r in BorrowRecord.objects.filter(status='borrowed').select_related('student', 'book') if r.is_overdue]
    recent_borrows = BorrowRecord.objects.order_by('-borrow_date')[:8].select_related('student', 'book')

    ctx = {
        'user': admin,
        'total_books': total_books,
        'total_students': total_students,
        'total_borrowed': total_borrowed,
        'total_returned': total_returned,
        'overdue_count': len(overdue_list),
        'overdue_list': overdue_list,
        'recent_borrows': recent_borrows,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


# Books CRUD
@require_admin
def manage_books(request):
    q = request.GET.get('q', '')
    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
    ctx = {'books': books, 'q': q, 'user': request.current_user}
    return render(request, 'admin_panel/manage_books.html', ctx)


@require_admin
def add_book(request):
    form = BookForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Book added successfully.")
        return redirect('manage_books')
    return render(request, 'admin_panel/book_form.html', {'form': form, 'action': 'Add', 'user': request.current_user})


@require_admin
def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    form = BookForm(request.POST or None, instance=book)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Book updated.")
        return redirect('manage_books')
    return render(request, 'admin_panel/book_form.html', {'form': form, 'action': 'Edit', 'book': book, 'user': request.current_user})


@require_admin
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, f'"{book.title}" deleted.')
        return redirect('manage_books')
    return render(request, 'admin_panel/confirm_delete.html', {'item': book, 'type': 'book', 'user': request.current_user})


# Students Management
@require_admin
def manage_students(request):
    q = request.GET.get('q', '')
    students = User.objects.filter(role='student')
    if q:
        students = students.filter(Q(name__icontains=q) | Q(matric_number__icontains=q) | Q(department__icontains=q))
    ctx = {'students': students, 'q': q, 'user': request.current_user}
    return render(request, 'admin_panel/manage_students.html', ctx)


@require_admin
def edit_student(request, student_id):
    student = get_object_or_404(User, pk=student_id, role='student')
    form = EditStudentForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Student updated.")
        return redirect('manage_students')
    return render(request, 'admin_panel/edit_student.html', {'form': form, 'student': student, 'user': request.current_user})


@require_admin
def delete_student(request, student_id):
    student = get_object_or_404(User, pk=student_id, role='student')
    if request.method == 'POST':
        student.delete()
        messages.success(request, f"Student {student.name} removed.")
        return redirect('manage_students')
    return render(request, 'admin_panel/confirm_delete.html', {'item': student, 'type': 'student', 'user': request.current_user})


# Borrowings Management
@require_admin
def manage_borrowings(request):
    status_filter = request.GET.get('status', '')
    records = BorrowRecord.objects.all().order_by('-borrow_date').select_related('student', 'book')
    if status_filter:
        records = records.filter(status=status_filter)
    ctx = {'records': records, 'status_filter': status_filter, 'user': request.current_user}
    return render(request, 'admin_panel/manage_borrowings.html', ctx)


@require_admin
def admin_borrow(request):
    form = BorrowForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.borrow_date = timezone.now().date()
        record.due_date = record.borrow_date + datetime.timedelta(days=14)
        record.save()
        messages.success(request, f"Book issued to {record.student.name}.")
        return redirect('manage_borrowings')
    return render(request, 'admin_panel/borrow_form.html', {'form': form, 'user': request.current_user})


@require_admin
def admin_return(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, status='borrowed')
    if request.method == 'POST':
        record.status = 'returned'
        record.return_date = timezone.now().date()
        record.save()
        messages.success(request, f'"{record.book.title}" marked as returned.')
        return redirect('manage_borrowings')
    return render(request, 'admin_panel/confirm_admin_return.html', {'record': record, 'user': request.current_user})
