from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from skills.models import Skill, BookingRequest, Review
from PIL import Image, ImageDraw, ImageFont
import random
import io
import os


class Command(BaseCommand):
    help = 'Create dummy data for testing the SkillsSwap application'
    
    def generate_skill_image(self, title, color):
        """Generate a simple placeholder image for a skill"""
        # Create a new image with the specified color
        img = Image.new('RGB', (400, 300), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add text to the image
        try:
            # Try to use a nice font, fall back to default if not available
            font = ImageFont.truetype("arial.ttf", 32)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw text in the center
        text_color = (255, 255, 255)
        
        # Split title into multiple lines if too long
        words = title.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            line = ' '.join(current_line)
            # Simple check if line is too long
            if len(line) > 15:
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
        lines.append(' '.join(current_line))
        
        # Draw the lines
        y_offset = 100
        for line in lines[:3]:  # Max 3 lines
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (400 - text_width) // 2
            draw.text((x, y_offset), line, fill=text_color, font=font)
            y_offset += 50
        
        # Save to bytes
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return ContentFile(img_io.getvalue(), name=f'{title.lower().replace(" ", "_")}.png')
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')
        
        # First, delete any reviews where the reviewer is the skill owner (self-reviews)
        all_reviews = Review.objects.all()
        deleted_count = 0
        for review in all_reviews:
            if review.reviewer == review.skill.owner:
                self.stdout.write(self.style.WARNING(f'Deleting self-review by {review.reviewer.username} on {review.skill.title}'))
                review.delete()
                deleted_count += 1
        
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'Cleaned up {deleted_count} self-reviews\n'))
        
        # Clear existing data (optional)
        # User.objects.all().delete()
        # Skill.objects.all().delete()
        # BookingRequest.objects.all().delete()
        # Review.objects.all().delete()
        
        # Create dummy users
        users = []
        usernames = ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 'grace', 'henry']
        
        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.capitalize(),
                    'last_name': 'Test'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            users.append(user)
        
        # Create dummy skills with images for some
        categories = ['academics', 'music', 'sports', 'arts', 'tech', 'languages', 'fitness']
        contact_prefs = ['email', 'phone', 'inperson', 'online']
        
        # Color scheme for different categories
        category_colors = {
            'music': (255, 107, 107),  # Red
            'tech': (0, 150, 136),     # Teal
            'languages': (156, 39, 176),  # Purple
            'sports': (76, 175, 80),   # Green
            'arts': (255, 193, 7),     # Amber
            'academics': (63, 81, 181), # Indigo
            'fitness': (244, 67, 54),  # Deep Orange
        }
        
        skills_created = 0
        skill_templates = [
            ('Piano Lessons', 'Learn to play piano from a professional pianist with 10 years experience', 'music', 50.00),
            ('Web Development', 'Learn HTML, CSS, and JavaScript from scratch', 'tech', 30.00),
            ('Spanish Tutoring', 'Improve your Spanish with conversational practice', 'languages', 25.00),
            ('Tennis Coaching', 'Professional tennis coaching for beginners to intermediate', 'sports', 40.00),
            ('Painting Basics', 'Learn basic oil and acrylic painting techniques', 'arts', 35.00),
            ('Math Tutoring', 'Help with algebra, geometry, and calculus', 'academics', 20.00),
            ('Yoga Classes', 'Relaxing yoga for flexibility and mindfulness', 'fitness', 15.00),
            ('Guitar Lessons', 'Learn to play acoustic guitar from basics to advanced', 'music', 28.00),
            ('French Language', 'Learn French conversation and grammar', 'languages', 30.00),
            ('Photography Tips', 'Learn photography composition and editing', 'arts', 45.00),
            ('Fitness Training', 'Personal fitness training and nutrition advice', 'fitness', 50.00),
            ('Chemistry Help', 'Tutoring in high school and college chemistry', 'academics', 35.00),
        ]
        
        skills = []
        for i, (title, description, category, price) in enumerate(skill_templates):
            skill, created = Skill.objects.get_or_create(
                title=title,
                owner=users[i % len(users)],
                defaults={
                    'description': description,
                    'category': category,
                    'price': price,
                    'is_free': False,
                    'contact_preference': random.choice(contact_prefs),
                    'availability_status': random.choice(['available', 'available', 'available', 'booked']),
                }
            )
            
            # Add images to first 8 skills (more than half)
            if created and i < 8 and not skill.image:
                try:
                    color = category_colors.get(category, (100, 100, 100))
                    skill.image = self.generate_skill_image(title, color)
                    skill.save()
                    self.stdout.write(f'Added image to: {title}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Could not add image to {title}: {str(e)}'))
            
            if created:
                skills_created += 1
                self.stdout.write(f'Created skill: {title}')
            skills.append(skill)
        
        # Create some free skills
        free_skills = [
            ('Python Basics', 'Learn Python programming fundamentals', 'tech', 'online'),
            ('English Conversation', 'Practice English speaking with a native speaker', 'languages', 'inperson'),
            ('Drawing Class', 'Basic drawing techniques and sketching', 'arts', 'inperson'),
        ]
        
        for title, description, category, contact in free_skills:
            skill, created = Skill.objects.get_or_create(
                title=title,
                defaults={
                    'owner': random.choice(users),
                    'description': description,
                    'category': category,
                    'price': None,
                    'is_free': True,
                    'contact_preference': contact,
                    'availability_status': 'available',
                }
            )
            
            # Add images to free skills
            if created and not skill.image:
                try:
                    color = category_colors.get(category, (100, 100, 100))
                    skill.image = self.generate_skill_image(title, color)
                    skill.save()
                    self.stdout.write(f'Added image to: {title}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Could not add image to {title}: {str(e)}'))
            
            if created:
                skills_created += 1
                self.stdout.write(f'Created free skill: {title}')
            skills.append(skill)
        
        self.stdout.write(self.style.SUCCESS(f'Created {skills_created} skills'))
        
        # Create booking requests with varied statuses
        bookings_created = 0
        status_distribution = ['pending', 'pending', 'accepted', 'completed', 'completed', 'declined']
        
        for _ in range(30):  # Create more bookings to have more completed ones for reviews
            skill = random.choice(skills)
            # Make sure requester is not the owner
            requester = random.choice([u for u in users if u != skill.owner])
            
            # Check if this booking already exists
            existing = BookingRequest.objects.filter(
                skill=skill,
                requester=requester
            ).first()
            
            if not existing:
                requested_date = datetime.now() + timedelta(days=random.randint(1, 30))
                booking = BookingRequest.objects.create(
                    skill=skill,
                    requester=requester,
                    requested_date=requested_date,
                    message=f'I am interested in learning {skill.title}. Please let me know availability.',
                    status=random.choice(status_distribution)
                )
                bookings_created += 1
                self.stdout.write(f'Created booking: {requester.username} → {skill.title} ({booking.status})')
        
        self.stdout.write(self.style.SUCCESS(f'Created {bookings_created} bookings'))
        
        # Create reviews
        reviews_created = 0
        
        # SESSION/SKILL REVIEWS - Comments about the teaching quality and session
        session_positive_reviews = [
            (5, 'Excellent teaching! Very clear and easy to follow.'),
            (5, 'Learned so much! Great instructor!'),
            (5, 'Well-organized session. Very professional.'),
            (4, 'Good explanation of concepts. Would recommend.'),
            (4, 'Covered the material thoroughly.'),
            (4, 'Engaging and informative session.'),
        ]
        
        session_neutral_reviews = [
            (3, 'Session was okay but could be better organized.'),
            (3, 'Learned some things but pace was off.'),
            (3, 'Average session, nothing special.'),
        ]
        
        session_negative_reviews = [
            (2, 'Confusing explanations. Hard to follow.'),
            (2, 'Did not learn much from this session.'),
            (1, 'Poorly prepared. Wasted my time.'),
            (1, 'Very confusing and disorganized.'),
        ]
        
        # USER REVIEWS - Comments about the person's personality and professionalism
        user_positive_reviews = [
            (5, 'Friendly and approachable! Great person to work with.'),
            (5, 'Very professional and reliable.'),
            (5, 'Excellent communicator. Easy to talk to.'),
            (4, 'Nice person. Helpful and responsive.'),
            (4, 'Professional and personable.'),
            (4, 'Great attitude and very dependable.'),
        ]
        
        user_neutral_reviews = [
            (3, 'Okay person to work with. Nothing special.'),
            (3, 'Decent enough but somewhat distant.'),
            (3, 'Adequate communication and support.'),
        ]
        
        user_negative_reviews = [
            (2, 'Not very friendly. Hard to communicate with.'),
            (2, 'Seems unreliable. Missed appointments.'),
            (1, 'Rude and dismissive. Poor communication.'),
            (1, 'Very unprofessional and unfriendly.'),
        ]
        
        # Create skill reviews (learner reviews teacher's teaching quality) with varied ratings
        completed_bookings = BookingRequest.objects.filter(status='completed').order_by('?')
        first_half = completed_bookings[:len(completed_bookings)//2]
        
        for booking in first_half:
            # Check if review already exists and requester is not the skill owner
            if booking.requester == booking.skill.owner:
                continue  # Skip if reviewer is the skill owner
            
            existing = Review.objects.filter(
                skill=booking.skill,
                reviewer=booking.requester,
                reviewed_user=booking.skill.owner,
                review_type='skill_review'
            ).first()
            
            if not existing:
                # Choose positive, neutral, or negative review
                rand = random.random()
                if rand < 0.7:  # 70% positive
                    rating, comment = random.choice(session_positive_reviews)
                elif rand < 0.85:  # 15% neutral
                    rating, comment = random.choice(session_neutral_reviews)
                else:  # 15% negative
                    rating, comment = random.choice(session_negative_reviews)
                
                review = Review.objects.create(
                    skill=booking.skill,
                    reviewer=booking.requester,
                    reviewed_user=booking.skill.owner,
                    review_type='skill_review',
                    rating=rating,
                    comment=comment
                )
                reviews_created += 1
                self.stdout.write(f'Created session review: {booking.requester.username} reviewed {booking.skill.owner.username} ({rating}★)')
        
        # Create learner reviews (teacher reviews learner's attitude) with varied ratings
        second_half = completed_bookings[len(completed_bookings)//2:]
        
        for booking in second_half:
            # Check if review already exists and reviewer is not the requester
            if booking.skill.owner == booking.requester:
                continue  # Skip if both are same person
            
            existing = Review.objects.filter(
                skill=booking.skill,
                reviewer=booking.skill.owner,
                reviewed_user=booking.requester,
                review_type='learner_review'
            ).first()
            
            if not existing:
                # Choose positive or negative learner review
                rand = random.random()
                if rand < 0.75:  # 75% positive
                    rating, comment = random.choice(session_positive_reviews)
                else:  # 25% negative
                    rating, comment = random.choice(session_negative_reviews)
                
                review = Review.objects.create(
                    skill=booking.skill,
                    reviewer=booking.skill.owner,
                    reviewed_user=booking.requester,
                    review_type='learner_review',
                    booking_request=booking,
                    rating=rating,
                    comment=comment
                )
                reviews_created += 1
                self.stdout.write(f'Created learner review: {booking.skill.owner.username} reviewed {booking.requester.username} ({rating}★)')
        
        # Create additional learner reviews to diversify reviews about personality
        # These reviews focus on the person's friendliness and professionalism (not just from bookings)
        for _ in range(10):
            reviewer = random.choice(users)
            reviewed_user = random.choice([u for u in users if u != reviewer])
            # Pick any skill, preferring ones owned by the reviewed_user to create personality reviews
            possible_skills = [s for s in skills if s.owner == reviewed_user]
            if not possible_skills:
                skill = random.choice(skills)
            else:
                skill = random.choice(possible_skills)
            
            # Don't allow someone to review their own skills
            if reviewer == skill.owner:
                continue
            
            # Check if this review already exists
            existing = Review.objects.filter(
                skill=skill,
                reviewer=reviewer,
                reviewed_user=reviewed_user,
                review_type='learner_review'
            ).first()
            
            if not existing:
                # Choose positive or negative personality review (about the person)
                rand = random.random()
                if rand < 0.6:  # 60% positive
                    rating, comment = random.choice(user_positive_reviews)
                elif rand < 0.8:  # 20% neutral
                    rating, comment = random.choice(user_neutral_reviews)
                else:  # 20% negative
                    rating, comment = random.choice(user_negative_reviews)
                
                try:
                    review = Review.objects.create(
                        skill=skill,
                        reviewer=reviewer,
                        reviewed_user=reviewed_user,
                        review_type='learner_review',
                        rating=rating,
                        comment=comment
                    )
                    reviews_created += 1
                    self.stdout.write(f'Created personality review: {reviewer.username} reviewed {reviewed_user.username} ({rating}★)')
                except:
                    pass  # Skip if unique constraint fails
        
        self.stdout.write(self.style.SUCCESS(f'Created {reviews_created} reviews'))
        
        self.stdout.write(self.style.SUCCESS('Dummy data creation completed!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Users: {len(users)}')
        self.stdout.write(f'  Skills: {skills_created}')
        self.stdout.write(f'  Bookings: {bookings_created}')
        self.stdout.write(f'  Reviews: {reviews_created}')
        self.stdout.write(f'\nYou can now log in with any of these accounts:')
        for username in usernames:
            self.stdout.write(f'  Username: {username}, Password: testpass123')
