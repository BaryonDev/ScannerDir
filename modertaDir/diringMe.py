import asyncio
import aiohttp
from urllib.parse import urljoin
import signal
import sys
import time
import logging
import multiprocessing
import os
import mmap
from tqdm import tqdm
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = multiprocessing.Manager().list()
scanned_count = multiprocessing.Value('i', 0)
total_directories = multiprocessing.Value('i', 0)
interrupt_event = multiprocessing.Event()

def read_directories_from_file(filename):
    try:
        with open(filename, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            return [line.decode('utf-8').strip() for line in mm.read().splitlines() if line.strip()]
    except FileNotFoundError:
        logging.error(f"File {filename} tidak ditemukan.")
        return []

def split_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

async def check_directory(session, base_url, directory, semaphore, pbar):
    if interrupt_event.is_set():
        raise asyncio.CancelledError()
    url = urljoin(base_url, directory)
    async with semaphore:
        try:
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
                ])
            }
            async with session.get(url, timeout=20, ssl=False, headers=headers) as response:
                if response.status == 200:
                    logging.info(f"[+] Directory found: {url}")
                    found_directories.append(url)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
    with scanned_count.get_lock():
        scanned_count.value += 1
    pbar.update(1)
    await asyncio.sleep(random.uniform(1, 3))  # Random delay between requests

async def scan_directories(base_url, directories, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        with tqdm(total=len(directories), desc="Scanning Progress", unit="dir") as pbar:
            tasks = [check_directory(session, base_url, directory, semaphore, pbar) for directory in directories]
            await asyncio.gather(*tasks, return_exceptions=True)

def worker(base_url, directories):
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(scan_directories(base_url, directories))
    except asyncio.CancelledError:
        logging.info("Worker process interrupted")

def signal_handler(signum, frame):
    logging.info("\nInterrupt received, stopping processes...")
    interrupt_event.set()

def print_progress():
    while not interrupt_event.is_set():
        scanned = scanned_count.value
        total = total_directories.value
        percentage = (scanned / total) * 100 if total > 0 else 0
        logging.info(f"Progress: {scanned}/{total} directories scanned ({percentage:.2f}%)")
        time.sleep(5) 

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = input("Masukkan URL website yang ingin di-scan: ")
    directories = read_directories_from_file('adminDir.txt')
    
    with total_directories.get_lock():
        total_directories.value = len(directories)
    
    num_processes = min(multiprocessing.cpu_count(), 4)  # Limit to 4 processes
    split_directories = list(split_list(directories, len(directories) // num_processes))
    
    progress_process = multiprocessing.Process(target=print_progress)
    progress_process.start()
    
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(base_url, split_directories[i]))
        processes.append(p)
        p.start()
    
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logging.info("Main process interrupted")
    finally:
        interrupt_event.set()
        progress_process.join()
        
        logging.info("\nHasil scan:")
        for dir in found_directories:
            logging.info(dir)
        
        logging.info(f"\nTotal direktori ditemukan: {len(found_directories)}")
        logging.info(f"Total direktori di-scan: {scanned_count.value}/{total_directories.value}")
        
        with open('found_directories.txt', 'w') as f:
            for directory in found_directories:
                f.write(f"{directory}\n")
        
        logging.info("Found directories saved to 'found_directories.txt'.")

if __name__ == "__main__":
    main()


