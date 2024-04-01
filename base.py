import sys
import requests
from loguru import logger
from selectolax.parser import HTMLParser
import re
from urllib.parse import urljoin

logger.remove()
logger.add('books.log', rotation='700kb', level='WARNING')
logger.add(sys.stderr, level='INFO')

base_url = "https://books.toscrape.com/index.html"


# function to retrieve all urls for all books in the library
def get_all_books_urls(url: str) -> list[str]:
    pass


def get_next_page_url(tree: HTMLParser) -> str:
    next_page_note = tree.css_first("li.next > a")
    if next_page_note and "href" in next_page_note.attributes:
        return urljoin(base_url, next_page_note.attributes['href'])
    logger.info("No next page")


def get_all_books_urls_on_page(tree: HTMLParser) -> list[str]:
    try:
        all_book_urls = tree.css("h3 > a")
        return [urljoin(base_url, link.attributes['href']) for link in all_book_urls if "href" in link.attributes]

    except Exception as e:
        logger.error(f"something went wrong to extract urls of books: {e}")
        return []


def get_book_price(url: str) -> float:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                      " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree = HTMLParser(response.text)
        price = extract_price_from_page(tree=tree)
        stock = extract_stock_quantity_from_page(tree=tree)
        return price * stock

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error : {e}")
        return 0.0


def extract_price_from_page(tree: HTMLParser) -> float:
    price_node = tree.css_first("p.price_color")

    if price_node:
        price_string = price_node.text()
    else:
        logger.error("price not found")
        return 0.0

    try:
        price = re.findall(r"[0-9.]+", price_string)[0]
    except IndexError as e:
        logger.error(f"something went wrong: {e}")
        return 0.0
    else:
        return float(price)


def extract_stock_quantity_from_page(tree: HTMLParser) -> int:
    try:
        quantity_node = tree.css_first('p.instock.availability')
        if quantity_node:
            return int(re.findall(f"\d+", quantity_node.text())[0])

    except AttributeError as e:
        logger.error(f"stock not found: {e}")
        return 0
    except IndexError as e:
        logger.error(f"something went wrong : {e}")
        return 0


def main():
    all_books_urls = get_all_books_urls(url=base_url)
    total_price = []
    for book_url in all_books_urls:
        price = get_book_price(url=book_url)
        total_price.append(price)
        return sum(total_price)


if __name__ == '__main__':
    r = requests.get(base_url)
    tree = HTMLParser(r.text)
    print(get_next_page_url(tree))
