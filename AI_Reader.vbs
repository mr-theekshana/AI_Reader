Set WshShell = CreateObject("WScript.Shell")
' Get the directory of the script
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' Run the batch file hidden
WshShell.Run chr(34) & strPath & "\run_hidden.bat" & chr(34), 0
Set WshShell = Nothing
