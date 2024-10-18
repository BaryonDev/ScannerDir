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
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = multiprocessing.Manager().list()
scanned_count = multiprocessing.Value('i', 0)
total_directories = multiprocessing.Value('i', 0)
interrupt_event = multiprocessing.Event()
ua = UserAgent()

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
    
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }
    
    async with semaphore:
        try:
            await asyncio.sleep(random.uniform(0.1, 0.3))
            async with session.get(url, timeout=7, ssl=False, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    if not any(error_sign in content.lower() for error_sign in ['404', 'not found']):
                        logging.info(f"[+] Directory found: {url}")
                        found_directories.append(url)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            if 'Too Many Requests' in str(e):
                await asyncio.sleep(2)
            pass
    with scanned_count.get_lock():
        scanned_count.value += 1
    pbar.update(1)

async def scan_directories(base_url, directories, max_concurrent=50):
    semaphore = asyncio.Semaphore(max_concurrent)
    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False, ttl_dns_cache=300)

    batch_size = 1000
    directory_batches = [directories[i:i + batch_size] for i in range(0, len(directories), batch_size)]
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for batch in directory_batches:
            with tqdm(total=len(batch), desc="Scanning Progress", unit="dir") as pbar:
                tasks = [check_directory(session, base_url, directory, semaphore, pbar) for directory in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(1)

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

def get_next_filename(base_filename):
    if not os.path.exists(base_filename):
        return base_filename
    
    index = 1
    while True:
        new_filename = f"{os.path.splitext(base_filename)[0]}{index}{os.path.splitext(base_filename)[1]}"
        if not os.path.exists(new_filename):
            return new_filename
        index += 1

def save_found_directories(directories):
    base_filename = 'found_directories.txt'
    filename = get_next_filename(base_filename)
    
    try:
        with open(filename, 'w') as f:
            for directory in directories:
                f.write(f"{directory}\n")
        logging.info(f"Found directories saved to '{filename}'.")
    except Exception as e:
        logging.error(f"Error saving found directories: {str(e)}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = input("Masukkan URL website yang ingin di-scan: ")
    directories = read_directories_from_file('dirWebList.txt')
    
    with total_directories.get_lock():
        total_directories.value = len(directories)
    
    num_processes = multiprocessing.cpu_count()
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
        
        save_found_directories(found_directories)

if __name__ == "__main__":
    main()