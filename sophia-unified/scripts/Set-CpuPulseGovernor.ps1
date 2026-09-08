<#
.SYNOPSIS
  Sophia CPU pulse governor for safe rhythm-based performance tuning.

.DESCRIPTION
  Default mode is Report. It reads CPU, power, memory, disk, wake, and boost
  policy state without changing the machine.

  Apply modes use Windows powercfg only. They do not overclock voltage, flash
  firmware, touch BIOS, patch drivers, or bypass hardware limits.

  Modes:
    Report   - inspect current pulse
    Cool     - reduce heat/boost pressure
    Balanced - restore sane balanced behaviour
    Burst    - prefer AC turbo responsiveness without disabling guardrails

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\Set-CpuPulseGovernor.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\Set-CpuPulseGovernor.ps1 -Mode Burst
#>

[CmdletBinding()]
param(
    [ValidateSet("Report", "Cool", "Balanced", "Burst")]
    [string]$Mode = "Report",
    [string]$OutDir = "C:\Users\chose\sophia-unified\state\cpu-pulse-governor",
    [int]$SampleSeconds = 1,
    [int]$Samples = 3
)

$ErrorActionPreference = "Continue"

$GUID_SUB_PROCESSOR = "54533251-82be-4824-96c1-47b60b740d00"
$GUID_MIN_PROCESSOR = "893dee8e-2bef-41e0-89c6-b55d0929964c"
$GUID_MAX_PROCESSOR = "bc5038f7-23e0-4960-96da-33abaf5935ec"
$GUID_COOLING_POLICY = "94d3a615-a899-4ac5-ae2b-e4d8f634367f"
$GUID_BOOST_MODE = "be337238-0d82-4146-a960-4f3749d470c7"
$SCHEME_BALANCED = "SCHEME_BALANCED"
$SCHEME_HIGH_PERFORMANCE = "SCHEME_MIN"

function New-Record {
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

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Value
    )
    $Value | ConvertTo-Json -Depth 12 | Out-File -LiteralPath $Path -Encoding utf8
}

function Invoke-CommandCapture {
    param(
        [string]$Name,
        [string]$Exe,
        [string[]]$Arguments = @()
    )
    $stdout = Join-Path $script:RunDir "$Name.out.txt"
    $stderr = Join-Path $script:RunDir "$Name.err.txt"
    try {
        $process = Start-Process -FilePath $Exe -ArgumentList $Arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        return New-Record -Code "COMMAND_CAPTURED" -Message "$Name completed" -Data @{
            name = $Name
            exe = $Exe
            arguments = $Arguments
            exit_code = $process.ExitCode
            stdout = $stdout
            stderr = $stderr
        }
    }
    catch {
        return New-Record -Code "COMMAND_FAILED" -Message "$Name failed" -Data @{
            name = $Name
            exe = $Exe
            arguments = $Arguments
            error = $_.Exception.Message
            stdout = $stdout
            stderr = $stderr
        }
    }
}

function Set-PowerValue {
    param(
        [string]$Name,
        [string]$Scheme,
        [string]$Setting,
        [int]$AcValue,
        [int]$DcValue
    )
    $records = @()
    $records += Invoke-CommandCapture -Name "$Name-ac" -Exe "powercfg.exe" -Arguments @("/setacvalueindex", $Scheme, $GUID_SUB_PROCESSOR, $Setting, "$AcValue")
    $records += Invoke-CommandCapture -Name "$Name-dc" -Exe "powercfg.exe" -Arguments @("/setdcvalueindex", $Scheme, $GUID_SUB_PROCESSOR, $Setting, "$DcValue")
    return $records
}

function Apply-Mode {
    param([string]$SelectedMode)

    $records = @()
    if ($SelectedMode -eq "Report") {
        return $records
    }

    if ($SelectedMode -eq "Cool") {
        $scheme = $SCHEME_BALANCED
        $records += Set-PowerValue -Name "cool-min-processor" -Scheme $scheme -Setting $GUID_MIN_PROCESSOR -AcValue 5 -DcValue 5
        $records += Set-PowerValue -Name "cool-max-processor" -Scheme $scheme -Setting $GUID_MAX_PROCESSOR -AcValue 85 -DcValue 70
        $records += Set-PowerValue -Name "cool-active-cooling" -Scheme $scheme -Setting $GUID_COOLING_POLICY -AcValue 1 -DcValue 1
        $records += Set-PowerValue -Name "cool-boost-disabled" -Scheme $scheme -Setting $GUID_BOOST_MODE -AcValue 0 -DcValue 0
        $records += Invoke-CommandCapture -Name "activate-cool-balanced" -Exe "powercfg.exe" -Arguments @("/setactive", $scheme)
        return $records
    }

    if ($SelectedMode -eq "Balanced") {
        $scheme = $SCHEME_BALANCED
        $records += Set-PowerValue -Name "balanced-min-processor" -Scheme $scheme -Setting $GUID_MIN_PROCESSOR -AcValue 5 -DcValue 5
        $records += Set-PowerValue -Name "balanced-max-processor" -Scheme $scheme -Setting $GUID_MAX_PROCESSOR -AcValue 100 -DcValue 85
        $records += Set-PowerValue -Name "balanced-active-cooling" -Scheme $scheme -Setting $GUID_COOLING_POLICY -AcValue 1 -DcValue 1
        $records += Set-PowerValue -Name "balanced-efficient-boost" -Scheme $scheme -Setting $GUID_BOOST_MODE -AcValue 3 -DcValue 3
        $records += Invoke-CommandCapture -Name "activate-balanced" -Exe "powercfg.exe" -Arguments @("/setactive", $scheme)
        return $records
    }

    if ($SelectedMode -eq "Burst") {
        $scheme = $SCHEME_HIGH_PERFORMANCE
        $records += Set-PowerValue -Name "burst-min-processor" -Scheme $scheme -Setting $GUID_MIN_PROCESSOR -AcValue 25 -DcValue 5
        $records += Set-PowerValue -Name "burst-max-processor" -Scheme $scheme -Setting $GUID_MAX_PROCESSOR -AcValue 100 -DcValue 85
        $records += Set-PowerValue -Name "burst-active-cooling" -Scheme $scheme -Setting $GUID_COOLING_POLICY -AcValue 1 -DcValue 1
        $records += Set-PowerValue -Name "burst-aggressive-boost" -Scheme $scheme -Setting $GUID_BOOST_MODE -AcValue 2 -DcValue 3
        $records += Invoke-CommandCapture -Name "activate-burst-high-performance" -Exe "powercfg.exe" -Arguments @("/setactive", $scheme)
        return $records
    }

    return $records
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$script:RunDir = Join-Path $OutDir $timestamp
New-Item -ItemType Directory -Path $script:RunDir -Force | Out-Null

$records = @()
$records += New-Record -Code "CPU_PULSE_STARTED" -Message "cpu pulse governor started" -Data @{
    mode = $Mode
    run_dir = $script:RunDir
    sample_seconds = $SampleSeconds
    samples = $Samples
    automatic_overclock = $false
    voltage_change = $false
    firmware_change = $false
}

$cpuPath = Join-Path $script:RunDir "cpu.json"
$systemPath = Join-Path $script:RunDir "system.json"
$batteryPath = Join-Path $script:RunDir "battery.json"
$diskPath = Join-Path $script:RunDir "disk.json"
$counterPath = Join-Path $script:RunDir "performance-counters.json"

try {
    Write-JsonFile -Path $cpuPath -Value (Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, CurrentClockSpeed, LoadPercentage, VirtualizationFirmwareEnabled)
    $records += New-Record -Code "CPU_CAPTURED" -Message "processor state captured" -Data @{ path = $cpuPath }
}
catch {
    $records += New-Record -Code "CPU_CAPTURE_FAILED" -Message "processor state unavailable" -Data @{ error = $_.Exception.Message }
}

try {
    Write-JsonFile -Path $systemPath -Value (Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, SystemType, TotalPhysicalMemory)
    Write-JsonFile -Path $batteryPath -Value (Get-CimInstance Win32_Battery | Select-Object Name, BatteryStatus, EstimatedChargeRemaining, EstimatedRunTime, Status)
    Write-JsonFile -Path $diskPath -Value (Get-PSDrive -PSProvider FileSystem | Select-Object Name, Root, @{Name = "FreeBytes"; Expression = { $_.Free } }, @{Name = "UsedBytes"; Expression = { $_.Used } })
    $records += New-Record -Code "SYSTEM_CAPTURED" -Message "system battery disk state captured" -Data @{ system = $systemPath; battery = $batteryPath; disk = $diskPath }
}
catch {
    $records += New-Record -Code "SYSTEM_CAPTURE_FAILED" -Message "system capture failed" -Data @{ error = $_.Exception.Message }
}

$counterPaths = @(
    "\Processor Information(_Total)\% Processor Utility",
    "\Processor Information(_Total)\Processor Frequency",
    "\Processor Information(_Total)\% of Maximum Frequency",
    "\Memory\Available MBytes",
    "\PhysicalDisk(_Total)\% Disk Time"
)
try {
    $counterData = Get-Counter $counterPaths -SampleInterval ([Math]::Max(1, $SampleSeconds)) -MaxSamples ([Math]::Max(1, $Samples))
    $flat = foreach ($sample in $counterData) {
        foreach ($counter in $sample.CounterSamples) {
            [ordered]@{
                timestamp = $sample.Timestamp.ToUniversalTime().ToString("o")
                path = $counter.Path
                value = [int][Math]::Round($counter.CookedValue)
            }
        }
    }
    Write-JsonFile -Path $counterPath -Value $flat
    $records += New-Record -Code "COUNTERS_CAPTURED" -Message "performance counters captured" -Data @{ path = $counterPath }
}
catch {
    $records += New-Record -Code "COUNTERS_FAILED" -Message "performance counters unavailable" -Data @{ error = $_.Exception.Message }
}

$records += Invoke-CommandCapture -Name "powercfg-active-scheme" -Exe "powercfg.exe" -Arguments @("/getactivescheme")
$records += Invoke-CommandCapture -Name "powercfg-processor-query" -Exe "powercfg.exe" -Arguments @("/query", "SCHEME_CURRENT", "SUB_PROCESSOR")
$records += Invoke-CommandCapture -Name "powercfg-requests" -Exe "powercfg.exe" -Arguments @("/requests")
$records += Invoke-CommandCapture -Name "powercfg-lastwake" -Exe "powercfg.exe" -Arguments @("/lastwake")
$records += Invoke-CommandCapture -Name "powercfg-waketimers" -Exe "powercfg.exe" -Arguments @("/waketimers")

$records += Apply-Mode -SelectedMode $Mode

if ($Mode -ne "Report") {
    $records += Invoke-CommandCapture -Name "powercfg-active-scheme-after" -Exe "powercfg.exe" -Arguments @("/getactivescheme")
    $records += Invoke-CommandCapture -Name "powercfg-processor-query-after" -Exe "powercfg.exe" -Arguments @("/query", "SCHEME_CURRENT", "SUB_PROCESSOR")
}

$summary = [ordered]@{
    kind = "sophia_cpu_pulse_governor_receipt_v1"
    mode = $Mode
    run_dir = $script:RunDir
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    automatic_overclock = $false
    voltage_change = $false
    firmware_change = $false
    records = $records
    next_actions = @(
        "Review powercfg-processor-query.out.txt for processor boost and throttle limits.",
        "Use -Mode Burst only on AC power with clear airflow.",
        "Use -Mode Cool if temperature, fan noise, or throttling is the current bottleneck.",
        "Free disk space before judging CPU tuning because a full C: drive can create system-wide lag.",
        "Do not use firmware flashing as a performance knob."
    )
}

$summaryPath = Join-Path $script:RunDir "cpu-pulse-summary.json"
Write-JsonFile -Path $summaryPath -Value $summary

Write-Host "[SOPHIA] CPU pulse governor complete."
Write-Host "[SOPHIA] Mode: $Mode"
Write-Host "[SOPHIA] Report folder: $script:RunDir"
Write-Host "[SOPHIA] Summary: $summaryPath"
Write-Host "[SOPHIA] Overclock/voltage/firmware changes: none."
