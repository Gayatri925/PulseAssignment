import sys
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
# ---------- Data model ----------

@dataclass
class Review:
    title: str
    date: str
    rating: float
    reviewer_name: str
    review_text: str
    source: str
    company: str

def parse_cli_args():
    if len(sys.argv) != 5:
        print(
            'Usage: python review_scraper.py <company_name> <start_date> <end_date> <source>\n'
            'Example: python review_scraper.py "Pulse" 2024-01-01 2024-12-31 g2'
        )
        sys.exit(1)

    company = sys.argv[1]
    try:
        start_date = datetime.fromisoformat(sys.argv[2]).date()
        end_date = datetime.fromisoformat(sys.argv[3]).date()
    except ValueError:
        print("Dates must be in YYYY-MM-DD format.")
        sys.exit(1)

    source = sys.argv[4].lower()
    if source not in {"g2", "capterra", "saas"}:
        print("source must be one of: g2, capterra, saas")
        sys.exit(1)

    return company, start_date, end_date, source


def in_range(date_str: str, start_d, end_d) -> bool:
    """Try some common date formats; if parsing fails, keep the review."""
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(date_str.strip(), fmt).date()
            return start_d <= d <= end_d
        except ValueError:
            continue
    return True  # do not drop if format unknown


def write_json(company: str, source: str, reviews: List[Review]):
    data = [asdict(r) for r in reviews]
    fname = f"{company.lower().replace(' ', '_')}_{source}_reviews.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(reviews)} reviews to {fname}")
# ---------- G2 scraper ----------

def build_g2_url(product_slug: str, page: int) -> str:
    # Example: https://www.g2.com/products/pulse/reviews?page=2
    return f"https://www.g2.com/products/{product_slug}/reviews?page={page}"


def scrape_g2(company: str, start_d, end_d) -> List[Review]:
    # Map company name to G2 slug (update this with the real Pulse slug)
    slug_map = {
        "pulse": "pulse",  # change if actual slug different
    }
    key = company.lower()
    if key not in slug_map:
        raise ValueError(
            f"No G2 slug configured for '{company}'. "
            "Update slug_map in scrape_g2()."
        )

    slug = slug_map[key]
    all_reviews: List[Review] = []
    page = 1

    while True:
        url = build_g2_url(slug, page)
        print(f"[G2] Fetching page {page}: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        # Selector may need adjustment after inspecting actual HTML
        cards = soup.select(".paper.paper--white.paper--box")
        if not cards:
            break

        for card in cards:
            title_el = card.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""

            date_el = card.find("time")
            date_txt = date_el.get_text(strip=True) if date_el else ""

            rating_el = card.find("meta", itemprop="ratingValue")
            rating = 0.0
            if rating_el and rating_el.get("content"):
                try:
                    rating = float(rating_el["content"])
                except ValueError:
                    rating = 0.0

            user_el = card.select_one("a.link--header-color")
            reviewer_name = user_el.get_text(strip=True) if user_el else ""

            body_el = card.find("div", itemprop="reviewBody")
            review_text = body_el.get_text(" ", strip=True) if body_el else ""

            if not in_range(date_txt, start_d, end_d):
                continue

            all_reviews.append(
                Review(
                    title=title,
                    date=date_txt,
                    rating=rating,
                    reviewer_name=reviewer_name,
                    review_text=review_text,
                    source="g2",
                    company=company,
                )
            )

        page += 1
        time.sleep(1)

    return all_reviews
# ---------- Capterra scraper ----------

def build_capterra_url(product_path: str, page: int) -> str:
    # Example base: https://www.capterra.com/p/12345/Pulse/reviews/
    base = f"https://www.capterra.com/p/{product_path}/reviews/"
    return base if page == 1 else f"{base}?page={page}"


def scrape_capterra(company: str, start_d, end_d) -> List[Review]:
    # Map company name to Capterra product path (ID/Name from URL)
    slug_map = {
        "pulse": "12345/Pulse",  # replace 12345/Pulse with real path
    }
    key = company.lower()
    if key not in slug_map:
        raise ValueError(
            f"No Capterra path configured for '{company}'. "
            "Update slug_map in scrape_capterra()."
        )

    path = slug_map[key]
    all_reviews: List[Review] = []
    page = 1

    while True:
        url = build_capterra_url(path, page)
        print(f"[Capterra] Fetching page {page}: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        # Selector may need adjustment after inspecting HTML
        cards = soup.select("section.review-card")
        if not cards:
            break

        for card in cards:
            title_el = card.select_one("h3.review-card__title")
            title = title_el.get_text(strip=True) if title_el else ""

            date_el = card.select_one("span.review-card__date")
            date_txt = date_el.get_text(strip=True) if date_el else ""

            rating_el = card.select_one("span.star-rating__rating")
            try:
                rating = float(rating_el.get_text(strip=True)) if rating_el else 0.0
            except ValueError:
                rating = 0.0

            user_el = card.select_one("span.review-card__reviewer-name")
            reviewer_name = user_el.get_text(strip=True) if user_el else ""

            body_el = card.select_one("p.review-card__review-text")
            review_text = body_el.get_text(" ", strip=True) if body_el else ""

            if not in_range(date_txt, start_d, end_d):
                continue

            all_reviews.append(
                Review(
                    title=title,
                    date=date_txt,
                    rating=rating,
                    reviewer_name=reviewer_name,
                    review_text=review_text,
                    source="capterra",
                    company=company,
                )
            )

        page += 1
        time.sleep(1)

    return all_reviews
# ---------- Bonus: third (example) source ----------

def scrape_saas_example(company: str, start_d, end_d) -> List[Review]:
    """
    Placeholder for a third SaaS review site.
    Replace URL and CSS selectors with the real site you choose.
    """
    base_url = f"https://example-saas-reviews.com/{company.lower()}/reviews?page="
    all_reviews: List[Review] = []
    page = 1

    while True:
        url = base_url + str(page)
        print(f"[SAAS] Fetching page {page}: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".review-card")
        if not cards:
            break

        for card in cards:
            title = card.select_one(".review-title").get_text(strip=True)
            date_txt = card.select_one(".review-date").get_text(strip=True)
            rating = float(card.select_one(".review-rating")["data-score"])
            reviewer_name = card.select_one(".reviewer-name").get_text(strip=True)
            review_text = card.select_one(".review-body").get_text(" ", strip=True)

            if not in_range(date_txt, start_d, end_d):
                continue

            all_reviews.append(
                Review(
                    title=title,
                    date=date_txt,
                    rating=rating,
                    reviewer_name=reviewer_name,
                    review_text=review_text,
                    source="saas",
                    company=company,
                )
            )

        page += 1
        time.sleep(1)

    return all_reviews
# ---------- Main ----------

def main():
    company, start_d, end_d, source = parse_cli_args()

    if source == "g2":
        reviews = scrape_g2(company, start_d, end_d)
    elif source == "capterra":
        reviews = scrape_capterra(company, start_d, end_d)
    else:
        reviews = scrape_saas_example(company, start_d, end_d)

    write_json(company, source, reviews)


if __name__ == "__main__":
    main()
