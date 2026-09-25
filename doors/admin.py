from django.contrib import admin
from .models import Door

@admin.register(Door)
class DoorAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'category', 'created_at')
    
    
    list_filter = ('category', 'brand', 'created_at')
    

    search_fields = ('name', 'brand')
    
    
    ordering = ('-created_at',)
    
    
    list_per_page = 20