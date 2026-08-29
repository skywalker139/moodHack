from django.contrib import admin

from .models import Article, ChatMessage, ChatSession, MoodJournal, MoodResource


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "created_at")
    readonly_fields = ("session_id", "created_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "created_at", "content_preview")
    list_filter = ("role", "created_at")
    search_fields = ("content",)

    @admin.display(description="Content")
    def content_preview(self, obj):
        return obj.content[:60]


@admin.register(MoodResource)
class MoodResourceAdmin(admin.ModelAdmin):
    list_display = ("mood", "primary_emotion")
    search_fields = ("mood", "primary_emotion", "description")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "created_at")
    search_fields = ("title", "description", "source")


@admin.register(MoodJournal)
class MoodJournalAdmin(admin.ModelAdmin):
    list_display = ("mood", "created_at", "note_preview")

    @admin.display(description="Note")
    def note_preview(self, obj):
        return obj.note[:60]
