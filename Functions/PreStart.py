#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Pré-Start Functions.

@author: AIR Centre
"""

### Import Libraries ############################################################################
import os
#################################################################################################
def ScriptOutput2List(ScriptOutput, ListOfOutputs):
    """
    This function adds the script's output to a list.
    Input:  ScriptOutput - Script's output as string. 
            ListOfOutputs - List, empty or not, with the string outputs from the script.
    Output: ListOfOutputs - The ScriptOutput added to the previous ListOfOutputs.
    """
    ListOfOutputs.append(ScriptOutput)
    print(ScriptOutput)
    
    return ListOfOutputs

#################################################################################################
def ScriptOutputs2LogFile(ListOfAllOutputs, FolderName):
    """
    This function saves the script's outputs as a text log file on a folder.
    Input: ListOfAllOutputs - List with all string outputs from the script.
           FolderName - Name (string) of the folder to save the text log file.
    Output: Folder with text log file with all outputs.
    """
    if not os.path.exists(FolderName):
        os.mkdir(FolderName)
    LogFileName = os.path.join(FolderName, "LogFile.txt")
    LogFile = open(LogFileName,"w") 
    LogFile.writelines(Line + "\n" for Line in ListOfAllOutputs)
    LogFile.close()

################################################################################################
def CloneModulesFromGitHub(SaveFolder):
    """
    This function clones FeLS and ACOLITE from GitHub and extracts on a folder.
    Input: SaveFolder - Name (string) of the folder to save the modules.
    Output: Modules extracted on folder.
    """
    FeLSfolder = os.path.join(SaveFolder, "fetchLandsatSentinelFromGoogleCloud-master")
    ACOLITEfolder = os.path.join(SaveFolder, "acolite-main")
    
    if not os.path.exists(FeLSfolder):
       print("\nCloning FeLS from GitHub...") 
       FeLSclone = "git clone https://github.com/EmanuelCastanho/fetchLandsatSentinelFromGoogleCloud.git " + FeLSfolder
       os.system(FeLSclone)
       print("Done.\n")

    if not os.path.exists(ACOLITEfolder):
       print("Cloning ACOLITE from GitHub...") 
       ACOLITEclone = "git clone https://github.com/acolite/acolite.git " + ACOLITEfolder
       os.system(ACOLITEclone)
       print("Done.\n")

################################################################################################