# Estagio_insa_scripts
The usage of this script requires Python to be installed.

## This repository has 2 working and functional scripts:
### - mfmc_version01.py
This script was designed to run in command line while a sequencing machine is working (generating .fastq or .fastq.gz files on a user-defined folder) to create both concatenated files (.fastq or .fastq.gz, which cumulatively store the information "read" by the sequencer and compile them into a merged file) and create the correspondant metadata .tsv file (which will come from a template metadata tsv file selected by the user). The template metadata file is also in this repository under the name "template_metadata.tsv" already filled with an example.
The script can be used in sequencing runs with barcoding enabled or disabled, as long as that information is provided as an argument to the function (described below).

#### Function arguments
- barcoding option : can be 'y' or 'n', depending on the sequencer settings (user defined).
- file format : can be 'fastq' or 'gz', depending on the sequencer settings (user defined).
- sequencer output folder: can be 'q' for the default folder or the directory of the sequencer output (i.e. 'fast_pass' for MinION), depending on the sequencer settings (user defined).
- output dir: the directory for the merged and metadata files created by the script.
- tsv template name: the name of the metadata template tsv file (must contain the extension of the file; i.e. 'meta_template.tsv').
- tsv template dir: the directory of the metadata template tsv file.
##### Example of usage in command line.
>> python mfmc_version01.py --bcopt y --ff gz --min_dir C:\Users\metagenomics_test\fast_pass --out_dir C:\Users\metagenomics_test\fast_pass C:\Users\metagenomics_test\out_files --tsv_t_n meta_template.tsv --tsv_t_dir C:\Users\metagenomics_test\metadata_templates
###### Needed package installation:
- pandas
- getopt
- sys
- natsort











### - plotting_from_all_reports_0.py
This script was designed to run in command line to create plots from the output of the Pathogen identification present in 'View all reports' tsv file. By creating plots of the processed data from the pathogen identification, the interpretation of the results get a visual support to auxiliate in the decision making.
Initially it opens the all_reports_file as a pandas dataframe so it can add columns with information such as the time taken running the previous script 'mfmc_version01.py' and the workflow codes. This is done to ensure the maximum amount of information to be plotted according to the user's preference.

Example of usage: creating a plot for each accession ID of 'Cov (%)' by 'time elapsed' so we can visualize how the coverage was increasing across time.

###### Needed package installation:
- pandas
- seaborn
