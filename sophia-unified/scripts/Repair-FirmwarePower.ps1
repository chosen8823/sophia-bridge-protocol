<#
.SYNOPSIS
  Sophia firmware/power membrane for Dell laptop recovery.

.DESCRIPTION
  Default mode is report-only. It gathers BIOS/UEFI, battery, ACPI, sleep,
  wake, WHEA, Kernel-Power, and Dell update evidence into a small folder.

  Firmware flashing is intentionally not automatic. BIOS/firmware updates can
  reboot or brick a machine if power is unstable. This script can discover the
  Dell update CLI and prepare evidence; run vendor updates manually when the
  machine is plugged in, backed up, and stable.

  Optional OS-level repairs are reversible and must be requested with switches.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\Repair-FirmwarePower.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\Repair-FirmwarePower.ps1 -DisableHibernate

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\Repair-FirmwarePower.ps1 -SetBalancedPower
#>

[CmdletBinding()]
param(
    [string]$OutDir = "C:\Users\chose\sophia-unified\state\firmware-power-repair",
    [int]$EventDays = 21,
    [switch]$RunEnergyReport,
    [switch]$DellScan,
    [switch]$SetBalancedPower,
    [switch]$DisableHibernate,
    [switch]$EnableHibernate
)

$ErrorActionPreference = "Continue"

function New-StableRecord {
    param(
        [string]$Code,
        [string]$Message,
        [hashtable]$Data = @{}
    )
    [ordered]@{
        code = $Code
        message = $Message
        data = $Data
    }
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Value
    )
    $Value | ConvertTo-Json -Depth 12 | Out-File -LiteralPath $Path -Encoding utf8
}

function Invoke-Capture {
    param(
        [string]$Name,
        [string]$Exe,
        [string[]]$Arguments = @()
    )
    $stdoutPath = Join-Path $script:RunDir "$Name.out.txt"
    $stderrPath = Join-Path $script:RunDir "$Name.err.txt"
    $started = (Get-Date).ToUniversalTime().ToString("o")
    try {
        $process = Start-Process -FilePath $Exe -ArgumentList $Arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        return New-StableRecord -Code "COMMAND_CAPTURED" -Message "$Name completed" -Data @{
            name = $Name
            exe = $Exe
            arguments = $Arguments
            exit_code = $process.ExitCode
            stdout = $stdoutPath
            stderr = $stderrPath
            started_utc = $started
            ended_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
    }
    catch {
        return New-StableRecord -Code "COMMAND_FAILED" -Message "$Name failed" -Data @{
            name = $Name
            exe = $Exe
            arguments = $Arguments
            error = $_.Exception.Message
            stdout = $stdoutPath
            stderr = $stderrPath
            started_utc = $started
            ended_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
    }
}

function Export-Cim {
    param(
        [string]$Name,
        [string]$ClassName,
        [string]$Namespace = "root\cimv2"
    )
    $path = Join-Path $script:RunDir "$Name.json"
    try {
        $items = Get-CimInstance -Namespace $Namespace -ClassName $ClassName -ErrorAction Stop
        Write-JsonFile -Path $path -Value $items
        return New-StableRecord -Code "CIM_CAPTURED" -Message "$ClassName captured" -Data @{
            name = $Name
            class_name = $ClassName
            namespace = $Namespace
            path = $path
        }
    }
    catch {
        return New-StableRecord -Code "CIM_UNAVAILABLE" -Message "$ClassName unavailable" -Data @{
            name = $Name
            class_name = $ClassName
            namespace = $Namespace
            error = $_.Exception.Message
        }
    }
}

function Export-SystemEvents {
    $path = Join-Path $script:RunDir "system-power-firmware-events.json"
    $start = (Get-Date).AddDays(-1 * [Math]::Max(1, $EventDays))
    $interestingSources = @(
        "Kernel-Power",
        "Power-Troubleshooter",
        "Microsoft-Windows-WHEA-Logger",
        "Microsoft-Windows-Kernel-Boot",
        "Microsoft-Windows-Kernel-General",
        "Microsoft-Windows-UserModePowerService",
        "ACPI"
    )
    try {
        $events = Get-WinEvent -FilterHashtable @{LogName = "System"; StartTime = $start} -ErrorAction Stop |
            Where-Object {
                $interestingSources -contains $_.ProviderName -or
                $_.Id -in @(1, 12, 13, 17, 18, 19, 41, 42, 107, 109, 172, 506, 507, 508, 6008)
            } |
            Select-Object -First 400 TimeCreated, Id, ProviderName, LevelDisplayName, Message
        Write-JsonFile -Path $path -Value $events
        return New-StableRecord -Code "EVENTS_CAPTURED" -Message "power and firmware events captured" -Data @{
            path = $path
            start_utc = $start.ToUniversalTime().ToString("o")
            max_events = 400
        }
    }
    catch {
        return New-StableRecord -Code "EVENTS_FAILED" -Message "event capture failed" -Data @{
            error = $_.Exception.Message
            path = $path
        }
    }
}

function Find-DellCommandUpdate {
    $candidates = @(
        "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe",
        "C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe",
        "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe",
        "C:\Program Files\Dell\UpdateService\ServiceShell.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Invoke-SafeRepairs {
    $records = @()
    if ($SetBalancedPower) {
        $records += Invoke-Capture -Name "set-balanced-power" -Exe "powercfg.exe" -Arguments @("/setactive", "SCHEME_BALANCED")
    }
    if ($DisableHibernate -and $EnableHibernate) {
        $records += New-StableRecord -Code "HIBERNATE_CONFLICT" -Message "choose DisableHibernate or EnableHibernate, not both"
    }
    elseif ($DisableHibernate) {
        $records += Invoke-Capture -Name "disable-hibernate" -Exe "powercfg.exe" -Arguments @("/hibernate", "off")
    }
    elseif ($EnableHibernate) {
        $records += Invoke-Capture -Name "enable-hibernate" -Exe "powercfg.exe" -Arguments @("/hibernate", "on")
    }
    return $records
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$script:RunDir = Join-Path $OutDir $timestamp
New-Item -ItemType Directory -Path $script:RunDir -Force | Out-Null

$isAdmin = Test-Administrator
$records = @()
$records += New-StableRecord -Code "REPAIR_SESSION_STARTED" -Message "firmware power membrane started" -Data @{
    run_dir = $script:RunDir
    is_admin = $isAdmin
    event_days = $EventDays
    run_energy_report = [bool]$RunEnergyReport
    dell_scan = [bool]$DellScan
    set_balanced_power = [bool]$SetBalancedPower
    disable_hibernate = [bool]$DisableHibernate
    enable_hibernate = [bool]$EnableHibernate
}

$records += Export-Cim -Name "bios" -ClassName "Win32_BIOS"
$records += Export-Cim -Name "computer-system" -ClassName "Win32_ComputerSystem"
$records += Export-Cim -Name "operating-system" -ClassName "Win32_OperatingSystem"
$records += Export-Cim -Name "battery" -ClassName "Win32_Battery"
$records += Export-Cim -Name "pnp-signed-drivers" -ClassName "Win32_PnPSignedDriver"
$records += Export-Cim -Name "battery-status-wmi" -ClassName "BatteryStatus" -Namespace "root\wmi"
$records += Export-Cim -Name "battery-static-data-wmi" -ClassName "BatteryStaticData" -Namespace "root\wmi"
$records += Export-Cim -Name "battery-full-charged-capacity-wmi" -ClassName "BatteryFullChargedCapacity" -Namespace "root\wmi"

$records += Invoke-Capture -Name "powercfg-available-sleep-states" -Exe "powercfg.exe" -Arguments @("/a")
$records += Invoke-Capture -Name "powercfg-requests" -Exe "powercfg.exe" -Arguments @("/requests")
$records += Invoke-Capture -Name "powercfg-lastwake" -Exe "powercfg.exe" -Arguments @("/lastwake")
$records += Invoke-Capture -Name "powercfg-waketimers" -Exe "powercfg.exe" -Arguments @("/waketimers")
$records += Invoke-Capture -Name "powercfg-wake-armed-devices" -Exe "powercfg.exe" -Arguments @("/devicequery", "wake_armed")
$records += Invoke-Capture -Name "powercfg-active-scheme" -Exe "powercfg.exe" -Arguments @("/getactivescheme")
$records += Invoke-Capture -Name "battery-report" -Exe "powercfg.exe" -Arguments @("/batteryreport", "/output", (Join-Path $script:RunDir "battery-report.html"))
$records += Invoke-Capture -Name "sleep-study" -Exe "powercfg.exe" -Arguments @("/sleepstudy", "/output", (Join-Path $script:RunDir "sleep-study.html"))

if ($RunEnergyReport) {
    $records += Invoke-Capture -Name "energy-report" -Exe "powercfg.exe" -Arguments @("/energy", "/duration", "30", "/output", (Join-Path $script:RunDir "energy-report.html"))
}

$records += Export-SystemEvents

$problemDevicesPath = Join-Path $script:RunDir "pnp-problem-devices.json"
try {
    $problemDevices = Get-PnpDevice -ErrorAction Stop |
        Where-Object { $_.Status -ne "OK" -or $_.FriendlyName -match "Battery|ACPI|Firmware|Thermal|Power" } |
        Select-Object Status, Class, FriendlyName, InstanceId, Problem
    Write-JsonFile -Path $problemDevicesPath -Value $problemDevices
    $records += New-StableRecord -Code "PNP_CAPTURED" -Message "problem and power-related devices captured" -Data @{ path = $problemDevicesPath }
}
catch {
    $records += New-StableRecord -Code "PNP_FAILED" -Message "PnP capture failed" -Data @{ error = $_.Exception.Message; path = $problemDevicesPath }
}

$dellCli = Find-DellCommandUpdate
if ($null -ne $dellCli) {
    $records += New-StableRecord -Code "DELL_UPDATE_CLI_FOUND" -Message "Dell update CLI discovered" -Data @{ path = $dellCli }
    if ($DellScan) {
        $records += Invoke-Capture -Name "dell-command-update-scan" -Exe $dellCli -Arguments @("/scan", "-outputLog", (Join-Path $script:RunDir "dell-command-update-scan.log"))
    }
}
else {
    $records += New-StableRecord -Code "DELL_UPDATE_CLI_MISSING" -Message "Dell update CLI was not found" -Data @{
        suggested_install = "Install Dell Command | Update from Dell Support, then rerun with -DellScan."
    }
}

$records += Invoke-SafeRepairs

$summary = [ordered]@{
    kind = "sophia_firmware_power_repair_receipt_v1"
    run_dir = $script:RunDir
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    is_admin = $isAdmin
    automatic_firmware_flash = $false
    records = $records
    next_actions = @(
        "Review battery-report.html and sleep-study.html.",
        "If sleep or wake loops are present, inspect powercfg-requests.out.txt, powercfg-lastwake.out.txt, and system-power-firmware-events.json.",
        "If hibernation or Fast Startup looks corrupted and you accept the tradeoff, rerun with -DisableHibernate.",
        "If the active plan is weird, rerun with -SetBalancedPower.",
        "If Dell Command Update is found and the laptop is plugged in with stable power, rerun with -DellScan before any manual firmware update."
    )
}

$summaryPath = Join-Path $script:RunDir "repair-summary.json"
Write-JsonFile -Path $summaryPath -Value $summary

Write-Host "[SOPHIA] Firmware/power membrane complete."
Write-Host "[SOPHIA] Report folder: $script:RunDir"
Write-Host "[SOPHIA] Summary: $summaryPath"
if (-not $isAdmin) {
    Write-Host "[SOPHIA] Note: rerun as Administrator for the fullest powercfg/device evidence."
}
Write-Host "[SOPHIA] No firmware was flashed automatically."
