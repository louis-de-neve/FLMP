import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from pathlib import Path

country = "GBR"

results_file = Path(f"C:\\Users\\Thomas Ball\\OneDrive - University of Cambridge\\Work\\Leakage_ratios\\results\\mrio_pipeline_results_260826\\2021\\{country}\\impacts_full.csv")
save_dir = Path("C:\\Users\\Thomas Ball\\OneDrive - University of Cambridge\\Work\\Work for others\\Andrew DEFRA 8sept")

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

df = pd.read_csv(results_file, index_col=0)
crop_db = pd.read_csv("input_data/commodity_crosswalk.csv")

cwalk = crop_db[["Item_Code", "group_name_v7"]].drop_duplicates()

domestic = df[df["Country_ISO"] == country]
imported = df[df["Country_ISO"] != country]

def group_totals(sub_df):
    dfx = sub_df.merge(cwalk, left_on="ItemT_Code", right_on="Item_Code", how="left")
    return dfx.groupby("group_name_v7").agg({"provenance_tonnes": "sum", "life_extinctions_per_sp_calc": "sum"})

domestic_totals = group_totals(domestic)
imported_totals = group_totals(imported)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 6))

groups = [g for g in color_dict if g != "Total"]

x = [0, 1]
xlabels = ["Domestic", "Imported"]

mass_bottoms = [0, 0]
impact_bottoms = [0, 0]

for group in groups:

    mass_vals = [
        domestic_totals["provenance_tonnes"].get(group, 0) / 1e6,
        imported_totals["provenance_tonnes"].get(group, 0) / 1e6,
    ]
    impact_vals = [
        domestic_totals["life_extinctions_per_sp_calc"].get(group, 0) / sp_count,
        imported_totals["life_extinctions_per_sp_calc"].get(group, 0) / sp_count,
    ]

    alpha = 0.8
    ax1.bar(x, mass_vals, 
            bottom=mass_bottoms, color=color_dict[group], 
            label=group,
            alpha = alpha)
    ax2.bar(x, impact_vals, 
            bottom=impact_bottoms, color=color_dict[group],
            alpha = alpha)

    mass_bottoms = [b + v for b, v in zip(mass_bottoms, mass_vals)]
    impact_bottoms = [b + v for b, v in zip(impact_bottoms, impact_vals)]

    print(f"{group} domestic mass (Mt): {mass_vals[0]:.3f}, imported mass (Mt): {mass_vals[1]:.3f}")
    print(f"{group} domestic impact: {impact_vals[0]:.3e}, imported impact: {impact_vals[1]:.3e}")

print(f"TOTAL domestic mass (Mt): {mass_bottoms[0]:.3f}, imported mass (Mt): {mass_bottoms[1]:.3f}")
print(f"TOTAL domestic impact: {impact_bottoms[0]:.3e}, imported impact: {impact_bottoms[1]:.3e}")

for ax in (ax1, ax2):
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels)

ax1.set_ylabel("Total mass (million tonnes)")
ax2.set_ylabel(r"Mean change in extinction risk per species ($\Delta E$ per sp.)")

# fig.legend(*ax1.get_legend_handles_labels(), 
#            loc="upper center", ncol=1, 
#         #    bbox_to_anchor=(0.5, -0.05)
#         )

ax2.legend(*ax1.get_legend_handles_labels(), 
           loc="upper left", ncol=1,
           fontsize = 9,
        #    bbox_to_anchor=(0.5, -0.05)
        )

fig.tight_layout()

fig.savefig(save_dir / "UK_domestic_vs_imported.png", dpi=300, bbox_inches="tight")

plt.show()
