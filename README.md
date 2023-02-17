# This repository has 2 working and functional scripts:
The usage of this script requires Python to be installed.

## mfmc_version01.py
###### Needed package installation:
- pandas
- getopt
- sys
- natsort

This script was designed to run in command line while a sequencing machine is working (generating .fastq or .fastq.gz files on a user-defined folder) to create both concatenated files (.fastq or .fastq.gz, which cumulatively store the information "read" by the sequencer and compile them into a merged file) and create the correspondant metadata .tsv file (which will come from a template metadata tsv file selected by the user). The template metadata file is also in this repository under the name "template_metadata.tsv" already filled with an example.
The script can be used in sequencing runs with barcoding enabled or disabled, as long as that information is provided as an argument to the function (described below).

#### Script options and arguments
| options | arguments | description |
| :------: | :----: |-----------|
| `bcopt` | 'y' or 'n' | barcoding option, ***y*** (yes) or ***n*** (no), depending on the sequencer settings.|
| `ff` | 'fastq' or 'gz' | file format, which can be ***fastq*** (fastq) or ***gz*** (fastq.gz), depending on the sequencer settings.|
| `min_dir` | 'q' or directory | sequencer output folder, which can be ***q*** for the default folder or the directory of the sequencer output (i.e. 'fast_pass' for MinION), depending on the sequencer settings.|
| `out_dir` | directory | the directory for output files (the merged and metadata files created by the script). In this directory, if barcoding is enabled, a folder will be created in the specified directory for each barcode folder, containing itself two folders: 'merged_files' and 'metadata_files', each with the corresponding files. If barcoding is disabled, the specified directory will only contain the two folders, 'merged_files' and 'metadata_files', each with the corresponding files.|
| `tsv_t_n` | name | the name of the metadata template tsv file (must contain the extension of the file; i.e. 'meta_template.tsv').|
| `tsv_t_dir` | directory | the directory of the metadata template tsv file. |

***Note***: All the options need to be prefixed with "--".

##### Example of usage in command line.
> \>\>python mfmc_version01.py --bcopt y --ff gz --min_dir C:\Users\metagenomics_test\fast_pass --out_dir C:\Users\processed_data --tsv_t_n meta_template.tsv --tsv_t_dir C:\Users\metagenomics_test\metadata_templates

This would run for barcoding *enabled*, for sequecing files in the format *fastq.gz*, the sequencing files where in *C:\Users\metagenomics_test\fast_pass*, the output files were stored in *C:\Users\processed_data*, the metadata template file name was *meta_template.tsv* and the metadata template file directory was *C:\Users\metagenomics_test\metadata_templates*.


## plotting_from_all_reports_2.py
###### Needed package installation:
- pandas
- seaborn

This script was designed to run in an interactive python shell to create plots from the output of the Pathogen identification present in 'View all reports' tsv file. By creating plots of the processed data from the pathogen identification, the interpretation of the results is enhanced by having the visual support to auxiliate in the decision making.

Initially it opens the all_reports_file as a pandas dataframe so it can add columns with information such as the time taken running the previous script 'mfmc_version01.py' and the workflow codes. This is done to ensure the maximum amount of information available to be plotted according to the user's preference.
There are various parameters with the corresponding inputs in order to garantee the possibility of fully customizing the generated plots.

#### Plot settings
| parameters | options | description |
| :------: | :----: | ----------- |
| `category` | column names | Create a plot for each chosen ***category***. The possible categories are all the column names in the all_reports.tsv file. |
| `x axis` | column names | Select the category represented in the ***x axis*** of the plot. The possible categories are all the column names in the all_reports.tsv file. |
| `y axis` | column names | Select the category represented in the ***y axis*** of the plot. The possible categories are all the column names in the all_reports.tsv file. |
| `parameter` | column names | For each chosen category, see the possible possibilities of a certain ***parameter***. The possible categories are all the column names in the all_reports.tsv file. |
| `plot type` | "scatter" or "line" | Type of plot. *Note* if **line** is chosen, plots with only 1 point will appear empty. |
| `save plot` | "y" or "n" | If you want to save the generated plots in a folder. |



Example of usage: creating a plot for each accession ID of 'Cov (%)' by 'time elapsed' so we can visualize how the coverage was increasing across time.



















