from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Appointment, ContactSubmission
import datetime

TIME_CHOICES = [
    (datetime.time(hour, 0), f"{hour:02d}:00") for hour in range(9, 18)
]


class CustomUserSignUpForm(UserCreationForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    age = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Age'
    }))
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Phone Number'
    }))

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "age",
            "gender",
            "phone",
            "password1",
            "password2",
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='doctor'),
        empty_label="Select a Doctor",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': datetime.date.today().strftime('%Y-%m-%d')
        }),
        initial=datetime.date.today
    )
    time_slot = forms.TimeField(
        widget=forms.Select(
            choices=TIME_CHOICES,
            attrs={'class': 'form-control'}
        )
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief reason for appointment (optional)'
        })
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time_slot', 'reason']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize doctor display
        self.fields['doctor'].label_from_instance = lambda obj: obj.get_display_name() + (f" - {obj.specialization}" if obj.specialization else "")


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ['first_name', 'last_name', 'mobile', 'email', 'message']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # include fields common to patients; doctors can also use this and update their fields
        fields = ['first_name', 'last_name', 'email', 'phone', 'age', 'gender', 'profile_image',]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'age': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'gender': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'specialization': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'qualification': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded border'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
        }        