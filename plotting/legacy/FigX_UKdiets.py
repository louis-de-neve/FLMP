import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
# import seaborn as sns
from pathlib import Path

# country = "GBR"
country = "USA"

year = 2021

skip = [
        "EAT-Lancet"
        # "No-ruminant"
        ]

res_dir = Path("../results/mrio_pipeline_results_260826_spam2020")
results_file = res_dir / str(year) / country / "impacts_full.csv"


Path(f"../outputs/{Path(res_dir).name}").mkdir(parents=True, exist_ok=True)
save_dir = Path(f"../outputs/{Path(res_dir).name}")

if country == "GBR":
    diets_dat = pd.read_csv("misc_scripts/diets5_UK.csv", encoding="latin-1")
    pop_scalar = 1.0 / 69487000 

elif country == "USA":
    diets_dat = pd.read_csv("misc_scripts/diets5_US.csv", encoding="latin-1")
    pop_scalar = 1.0 / 342500000 # 342.6M

spdf = pd.read_csv("input_data/mapspam_outputs/outputs/2020/processed_results_2020.csv")
sp_count = spdf.sp_count.max()

color_dict = {'Grains, roots, starchy carbohydrates' : "#E69F00",
                'Legumes, beans, nuts' : "#F0E442",
                'Fruit and vegetables' : "#009E73",
                'Stimulants and spices' : "#56B4E9",
                'Ruminant meat' : "#D55E00", 
                'Dairy and eggs' : "#0072B2",
                'Poultry and pig meat' : "#CC79A7", 
                'Sugar crops' : "#93F840",
                'Total' : "#000000"
                }




diets_dat = diets_dat.drop(columns=[col for col in diets_dat.columns if col in skip])

df = pd.read_csv(results_file, index_col=0)
country_codes = pd.read_excel("input_data/nocsDataExport_20251021-164754.xlsx")
crop_db = pd.read_csv("input_data/commodity_crosswalk.csv")

cwalk = crop_db[["group_name_v6", "group_name_v7"]].drop_duplicates()
diets = diets_dat.merge(cwalk, left_on="Group", right_on="group_name_v6", how="left")

cwalk = crop_db[["Item_Code", "group_name_v7"]].drop_duplicates()
dfx = df.groupby("ItemT_Code").sum()["life_extinctions_per_sp_calc"].sort_values(ascending=False).reset_index()
dfx = dfx.merge(cwalk, left_on="ItemT_Code", right_on="Item_Code", how="left")

dfxx = dfx.groupby("group_name_v7").sum()["life_extinctions_per_sp_calc"].reset_index()

fig, ax = plt.subplots(figsize=(7, 6))



for d, diet in enumerate(diets_dat.columns[1:]):

    diet_cals = diets.loc[diets["Group"] == "Cals", diet].sum()
    base_cals = diets.loc[diets["Group"] == "Cals", "Baseline"].sum()
    
    cal_scalar = diet_cals / base_cals

    diet_p = diets.loc[diets["Group"] != "Cals", diet].sum()
    base_p = diets.loc[diets["Group"] != "Cals", "Baseline"].sum()

    p_scalar = diet_p / base_p

    total_height = 0
    for g, group in enumerate(dfxx["group_name_v7"].unique()):
        
        group_impact = dfxx[dfxx["group_name_v7"] == group]["life_extinctions_per_sp_calc"].values[0]

        diet_base = diets.loc[diets["group_name_v7"] == group, diet].sum()
        base_base = diets.loc[diets["group_name_v7"] == group, "Baseline"].sum()

        group_scalar = diet_base / base_base

        val_scalar = (1/cal_scalar) * group_scalar

        if group in ("Stimulants and spices", "Sugar crops"):
            val_scalar = 1

        val = group_impact * val_scalar * pop_scalar * (1/365) * (1/p_scalar) * (1/sp_count)

        ax.bar(d, val, bottom=total_height,
               color=color_dict[group], 
               label=group if d == 0 else "")
        
        total_height += val

    print(f"{diet}: {total_height:.2e}")
    
    print(f"TOTAL SP {diet}: {total_height * sp_count * 365 / pop_scalar:.2e}")
ax.legend()
ax.set_xticks(range(len(diets_dat.columns[1:])))
ax.set_xticklabels(diets_dat.columns[1:], rotation=45, ha="right")

ax.set_ylabel("Mean change extinction risk opp-cost ($\Delta E$ per sp., per cap.)")

fig.tight_layout()

print(f"Saving figure to ../outputs/{Path(res_dir).name}/FigX_{country}_{year}.png")
plt.savefig(f"../outputs/{Path(res_dir).name}/FigX_{country}_{year}.png", dpi=600, bbox_inches='tight')

plt.show()