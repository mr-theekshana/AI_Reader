$WshShell = New-Object -ComObject WScript.Shell
$Path = "d:\Side_Projects\AI_Reader"
$ShortcutPath = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "AI Reader.lnk")
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$Path\AI_Reader.vbs`""
$Shortcut.WorkingDirectory = $Path
$Shortcut.IconLocation = "$Path\icon.ico"
$Shortcut.Description = "AI Reader - Natural AI Voice Reader"
$Shortcut.Save()
Write-Host "Desktop shortcut created successfully!"
