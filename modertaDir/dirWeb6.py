import asyncio
import aiohttp
from urllib.parse import urljoin
import signal
import sys
import time
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

found_directories = []
total_directories = 0
scanned_count = 0
start_time = time.time()

async def check_directory(session, base_url, directory):
    url = urljoin(base_url, directory)
    try:
        async with session.get(url, timeout=10, ssl=False) as response:
            if response.status == 200:
                logging.info(f"[+] Directory found: {url}")
                return url
    except Exception as e:
        logging.error(f"Error checking {url}: {str(e)}")
    return None

async def update_progress():
    global scanned_count, total_directories, start_time
    while scanned_count < total_directories:
        percentage = (scanned_count / total_directories) * 100
        elapsed_time = time.time() - start_time
        speed = scanned_count / elapsed_time if elapsed_time > 0 else 0
        print(f"\rDir scanned {scanned_count}/{total_directories} at {percentage:.1f}% (Speed: {speed:.2f} dirs/sec)", end='')
        await asyncio.sleep(1)

async def scan_directories(base_url, directories, max_concurrent=50):
    global scanned_count, found_directories
    
    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_directory(session, base_url, directory) for directory in directories]
        
        progress_task = asyncio.create_task(update_progress())
        
        chunk_size = 1000
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i+chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for result in results:
                if isinstance(result, str):  # Valid URL found
                    found_directories.append(result)
                scanned_count += 1
            
            logging.info(f"Completed chunk {i//chunk_size + 1}/{len(tasks)//chunk_size + 1}")
            await asyncio.sleep(1)  # Small delay between chunks to avoid overwhelming the server
        
        await progress_task

def read_directories_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"File {filename} tidak ditemukan.")
        return []

def signal_handler(sig, frame):
    logging.info("\nScanning interrupted.")
    logging.info(f"Total directories scanned: {scanned_count}")
    logging.info(f"Directories found: {len(found_directories)}")
    
    with open('found_directories.txt', 'w') as f:
        for directory in found_directories:
            f.write(f"{directory}\n")
    
    logging.info("Found directories saved to 'found_directories.txt'.")
    sys.exit(0)

async def main():
    global total_directories
    
    signal.signal(signal.SIGINT, signal_handler)
    
    base_url = input("Masukkan URL website yang ingin di-scan: ")
    directories = read_directories_from_file('adminDir.txt')
    total_directories = len(directories)
    
    logging.info(f"Scanning direktori pada {base_url}...")
    await scan_directories(base_url, directories)
    
    logging.info("\nHasil scan:")
    for dir in found_directories:
        logging.info(dir)
    
    logging.info(f"\nTotal direktori ditemukan: {len(found_directories)}")
    
    with open('found_directories.txt', 'w') as f:
        for directory in found_directories:
            f.write(f"{directory}\n")
    
    logging.info("Found directories saved to 'found_directories.txt'.")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())