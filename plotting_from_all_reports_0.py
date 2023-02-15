# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 16:03:28 2023

@author: andre
"""

"""
15/02/2023
###############################################################################
Este é a última versão funcional para criar um export_all com tudo + os tempos de run.
###############################################################################
"""
#DRAFT 2 - WORKS
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



####### Plotting with seaborn
def plot_s_graphics(pd_df, param, x_axis, y_axis, plot_type, out_dir, separator):
    
    plots_dir=os.path.join(out_dir, "output_plots")
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    
    
    
    #Picking the palette of colors for the plots.
    pal=sns.color_palette("tab10")
    
    os.chdir(plots_dir)
    
    pd_df = pd_df.sort_values(by=[param, y_axis], ascending=False)
    
    for par in pd_df[param].unique():
        sub_df=pd_df[pd_df[param]==par]
        sub_df=sub_df.sort_values(by=[param, y_axis], ascending=True)
        
        
        plot_=sns.relplot(
            data=sub_df, kind=plot_type, 
            x=x_axis, y=y_axis,
            facet_kws=dict(sharex=False), col=param, hue=separator, style=separator,
            palette=(pal), markers=True, dashes=True, size=separator)
        
        sns.set(style='whitegrid', rc = {'legend.labelspacing': 1.2})
        
        if len(par)>10:
            n=par[:10]
            plot_.savefig(f"{n}.jpeg", dpi=800)
        else:
            plot_.savefig(f"{par}.jpeg", dpi=800) #, dpi=600
        # plot_.savefig(f"{par}_{x_axis}_by_{y_axis}.jpeg", dpi=800) #, dpi=600
        

        
def main(all_rep_dir, metadata_dir, param, x_axis, y_axis, plot_type, separator):
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
    #all_reports_file_dir=str(input("Input the all_reports.tsv file directory:\n > "))
    
    #param=str(input("Parameter by which u want to create graphics for:\n(must be a column from the all_reports.tsv file)\n > "))
    
    #x_axis=str(input("x axis:\n(must be a column from the all_reports.tsv file)\n > "))
    
    #y_axis=str(input("y axis:\n(must be a column from the all_reports.tsv file)\n > "))
    
    #plot_type=str(input("Plot type:\n('scatter' or 'line')\n > "))
    
    os.chdir(all_rep_dir)
    all_rep_name=search_folder(all_rep_dir)
    df = pd.read_csv(all_rep_name[0], sep='\t')
    df1=merge_all_reports_and_times(df, metadata_dir)
    plot_s_graphics(df1, param, x_axis, y_axis, plot_type, all_rep_dir, separator)


##### Testing
all_rep_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\André\\Mestrado - Bioinfo\\2º Ano\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples\\all_reports_file_folder"
metadata_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\André\\Mestrado - Bioinfo\\2º Ano\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples\\out_files\\barcode11\\metadata_files"
param="Description"
x_axis="time elapsed"
y_axis="Cov (%)" #Cov (%)
plot_type="line" #or 'line'
separator="workflow"
directory = "out_graphs"

#main(all_rep_dir, metadata_dir, param, x_axis, y_axis, plot_type, separator)
