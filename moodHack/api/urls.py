from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/chat/", views.chat, name="chat"),
    path("api/mood/", views.mood, name="mood"),
    path("api/moods/", views.moods, name="moods"),
    path("api/articles/", views.articles, name="articles"),
    path("api/articles/refresh/", views.refresh_articles, name="refresh_articles"),
    path("api/journal/", views.journal, name="journal"),
    path("api/history/", views.history, name="history"),
]
