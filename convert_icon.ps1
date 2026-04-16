Add-Type -AssemblyName System.Drawing
$imagePath = "d:\Side_Projects\AI_Reader\icon.png"
$icoPath = "d:\Side_Projects\AI_Reader\icon.ico"

$image = [System.Drawing.Bitmap]::FromFile($imagePath)
$newIcon = [System.Drawing.Bitmap]::new($image, 256, 256)
$hIcon = $newIcon.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($hIcon)

$fileStream = [System.IO.File]::OpenWrite($icoPath)
$icon.Save($fileStream)
$fileStream.Close()

$icon.Dispose()
[System.Runtime.InteropServices.Marshal]::FreeHGlobal($hIcon)
$newIcon.Dispose()
$image.Dispose()
write-host "Icon converted successfully to $icoPath"
