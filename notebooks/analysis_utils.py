import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def module_in_repos(df):
    return df.groupby('module')['repo'].nunique().reset_index().rename(columns={'repo': 'count'})


def module_in_files(df):
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

    if set(df.columns) == {'module', 'count'} or set(df.columns) == {'component_name', 'count'}:
        df = df.sort_values(by='count', ascending=False).head(top_n).set_index(df.columns[0]).sort_values(by='count')
        df.plot(kind='barh', edgecolor='white', ax=ax, width=0.8, color=list(color_map.values()))
        ax.get_legend().remove()

    elif set(df.columns) == {'module', 'component_type', 'count'} or set(df.columns) == {'component_name', 'component_type', 'count'}:
        grouping_column = 'module' if 'module' in df.columns else 'component_name'
        top_n_names = df.groupby(grouping_column)['count'].sum().sort_values(ascending=False).head(top_n).index
        df = df[df[grouping_column].isin(top_n_names)]
        df = df.pivot(index=grouping_column, columns='component_type', values='count')
        df = df.loc[df.sum(axis=1).sort_values(ascending=True).index]
        df.plot(kind='barh', stacked=True, edgecolor='white', ax=ax, width=0.8, color=[color_map[col] for col in df.columns])
        ax.legend(title='Component Type', loc='lower right')

    for i, total in enumerate(df.sum(axis=1)):
        if full_count:
            percentage = total / full_count * 100
            ax.text(total + 0.1, i, '{:1.0f}%'.format(percentage), va="center", fontsize=12)
        else:
            ax.text(total + 0.1, i, '{:1.0f}'.format(total), va="center", fontsize=12)

    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title(title, fontsize=16)
    ax.set_xticks([])
    ax.tick_params(axis='y', length=0, labelsize=12)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    plt.show()


def get_corr_table(df, index='filename', column='component_name', binary=True, top_n=24):
    if index in ('filename', 'repo') and column in ('component_name', 'module'):
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
    plt.figure(figsize=(16, 16))
    ax = sns.heatmap(df, cmap='coolwarm', center=0, annot=True, annot_kws={'size': 12}, fmt='.2f', mask=mask, cbar=False)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize = 12)
    ax.set_yticklabels(ax.get_ymajorticklabels(), fontsize = 12)
    ax.tick_params(bottom=False, left=False)
    ax.set(xlabel='', ylabel='')
    plt.title(title, fontsize=16)
    plt.show()
