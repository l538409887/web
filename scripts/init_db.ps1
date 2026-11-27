# =============================================================
#  一键初始化数据库（Windows / PowerShell）
#
#  依次执行 db/ 下四个 SQL 文件，顺序不能换：
#    1. schema.sql           建库 + 建 19 张表（含 DROP，会清空同名表）
#    2. 00_create_user.sql   建最小权限账号 novel_app
#    3. seed.sql             首批演示数据（12 本书 / 6 个账号）
#    4. demo_extra_books.sql 再补 10 本书（首页三个书区需要 22 本）
#
#  用法：
#    pwsh scripts/init_db.ps1          # 有确认提示
#    pwsh scripts/init_db.ps1 -Force   # 跳过确认
#
#  注意：
#    - schema.sql 会 DROP 已有表，seed.sql 会 TRUNCATE，只适合全新环境。
#      已有数据请改用 db/migrations/ 增量脚本。
#    - mysql 客户端打不开含中文的绝对路径，所以先切到 db/ 目录、
#      用相对文件名执行（这是实测踩出来的坑）。
# =============================================================
param([switch]$Force)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$dbDir = Join-Path $repoRoot 'db'

function Find-Mysql {
    $cmd = Get-Command mysql -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @(
            'E:\MySQL\MySQL Server 8.0\bin\mysql.exe',
            'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe',
            'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe'
        )) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$mysql = Find-Mysql
if (-not $mysql) {
    Write-Host "[错误] 找不到 mysql 客户端。" -ForegroundColor Red
    Write-Host "       请把 MySQL 的 bin 目录加入 PATH，或手动执行 db/ 下的四个 SQL 文件。"
    exit 1
}
Write-Host ("mysql: " + $mysql) -ForegroundColor DarkGray

$files = @('schema.sql', '00_create_user.sql', 'seed.sql', 'demo_extra_books.sql')
foreach ($f in $files) {
    if (-not (Test-Path (Join-Path $dbDir $f))) {
        Write-Host ("[错误] 缺少文件 db/" + $f) -ForegroundColor Red
        exit 1
    }
}

Write-Host ''
Write-Host '即将执行：' -ForegroundColor Yellow
Write-Host '  1. 重建数据库与全部表（会清空已有数据）'
Write-Host '  2. 创建最小权限账号 novel_app'
Write-Host '  3. 写入演示数据 22 本书'
Write-Host ''

if (-not $Force) {
    $ans = Read-Host '确认继续？输入 yes 回车'
    if ($ans -ne 'yes') {
        Write-Host '已取消。'
        exit 0
    }
}

$secure = Read-Host '请输入 MySQL root 密码' -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:MYSQL_PWD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
}
finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$steps = @(
    @{ n = 1; f = 'schema.sql'; db = $null },
    @{ n = 2; f = '00_create_user.sql'; db = $null },
    @{ n = 3; f = 'seed.sql'; db = 'novel_platform' },
    @{ n = 4; f = 'demo_extra_books.sql'; db = 'novel_platform' }
)

Push-Location $dbDir
try {
    foreach ($s in $steps) {
        Write-Host ("[{0}/4] {1} ..." -f $s.n, $s.f) -NoNewline
        if ($s.db) {
            & $mysql -u root --default-character-set=utf8mb4 $s.db -e "source $($s.f)" 2>&1 | Out-Host
        }
        else {
            & $mysql -u root --default-character-set=utf8mb4 -e "source $($s.f)" 2>&1 | Out-Host
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host ' 失败' -ForegroundColor Red
            return
        }
        Write-Host ' 完成' -ForegroundColor Green
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host '验证结果：' -ForegroundColor Cyan
& $mysql -u root --default-character-set=utf8mb4 -t novel_platform -e "SELECT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='novel_platform') AS tables, (SELECT COUNT(*) FROM book) AS books, (SELECT COUNT(*) FROM book_chapter) AS chapters, (SELECT COUNT(*) FROM sys_user) AS users;"

Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue

Write-Host ''
Write-Host '数据库就绪。接下来：' -ForegroundColor Green
Write-Host '  1) cd backend'
Write-Host '  2) copy .env.example .env   改 DATABASE_URL 的密码 + SECRET_KEY'
Write-Host '  3) python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt'
Write-Host '  4) python scripts/check_env.py'
Write-Host '  5) uvicorn main:app --reload --port 8000'
