#!/usr/bin/env python3
"""Spider for public Turners used-car listings.

The site is straightforward to scrape because the listing pages are public,
server-rendered HTML pages with visible result cards, pagination, and detail
pages that expose the vehicle fields in text form.

This script keeps the implementation lightweight:
- fetch pages with urllib
- parse HTML with the standard library HTMLParser
- normalize the result into the project listing shape

Example:
    python data/turners_spider.py \
        --start-url https://www.turners.co.nz/Cars/used-cars/used-cars-auckland/ \
        --output data/turners_listings.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Iterator, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_START_URLS = [
    "https://www.turners.co.nz/Cars/used-cars/used-cars-auckland/",
]
DEFAULT_PAGE_SIZE = 110

TITLE_RE = re.compile(r"^(?P<year>19\d{2}|20\d{2})\s+(?P<rest>.+)$")
PRICE_RE = re.compile(r"\$\s*([\d,]+)")
ODOMETER_RE = re.compile(r"Odometer\s+([\d,]+)\s*km", re.I)
LISTING_HINT_RE = re.compile(r"^(?:19\d{2}|20\d{2})\s+[A-Z0-9].+")
BLOCK_TAGS = {
    "article",
    "aside",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
    "ol",
}
SKIP_TAGS = {"script", "style", "noscript"}
SECTION_STOPS = {
    "All Vehicle Features",
    "Contact & Location",
    "Contact Details",
    "Additional Information",
    "Vehicle Star Ratings",
    "Your Notes",
    "Odometer History",
}


@dataclass
class TurnersListing:
    listing_id: str
    title: str
    brand: Optional[str]
    model: Optional[str]
    year: Optional[int]
    price: Optional[int]
    mileage: Optional[int]
    transmission: Optional[str]
    fuel_type: Optional[str]
    seller_type: str
    location: Optional[str]
    description: Optional[str]


@dataclass
class Anchor:
    href: str
    text: str
    attrs: dict[str, str]


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[Anchor] = []
        self._current_href: Optional[str] = None
        self._current_attrs: dict[str, str] = {}
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "a":
            return
        self._current_attrs = {key: value or "" for key, value in attrs}
        self._current_text = []
        self._current_href = self._current_attrs.get("href")

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return
        text = normalize_whitespace("".join(self._current_text))
        self.anchors.append(Anchor(href=self._current_href, text=text, attrs=self._current_attrs))
        self._current_href = None
        self._current_attrs = {}
        self._current_text = []


class TextLineCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self._buffer: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag.lower() in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag.lower() in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self._buffer.append(data)

    def close(self) -> None:
        self._flush()
        super().close()

    def _flush(self) -> None:
        text = normalize_whitespace("".join(self._buffer))
        if text:
            self.lines.append(text)
        self._buffer = []


def extract_text_lines(html: str) -> list[str]:
    parser = TextLineCollector()
    parser.feed(html)
    parser.close()
    return [line for line in parser.lines if line]


def fetch_html(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def absolute_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def set_query_params(url: str, **params: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key, value in params.items():
        query[key] = [value]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def same_site(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith("turners.co.nz")


def is_probable_listing_link(text: str, href: str) -> bool:
    if not text or not href:
        return False
    if not same_site(href):
        return False
    if "/Cars/" not in href:
        return False
    if href.rstrip("/").endswith("/Cars") or href.rstrip("/").endswith("/used-cars"):
        return False
    text = normalize_whitespace(text)
    return bool(LISTING_HINT_RE.match(text))


def collect_anchors(html: str) -> list[Anchor]:
    parser = AnchorCollector()
    parser.feed(html)
    return parser.anchors


def extract_listing_links(html: str, page_url: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for anchor in collect_anchors(html):
        text = normalize_whitespace(anchor.text)
        href = absolute_url(page_url, anchor.href)
        if is_probable_listing_link(text, href) and href not in seen:
            seen.add(href)
            links.append(href)

    return links


def extract_pagination_links(html: str, page_url: str) -> list[str]:
    current = urlparse(page_url)
    current_query = parse_qs(current.query)
    candidates: list[str] = []
    seen: set[str] = set()

    for anchor in collect_anchors(html):
        href = absolute_url(page_url, anchor.href)
        parsed = urlparse(href)
        if parsed.netloc != current.netloc:
            continue
        if parsed.path != current.path:
            continue

        query = parse_qs(parsed.query)
        if query == current_query:
            continue

        label = normalize_whitespace(anchor.text)
        aria_label = normalize_whitespace(anchor.attrs.get("aria-label", ""))
        title = normalize_whitespace(anchor.attrs.get("title", ""))
        pagination_hint = bool(
            label.isdigit()
            or label.lower() in {"next", "prev", "previous", "last", "first"}
            or aria_label.lower() in {"next", "prev", "previous", "last", "first"}
            or title.lower() in {"next", "prev", "previous", "last", "first"}
            or any(key.lower() in {"page", "pagesize", "pageindex", "p"} for key in query)
        )
        if pagination_hint and href not in seen:
            seen.add(href)
            candidates.append(href)
            continue

        if (label or aria_label or title) and href not in seen:
            if query:
                seen.add(href)
                candidates.append(href)

    return candidates


def parse_detail_page(html: str, market_location: str, listing_ref: Optional[str] = None) -> TurnersListing:
    lines = extract_text_lines(html)

    vehicle = get_section_value(lines, "Vehicle")
    year = parse_int(get_section_value(lines, "Year"))
    brand, model = split_vehicle_name(vehicle)
    title = build_title(year, vehicle)
    price = parse_money(get_price(lines))
    mileage = parse_int(get_section_value(lines, "Odometer"))
    transmission = normalize_value(get_section_value(lines, "Transmission"))
    fuel_type = normalize_value(get_section_value(lines, "Fuel"))
    description = extract_commentary(lines)

    ref = normalize_value(listing_ref or get_section_value(lines, "Turners Ref"))
    listing_id = make_listing_id(market_location, brand, model, ref)

    return TurnersListing(
        listing_id=listing_id,
        title=title,
        brand=brand,
        model=model,
        year=year,
        price=price,
        mileage=mileage,
        transmission=transmission.lower() if transmission else None,
        fuel_type=fuel_type.lower() if fuel_type else None,
        seller_type="dealer",
        location=market_location,
        description=description,
    )


def extract_actual_location(html: str) -> Optional[str]:
    lines = extract_text_lines(html)
    return (
        get_section_value(lines, "Vehicle Location")
        or get_section_value(lines, "Location")
        or get_section_value(lines, "Branch")
    )


def split_vehicle_name(vehicle: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not vehicle:
        return None, None
    parts = vehicle.split()
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]


def build_title(year: Optional[int], vehicle: Optional[str]) -> str:
    if year and vehicle:
        return f"{year} {vehicle}"
    if vehicle:
        return vehicle
    return "Unknown listing"


def get_section_value(lines: list[str], label: str) -> Optional[str]:
    for index, line in enumerate(lines):
        if normalize_value(line).lower() == label.lower():
            for candidate in lines[index + 1 :]:
                candidate = normalize_value(candidate)
                if candidate:
                    return candidate
    return None


def get_price(lines: list[str]) -> Optional[str]:
    for index, line in enumerate(lines):
        if normalize_value(line).lower() in {"buynow", "buy now"}:
            for candidate in lines[index + 1 :]:
                if normalize_value(candidate) in SECTION_STOPS:
                    break
                match = PRICE_RE.search(candidate)
                if match:
                    return match.group(1)
    return None


def parse_money(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    return int(value.replace(",", ""))


def parse_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = re.search(r"([\d,]+)", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def normalize_value(value: Optional[str]) -> str:
    return normalize_whitespace(value or "")


def extract_commentary(lines: list[str]) -> Optional[str]:
    for index, line in enumerate(lines):
        if normalize_value(line).lower() == "comments":
            content: list[str] = []
            for candidate in lines[index + 1 :]:
                cleaned = normalize_value(candidate)
                if not cleaned:
                    continue
                if cleaned in SECTION_STOPS or cleaned.lower() == "read more":
                    break
                if cleaned.lower().startswith("vehicle location"):
                    break
                content.append(cleaned)
            if content:
                return " ".join(content[:4])
    return None


def make_listing_id(location: str, brand: Optional[str], model: Optional[str], ref: Optional[str]) -> str:
    parts = [location_code(location), slugify(brand), slugify(model), slugify(ref)]
    parts = [part for part in parts if part]
    return "-".join(parts) or "turners-listing"


def slugify(value: Optional[str], max_len: Optional[int] = None) -> str:
    if not value:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if max_len:
        slug = slug[:max_len]
    return slug


def location_code(location: str) -> str:
    mapping = {
        "auckland": "akl",
        "wellington": "wlg",
        "christchurch": "chc",
        "hamilton": "hlz",
        "tauranga": "trg",
        "rotorua": "rot",
        "napier": "npe",
        "new plymouth": "npl",
        "palmerston north": "pnh",
        "dunedin": "dud",
        "whangarei": "wre",
    }
    key = normalize_value(location).lower()
    return mapping.get(key, slugify(location, max_len=3) or "turners")


def is_market_location(actual_location: Optional[str], market_location: str) -> bool:
    if not market_location:
        return True
    if not actual_location:
        return True

    normalized_location = normalize_value(actual_location).lower()
    normalized_market = normalize_value(market_location).lower()
    if normalized_market == normalized_location:
        return True

    if normalized_market == "auckland":
        return any(
            token in normalized_location
            for token in (
                "auckland",
                "botany",
                "manukau",
                "new lynn",
                "north shore",
                "panmure",
                "penrose",
                "westgate",
                "otahuhu",
                "wiri",
                "mt richmond",
                "mount richmond",
                "gavin street",
            )
        )

    return normalized_market in normalized_location


def build_model_search_url(brand: str, model: str, page_size: int) -> str:
    brand_slug = slugify(brand)
    model_slug = slugify(model)
    url = f"https://www.turners.co.nz/Cars/Used-Cars-for-Sale/{brand_slug}/{model_slug}/"
    return set_query_params(url, pagesize=str(page_size))


def expand_start_urls(
    start_urls: Iterable[str],
    brands: set[str],
    models: set[str],
    page_size: int,
) -> list[str]:
    seeds: list[str] = []
    seen: set[str] = set()

    for url in start_urls:
        normalized = set_query_params(url, pagesize=str(page_size))
        if normalized not in seen:
            seen.add(normalized)
            seeds.append(normalized)

    for brand in sorted(brands):
        for model in sorted(models):
            model_url = build_model_search_url(brand, model, page_size=page_size)
            if model_url not in seen:
                seen.add(model_url)
                seeds.append(model_url)

    return seeds


def crawl(
    start_urls: Iterable[str],
    max_pages: int,
    delay: float,
    timeout: int,
    brands: set[str],
    models: set[str],
    market_location: str,
) -> Iterator[TurnersListing]:
    visited_pages: set[str] = set()
    visited_details: set[str] = set()
    queue: list[str] = list(start_urls)

    while queue and len(visited_pages) < max_pages:
        page_url = queue.pop(0)
        if page_url in visited_pages:
            continue
        visited_pages.add(page_url)

        html = fetch_html(page_url, timeout=timeout)
        for detail_url in extract_listing_links(html, page_url):
            if detail_url in visited_details:
                continue
            visited_details.add(detail_url)

            detail_html = fetch_html(detail_url, timeout=timeout)
            actual_location = extract_actual_location(detail_html)
            if not is_market_location(actual_location, market_location):
                if delay:
                    time.sleep(delay)
                continue
            listing = parse_detail_page(detail_html, market_location=market_location)
            if (
                listing.brand
                and listing.model
                and listing.brand.lower() in brands
                and listing.model.lower() in models
            ):
                yield listing
            if delay:
                time.sleep(delay)

        for next_page in extract_pagination_links(html, page_url):
            if next_page not in visited_pages and next_page not in queue:
                queue.append(next_page)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape public Turners used-car listings.")
    parser.add_argument(
        "--start-url",
        action="append",
        dest="start_urls",
        help="Listing page to crawl. Can be passed multiple times.",
    )
    parser.add_argument(
        "--output",
        default="data/turners_listings.jsonl",
        help="Output path for JSONL results.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum number of listing pages to visit across all start URLs.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between detail page requests.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--brands",
        default="Toyota,Honda,Mazda",
        help="Comma-separated brand filter for the output dataset.",
    )
    parser.add_argument(
        "--location",
        default="Auckland",
        help="Market location to stamp onto the output listings.",
    )
    parser.add_argument(
        "--models",
        default="Aqua,Prius,RAV4,Civic,Fit,HR-V,Mazda2,Mazda3,CX-5",
        help="Comma-separated model filter for the output dataset.",
    )
    parser.add_argument(
        "--per-model-limit",
        type=int,
        default=10,
        help="Maximum number of listings to keep per model after sorting by price.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    start_urls = args.start_urls or DEFAULT_START_URLS
    brands = {brand.strip().lower() for brand in args.brands.split(",") if brand.strip()}
    models = {model.strip().lower() for model in args.models.split(",") if model.strip()}
    seed_urls = expand_start_urls(start_urls, brands, models, page_size=DEFAULT_PAGE_SIZE)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    buckets: dict[tuple[str, str], list[TurnersListing]] = {}
    listings = 0
    emitted = 0
    with output_path.open("w", encoding="utf-8") as fh:
        for listing in crawl(
            seed_urls,
            max_pages=args.max_pages,
            delay=args.delay,
            timeout=args.timeout,
            brands=brands,
            models=models,
            market_location=args.location,
        ):
            listings += 1
            if not listing.brand or not listing.model:
                continue
            key = (listing.brand.lower(), listing.model.lower())
            buckets.setdefault(key, []).append(listing)

        for key in sorted(buckets):
            items = sorted(
                buckets[key],
                key=lambda item: (
                    item.price is None,
                    item.price if item.price is not None else 0,
                    item.year is None,
                    -(item.year or 0),
                    item.mileage is None,
                    item.mileage if item.mileage is not None else 0,
                    item.title,
                ),
            )[: args.per_model_limit]
            for item in items:
                fh.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
                emitted += 1

    print(f"Found {listings} listings and wrote {emitted} sorted listings to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
