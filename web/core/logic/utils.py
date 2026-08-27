import pandas as pd

from core.loader import load_species, load_individuals, load_moves

def save_new_individual(new_row):
    individuals = load_individuals()
    individuals = pd.concat([individuals, pd.DataFrame([new_row])], ignore_index=True)
    individuals.to_csv("data/individuals.csv", index=False)

def update_individual(edit_id, updated_row):
    individuals = load_individuals()
    for col, val in updated_row.items():
        individuals.loc[individuals["individual_id"] == edit_id, col] = val

    individuals.to_csv("data/individuals.csv", index=False)
