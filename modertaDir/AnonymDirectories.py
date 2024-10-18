import asyncio
import aiohttp
from urllib.parse import urljoin
import signal
import sys
import time
import logging
import multiprocessing
import os
from tqdm import tqdm
import random
from fake_useragent import UserAgent
import aiohttp_socks
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = multiprocessing.Manager().list()
scanned_count = multiprocessing.Value('i', 0)
total_directories = multiprocessing.Value('i', 0)
interrupt_event = multiprocessing.Event()

class DirectoryScanner:
    def __init__(self, base_url: str, proxy_list: List[str]):
        self.base_url = base_url
        self.proxy_list = proxy_list
        self.found_directories = []
        self.current_proxy_index = 0
        self.ua = UserAgent()
        
    def get_next_proxy(self) -> Optional[str]:
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    async def check_directory(self, directory: str) -> None:
        url = urljoin(self.base_url, directory)
        proxy = self.get_next_proxy()
        
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        try:
            if proxy:
                connector = aiohttp_socks.ProxyConnector.from_url(proxy)
            else:
                connector = aiohttp.TCPConnector(ssl=False)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        if not any(error_sign in content.lower() for error_sign in ['404', 'not found']):
                            print(f"[+] Found: {url}")
                            found_directories.append(url)
                            
        except Exception as e:
            logging.debug(f"Error checking {url}: {str(e)}")
        finally:
            await asyncio.sleep(random.uniform(1, 2))

def read_directories_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"File {filename} tidak ditemukan.")
        return []

def read_proxies_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"File proxy {filename} tidak ditemukan. Menggunakan tanpa proxy...")
        return []

def signal_handler(signum, frame):
    logging.info("\nInterrupt received, stopping processes...")
    interrupt_event.set()

def save_found_directories(directories):
    filename = 'found_directories.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        for directory in directories:
            f.write(f"{directory}\n")
    logging.info(f"Found directories saved to '{filename}'")

async def scan_worker(base_url, directories, proxy_list):
    scanner = DirectoryScanner(base_url, proxy_list)
    sem = asyncio.Semaphore(10)  # Batasi 10 request concurrent
    
    async def bounded_scan(directory):
        async with sem:
            await scanner.check_directory(directory)
    
    tasks = [bounded_scan(directory) for directory in directories]
    with tqdm(total=len(directories), desc="Scanning Progress") as pbar:
        for task in asyncio.as_completed(tasks):
            try:
                await task
                pbar.update(1)
            except Exception as e:
                logging.error(f"Error in scan worker: {str(e)}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = input("Masukkan URL website yang ingin di-scan: ")
    directories = read_directories_from_file('holderMin.txt')
    proxy_list = read_proxies_from_file('proxies.txt')
    
    if not directories:
        logging.error("Tidak ada direktori untuk di-scan.")
        return
    
    with total_directories.get_lock():
        total_directories.value = len(directories)
    
    try:
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(scan_worker(base_url, directories, proxy_list))
        
    except KeyboardInterrupt:
        logging.info("\nScanning dihentikan oleh user.")
    finally:
        logging.info("\nHasil scan:")
        for dir in found_directories:
            logging.info(dir)
        
        logging.info(f"\nTotal direktori ditemukan: {len(found_directories)}")
        save_found_directories(found_directories)

if __name__ == "__main__":
    main()