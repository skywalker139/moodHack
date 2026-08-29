"""Optional article scraper.

Pulls title/description/source metadata from a small allowlist of stable
wellness resources into the Article library. Run manually via:

    python manage.py scrape_articles

or through `POST /api/articles/refresh/`.
"""
from django.core.management.base import BaseCommand

from api.models import Article

# Stable, well-known resource pages that are safe to fetch for metadata.
SOURCES = [
    {
        "url": "https://www.mind.org.uk/information-support/types-of-mental-health-problems/anxiety-and-panic-attacks/",
        "topics": ["anxiety", "mental health"],
        "source": "Mind",
    },
    {
        "url": "https://www.nimh.nih.gov/health/topics/depression",
        "topics": ["depression", "mental health"],
        "source": "NIMH",
    },
]


class Command(BaseCommand):
    help = "Scrape article metadata from configured wellness sources."

    def handle(self, *args, **options):
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            self.stderr.write(
                "Scraper dependencies missing. Run: pip install requests beautifulsoup4"
            )
            return

        headers = {"User-Agent": "moodHack/1.0 (wellness article metadata)"}
        added = 0

        for source in SOURCES:
            url = source["url"]
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"Failed to fetch {url}: {exc}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            description_tag = soup.find("meta", attrs={"name": "description"})
            description = (
                description_tag.get("content", "").strip()
                if description_tag
                else ""
            )

            _, created = Article.objects.update_or_create(
                url=url,
                defaults={
                    "title": title,
                    "description": description,
                    "topics": source["topics"],
                    "source": source["source"],
                },
            )
            if created:
                added += 1

        self.stdout.write(self.style.SUCCESS(f"Scraped {added} new articles."))
