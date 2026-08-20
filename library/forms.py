from django import forms
from .models import User, Book, BorrowRecord
import datetime


class StudentSignupForm(forms.Form):
    name          = forms.CharField(max_length=150, label="Full Name")
    email         = forms.EmailField(label="Email Address")
    matric_number = forms.CharField(max_length=20, label="Matric Number")
    department    = forms.CharField(max_length=100)
    level         = forms.ChoiceField(choices=User.LEVEL_CHOICES)
    password      = forms.CharField(widget=forms.PasswordInput, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean_matric_number(self):
        matric = self.cleaned_data['matric_number'].upper()
        if User.objects.filter(matric_number=matric).exists():
            raise forms.ValidationError("A student with this matric number already exists.")
        return matric

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class StudentLoginForm(forms.Form):
    matric_number = forms.CharField(max_length=20, label="Matric Number")
    password      = forms.CharField(widget=forms.PasswordInput)


class AdminLoginForm(forms.Form):
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class BookForm(forms.ModelForm):
    class Meta:
        model  = Book
        fields = ['title', 'author', 'category', 'isbn', 'quantity', 'description', 'soft_copy', 'external_drive_link']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class BorrowForm(forms.ModelForm):
    class Meta:
        model  = BorrowRecord
        fields = ['student', 'book']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(role='student', is_active=True)
        self.fields['book'].queryset    = Book.objects.all()

    def clean_book(self):
        book = self.cleaned_data['book']
        if book.available_copies <= 0:
            raise forms.ValidationError("This book has no available copies.")
        return book


class StudentBorrowForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.none(), empty_label="Select a book")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.filter(quantity__gt=0)


class EditStudentForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['name', 'department', 'level']

# Patch: add Bootstrap classes to all form widgets at module level
def _bootstrap_form(form_class):
    for field in form_class.base_fields.values():
        w = field.widget
        existing = w.attrs.get('class', '')
        if isinstance(w, forms.Select):
            w.attrs['class'] = (existing + ' form-select').strip()
        elif isinstance(w, forms.Textarea):
            w.attrs['class'] = (existing + ' form-control').strip()
        else:
            w.attrs['class'] = (existing + ' form-control').strip()

for _f in [StudentSignupForm, StudentLoginForm, AdminLoginForm, BookForm, BorrowForm, StudentBorrowForm, EditStudentForm]:
    _bootstrap_form(_f)
