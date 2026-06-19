import asyncio
import time
import aiohttp
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.shared import API_SECRET

async def send_single_request(session, url, headers, payload, stats):
    start = time.perf_counter()
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            latency = (time.perf_counter() - start) * 1000  # ms
            status = response.status
            stats["status_codes"][status] = stats["status_codes"].get(status, 0) + 1
            if status == 200:
                stats["success"] += 1
                stats["latencies"].append(latency)
            else:
                stats["failures"] += 1
    except Exception as e:
        stats["failures"] += 1
        stats["errors"].append(str(e))

async def load_test_worker(queue, session, url, headers, payload, stats):
    while True:
        job = await queue.get()
        if job is None:
            queue.task_done()
            break
        await send_single_request(session, url, headers, payload, stats)
        queue.task_done()

async def run_load_test(url, total_requests, concurrency):
    headers = {
        "X-API-Key": API_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "action": "STATUS"
    }

    stats = {
        "success": 0,
        "failures": 0,
        "latencies": [],
        "status_codes": {},
        "errors": []
    }

    print(f"Starting Load Test...")
    print(f"Target URL: {url}")
    print(f"Concurrency Level: {concurrency}")
    print(f"Total Requests: {total_requests}")
    print("--------------------------------------------------")

    # Queue of requests
    queue = asyncio.Queue()
    for _ in range(total_requests):
        await queue.put(True)
    # Put sentinel values to stop workers
    for _ in range(concurrency):
        await queue.put(None)

    start_time = time.perf_counter()

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = []
        for _ in range(concurrency):
            worker = asyncio.create_task(load_test_worker(queue, session, url, headers, payload, stats))
            workers.append(worker)

        await queue.join()
        await asyncio.gather(*workers)

    end_time = time.perf_counter()
    total_time = end_time - start_time

    # Calculate statistics
    latencies = stats["latencies"]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    rps = total_requests / total_time if total_time > 0 else 0

    print("\nLoad Test Results:")
    print(f"Total Time Elapsed: {total_time:.3f} seconds")
    print(f"Throughput: {rps:.2f} requests/second")
    print(f"Successful Requests: {stats['success']}")
    print(f"Failed Requests: {stats['failures']}")
    print(f"Latency Profile:")
    print(f"   - Minimum Latency: {min_latency:.2f} ms")
    print(f"   - Maximum Latency: {max_latency:.2f} ms")
    print(f"   - Average Latency: {avg_latency:.2f} ms")
    print("Status Code Breakdown:")
    for code, count in stats["status_codes"].items():
        print(f"   - HTTP {code}: {count} times")
    if stats["errors"]:
        print(f"Errors encountered ({len(stats['errors'])}):")
        for err in set(stats["errors"][:5]):
            print(f"   - {err}")

    return stats

if __name__ == "__main__":
    url = os.environ.get("TARGET_URL", "http://127.0.0.1:8080/api")
    total_requests = int(os.environ.get("TOTAL_REQUESTS", 100))
    concurrency = int(os.environ.get("CONCURRENCY", 10))
    
    asyncio.run(run_load_test(url, total_requests, concurrency))
