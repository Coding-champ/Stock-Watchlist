# Update Index Weights - PowerShell Script
# Automatically updates constituent weights for all indices
# Can be scheduled with Windows Task Scheduler

param(
    [string]$VenvPath = "D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist\.venv",
    [string]$WorkspaceRoot = "D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist",
    [string]$Method = "market_cap",
    [switch]$DryRun,
    [string[]]$Indices = @("^GSPC", "^GDAXI", "^NDX")
)

# Log function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

# Activate virtual environment
Write-Log "Activating virtual environment..."
& "$VenvPath\Scripts\Activate.ps1"

# Change to workspace directory
Set-Location $WorkspaceRoot

# Update weights for each index
foreach ($index in $Indices) {
    Write-Log "Updating weights for $index..."
    
    $args = @(
        "tools\calculate_index_weights.py",
        "--index", $index,
        "--method", $Method
    )
    
    if ($DryRun) {
        $args += "--dry-run"
    }
    
    try {
        python @args
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ Successfully updated $index"
        } else {
            Write-Log "✗ Failed to update $index (exit code: $LASTEXITCODE)"
        }
    } catch {
        Write-Log "✗ Error updating $index: $_"
    }
}

Write-Log "Weight update completed!"

# Deactivate virtual environment
deactivate
