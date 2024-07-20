import pathlib
import sys
import zipfile

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

COLUMNS = [
    "percentage of input passed filter",
    "percentage of input merged",
    "percentage of input non-chimeric",
]


def main() -> int:
    results_dir = pathlib.Path("./results/qiime2_backup_2")
    paths = [pathlib.Path(path) for path in results_dir.glob("filtering_stats*.qza")]
    params = [
        pathlib.Path(path).name.replace("filtering_stats_", "").strip(".qza")
        for path in results_dir.glob("filtering_stats*.qza")
    ]

    print(paths)

    dfs = []
    for path, name in zip(paths, params):
        with zipfile.ZipFile(path, "r") as zip_handler:
            zip_handler.extractall(results_dir / name)

        stats_path = pathlib.Path(results_dir / name).glob("**/stats.tsv")
        if stats_path:
            stats_path = next(stats_path).resolve()

        df = (
            pd.read_csv(stats_path, sep="\t", skiprows=[1], index_col=0)[COLUMNS]
            .stack()
            .rename(name)
        )
        dfs.append(df)

    matplotlib.use('TKAgg')
    split_into = 6
    fig, ax = plt.subplots(nrows=split_into, ncols=1,figsize=(15,5), sharey=True)

    print(len(dfs))
    step = len(dfs) // split_into
    for i, dfs_window_start in enumerate(range(0, len(dfs), step)):
        dfs_window_stop = dfs_window_start + step
        print(i, dfs_window_start, dfs_window_stop)
        data = (
            pd.concat(dfs[dfs_window_start:dfs_window_stop], axis=1)
            .stack(level=0)
            .reset_index()
            .set_index("sample-id")
            .rename(columns={"level_1": "variable", "level_2": "group", 0: "value"})
        )

        sns.boxplot(data, x="group", y='value', hue="variable", ax=ax[i])
        ax[i].tick_params(rotation=10)
        ax[i].legend([], [], frameon=False)
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc='upper center')
    plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
