import pandas as pd

def load_species():
    df = pd.read_csv("data/species.csv")

    # species_id の _normal 付きデータは除外する
    df = df[~df["species_id"].str.contains("_normal", case=False, na=False)]

    for col in ["elitefast", "elitecharge", "evolves_to", "evolves_from"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    return df

def load_moves():
    return pd.read_csv("data/moves.csv")

def load_individuals():
    df = pd.read_csv("data/individuals.csv")

    # NaN を False に置き換え
    df["is_shadow"] = (
        df["is_shadow"]
            .fillna(False)
            .map(lambda x: True if x in [True, "True", 1] else False)
    )
    df["is_purified"] = (
        df["is_purified"]
            .fillna(False)
            .map(lambda x: True if x in [True, "True", 1] else False)
    )
    return df

def load_opponents():
    return pd.read_csv("data/opponents.csv")
