#!/usr/bin/env python3
"""Free candidate discovery using AniList's public GraphQL API.

This module does NOT download chapter scans. It only returns metadata and
promotional artwork URLs for discovery/ranking. Final visual assets must be
explicitly approved/whitelisted in the project manifest.
"""
import json
import urllib.request

API = "https://graphql.anilist.co"

QUERY = r'''
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: MANGA, countryOfOrigin: "KR", sort: TRENDING_DESC, isAdult: false) {
      id
      title { romaji english native }
      description(asHtml: false)
      genres
      siteUrl
      coverImage { extraLarge large color }
      bannerImage
      popularity
      trending
      averageScore
      status
      chapters
    }
  }
}
'''


def fetch_candidates(limit=20):
    body = json.dumps({"query": QUERY, "variables": {"page": 1, "perPage": limit}}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json", "User-Agent": "GPT-Manhwa-Shorts/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out = []
    for m in data["data"]["Page"]["media"]:
        title = m["title"].get("english") or m["title"].get("romaji") or m["title"].get("native")
        out.append({
            "id": m["id"],
            "title": title,
            "title_romaji": m["title"].get("romaji"),
            "description": m.get("description") or "",
            "genres": m.get("genres") or [],
            "site_url": m.get("siteUrl"),
            "cover_url": (m.get("coverImage") or {}).get("extraLarge") or (m.get("coverImage") or {}).get("large"),
            "banner_url": m.get("bannerImage"),
            "popularity": m.get("popularity") or 0,
            "trending": m.get("trending") or 0,
            "average_score": m.get("averageScore") or 0,
            "status": m.get("status"),
            "chapters": m.get("chapters"),
        })
    return out


if __name__ == "__main__":
    print(json.dumps(fetch_candidates(), indent=2, ensure_ascii=False))
