import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def _perform_aggregation(df: pd.DataFrame, group_columns: list, agg_column: str, agg_func, final_columns: list) -> pd.DataFrame:
    df = df[group_columns + [agg_column]]
    df = df.groupby(group_columns)[agg_column].agg(agg_func).reset_index()
    df.columns = final_columns
    return df


def count_libraries_usage(df: pd.DataFrame, by: str = 'files') -> pd.DataFrame:
    if by not in ('files', 'occurences'):
        raise ValueError(f"Invalid value for 'by' parameter. Accepted values are 'files' or 'occurrences', got '{by}'")
    elif by == 'files':
        return _perform_aggregation(df, ['module'], 'filename', 'nunique', ['module_name', 'count'])
    elif by == 'occurences':
        return _perform_aggregation(df, ['module'], 'count', 'sum', ['module_name', 'count'])
    

def count_component_types_by_module(df: pd.DataFrame) -> pd.DataFrame:
    df = df.groupby(['module', 'component_type']).size().reset_index(name='count')
    return df


def count_components_usage(df: pd.DataFrame, module: str, by: str = 'files', component_types: tuple = ('function', 'attribute', 'class', 'method', 'exception')) -> pd.DataFrame:
    df = df[(df['module'] == module) & (df['component_type'].isin(component_types))]

    if by not in ('files', 'occurences'):
        raise ValueError(f"Invalid value for 'by' parameter. Accepted values are 'files' or 'occurrences', got '{by}'")
    elif by == 'files':
        return _perform_aggregation(df, ['component_type', 'component_name'], 'filename', 'nunique', ['component_type', 'component_name', 'count'])
    elif by == 'occurences':
        return _perform_aggregation(df, ['component_type', 'component_name'], 'count', 'sum', ['component_type', 'component_name', 'count'])


def show_popularity(df: pd.DataFrame, title: str, top_n: int = 10):
    entity_type = [col for col in df.columns if col != 'count'][0]
    df = df.sort_values('count', ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.barplot(y=entity_type, x='count', data=df, orient='h', ax=ax)
    
    for i in range(top_n):
        ax.text(df['count'].iloc[i], i, 
                f' {df["count"].iloc[i]:,.0f}', 
                va='center')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.tick_params(axis='y', length=0)
    
    plt.title(title)
    plt.show()
