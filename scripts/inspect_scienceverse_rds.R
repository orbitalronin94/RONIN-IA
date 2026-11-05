args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else "data/datasets/candidates/scienceverse-fulltext"
out <- if (length(args) >= 2) args[[2]] else "scienceverse-rds-inspection"
dir.create(out, recursive = TRUE, showWarnings = FALSE)

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("jsonlite package is required")
}

sha256_file <- function(path) {
  result <- system2("sha256sum", args = shQuote(path), stdout = TRUE, stderr = TRUE)
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) {
    stop("sha256sum failed for ", path, ": ", paste(result, collapse = " "))
  }
  strsplit(result[[1]], "[[:space:]]+")[[1]][[1]]
}

read_json_file <- function(path) {
  jsonlite::fromJSON(
    paste(readLines(path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"),
    simplifyVector = FALSE
  )
}

expected_count <- function(provenance, fields) {
  for (field in fields) {
    value <- provenance[[field]]
    if (!is.null(value) && length(value) == 1L) {
      number <- suppressWarnings(as.integer(value))
      if (!is.na(number)) return(number)
    }
  }
  NA_integer_
}

describe <- function(x, depth = 0L, max_depth = 5L) {
  cls <- paste(class(x), collapse = "/")
  dims <- dim(x)
  nms <- names(x)
  result <- list(
    class = cls,
    typeof = typeof(x),
    length = length(x),
    dimensions = if (is.null(dims)) NULL else as.integer(dims),
    names_count = if (is.null(nms)) 0L else length(nms),
    names_sample = if (is.null(nms)) character() else head(nms, 20L)
  )
  if (is.data.frame(x)) {
    result$columns <- lapply(names(x), function(column_name) {
      value <- x[[column_name]]
      item <- list(
        name = column_name,
        class = paste(class(value), collapse = "/"),
        typeof = typeof(value),
        length = length(value)
      )
      if (is.character(value)) {
        nonempty <- !is.na(value) & nchar(value, type = "chars") > 0L
        lengths <- nchar(value[nonempty], type = "chars")
        item$nonempty_values <- sum(nonempty)
        item$median_character_length <- if (length(lengths)) unname(stats::median(lengths)) else 0L
        item$max_character_length <- if (length(lengths)) max(lengths) else 0L
      }
      item
    })
  }
  if (depth < max_depth && is.list(x) && !is.data.frame(x) && length(x) > 0L) {
    idx <- unique(c(seq_len(min(length(x), 5L)), if (length(x) > 5L) length(x)))
    result$elements <- lapply(idx, function(i) {
      child <- describe(x[[i]], depth + 1L, max_depth)
      child$index <- i
      child$name <- if (!is.null(nms) && length(nms) >= i) nms[[i]] else NULL
      child
    })
  }
  result
}

collect_data_frames <- function(x, path = "root", depth = 0L, max_depth = 7L, budget = 500L) {
  if (is.data.frame(x)) {
    columns <- names(x)
    return(list(list(
      path = path,
      rows = nrow(x),
      columns = columns,
      doi_columns = columns[grepl("doi|article_id", columns, ignore.case = TRUE)],
      text_candidate_columns = columns[grepl("text|full.?text|body|content|xml|abstract|article", columns, ignore.case = TRUE)]
    )))
  }
  if (!is.list(x) || depth >= max_depth || length(x) == 0L || budget <= 0L) {
    return(list())
  }
  nms <- names(x)
  indices <- unique(c(seq_len(min(length(x), 8L)), if (length(x) > 8L) length(x)))
  result <- list()
  for (i in indices) {
    if (length(result) >= budget) break
    child_name <- if (!is.null(nms) && length(nms) >= i && nzchar(nms[[i]])) nms[[i]] else as.character(i)
    result <- c(result, collect_data_frames(
      x[[i]],
      paste0(path, "/", child_name),
      depth + 1L,
      max_depth,
      budget - length(result)
    ))
  }
  result
}

truthy <- function(x) {
  toupper(trimws(as.character(x))) %in% c("TRUE", "T", "1", "YES")
}

files <- list.files(root, pattern = "\\.rds$", recursive = TRUE, full.names = TRUE)
if (!length(files)) stop("No RDS files found under ", root)

reports <- list()
errors <- character()
for (f in files) {
  message("Auditing ", f)
  base <- dirname(f)
  provenance_path <- file.path(base, "provenance.json")
  manifest_path <- file.path(base, "manifest.csv")
  eligible_path <- file.path(base, "eligible-manifest.csv")
  audit_path <- file.path(base, "crossref-license-audit.json")
  required_paths <- c(provenance_path, manifest_path, eligible_path)
  if (!all(file.exists(required_paths))) {
    errors <- c(errors, paste("Missing provenance/manifest file beside", f))
    next
  }

  provenance <- read_json_file(provenance_path)
  payload_bytes <- unname(file.info(f)$size)
  payload_sha256 <- sha256_file(f)
  manifest_sha256 <- sha256_file(manifest_path)
  eligible_sha256 <- sha256_file(eligible_path)

  manifest <- read.csv(manifest_path, stringsAsFactors = FALSE, check.names = FALSE, na.strings = character())
  eligible <- read.csv(eligible_path, stringsAsFactors = FALSE, check.names = FALSE, na.strings = character())

  local_errors <- character()
  if (payload_bytes != as.numeric(provenance$payload_bytes)) {
    local_errors <- c(local_errors, "payload byte count differs from provenance")
  }
  if (!identical(payload_sha256, provenance$payload_sha256)) {
    local_errors <- c(local_errors, "payload SHA-256 differs from provenance")
  }
  if (!identical(manifest_sha256, provenance$manifest_sha256)) {
    local_errors <- c(local_errors, "source manifest SHA-256 differs from provenance")
  }
  if (!identical(eligible_sha256, provenance$eligible_manifest_sha256)) {
    local_errors <- c(local_errors, "eligible manifest SHA-256 differs from provenance")
  }

  expected_manifest <- expected_count(provenance, c("manifest_rows", "documents_in_manifest"))
  expected_eligible <- expected_count(provenance, c("unique_doi_documents", "documents_converted_and_license_verified"))
  if (!is.na(expected_manifest) && nrow(manifest) != expected_manifest) {
    local_errors <- c(local_errors, "source manifest row count differs from provenance")
  }
  if (!is.na(expected_eligible) && nrow(eligible) != expected_eligible) {
    local_errors <- c(local_errors, "eligible manifest row count differs from provenance")
  }

  if (!"doi" %in% names(manifest) || !"doi" %in% names(eligible)) {
    local_errors <- c(local_errors, "source and eligible manifests must both contain DOI")
  } else {
    manifest_dois <- tolower(trimws(as.character(manifest$doi)))
    eligible_dois <- tolower(trimws(as.character(eligible$doi)))
    if (any(is.na(eligible_dois)) || any(!nzchar(eligible_dois)) || anyDuplicated(eligible_dois)) {
      local_errors <- c(local_errors, "eligible manifest DOI field missing, empty or duplicated")
    }
    if (any(!eligible_dois %in% manifest_dois)) {
      local_errors <- c(local_errors, "eligible DOI is absent from source manifest")
    }

    if (file.exists(audit_path)) {
      audit <- read_json_file(audit_path)
      for (doi in eligible_dois) {
        record <- audit[[doi]]
        if (is.null(record) || !identical(as.character(record$status), "confirmed")) {
          local_errors <- c(local_errors, paste("Crossref audit missing/uncertain for DOI", doi))
          next
        }
        urls <- if (!is.null(record$confirmed_license_urls)) {
          unlist(record$confirmed_license_urls, use.names = FALSE)
        } else {
          unlist(record$license_urls, use.names = FALSE)
        }
        ccby4 <- any(grepl("creativecommons\\.org/licenses/by/4\\.0/?$", urls, ignore.case = TRUE))
        cc0 <- any(grepl("creativecommons\\.org/publicdomain/zero/1\\.0/?$", urls, ignore.case = TRUE))
        if (!ccby4 && !cc0) {
          local_errors <- c(local_errors, paste("Crossref does not confirm an accepted CC BY 4.0/CC0 license for DOI", doi))
        }
      }
    } else {
      normalized_license <- gsub("[^a-z0-9]", "", tolower(trimws(as.character(eligible$license))))
      if (any(normalized_license != "ccby40")) {
        local_errors <- c(local_errors, "eligible manifest contains a license other than exact CC BY 4.0")
      }
    }
  }

  for (field in c("pdf_exists", "xml_exists", "in_rds")) {
    if (field %in% names(eligible) && !all(truthy(eligible[[field]]))) {
      local_errors <- c(local_errors, paste("eligible manifest has a false", field, "flag"))
    }
  }

  excluded <- if ("doi" %in% names(manifest) && "doi" %in% names(eligible)) {
    manifest[!tolower(trimws(as.character(manifest$doi))) %in% tolower(trimws(as.character(eligible$doi))), , drop = FALSE]
  } else {
    manifest[FALSE, , drop = FALSE]
  }
  excluded_rows <- lapply(seq_len(nrow(excluded)), function(i) {
    row <- excluded[i, , drop = FALSE]
    reasons <- character()
    if ("license" %in% names(row) && !tolower(trimws(as.character(row$license[[1]]))) %in% c("cc-by 4.0", "cc-by-4.0", "cc-by")) {
      reasons <- c(reasons, "upstream_license_not_exact_cc_by")
    }
    if ("pdf_exists" %in% names(row) && !truthy(row$pdf_exists[[1]])) reasons <- c(reasons, "pdf_missing")
    if ("xml_exists" %in% names(row) && !truthy(row$xml_exists[[1]])) reasons <- c(reasons, "xml_missing")
    if ("in_rds" %in% names(row) && !truthy(row$in_rds[[1]])) reasons <- c(reasons, "not_in_RDS")
    list(doi = as.character(row$doi[[1]]), reasons = reasons)
  })

  object <- tryCatch(readRDS(f), error = function(e) {
    local_errors <<- c(local_errors, paste("readRDS failed:", conditionMessage(e)))
    NULL
  })
  structure <- if (is.null(object)) NULL else tryCatch(
    list(
      top_level = describe(object),
      data_frames = collect_data_frames(object)
    ),
    error = function(e) {
      local_errors <<- c(local_errors, paste("structure inspection failed:", conditionMessage(e)))
      NULL
    }
  )
  report_id <- paste0(basename(base), "-", substr(payload_sha256, 1L, 8L))
  reports[[report_id]] <- list(
    dataset_id = provenance$dataset_id,
    payload_file = basename(f),
    payload_bytes = payload_bytes,
    payload_sha256 = payload_sha256,
    manifest_sha256 = manifest_sha256,
    eligible_manifest_sha256 = eligible_sha256,
    crossref_audit_sha256 = if (file.exists(audit_path)) sha256_file(audit_path) else NULL,
    manifest_rows = nrow(manifest),
    eligible_rows = nrow(eligible),
    excluded_rows = excluded_rows,
    license_values = if ("license" %in% names(eligible)) unique(eligible$license) else character(),
    doi_unique = "doi" %in% names(eligible) && !anyDuplicated(tolower(trimws(eligible$doi))),
    validation_errors = local_errors,
    structure = structure
  )
  if (length(local_errors)) errors <- c(errors, paste(report_id, local_errors, sep = ": "))
}

report <- list(
  schema_version = 3L,
  status = if (length(errors)) "FAIL" else "PASS_STRUCTURE_AND_PROVENANCE_HASHES",
  source_root = root,
  datasets = reports,
  errors = errors,
  training_eligible = FALSE,
  note = "This inspection verifies RDS readability, source/eligible manifest hashes and declared CC BY 4.0 evidence only. It does not verify publisher ownership, third-party rights, privacy, text quality, deduplication, splits or admission."
)
writeLines(
  as.character(jsonlite::toJSON(report, auto_unbox = TRUE, pretty = TRUE, null = "null")),
  file.path(out, "structure-report.json")
)
writeLines(capture.output(sessionInfo()), file.path(out, "session-info.txt"))
if (length(errors)) stop(paste(errors, collapse = "\n"))
