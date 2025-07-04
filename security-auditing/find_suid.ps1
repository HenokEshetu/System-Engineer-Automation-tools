# -----------------------------------------
# Privileged Executable Finder (Windows)
# -----------------------------------------

$OutFile = "Privileged_Executables.txt"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Computer = $env:COMPUTERNAME

Write-Host "[Success] Privileged Executable Scan - $Timestamp on $Computer"

$Paths = @(
    "$Env:SystemRoot\System32",
    "$Env:ProgramFiles",
    "$Env:ProgramFiles(x86)",
    "$Env:UserProfile\Desktop",
    "C:\Users\Public\Desktop"
)

$Executables = @()

foreach ($path in $Paths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Recurse -Include *.exe -ErrorAction SilentlyContinue |
        ForEach-Object {
            $acl = Get-Acl $_.FullName
            $owner = $acl.Owner
            if ($owner -match "SYSTEM|Administrators|TrustedInstaller") {
                $Executables += "$($_.FullName)  [Owner: $owner]"
            }
        }
    }
}

$Executables | Tee-Object -FilePath $OutFile
Write-Host "[Success] Scan complete. Results saved to $OutFile"
