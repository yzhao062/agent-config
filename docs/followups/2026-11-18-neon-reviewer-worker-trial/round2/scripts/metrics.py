import json, sqlite3, sys, pathlib
R = pathlib.Path(sys.argv[1]); C = pathlib.Path(sys.argv[2]).expanduser()
rows = {}
for line in (R / "summary.txt").read_text().splitlines():
    parts = dict(p.split("=", 1) for p in line.split()[1:]); name = line.split()[0]
    usage = {}
    for l in (R / f"{name}.err").read_text(errors="replace").splitlines():
        try: e = json.loads(l)
        except ValueError: continue
        if e.get("event") == "result": usage = (e.get("result") or {}).get("usage") or {}
    db = C / f"{parts['conversation']}.db"
    con = sqlite3.connect(db); calls = con.execute("select count(*) from gen_metadata").fetchone()[0]; con.close()
    rows[name] = (int(parts["wall_s"]), usage.get("input_tokens", 0) + usage.get("output_tokens", 0), usage.get("cache_read_tokens", 0), calls)
print("# Round 2 raw measurements, 2026-11-18, all twelve reviews launched together at 21:44 local.")
print("# name wall_s input+output_tokens cache_read_tokens model_calls")
for n in sorted(rows): print(n, *rows[n])
for arm in ("carbon", "neon"):
    sel = [v for k, v in rows.items() if k.endswith(arm)]
    print(f"# total {arm}: wall_s={sum(v[0] for v in sel)} io={sum(v[1] for v in sel)} cache={sum(v[2] for v in sel)} calls={sum(v[3] for v in sel)}")
