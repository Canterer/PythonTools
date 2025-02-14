import os
 
def rename_files_in_folder(folder_path, old_suffix, new_suffix):
    for filename in os.listdir(folder_path):
        if filename.endswith(old_suffix):
            os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, filename.replace(old_suffix, new_suffix)))
 

rename_files_in_folder(os.getcwd(), '.jpeg', '.ts')
