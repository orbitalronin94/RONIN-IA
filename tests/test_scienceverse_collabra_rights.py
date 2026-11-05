from scripts.preflight_scienceverse_collabra_rights import classify_license_urls


def test_cc_by_4_http_and_trailing_slash_variants_are_accepted() -> None:
    assert classify_license_urls(["http://creativecommons.org/licenses/by/4.0"]) == "cc_by_4_verified_in_crossref"
    assert classify_license_urls(["https://creativecommons.org/licenses/by/4.0/"]) == "cc_by_4_verified_in_crossref"


def test_missing_or_restrictive_licenses_are_not_accepted() -> None:
    assert classify_license_urls([]) == "hold_no_item_level_license_in_crossref"
    assert classify_license_urls(["https://creativecommons.org/licenses/by-nc/4.0/"]) == "reject_or_quarantine_restrictive_license"
    assert classify_license_urls(["https://creativecommons.org/licenses/by/4.0/", "https://creativecommons.org/licenses/by-sa/4.0/"]) == "reject_or_quarantine_restrictive_license"
    assert classify_license_urls([], item_found=False) == "hold_not_found_in_crossref_issn_query"
