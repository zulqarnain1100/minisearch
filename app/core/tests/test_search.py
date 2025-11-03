import json
from django.test import TestCase, Client, override_settings
from django.core.management import call_command
from django.urls import reverse

# Use local memory cache in tests (no Redis dependency)
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "minisearch-test-cache",
    }
}

@override_settings(CACHES=TEST_CACHES)
class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Load seed via fixture if available; otherwise insert minimal docs
        try:
            call_command("loaddata", "minisearch.json", verbosity=0)
        except Exception:
            from core.models import Document
            Document.objects.create(
                title="Data science with Python",
                body="pandas scikit-learn python"
            )
            Document.objects.create(
                title="Environment and sustainability",
                body="environment policies impact over time"
            )
            Document.objects.create(
                title="Boolean search examples",
                body="Use AND, OR, NOT in tsquery"
            )

    def setUp(self):
        self.client = Client()

    def _search(self, q):
        return self.client.get(reverse("search"), {"q": q})

    def test_home_loads(self):
        r = self.client.get(reverse("search"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "MiniSearch")

    def test_fts_boolean_and(self):
        r = self._search("data science AND python")
        self.assertEqual(r.status_code, 200)
        # Expect result list exists in template
        self.assertContains(r, "Results")
        self.assertContains(r, "Data science with Python")

    def test_boolean_not(self):
        r = self._search("policy NOT privacy")
        self.assertEqual(r.status_code, 200)
        # Should *not* include "Privacy and data governance" if seeded
        self.assertNotContains(r, "Privacy and data governance")

    def test_trigram_fuzzy(self):
        r = self._search("environmnt")  # typo
        self.assertEqual(r.status_code, 200)
        # Should still match environment docs by trigram
        self.assertContains(r, "Environment")

    def test_cache_hits(self):
        # First request should not be cache (source: fts/trigram)
        r1 = self._search("python")
        self.assertEqual(r1.status_code, 200)
        # Second identical request should be cached
        r2 = self._search("python")
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "source: cache")

    def test_recent_queries_capped(self):
        for i in range(15):
            self._search(f"q{i}")
        # Load home to see chips
        r = self.client.get(reverse("search"))
        self.assertEqual(r.status_code, 200)
        # Only 10 chips should be visible; we test last few exist
        self.assertContains(r, "q14")
        self.assertContains(r, "q13")
        self.assertContains(r, "q5")   # oldest kept (10 total)

