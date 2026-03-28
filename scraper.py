# -*- coding: utf-8 -*-
import requests
import sqlite3
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

DB_PATH = "whisky_auctions.db"
DELAY   = 1.2

def fetch_lot(lot_id, auction_slug):
    url = f"https://www.scotchwhiskyauctions.com/auctions/{auction_slug}/{lot_id}/"
    try:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=10)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        pass
    return None

def parse_lot(soup, lot_id):
    result = {
        "lot_id": lot_id, "title": None, "lot_number": None,
        "winning_bid": None, "distilled_date": None, "bottled_date": None,
        "age_years": None, "cask_type": None, "cask_number": None,
        "abv": None, "volume_cl": None, "bottle_number": None,
        "total_bottles": None,
    }

    h1 = soup.find("h1")
    result["title"] = h1.text.strip() if h1 else None

    lines = [l.strip() for l in 
             soup.get_text(separator="\n").split("\n") if l.strip()]

    for line in lines:
        if line.startswith("Lot number:"):
            result["lot_number"] = line.replace("Lot number:", "").strip()
        elif line.startswith("Winning bid:"):
            raw = line.replace("Winning bid:", "").replace(",", "").strip()
            raw = "".join(c for c in raw if c.isdigit() or c == ".")
            try:
                result["winning_bid"] = float(raw)
            except ValueError:
                pass
        elif line.startswith("Distilled:"):
            result["distilled_date"] = line.replace("Distilled:", "").strip()
        elif line.startswith("Bottled:"):
            result["bottled_date"] = line.replace("Bottled:", "").strip()
        elif line.startswith("Age:"):
            m = re.search(r"(\d+\.?\d*)", line)
            result["age_years"] = float(m.group(1)) if m else None
        elif line.startswith("Cask Type:"):
            result["cask_type"] = line.replace("Cask Type:", "").strip()
        elif line.startswith("Cask Number:"):
            result["cask_number"] = line.replace("Cask Number:", "").strip()
        elif "% ABV" in line and "/" in line:
            abv = re.search(r"(\d+\.?\d*)%\s*ABV", line)
            vol = re.search(r"/\s*(\d+)cl", line)
            result["abv"]       = float(abv.group(1)) if abv else None
            result["volume_cl"] = int(vol.group(1))   if vol else None
        elif line.startswith("Bottle Number:"):
            parts = line.replace("Bottle Number:", "").strip().split("/")
            if len(parts) == 2:
                try:
                    result["bottle_number"] = int(parts[0].strip())
                    result["total_bottles"] = int(parts[1].strip())
                except ValueError:
                    pass
    return result

def get_or_create(cursor, table, col, val):
    cursor.execute(f"SELECT id FROM {table} WHERE {col} = ?", (val,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(f"INSERT INTO {table} ({col}) VALUES (?)", (val,))
    return cursor.lastrowid

def insert_lot(cursor, lot, auction_id):
    cask_type_id = None
    if lot["cask_type"]:
        cask_type_id = get_or_create(cursor, "cask_types", "name", lot["cask_type"])
    cursor.execute("""
        INSERT OR IGNORE INTO lots (
            lot_id, lot_number, auction_id, cask_type_id,
            title, winning_bid, distilled_date, bottled_date,
            age_years, abv, volume_cl, bottle_number,
            total_bottles, cask_number
        ) VALUES (
            :lot_id, :lot_number, :auction_id, :cask_type_id,
            :title, :winning_bid, :distilled_date, :bottled_date,
            :age_years, :abv, :volume_cl, :bottle_number,
            :total_bottles, :cask_number
        )
    """, {**lot, "auction_id": auction_id, "cask_type_id": cask_type_id})

def run():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, auction_number, url FROM auctions
        ORDER BY auction_number DESC
    """)
    auction_rows = cursor.fetchall()

    auction_registry = {
        177: (862100, 867182, "226-the-177th-auction"),
        176: (857584, 861947, "225-the-176th-auction"),
        175: (847191, 857052, "224-the-175th-auction"),
        174: (847301, 853007, "223-the-174th-auction"),
        173: (841368, 846899, "222-the-173rd-auction"),
        172: (830552, 840988, "221-the-172nd-auction"),
        171: (825559, 835241, "220-the-171st-auction"),
        170: (825472, 829675, "219-the-170th-auction"),
        169: (815056, 823171, "218-the-169th-auction"),
        168: (814886, 819058, "217-the-168th-auction"),
        167: (809685, 814858, "216-the-167th-auction"),
        166: (803706, 809705, "215-the-166th-auction"),
        165: (798540, 803511, "214-the-165th-auction"),
        164: (790441, 798341, "213-the-164th-auction"),
        163: (790354, 794375, "212-the-163rd-auction"),
        162: (783059, 789395, "210-the-162nd-auction"),
        161: (775956, 782840, "209-the-161st-auction"),
        160: (766795, 775801, "208-the-160th-auction"),
        159: (762179, 768111, "207-the-159th-auction"),
        158: (756745, 761774, "206-the-158th-auction"),
        157: (751345, 754921, "205-the-157th-auction"),
        156: (746236, 750997, "204-the-156th-auction"),
        155: (740882, 745356, "203-the-155th-auction"),
        154: (732706, 739892, "202-the-154th-auction"),
    }

    total_scraped = 0
    total_skipped = 0
    total_failed  = 0

    for auction_db_id, auction_number, url in auction_rows:
        if auction_number not in auction_registry:
            continue

        id_start, id_end, slug = auction_registry[auction_number]

        print(f"\n[{datetime.now():%H:%M:%S}] "
              f"Auction {auction_number} ({slug})")
        print(f"  ID range: {id_start:,} to {id_end:,} "
              f"({id_end - id_start:,} IDs)")

        scraped = skipped = failed = 0

        for lot_id in range(id_start, id_end + 1):
            try:
                cursor.execute(
                    "SELECT id FROM lots WHERE lot_id = ?", (lot_id,)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue

                soup = fetch_lot(lot_id, slug)
                time.sleep(DELAY)

                if not soup or "Winning bid" not in soup.get_text():
                    failed += 1
                    continue

                lot = parse_lot(soup, lot_id)
                insert_lot(cursor, lot, auction_db_id)
                conn.commit()
                scraped += 1

                if scraped % 100 == 0:
                    print(f"  [{datetime.now():%H:%M:%S}] "
                          f"scraped={scraped:,} "
                          f"skipped={skipped:,} "
                          f"failed={failed:,} "
                          f"lot={lot_id:,}")

            except KeyboardInterrupt:
                print("\nInterrupted � progress saved.")
                conn.close()
                return
            except Exception as e:
                failed += 1
                continue

        total_scraped += scraped
        total_skipped += skipped
        total_failed  += failed

        print(f"  Done: scraped={scraped:,} "
              f"skipped={skipped:,} failed={failed:,}")

    print(f"\nAll auctions complete.")
    print(f"Total: scraped={total_scraped:,} "
          f"skipped={total_skipped:,} failed={total_failed:,}")
    conn.close()

if __name__ == "__main__":
    run()
