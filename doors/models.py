from django.db import models
from django.contrib.auth.models import User

class Door(models.Model):
    CATEGORY_CHOICES = [
        ('Standart', 'Standart'),
        ('Premium', 'Premium'),
    ]

    name = models.CharField(max_length=255, verbose_name="Eshik nomi")
    brand = models.CharField(max_length=255, verbose_name="Brend")
    price = models.PositiveIntegerField(verbose_name="Narxi (UZS)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Standart')
    image = models.ImageField(upload_to='doors/', blank=True, null=True, verbose_name="Rasm")
    coating = models.CharField(max_length=255, blank=True, verbose_name="Qoplama")
    structure = models.CharField(max_length=255, blank=True, verbose_name="Tuzilishi")
    description = models.TextField(blank=True, default="", verbose_name="Tavsif")
    
    # Like-lar uchun
    likes = models.ManyToManyField(User, blank=True, related_name='liked_doors')

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.name

class Comment(models.Model):
    door = models.ForeignKey(Door, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.door.name}'

