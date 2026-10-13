"""
Command Line Interface for Long Term Episodic Vector Db.
"""
import argparse
import csv
import json
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger
from episodic_vector_store.store import VectorStore
import os

supervisor = SystemSupervisor(model_provider="mock")


def parse_csv_bool(value):
    """Parse CSV boolean values without treating the string 'False' as true."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in ("", "false", "0", "no", "n"):
        return False
    if normalized in ("true", "1", "yes", "y"):
        return True
    raise ValueError(f"Invalid boolean value: {value!r}")


def parse_embedding(value):
    """Parse a JSON numeric array; VectorStore enforces dimensional validity."""
    data = json.loads(value)
    if not isinstance(data, list):
        raise ValueError("Embedding must be a JSON array, e.g. '[1,0,0]'")
    return data



def main(argv=None):
    parser = argparse.ArgumentParser(prog="long-term-episodic-vector-db", description="Long Term Episodic Vector Db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    # Exact cosine similarity over supplied vectors (no automatic embeddings).
    p_put = subparsers.add_parser("memory-put", help="Insert or replace a vector episode")
    p_put.add_argument("--id", required=True)
    p_put.add_argument("--vector", required=True, help="Embedding as a JSON array")
    p_put.add_argument("--text", default="")
    p_put.add_argument("--metadata", default="{}", help="JSON object")
    p_search = subparsers.add_parser("memory-search", help="Exact cosine search")
    p_search.add_argument("--vector", required=True)
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.add_argument("--min-similarity", type=float, default=-1.0)
    subparsers.add_parser("memory-list", help="List stored episodes")
    p_delete = subparsers.add_parser("memory-delete", help="Delete a stored episode")
    p_delete.add_argument("--id", required=True)
    for p in (p_put, p_search, subparsers.choices["memory-list"], p_delete):
        p.add_argument("--db", default=os.environ.get("EPISODIC_STORE_PATH", "episodes.json"),
                       help="Local JSON storage path (default: episodes.json)")

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  LONG TERM EPISODIC VECTOR DB")
        print(f"  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Long Term Episodic Vector Db Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = list(dict.fromkeys(fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]))
        out_rows = []
        for r in rows:
            payload = SystemTaskPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=float(r.get("primary_metric", 15.0)),
                secondary_metric=float(r.get("secondary_metric", 5.0)),
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=parse_csv_bool(r.get("is_critical_flag", False)),
            )
            dossier = supervisor.process_task(payload)
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command.startswith("memory-"):
        store = VectorStore(args.db)
        if args.command == "memory-put":
            item = store.put(args.id, parse_embedding(args.vector),
                             text=args.text, metadata=json.loads(args.metadata))
            print(json.dumps(item, ensure_ascii=False, indent=2))
        elif args.command == "memory-search":
            matches = store.search(parse_embedding(args.vector),
                                   top_k=args.top_k, min_similarity=args.min_similarity)
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        elif args.command == "memory-list":
            print(json.dumps(store.list_episodes(), ensure_ascii=False, indent=2))
        elif args.command == "memory-delete":
            print(json.dumps({"deleted": store.delete(args.id)}))
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Long Term Episodic Vector Db API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
