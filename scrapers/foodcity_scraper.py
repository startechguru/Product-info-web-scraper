import json
import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from scrapers.base_scraper import BaseScraper
from utils.helpers import clean_text


class FoodCityScraper(BaseScraper):
    WEBSITE = "FoodCity"

    def make_product(self, url):
        return {
            "website": self.WEBSITE,
            "url": url,
            "product_name": "",
            "brand": "",
            "size": "",
            "price": "",
            "description": "",
            "ingredients": "",
            "image_url": "",
            "status": "success",
            "error": ""
        }

    def make_error_product(self, url, error_message):
        product = self.make_product(url)
        product["status"] = "failed"
        product["error"] = error_message
        return product

    def scrape(self, url):
        playwright = browser = context = page = None

        try:
            playwright, browser, context, page = self.open_page(url)

            problem = self.detect_page_problem(page)
            if problem:
                return [self.make_error_product(url, problem)]

            return [self.scrape_product_page(page, url)]

        except PlaywrightTimeoutError:
            return [self.make_error_product(url, "Page load timeout")]
        except Exception as e:
            return [self.make_error_product(url, str(e))]
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

    def detect_page_problem(self, page):
        try:
            body_text = clean_text(page.inner_text("body")).lower()

            known_problems = [
                "not found",
                "page not found",
                "temporarily unavailable",
                "access denied",
                "forbidden",
                "error",
                "service unavailable",
            ]

            for problem in known_problems:
                if problem in body_text:
                    return f"Website issue detected: {problem}"

            if not page.url or "foodcityships.com" not in page.url:
                return "Unexpected redirect or invalid page URL"

            return ""
        except Exception as e:
            return f"Could not validate page state: {e}"

    def scrape_product_page(self, page, url):
        product = self.make_product(url)

        try:
            page.wait_for_timeout(2500)

            json_ld_data = self.extract_json_ld(page)

            if json_ld_data:
                product["product_name"] = clean_text(json_ld_data.get("name", ""))
                product["description"] = clean_text(
                    self.strip_html(json_ld_data.get("description", ""))
                )
                product["image_url"] = self.extract_image_from_json_ld(json_ld_data)
                product["brand"] = self.extract_brand_from_json_ld(json_ld_data)
                product["price"] = self.extract_price_from_json_ld(json_ld_data)

            if not product["product_name"]:
                product["product_name"] = clean_text(
                    self.safe_text(page, "h1")
                    or self.safe_text(page, '[class*="product-title"]')
                )

            if not product["price"]:
                product["price"] = clean_text(
                    self.safe_text(page, '[class*="price"]')
                    or self.safe_text(page, '[data-testid*="price"]')
                )

            if not product["description"]:
                product["description"] = clean_text(
                    self.safe_text(page, '[class*="description"]')
                    or self.safe_text(page, '[data-testid*="description"]')
                )

            if not product["image_url"]:
                product["image_url"] = (
                    self.safe_attr(page, 'img[src*="product"]', "src")
                    or self.safe_attr(page, "img", "src")
                )

            if not product["brand"]:
                product["brand"] = self.extract_brand(
                    product["product_name"], product["description"]
                )

            product["size"] = self.extract_size(
                product["product_name"], product["description"]
            )

            product["ingredients"] = self.extract_ingredients(page)

            if not product["product_name"]:
                product["status"] = "failed"
                product["error"] = "Product title not found"

        except Exception as e:
            product["status"] = "failed"
            product["error"] = str(e)

        return product

    def extract_json_ld(self, page):
        try:
            scripts = page.query_selector_all('script[type="application/ld+json"]')
            for script in scripts:
                raw = script.inner_text().strip()
                if not raw:
                    continue

                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                found = self.find_product_object(data)
                if found:
                    return found
        except Exception:
            pass

        return {}

    def find_product_object(self, data):
        if isinstance(data, dict):
            if data.get("@type") == "Product":
                return data

            for value in data.values():
                found = self.find_product_object(value)
                if found:
                    return found

        elif isinstance(data, list):
            for item in data:
                found = self.find_product_object(item)
                if found:
                    return found

        return {}

    def extract_brand_from_json_ld(self, data):
        brand = data.get("brand", "")
        if isinstance(brand, dict):
            return clean_text(brand.get("name", ""))
        return clean_text(brand)

    def extract_price_from_json_ld(self, data):
        offers = data.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]

        if isinstance(offers, dict):
            price = clean_text(str(offers.get("price", "")))
            currency = clean_text(str(offers.get("priceCurrency", "")))
            if price and currency:
                return f"{currency} {price}"
            return price

        return ""

    def extract_image_from_json_ld(self, data):
        image = data.get("image", "")
        if isinstance(image, list):
            return clean_text(image[0]) if image else ""
        return clean_text(image)

    def extract_brand(self, name, description):
        for text in [name, description]:
            if not text:
                continue

            cleaned = clean_text(text)
            parts = cleaned.split()
            if parts:
                return parts[0]

        return ""

    def extract_size(self, name, description):
        texts = [name, description]
        pattern = r"\b(\d+(?:\.\d+)?)\s?(oz|fl oz|ml|l|lb|g|kg|count|ct)\b"

        for text in texts:
            if not text:
                continue
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return clean_text(match.group(0))

        return ""

    def extract_ingredients(self, page):
        selectors = [
            '[id*="ingredient"]',
            '[class*="ingredient"]',
            '[data-testid*="ingredient"]',
        ]

        for selector in selectors:
            text = clean_text(self.safe_text(page, selector))
            if text:
                return text

        try:
            body_text = clean_text(page.inner_text("body"))
            match = re.search(
                r"(ingredients[:\s].{0,1200})",
                body_text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if match:
                return clean_text(match.group(1))
        except Exception:
            pass

        return ""

    def strip_html(self, text):
        return re.sub(r"<[^>]+>", " ", text or "").strip()