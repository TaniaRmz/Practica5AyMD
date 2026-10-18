"""Escalamiento, correlación y componentes principales."""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import NUMERIC


def prepare_features(clean, threshold=0.95, variance_target=0.95):
    train = clean["partition"].eq("entrenamiento")
    if train.sum() < 10 or (~train).sum() < 2:
        raise ValueError("La limpieza dejó muy pocos datos en una de las particiones.")
    corr = clean.loc[train, NUMERIC].corr(method="pearson")
    kept, removed = [], []
    # Dejamos primero la potencia activa porque sirve para explicar el consumo.
    for column in NUMERIC:
        if clean.loc[train, column].std() == 0:
            removed.append({"variable": column, "reason": "constante", "related_to": None, "r": None})
            continue
        redundant = next((other for other in kept if abs(corr.loc[column, other]) >= threshold), None)
        if redundant:
            removed.append({"variable": column, "reason": "correlacion", "related_to": redundant,
                            "r": float(corr.loc[column, redundant])})
        else:
            kept.append(column)
    if "Global_active_power" not in kept or len(kept) < 2:
        raise ValueError("No hay suficientes variables con variación, incluyendo la potencia activa.")

    scaler = StandardScaler()
    scaler.fit(clean.loc[train, kept])
    scaled = scaler.transform(clean[kept])
    # El PCA ve solo el pasado. Después proyectamos todas las filas con ese mismo ajuste.
    pca = PCA(svd_solver="full")
    pca.fit(scaled[train.to_numpy()])
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    count = min(len(kept), int(np.searchsorted(cumulative, variance_target) + 1))
    scores = pca.transform(scaled)
    components = [f"PC{i + 1}" for i in range(len(kept))]
    prepared = clean[["timestamp", "partition", "was_imputed", "power_observed"]].copy()
    prepared[kept] = scaled
    prepared[components[:count]] = scores[:, :count]

    variance = pd.DataFrame({
        "component": components,
        "explained": pca.explained_variance_ratio_, "cumulative": cumulative,
        "retained": np.arange(len(kept)) < count,
    })
    # Estos pesos son los coeficientes de las variables estandarizadas en cada PC.
    weights = pd.DataFrame(pca.components_.T, index=kept, columns=components)
    weights.index.name = "variable"
    sample_index = np.unique(np.linspace(0, len(clean) - 1, min(6000, len(clean)), dtype=int))
    projection = clean.iloc[sample_index][["timestamp", "partition"]].copy()
    projection["PC1"] = scores[sample_index, 0]
    projection["PC2"] = scores[sample_index, 1]
    projection["power_kw"] = clean.iloc[sample_index]["Global_active_power"].to_numpy()
    model = {
        "kept": kept, "removed": removed, "correlation_threshold": threshold,
        "variance_target": variance_target, "components_retained": count,
        "retained_variance": float(cumulative[count - 1]),
        "scaler_mean": dict(zip(kept, scaler.mean_.tolist())),
        "scaler_scale": dict(zip(kept, scaler.scale_.tolist())),
        "pca_mean": pca.mean_.tolist(), "pca_coefficients": pca.components_.tolist(),
        "fit_partition": "entrenamiento",
    }
    return prepared, corr, variance, weights, projection, model
