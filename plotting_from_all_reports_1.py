# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 11:03:42 2023

@author: andre
"""

import os
import pandas as pd
import seaborn as sns
# import matplotlib.pyplot as plt


def search_folder(cwd):
    """
    Lists all the files in the current work directory (cwd).
    
    Takes:                  Returns:
        str                     list
    """
    cur_files=os.listdir(cwd)
    return cur_files

def get_workflow_num(run_name):
    """
    Gets the workflow code from the run_name.
    
    Takes:              Returns:
        str*str             str*str
    """
    max_un_index=0
    for i in range(len(run_name)):
        if run_name[i]=="_":
            max_un_index=i
    
    max_un_index+=1
    run_num=run_name[max_un_index:]
    return run_num

def add_workflow(df):
    """
    Adds the workflow column to the pandas dataframe and fills it with the
    workflow codes from each run.
    
    Takes:                          Returns:
        obj: pandas dataframe           obj: pandas dataframe
    """
    df['workflow'] = ''
    
    for index, row in df.iterrows():
        work_f=row['Run']
        work_f_num=get_workflow_num(work_f)
        df.at[index, 'workflow'] = work_f_num
        
    return df

def merge_all_reports_and_times(df, metadata_dir):
    """
    Takes the all_reports_file, reads it as a pandas dataframe, 
    gets all the time_elapsed values of each sample and adds it 
    to the pandas dataframe.
    The final dataframe has all the info + time_elapsed.
    """
    #Go to the directory of the metadata files
    os.chdir(metadata_dir)
    
    #For each metafile, it reads
    meta_files=search_folder(metadata_dir)
    for met_file in meta_files:
        df1 = pd.read_csv(met_file, sep='\t')
        df1 = df1.loc[:, ["sample name", "time elapsed"]]
        # os.chdir("C:\\Users\\andre\\OneDrive - FCT NOVA\André\\Mestrado - Bioinfo\\2º Ano\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_formating_metadata\\new_meta")
        for index, row in df.iterrows():
            if row["Sample"] == df1["sample name"][0]:
                df.at[index, "time elapsed"] = df1.at[0, "time elapsed"]
        
        
    # #Add the workflows
    df=add_workflow(df)

    # #Directory of the new all_report file with all the info + time_elapsed
    # cwd="C:\\Users\\andre\\OneDrive - FCT NOVA\André\\Mestrado - Bioinfo\\2º Ano\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_formating_metadata\\new_all_reports"
    # os.chdir(cwd)
    # df.to_csv("new_export_all_reports_13_02_2023.tsv", sep="\t", index=False)
    
    return df

def plot_s_graphics(pd_df, param, x_axis, y_axis, plot_type, separator, save_or, save_dir, dpi_qual):
        
    ans=(True, separator)
    if separator not in pd_df.columns:
        ans=(False, separator)
        separator=None
    
    
    #Picking the palette of colors for the plots.
    # pal=sns.color_palette("tab10")
    
    
    pd_df = pd_df.sort_values(by=[param, y_axis], ascending=False)
    
    for par in pd_df[param].unique():
        sub_df=pd_df[pd_df[param]==par]
        sub_df=sub_df.sort_values(by=[param, y_axis], ascending=True)
        
        # plot_export_name=sub_df
        
        plot_=sns.relplot(
            data=sub_df, kind=plot_type, 
            x=x_axis, y=y_axis,
            facet_kws=dict(sharex=False), col=param, hue=separator, style=separator,
            markers=True, dashes=True, size=separator) #,palette=(pal)
        
        sns.set(style='whitegrid', rc = {'legend.labelspacing': 1.2})
        
        if save_or=="y":
            plots_dir=os.path.join(save_dir, "output_plots")
            if not os.path.exists(plots_dir):
                os.makedirs(plots_dir)
            os.chdir(plots_dir)
            plot_.savefig(f"{param}-{par}.jpeg", dpi=dpi_qual)
            
    
    if ans[0]==False:
        print(f"{ans[1]} doesnt exist.")

### MAIN FOR COMMAND LINE  
def main():
    """
    INSTRUCTIONS:
    
    all_reports file_dir - directory of the all_reports file
        
    metadata_dir - directory of the metadata files
    
    param - plotting for each 'param'
    
    x_axis - column name to assign to x_axis
    
    y_axis - column name to assign to y_axis
    
    plot_type - can be 'scatter' or 'line'
    
    separator - represents the various samples of the same 'param' which have different 'separator'.
    Example: separator = 'workflow' will show the different workflows used for the same same.
    """
    all_rep_dir=str(input("Input the all_reports.tsv file directory:\n > "))
    while os.path.exists(all_rep_dir)!=True:
        print("Invalid directory...")
        all_rep_dir=str(input("Input the all_reports.tsv file directory:\n > "))
    
    metadata_dir=str(input("Input the metadata files directory:\n > "))
    while os.path.exists(metadata_dir)!=True:
        print("Invalid directory...")
        metadata_dir=str(input("Input the metadata files directory:\n > "))
    

    os.chdir(all_rep_dir)
    all_rep_name=search_folder(all_rep_dir)
    df = pd.read_csv(all_rep_name[0], sep='\t')
    df1=merge_all_reports_and_times(df, metadata_dir)
    

    print("\nCreating a plot for each:")
    for _ in df1.columns:
        print("- ", _)
    param=str(input("> "))
    while param not in df1.columns:
        print(f"{param} not a column option")
        param=str(input("> "))
    
    print("\nx_axis:\n(must be a column from the all_reports.tsv file)")
    for _ in df1.columns:
        if _!=param:
            print("- ", _)
    x_axis=str(input("> "))
    while x_axis not in df1.columns:
        print(f"{x_axis} not a column option")
        x_axis=str(input("> "))
    
    print("\ny_axis:\n(must be a column from the all_reports.tsv file)\n")
    for _ in df1.columns:
        if _!=param and _!=x_axis:
            print("- ", _)
    y_axis=str(input("> "))
    while y_axis not in df1.columns:
        print(f"{y_axis} not a column option")
        y_axis=str(input("> "))
    
    print(f"\nFor each {param} i want to also see the different:")
    for _ in df1.columns:
        if _!=param and _!=x_axis and _!=y_axis:
            print("- ", _)
    separator=str(input("> "))
    while separator not in df1.columns:
        print(f"{separator} not a column option")
        separator=str(input("> "))
    
    plot_type=str(input("Plot type:\n('scatter' or 'line')\n > "))
    while plot_type not in ("line", "scatter"):
        plot_type=str(input("Plot type:\n('scatter' or 'line')\n > "))
    
    save_or=str(input("Do you wish to save the resultant plots? ('y' or 'n')\n > "))
    while save_or not in ("y", "n"):
        save_or=str(input("Do you wish to save the resultant plots? ('y' or 'n')\n > "))
    if save_or=="y":
        print(f"The plots will be saved in the format of {param}.[{param}].jpeg\n")
        save_dir=str(input("\nDirectory to save the resultant plots?\n > "))
        dpi_qual=int(input("Quality of the image (dpi - higher dpi inscreases file size):\n > "))
    else:
        save_dir=None
        dpi_qual=None
    
    
    plot_s_graphics(df1, param, x_axis, y_axis, plot_type, separator, save_or, save_dir, dpi_qual)

main()


