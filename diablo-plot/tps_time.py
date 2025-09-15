import json, sys, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_result(path):
    with open(path, "r") as f: return json.load(f)

def committed_commits(res):
    ts = []
    for loc in res.get("Locations", []):
        for cli in loc.get("Clients", []):
            for ia in cli.get("Interactions", []):
                st = ia.get("SubmitTime", -1)
                ct = ia.get("CommitTime", -1)
                ab = ia.get("AbortTime", -1)
                err = ia.get("HasError", False)
                if st >= 0 and ct >= 0 and ab < 0 and not err and ct >= st:
                    ts.append(ct)
    return np.array(ts)

def per_second_tps(commit_times, bin_size=1.0):
    if commit_times.size == 0: 
        return pd.DataFrame(columns=["time_s","tps"])
    end = commit_times.max()
    if end <= 0: 
        return pd.DataFrame({"time_s":[0.0], "tps":[0.0]})
    bins = np.arange(0, end + bin_size, bin_size)
    counts, edges = np.histogram(commit_times, bins=bins)
    return pd.DataFrame({"time_s": edges[:-1], "tps": counts / bin_size})

def plot_tps(df_tps, out_path="throughput_vs_time.png", bin_size=1.0, smooth_window_s=5):
    sns.set_context("talk")
    fig, ax = plt.subplots(figsize=(10,4))
    sns.lineplot(data=df_tps, x="time_s", y="tps", ax=ax, label="TPS")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Throughput (tx/s)")
    ax.grid(True)
    plt.title(f"TPS against time (window = {bin_size})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")

if __name__ == "__main__":
    # Get the input file path from command-line arguments or use a default
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("result.json")
    output_path = input_path.with_stem(f"{input_path.stem}-time").with_suffix(".png")

    bin_size = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    res = load_result(input_path)
    commits = committed_commits(res)
    df_tps = per_second_tps(commits, bin_size=bin_size)
    plot_tps(df_tps, out_path=output_path, bin_size=bin_size)