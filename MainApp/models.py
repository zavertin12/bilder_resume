from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100, blank=True)

    about = models.TextField(blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name()

    def full_name(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"


class ResumeComment(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Resume comment"
        verbose_name_plural = "Resume comments"

    def __str__(self):
        return f"Comment by {self.user} on {self.resume}"


class Vacancy(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vacancies',
    )
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.company}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"


class VacancyApplication(models.Model):
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vacancy_applications',
    )
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['vacancy', 'applicant'],
                name='unique_vacancy_application_per_applicant',
            ),
        ]
        verbose_name = "Vacancy application"
        verbose_name_plural = "Vacancy applications"

    def __str__(self):
        return f"{self.applicant} applied for {self.vacancy}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class EditProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
    
    class Meta:
        verbose_name = "Edit Profile"
        verbose_name_plural = "Edit Profiles"