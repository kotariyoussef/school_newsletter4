from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class StudentRequest(models.Model):
    """Model for student status requests"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reason = models.TextField(help_text="Why do you want to be a student on this platform?")
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    
    def _str_(self):
        return f"{self.user.username}'s student request"

class StudentProfile(models.Model):
    """Student profile model that extends the User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = CKEditor5Field('Text', blank=True, null=True, config_name='default')
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.png', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.full_name or self.user.username)
            self.slug = slug
        if self.profile_picture:
            img = Image.open(self.profile_picture)
            img = img.convert('RGB')
            img.thumbnail((300, 300))  # Resize image to a max of 300x300
            temp_image = BytesIO()
            img.save(temp_image, format='JPEG')
            temp_image.seek(0)
            self.profile_picture = InMemoryUploadedFile(temp_image, 'ImageField', 
                                                        self.profile_picture.name, 
                                                        'image/jpeg', temp_image.tell(), None)
        super().save(*args, **kwargs)