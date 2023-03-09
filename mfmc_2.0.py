# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 14:20:20 2023

@author: andre
"""

import time
import os
import gzip
import pandas as pd
import getopt, sys
import shutil
from natsort import natsorted

"""
Notes:
- Now automatically detects if there's barcoding or not and also the format.
- Now it always creates .fastq.gz merged files.

TO DO:
- de sleep em sleep fazer uma pasta com 'lattest_compilation_to_upload' todos os últimos concatenados por amostra 
(barcode10, barcode11, etc) + um ficheiro de metadata com todos os dados respetivos dos concatenados totais.

"""

#CONSTANTS
HELP=" _________________________________________________\n | mfmc.py - MERGING FASTQ AND METADATA CREATION | \n _________________________________________________\nExample of usage:\npython mfmc.py --in_dir C:\\users\\samples --out_dir C:\\users\processed_files --tsv_t_name template.tsv --tsv_t_dir C:\\users\\templates \n\nOptions and arguments:\n--in_dir [DIRECTORY OF THE FAST_PASS] : directory of the files being produced by the sequencing machine (typically the 'fast_pass' folder).\n--out_dir [OUTPUT DIRECTORY or 'q' for the default] : desired directory to storage the output files\n--tsv_t_n [TSV TEMPLATE FILE NAME] : name of the tsv template\n--tsv_t_dir [TSV TEMPLATE DIRECTORY] : directory of the tsv template file\n--sleep [TIME SLEEP] : amount of time (in seconds) for the script to hold, between search cycles"
ARGUMENT_OPTIONS=["--in_dir", "--out_dir", "--tsv_t_n","--tsv_t_dir"]

#### Auxilary functions
def find_barcode_and_ff(fastq_dir):
    res=None
    path_content=os.listdir(fastq_dir)
    for c in path_content:
        if c[-2:]=="gz":
            res=(False, "gz")
            return res
        elif c[-5:]=="fastq":
            res=(False, "fastq")
            return res
        else:
            new_dir=os.path.join(fastq_dir, c)
            _ = os.listdir(new_dir)
            for aaa in _:
                if aaa[-2:]=="gz":
                    res=(True, "gz")
                    return res
                elif aaa[-5:]=="fastq":
                    res=(True, "fastq")
                    return res
                    
    
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

def get_lattest_comp():
    pass

#############             1 - Creating the tsv report             #############
def read_tsv_template(tsv_template_filename, tsv_temp_dir):
    os.chdir(tsv_temp_dir)
    template_tsv = pd.read_csv(tsv_template_filename, sep='\t')
    pd.options.mode.chained_assignment = None  # default='warn'
    
    template_tsv["sample name"][0]=""
    template_tsv["fastq1"][0]=""
    template_tsv["fastq2"][0]=""
    
    return template_tsv
          
def create_tsv(filename, file_format, tsv_template_filename, tsv_temp_dir, time_elapsed, metadata_dir):
    if file_format=="fastq":
        #Get sample_name
        proj_name=filename[:-6]
        
        ff_name=proj_name+"_metadata.tsv"
        
        #Create the tsv template
        tsv_temp=read_tsv_template(tsv_template_filename, tsv_temp_dir)
        pd.options.mode.chained_assignment = None  # default='warn'
        os.chdir(metadata_dir)
        tsv_temp["sample name"][0]=proj_name
        tsv_temp["fastq1"][0]=filename
        tsv_temp["time elapsed"]=time_elapsed
        
        #Save the metadata.tsv file
        ff_name=proj_name+"_metadata.tsv"
        tsv_temp.to_csv(ff_name, sep="\t", index=False)
    
    if file_format=="gz":
        #Get sample_name
        proj_name=filename[:-9]
        ff_name=proj_name+"_metadata.tsv"
        
        #Create the tsv template
        tsv_temp=read_tsv_template(tsv_template_filename, tsv_temp_dir)
        pd.options.mode.chained_assignment = None  # default='warn'
        os.chdir(metadata_dir)
        tsv_temp["sample name"][0]=proj_name
        tsv_temp["time elapsed"]=time_elapsed
        tsv_temp["fastq1"][0]=filename
        
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
def read_and_write(filename, file_format, last_file_read, file_nums, run_name, run_num, fastq_dir, merged_gz_dir):
    """
    Based on the file_format, it either reads fastq or fastq.gz files.
    Reads the file 'filename' and storages all its content in a list which is
    taking all the info from each read file so it can make a merged file.
    
    Takes:                              Returns:
        str*str*lst*dic*str*str             lst
    """
    if last_file_read==[]:
        os.chdir(fastq_dir)
        
        run_name, run_num=get_run_info(filename, file_format)
        
        file_nums.append(str(run_num))
        #print("file_nums: ", file_nums)
        
        if file_format=="fastq":
            
            merged_name=run_name
            merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq.gz"
            
            
            #Reading the file
            try:
                fhr=open(filename, mode="r")
            except:
                return print("File doesnt exist.")
            lines=fhr.read().splitlines()
            
            #Writing
            os.chdir(merged_gz_dir)
            
            fhw=gzip.open(merged_name, "ab")
            while lines!=[]:
                seq_id=lines.pop(0)
                m=seq_id+"\n"
                fhw.write(m.encode())
                
                raw_seq=lines.pop(0)
                m=raw_seq+"\n"
                fhw.write(m.encode())
                
                plus_s=lines.pop(0)
                m=plus_s+"\n"
                fhw.write(m.encode())
                
                qual_vals=lines.pop(0)
                m=qual_vals+"\n"
                fhw.write(m.encode())
            
            fhr.close()
            fhw.close()
            
            last_file_read.append(merged_name)
        
    
            
        if file_format=="gz":
            
            merged_name=run_name
            merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq.gz"
            
            print()
            print("filename:",filename)
            print("merged_name:", merged_name)
            
            
            #Reading the file
            try:
                print("try: ", filename)
                fhr=gzip.open(filename, mode="rb")
            except:
                return print("(gz) File doesnt exist.")
            lines=fhr.read().splitlines()
            
            #Writing
            os.chdir(merged_gz_dir)
            
            fhw=gzip.open(merged_name, "ab")
            while lines!=[]:
                seq_id=lines.pop(0).decode()
                m=seq_id+"\n"
                fhw.write(m.encode())
                
                raw_seq=lines.pop(0).decode()
                m=raw_seq+"\n"
                fhw.write(m.encode())
                
                plus_s=lines.pop(0).decode()
                m=plus_s+"\n"
                fhw.write(m.encode())
                
                qual_vals=lines.pop(0).decode()
                m=qual_vals+"\n"
                fhw.write(m.encode())
    
            fhr.close()
            fhw.close()
            
            last_file_read.append(merged_name)
            
    
    else:
        os.chdir(fastq_dir)
        
        run_name, run_num=get_run_info(filename, file_format)
        
        file_nums.append(str(run_num))
        #print("file_nums: ", file_nums)
        
        if file_format=="fastq":
            
            merged_name=run_name
            merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq.gz"
            
            
            #Reading the file
            try:
                fhr=open(filename, mode="r")
            except:
                return print("File doesnt exist.")
            lines=fhr.read().splitlines()
            
            
            #Writing
            os.chdir(merged_gz_dir)
            shutil.copyfile(last_file_read[-1], merged_name)
            
            fhw=gzip.open(merged_name, "ab")
            while lines!=[]:
                seq_id=lines.pop(0)
                m=seq_id+"\n"
                fhw.write(m.encode())
                
                raw_seq=lines.pop(0)
                m=raw_seq+"\n"
                fhw.write(m.encode())
                
                plus_s=lines.pop(0)
                m=plus_s+"\n"
                fhw.write(m.encode())
                
                qual_vals=lines.pop(0)
                m=qual_vals+"\n"
                fhw.write(m.encode())
            
            fhr.close()
            fhw.close()
            
            last_file_read.append(merged_name)
            
            
        if file_format=="gz":
            
            merged_name=run_name
            merged_name+=str(file_nums[0])+"-"+str(file_nums[-1])+".fastq.gz"
            
    
            #Reading the file
            try:
                fhr=gzip.open(filename, mode="rb")
            except:
                return print("File doesnt exist.")
            lines=fhr.read().splitlines()
            
            #Writing
            os.chdir(merged_gz_dir)
            shutil.copyfile(last_file_read[-1], merged_name)
            
            fhw=gzip.open(merged_name, "ab")
            while lines!=[]:
                seq_id=lines.pop(0).decode()
                m=seq_id+"\n"
                fhw.write(m.encode())
                
                raw_seq=lines.pop(0).decode()
                m=raw_seq+"\n"
                fhw.write(m.encode())
                
                plus_s=lines.pop(0).decode()
                m=plus_s+"\n"
                fhw.write(m.encode())
                
                qual_vals=lines.pop(0).decode()
                m=qual_vals+"\n"
                fhw.write(m.encode())
    
            fhr.close()
            fhw.close()
            
            last_file_read.append(merged_name)
            
    print("read_write (merged_name): ", merged_name)
    return merged_name
    
####################          5 - Main functions          #####################
"""For barcodded samples"""  
def pre_main_bar(bar_dir, barcode, already_processed_data_dic, pross_numbers, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir):
    #Directory of the fastq.gz files from the MinIon
    fastq_dir=bar_dir
    os.chdir(fastq_dir)

    last_file_read=[]

    folder_files_=search_folder(fastq_dir)
    
    folder_files = natsorted(folder_files_)
    # print(natsort_file_names)
    
    if folder_files==[]:
        print("Folder is empty")
    
    else:
        print("Folder not empty")
     
        
        for file in folder_files:
            
            if file not in already_processed_data_dic[barcode]:
                
                #Adding the information about the already read data to the dictionary.
                already_processed_data_dic[barcode].append(file)
                
                print("new_file_name:", file)
                
                
            
                if barcode not in pross_numbers:
                    pross_numbers[barcode]=[]
                
                ### MERGED FILES ###
                
                #Get universal run_name and run_number
                run_name, run_num= get_run_info(file, file_format)
                
                #Directory of the merged gz files
                merged_gz_dir=os.path.join(out_bar_dir,"merged_files")
                
                if not os.path.exists(merged_gz_dir):   #para verificar se existe o ficheiro/pasta
                    os.makedirs(merged_gz_dir)
                os.chdir(merged_gz_dir)
                
                #Read and write
                merged_name=read_and_write(file, file_format, last_file_read, pross_numbers[barcode], run_name, run_num, fastq_dir, merged_gz_dir)
                
                print("pre_main: ", merged_name)
                
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
   
def main_w_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir, sleep_time):
    start_time=time.time()
    
    default_sleep=5
    real_sleep=0
    if sleep_time!=None:
        real_sleep=sleep_time
    else:
        real_sleep=default_sleep
    
    
    run_num=0
    
    pross_nums={}
    already_processed_data={}
    
    # while(True):
    while run_num<=1: #Testing automatic, erase later
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
            nwd=os.path.join(minion_file_dir, barcode)
            
            already_processed_data=pre_main_bar(nwd, barcode, already_processed_data, pross_nums, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir)
               
            print()
    
        run_num+=1
        time.sleep(int(real_sleep))
                
     
        
"""For non-barcodded samples"""
def pre_main_no_bar(minion_file_dir, already_processed_data_dic, pross_numbers, file_format, start_time, out_bar_dir, tsv_temp_name, tsv_temp_dir):
    #Directory of the fastq.gz files from the MinIon
    fastq_dir=minion_file_dir
    os.chdir(minion_file_dir)

    #This storages all the lines read from each fastq.gz files to create the merged.
    last_file_read=[]

    folder_files_=search_folder(minion_file_dir)
    
    folder_files = natsorted(folder_files_)
    # print(natsort_file_names)
    
    if folder_files==[]:
        print("Folder is empty")
    
    else:
        print("Folder not empty")
     
        
        for file in folder_files:
            
            if file not in already_processed_data_dic:
                
                #Adding the information about the already read data to the dictionary.
                already_processed_data_dic.append(file)
                
                print("new_file_name:", file)
                
                ### MERGED FILES ###
                
                #Get universal run_name and run_number
                run_name, run_num= get_run_info(file, file_format)
                
                #Directory of the merged gz files
                merged_gz_dir=os.path.join(out_bar_dir,"merged_files")
                
                if not os.path.exists(merged_gz_dir):   #para verificar se existe o ficheiro/pasta
                    os.makedirs(merged_gz_dir)
                os.chdir(merged_gz_dir)
                
                #Read and write
                merged_name=read_and_write(file, file_format, last_file_read, pross_numbers, run_name, run_num, fastq_dir, merged_gz_dir)
                
                
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

def main_no_bar(file_format, minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir, sleep_time):
    start_time=time.time()
    
    default_sleep=5
    real_sleep=0
    if sleep_time!=None:
        real_sleep=sleep_time
    else:
        real_sleep=default_sleep
    
    run_num=0
    
    pross_nums=[]
    already_processed_data=[]
    
    # while(True):
    while run_num<=1: #Testing automatic, erase later
        print(f"\nRun {run_num}")
    
        already_processed_data=pre_main_no_bar(minion_file_dir, already_processed_data, pross_nums, file_format, start_time, out_files_dir, tsv_temp_name, tsv_temp_dir)
           
        print()
    
        run_num+=1
        time.sleep(int(real_sleep))




def main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time):
    input("\nPress any key to start the script.")
    if output_dir!="q":
        out_files_dir=os.path.join(output_dir,"out_files")
    else:
        os.chdir(minion_file_dir)
        os.chdir('..')
        cwd=os.getcwd()
        out_files_dir=os.path.join(cwd,"out_files")
        
    if not os.path.exists(out_files_dir):
        os.makedirs(out_files_dir)
    
    res=find_barcode_and_ff(minion_file_dir)
    
    if res[0]==True:
        main_w_bar(res[1], minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir, sleep_time)
    else:
        main_no_bar(res[1], minion_file_dir, out_files_dir, tsv_temp_name, tsv_temp_dir, sleep_time)
        

############################ SYSTEM STUFF ##########################
"""
#h:b:f:m:
"""

def main_main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["Help", "in_dir=", "out_dir=", "tsv_t_n=","tsv_t_dir=", "sleep="])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    
    used_args={}
    minion_file_dir=None
    output_dir=None
    tsv_temp_name=None
    tsv_temp_dir=None
    sleep_time=None
    
    used_args={"--in_dir":None,
                "--out_dir":None,
                "--tsv_t_n":None,
                "--tsv_t_dir":None,
                "--sleep":None}
    
    for o, a in opts:
        if o in ("-h", "--Help"):
            print(HELP)
            sys.exit()
        elif o in ("--in_dir"):
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
        elif o in ("--sleep"):
            sleep_time=a
            used_args[o]=a
        else:
            assert False, "unhandled option"
    
    res=True
    for key in used_args.keys():
        if used_args[key]==None and key!="--sleep":
            print(f"{key} argument is missing.")
            res=False
    
    if res==True:
        main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time)
    else:
        return
            

if __name__ == "__main__":
    main_main()









# TESTING

# # print("barcoding on and gz")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_gz_bar\\fastq_gz_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding off and gz")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_gz_n_bar\\fastq_gz_n_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding on and fastq")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_bar\\fastq_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding off and fastq")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\1º Ano\\2º Semestre\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_n_bar\\fastq_n_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\1º Ano\\2º Semestre\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)



