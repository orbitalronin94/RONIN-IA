#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1L) args[[1L]] else "data/datasets/candidates/scienceverse-fulltext"
out_root <- if (length(args) >= 2L) args[[2L]] else "data/datasets/candidates/scienceverse-text-export-v1"
dir.create(out_root, recursive = TRUE, showWarnings = FALSE)

if (!requireNamespace("jsonlite", quietly = TRUE)) stop("jsonlite is required")
if (!requireNamespace("digest", quietly = TRUE)) stop("digest is required")

read_json <- function(path) {
  jsonlite::fromJSON(paste(readLines(path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"),
                     simplifyVector = FALSE)
}
write_jsonl <- function(items, con) {
  for (item in items) {
    writeLines(as.character(jsonlite::toJSON(item, auto_unbox = TRUE, null = "null",
                                             na = "null", digits = NA)), con, useBytes = TRUE)
  }
}
normalise_doi <- function(x) {
  x <- tolower(trimws(as.character(x)))
  x <- sub("^https?://(dx\\.)?doi\\.org/", "", x, perl = TRUE)
  x <- sub("^doi:\\s*", "", x, perl = TRUE)
  x
}
normalise_body <- function(x) {
  x <- enc2utf8(as.character(x))
  x <- gsub("\r\n?", "\n", x, perl = TRUE)
  x <- trimws(x)
  x
}
EMAIL_RE <- "(?i)\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b"
SSN_RE <- "\\b\\d{3}-\\d{2}-\\d{4}\\b"

roots <- c(root, "data/datasets/candidates/scienceverse-crossref-verified")
files <- unlist(lapply(roots, function(r) {
  if (dir.exists(r)) list.files(r, pattern = "\\.rds$", recursive = TRUE, full.names = TRUE) else character()
}), use.names = FALSE)
if (!length(files)) stop("No RDS packages found")
global_hashes <- new.env(parent = emptyenv())
global_dois <- new.env(parent = emptyenv())
summary <- list()
for (rds in files) {
  dataset_dir <- dirname(rds)
  dataset <- basename(dataset_dir)
  provenance_path <- file.path(dataset_dir, "provenance.json")
  eligible_path <- file.path(dataset_dir, "eligible-manifest.csv")
  if (!file.exists(provenance_path) || !file.exists(eligible_path)) {
    stop("Missing provenance or eligible manifest for ", dataset)
  }
  provenance <- read_json(provenance_path)
  eligible <- read.csv(eligible_path, stringsAsFactors = FALSE, check.names = FALSE,
                       na.strings = character(), encoding = "UTF-8")
  if (!all(c("doi", "title") %in% names(eligible))) stop(dataset, ": eligible manifest needs DOI and title")
  eligible_doi <- normalise_doi(eligible$doi)
  if (anyDuplicated(eligible_doi)) stop(dataset, ": eligible DOI manifest is not unique")

  message("Exporting ", dataset, " (", nrow(eligible), " eligible DOIs)")
  object <- readRDS(rds)
  out_dir <- file.path(out_root, dataset)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  jsonl_path <- file.path(out_dir, "documents.jsonl.gz")
  manifest_path <- file.path(out_dir, "manifest.jsonl")
  excluded_path <- file.path(out_dir, "excluded.jsonl")
  gz <- gzfile(jsonl_path, open = "wt", encoding = "UTF-8", compression = 9)
  manifest_con <- file(manifest_path, open = "wt", encoding = "UTF-8")
  excluded_con <- file(excluded_path, open = "wt", encoding = "UTF-8")

  stats <- list(rds_objects = length(object), eligible_dois = nrow(eligible),
                exported_documents = 0L, excluded_not_eligible = 0L,
                excluded_missing_text = 0L, excluded_short_text = 0L,
                excluded_pii_pattern = 0L, excluded_duplicate_text = 0L, excluded_duplicate_doi = 0L,
                unmatched_eligible_dois = 0L, exported_text_bytes = 0)
  matched <- character()
  seen_local <- new.env(parent = emptyenv())

  for (idx in seq_along(object)) {
    paper <- object[[idx]]
    info <- paper$info
    doi <- if (is.data.frame(info) && "doi" %in% names(info) && nrow(info)) {
      normalise_doi(info$doi[[1L]])
    } else ""
    object_names <- names(object)
    paper_id <- if (!is.null(paper$paper_id) && length(paper$paper_id)) {
      as.character(paper$paper_id[[1L]])
    } else if (!is.null(object_names) && length(object_names) >= idx && nzchar(object_names[[idx]])) {
      object_names[[idx]]
    } else as.character(idx)
    row_index <- match(doi, eligible_doi)
    if (is.na(row_index)) {
      stats$excluded_not_eligible <- stats$excluded_not_eligible + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = if (nzchar(doi)) doi else NULL,
                            reason = "not_in_eligible_manifest")), excluded_con)
      next
    }
    if (exists(doi, envir = seen_local, inherits = FALSE)) {
      stats$excluded_duplicate_doi <- stats$excluded_duplicate_doi + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "duplicate_doi_object_in_rds")), excluded_con)
      next
    }
    assign(doi, TRUE, envir = seen_local)
    matched <- c(matched, doi)
    title <- as.character(eligible$title[[row_index]])
    text_df <- paper$text
    if (!is.data.frame(text_df) || !"text" %in% names(text_df)) {
      stats$excluded_missing_text <- stats$excluded_missing_text + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "missing_text_table")), excluded_con)
      next
    }
    if ("text_id" %in% names(text_df)) {
      ord <- order(text_df$text_id, na.last = TRUE)
      text_df <- text_df[ord, , drop = FALSE]
    }
    sections <- paper$section
    section_headers <- character()
    if (is.data.frame(sections) && all(c("section_id", "header") %in% names(sections))) {
      section_headers <- as.character(sections$header)
      names(section_headers) <- as.character(sections$section_id)
    }
    parts <- character()
    last_section <- NA_character_
    for (j in seq_len(nrow(text_df))) {
      if (is.na(text_df$text[[j]])) next
      paragraph <- normalise_body(text_df$text[[j]])
      if (!nzchar(paragraph)) next
      section_id <- if ("section_id" %in% names(text_df)) as.character(text_df$section_id[[j]]) else NA_character_
      if (!is.na(section_id) && nzchar(section_id) && !identical(section_id, last_section) &&
          section_id %in% names(section_headers)) {
        raw_header <- section_headers[[section_id]]
        if (!is.na(raw_header)) {
          header <- normalise_body(raw_header)
          if (nzchar(header)) parts <- c(parts, paste0("## ", header))
        }
      }
      parts <- c(parts, paragraph)
      last_section <- section_id
    }
    body <- paste(parts, collapse = "\n\n")
    body <- normalise_body(body)
    if (!nzchar(body)) {
      stats$excluded_missing_text <- stats$excluded_missing_text + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "empty_text_body")), excluded_con)
      next
    }
    body_bytes <- nchar(body, type = "bytes")
    if (body_bytes < 2000L) {
      stats$excluded_short_text <- stats$excluded_short_text + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "text_under_2000_bytes", text_bytes = body_bytes)), excluded_con)
      next
    }
    if (grepl(EMAIL_RE, body, perl = TRUE) || grepl(SSN_RE, body, perl = TRUE)) {
      stats$excluded_pii_pattern <- stats$excluded_pii_pattern + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "email_or_ssn_pattern", text_bytes = body_bytes)), excluded_con)
      next
    }
    text_sha <- digest::digest(body, algo = "sha256", serialize = FALSE)
    if (exists(text_sha, envir = global_hashes, inherits = FALSE)) {
      stats$excluded_duplicate_text <- stats$excluded_duplicate_text + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "exact_duplicate_text_sha256",
                            duplicate_of = get(text_sha, envir = global_hashes),
                            text_sha256 = text_sha)), excluded_con)
      next
    }
    if (exists(doi, envir = global_dois, inherits = FALSE)) {
      stats$excluded_duplicate_doi <- stats$excluded_duplicate_doi + 1L
      write_jsonl(list(list(dataset = dataset, paper_id = paper_id, doi = doi,
                            reason = "duplicate_doi_across_scienceverse_packages",
                            duplicate_of = get(doi, envir = global_dois))), excluded_con)
      next
    }
    assign(doi, paste(dataset, doi, sep = ":"), envir = global_dois)
    assign(text_sha, paste(dataset, doi, sep = ":"), envir = global_hashes)
    license_value <- if ("crossref_verified_license" %in% names(eligible)) {
      as.character(eligible$crossref_verified_license[[row_index]])
    } else if ("license" %in% names(eligible)) {
      as.character(eligible$license[[row_index]])
    } else NA_character_
    authors <- character()
    author_df <- paper$author
    if (is.data.frame(author_df) && all(c("given", "family") %in% names(author_df))) {
      given <- as.character(author_df$given)
      family <- as.character(author_df$family)
      given[is.na(given)] <- ""
      family[is.na(family)] <- ""
      authors <- unique(trimws(paste(given, family)))
      authors <- authors[nzchar(authors)]
    }
    license_url <- if (grepl("/publicdomain/zero/1.0", license_value, ignore.case = TRUE)) {
      "https://creativecommons.org/publicdomain/zero/1.0/"
    } else if (grepl("/licenses/by/4.0", license_value, ignore.case = TRUE) ||
               identical(trimws(license_value), "CC-BY 4.0")) {
      "https://creativecommons.org/licenses/by/4.0/"
    } else NA_character_
    record <- list(schema_version = "ronin.document.v1", dataset = dataset,
                   paper_id = paper_id, doi = doi, source_url = paste0("https://doi.org/", doi),
                   title = title, authors = authors,
                   target_library = provenance$target_library,
                   license = license_value, license_url = license_url,
                   source = "ScienceVerse papers / pinned RDS full-text", attribution = list(authors = authors, title = title, doi = doi, license_url = license_url),
                   text = body, text_sha256 = text_sha, text_bytes = body_bytes,
                   status = "candidate_pending_global_validation", training_eligible = FALSE)
    write_jsonl(list(record), gz)
    manifest_record <- record[names(record) != "text"]
    write_jsonl(list(manifest_record), manifest_con)
    stats$exported_documents <- stats$exported_documents + 1L
    stats$exported_text_bytes <- stats$exported_text_bytes + body_bytes
  }

  missing <- setdiff(eligible_doi, unique(matched))
  stats$unmatched_eligible_dois <- length(missing)
  if (length(missing)) {
    for (doi in missing) write_jsonl(list(list(dataset = dataset, doi = doi,
                                                reason = "eligible_doi_missing_from_rds")), excluded_con)
  }
  close(gz); close(manifest_con); close(excluded_con)
  stats$jsonl_gzip_bytes <- unname(file.info(jsonl_path)$size)
  stats$manifest_bytes <- unname(file.info(manifest_path)$size)
  stats$excluded_bytes <- unname(file.info(excluded_path)$size)
  record <- list(dataset_id = paste0("scienceverse-", dataset, "-text-export-v1"),
                 source_rds = rds, source_rds_sha256 = provenance$payload_sha256,
                 eligible_manifest_sha256 = provenance$eligible_manifest_sha256,
                 target_library = provenance$target_library,
                 extraction = "paper$text$text rows ordered by text_id; section headers restored from paper$section; author names retained for CC-BY attribution; emails, affiliations and ORCIDs omitted",
                 privacy_filter = "reject body containing email or SSN patterns; owner-attested human review coverage is recorded in data/datasets/reviews/human-review-attestation-2026-11-05.json",
                 duplicate_policy = "global exact text SHA-256 across every RDS package discovered under scienceverse-fulltext and scienceverse-crossref-verified in one shared hash registry; later exact duplicates excluded",
                 stats = stats, status = "candidate_owner_review_attested_global_near_duplicate_and_partition_gates_pending",
                 human_review_status = "owner_attested_complete",
                 human_review_attestation = "data/datasets/reviews/human-review-attestation-2026-11-05.json",
                 training_eligible = FALSE)
  writeLines(as.character(jsonlite::toJSON(record, auto_unbox = TRUE, pretty = TRUE, null = "null")),
             file.path(out_dir, "provenance.json"), useBytes = TRUE)
  summary[[dataset]] <- record
  message(dataset, ": exported=", stats$exported_documents,
          " excluded_pii=", stats$excluded_pii_pattern,
          " excluded_duplicate=", stats$excluded_duplicate_text,
          " unmatched=", stats$unmatched_eligible_dois,
          " gzip_bytes=", stats$jsonl_gzip_bytes)
}
writeLines(as.character(jsonlite::toJSON(list(status = "candidate_export_complete",
                                              datasets = summary,
                                              training_eligible = FALSE),
                                         auto_unbox = TRUE, pretty = TRUE, null = "null")),
           file.path(out_root, "summary.json"), useBytes = TRUE)
