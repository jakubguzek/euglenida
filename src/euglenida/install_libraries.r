#!/usr/bin/env Rscript
# Funcation for loading packages, taken from
# https://gitlab.com/iembry/install.load
install_load <- function(package1, ...,
                         installation_function = install.packages,
                         verbose = FALSE,
                         repos = "https://cloud.r-project.org") {
  # convert arguments to vector
  packages <- c(package1, ...)

  # start loop to determine if each package is installed
  for (package in packages) {
    # if package is installed locally, load
    if (package %in% rownames(installed.packages())) {
      if (verbose) print(paste("Loading libarary", package))
      try(do.call(library, list(package))) # Source 2
    } else {
      # if package is not installed locally, download and then load
      if (verbose) {
        print(paste(
          "Library", package, "is not installed. Trying to install it..."
        ))
      }
      installation_function(
        package,
        repos = repos,
        dependencies = NA,
        type = getOption("pkgType")
      )
      try(do.call(library, list(package))) # Source 2
    }
  }
}

install_analyses_libraries <- function(verbose = FALSE) {
  if (verbose) print("Installing R libraries")

  if (!require("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager")
  }

  # Load phyloseq or install it using BiocManager if it's not already installed.
  biocmanages_packages <- c("phyloseq")
  install_load(
    biocmanages_packages,
    installation_function = function(p) BiocManager::install(p, force = TRUE),
    verbose = verbose
  )

  # Load CRAN ackages or install them if they ar not already installed,
  cran_packages <- c(
    "vegan", "tidyverse", "ggplot2", "plyr", "dplyr", "fansi", "remotes"
  )
  install_load(cran_packages, verbose = verbose)

  # Load qiime2R or install it if it's not already installed.
  remotes_packages <- c("jbisanz/qiime2R")
  install_load(
    remotes_packages,
    installation_function = function(p) remotes::install_github(p),
    verbose = verbose
  )
  return(0)
}

main <- function() {
  retval <- install_analyses_libraries(verbose = TRUE)
  return(retval)
}

if (!interactive()) {
  main()
}
