"""generate_plots.py - Generate clean, informative performance & quality graphs.

Phase 3 Visualization:
1. PSNR vs. Payload Utilization % across resolutions
2. MSE vs. Payload Size across security modes
3. SSIM vs. Payload Size
4. Execution Time (Encode vs. Decode) comparison
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt

RESULTS_PATH = Path("output") / "experiments" / "experiment_results.json"
PLOTS_DIR = Path("output") / "experiments" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)


def generate_all_plots():
    data = load_results()

    # Style configuration
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8

    # 1. Plot: PSNR vs Payload Utilization %
    fig, ax = plt.subplots(figsize=(8, 5))
    for res, color, marker in [("250x250", "#1f77b4", "o"), ("500x500", "#ff7f0e", "s")]:
        subset = [d for d in data if d["resolution"] == res and d["mode"] == "Plain LSB"]
        util = [d["utilization_pct"] for d in subset]
        psnr = [d["psnr_db"] for d in subset]
        ax.plot(util, psnr, marker=marker, color=color, linewidth=2, markersize=8, label=f"Cover {res} (Plain LSB)")

    ax.set_title("Peak Signal-to-Noise Ratio (PSNR) vs. Payload Utilization", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Payload Utilization (% of Stego Capacity)", fontsize=11)
    ax.set_ylabel("PSNR (dB)", fontsize=11)
    ax.axhline(50, color="#d62728", linestyle="--", alpha=0.7, label="Imperceptibility Threshold (50 dB)")
    ax.set_ylim(45, 80)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ddd")
    plt.tight_layout()
    plot1_path = PLOTS_DIR / "psnr_vs_utilization.png"
    plt.savefig(plot1_path, dpi=300)
    plt.close()

    # 2. Plot: MSE vs Payload Size across Modes
    fig, ax = plt.subplots(figsize=(8, 5))
    subset_250 = [d for d in data if d["resolution"] == "250x250"]
    modes = ["Plain LSB", "zlib + AES-GCM"]
    colors = {"Plain LSB": "#2ca02c", "zlib + AES-GCM": "#9467bd"}
    markers = {"Plain LSB": "^", "zlib + AES-GCM": "D"}

    for mode in modes:
        mode_data = [d for d in subset_250 if d["mode"] == mode]
        sizes = [d["payload_size_bytes"] / 1024 for d in mode_data]
        mse = [d["mse"] for d in mode_data]
        ax.plot(sizes, mse, marker=markers[mode], color=colors[mode], linewidth=2, markersize=8, label=mode)

    ax.set_title("Mean Squared Error (MSE) vs. Payload Size (Cover: 250x250)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Original Payload Size (KB)", fontsize=11)
    ax.set_ylabel("Mean Squared Error (MSE)", fontsize=11)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ddd")
    plt.tight_layout()
    plot2_path = PLOTS_DIR / "mse_vs_payload_size.png"
    plt.savefig(plot2_path, dpi=300)
    plt.close()

    # 3. Plot: SSIM vs Payload Size
    fig, ax = plt.subplots(figsize=(8, 5))
    for res, color, marker in [("250x250", "#17becf", "o"), ("500x500", "#e377c2", "X")]:
        subset = [d for d in data if d["resolution"] == res and d["mode"] == "Plain LSB"]
        sizes = [d["payload_size_bytes"] / 1024 for d in subset]
        ssim = [d["ssim"] for d in subset]
        ax.plot(sizes, ssim, marker=marker, color=color, linewidth=2, markersize=8, label=f"{res}")

    ax.set_title("Structural Similarity Index (SSIM) vs. Payload Size", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Payload Size (KB)", fontsize=11)
    ax.set_ylabel("SSIM", fontsize=11)
    ax.set_ylim(0.992, 1.0005)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ddd")
    plt.tight_layout()
    plot3_path = PLOTS_DIR / "ssim_vs_payload_size.png"
    plt.savefig(plot3_path, dpi=300)
    plt.close()

    # 4. Plot: Execution Time Comparison (Encode vs Decode)
    fig, ax = plt.subplots(figsize=(9, 5))
    plain_subset = [d for d in data if d["mode"] == "Plain LSB"]
    secure_subset = [d for d in data if d["mode"] == "zlib + AES-GCM"]

    labels = [f"{d['payload_type']} ({d['resolution']})" for d in plain_subset]
    x = range(len(labels))
    width = 0.35

    ax.bar([i - width/2 for i in x], [d["encode_time_ms"] for d in plain_subset], width=width, label="Plain LSB Encode", color="#4a90e2")
    ax.bar([i + width/2 for i in x], [d["encode_time_ms"] for d in secure_subset], width=width, label="zlib+AES-GCM Encode", color="#e94e77")

    ax.set_title("Encoding Execution Time Comparison by Payload Type & Resolution", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Execution Time (milliseconds)", fontsize=11)
    ax.legend(frameon=True, facecolor="white", edgecolor="#ddd")
    plt.tight_layout()
    plot4_path = PLOTS_DIR / "execution_time_comparison.png"
    plt.savefig(plot4_path, dpi=300)
    plt.close()

    print(f"Generated 4 performance plots in: {PLOTS_DIR}")


if __name__ == "__main__":
    generate_all_plots()
