import os
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Connect to Protgres Service
GAMES_LIST = os.getenv('TARGET_GAMES', 'valheim').split(',')
PROXY_URL = os.getenv('THUNDERSTORE_PROXY')
DB_HOST = os.getenv('DB_HOST')
DB_PASS = os.getenv('DB_PASS', 'mysecretpassword')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db(conn):
    cur = conn.cursor()
    # Postgres Syntax: Note the specific types
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mods (
            id TEXT PRIMARY KEY,
            game TEXT,
            name TEXT,
            owner TEXT,
            version TEXT,
            url TEXT,
            downloads BIGINT,
            last_updated TIMESTAMP,
            synced_at TIMESTAMP
        );
        -- Create an index for faster web searches
        CREATE INDEX IF NOT EXISTS idx_game ON mods(game);
    ''')
    conn.commit()

def sync_game(game_id, conn):
    print(f"🎮 Starting Sync for Community: {game_id}")
    
    # 1. Construct the Game-Specific API Endpoint
    # Most Thunderstore communities use: https://[game].thunderstore.io
    url = f"https://{game_id}.thunderstore.io/api/v1/package/"
    headers = {'User-Agent': 'ModCrawler/1.0'}
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        packages = response.json()
        
        print(f"   ✅ Fetched {len(packages)} mods. Writing to DB...")
        
        timestamp = datetime.utcnow()
        values = [
            (
                pkg['uuid4'],
                game_id,
                pkg['name'],
                pkg['owner'],
                pkg['versions'][0]['version_number'], 
                pkg['package_url'],
                sum(v['downloads'] for v in pkg['versions']), 
                pkg['date_updated'],
                timestamp
            )
            for pkg in packages
        ]
        
        query = """
            INSERT INTO mods (id, game, name, owner, version, url, downloads, last_updated, synced_at)
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                version = EXCLUDED.version,
                downloads = EXCLUDED.downloads,
                last_updated = EXCLUDED.last_updated,
                synced_at = EXCLUDED.synced_at;
        """
        
        # The cursor is managed automatically here too
        with conn.cursor() as cursor:
            execute_values(cursor, query, values)
        
        conn.commit()
        print(f"   💾 Saved {game_id} to database.")

    except Exception as e:
        print(f"   ❌ Failed to sync {game_id}: {e}")
        conn.rollback() # Roll back the transaction if the upsert fails so the connection remains usable

def main():
    print("🚀 Mod Syncer Started")
    time.sleep(5)
    
    try:
        # Open a single connection for the entire lifecycle of the script
        with get_db_connection() as conn:
            init_db(conn)
            
            for game in GAMES_LIST:
                game = game.strip()
                if game:
                    sync_game(game, conn)
                    time.sleep(2) 
                    
    except Exception as e:
        print(f"🔥 Fatal DB Error: {e}")
        return
            
    print("💤 Sync Complete. Sleeping.")

if __name__ == "__main__":
    main()
