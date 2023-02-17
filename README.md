# Estagio_insa_scripts
Functional scripts

This repository has 2 working and functional scripts:
- mfmc_version01.py
- plotting_from_all_reports_0.py

## - mfmc_version01.py
This script was designed to run while a sequencing machine is working (generating .fastq or .fastq.gz files on a user-defined folder) to create both concatenated files (.fastq or .fastq.gz, which cumulatively store the information "read" by the sequencer and compile them into a merged file) and create the correspondant metadata .tsv file (which will come from a template metadata tsv file selected by the user). The template metadata file is also in this repository under the name "template_metadata.tsv" already filled with an example.

###### To use 'mfmc_version01.py' some packages are required:
- pandas
- getopt
- sys
- natsort


## - plotting_from_all_reports_0.py
This script was designed to create plots from the output of the Pathogen identification present in 'View all reports' tsv file. By creating plots of the processed data from the pathogen identification, the interpretation of the results get a visual support to auxiliate in the decision making.
Initially it opens the all_reports_file as a pandas dataframe so it can add columns with information such as the time taken running the previous script 'mfmc_version01.py' and the workflow codes. This is done to ensure the maximum amount of information to be plotted according to the user's preference.
Example of usage: creating a plot for each accession ID of 'Cov (%)' by 'time elapsed' so we can visualize how the coverage was increasing across time.

###### To use 'plotting_from_all_reports_0.py' some packages are required:
- pandas
- seaborn
