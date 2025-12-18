# Amazon.de Playwright Mini-Challenge — “Harry Potter Buch”

This repository contains a small **web automation** script built with **Python + Playwright** that:

- Opens **amazon.de**
- Searches for **"Harry Potter Buch"**
- Clicks the **first organic** search result (best-effort: skips **Gesponsert / Anzeige**)
- Extracts the **full product title** and **price** from the product page
- Prints the result to the console as a clean JSON object
