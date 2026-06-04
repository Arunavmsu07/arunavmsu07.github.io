#!/usr/bin/env python3
"""Fetch public works from ORCID and write publications.json.

Runs inside GitHub Actions (server-side), so there is no CORS or browser-extension
blocking. The site loads the resulting publications.json same-origin, which the
browser never blocks.
"""
import json
import urllib.request

ORCID = "0000-0001-6133-5398"
URL = f"https://pub.orcid.org/v3.0/{ORCID}/works"
ALLOWED_TYPES = {"journal-article", "preprint", "book-chapter", "review"}


def fetch():
    req = urllib.request.Request(
        URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "arunavmsu07.github.io publication sync",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse(data):
    out, seen = [], set()
    for group in data.get("group", []):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        s = summaries[0]

        ext = (s.get("external-ids") or {}).get("external-id", []) or []
        doi = ""
        for e in ext:
            if e.get("external-id-type") == "doi":
                doi = (e.get("external-id-value") or "").lower().strip()
                break

        typ = s.get("type") or ""
        if typ not in ALLOWED_TYPES:
            continue

        title = ((s.get("title") or {}).get("title") or {}).get("value", "Untitled")
        journal = (s.get("journal-title") or {}).get("value", "") if s.get("journal-title") else ""
        year = ((s.get("publication-date") or {}).get("year") or {}).get("value", "")

        key = doi or title
        if key in seen:
            continue
        seen.add(key)

        out.append({
            "title": title,
            "journal": journal,
            "year": year,
            "doi": doi,
            "type": typ,
        })

    def year_key(p):
        try:
            return int(p["year"])
        except (TypeError, ValueError):
            return 0

    out.sort(key=year_key, reverse=True)
    return out


def main():
    works = parse(fetch())
    with open("publications.json", "w", encoding="utf-8") as f:
        json.dump(works, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(works)} works to publications.json")


if __name__ == "__main__":
    main()