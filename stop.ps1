$connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    if ($conn.OwningProcess -gt 0) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -ne "System") {
            Write-Host "Stopping Interview Detection System (PID: $($conn.OwningProcess), Name: $($proc.ProcessName))..."
            Stop-Process -Id $conn.OwningProcess -Force
            Write-Host "System stopped."
            return
        }
    }
}
Write-Host "Interview Detection System is not running on port 5000."
pause
