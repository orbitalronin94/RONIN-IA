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
        nonempty <- nchar(value, type = "chars") > 0L & !is.na(value)
        lengths <- nchar(value[nonempty], type = "chars")
        item$nonempty_values <- sum(nonempty)
        item$median_character_length <- if (length(lengths)) unname(stats::median(lengths)) else 0L
        item$max_character_length <- if (length(lengths)) max(lengths) else 0L
      }
      item
    })
  }
  if (depth < max_depth && is.list(x) && !is.data.frame(x) && length(x) > 0L) {
    idx <- unique(c(seq_len(min(length(x), 4L)), if (length(x) > 4L) length(x)))
    result$elements <- lapply(idx, function(i) {
      child <- describe(x[[i]], depth + 1L, max_depth)
      child$index <- i
      child$name <- if (!is.null(nms) && length(nms) >= i) nms[[i]] else NULL
      child
    })
  }
  result
}

collect_data_frames <- function(x, path = "root", depth = 0L, max_depth = 6L) {
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
  if (!is.list(x) || depth >= max_depth || length(x) == 0L) {
    return(list())
  }
  nms <- names(x)
  result <- list()
  for (i in seq_along(x)) {
    child_name <- if (!is.null(nms) && length(nms) >= i && nzchar(nms[[i]])) nms[[i]] else as.character(i)
    result <- c(result, collect_data_frames(x[[i]], paste0(path, "/", child_name), depth + 1L, max_depth))
    if (length(result) > 5000L) {
      stop("RDS structure contains more than 5,000 nested data-frame nodes")
    }
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
  if (nrow(manifest) != as.integer(provenance$documents_in_manifest)) {
    local_errors <- c(local_errors, "source manifest row count differs from provenance")
  }
  if (nrow(eligible) != as.integer(provenance$documents_converted_and_license_verified)) {
    local_errors <- c(local_errors, "eligible manifest row count differs from provenance")
  }
  if (!"doi" %in% names(eligible) || anyDuplicated(eligible$doi)) {
    local_errors <- c(local_errors, "eligible manifest DOI field missing or duplicated")
  }
  if (!"license" %in% names(eligible) || any(trimws(eligible$license) != "CC-BY 4.0")) {
    local_errors <- c(local_errors, "eligible manifest contains a non-CC-BY-4.0 row")
  }
  for (field in c("pdf_exists", "xml_exists", "in_rds")) {
    if (field %in% names(eligible) && !all(truthy(eligible[[field]]))) {
      local_errors <- c(local_errors, paste("eligible manifest has a false", field, "flag"))
    }
  }

  excluded <- manifest[!manifest$doi %in% eligible$doi, , drop = FALSE]
  excluded_rows <- lapply(seq_len(nrow(excluded)), function(i) {
    row <- excluded[i, , drop = FALSE]
    reasons <- character()
    if ("license" %in% names(row) && trimws(row$license[[1]]) != "CC-BY 4.0") reasons <- c(reasons, "license_not_CC-BY_4.0")
    if ("pdf_exists" %in% names(row) && !truthy(row$pdf_exists[[1]])) reasons <- c(reasons, "pdf_missing")
    if ("xml_exists" %in% names(row) && !truthy(row$xml_exists[[1]])) reasons <- c(reasons, "xml_missing")
    if ("in_rds" %in% names(row) && !truthy(row$in_rds[[1]])) reasons <- c(reasons, "not_in_RDS")
    list(doi = as.character(row$doi[[1]]), reasons = reasons)
  })

  object <- tryCatch(readRDS(f), error = function(e) {
    local_errors <<- c(local_errors, paste("readRDS failed:", conditionMessage(e)))
    NULL
  })
  structure <- if (is.null(object)) NULL else list(
    top_level = describe(object),
    data_frames = collect_data_frames(object)
  )
  report_id <- basename(base)
  reports[[report_id]] <- list(
    dataset_id = provenance$dataset_id,
    payload_file = basename(f),
    payload_bytes = payload_bytes,
    payload_sha256 = payload_sha256,
    manifest_sha256 = manifest_sha256,
    eligible_manifest_sha256 = eligible_sha256,
    manifest_rows = nrow(manifest),
    eligible_rows = nrow(eligible),
    excluded_rows = excluded_rows,
    license_values = if ("license" %in% names(eligible)) unique(eligible$license) else character(),
    doi_unique = "doi" %in% names(eligible) && !anyDuplicated(eligible$doi),
    validation_errors = local_errors,
    structure = structure
  )
  errors <- c(errors, paste(report_id, local_errors, sep = ": "))
}

report <- list(
  schema_version = 2L,
  status = if (length(errors)) "FAIL" else "PASS_STRUCTURE_AND_PROVENANCE_HASHES",
  source_root = root,
  datasets = reports,
  errors = errors
)
writeLines(
  as.character(jsonlite::toJSON(report, auto_unbox = TRUE, pretty = TRUE, null = "null")),
  file.path(out, "structure-report.json")
)
writeLines(capture.output(sessionInfo()), file.path(out, "session-info.txt"))
if (length(errors)) stop(paste(errors, collapse = "\n"))
