import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

df = pd.read_csv("ufc_analysis_data.csv")
df["total_fights"] = df["wins"] + df["losses"] + df["draws"]
df = df[df["total_fights"] >= 3].copy()
print(f"fighters with >=3 fights: {len(df)}")

feat_cols = ["slpm", "str_acc", "sapm", "str_def", "td_avg", "td_acc", "td_def", "sub_avg"]
X = df[feat_cols].values
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

pca = PCA(n_components=4, random_state=0)
pcs = pca.fit_transform(Xs)
print("\nexplained variance ratio:", np.round(pca.explained_variance_ratio_, 3))
print("cumulative:", np.round(np.cumsum(pca.explained_variance_ratio_), 3))

loadings = pd.DataFrame(pca.components_.T, index=feat_cols, columns=[f"PC{i+1}" for i in range(4)])
print("\nloadings:\n", loadings.round(3))

# k-means on PC1+PC2 (striking vs grappling axes) with k=3
km = KMeans(n_clusters=3, random_state=0, n_init=10)
df["cluster"] = km.fit_predict(pcs[:, :2])

print("\ncluster sizes:\n", df["cluster"].value_counts())
print("\ncluster means (raw stats):")
print(df.groupby("cluster")[feat_cols + ["win_rate"]].mean().round(2))

df.to_csv("fighters_with_style_cluster.csv", index=False)
print("\nsaved fighters_with_style_cluster.csv")

print("\n" + "="*70)
print("Re-cluster on PC2 only (striking <-> grappling axis, skill-level-free)")
print("="*70)
km2 = KMeans(n_clusters=3, random_state=0, n_init=10)
df["style_cluster"] = km2.fit_predict(pcs[:, 1].reshape(-1, 1))

# order clusters by PC2 mean so labels are consistent (low->high)
order = df.groupby("style_cluster")["cluster"].count().index  # placeholder
pc2_means = pd.Series(pcs[:, 1]).groupby(df["style_cluster"]).mean().sort_values()
label_map = {}
names = ["グラップラー", "オールラウンダー", "ストライカー"]
for name, cl in zip(names, pc2_means.index):
    label_map[cl] = name
df["style_label"] = df["style_cluster"].map(label_map)

print(df.groupby("style_label")[feat_cols].mean().round(2))
print()
print(df["style_label"].value_counts())
df.to_csv("fighters_with_style_cluster.csv", index=False)
