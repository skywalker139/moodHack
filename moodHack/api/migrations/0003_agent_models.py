import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_chatmessage_delete_chatbot"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "session_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="MoodResource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("mood", models.CharField(max_length=50, unique=True)),
                ("primary_emotion", models.CharField(blank=True, max_length=50)),
                ("description", models.TextField(blank=True)),
                ("coping_mechanisms", models.JSONField(default=list)),
                ("music_suggestions", models.JSONField(default=list)),
                ("resource_links", models.JSONField(default=list)),
                ("keywords", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("url", models.URLField(max_length=1000)),
                ("description", models.TextField(blank=True)),
                ("topics", models.JSONField(default=list)),
                ("source", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MoodJournal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("mood", models.CharField(max_length=50)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # Replace the old ChatMessage schema. The old model carried no session
        # and no per-message role/tool data, so it is dropped and recreated.
        migrations.DeleteModel(name="ChatMessage"),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("assistant", "Assistant"),
                            ("system", "System"),
                            ("tool", "Tool"),
                        ],
                        default="user",
                        max_length=20,
                    ),
                ),
                ("content", models.TextField(blank=True)),
                ("tool_calls", models.JSONField(blank=True, default=list)),
                ("articles", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="api.chatsession",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
