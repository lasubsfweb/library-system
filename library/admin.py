from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Book, BorrowRecord

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ('name', 'role', 'matric_number', 'email', 'date_joined')
    list_filter    = ('role',)
    search_fields  = ('name', 'matric_number', 'email')
    ordering       = ('-date_joined',)
    fieldsets      = None
    add_fieldsets  = None
    filter_horizontal = ()

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'category', 'isbn', 'quantity')
    search_fields = ('title', 'author', 'isbn')
    list_filter   = ('category',)

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display  = ('student', 'book', 'borrow_date', 'due_date', 'return_date', 'status')
    list_filter   = ('status',)
    search_fields = ('student__name', 'book__title')
