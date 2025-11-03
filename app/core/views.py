from django.shortcuts import render

# Create your views here.

# app/core/views.py
from typing import List, Dict, Any
from django.shortcuts import render
from django.db.models import F, Value, TextField
from django.db.models.functions import Substr
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse

from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank
)
from django.contrib.postgres.search import TrigramSimilarity

from core.models import Document

CACHE_TTL_SECONDS = 60 * 10              # 10 minutes
RECENT_QUERIES_KEY = "minisearch:recent_queries"  # stores a list[str], max 10
MAX_RECENT = 10
TRIGRAM_THRESHOLD = 0.30                 # demo threshold
RESULT_LIMIT = 10

def _normalize_query(q: str) -> str:
    return " ".join(q.split()).strip().lower()

def _push_recent_query(normalized_q: str) -> None:
    recent: List[str] = cache.get(RECENT_QUERIES_KEY, [])
    # Keep unique; move to front if exists
    if normalized_q in recent:
        recent.remove(normalized_q)
    recent.insert(0, normalized_q)
    cache.set(RECENT_QUERIES_KEY, recent[:MAX_RECENT], CACHE_TTL_SECONDS)

def _cache_key_for_query(normalized_q: str) -> str:
    return f"minisearch:cache:{normalized_q}"

def search_view(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    context: Dict[str, Any] = {
        "q": q,
        "results": [],
        "recent_queries": cache.get(RECENT_QUERIES_KEY, []),
        "source": "idle"  # idle | cache | fts | trigram
    }

    if not q:
        return render(request, "search.html", context)

    nq = _normalize_query(q)
    cache_key = _cache_key_for_query(nq)

    # 1) Try cache
    cached = cache.get(cache_key)
    if cached:
        context.update({"results": cached, "source": "cache"})
        _push_recent_query(nq)
        return render(request, "search.html", context)

    # 2) FTS first (supports AND/OR/NOT via websearch)
    vector = SearchVector("title", weight="A", config="english") + \
             SearchVector("body", weight="B", config="english")
    query = SearchQuery(q, search_type="websearch", config="english")

    fts_qs = (
        Document.objects
        .annotate(rank=SearchRank(vector, query))
        .filter(rank__gt=0.0)
        .order_by("-rank")
        .annotate(
            # Simple deterministic snippet (first 180 chars)
            snippet=Substr(F("body"), 1, 180),
        )
    )[:RESULT_LIMIT]

    results = list(fts_qs.values("id", "title", "snippet"))
    if results:
        context.update({"results": results, "source": "fts"})
        cache.set(cache_key, results, CACHE_TTL_SECONDS)
        _push_recent_query(nq)
        return render(request, "search.html", context)

    # 3) Fuzzy fallback via trigram similarity on title/body
    trigram_qs = (
        Document.objects
        .annotate(
            sim_title=TrigramSimilarity("title", q),
            sim_body=TrigramSimilarity("body", q),
        )
        .annotate(sim=F("sim_title") + F("sim_body"))
        .filter(sim__gt=TRIGRAM_THRESHOLD)
        .order_by("-sim")
        .annotate(snippet=Substr(F("body"), 1, 180))
    )[:RESULT_LIMIT]

    results = list(trigram_qs.values("id", "title", "snippet"))
    if results:
        context.update({"results": results, "source": "trigram"})
        cache.set(cache_key, results, CACHE_TTL_SECONDS)
        _push_recent_query(nq)
        return render(request, "search.html", context)

    # 4) No results
    cache.set(cache_key, [], CACHE_TTL_SECONDS)
    _push_recent_query(nq)
    return render(request, "search.html", context)

