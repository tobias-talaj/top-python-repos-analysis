import pandas as pd
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
            percentage = total / full_count * 100  # calculate percentage
            ax.text(total + 0.1, i, '{:1.0f}%'.format(percentage), va="center", fontsize=12)  # display percentage
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
