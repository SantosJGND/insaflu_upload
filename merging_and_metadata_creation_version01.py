# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 16:56:33 2023

@author: andre

Notas:
    - fazer o README e meter no github.
    - conseguir meter o título dos plots como (por exemplo) accID : X | Description: Y
    - limpar o código (tirar comentários e assim)
    - começar a escrever o relatório
    
Last update 15/02/2023 - 16:09
###############################################################################
Este é a última versão funcional com:
    - Aceita samples com e sem barcodding.
    - Aceita a pasta de 'fastq_pass' como user input.
    - Aceita a pasta de output (para guardar os ficheiros tratados) como user input.
    - Iteração pelas várias pastas de barcode que podem ir aparecendo.
    - Iteração pelos ficheiros (sem barcode) que podem ir aparecendo.
###############################################################################

AVISOS:
    - ver o erro abaixo DONE

SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame
See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
  template_tsv["sample name"][0]=""
SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame

https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
"""
import time
import os
import gzip
import pandas as pd
import getopt, sys
from natsort import natsorted

#CONSTANTS
HELP="\nArguments to the function:\n--bcopt ['y' or 'n'] : barcode option\n--ff ['fastq' or 'gz'] : file format\n--min_dir [DIRECTORY OF THE FAST_PASS] : minion file directory\n--out_dir [OUTPUT DIRECTORY or 'q' for the default]\n--tsv_t_n [TSV TEMPLATE FILE NAME]\n--tsv_t_dir [TSV TEMPLATE DIRECTORY]"
ARGUMENT_OPTIONS=["--bcopt", "--ff", "--min_dir", "--out_dir", "--tsv_t_n","--tsv_t_dir"]

#### Auxilary functions
def file_check_warning(file, file_format):
    """
    Verifies if the correct file format is being used according to the user's
    inputted file format.
    
    Takes:              Returns:
        string              bool
    """
    # run_name, run_num=get_run_info(file, file_format)
    if file_format=="gz":
        if file[-8:]!="fastq.gz":
            print("Error.\nfastq files in folder, only gz files allowed.")
            print(str(input("Remove the files and restart the script.")))

    if file_format=="fastq":
        if file[-5:]!="fastq":
            print("Error.\ngz files in folder, only fastq files allowed.")
            print(str(input("Remove the files and restart the script.")))

def get_formated_time(seconds):
    secs = seconds % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60
    secs %= 60
    return str(round(hour))+":"+str(round(mins))+":"+str(round(secs))

def get_run_info(filename, file_format):
    """
    Gets the run_name and run_num by knowing the filename and file_format.
    
    Takes:              Returns:
        str*str             str*str
    """
    if file_format=="fastq":
        max_un_index=0
        for i in range(len(filename)):
            if filename[i]=="_":
                max_un_index=i
        
        max_un_index+=1
        run_name=filename[:max_un_index]
        run_num=filename[max_un_index:-6]
        
    if file_format=="gz":
        max_un_index=0
        for i in range(len(filename)):
            if filename[i]=="_":
                max_un_index=i
        
        max_un_index+=1
        run_name=filename[:max_un_index]
        run_num=filename[max_un_index:-9]

    return run_name, run_num


#############             1 - Creating the tsv report             #############
def read_tsv_template(tsv_template_filename, tsv_temp_dir):
    os.chdir(tsv_temp_dir)
    template_tsv = pd.read_csv(tsv_template_filename, sep='\t')
    pd.options.mode.chained_assignment = None  # default='warn'
    
    template_tsv["sample name"][0]=""
    
    return template_tsv
          
def create_tsv(filename, file_format, tsv_template_filename, tsv_temp_dir, time_elapsed, metadata_dir):
    if file_format=="fastq":
        #Get sample_name
        proj_name=filename[:-6]
        
        #Create the tsv template
        tsv_temp=read_tsv_template(tsv_template_filename, tsv_temp_dir)
        pd.options.mode.chained_assignment = None  # default='warn'
        os.chdir(metadata_dir)
        tsv_temp["sample name"][0]=proj_name
        tsv_temp["time elapsed"]=time_elapsed
        
        #Save the metadata.tsv file
        ff_name=proj_name+"_metadata.tsv"
        tsv_temp.to_csv(ff_name, sep="\t", index=False)
    
    if file_format=="gz":
        #Get sample_name
        proj_name=filename[:-9]
        
        #Create the tsv template
        tsv_temp=read_tsv_template(tsv_template_filename, tsv_temp_dir)
        pd.options.mode.chained_assignment = None  # default='warn'
        os.chdir(metadata_dir)
        tsv_temp["sample name"][0]=proj_name
        tsv_temp["time elapsed"]=time_elapsed
        
        #Save the metadata.tsv file
        ff_name=proj_name+"_metadata.tsv"
        tsv_temp.to_csv(ff_name, sep="\t", index=False)

        """
        To disable the warning:
            pd.options.mode.chained_assignment = None  # default='warn'
        """

##################       2 - Going through the folder       ###################
def search_folder(cwd):
    """
    Lists all the files in the current work directory (cwd).
    
    Takes:                  Returns:
        str                     list
    """
    cur_files=os.listdir(cwd)
    return cur_files
    


########################          3 - Reading          ########################
def read_file(filename, file_format, data_storage, file_nums, run_name, run_num):
    """
    Based on the file_format, it either reads fastq or fastq.gz files.
    Reads the file 'filename' and storages all its content in a list which is
    taking all the info from each read file so it can make a merged file.
    
    Takes:                              Returns:
        str*str*lst*dic*str*str             lst
    """
    if file_format=="fastq":
        file_nums.append(str(run_num))
        try:
            fh=open(filename, mode="r")
        except:
            return print("File doesnt exist.")
        lines=fh.read().splitlines()
        while lines!=[]:
            seq_id=lines.pop(0)
            raw_seq=lines.pop(0)
            plus_s=lines.pop(0)
            qual_vals=lines.pop(0)
            b=[seq_id,raw_seq,plus_s,qual_vals]
            data_storage.extend(b)
        return data_storage
    
    if file_format=="gz":
        file_nums.append(str(run_num))
        try:
            fh=gzip.open(filename, mode="rb")
        except:
            return print("File doesnt exist.")
        lines=fh.read().splitlines()
        while lines!=[]:
            seq_id=lines.pop(0).decode()
            raw_seq=lines.pop(0).decode()
            plus_s=lines.pop(0).decode()
            qual_vals=lines.pop(0).decode()
            b=[seq_id,raw_seq,plus_s,qual_vals]
            data_storage.extend(b)
        return data_storage
    


########################          4 - Writing          ########################
def write_new_data(new_file_name, file_format, file_nums, new_info, run_name):
    """
    Takes the new file name given as argument, the file format, the list of 
    all the information read so far (new_info) and creates a new 'merged' file
    of the same format which has all the information from the files read so far.
    It returns the merged name so it can be used to name the metadata file of
    this merged file.
    
    Takes:                              Returns:
        str*str*lst*lst*str                 str
    """
    if file_format=="fastq":
        merged_name=run_name
        merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq"

        fh=open(merged_name, "w")
        for a in new_info:
            fh.write(a+"\n")
        fh.close()
        return merged_name
    
    if file_format=="gz":
        merged_name=run_name
        merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq.gz"

        fh=gzip.open(merged_name, "wb")
        for a in new_info:
            m=a+"\n"
            fh.write(m.encode())
        fh.close()
        return merged_name


####################          5 - Main functions          #####################
"""For barcodded samples"""  
def pre_main_bar(bar_dir, barcode, already_processed_data_dic, pross_numbers, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir):
    #Directory of the fastq.gz files from the MinIon
    fastq_dir=bar_dir
    os.chdir(fastq_dir)

    #This storages all the lines read from each fastq.gz files to create the merged.
    data_storage=[]

    folder_files_=search_folder(fastq_dir)
    
    folder_files = natsorted(folder_files_)
    # print(natsort_file_names)
    
    if folder_files==[]:
        print("Folder is empty")
    
    else:
        print("Folder not empty")
     
        #This prompts a message after checking if the file format is according to the user input. 
        file_check_warning(folder_files[0], file_format)
        
        for file in folder_files:
            
            if file not in already_processed_data_dic[barcode]:
                
                #Adding the information about the already read data to the dictionary.
                already_processed_data_dic[barcode].append(file)
                
                print("new_file_name:", file)
                
                
                #Get universal run_name and run_number
                run_name, run_num= get_run_info(file, file_format)
                
                
                if barcode not in pross_numbers:
                    pross_numbers[barcode]=[]
                
                #Reads gz file
                new_info=read_file(file, file_format, data_storage, pross_numbers[barcode], run_name, run_num)
                
                #Directory of the merged gz files
                merged_gz_dir=os.path.join(out_bar_dir,"merged_files")
                
                if not os.path.exists(merged_gz_dir):   #para verificar se existe o ficheiro/pasta
                    os.makedirs(merged_gz_dir)
                os.chdir(merged_gz_dir)
                merged_name=write_new_data(file, file_format, pross_numbers[barcode], new_info, run_name)
                
                
                
                ### METADATA ###
                #Directory of the metadata
                metadata_dir=os.path.join(out_bar_dir,"metadata_files")
                
                #Create the metadata dir if it doesnt exists
                if not os.path.exists(metadata_dir):
                    os.makedirs(metadata_dir)
                    
                #Go to the metadata dir
                os.chdir(metadata_dir)
                
                #Fill the file with information under"
                end_time=time.time()
                total_time=end_time-start_time
                ft=get_formated_time(total_time)
                create_tsv(merged_name, file_format, tsv_temp_name, tsv_temp_dir, ft, metadata_dir)
                
                
                ### FASTQ FILES ###
                #Directory of the fastq.gz files from the MinIon
                fastq_dir=bar_dir
                os.chdir(fastq_dir)
    
            else:
                print("File already added.")
                
    return already_processed_data_dic
   
def main_w_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir):
    start_time=time.time()
    
    run_num=0
    
    pross_nums={}
    already_processed_data={}
    
    while(True):
        print(f"\nRun {run_num}")
    
        #Directory of the sample files (barcode00, barcode01, etc)
        os.chdir(minion_file_dir)
        bc_folders=search_folder(minion_file_dir)
        
        for barcode in bc_folders:
            
            out_bar_dir=os.path.join(out_files_dir, barcode)
            if not os.path.exists(out_bar_dir):
                os.makedirs(out_bar_dir)
                
                
            if barcode not in already_processed_data.keys():
                already_processed_data[barcode]=[]
                
            print("looking in folder: ", barcode)
            nwd=minion_file_dir+"\\"+barcode
            
            already_processed_data=pre_main_bar(nwd, barcode, already_processed_data, pross_nums, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir)
               
            print()
    
        run_num+=1
        time.sleep(5)
                
     
        
"""For non-barcodded samples"""
def pre_main_no_bar(minion_file_dir, already_processed_data_dic, pross_numbers, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir):
    #Directory of the fastq.gz files from the MinIon
    os.chdir(minion_file_dir)

    #This storages all the lines read from each fastq.gz files to create the merged.
    data_storage=[]

    folder_files_=search_folder(minion_file_dir)
    
    folder_files = natsorted(folder_files_)
    # print(natsort_file_names)
    
    if folder_files==[]:
        print("Folder is empty")
    
    else:
        print("Folder not empty")
     
        #This prompts a message after checking if the file format is according to the user input. 
        file_check_warning(folder_files[0], file_format)
        
        for file in folder_files:
            
            if file not in already_processed_data_dic:
                
                #Adding the information about the already read data to the dictionary.
                already_processed_data_dic.append(file)
                
                print("new_file_name:", file)
                
                ### MERGED ###
                #Get universal run_name and run_number
                run_name, run_num= get_run_info(file, file_format)
                
                #Reads gz file
                new_info=read_file(file, file_format, data_storage, pross_numbers, run_name, run_num)
                
                #Directory of the merged gz files
                merged_gz_dir=os.path.join(out_bar_dir,"merged_files")
                
                if not os.path.exists(merged_gz_dir):   #para verificar se existe o ficheiro/pasta
                    os.makedirs(merged_gz_dir)
                os.chdir(merged_gz_dir)
                merged_name=write_new_data(file, file_format, pross_numbers, new_info, run_name)
                
                
                
                ### METADATA ###
                #Directory of the metadata
                metadata_dir=os.path.join(out_bar_dir,"metadata_files")
                
                #Create the metadata dir if it doesnt exists
                if not os.path.exists(metadata_dir):
                    os.makedirs(metadata_dir)
                    
                #Go to the metadata dir
                os.chdir(metadata_dir)
                
                #Fill the file with information under
                end_time=time.time()
                total_time=end_time-start_time
                ft=get_formated_time(total_time)
                create_tsv(merged_name, file_format, tsv_temp_name, tsv_temp_dir, ft, metadata_dir)
                
                ### FASTQ FILES ###
                #Directory of the fastq.gz files from the MinIon
                os.chdir(minion_file_dir)
    
            else:
                print("File already added.")
                
    return already_processed_data_dic

def main_no_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir):
    start_time=time.time()
    
    run_num=0
    
    pross_nums=[]
    already_processed_data=[]
    
    while(True):
        print(f"\nRun {run_num}")
    
        already_processed_data=pre_main_no_bar(minion_file_dir, already_processed_data, pross_nums, file_format, start_time, out_files_dir, tsv_temp_name, tsv_temp_dir)
           
        print()
    
        run_num+=1
        time.sleep(5)




def main(bar_code_option, file_format, minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir):
    """
    INSTRUCTIONS:
        
    bar_code_option - 'y' or 'n'
    
    file_format - 'fastq' or 'gz'
    
    minion_file_dir - fast_pass directory
    
    output_dir - output files directory or 'q'. 
                 If 'q':
                     Creates a 'out_files' folder in the same folder of the 'fast_pass'.
    
                 Else: 
                     Create a folder called 'out_files' 
                     with 2 folders: 'merged_files' and 'metadata_files' which will
                     have the corresponding output files.
    """
    input("Press any key to start the script.")
    if output_dir!="q":
        out_files_dir=os.path.join(output_dir,"out_files")
    else:
        os.chdir(minion_file_dir)
        os.chdir('..')
        cwd=os.getcwd()
        out_files_dir=os.path.join(cwd,"out_files")
        
    if not os.path.exists(out_files_dir):
        os.makedirs(out_files_dir)
    
    if bar_code_option=="y":
        main_w_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir)
    if bar_code_option=="n":
        main_no_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir)
     

############################ SYSTEM STUFF ##########################
"""
#h:b:f:m:
"""

def main_main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["Help","bcopt=", "ff=", "min_dir=", "out_dir=", "tsv_t_n=","tsv_t_dir="])
        # print()
        # print("#######")
        # print('ARGV      :', sys.argv[1:])
        # print ('OPTIONS   :', opts)
        # print("#######")
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    used_args={}
    output = None
    verbose = False
    
    used_args={}
    barcode_option=None
    file_format=None
    minion_file_dir=None
    output_dir=None
    tsv_temp_name=None
    tsv_temp_dir=None
    
    used_args={"--bcopt":None,
                "--ff":None,
                "--min_dir":None,
                "--out_dir":None,
                "--tsv_t_n":None,
                "--tsv_t_dir":None}
    
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--Help"):
            print(HELP)
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        elif o in ("--bcopt"):
            bar_code_option=a
            used_args[o]=a
        elif o in ("--ff"):
            file_format=a
            used_args[o]=a
        elif o in ("--min_dir"):
            minion_file_dir=a
            used_args[o]=a
        elif o in ("--out_dir"):
            output_dir=a
            used_args[o]=a
        elif o in ("--tsv_t_n"):
            tsv_temp_name=a
            used_args[o]=a
        elif o in ("--tsv_t_dir"):
            tsv_temp_dir=a
            used_args[o]=a
        else:
            assert False, "unhandled option"
    
    res=True
    for key in used_args.keys():
        if used_args[key]==None:
            print(f"{key} argument is missing.")
            res=False
    
    if res==True:
        main(bar_code_option, file_format, minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir)
    else:
        return
            

if __name__ == "__main__":
    main_main()










### TESTING
# bar_code_option="y"
# file_format="fastq"
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples\\fastq_test_files"
# output_dir="q"
# output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"

# main(bar_code_option, file_format, minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir)


# # ##### Testing
# bar_code_option="y"
# file_format="gz"
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples\\20221110_metagenomics_test_gz"
# output_dir="q"
# output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"

# main(bar_code_option, file_format, minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir)






