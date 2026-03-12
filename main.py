import csv
import json
import os

from scrapers.foodcity_scraper import FoodCityScraper
from scrapers.target_scraper import TargetScraper
from scrapers.walmart_scraper import WalmartScraper


URLS = [
    "https://www.target.com/p/noxzema-classic-clean-original-deep-cleansing-cream-12oz/-/A-11000080",
    "https://www.walmart.com/ip/Noxzema-Classic-Clean-Original-Deep-Cleansing-Cream-12-oz/10294073",
    "https://foodcityships.com/p/3085/Noxzema-Deep-Original-Classic-Clean-Cleansing-Cream--12-oz",
]


def get_scraper(url):
    url_lower = url.lower()

    if "target.com" in url_lower:
        return TargetScraper()

    if "walmart.com" in url_lower:
        return WalmartScraper()

    if "foodcityships.com" in url_lower:
        return FoodCityScraper()

    return None


def save_json_grouped(data, path="output/products.json"):
    grouped_data = {
        "foodcity": [item for item in data if item.get("website", "").lower() == "foodcity"],
        "target": [item for item in data if item.get("website", "").lower() == "target"],
        "walmart": [item for item in data if item.get("website", "").lower() == "walmart"],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, indent=4, ensure_ascii=False)


def save_csv(data, path="output/products.csv"):
    if not data:
        return

    rows = []
    for item in data:
        row = item.copy()
        if isinstance(row.get("size"), dict):
            row["size"] = json.dumps(row["size"], ensure_ascii=False)
        rows.append(row)

    fieldnames = [
        "website",
        "url",
        "product_name",
        "brand",
        "size",
        "price",
        "description",
        "ingredients",
        "image_url",
        "status",
        "error",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    os.makedirs("output", exist_ok=True)

    all_results = []

    for url in URLS:
        scraper = get_scraper(url)

        if scraper is None:
            all_results.append({
                "website": "Unknown",
                "url": url,
                "product_name": "",
                "brand": "",
                "size": "",
                "price": "",
                "description": "",
                "ingredients": "",
                "image_url": "",
                "status": "failed",
                "error": "No scraper found for this website",
            })
            continue

        try:
            result = scraper.scrape(url)

            print(f"Scraping finished for: {url}")
            print("Returned type:", type(result))
            print("Returned length:", len(result) if isinstance(result, list) else 1)

            if isinstance(result, list):
                all_results.extend(result)
            else:
                all_results.append(result)

        except Exception as e:
            site_name = scraper.__class__.__name__.replace("Scraper", "")
            all_results.append({
                "website": site_name,
                "url": url,
                "product_name": "",
                "brand": "",
                "size": "",
                "price": "",
                "description": "",
                "ingredients": "",
                "image_url": "",
                "status": "failed",
                "error": f"Unhandled scraper error: {str(e)}",
            })

    print("Final all_results length:", len(all_results))

    save_json_grouped(all_results)
    save_csv(all_results)

    print("Scraping completed.")
    print("JSON saved to: output/products.json")
    print("CSV saved to: output/products.csv")


if __name__ == "__main__":
    main()