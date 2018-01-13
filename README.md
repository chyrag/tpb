# tpb
The pirate bay utility

Simple utility that uses BeautifulSoup.

Usage:
*  tpb [--verbose] [--mirror=<mirror>] [--category=<category>] [--limit=<limit>] search <term>
   Search and display the given term.
*  tpb [--verbose] [--mirror=<mirror>] [--category=<category>] download <term>
   Search and download the first search result.
*  tpb [--verbose] [--mirror=<mirror>] --list-categories
   List the categories (not implemented)
*  tpb [--verbose] configure --mirror=<mirror>
   Configure the utility to use the given mirror for searching and downloading.
*  tpb [--verbose] show
   Dump the configuration.
*  tpb [--verbose] status
   Show the status of various pirate bay mirrors.
