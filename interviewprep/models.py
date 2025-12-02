from django.db import models
from django.contrib.auth.models import User


class Topic(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('done', 'Completed')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.category}) - {self.user.username}'


class Question(models.Model):
    CATEGORY_CHOICES = (
        ("Frontend", "Frontend"),
        ("Backend", "Backend"),
        ("Database", "Database"),
        ("Aptitude", "Aptitude"),
        ("HR", "HR"),
        ("System Design", "System Design"),
    )

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    topic = models.CharField(max_length=255)
    question = models.TextField()
    qtype = models.CharField(max_length=20, default="MCQ")

    option_a = models.CharField(max_length=255, blank=True, null=True)
    option_b = models.CharField(max_length=255, blank=True, null=True)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)

    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return f'[{self.category} - {self.topic}] {self.question[:50]}'


class UserQuestionAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} -> {self.question.id} -> {self.is_correct}'


class TopicContent(models.Model):
    topic = models.CharField(max_length=200, unique=True)
    content = models.TextField()  # HTML formatted explanation
    category = models.CharField(max_length=100)

    def __str__(self):
        return self.topic


class TestScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    score = models.FloatField(default=0)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.topic} - {self.score}%"
    