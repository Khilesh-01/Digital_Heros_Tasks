"""Extracts audit signals from raw HTML.

Pure function(s) with no I/O - this makes the parsing logic trivial to
unit test in isolation from the network layer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

_NON_CONTENT_TAGS = ("script", "style", "noscript", "template", "svg", "head")
_WORD_RE = re.compile(r"[A-Za-z0-9'’]+")


@dataclass(frozen=True)
class ParsedPage:
    title: str | None
    meta_description: str | None
    h1_count: int
    total_images: int
    images_without_alt: int
    word_count: int
    canonical_url: str | None
    og_title: str | None
    favicon_present: bool
    language: str | None
    seo_score: int


def parse_html(html: str) -> ParsedPage:
    """Parse `html` and return every signal Page Pulse reports on.

    Never raises on malformed markup - BeautifulSoup's built-in parser is
    lenient by design, and we defensively guard every extraction step.
    """
    soup = BeautifulSoup(html or "", "html.parser")

    title = _extract_title(soup)
    meta_description = _extract_meta_description(soup)
    h1_count = len(soup.find_all("h1"))
    total_images, images_without_alt = _extract_image_stats(soup)
    word_count = _extract_word_count(soup)
    canonical_url = _extract_canonical(soup)
    og_title = _extract_og_title(soup)
    favicon_present = _has_favicon(soup)
    language = _extract_language(soup)

    seo_score = _compute_seo_score(
        title=title,
        meta_description=meta_description,
        h1_count=h1_count,
        images_without_alt=images_without_alt,
        total_images=total_images,
        canonical_url=canonical_url,
        word_count=word_count,
    )

    return ParsedPage(
        title=title,
        meta_description=meta_description,
        h1_count=h1_count,
        total_images=total_images,
        images_without_alt=images_without_alt,
        word_count=word_count,
        canonical_url=canonical_url,
        og_title=og_title,
        favicon_present=favicon_present,
        language=language,
        seo_score=seo_score,
    )


def _extract_title(soup: BeautifulSoup) -> str | None:
    tag = soup.find("title")
    if tag and tag.get_text(strip=True):
        return tag.get_text(strip=True)
    return None


def _extract_meta_description(soup: BeautifulSoup) -> str | None:
    tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if tag and tag.get("content"):
        content = tag["content"].strip()
        return content or None
    return None


def _extract_image_stats(soup: BeautifulSoup) -> tuple[int, int]:
    images = soup.find_all("img")
    total = len(images)
    missing = 0
    for img in images:
        alt = img.get("alt")
        if alt is None or not alt.strip():
            missing += 1
    return total, missing


def _extract_word_count(soup: BeautifulSoup) -> int:
    # Work on a copy so we don't mutate the tree other extractors rely on.
    body = soup.body or soup
    for tag_name in _NON_CONTENT_TAGS:
        for tag in body.find_all(tag_name):
            tag.decompose()

    # Skip content hidden via the standard `hidden` attribute or inline display:none.
    for tag in body.find_all(attrs={"hidden": True}):
        tag.decompose()
    for tag in body.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()

    text = body.get_text(separator=" ", strip=True)
    return len(_WORD_RE.findall(text))


def _extract_canonical(soup: BeautifulSoup) -> str | None:
    tag = soup.find("link", attrs={"rel": re.compile("canonical", re.I)})
    if tag and tag.get("href"):
        return tag["href"].strip()
    return None


def _extract_og_title(soup: BeautifulSoup) -> str | None:
    tag = soup.find("meta", attrs={"property": re.compile("^og:title$", re.I)})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _has_favicon(soup: BeautifulSoup) -> bool:
    return soup.find("link", attrs={"rel": re.compile("icon", re.I)}) is not None


def _extract_language(soup: BeautifulSoup) -> str | None:
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        return html_tag["lang"].strip()
    return None


def _compute_seo_score(
    *,
    title: str | None,
    meta_description: str | None,
    h1_count: int,
    images_without_alt: int,
    total_images: int,
    canonical_url: str | None,
    word_count: int,
) -> int:
    """A deliberately simple, transparent 0-100 heuristic - not a substitute
    for real SEO tooling, just a friendly at-a-glance signal."""
    score = 0
    score += 20 if title else 0
    score += 15 if meta_description else 0
    score += 20 if h1_count == 1 else (10 if h1_count > 1 else 0)
    score += 15 if canonical_url else 0
    score += 15 if word_count >= 300 else int(15 * (word_count / 300)) if word_count else 0
    if total_images == 0:
        score += 15
    else:
        clean_ratio = (total_images - images_without_alt) / total_images
        score += int(15 * clean_ratio)
    return max(0, min(100, score))
