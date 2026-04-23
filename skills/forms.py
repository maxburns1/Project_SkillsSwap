from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Skill, Review, BookingRequest


# ============================================================================
# USER FORMS - For registration and user profile
# ============================================================================
class RegisterForm(UserCreationForm):
    """
    Form for new users to create an account.
    Extends Django's built-in UserCreationForm.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# ============================================================================
# SKILL FORMS - For creating and editing skills
# ============================================================================
class SkillForm(forms.ModelForm):
    """
    Form for creating or editing a skill post.
    Users fill this out to post a new skill or update existing one.
    """
    
    def clean_price(self):
        """Validate that price is not negative"""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative.")
        return price
    
    class Meta:
        model = Skill
        fields = [
            'title',
            'description', 
            'category',
            'is_free',
            'price',
            'contact_preference',
            'availability_status',
            'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'E.g., Piano Lessons, Web Design Help'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe what you offer, your experience, and any requirements',
                'rows': 5
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_free': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave empty if free',
                'step': '0.01'
            }),
            'contact_preference': forms.Select(attrs={
                'class': 'form-control'
            }),
            'availability_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def clean(self):
        """
        Custom validation: if price is entered, is_free should be False
        """
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        is_free = cleaned_data.get('is_free')
        
        if price and price > 0 and is_free:
            raise forms.ValidationError(
                "If you entered a price, uncheck 'is_free'."
            )
        
        return cleaned_data


# ============================================================================
# REVIEW FORM - For rating and reviewing a skill or learner
# ============================================================================
class ReviewForm(forms.ModelForm):
    """
    Form for leaving a review/rating on a skill or a learner.
    The review_type and reviewed_user are set in the view.
    """
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-check-input'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Share your feedback (optional)',
                'rows': 4
            })
        }


# ============================================================================
# BOOKING REQUEST FORM - For requesting to use a skill
# ============================================================================
class BookingRequestForm(forms.ModelForm):
    """
    Form for requesting to use someone's skill.
    """
    
    class Meta:
        model = BookingRequest
        fields = ['requested_date', 'message']
        widgets = {
            'requested_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': 'When do you want this skill?'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell the skill owner about your request',
                'rows': 4
            })
        }
