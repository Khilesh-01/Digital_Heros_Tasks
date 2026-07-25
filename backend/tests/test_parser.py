"""Unit tests for app.services.parser.

Covers: happy path, missing title, missing meta description, malformed
HTML, word count accuracy, and images-without-alt counting.
"""
from app.services.parser import parse_html

HAPPY_PATH_HTML = """
<html lang="en">
<head>
    <title>Page Pulse Demo</title>
    <meta name="description" content="A demo page for testing the parser.">
    <link rel="canonical" href="https://example.com/">
    <meta property="og:title" content="Page Pulse Demo OG">
    <link rel="icon" href="/favicon.ico">
</head>
<body>
    <h1>Welcome to Page Pulse</h1>
    <p>This is a simple paragraph with exactly eight words here.</p>
    <img src="a.png" alt="A descriptive image">
    <img src="b.png" alt="">
    <img src="c.png">
    <script>console.log("ignore me completely");</script>
    <style>.hidden { color: red; }</style>
</body>
</html>
"""


def test_parses_happy_path_correctly():
    result = parse_html(HAPPY_PATH_HTML)

    assert result.title == "Page Pulse Demo"
    assert result.meta_description == "A demo page for testing the parser."
    assert result.h1_count == 1
    assert result.total_images == 3
    assert result.images_without_alt == 2  # empty alt and missing alt both count
    assert result.canonical_url == "https://example.com/"
    assert result.og_title == "Page Pulse Demo OG"
    assert result.favicon_present is True
    assert result.language == "en"


def test_word_count_excludes_scripts_and_styles():
    result = parse_html(HAPPY_PATH_HTML)
    # "This is a simple paragraph with exactly eight words here." = 10 words,
    # plus "Welcome to Page Pulse" = 4 words -> 14 total. Script/style text ignored.
    assert result.word_count == 14


def test_missing_title_returns_none():
    html = "<html><head></head><body><p>No title here at all.</p></body></html>"
    result = parse_html(html)
    assert result.title is None


def test_missing_meta_description_returns_none():
    html = "<html><head><title>Only a title</title></head><body></body></html>"
    result = parse_html(html)
    assert result.meta_description is None


def test_malformed_html_does_not_raise():
    malformed = "<html><head><title>Broken</title><body><p>Unclosed tags everywhere<div>"
    # Should not raise - BeautifulSoup's html.parser is lenient by design,
    # even with unclosed <p>/<div> tags in the body.
    result = parse_html(malformed)
    assert result.title == "Broken"
    assert result.h1_count == 0
    assert result.word_count > 0


def test_empty_html_returns_safe_defaults():
    result = parse_html("")
    assert result.title is None
    assert result.meta_description is None
    assert result.h1_count == 0
    assert result.total_images == 0
    assert result.images_without_alt == 0
    assert result.word_count == 0


def test_images_without_alt_counts_missing_and_blank_alt():
    html = """
    <html><body>
        <img src="1.png" alt="present">
        <img src="2.png" alt="   ">
        <img src="3.png">
    </body></html>
    """
    result = parse_html(html)
    assert result.total_images == 3
    assert result.images_without_alt == 2


def test_multiple_h1_tags_are_all_counted():
    html = "<html><body><h1>One</h1><h1>Two</h1><h1>Three</h1></body></html>"
    result = parse_html(html)
    assert result.h1_count == 3
