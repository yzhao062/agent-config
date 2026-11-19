"""Sum Agy stream-json usage per run: keys of every usage object, summed; count
steps, tool calls, and subagent-looking events. Prints numbers only."""
import json, sys, collections
for path in sys.argv[1:]:
    tot = collections.Counter(); steps = 0; tools = collections.Counter(); status = None; convs = set()
    try:
        lines = open(path, errors="replace").read().splitlines()
    except OSError:
        print(path, "missing"); continue
    for line in lines:
        try: e = json.loads(line)
        except ValueError: continue
        su = e.get("step_update") or {}
        if su.get("conversation_id"): convs.add(su["conversation_id"])
        if su.get("state") == "DONE":
            steps += 1
            for k, v in (su.get("usage") or {}).items():
                if isinstance(v, (int, float)): tot[k] += v
            if su.get("step_type"): tools[su["step_type"]] += 1
        if e.get("event") == "result":
            status = (e.get("result") or {}).get("status")
            for k, v in ((e.get("result") or {}).get("usage") or {}).items():
                if isinstance(v, (int, float)): tot["result_" + k] += v
    name = path.split("/")[-2] if path.endswith("/tail") else path.split("/")[-1]
    print(f"{name[:60]} status={status} steps={steps} convs={len(convs)} usage={dict(tot)} types={dict(tools.most_common(6))}")
