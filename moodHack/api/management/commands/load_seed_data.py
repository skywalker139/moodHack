from django.core.management.base import BaseCommand

from api import seed_data
from api.models import Article, MoodResource


class Command(BaseCommand):
    help = "Load mood resources and starter articles into the knowledge base."

    def handle(self, *args, **options):
        created_moods = 0
        updated_moods = 0

        for mood, primary in seed_data.all_moods():
            resource = seed_data.MOOD_RESOURCES.get(mood)
            if resource is None and mood in seed_data.TERTIARY_MOODS:
                # Find the parent secondary mood to inherit from.
                parent = None
                for secondary, tertiaries in seed_data.TERTIARY_MOODS.items():
                    if mood in tertiaries:
                        parent = secondary
                        break
                if parent:
                    resource = seed_data.MOOD_RESOURCES.get(parent)

            tertiary_extra = seed_data.TERTIARY_RESOURCES.get(mood, {})

            defaults = {
                "primary_emotion": primary,
                "description": (resource or {}).get("description", ""),
                "coping_mechanisms": tertiary_extra.get(
                    "coping", (resource or {}).get("coping", [])
                ),
                "music_suggestions": tertiary_extra.get(
                    "music", (resource or {}).get("music", [])
                ),
                "resource_links": seed_data.RESOURCE_LINKS,
                "keywords": (resource or {}).get("keywords", [mood.lower()]),
            }

            _, created = MoodResource.objects.update_or_create(
                mood=mood, defaults=defaults
            )
            if created:
                created_moods += 1
            else:
                updated_moods += 1

        created_articles = 0
        for article in seed_data.ARTICLES:
            _, created = Article.objects.update_or_create(
                url=article["url"],
                defaults={
                    "title": article["title"],
                    "description": article["description"],
                    "topics": article["topics"],
                    "source": article["source"],
                },
            )
            if created:
                created_articles += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Moods: {created_moods} created, {updated_moods} updated. "
                f"Articles: {created_articles} created."
            )
        )
