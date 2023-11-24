import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def libraries_in_repos(df):
    df = df.drop(['module'], axis=1).drop_duplicates()
    return df.groupby('library')['repo'].nunique().reset_index().rename(columns={'repo': 'count'})


def libraries_in_files(df):
    df = df.drop(['module'], axis=1).drop_duplicates()
    return df.groupby('library')['filename'].nunique().reset_index().rename(columns={'filename': 'count'})


def modules_in_repos(df):
    return df.groupby('module')['repo'].nunique().reset_index().rename(columns={'repo': 'count'})


def modules_in_files(df):
    return df.groupby('module')['filename'].nunique().reset_index().rename(columns={'filename': 'count'})


def module_component_counts(df):
    return df.groupby(['module', 'component_type'])['count'].sum().reset_index()


def component_in_files(df, module):
    return df[df['module'] == module].groupby(['component_type', 'component_name'])['filename'].nunique().reset_index().rename(columns={'filename': 'count'})


def component_counts(df, module):
    return df[df['module'] == module].groupby(['component_type', 'component_name'])['count'].sum().reset_index()


def specific_component_type_in_files(df, module, component_type):
    return df[(df['module'] == module) & (df['component_type'] == component_type)].groupby('component_name')['filename'].nunique().reset_index().rename(columns={'filename': 'count'})


def specific_component_type_counts(df, module, component_type):
    return df[(df['module'] == module) & (df['component_type'] == component_type)].groupby('component_name')['count'].sum().reset_index()


def show_popularity(df, title, top_n=None, full_count=None):
    color_map = {
        'attribute': '#488A99',
        'class': '#DBAE58',
        'exception': '#AC3E31',
        'function': '#484848',
        'method': '#DADADA'       
    }

    fig, ax = plt.subplots(figsize=(16, 8))

    if len(df.columns) == 2:
        df = df.sort_values(by='count', ascending=False).head(top_n).set_index(df.columns[0]).sort_values(by='count')
        df.plot(kind='barh', edgecolor='white', ax=ax, width=0.8, color=list(color_map.values()))
        ax.get_legend().remove()

    elif len(df.columns) == 3:
        grouping_column = set(df.columns) & set(['module', 'library', 'component_name']).pop()
        top_n_names = df.groupby(grouping_column)['count'].sum().sort_values(ascending=False).head(top_n).index
        df = df[df[grouping_column].isin(top_n_names)]
        df = df.pivot(index=grouping_column, columns='component_type', values='count')
        df = df.loc[df.sum(axis=1).sort_values(ascending=True).index]
        df.plot(kind='barh', stacked=True, edgecolor='white', ax=ax, width=0.8, color=[color_map[col] for col in df.columns])
        ax.legend(title='Component Type', loc='lower right')

    ax.set_xlim([-max(df.sum(axis=1)) * 0.08, max(df.sum(axis=1)) * 1.1])

    for i, total in enumerate(df.sum(axis=1)):
        if full_count:
            percentage = total / full_count * 100
            ax.text(-0.05, i, '{:1.1f}%'.format(percentage), va="center", fontsize=12, ha="right")
        else:
            ax.text(-0.05, i, '{:1.0f}'.format(total), va="center", fontsize=12, ha="right")

    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title(title, fontsize=16)
    ax.set_xticks([])
    ax.tick_params(axis='y', length=0, labelsize=12)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    plt.show()


def get_corr_table(df, index='filename', column='component_name', binary=True, top_n=24):
    if index in ('filename', 'repo') and column in ('component_name', 'module', 'library'):
        if 'count' not in df.columns:
            df['count'] = 1
        df = df[[index, column, 'count']]
        if index == 'filename':
            top = df.groupby(column)['filename'].nunique().sort_values(ascending=False).head(top_n).index
        else:
            top = df.groupby(column)['count'].sum().sort_values(ascending=False).head(top_n).index

        pivot_df = df[df[column].isin(top)].pivot_table(index=index, columns=column, values='count', fill_value=0)

        if binary:
            binary_df = pivot_df.copy()
            binary_df[binary_df > 0] = 1
            return binary_df.corr()
        else:
            return pivot_df.corr()
        

def show_correlation(df, title):
    mask = np.triu(np.ones_like(df, dtype=bool))
    cmap = LinearSegmentedColormap.from_list("custom", ['#DADADA', '#484848'], N=256)

    plt.figure(figsize=(16, 16))
    ax = sns.heatmap(df, cmap=cmap, center=0, annot=True, annot_kws={'size': 12}, fmt='.2f', mask=mask, cbar=False)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize = 12)
    ax.set_yticklabels(ax.get_ymajorticklabels(), fontsize = 12)
    ax.tick_params(bottom=False, left=False)
    ax.set(xlabel='', ylabel='')
    plt.title(title, fontsize=16)
    plt.show()
