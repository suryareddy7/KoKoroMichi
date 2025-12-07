import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery('kokoromichi_worker', broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def run_arena_match(match_id, guild_id):
    # Simulate a long-running arena match
    import time
    time.sleep(5)  # Replace with real logic
    print(f"Arena match {match_id} for guild {guild_id} completed.")
    return {"match_id": match_id, "guild_id": guild_id, "status": "completed"}

# Example: enqueue with
# run_arena_match.delay('match123', 'guild456')
