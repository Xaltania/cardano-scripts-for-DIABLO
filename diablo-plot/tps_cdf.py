import json, sys
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

def load_latencies(path):
    with open(path, "r") as f:
        res = json.load(f)
    L = []
    for loc in res.get("Locations", []):
        for client in loc.get("Clients", []):
            for ia in client.get("Interactions", []):
                st = ia.get("SubmitTime", -1)
                ct = ia.get("CommitTime", -1)
                ab = ia.get("AbortTime", -1)
                err = ia.get("HasError", False)
                if st >= 0 and ct >= 0 and ab < 0 and not err and ct >= st:
                    L.append(ct - st)
    return np.array(L)

if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("result.json")
    output_path = input_path.with_stem(f"{input_path.stem}-ecdf").with_suffix(".png")

    latencies = load_latencies(input_path)
    sns.set_context("talk")
    plt.figure(figsize=(7,4))
    sns.ecdfplot(latencies)
    plt.xlabel("Latency (s)")
    plt.ylabel("Proportion")
    plt.title("eCDF of Transaction Latencies")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    print(f"wrote {output_path}")