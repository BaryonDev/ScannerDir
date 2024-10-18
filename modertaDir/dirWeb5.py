import asyncio
import aiohttp
from urllib.parse import urljoin
import signal
import sys
import time
import logging
import multiprocessing
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = multiprocessing.Manager().list()
interrupt_event = multiprocessing.Event()

def read_directories_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"File {filename} tidak ditemukan.")
        return []

def split_list(lst, n):
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


async def check_directory(session, base_url, directory):
    if interrupt_event.is_set():
        raise asyncio.CancelledError()
    url = urljoin(base_url, directory)
    try:
        async with session.get(url, timeout=10, ssl=False) as response:
            if response.status == 200:
                logging.info(f"[+] Directory found: {url}")
                return url
    except Exception:
        # Mengabaikan error tanpa mencetaknya
        pass
    return None
# async def check_directory(session, base_url, directory):
#     if interrupt_event.is_set():
#         raise asyncio.CancelledError()
#     url = urljoin(base_url, directory)
#     try:
#         async with session.get(url, timeout=10, ssl=False) as response:
#             if response.status == 200:
#                 logging.info(f"[+] Directory found: {url}")
#                 return url
#     except Exception as e:
#         logging.error(f"Error checking {url}: {str(e)}")
#     return None

async def scan_directories(base_url, directories, max_concurrent=50):
    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_directory(session, base_url, directory) for directory in directories]
        
        chunk_size = 1000
        for i in range(0, len(tasks), chunk_size):
            if interrupt_event.is_set():
                break
            chunk = tasks[i:i+chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for result in results:
                if isinstance(result, str):  # Valid URL found
                    found_directories.append(result)
            
            logging.info(f"Completed chunk {i//chunk_size + 1}/{len(tasks)//chunk_size + 1}")
            await asyncio.sleep(1)  # Small delay between chunks to avoid overwhelming the server

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

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = input("Masukkan URL website yang ingin di-scan: ")
    directories = read_directories_from_file('claudeGens.txt')
    
    num_processes = 4
    split_directories = split_list(directories, num_processes)
    
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
        logging.info("\nHasil scan:")
        for dir in found_directories:
            logging.info(dir)
        
        logging.info(f"\nTotal direktori ditemukan: {len(found_directories)}")
        
        with open('found_directories.txt', 'w') as f:
            for directory in found_directories:
                f.write(f"{directory}\n")
        
        logging.info("Found directories saved to 'found_directories.txt'.")

if __name__ == "__main__":
    main()