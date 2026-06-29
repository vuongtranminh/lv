"""Phân tích định tính — Clustering reasoning bằng K-Means.

Áp dụng phương pháp của bài báo *Large Language Models are Autonomous Cyber Defenders* [2]
mục IV.E:

1. Thu thập (action, reasoning_text) từ audit log
2. Embedding reasoning_text bằng OpenAI text-embedding-3-large (3.072 chiều)
3. Giảm chiều bằng PCA xuống 3 thành phần
4. Phân cụm bằng K-Means với K xác định qua Elbow + Silhouette
5. Tóm tắt mỗi cluster bằng LLM
6. Vẽ scatter plot 2D + xuất bảng đặc trưng cluster

Sử dụng:
    python benchmark/analyze_clustering.py benchmark/results/ --setup C
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    import matplotlib.pyplot as plt
except ImportError as e:
    print("Thiếu dependency. Cài: pip install pandas scikit-learn matplotlib openai")
    print(f"Detail: {e}")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("WARN: openai chưa cài. Sẽ skip phần tóm tắt cluster bằng LLM.")
    OpenAI = None


# ─── Cấu hình ────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
PCA_COMPONENTS = 3
K_RANGE = range(2, 8)


# ─── Bước 1 — Thu thập (action, reasoning) ──────────────────────────────────

def load_audit_logs(results_dir: Path, setup_filter: str = None) -> pd.DataFrame:
    """Đọc tất cả CSV trong results/, gộp thành 1 DataFrame."""
    files = sorted(results_dir.glob("*.csv"))
    if setup_filter:
        files = [f for f in files if f.name.startswith(f"{setup_filter}_")]

    if not files:
        raise FileNotFoundError(f"Không tìm thấy CSV nào trong {results_dir} (filter: {setup_filter})")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["source_file"] = f.name
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    # Chỉ giữ dòng có reasoning + action
    combined = combined.dropna(subset=["llm_reasoning", "final_action"])
    combined = combined[combined["llm_reasoning"].str.strip() != ""]
    print(f"Đã load {len(combined)} cặp (action, reasoning) từ {len(files)} file.")
    return combined


# ─── Bước 2 — Embedding ──────────────────────────────────────────────────────

def embed_reasoning(df: pd.DataFrame, batch_size: int = 100) -> np.ndarray:
    """Gọi OpenAI text-embedding-3-large theo batch."""
    if OpenAI is None:
        raise RuntimeError("openai package không có. Cài: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY chưa set. Cần để gọi embedding API.")

    client = OpenAI(api_key=api_key)
    texts = df["llm_reasoning"].tolist()
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend([item.embedding for item in response.data])
        print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)}")

    return np.array(embeddings)


# ─── Bước 3 — PCA giảm chiều ─────────────────────────────────────────────────

def reduce_dimension(embeddings: np.ndarray, n_components: int = 3) -> np.ndarray:
    pca = PCA(n_components=n_components, random_state=42)
    reduced = pca.fit_transform(embeddings)
    explained = pca.explained_variance_ratio_.sum()
    print(f"PCA: giảm từ {embeddings.shape[1]} → {n_components} chiều (giữ {explained:.1%} variance)")
    return reduced


# ─── Bước 4 — K-Means + chọn K tối ưu ───────────────────────────────────────

def find_optimal_k(reduced: np.ndarray, k_range=K_RANGE) -> int:
    """Elbow Method + Silhouette Score."""
    wcss = []   # Within-cluster sum of squares
    sils = []

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(reduced)
        wcss.append(kmeans.inertia_)
        sils.append(silhouette_score(reduced, labels))
        print(f"  K={k}: WCSS={kmeans.inertia_:.0f}, Silhouette={sils[-1]:.3f}")

    # Chọn K có silhouette cao nhất
    optimal_k = list(k_range)[np.argmax(sils)]
    print(f"K tối ưu (silhouette cao nhất): {optimal_k}")

    return optimal_k, wcss, sils


def cluster_with_kmeans(reduced: np.ndarray, k: int) -> np.ndarray:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    return kmeans.fit_predict(reduced)


# ─── Bước 5 — Tóm tắt cluster bằng LLM ──────────────────────────────────────

def summarize_clusters(df: pd.DataFrame, labels: np.ndarray) -> dict:
    """Dùng GPT-4o để tóm tắt nội dung mỗi cluster."""
    if OpenAI is None:
        return {int(k): "(skip — không có OpenAI client)" for k in set(labels)}

    client = OpenAI()
    summaries = {}

    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        sample_reasoning = df[mask]["llm_reasoning"].sample(min(20, mask.sum()), random_state=42).tolist()

        prompt = (
            "Dưới đây là các đoạn reasoning của một AI agent phòng thủ mạng trong cùng cụm. "
            "Tóm tắt chủ đề chính của cụm này trong 1-2 câu (tiếng Việt):\n\n"
            + "\n---\n".join(sample_reasoning[:10])
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        summary = response.choices[0].message.content.strip()
        summaries[int(cluster_id)] = summary
        print(f"  Cluster {cluster_id}: {summary[:80]}...")

    return summaries


# ─── Bước 6 — Visualization ──────────────────────────────────────────────────

def plot_clusters(reduced: np.ndarray, labels: np.ndarray, output_path: Path):
    """Scatter plot 2D dùng 2 thành phần PCA đầu tiên."""
    fig, ax = plt.subplots(figsize=(10, 7))
    n_clusters = len(set(labels))
    colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))

    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        ax.scatter(reduced[mask, 0], reduced[mask, 1],
                   c=[colors[cluster_id]], label=f"Cluster {cluster_id}",
                   alpha=0.6, s=30)

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Phân cụm reasoning của LLM Agent (K-Means + PCA)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Đã lưu hình: {output_path}")


def plot_elbow(wcss, sils, k_range, output_path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(list(k_range), wcss, "o-")
    ax1.set_xlabel("K")
    ax1.set_ylabel("WCSS")
    ax1.set_title("Elbow Method")
    ax1.grid(True)

    ax2.plot(list(k_range), sils, "o-")
    ax2.set_xlabel("K")
    ax2.set_ylabel("Silhouette Score")
    ax2.set_title("Silhouette Score")
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Đã lưu hình: {output_path}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path, help="Thư mục chứa CSV audit log")
    parser.add_argument("--setup", help="Filter theo setup (A/B/C)")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results",
                        help="Thư mục xuất kết quả")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # Pipeline
    print("=== Bước 1: Load audit logs ===")
    df = load_audit_logs(args.results_dir, args.setup)

    print("\n=== Bước 2: Embedding ===")
    embeddings = embed_reasoning(df)

    print("\n=== Bước 3: PCA giảm chiều ===")
    reduced = reduce_dimension(embeddings, n_components=PCA_COMPONENTS)

    print("\n=== Bước 4: K-Means + chọn K tối ưu ===")
    optimal_k, wcss, sils = find_optimal_k(reduced)
    labels = cluster_with_kmeans(reduced, optimal_k)

    print("\n=== Bước 5: Tóm tắt cluster bằng LLM ===")
    summaries = summarize_clusters(df, labels)

    print("\n=== Bước 6: Xuất kết quả ===")
    df_out = df.copy()
    df_out["cluster"] = labels
    df_out["pc1"] = reduced[:, 0]
    df_out["pc2"] = reduced[:, 1]

    suffix = f"_{args.setup}" if args.setup else ""
    df_out.to_csv(args.output / f"clustering_result{suffix}.csv", index=False)

    with open(args.output / f"cluster_summaries{suffix}.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    plot_clusters(reduced, labels, args.output / f"clustering{suffix}.png")
    plot_elbow(wcss, sils, K_RANGE, args.output / f"elbow_silhouette{suffix}.png")

    # Bảng đặc trưng cluster
    cluster_stats = []
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        actions = df[mask]["final_action"].value_counts().head(3)
        cluster_stats.append({
            "cluster": int(cluster_id),
            "size": int(mask.sum()),
            "summary": summaries.get(int(cluster_id), ""),
            "top_actions": actions.to_dict(),
        })

    with open(args.output / f"cluster_stats{suffix}.json", "w", encoding="utf-8") as f:
        json.dump(cluster_stats, f, indent=2, ensure_ascii=False)

    print("\nHoàn thành. Xem file output trong:", args.output)


if __name__ == "__main__":
    main()
