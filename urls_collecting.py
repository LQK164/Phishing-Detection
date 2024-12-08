import logging
import logging.config
import os
from typing import Callable, TypeVar

import httpx

# Cấu hình logging
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "phase1",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "phase1",
            "filename": "url_count.log",
        },
    },
    "formatters": {
        "phase1": {
            "format": "%(levelname)s [%(asctime)s] %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
        },
    },
}
logging.config.dictConfig(LOGGING_CONFIG)

T = TypeVar("T")


def get(
    client: httpx.Client,
    url: str,
    apply_fn: Callable[[httpx.Response], T] | None = None,
):
    response = client.get(url)

    if response.status_code == 200:
        if apply_fn:
            return apply_fn(response)
        return response
    else:
        response.raise_for_status()


# Hàm lấy dữ liệu từ OpenPhish
def get_openphish_data(client: httpx.Client):
    return get(
        client,
        "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt",
        lambda response: response.text.splitlines(),
    )


# Hàm lưu tối đa 10 URL vào file
def save_urls_to_file(
    urls: list[str], folder_path: str, filename: str, max_urls: int = 10
):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, filename)

    with open(file_path, "w", encoding="utf-8") as file:
        for url in urls[:max_urls]:  # Chỉ lấy tối đa `max_urls` URL
            file.write(url + "\n")


if __name__ == "__main__":
    with httpx.Client(follow_redirects=True) as client:
        # Thu thập URL từ OpenPhish
        logging.info("Getting URLs from API")
        try:
            openphish_urls = get_openphish_data(client)
        except Exception as e:
            logging.error(f"OpenPhish: {e}")
            openphish_urls = []

    # Lưu tối đa 10 URL vào file
    if openphish_urls:
        logging.info(f"Saved OpenPhish URLs")
        logging.info(f"Saved PhishStats URLs")
        logging.info(f"Saved PhishTank URLs")
        save_urls_to_file(
            openphish_urls, "./URLs_Storage", "openphish_urls.txt", max_urls=10
        )
