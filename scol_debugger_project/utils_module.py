import subprocess
import re
import os
import string
import datetime

# P: Takes a filename containing command line as input
# T: Read command line from the file, if file is empty it prompts for input
# R: Returns a list of string containing the command line
def InputCommand(filename):
    file = open(filename, "r")
    command = file.read().rstrip().split()
    if not command or command[0].lower() != "supercollider":
        command = input("Enter commandline: ").rstrip().split()
    file.close()
    return command


# P: Takes a list containing command line as input
# T: Prompts a user to set timeout value in seconds
# R: Returns a list of command
def setTimeOutValue(command):
    timeoutValue = int(input("Set timeout secs (Enter 0 to proceed without timeout): "))
    if timeoutValue > 0:
        timeout = f"timeout {timeoutValue}s "
        command = (timeout + " ".join(command)).split()
    return command


# P: Takes a list containing a command line as input
# T: run the command line process
# R: returns the name of the new log file created by the executed process
def runProcess(command):
    path = os.getcwd()
    prevFiles = set(os.listdir(path))
    subprocess.run(command, capture_output=True, text=True)
    currFiles = set(os.listdir(path))
    newFile = currFiles - prevFiles
    if len(newFile) > 0:
        newFile1 = list(newFile)[0]
    return newFile1


# P: Takes a log file name as input and boolean delete parameter
# T: Reads content of the log file into a string and organize the log file into the log folder or delete it
# R: Returns the content of the log file
def accessLogFile(filename, delete=False):
    file = open(filename, "r")
    content = file.read()
    file.close()
    # Get filepath
    name = os.name
    cwd = os.getcwd()
    if name == "posix":
        filePath = f"{cwd}/{filename}"
        destinationDir = f"{cwd}/logs"
    else:
        filePath = f"{cwd}\{filename}"
        destinationDir = f"{cwd}\logs"
    # delete the file
    if delete:
        os.remove(filePath)
    else:
        # move file to logs folder
        filename = os.path.basename(filePath)
        destFilePath = os.path.join(destinationDir, filename)
        os.rename(filePath, destFilePath)
    return content


# P: Takes content of a log file as input
# T: Find error causing parameters in the log file content
# R: returns a list containing errors found
def findError(logContent):
    # ==== ADD NEW REGEX TO THE LIST BELOW FOR NEW ERROR SIGNATURES ====
    errorsSigRegex = [r'ERROR:(.*)']
    # ==================================================================
    errorLst = []
    for regex in errorsSigRegex:
        error = re.findall(regex, logContent, re.MULTILINE)
        errorLst = list(set(errorLst + error))
    return errorLst

# P: Takes a single parameter commandLst, which is a list of strings representing the command line
# T: This function splits the command line arguments into three separate list
# R: This function returns a list containing the three output lists: [paramLst, threadDevLst, targLst]
# paramLst (for regular options) ex. [-set=00, -seconds=40, ways=1]
# threadDevLst (for options related to threads and devices) ex. [-T1=11, -t1=\sv\00, -D1=sv\00]
# targLst (for target options) ex. [-targ11=\socket\123]
def splitCmd(commandLst):
    regLst = [r"-T\d+=", r"-t\d+=", r"-D\d+=", r"-targ\d+="]
    paramLst = []
    threadDevLst = []
    targLst = []
    for option in commandLst:
        if re.search(regLst[0], option) \
                or re.search(regLst[1], option) \
                or re.search(regLst[2], option):
            threadDevLst.append(option)
        elif re.search(regLst[3], option):
            targLst.append(option)
        else:
            paramLst.append(option)
    return [paramLst, threadDevLst, targLst]

# P: lstAfterSplit is a list of three sub-lists containing parameters, thread/device options, and target options
# T: The function takes the sub-list of thread/device and target options from the lstAfterSplit parameter,
#    groups the options by their respective threads, and returns a new list with the parameter sub-list and
#    the grouped thread/device and target options.
# R: A list containing two sub-lists. The first sub-list contains parameters and the second sub-list contains
#    grouped thread/device and target options.
# outerGroup ex. [-targ11=/sv/socket, -T1=11, -t1=\sv\00, -D1=sv\00]
def groupCmd(lstAfterSplit):
    lst = lstAfterSplit[1] + lstAfterSplit[2]
    lstStr = " ".join(lst)
    result = {}
    for i in lstAfterSplit[1]:
        match = re.findall(r'-T(\d+)=(\d+)', i)
        if match:
            result[int(match[0][0])] = int(match[0][1])

    outerGroup = []
    for k, v in result.items():
        innerGroup = ""
        dev = [f"-targ{v}=", f"-T{k}=", f"-D{k}=", f"-t{k}="]
        for i in dev:
            regex = f"{i}\S+"
            match = re.search(regex, lstStr)
            innerGroup += (match.group(0) + " ")
        outerGroup.append(innerGroup)
    return [lstAfterSplit[0], outerGroup]

# P: groupedLst - a list of two lists, where the first list contains command line parameters and
#                 the second list contains thread and device options grouped by thread.
#    error - a list of string containing the error initially found in the logs of the length command line
# T: The function uses a local search algorithm to remove the non-error-causing options from the two
#    queues in a way that the maximum possible number of options are removed leaving error causing option.
# R: The function then returns a shortened command line that produce the error-causing output.
def minC(groupedLst, error):
    paramLst = groupedLst[0]
    threadDevLst = groupedLst[1]
    queue1 = paramLst[2:]
    queue2 = threadDevLst
    lastRemoved1 = ""
    lastRemoved2 = ""
    lastQueItem1 = queue1[0]
    lastQueItem2 = queue2[0]
    currLastQue1 = queue1[-1]
    currLastQue2 = queue2[-1]

    while currLastQue1 != lastQueItem1:
        cmdline = (" ".join(paramLst[:2]) + " " + " ".join(queue1) + " " + " ".join(queue2)).split()
        filename = runProcess(cmdline)
        logContent = accessLogFile(filename, True)
        newError = findError(logContent)
        if error == newError:
            lastRemoved1 = queue1[-1]
            queue1.pop()
        else:
            queue1.insert(0, lastRemoved1)
        currLastQue1 = queue1[-1]

    while currLastQue2 != lastQueItem2:
        cmdline = (" ".join(paramLst[:2]) + " " + " ".join(queue1) + " " + " ".join(queue2)).split()
        filename = runProcess(cmdline)
        logContent = accessLogFile(filename, True)
        newError = findError(logContent)
        if error == newError:
            lastRemoved2 = queue2[-1]
            queue2.pop()
        else:
            queue2.insert(0, lastRemoved2)
        currLastQue2 = queue2[-1]

    return cmdline

# P: commandLst: a list of strings representing the command to be written to the failure log.
#    supercolliderLogFileName: a string representing the name of the supercollider log file.
#    errorOptions: an optional list of strings representing the error options associated with the failure.
#    errorMessage: an optional string representing the error message associated with the failure.
# T: Writes operations that failed to a failure log
# R: None
def writeToFailureLog(commandLst, supercolliderLogFileName, errorOptions=None, errorMessage=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    command = " ".join(commandLst[2:]) if commandLst[0] == "timeout" else " ".join(commandLst)
    # Get File path
    name = os.name
    if name == "posix":
        filePath = f"{os.getcwd()}/logs/{supercolliderLogFileName}"
    else:
        filePath = f"{os.getcwd()}\logs\{supercolliderLogFileName}"
    with open("failure.log", 'a') as f:
        f.write(f"Timestamp: {timestamp}\n")
        if errorMessage:
            f.write(f"Error message: {errorMessage}\n")
        f.write(f"File: {filePath}\n")
        f.write(f"Command: {command}\n")
        if errorOptions:
            errorOptions = ", ".join(errorOptions)
            f.write(f"Error options: {errorOptions}\n")
        f.write("\n")
