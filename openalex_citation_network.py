"""
openalex_citation_network.py
--------------------------------
Fetch a citation network from OpenAlex for climate-related concepts and
write two CSV files: nodes.csv and edges.csv.

Usage (basic):
    python openalex_citation_network.py --concept "climate change" --n 200 --mailto "you@example.com"

Notes:
  - By default, edges are from a work -> its referenced works (citations).
  - We enrich nodes for the seed set and (optionally) the referenced works.
"""
import argparse
import csv
import sys
import time
import requests
from urllib.parse import urlencode

OPENALEX_BASE = "https://api.openalex.org"
WORKS_ENDPOINT = f"{OPENALEX_BASE}/works"
CONCEPTS_ENDPOINT = f"{OPENALEX_BASE}/concepts"

def lookup_concept_id(term, mailto=None):
    params = {"search": term}
    if mailto:
        params["mailto"] = mailto
    r = requests.get(CONCEPTS_ENDPOINT, params=params, timeout=40)
    r.raise_for_status()
    js = r.json()
    results = js.get("results", [])
    if not results:
        raise ValueError(f"No concept results for: {term}")
    # Pick the highest ranked
    best = results[0]
    return best["id"].split("/")[-1], best["display_name"]

def fetch_works_for_concept(concept_id, n=200, mailto=None, per_page=200):
    params = {
        "filter": f"concepts.id:{concept_id}",
        "per_page": min(per_page, 200),
        "sort": "cited_by_count:desc",
    }
    if mailto:
        params["mailto"] = mailto
    works = []
    url = WORKS_ENDPOINT + "?" + urlencode(params)
    while len(works) < n and url:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        js = r.json()
        works.extend(js.get("results", []))
        url = js.get("meta", {}).get("next_page")
        time.sleep(0.5)  # polite
    return works[:n]

def to_node_row(w):
    return [
        w.get("id",""),
        w.get("display_name",""),
        (w.get("doi","") or ""),
        (w.get("publication_year","") or ""),
        (w.get("host_venue",{}).get("display_name","") or ""),
        # (w.get("authorships",[{}])[0].get("institutions",[{}])[0].get("display_name","") or ""),
        (w.get("cited_by_count",0) or 0)
    ]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept", default="climate change",
                    help="Concept term to search (e.g., 'climate change', 'atmospheric science')")
    ap.add_argument("--n", type=int, default=200, help="Number of seed works to fetch")
    ap.add_argument("--mailto", default=None, help="Your email for OpenAlex polite usage")
    ap.add_argument("--expand-refs", action="store_true",
                    help="Also fetch metadata for referenced works to enrich nodes")
    ap.add_argument("--out-nodes", default="nodes.csv")
    ap.add_argument("--out-edges", default="edges.csv")
    args = ap.parse_args()

    try:
        concept_id, concept_name = lookup_concept_id(args.concept, args.mailto)
    except Exception as e:
        print(f"Failed to find concept '{args.concept}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Using concept: {concept_name} (ID: {concept_id})")

    works = fetch_works_for_concept(concept_id, n=args.n, mailto=args.mailto)
    print(f"Fetched {len(works)} works")

    # Build node and edge sets
    node_map = {}
    edges = []

    for w in works:
        wid = w.get("id","")
        node_map[wid] = w
        for tgt in (w.get("referenced_works") or []):
            edges.append([wid, tgt])
            if args.expand_refs and tgt not in node_map:
                # Attempt to fetch minimal metadata for referenced work
                params = {}
                if args.mailto:
                    params["mailto"] = args.mailto
                rw = requests.get(tgt, params=params, timeout=30)
                if rw.status_code == 200:
                    node_map[tgt] = rw.json()
                else:
                    node_map.setdefault(tgt, {"id": tgt, "display_name": "", "doi": "", "publication_year": ""})
                time.sleep(0.25)

    # Write CSVs
    with open(args.out_nodes, "w", newline="", encoding="utf-8") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["id","title","doi","year","venue","lead_institution","cited_by_count"])
        for wid, meta in node_map.items():
            wcsv.writerow(to_node_row(meta))

    with open(args.out_edges, "w", newline="", encoding="utf-8") as f:
        ecsv = csv.writer(f)
        ecsv.writerow(["source","target"])
        for s, t in edges:
            ecsv.writerow([s, t])

    print(f"Wrote {args.out_nodes} and {args.out_edges}")

if __name__ == "__main__":
    main()
