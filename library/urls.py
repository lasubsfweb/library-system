from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('',                   views.home,            name='home'),
    path('signup/',            views.student_signup,  name='student_signup'),
    path('login/',             views.student_login,   name='student_login'),
    path('admin-login/',       views.admin_login,     name='admin_login'),
    path('logout/',            views.logout_view,     name='logout'),

    # Student
    path('dashboard/',         views.student_dashboard, name='student_dashboard'),
    path('books/',             views.browse_books,      name='browse_books'),
    path('books/borrow/<int:book_id>/',   views.student_borrow, name='student_borrow'),
    path('books/return/<int:record_id>/', views.student_return, name='student_return'),

    # Admin — Books
    path('admin/dashboard/',   views.admin_dashboard,  name='admin_dashboard'),
    path('admin/books/',       views.manage_books,     name='manage_books'),
    path('admin/books/add/',   views.add_book,         name='add_book'),
    path('admin/books/<int:book_id>/edit/',   views.edit_book,   name='edit_book'),
    path('admin/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),

    # Admin — Students
    path('admin/students/',    views.manage_students,  name='manage_students'),
    path('admin/students/<int:student_id>/edit/',   views.edit_student,   name='edit_student'),
    path('admin/students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('admin/students/<int:student_id>/approve/', views.approve_student, name='approve_student'),

    # Admin — Borrowings & Requests
    path('admin/borrowings/',           views.manage_borrowings, name='manage_borrowings'),
    path('admin/requests/',             views.manage_requests,   name='manage_requests'),
    path('admin/requests/<int:record_id>/approve/', views.admin_approve_request, name='admin_approve_request'),
    path('admin/requests/<int:record_id>/reject/', views.admin_reject_request, name='admin_reject_request'),
    path('admin/borrowings/<int:record_id>/return/', views.admin_return, name='admin_return'),
]
