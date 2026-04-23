from django.contrib import admin
from .models import Skill, Review, BookingRequest

# ============================================================================
# ADMIN CONFIGURATION - Customize the admin panel
# ============================================================================

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """
    Configure how Skills appear in the admin panel.
    Shows important fields and makes them searchable.
    """
    list_display = ('title', 'owner', 'category', 'price', 'is_free', 'created_at')
    list_filter = ('category', 'is_free', 'availability_status', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Skill Info', {
            'fields': ('owner', 'title', 'description', 'category', 'image')
        }),
        ('Pricing & Contact', {
            'fields': ('price', 'is_free', 'contact_preference')
        }),
        ('Status', {
            'fields': ('availability_status', 'created_at', 'updated_at')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Configure how Reviews appear in the admin panel.
    """
    list_display = ('skill', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('skill__title', 'reviewer__username', 'comment')
    readonly_fields = ('created_at',)


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    """
    Configure how Booking Requests appear in the admin panel.
    """
    list_display = ('skill', 'requester', 'status', 'requested_date', 'created_at')
    list_filter = ('status', 'created_at', 'requested_date')
    search_fields = ('skill__title', 'requester__username', 'message')
    readonly_fields = ('created_at', 'updated_at')

