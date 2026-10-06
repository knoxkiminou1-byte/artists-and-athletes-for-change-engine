"""AAFC integration CLI. Run: python -m aafc_engine.integrations list"""
import json
import sys
from .runtime import load_catalog

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    catalog = load_catalog()
    if not args or args[0] == "list":
        system = args[1] if len(args) > 1 else None
        rows = [row for row in catalog if not system or system in row["systems"]]
        for row in rows:
            print(f"{row['n']:03d}  {row['status']:16}  {row['name']}  {row['url']}")
        print(f"{len(rows)} MIT integrations")
        return 0
    if args[0] == "json":
        print(json.dumps(catalog))
        return 0
    print("usage: python -m aafc_engine.integrations list [system]", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
