$dataDir = "C:\Users\amit1\mysql-local-dev\data"
$logFile = "C:\Users\amit1\mysql-local-dev\error.log"
$pidFile = "C:\Users\amit1\mysql-local-dev\mysqld.pid"
$sock = "C:\Users\amit1\mysql-local-dev\mysql.sock"

$argList = @(
    "--datadir=$dataDir",
    "--port=3307",
    "--socket=$sock",
    "--standalone",
    "--log-error=$logFile",
    "--pid-file=$pidFile"
)

Start-Process -FilePath "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" -ArgumentList $argList -WindowStyle Hidden
Start-Sleep -Seconds 4
Write-Output "MySQL (standalone dev instance) starting on port 3307 - check $logFile for status."
