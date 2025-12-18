import json
from playwright.sync_api import sync_playwright


def handle_cookies_and_popups(page):
    #Checks for and closes cookie
    try:
        if page.get_by_text("Weiter shoppen").is_visible(timeout=1000):
            page.get_by_text("Weiter shoppen").click()
    except:
        pass

    try:
        # Check for multiple variations of the cookie accept button
        selectors = ["#sp-cc-accept", "[data-cel-widget='sp-cc-accept']", "input[name='accept']", "text=Akzeptieren"]
        for sel in selectors:
            if page.locator(sel).first.is_visible(timeout=500):
                page.locator(sel).first.click()
                page.wait_for_timeout(500)
                return
    except:
        pass


def scrape_amazon():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="de-DE"
        )
        page = context.new_page()

        try:
            # --- STEP 1: NAVIGATION ---
            print("--- Step 1: Navigation ---")
            page.goto("https://www.amazon.de", wait_until="domcontentloaded")
            handle_cookies_and_popups(page)

            # --- STEP 2: SEARCH INPUT ---
            print("\n--- Step 2: Search Interaction ---")
            search_input = page.locator("#twotabsearchtextbox")
            search_input.wait_for(state="visible", timeout=10000)

            print("Typing search query...")
            search_input.fill("Harry Potter Buch")
            search_input.press("Enter")

            page.wait_for_selector("div[data-component-type='s-search-result']", timeout=15000)

            handle_cookies_and_popups(page)

            # --- STEP 3: PROCESSING RESULTS ---
            print("\n--- Step 3: Processing Results ---")
            # Scroll to ensure lazy-loaded elements appear
            for _ in range(3):
                page.mouse.wheel(0, 800)
                page.wait_for_timeout(500)

            # Select all result containers
            results = page.locator("div[data-component-type='s-search-result']").all()
            print(f"Found {len(results)} total items. Inspecting...")

            target_url = None

            for index, card in enumerate(results):
                card_text = card.inner_text()

                # --- CHECK 1: SPONSORED ---
                # Check for "Sponsored"
                if card.locator(".puis-sponsored-label-text").count() > 0 or \
                        "Gesponsert" in card_text[:100] or \
                        "Sponsored" in card_text[:100]:
                    print(f"Result {index + 1}: Skipped (Sponsored)")
                    continue

                # --- CHECK 2: FIND TITLE & LINK ---
                link_locator = None

                if card.locator("h2 a").count() > 0:
                    link_locator = card.locator("h2 a").first

                elif card.locator("a.a-link-normal .a-text-normal").count() > 0:
                    link_locator = card.locator("a.a-link-normal").filter(has=page.locator(".a-text-normal")).first

                elif card.locator("a[href*='/dp/']").count() > 0:
                    link_locator = card.locator("a[href*='/dp/']").first

                if not link_locator:
                    html_snippet = card.inner_html()[:200].replace("\n", "")
                    print(f"Result {index + 1}: Skipped (Structure unknown). HTML snippet: {html_snippet}...")
                    continue

                # --- CHECK 3: VALIDATE LINK ---
                url = link_locator.get_attribute("href")
                if not url:
                    continue

                # Normalize URL
                if not url.startswith("http"):
                    url = "https://www.amazon.de" + url

                print(f"Result {index + 1}: MATCH FOUND! -> {url}")
                target_url = url
                break

            if not target_url:
                raise Exception("Could not find any organic product links.")

            # --- STEP 4: EXTRACT PRODUCT DATA ---
            print("\n--- Step 4: Extract Product Data ---")
            page.goto(target_url, wait_until="domcontentloaded")
            handle_cookies_and_popups(page)

            # Get Title
            title = page.locator("#productTitle").inner_text().strip()

            # Get Price
            price = "N/A"
            price_selectors = [
                "#price", ".a-price .a-offscreen", "#price_inside_buybox",
                "#kindle-price", ".apexPriceToPay", "#tmm-grid-swatch-PAPERBACK .a-color-price"
            ]
            for sel in price_selectors:
                if page.locator(sel).first.is_visible():
                    price = page.locator(sel).first.inner_text().strip()
                    break

            result = {"title": title, "price": price}
            print("\n" + "=" * 40)
            print(json.dumps(result, indent=4, ensure_ascii=False))
            print("=" * 40)

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="final_debug.png")
        finally:
            browser.close()


if __name__ == "__main__":
    scrape_amazon()