"""Full backfill: ingest ALL wiki pages into Neo4j with full quality.
No LLM API calls — uses deterministic pipeline for labels, dates, types,
relationships, and cross-references. Then runs temporal causality chains."""
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

from src.knowledge_graph.connection import neo4j_conn
from src.knowledge_graph.ingest import ingest_wiki_page
from src.wiki.writer import read_page, cross_reference_new_page, append_to_index, append_to_log, invalidate_index_cache
from src.cache import cache_store, cache_decorator

WIKI_DIR = os.path.join(os.path.dirname(__file__), "..", "wiki")
WIKI_SUBDIRS = ["entities", "concepts", "projects"]

def main():
    neo4j_conn.connect()
    driver = neo4j_conn.get_driver()
    if not driver:
        print("ERROR: Could not connect to Neo4j")
        sys.exit(1)

    # Clear any stale reconciliation gate so we don't conflict
    try:
        from src.reconciliation_gate import clear_stale_gate
        clear_stale_gate()
    except Exception:
        pass

    all_pages = []
    for subdir in WIKI_SUBDIRS:
        dir_path = os.path.join(WIKI_DIR, subdir)
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            if fname.endswith(".md"):
                all_pages.append((os.path.splitext(fname)[0], subdir))

    total = len(all_pages)
    print(f"\nIngesting {total} wiki pages into Neo4j with full quality pipeline...")
    print(f"  ✓ Labels inferred deterministically (Person/Event/Project/etc)")
    print(f"  ✓ Event dates extracted from body text")
    print(f"  ✓ Event types inferred from tags")
    print(f"  ✓ Relationships from wiki links + frontmatter")
    print(f"  ✓ Cross-references updated")
    print(f"  ✓ Index + log updated\n")

    errors = 0
    for idx, (slug, subdir) in enumerate(all_pages):
        try:
            page_data = read_page(slug, page_type=subdir)
            if not page_data or "frontmatter" not in page_data:
                print(f"  SKIP [{idx+1}/{total}] {slug} — cannot read")
                continue

            title = page_data["frontmatter"].get("title", slug)
            tags = page_data["frontmatter"].get("tags", [])
            sources = page_data["frontmatter"].get("sources", [])
            related = page_data["frontmatter"].get("related", [])
            body = page_data.get("body", "")
            full_content = f"---\ntitle: {title}\ntags: {tags}\nsources: {sources}\nrelated: {related}\n---\n\n{body}"

            cross_reference_new_page(slug, title, subdir)
            ingest_wiki_page(driver, title=title, content=full_content, default_tags=tags, default_sources=sources)
            append_to_index([(slug, title, subdir)])
            append_to_log(f"Full backfill: {slug} ({subdir})")

            if (idx + 1) % 50 == 0:
                print(f"  [{idx+1}/{total}] {slug} — {errors} errors")
        except Exception as e:
            print(f"  ERROR [{idx+1}/{total}] {slug}: {e}")
            errors += 1

    invalidate_index_cache()

    print(f"\n=== BACKFILL COMPLETE ===")
    print(f"  {total} pages ingested, {errors} errors")

    # Build temporal causality chains between Event nodes
    print(f"\nBuilding temporal causality chains...")
    try:
        from src.knowledge_graph.temporal_causality import build_temporal_causality_chains
        result = build_temporal_causality_chains(driver)
        print(f"  PRECEDED_BY: {result['preceded_by']}, CAUSED: {result['caused']}")
    except Exception as e:
        print(f"  Error: {e}")

    # Verify data quality
    print(f"\n=== DATA QUALITY VERIFICATION ===")
    with driver.session() as session:
        n = session.run('MATCH (n:Entity) RETURN count(n) AS c').single()['c']
        r = session.run('MATCH ()-[x]->() RETURN count(x) AS c').single()['c']
        e = session.run('MATCH (e:Event) RETURN count(e) AS c').single()['c']
        ed = session.run('MATCH (e:Event) WHERE e.date IS NOT NULL RETURN count(e) AS c').single()['c']
        bad = session.run('MATCH (n:Entity) WHERE n.date IS NOT NULL AND NOT n:Event RETURN count(n) AS c').single()['c']
        pb = session.run('MATCH ()-[x:PRECEDED_BY]->() RETURN count(x) AS c').single()['c']
        print(f"  Nodes: {n}")
        print(f"  Relationships: {r}")
        print(f"  Events: {e} total, {ed} with dates")
        print(f"  Non-Event nodes with dates: {bad} (should be 0)")
        print(f"  PRECEDED_BY chains: {pb}")

        if ed == e and bad == 0:
            print(f"\n✅ ALL DATA QUALITY CHECKS PASSED")
        else:
            print(f"\n⚠️  Some checks need attention")

    neo4j_conn.close()
    print(f"\nReady to restart server.")

if __name__ == "__main__":
    main()
