import asyncio
import aiohttp
from urllib.parse import urljoin
import signal
import sys
import time
import logging
import random
import argparse
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = []
scanned_count = 0
total_directories = 0
interrupt_event = asyncio.Event()

def read_directories_from_file(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"File {filename} tidak ditemukan.")
        return []

async def check_directory(session, base_url, directory, pbar):
    if interrupt_event.is_set():
        return
    url = urljoin(base_url, directory)
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    try:
        async with session.get(url, timeout=10, ssl=False, headers=headers, allow_redirects=False) as response:
            if response.status in [200, 301, 302, 307]:
                logging.info(f"[+] Directory found: {url}")
                found_directories.append(url)
    except Exception as e:
        logging.debug(f"Error checking {url}: {str(e)}")
    finally:
        global scanned_count
        scanned_count += 1
        pbar.update(1)
    await asyncio.sleep(random.uniform(2, 5))  # Random delay between requests

async def scan_directories(base_url, directories, max_concurrent=3):
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent, ssl=False, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        with tqdm(total=len(directories), desc="Scanning Progress", unit="dir") as pbar:
            tasks = [check_directory(session, base_url, directory, pbar) for directory in directories]
            await asyncio.gather(*tasks, return_exceptions=True)

def signal_handler(signum, frame):
    logging.info("\nInterrupt received, stopping processes...")
    interrupt_event.set()

async def print_progress():
    global scanned_count, total_directories
    while not interrupt_event.is_set():
        percentage = (scanned_count / total_directories) * 100 if total_directories > 0 else 0
        logging.info(f"Progress: {scanned_count}/{total_directories} directories scanned ({percentage:.2f}%)")
        await asyncio.sleep(10)

async def main(args):
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = args.url
    directories = read_directories_from_file(args.file)
    
    global total_directories
    total_directories = len(directories)
    
    progress_task = asyncio.create_task(print_progress())
    
    try:
        await scan_directories(base_url, directories, max_concurrent=args.concurrent)
    except asyncio.CancelledError:
        logging.info("Scanning interrupted")
    finally:
        interrupt_event.set()
        await progress_task
        
        logging.info("\nHasil scan:")
        for dir in found_directories:
            logging.info(dir)
        
        logging.info(f"\nTotal direktori ditemukan: {len(found_directories)}")
        logging.info(f"Total direktori di-scan: {scanned_count}/{total_directories}")
        
        with open('found_directories.txt', 'w') as f:
            for directory in found_directories:
                f.write(f"{directory}\n")
        
        logging.info("Found directories saved to 'found_directories.txt'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Directory Scanner")
    parser.add_argument("url", help="Base URL to scan")
    parser.add_argument("file", help="File containing directory list")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent requests (default: 3)")
    args = parser.parse_args()
    
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args))