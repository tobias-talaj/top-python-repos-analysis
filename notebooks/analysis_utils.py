import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def count_libraries_usage(df: pd.DataFrame, by: str = 'files') -> pd.DataFrame:
    df_copy = df.copy()
    if by == 'files':
        df_copy = df_copy.groupby('module')['filename'].nunique().reset_index()
        df_copy.columns = ['module_name', 'count']
        return df_copy
    elif by == 'occurences':
        return df_copy.groupby('module')['count'].sum().reset_index()
    else:
        raise ValueError(f"Invalid value for 'by' parameter. Accepted values are 'files' or 'occurrences', got '{by}'")
    

def count_components_usage(df: pd.DataFrame, module: str, by: str = 'files', component_types: tuple = ('function', 'attribute', 'class', 'method', 'exception')) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy = df_copy[(df_copy['module'] == module) & (df_copy['component_type'].isin(component_types))]
    if by == 'files':
        df_copy = df_copy[['component_name', 'filename']].groupby('component_name')['filename'].nunique().reset_index()
        df_copy.columns = ['component_name', 'count']
        return df_copy
    elif by == 'occurences':
        return df_copy[['component_name', 'count']].groupby('component_name')['count'].sum().reset_index()


def show_popularity(df: pd.DataFrame, title: str, top_n: int = 10):
    df_copy = df.copy()
    entity_type = [col for col in df_copy.columns if col != 'count'][0]
    df_copy = df_copy.sort_values('count', ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.barplot(y=entity_type, x='count', data=df_copy, orient='h', ax=ax)
    
    for i in range(top_n):
        ax.text(df_copy['count'].iloc[i], i, 
                f' {df_copy["count"].iloc[i]:,.0f}', 
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
