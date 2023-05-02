from utils_module import *

# Set timeout value for the input command and run the process
commandLst = setTimeOutValue(InputCommand("debug.cmd"))
print("\nRunning the process...")
errorLog = runProcess(commandLst)
print("Accessing log file...")
logContent = accessLogFile(errorLog)
print("Finding errors in the log file...")
error = findError(logContent)

# If no error found, write to failure log, else diagnose errors and minimize commandline
if not error:
    print("No errors found\nWriting to failure log")
    writeToFailureLog(commandLst, errorLog, errorMessage="No errors found! Optimize findError function")
    print("Successfully entered into failure log")
else:
    print("Diagnosing errors found")
    lstAfterSplit = splitCmd(commandLst)
    groupedLst = groupCmd(lstAfterSplit)
    print("Minimizing commandline...\n")
    minC = minC(groupedLst, error)

    # Convert the minimized commandline to output string
    if minC[0] == "timeout":
        output = " ".join(minC[2:])
    else:
        output = " ".join(minC)

    # Print the minimized commandline
    print("Minimized commandline:")
    print(output, "\n\n")
