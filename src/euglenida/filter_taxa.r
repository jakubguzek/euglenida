#!/usr/bin/env Rscript

suppressWarnings(suppressMessages(library(R.utils)))
library(optparse)
library(qiime2R)
library(phyloseq)
suppressWarnings(suppressMessages(library(vegan)))

create_options <- function() {
  options <- list(
    make_option(
      c("-f", "--features"),
      type = "character",
      help = "input file with table containing number of reads per sample"
    ),
    make_option(
      "--tree",
      type = "character",
      help = "input file with phylogenetic tree of reads"
    ),
    make_option(
      "--metadata",
      type = "character",
      help = "input file with metadata"
    ),
    make_option(
      "--taxonomy",
      type = "character",
      help = "input file with table containig taxonomical classification"
    ),
    make_option(
      "--verbose",
      default = FALSE,
      action = "store_true",
      help = "Make output more verbose"
    ),
    make_option(
      c("-o", "--outdir"),
      default = "./results/phyloseq",
      type = "character",
      help = "Path to directory where filtered data and rarecurve should be saved."
    ),
    make_option(
      "--step",
      default = 50,
      type = "integer",
      help = "Step argument for rarecurve function."
    ),
    make_option(
      "--glom",
      type = "character",
      metavar = "GLOM_LEVEL",
      help = "Whether to glom taxa at some level and at what level"
    )
  )
  parser <- OptionParser(option_list = options)
  return(parser)
}

print_args <- function(args) {
  printf("Commandline aguments:\n")
  for (i in seq_along(args)) {
    printf(paste("\t", names(args)[i], ":", args[i], end = "\n"))
  }
}

print_phyloseq_object_info <- function(phyloseq_object) {
  print(phyloseq_object)
  printf("Sample names:\n")
  print(sample_names(phyloseq_object))
  printf("Sample metadata columns:\n")
  print(sample_variables(phyloseq_object))
  printf("Taxonomic ranks in data: ")
  print(rank_names(phyloseq_object))
  printf("Taxa per sample in data:\n")
  print(sample_sums(phyloseq_object))
}

main <- function() {
  parser <- create_options()
  args <- parse_args(parser)
  if (
    is.null(args$features) || is.null(args$tree) ||
      is.null(args$metadata) || is.null(args$taxonomy)
  ) {
    print_help(parser)
    stop("At least one argument must be supplied (input file).n", call. = FALSE)
  }

  if (args$verbose) {
    sink(stderr())
    options(error = function() {
      on.exit(sink(NULL))
      traceback(3, max.lines = 1L)
      if (!interactive()) {
        q(status = 1)
      }
    })
  }

  if (args$verbose) print_args(args)

  if (!dir.exists(args$outdir)) {
    printf("No such file or directory: %s\n", args$outdir)
    printf("Creating output directory: %s\n", args$outdir)
    dir.create(args$outdir)
  }

  if (args$verbose) printf("Creating phyloseq object from qiime2 artifact..\n")
  data <- qza_to_phyloseq(
    features = args$features,
    tree = args$tree,
    taxonomy = args$taxonomy,
    metadata = args$metadata
  )

  if (args$verbose) print_phyloseq_object_info(data)
  if (args$verbose) printf("\nFiltering out non-euglenida taxa...\n")

  filtered_data <- subset_taxa(data, Order == "Euglenida")
  if (!is.null(args$glom) || length(args$glom > 0)) {
    if (!args$glom %in% rank_names(filtered_data)) {
      stop(paste("Incorrect rank name for tax_glom:", args$glom))
    }
    printf("Glomming taxa at level: %s\n", args$glom)
    filtered_data <- tax_glom(filtered_data, args$glom)
  }

  if (args$verbose) print_phyloseq_object_info(filtered_data)

  rds_save_path <- paste(args$outdir, "/filtered_phyloseq.rds", sep = "")
  if (args$verbose) printf("Saving filtered data to: %s\n", rds_save_path)
  saveRDS(filtered_data, rds_save_path)

  rarecurve_save_path <- paste(args$outdir, "/rarecurve.pdf", sep = "")
  if (args$verbose) printf("Saving rarevurve plot to: %s\n", rarecurve_save_path)
  pdf(rarecurve_save_path, height = 5, width = 13)
  rarecurve(
    data.frame(t(otu_table(filtered_data))),
    step = 50,
    cex = 0.9,
    label = FALSE,
    col = rainbow(12),
  )
  dev.off()

  X11(height = 5, width = 12)
  rarecurve(
    data.frame(t(otu_table(filtered_data))),
    step = 50,
    cex = 0.9,
    label = FALSE,
    col = rainbow(12),
  )
  while (names(dev.cur()) != "null device") Sys.sleep(1)

  if (args$verbose) {
    X11(height = 5, width = 12)
    hist(taxa_sums(filtered_data), breaks = 50, xlab = "Number of reads")
    while (names(dev.cur()) != "null device") Sys.sleep(1)
  }
}

if (!interactive()) {
  main()
}
