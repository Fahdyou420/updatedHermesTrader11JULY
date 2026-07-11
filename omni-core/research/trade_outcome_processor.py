import json, os, re, glob
from datetime import datetime
from collections import Counter

MT5_COMMON = r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
RESEARCH_DIR = r"C:\Users\user\Desktop\hermes_claude\omni-core\research"
os.makedirs(RESEARCH_DIR, exist_ok=True)

RESULTS_PATH = os.path.join(RESEARCH_DIR, "rd_results.jsonl")


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def extract_strategy_tag(text):
    m = re.search(r"Agent\s+(\d+)\s+\(([^)]+)\)", str(text))
    if m:
        return f"agent{m.group(1)}_{m.group(2)}"
    m = re.search(r"strategy[:_]?\s*([A-Za-z0-9_]+)", str(text), re.I)
    if m:
        return m.group(1)
    return "unknown"


def process_outcomes(limit=200):
    outcomes = sorted(glob.glob(os.path.join(MT5_COMMON, "Trade_Outcome_*.json")))[-limit:]
    tag_pnl = Counter()
    tag_consec = Counter()
    findings = []
    last_loss_tag = None
    streak = 0

    for path in outcomes:
        data = read_json(path)
        pnl = data.get("PnL") or data.get("pnl") or 0.0
        try:
            pnl = float(pnl)
        except Exception:
            pnl = 0.0
        reasoning = data.get("Reasoning") or data.get("reasoning") or data.get("comment") or data.get("bus_message") or data.get("signal") or ""
        tag = extract_strategy_tag(reasoning)
        tag_pnl[tag] += pnl

        if pnl < 0:
            if last_loss_tag == tag:
                streak += 1
            else:
                streak = 1
            last_loss_tag = tag
            tag_consec[tag] = max(tag_consec[tag], streak)
        else:
            last_loss_tag = None
            streak = 0

        findings.append({"path": os.path.basename(path), "tag": tag, "pnl": pnl, "streak": streak if pnl < 0 else 0})

    summary = {
        "processed": len(outcomes),
        "tag_pnl": dict(tag_pnl),
        "tag_consecutive_losses": dict(tag_consec),
        "worst_tags": sorted(tag_pnl.items(), key=lambda x: x[1])[:5],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    with open(RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    process_outcomes()
