# Mike Hugman, February 2014
#
# Given a curl command, this script will pare down the headers and parameters to only the ones that are necessary to get the same response. 
# It first removes the headers, then the parameters, one by one and checks at each stage to see if the output is the same. If the output
# is not the same without that header/parameter, it is assumed to be necessary. 

import re
import subprocess
import sys
import os

def getOutput(newHeaders, fullHeaders, newParams, fullParams, newCurl, binaryData): 
    
    returnString = ""
       
    if newHeaders == [] and len(fullHeaders) > 0 : 
        returnString += "\n" + "\n" + "None of the headers are necessary." + "\n"
    elif len(fullHeaders) == 0 :
        returnString += "\n" + "\n" + "There were no headers." + "\n"
    else: 
        returnString += "\n" + "\n" + str(len(newHeaders)) + " out of " + str(len(fullHeaders)) + " headers are necessary." 
        returnString += "\n" + "The necessary headers are:" 

        # Construct a list of the necessary headers from "newHeaders"
        for header in newHeaders:
            returnString += "\n" + "\n" + "\t" + "Necessary Header:" + re.sub(r"(?s)^(.*?):.*$", r"\1", header)
            returnString += "\n" + "\t" + "Value:" + re.sub(r"(?s)^.*?:(.*)$", r"\1", header)
        
    if newParams == []  and len(fullParams) > 0 : 
        returnString += "\n" + "\n" + "None of the parameters are necessary." "\n"
    elif len(fullParams) == 0 : 
        returnString += "\n" + "\n" + "There were no parameters." + "\n"
    else: 

        returnString += "\n" + "\n" + str(len(newParams)) + " out of " +  str(len(fullParams)) + " parameters are necessary." 
        returnString += "\n" + "The necessary parameters are:" 
        # Construct a list of the necessary parameters from "newParams"
        for param in newParams:
            returnString += "\n" + "\n" + "\t" + "Necessary Parameter:" + param[0]
            returnString += "\n" + "\t" + "Value: " + param[1]

    if len(binaryData) > 0 and re.search(r"--data-binary\s*'([^']*)'", newCurl): 
    
        
    
        #seeUnnecessary = raw_input("Do you want to see the parameters that were not necessary? (y/n)")
        seeUnnecessary = "y"
    
        if seeUnnecessary == "y": 
            unnecessaryParams = [x for x in fullParams if newParams.count(x) == 0 ]
        
            for param in unnecessaryParams :
                returnString += "\n" + "\n" + "\t" + "Unnecessary Parameter:" +  param[0]
                returnString += "\n" + "\t" + "Value: " + param[1]
    
        returnString += "\n" + "\n" + "New curl with the unnecessary headers and parameters removed: "
        returnString += "\n" + newCurl

    return returnString


# We can't just have the user directly input the curl because it is often too long and will get truncated. Instead they have to create
# a text file containing (only) the curl and place it in the same directory as this script
nameOfFile = raw_input("Enter the name of the file with the curl in it (put the file in the folder /curlInput/ in same directory as script):")
fullCurl = open(os.path.abspath(os.curdir) + "/curlInput/" + nameOfFile, "r").read()

#fullCurl = raw_input("Enter the cURL: ")

#########################################################################################################
# Massage the input into correct format for "subprocess" - each command must be a separate item in a list
#########################################################################################################

fullCurl = fullCurl.replace("curl", "")
fullCurl = fullCurl.replace("--compressed", "")

# request URL is the second item in the command
requestUrl = re.sub(r"(?s)^.*?'(.*?)'.*$", r"\1", fullCurl)
fullCurlSeparated = ['curl', requestUrl]

# get all the headers in the command (labelled with a "-H")
fullHeaders = re.findall(r"-H\s*'([^']*)'", fullCurl)

# get all the form data (labelled with a "--data"), if there is any
try:
    fullData = re.findall(r"--data\s*'([^']*)'", fullCurl)[0]
except: 
    fullData = ''

# Sometimes the curl will have binary form data - we're going to assume it is "all or nothing" and can't be parsed
try:
    binaryData = re.findall(r"--data-binary\s*'([^']*)'", fullCurl)[0]
except: 
    binaryData = ''

for header in fullHeaders : 
    fullCurlSeparated.append('-H')
    fullCurlSeparated.append(header)
    
if len(fullData) > 0: 
    fullCurlSeparated.append('--data')
    fullCurlSeparated.append(fullData)

if len(binaryData) > 0: 
    fullCurlSeparated.append('--data-binary')
    fullCurlSeparated.append(binaryData)

fullCurlSeparated.append('--compressed')

######################################################
# Now generate a list of parameters with the form data
######################################################

firstParam = re.findall(r"^([^=]*)=([^&]*)", fullData)
restofParams = re.findall(r"&([^=]*)=([^&]*)", fullData)
fullParams = firstParam + restofParams

#########################################################################################################
# This will give us the output of the full curl command - we will compare our subsequent output to this. 
#########################################################################################################
fullOutput = subprocess.check_output(fullCurlSeparated)
newCurlSeparated = fullCurlSeparated

raise ValueError(type(fullOutput))

#####################################################################
# First, try removing headers one by one to see if they are necessary. 
#####################################################################

newHeaders = fullHeaders[:]
for header in fullHeaders : 
    
    # We're keeping track of two things here: a list of the necessary headers, and the headers with newCurlSeparated
    # hence the need for two indices. There's probably a way to simplify this. 

    removedHeaderIndex_1 = newHeaders.index(header)
    newHeaders.remove(header)
    
    # try removing one of the headers
    # get index of that removed header so we can insert it back in in the same place if necessary
    removedHeaderIndex_2 = newCurlSeparated.index(header)    
    removedHeader = newCurlSeparated.pop(removedHeaderIndex_2)    

    # Remove the header's label, which is located one place before the value
    removedHeaderLabel = newCurlSeparated.pop(removedHeaderIndex_2 - 1)
    
    # test the new curl without that header, compare it to the output of the full curl 
    newOutput = subprocess.check_output(newCurlSeparated)
        
    # if the output with that header removed is not the same, we shouldn't have removed it - put it back in. 
    if newOutput != fullOutput : 
        
        newCurlSeparated.insert(removedHeaderIndex_2 - 1, removedHeaderLabel)
        newCurlSeparated.insert(removedHeaderIndex_2, removedHeader)
        newHeaders.insert(removedHeaderIndex_1, header)

#######################################################
# Next, do the same for the parameters in the form data
#######################################################

newParams = fullParams[:]
for param in fullParams :
    newData = "" 
    
    oldData = newCurlSeparated[newCurlSeparated.index('--data') + 1]

    removedParamIndex = newParams.index(param)
    newParams.remove(param)
    
    # Construct a new form data string, removing that parameter    
    for np in newParams: 

        newData = newData + "&" + np[0] + "=" + np[1]

    # remove ampersand at beginning
    newData = newData[1:]     
    newCurlSeparated[newCurlSeparated.index('--data') + 1] = newData
              
    # test the new curl without that parameter, compare it to the output of the full curl 
    newOutput = subprocess.check_output(newCurlSeparated)
        
    # if the output with that parameter removed is not the same, we shouldn't have removed it - put it back in.
    # Also put the old data back in to newCurlSeparated 
    if newOutput != fullOutput : 
        newParams.insert(removedParamIndex, param)
        newCurlSeparated[newCurlSeparated.index('--data') + 1] = oldData

############################################################################
# Now we're going to see if the binary data is necessary (it probably is)
############################################################################


if len(binaryData) > 0: 
    binaryData = newCurlSeparated[newCurlSeparated.index('--data-binary') + 1]
    newCurlSeparated[newCurlSeparated.index('--data-binary') + 1] = ''

    # test the new curl without the binary data, compare it to the output of the full curl 
    newOutput = subprocess.check_output(newCurlSeparated)

    # if the output with the binary data removed is not the same, we shouldn't have removed it - put it back in.
    if newOutput != fullOutput :
        newCurlSeparated[newCurlSeparated.index('--data-binary') + 1] = binaryData



##########################################################################################################
# construct a list of the necessary headers and parameters to return to the user
# Also turn the separated curl into a regular, non-separated curl that you can paste into the command line
##########################################################################################################

# Create a file to output to if the user would like (some output will be really long and inconvenient to view in window)

newCurl = ''
for item in newCurlSeparated: 
    
    # add quotes to the values but not the labels
    if item != 'curl':
        item = re.sub(r"^\s*(?!-+[A-Za-z]+)(.*)$", r"'\1'", item)
    newCurl = newCurl + ' ' + item



output = getOutput(newHeaders, fullHeaders, newParams, fullParams, newCurl, binaryData)

shouldWeOutputToFile = raw_input("Would you like to output to a file? (y/n)")

if shouldWeOutputToFile == "y": 

    outputFile = file(os.path.abspath(os.curdir) + "/curlOutput/" + "output-" + nameOfFile, "w")
    outputFile.write(output)
    outputFile.close()

    print "Output written to file: " + os.path.abspath(os.curdir) + "/curlOutput/"+ "output-" + nameOfFile

else: 
    print output








   
