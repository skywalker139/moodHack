import uuid

from django.db import models


class ChatSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.session_id)


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
        ("tool", "Tool"),
    )

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    content = models.TextField(blank=True)
    tool_calls = models.JSONField(default=list, blank=True)
    articles = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class MoodResource(models.Model):
    mood = models.CharField(max_length=50, unique=True)
    primary_emotion = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    coping_mechanisms = models.JSONField(default=list)
    music_suggestions = models.JSONField(default=list)
    resource_links = models.JSONField(default=list)
    keywords = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mood


class Article(models.Model):
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=1000)
    description = models.TextField(blank=True)
    topics = models.JSONField(default=list)
    source = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MoodJournal(models.Model):
    mood = models.CharField(max_length=50)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mood} @ {self.created_at:%Y-%m-%d %H:%M}"
