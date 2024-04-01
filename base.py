import random
import sys
import time

import requests
from loguru import logger
from selectolax.parser import HTMLParser
import re
from urllib.parse import urljoin

logger.remove()
logger.add('books.log', rotation='700kb', level='WARNING')
logger.add(sys.stderr, level='INFO')


# function to retrieve all urls for all books in the library
def get_all_books_urls(url: str) -> list[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                      " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    urls = []
    with requests.Session() as session:
        while True:
            try:
                # logger.info(f"scraping page at {url}")
                response = session.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Http requests error from {url}: {e}")
                continue

            tree = HTMLParser(response.text)
            book_urls = get_all_books_urls_on_page(url, tree)
            urls.extend(book_urls)
            url = get_next_page_url(url, tree)
            if not url:
                break

        return urls


def get_next_page_url(url: str, tree: HTMLParser) -> str | None:
    next_page_note = tree.css_first("li.next > a")
    if next_page_note and "href" in next_page_note.attributes:
        return urljoin(url, next_page_note.attributes['href'])
    logger.info(f"No next page:{url}")


def get_all_books_urls_on_page(url: str, tree: HTMLParser) -> list[str]:
    try:
        all_book_urls = tree.css("h3 > a")
        return [urljoin(url, link.attributes['href']) for link in all_book_urls if "href" in link.attributes]

    except Exception as e:
        logger.error(f"something went wrong to extract urls of books: {e}")
        return []


def get_book_price(url: str, session: requests.Session = None) -> float:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                      " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    try:
        if session:
            response = session.get(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree = HTMLParser(response.text)
        price = extract_price_from_page(tree=tree)
        stock = extract_stock_quantity_from_page(tree=tree)
        price_stock = price * stock
        logger.info(f"get book price at {url}: found {price_stock}")
        return price_stock

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
    base_url = "https://books.toscrape.com/index.html"
    all_books_urls = get_all_books_urls(url=base_url)
    total_price = []
    with requests.Session() as session:
        for book_url in all_books_urls:
            price = get_book_price(url=book_url, session=session)
            total_price.append(price)
            time.sleep(random.uniform(0.8, 1))
        return sum(total_price)


if __name__ == '__main__':
    print(main())
