import os
from icrawler.builtin import GoogleImageCrawler

def download_google_images(query, num_images=5):
    """
    Downloads images from Google using icrawler.

    Parameters:
        query (str): The search term for images.
        num_images (int): Number of images to download.
    """
    save_dir = f"./images/{query.replace(' ', '_')}"
    os.makedirs(save_dir, exist_ok=True)

    google_crawler = GoogleImageCrawler(storage={"root_dir": save_dir})
    google_crawler.crawl(keyword=query, max_num=num_images)

    print(f"Downloaded {num_images} images for query: '{query}' in {save_dir}")

if __name__ == "__main__":
    search_query = input("Enter search query: ")
    num_images = int(input("Enter number of images to download: "))

    download_google_images(search_query, num_images)
