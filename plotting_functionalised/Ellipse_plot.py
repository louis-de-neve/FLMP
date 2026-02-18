import pandas as pd
import numpy as np
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

def confidence_ellipse(x, y, ax, n_std=3.0, facecolor='none', **kwargs):
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensional dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                      facecolor=facecolor, **kwargs)

    # Calculating the standard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the standard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)
    print(mean_x, mean_y)

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mean_x, mean_y)

    ellipse.set_transform(transf + ax.transAxes)
    return ax.add_patch(ellipse)

def ellipse_plot(ax, country_df_2010, country_df_2021, region_map, regions, cons_2010,
                      xlims=(1e-8, 1),
                      ylims=(5e-11, 2e-5),
                      xvar="Cons_share", yvar="E_per_kg"
                      ):
    ax.set_xlim(*xlims)
    ax.set_ylim(*ylims)
    ax.set_yscale("log")
    ax.set_xscale("log")
    axis_to_data = ax.transAxes + ax.transData.inverted()
    data_to_axis = axis_to_data.inverted()

    country_df_2010 = country_df_2010.merge(region_map[["alpha-3", "region"]], left_on="ISO", right_on="alpha-3", how="left")
    country_df_2021 = country_df_2021.merge(region_map[["alpha-3", "region"]], left_on="ISO", right_on="alpha-3", how="left")

    if "Cons_share" not in country_df_2021.columns:
        country_df_2021["Cons_share"] = country_df_2021["Production_kg"]/cons_2010
    if "Cons_share" not in country_df_2010.columns:
        country_df_2010["Cons_share"] = country_df_2010["Production_kg"]/cons_2010

    for region in regions["region"].unique():
        region_countries_2010 = country_df_2010[country_df_2010["region"]==region]
        region_countries_2021 = country_df_2021[country_df_2021["region"]==region]
        xy = []
        xs = []
        ys = []
        for _, row in region_countries_2021.iterrows():
            x = row[xvar]
            y = row[yvar]
            xy.append(data_to_axis.transform(((x,y))))
            xs.append(x)
            ys.append(y)
        xn = np.array([m[0] for m in xy])
        yn = np.array([m[1] for m in xy])
        c = region_map[region_map["region"]==region]["Color"].values[0]
        ellipse = confidence_ellipse(xn, yn, ax, n_std=2, facecolor=c[:-2]+"10", edgecolor=c)
        ax.scatter(xs, ys, color=c, label=region, alpha=0.5)
        for _, row in region_countries_2021.iterrows():
            x = row[xvar]
            y = row[yvar]
            tag = row["ISO"]
            if not ellipse.contains_point(ax.transData.transform(((x,y)))):
                x,y = data_to_axis.transform(((x,y)))
                i = -1 if y < 0.5 else 1
                x,y = axis_to_data.transform(((x,y+0.02*i)))
                ax.text(x, y, tag, fontsize=6, color=c, ha="center", va="center")
 

    ax.set_title("Change in consumption impact between 2010 and 2021")
    ax.set_ylabel("Impact, Annual Extinctions per kg")
    ax.set_xlabel("Share of Global Food Consumption")

    ax.legend(title=f"Region", fontsize=6)



    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    total_grid_color = "#2F7FF8"
    for i in range(int(np.log10(x1*y1))-2, int(np.log10(x2*y2))+2):
        i = 10 ** (i)
        x = np.logspace(np.log10(x1)-1, np.log10(x2)+1, 50)
        y = i/x
        ax.plot(x, y, color=total_grid_color, alpha=0.4, linewidth=0.8, zorder=1)
    for j in range(int(np.log10(x1*y1))-2, int(np.log10(x2*y2))+2):
        for i in np.linspace(1*(10**j), 9*(10**j), 9):
            x = np.logspace(np.log10(x1)-1, np.log10(x2)+1, 50)
            y = i/x
            ax.plot(x, y, ls="dashed", color=total_grid_color, alpha=0.2, linewidth=0.8, zorder=1)
    ax3 = ax.twiny()
    ax3.set_xscale('log')
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    ax3.set_xlim(x1*y2, x2*y2)
    ax3.set_xlabel("Annual Extinctions per kg", color=total_grid_color)
    ax3.tick_params(axis='x', colors=total_grid_color)
        

