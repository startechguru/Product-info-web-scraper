import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from scrapers.base_scraper import BaseScraper
from utils.helpers import clean_text


class TargetScraper(BaseScraper):
    BASE_URL = "https://www.target.com"

    def make_product(self, url):
        return {
            "website": "Target",
            "url": url,
            "product_name": "",
            "brand": "",
            "size": {},
            "price": "",
            "description": "",
            "ingredients": "",
            "image_url": "",
            "status": "success",
            "error": ""
        }

    def make_error_product(self, url, error_message):
        return {
            "website": "Target",
            "url": url,
            "product_name": "",
            "brand": "",
            "size": {},
            "price": "",
            "description": "",
            "ingredients": "",
            "image_url": "",
            "status": "failed",
            "error": error_message
        }

    def build_full_url(self, href):
        if not href:
            return ""

        href = href.strip()

        if href.startswith("http://") or href.startswith("https://"):
            return href

        if href.startswith("//"):
            return "https:" + href

        if href.startswith("/"):
            return self.BASE_URL + href

        return self.BASE_URL + "/" + href

    def normalize_url(self, url):
        if not url:
            return ""

        url = url.strip()
        url = url.split("#")[0]

        base, sep, query = url.partition("?")
        if not sep:
            return base.rstrip("/")

        allowed_params = []
        for part in query.split("&"):
            if part.startswith("preselect="):
                allowed_params.append(part)

        if allowed_params:
            return base.rstrip("/") + "?" + "&".join(sorted(allowed_params))

        return base.rstrip("/")

    def is_target_product_url(self, url):
        if not url:
            return False

        normalized = self.normalize_url(url)
        return normalized.startswith(self.BASE_URL + "/p/") and "/-/A-" in normalized

    def is_target_unavailable_page(self, page):
        try:
            body_text = page.inner_text("body").lower()
        except Exception:
            body_text = ""

        unavailable_keywords = [
            "item not available",
            "not available at target",
            "sorry, this item isn't available",
            "page not found",
            "we couldn't find",
            "product not found",
            "something went wrong",
            "sorry, we're unable to process your request",
        ]

        return any(keyword in body_text for keyword in unavailable_keywords)

    def wait_for_page_settle(self, page):
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        page.wait_for_timeout(4000)

    def smart_scroll(self, page):
        try:
            previous_height = -1

            for _ in range(12):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(1200)

                try:
                    current_height = page.evaluate("document.body.scrollHeight")
                except Exception:
                    current_height = None

                if current_height == previous_height:
                    break

                previous_height = current_height

            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1500)
        except Exception as e:
            print("Scroll error:", e)

    def collect_sub_product_links(self, page, current_url):
        links = set()
        current_normalized = self.normalize_url(current_url)

        self.wait_for_page_settle(page)
        self.smart_scroll(page)

        try:
            html = page.content()
        except Exception:
            html = ""

        print("HTML length:", len(html))
        print("Contains '/-/A-' ?", "/-/A-" in html)

        selectors = [
            'a[href*="/-/A-"]',
            'a[href*="/p/"][href*="/-/A-"]',
            '[data-test="productCardVariantMini"] a[href]',
            '[data-test="product-card"] a[href]',
            '[data-test="product-title"] a[href]',
            'a[data-test="product-title"]',
            'a.styles_productCardLink__qh8df[href]',
            'a[href*="target.com/p/"][href*="/-/A-"]',
        ]

        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                print(f"Selector {selector} -> {len(elements)} elements")

                for el in elements:
                    href = el.get_attribute("href")
                    full_url = self.build_full_url(href)
                    normalized = self.normalize_url(full_url)

                    if not normalized:
                        continue
                    if not self.is_target_product_url(normalized):
                        continue
                    if normalized == current_normalized:
                        continue

                    links.add(normalized)
            except Exception as e:
                print(f"Selector failed: {selector} -> {e}")

        try:
            regex_patterns = [
                r'href="([^"]*?/p/[^"]*?/-/A-\d+[^"]*)"',
                r'"url":"(https:\\/\\/www\.target\.com\\/p\\/.*?\\/-\\/A-\d+[^"]*)"',
                r'"canonicalUrl":"(https:\\/\\/www\.target\.com\\/p\\/.*?\\/-\\/A-\d+[^"]*)"',
            ]

            for pattern in regex_patterns:
                matches = re.findall(pattern, html)
                print(f"Regex pattern {pattern} -> {len(matches)} matches")

                for href in matches:
                    href = href.replace("\\/", "/")
                    full_url = self.build_full_url(href)
                    normalized = self.normalize_url(full_url)

                    if not normalized:
                        continue
                    if not self.is_target_product_url(normalized):
                        continue
                    if normalized == current_normalized:
                        continue

                    links.add(normalized)
        except Exception as e:
            print("Regex extraction failed:", e)

        final_links = sorted(list(links))
        print("Final unique links:", len(final_links))
        for i, link in enumerate(final_links, 1):
            print(f"[{i}] {link}")

        return final_links

    def scrape(self, url):
        results = []
        playwright = browser = context = page = None

        try:
            playwright, browser, context, page = self.open_page(url)
            self.wait_for_page_settle(page)

            is_unavailable = self.is_target_unavailable_page(page)
            print("Unavailable page detected:", is_unavailable)

            if is_unavailable:
                sub_links = self.collect_sub_product_links(page, url)

                if len(sub_links) == 0:
                    results.append(self.make_error_product(url, "No related product links found"))
                    return results

                seen_urls = set()

                for i, full_url in enumerate(sub_links, start=1):
                    normalized = self.normalize_url(full_url)

                    if normalized in seen_urls:
                        print("Duplicate sub page skipped:", normalized)
                        continue

                    seen_urls.add(normalized)
                    print(f"Opening sub page {i}: {normalized}")

                    sub_page = None
                    try:
                        sub_page = context.new_page()
                        sub_page.set_default_timeout(45000)
                        sub_page.set_default_navigation_timeout(45000)

                        response = sub_page.goto(normalized, timeout=45000, wait_until="domcontentloaded")
                        self.wait_for_page_settle(sub_page)

                        print("Goto response:", response.status if response else "No response")
                        print("Loaded final url:", sub_page.url)

                        product = self.scrape_product_page(sub_page, self.normalize_url(sub_page.url or normalized))
                        if not product.get("product_name"):
                            product["status"] = "failed"
                            product["error"] = product["error"] or "Product title not found"

                        results.append(product)

                    except PlaywrightTimeoutError:
                        print("Timeout while opening:", normalized)
                        results.append(self.make_error_product(normalized, "Sub-page timeout"))

                    except Exception as e:
                        print("Sub-page error:", normalized, str(e))
                        results.append(self.make_error_product(normalized, str(e)))

                    finally:
                        try:
                            if sub_page:
                                sub_page.close()
                        except Exception:
                            pass

                if len(results) == 0:
                    results.append(self.make_error_product(url, "Sub-links found but no products scraped"))

            else:
                product = self.scrape_product_page(page, self.normalize_url(page.url or url))
                results.append(product)

        except Exception as e:
            results.append(self.make_error_product(url, str(e)))

        finally:
            try:
                if page:
                    page.close()
            except Exception:
                pass

            try:
                if context:
                    context.close()
            except Exception:
                pass

            try:
                if browser:
                    browser.close()
            except Exception:
                pass

            try:
                if playwright:
                    playwright.stop()
            except Exception:
                pass

        deduped = []
        seen = set()

        for item in results:
            normalized = self.normalize_url(item.get("url", ""))
            key = (
                normalized,
                clean_text(item.get("product_name", "")).lower(),
                clean_text(item.get("image_url", "")).lower(),
            )

            if key in seen:
                print("Duplicate result removed:", key)
                continue

            seen.add(key)
            item["url"] = normalized
            deduped.append(item)

        print("Total products scraped:", len(deduped))
        return deduped

    def scrape_product_page(self, page, url):
        product = self.make_product(url)

        try:
            self.wait_for_page_settle(page)

            product["product_name"] = clean_text(
                self.safe_text(page, '#pdp-product-title-id')
                or self.safe_text(page, 'h1[data-test="product-title"]')
                or self.safe_text(page, "h1")
            )

            product["price"] = clean_text(
                self.safe_text(page, '[data-test="product-price"]')
                or self.safe_text(page, '[data-test="current-price"]')
            )

            product["description"] = self.extract_description(page)

            product["image_url"] = (
                self.safe_attr(page, 'picture img', 'src')
                or self.safe_attr(page, 'img[alt]', 'src')
                or self.safe_attr(page, 'img', 'src')
            )

            brand, size_data = self.extract_brand_and_size(page)
            product["brand"] = brand
            product["size"] = size_data

            product["ingredients"] = self.extract_ingredients(page)

            if not product["product_name"]:
                product["status"] = "failed"
                product["error"] = "Product title not found"

        except Exception as e:
            product["status"] = "failed"
            product["error"] = str(e)

        return product

    def extract_description(self, page):
        selectors = [
            '[data-test="item-details-description"]',
            'div[data-test="item-details-description"]',
        ]

        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                for el in elements:
                    text = clean_text(el.inner_text())
                    if text:
                        return text
            except Exception:
                pass

        try:
            text = page.evaluate(
                """() => {
                    const el = document.querySelector('[data-test="item-details-description"]');
                    return el ? (el.innerText || el.textContent || "").trim() : "";
                }"""
            )
            text = clean_text(text)
            if text:
                return text
        except Exception:
            pass

        return ""

    def extract_brand_and_size(self, page):
        brand = ""
        size_data = {}

        breadcrumb_nodes = page.query_selector_all('[data-test="@web/Breadcrumbs/BreadcrumbLink"]')
        breadcrumb_values = []

        for node in breadcrumb_nodes:
            try:
                text = clean_text(node.inner_text())
                if text:
                    breadcrumb_values.append(text)
            except Exception:
                pass

        if breadcrumb_values:
            brand = breadcrumb_values[-1]

        spans = page.query_selector_all('.styles_headerSpan__wl9MD')

        for span in spans:
            try:
                key = clean_text(span.inner_text())
                if not key:
                    continue

                value = ""
                try:
                    value = span.evaluate(
                        """el => {
                            let node = el.nextSibling;
                            let collected = "";

                            while (node) {
                                if (node.nodeType === Node.TEXT_NODE) {
                                    const t = (node.textContent || "").trim();
                                    if (t) {
                                        collected = t;
                                        break;
                                    }
                                } else if (node.nodeType === Node.ELEMENT_NODE) {
                                    const t = (node.innerText || node.textContent || "").trim();
                                    if (t) {
                                        collected = t;
                                        break;
                                    }
                                }
                                node = node.nextSibling;
                            }

                            return collected.trim();
                        }"""
                    )
                except Exception:
                    value = ""

                value = clean_text(value)

                if key and value and key != value:
                    size_data[key] = value
            except Exception:
                pass

        if not brand:
            try:
                values = []
                fallback_spans = page.query_selector_all('.styles_headerSpan__wl9MD')
                for span in fallback_spans:
                    text = clean_text(span.inner_text())
                    if text:
                        values.append(text)
                if values:
                    brand = values[0]
            except Exception:
                pass

        return brand, size_data

    def extract_ingredients(self, page):
        try:
            caps_nodes = page.query_selector_all('.h-text-transform-caps')
            contents = []

            for node in caps_nodes:
                try:
                    text = clean_text(node.inner_text())
                    if text:
                        contents.append(text)
                except Exception:
                    pass

            if contents:
                return " ".join(contents)
        except Exception:
            pass

        try:
            body_text = page.inner_text("body")
            return self.get_ingredients(body_text)
        except Exception:
            return ""

    def get_ingredients(self, text):
        if not text:
            return ""

        lower_text = text.lower()
        idx = lower_text.find("ingredients")

        if idx == -1:
            return ""

        snippet = text[idx:idx + 1000]
        return clean_text(snippet)