"""
NYC GeoSupport Geocoder Function
"""
import aiohttp
import asyncio
import pandas as pd
import os
from datetime import datetime
from pathlib import Path


# ── Config ─────────────────────────────────────────────────────────────────────

GEOSEARCH_URL       = "https://geosearch.planninglabs.nyc/v2/search"
CONCURRENCY         = 10
CHECKPOINT_N        = 500

REPO_ROOT = Path(__file__).resolve().parent.parent  # src/ → repo root
DATA_DIR  = REPO_ROOT / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VIOLATION_CHECKPOINT  = str(DATA_DIR / "violation_geocoded.csv")
RESPONDENT_CHECKPOINT = str(DATA_DIR / "respondent_geocoded.csv")

# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_geosearch_response(data, original_address):
    empty = {
        "input_address": original_address,
        "label":         None,
        "housenumber":   None,
        "street":        None,
        "borough":       None,
        "neighbourhood": None,
        "locality":      None,
        "postalcode":    None,
        "region_a":      None,
        "match_type":    None,
        "accuracy":      None,
        "confidence":    None,
        "lat":           None,
        "lon":           None,
        "bbl":           None,
        "bin":           None,
        "source":        None,
        "layer":         None,
    }

    try:
        features = data.get("features", [])
        if not features:
            return empty

        top    = features[0]
        props  = top.get("properties", {})
        coords = top.get("geometry", {}).get("coordinates", [None, None])
        pad    = props.get("addendum", {}).get("pad", {})

        return {
            "input_address": original_address,
            "label":         props.get("label"),
            "housenumber":   props.get("housenumber"),
            "street":        props.get("street"),
            "borough":       props.get("borough"),
            "neighbourhood": props.get("neighbourhood"),
            "locality":      props.get("locality"),
            "postalcode":    props.get("postalcode"),
            "region_a":      props.get("region_a"),
            "match_type":    props.get("match_type"),
            "accuracy":      props.get("accuracy"),
            "confidence":    props.get("confidence"),
            "lat":           coords[1],
            "lon":           coords[0],
            "bbl":           pad.get("bbl"),
            "bin":           pad.get("bin"),
            "source":        props.get("source"),
            "layer":         props.get("layer"),
        }

    except Exception:
        return empty

# ── Single request ─────────────────────────────────────────────────────────────

async def geocode_one(session, semaphore, address):
    if not address:
        return parse_geosearch_response({}, address)

    params = {"text": address, "size": 1}

    async with semaphore:
        for attempt in range(3):
            try:
                async with session.get(
                    GEOSEARCH_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return parse_geosearch_response(data, address)
                    elif resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(2 ** attempt)

    return parse_geosearch_response({}, address)

# ── Checkpoint helpers ─────────────────────────────────────────────────────────

def load_checkpoint(path):
    if not os.path.exists(path):
        return set(), []
    df = pd.read_csv(path)
    done = set(df["input_address"].dropna().tolist())
    return done, df.to_dict("records")

def save_checkpoint(records, path):
    pd.DataFrame(records).to_csv(path, index=False)

# ── Main pipeline ──────────────────────────────────────────────────────────────

async def geocode_addresses(addresses, checkpoint_path):
    done_set, results = load_checkpoint(checkpoint_path)
    remaining = [a for a in addresses if a not in done_set]

    print(f"Total:       {len(addresses)}")
    print(f"Already done:{len(done_set)}")
    print(f"Remaining:   {len(remaining)}")

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        tasks = [geocode_one(session, semaphore, addr) for addr in remaining]

        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            results.append(result)

            if (i + 1) % CHECKPOINT_N == 0:
                save_checkpoint(results, checkpoint_path)
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Checkpointed {i + 1}/{len(remaining)}")

    save_checkpoint(results, checkpoint_path)
    print(f"Done — {len(results)} total records saved to {checkpoint_path}")
    return pd.DataFrame(results)