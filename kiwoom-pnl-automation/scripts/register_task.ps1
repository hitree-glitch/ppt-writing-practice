$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "python"
$Config = Join-Path $ProjectDir "config.json"
$Action = New-ScheduledTaskAction -Execute $Python -Argument "-m pnl_automation.cli --config `"$Config`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 7:00PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "KiwoomMonthlyPnlAutomation" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Update monthly realized PnL Google Sheet from Kiwoom REST API"
Write-Host "Registered task: KiwoomMonthlyPnlAutomation"
