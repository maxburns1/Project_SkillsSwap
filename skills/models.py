from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ============================================================================
# SKILL MODEL - Represents a skill or service someone offers
# ============================================================================
class Skill(models.Model):
    """
    A skill is something a student can teach or offer to others.
    Example: "Piano Lessons", "Web Design Help", "Spanish Tutoring"
    """
    
    CATEGORY_CHOICES = [
        ('academics', 'Academics'),
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('arts', 'Arts & Design'),
        ('tech', 'Technology'),
        ('languages', 'Languages'),
        ('fitness', 'Fitness'),
        ('other', 'Other'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Not Available'),
        ('booked', 'Booked Out'),
    ]
    
    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('inperson', 'In-Person'),
        ('online', 'Online'),
    ]
    
    # Who owns this skill post
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    
    # Basic skill information
    title = models.CharField(max_length=100, help_text="What skill are you offering?")
    description = models.TextField(help_text="Describe what you can teach/offer")
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        help_text="Category of your skill"
    )
    
    # Pricing information
    price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Price per session (leave empty for free)"
    )
    is_free = models.BooleanField(default=False, help_text="Check if this skill is free")
    
    # Availability
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    
    # How to contact you
    contact_preference = models.CharField(
        max_length=20,
        choices=CONTACT_CHOICES,
        default='email',
        help_text="How should people contact you?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional image for the skill
    image = models.ImageField(upload_to='skill_images/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']  # Show newest skills first
    
    def __str__(self):
        return self.title
    
    def average_rating(self):
        """Calculate average rating for this skill"""
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(r.rating for r in reviews) / reviews.count()
        return None


# ============================================================================
# REVIEW MODEL - Users can review and rate skills they've used
# ============================================================================
class Review(models.Model):
    """
    A review is feedback someone leaves about a skill or about a learner.
    - Skill review: learner reviews the skill and teacher
    - Learner review: teacher reviews the learner's experience/attitude
    Includes a rating (1-5 stars) and a comment.
    """
    
    REVIEW_TYPE_CHOICES = [
        ('skill_review', 'Skill Review'),
        ('learner_review', 'Learner Review'),
    ]
    
    # Which skill is this related to
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='reviews')
    
    # Who left the review
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_left')
    
    # The user being reviewed (teacher for skill_review, learner for learner_review)
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Type of review
    review_type = models.CharField(
        max_length=20,
        choices=REVIEW_TYPE_CHOICES,
        default='skill_review',
        help_text="What type of review is this?"
    )
    
    # Related booking request (optional, for learner reviews)
    booking_request = models.ForeignKey(
        'BookingRequest', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviews'
    )
    
    # Rating out of 5
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate from 1 (poor) to 5 (excellent)"
    )
    
    # Written review
    comment = models.TextField(blank=True, help_text="Optional comment")
    
    # When the review was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Each user can only review another user once per review type per skill
        unique_together = ['skill', 'reviewer', 'reviewed_user', 'review_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_review_type_display()} by {self.reviewer.username} about {self.reviewed_user.username}"


# ============================================================================
# BOOKING REQUEST MODEL - Users request to book/use a skill
# ============================================================================
class BookingRequest(models.Model):
    """
    A booking request is when someone wants to use someone else's skill.
    The skill owner can accept or decline the request.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    
    # Which skill is being requested
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='booking_requests')
    
    # Who is requesting
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_requests')
    
    # When they want to book it
    requested_date = models.DateTimeField(help_text="When do you want this skill?")
    
    # Message from requester to skill owner
    message = models.TextField(blank=True, help_text="Tell the skill owner about your request")
    
    # Current status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.requester.username} → {self.skill.title}"
