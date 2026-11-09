from scripts.acquire_libretexts_espanol import (
    extract_book_objects,
    is_cc_by_4,
    normalize_markdown,
)


def test_cc_by_4_filter_rejects_noncommercial_and_sharealike():
    assert is_cc_by_4("CC BY 4.0 International")
    assert is_cc_by_4("https://creativecommons.org/licenses/by/4.0/")
    assert not is_cc_by_4("CC BY-NC-SA 4.0")
    assert not is_cc_by_4("CC BY-ND 4.0")


def test_normalize_markdown_removes_images_but_keeps_math_and_text():
    source = "# Física\n\nTexto antes ![figura](https://example.org/image.png) después.\n\n![solo imagen](https://example.org/only.png)\n\n$$E=mc^2$$"
    cleaned = normalize_markdown(source)
    assert "figura" not in cleaned
    assert "solo imagen" not in cleaned
    assert "Texto antes" in cleaned and "después" in cleaned
    assert "$$E=mc^2$$" in cleaned

def test_extract_book_objects_handles_commons_book_id_and_license_code():
    books = extract_book_objects([{
        "bookID": "espanol-51387",
        "title": "Manual de microbiología general",
        "author": "Autores",
        "library": "espanol",
        "license": "ccby",
        "links": {"online": "https://espanol.libretexts.org/Biologia/Manual"},
    }])
    assert len(books) == 1
    assert books[0]["book_id"] == "espanol-51387"
    assert books[0]["license_code"] == "ccby"


def test_extract_book_objects_rejects_noncommercial_and_sharealike():
    books = extract_book_objects([
        {"bookID": "espanol-1", "title": "NC", "library": "espanol", "license": "ccbyncsa", "links": {"online": "https://espanol.libretexts.org/NC"}},
        {"bookID": "espanol-2", "title": "SA", "library": "espanol", "license": "ccbysa", "links": {"online": "https://espanol.libretexts.org/SA"}},
    ])
    assert books == []
