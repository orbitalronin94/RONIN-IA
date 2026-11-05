args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: extract_scienceverse_collabra.R <rds> <eligible-dois.txt> <output.csv>")
rds_path <- args[[1]]
allow_path <- args[[2]]
out_path <- args[[3]]

papers <- readRDS(rds_path)
if (!is.list(papers) || length(papers) < 1) stop("RDS is not a non-empty paper list")
allowed <- tolower(trimws(readLines(allow_path, warn = FALSE)))
allowed <- allowed[nzchar(allowed)]
if (length(allowed) != 748L) stop(sprintf("expected exactly 748 CC BY 4.0 DOIs, got %d", length(allowed)))
if (anyDuplicated(allowed)) stop("duplicate DOI in rights allowlist")

records <- vector("list", length(papers))
n <- 0L
excluded <- list()
for (i in seq_along(papers)) {
  p <- papers[[i]]
  info <- p$info
  doi <- tolower(trimws(as.character(info$doi[[1]])))
  if (is.na(doi) || !doi %in% allowed) {
    excluded[[length(excluded) + 1L]] <- doi
    next
  }
  if (is.null(p$text) || !is.data.frame(p$text) || !"text" %in% names(p$text)) {
    stop(sprintf("paper %s has no text table", doi))
  }
  section_types <- setNames(as.character(p$section$section_type), as.character(p$section$section_id))
  text_rows <- p$text
  sid <- as.character(text_rows$section_id)
  stype <- unname(section_types[sid])
  keep <- !is.na(text_rows$section_id) & !is.na(stype) &
    !tolower(stype) %in% c("references", "funding", "acknowledgment",
                           "author_contributions", "coi", "ethics", "keywords")
  body <- as.character(text_rows$text[keep])
  body <- trimws(gsub("[[:space:]]+", " ", body))
  body <- body[nzchar(body)]
  full_text <- paste(body, collapse = "\n")
  if (nchar(full_text, type = "chars") < 1000L) {
    excluded[[length(excluded) + 1L]] <- paste0(doi, ":short_or_empty")
    next
  }
  title <- as.character(info$title[[1]])
  if (is.na(title)) title <- ""
  n <- n + 1L
  records[[n]] <- data.frame(doi = doi, title = title, text = full_text,
                             stringsAsFactors = FALSE)
}
records <- records[seq_len(n)]
if (n != 748L) stop(sprintf("expected 748 extracted CC BY papers, got %d", n))
result <- do.call(rbind, records)
if (anyDuplicated(result$doi)) stop("duplicate DOI after extraction")
dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
write.csv(result, out_path, row.names = FALSE, fileEncoding = "UTF-8", na = "")
cat(sprintf("extracted_papers=%d\nexcluded=%d\ncsv_bytes=%d\n",
            nrow(result), length(excluded), file.info(out_path)$size))
