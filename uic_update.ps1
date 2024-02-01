$fileUI = Get-Item "./form.ui"
$lastSaveDateUI = $fileUI.LastWriteTime
"form.ui:    " + $lastSaveDateUI
$filePy = Get-Item "./ui_form.py"
$lastSaveDatePy = $filePy.LastWriteTime
"ui_form.py: " + $lastSaveDatePy
"form.ui Newer than ui_form.py : " + ($lastSaveDateUI -gt $lastSaveDatePy)
if ($lastSaveDateUI -gt $lastSaveDatePy) {
    & pyside6-uic form.ui -o ui_form.py
    Write-Host "ui_form.py updated."
} else {
    Write-Host "No conversion."
}