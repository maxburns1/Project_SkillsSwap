from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Skill, Review, BookingRequest
from .forms import RegisterForm, SkillForm, ReviewForm, BookingRequestForm


# ============================================================================
# AUTHENTICATION VIEWS - Login, Logout, Register
# ============================================================================
def register(request):
    """
    Handle user registration.
    GET: Show registration form
    POST: Create new user account
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Save the new user
            user = form.save()
            
            # Log them in automatically
            login(request, user)
            
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('skill_list')
        else:
            # Show validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """
    Handle user login.
    GET: Show login form
    POST: Authenticate and log in user
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('skill_list')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """
    Log out the current user.
    """
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('skill_list')


# ============================================================================
# SKILL VIEWS - List, Detail, Create, Update, Delete
# ============================================================================
def skill_list(request):
    """
    Display all skills with search and filter functionality.
    GET parameters:
    - search: Search by title or description
    - category: Filter by category
    """
    skills = Skill.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        # Search in title and description
        skills = skills.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category = request.GET.get('category')
    if category:
        skills = skills.filter(category=category)
    
    # Get unique categories for the filter dropdown
    categories = Skill.CATEGORY_CHOICES
    
    context = {
        'skills': skills,
        'search_query': search_query,
        'selected_category': category,
        'categories': categories,
    }
    
    return render(request, 'skills/list.html', context)


def skill_detail(request, pk):
    """
    Display a single skill with details, reviews, and booking option.
    Shows:
    - Skill details
    - Average rating from skill reviews
    - All reviews (both skill and learner reviews)
    - Booking request form (if logged in and not owner)
    """
    skill = get_object_or_404(Skill, pk=pk)
    reviews = skill.reviews.all()
    
    # Check if current user can review (must not be owner)
    can_review = request.user.is_authenticated and request.user != skill.owner
    
    # Check if user already left a skill review for this skill
    user_already_reviewed = reviews.filter(
        reviewer=request.user, 
        review_type='skill_review'
    ).exists() if request.user.is_authenticated else False
    
    context = {
        'skill': skill,
        'reviews': reviews,
        'can_review': can_review,
        'user_already_reviewed': user_already_reviewed,
        'average_rating': skill.average_rating(),
    }
    
    return render(request, 'skills/detail.html', context)


@login_required(login_url='login')
def skill_create(request):
    """
    Create a new skill post.
    Only logged-in users can create skills.
    """
    if request.method == 'POST':
        form = SkillForm(request.POST, request.FILES)
        if form.is_valid():
            # Don't save yet - we need to set the owner
            skill = form.save(commit=False)
            skill.owner = request.user
            skill.save()
            
            messages.success(request, 'Your skill has been posted!')
            return redirect('skill_detail', pk=skill.pk)
    else:
        form = SkillForm()
    
    return render(request, 'skills/form.html', {'form': form, 'title': 'Post a New Skill'})


@login_required(login_url='login')
def skill_update(request, pk):
    """
    Update an existing skill post.
    Only the skill owner can update it.
    """
    skill = get_object_or_404(Skill, pk=pk)
    
    # Check if user is the owner
    if request.user != skill.owner:
        messages.error(request, 'You can only edit your own skills.')
        return redirect('skill_detail', pk=pk)
    
    if request.method == 'POST':
        form = SkillForm(request.POST, request.FILES, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your skill has been updated!')
            return redirect('skill_detail', pk=skill.pk)
    else:
        form = SkillForm(instance=skill)
    
    return render(request, 'skills/form.html', {'form': form, 'title': 'Edit Skill'})


@login_required(login_url='login')
def skill_delete(request, pk):
    """
    Delete a skill post.
    Only the owner can delete it.
    """
    skill = get_object_or_404(Skill, pk=pk)
    
    # Check if user is the owner
    if request.user != skill.owner:
        messages.error(request, 'You can only delete your own skills.')
        return redirect('skill_detail', pk=pk)
    
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Your skill has been deleted.')
        return redirect('skill_list')
    
    return render(request, 'skills/confirm_delete.html', {'skill': skill})


# ============================================================================
# REVIEW VIEWS - Create and delete reviews
# ============================================================================
@login_required(login_url='login')
def review_create(request, skill_pk):
    """
    Add a skill review to a skill.
    Only logged-in users who are NOT the skill owner can leave skill reviews.
    A skill review includes feedback about the skill and the teacher.
    """
    skill = get_object_or_404(Skill, pk=skill_pk)
    
    # Can't review your own skill
    if request.user == skill.owner:
        messages.error(request, 'You cannot review your own skill.')
        return redirect('skill_detail', pk=skill_pk)
    
    # Check if user already reviewed this skill
    existing_review = skill.reviews.filter(
        reviewer=request.user, 
        review_type='skill_review'
    ).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this skill.')
        return redirect('skill_detail', pk=skill_pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.skill = skill
            review.reviewer = request.user
            review.reviewed_user = skill.owner  # Review is about the skill owner (teacher)
            review.review_type = 'skill_review'
            review.save()
            
            messages.success(request, 'Your review has been posted!')
            return redirect('skill_detail', pk=skill_pk)
    else:
        form = ReviewForm()
    
    return render(request, 'skills/review_form.html', {'form': form, 'skill': skill})


@login_required(login_url='login')
def learner_review_create(request, booking_pk):
    """
    Leave a learner review after completing a booking.
    Only the skill owner (teacher) can review the learner (requester).
    """
    booking = get_object_or_404(BookingRequest, pk=booking_pk)
    skill = booking.skill
    learner = booking.requester
    
    # Only the skill owner can review the learner
    if request.user != skill.owner:
        messages.error(request, 'Only the skill owner can review learners.')
        return redirect('skill_detail', pk=skill.pk)
    
    # Check if teacher already reviewed this learner for this skill
    existing_review = skill.reviews.filter(
        reviewer=request.user,
        reviewed_user=learner,
        review_type='learner_review'
    ).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this learner for this skill.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.skill = skill
            review.reviewer = request.user  # Teacher reviews
            review.reviewed_user = learner  # About the learner
            review.review_type = 'learner_review'
            review.booking_request = booking
            review.save()
            
            messages.success(request, 'Your learner review has been posted!')
            return redirect('dashboard')
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'skill': skill,
        'learner': learner,
        'booking': booking,
        'page_title': f'Review Learner: {learner.username}'
    }
    
    return render(request, 'skills/review_form.html', context)


@login_required(login_url='login')
def review_delete(request, review_pk):
    """
    Delete a review (only the reviewer can delete it).
    """
    review = get_object_or_404(Review, pk=review_pk)
    skill_pk = review.skill.pk
    
    # Only the reviewer can delete their own review
    if request.user != review.reviewer:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('skill_detail', pk=skill_pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
    
    return redirect('skill_detail', pk=skill_pk)


# ============================================================================
# BOOKING REQUEST VIEWS
# ============================================================================
@login_required(login_url='login')
def booking_request_create(request, skill_pk):
    """
    Create a booking request for a skill.
    Users request to use someone's skill.
    """
    skill = get_object_or_404(Skill, pk=skill_pk)
    
    # Can't book your own skill
    if request.user == skill.owner:
        messages.error(request, 'You cannot book your own skill.')
        return redirect('skill_detail', pk=skill_pk)
    
    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.skill = skill
            booking.requester = request.user
            booking.save()
            
            messages.success(request, 'Your booking request has been sent!')
            return redirect('skill_detail', pk=skill_pk)
    else:
        form = BookingRequestForm()
    
    return render(request, 'skills/booking_form.html', {'form': form, 'skill': skill})


@login_required(login_url='login')
def booking_request_update(request, booking_pk):
    """
    Accept or decline a booking request, or mark as completed.
    Only the skill owner can respond to bookings.
    """
    booking = get_object_or_404(BookingRequest, pk=booking_pk)
    
    # Only the skill owner can respond
    if request.user != booking.skill.owner:
        messages.error(request, 'You can only respond to booking requests for your own skills.')
        return redirect('skill_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            booking.status = 'accepted'
            messages.success(request, 'Booking request accepted!')
        elif action == 'decline':
            booking.status = 'declined'
            messages.info(request, 'Booking request declined.')
        elif action == 'complete':
            booking.status = 'completed'
            messages.success(request, 'Booking marked as completed!')
        
        booking.save()
    
    return redirect('dashboard')


# ============================================================================
# DASHBOARD - User's own skills, reviews, and bookings
# ============================================================================
@login_required(login_url='login')
def dashboard(request):
    """
    Show the logged-in user's dashboard with:
    - Their posted skills
    - Booking requests they've received (as skill owner)
    - Booking requests they've made (as requester)
    - Skill reviews they've received (about their teaching)
    - Learner reviews they've received (about learners they taught)
    """
    user = request.user
    
    # Get user's skills
    my_skills = user.skills.all()
    
    # Get booking requests they've made (as requester)
    my_bookings = user.booking_requests.all()
    
    # Get booking requests for their skills (as skill owner)
    received_bookings = BookingRequest.objects.filter(skill__owner=user)
    
    # Get all reviews about this user (both skill reviews and learner reviews)
    reviews_received = Review.objects.filter(reviewed_user=user)
    
    # Separate reviews by type
    skill_reviews_received = reviews_received.filter(review_type='skill_review')
    learner_reviews_received = reviews_received.filter(review_type='learner_review')
    
    context = {
        'my_skills': my_skills,
        'my_bookings': my_bookings,
        'received_bookings': received_bookings,
        'skill_reviews_received': skill_reviews_received,
        'learner_reviews_received': learner_reviews_received,
        'all_reviews_received': reviews_received,
    }
    
    return render(request, 'skills/dashboard.html', context)
