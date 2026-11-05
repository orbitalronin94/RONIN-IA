args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else "data/datasets/candidates/scienceverse-fulltext"
out <- if (length(args) >= 2) args[[2]] else "scienceverse-rds-inspection"
dir.create(out, recursive = TRUE, showWarnings = FALSE)

describe <- function(x, depth = 0L, max_depth = 4L) {
  cls <- paste(class(x), collapse = "/")
  dims <- dim(x)
  nms <- names(x)
  result <- list(class = cls, typeof = typeof(x), length = length(x),
                 dimensions = if (is.null(dims)) NULL else as.integer(dims),
                 names_count = if (is.null(nms)) 0L else length(nms),
                 names_sample = if (is.null(nms)) character() else head(nms, 12L))
  if (depth < max_depth && is.list(x) && length(x) > 0L) {
    idx <- unique(c(seq_len(min(length(x), 3L)), if (length(x) > 3L) length(x)))
    result$elements <- lapply(idx, function(i) {
      child <- describe(x[[i]], depth + 1L, max_depth)
      child$index <- i
      child$name <- if (!is.null(nms) && length(nms) >= i) nms[[i]] else NULL
      child
    })
  }
  if (is.atomic(x) && length(x) > 0L && length(x) <= 20L) {
    result$sample <- as.character(x)
  } else if (is.atomic(x) && length(x) > 20L) {
    result$sample <- as.character(head(x, 5L))
  }
  result
}

json_escape <- function(x) {
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    jsonlite::toJSON(x, auto_unbox = TRUE, pretty = TRUE, null = "null", dataframe = "rows")
  } else {
    stop("jsonlite package is required")
  }
}

files <- list.files(root, pattern = "\\.rds$", recursive = TRUE, full.names = TRUE)
if (!length(files)) stop("No RDS files found under ", root)
reports <- list()
for (f in files) {
  message("Reading ", f)
  obj <- readRDS(f)
  id <- tools::file_path_sans_ext(basename(f))
  reports[[id]] <- list(file = f, bytes = unname(file.info(f)$size), structure = describe(obj))
}
writeLines(as.character(json_escape(reports)), file.path(out, "structure-report.json"))
writeLines(capture.output(sessionInfo()), file.path(out, "session-info.txt"))
