from playwright.sync_api import sync_playwright


class BaseScraper:
    def __init__(self):
        self.timeout = 30000

    def open_page(self, url):
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1400, "height": 2200},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
        )

        page = context.new_page()
        page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        return playwright, browser, context, page

    def safe_text(self, page, selector):
        try:
            el = page.query_selector(selector)
            return el.inner_text().strip() if el else ""
        except Exception:
            return ""

    def safe_attr(self, page, selector, attr):
        try:
            el = page.query_selector(selector)
            return el.get_attribute(attr) if el else ""
        except Exception:
            return ""