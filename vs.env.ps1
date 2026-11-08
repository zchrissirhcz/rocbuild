#Requires -Version 5.1
<#
.SYNOPSIS
    一键激活 Visual Studio 开发者环境（VS 2022 / VS 2026），适用于任意 PowerShell 会话。

.DESCRIPTION
    必须用「点号」加载，环境变量才会留在当前会话：

        . ~/.vs.env.ps1                      # 自动使用最新安装的 VS
        . ~/.vs.env.ps1 -p vs2022            # 指定 VS 2022
        . ~/.vs.env.ps1 -p vs2022 -a x86     # VS 2022 + 32 位目标
        . ~/.vs.env.ps1 --list               # 只列出已安装实例
        . ~/.vs.env.ps1 -p vs2022 --refresh  # 忽略缓存，重新探测

    原理：调用 VS 自带的 Microsoft.VisualStudio.DevShell.dll（Enter-VsDevShell），
    首次约 2 秒；随后把结果缓存到 %LOCALAPPDATA%\vsdev-env\*.txt，
    再次激活通常只要几十毫秒。VS 升级（devenv.exe 版本变化）后缓存自动失效重算。
    若某个安装没有 DevShell，则退回 vcvarsall.bat 方式。

    参数写法同时兼容 -p / --product / -P 这类大小写与单双横线写法。

.PARAMETER p
    产品/版本：vs2022、vs2026、2022、2026、17、18、latest。留空 = 最新安装的版本。

.PARAMETER a
    目标架构：x64（默认）/ x86 / arm64。

.PARAMETER list
    列出已安装的 Visual Studio 实例后退出。

.PARAMETER refresh
    忽略缓存，重新探测并写入新缓存。

.PARAMETER no-cache
    本次不写缓存（仍然会读缓存）。

.PARAMETER quiet
    不打印激活成功的摘要。

.EXAMPLE
    . ~/.vs.env.ps1

.EXAMPLE
    . ~/.vs.env.ps1 -p vs2022 -a x86
#>

function __VsEnv_ShowHelp {
    Write-Host @'
用法:
  . ~/.vs.env.ps1                       自动选最新安装的 VS
  . ~/.vs.env.ps1 -p vs2022             指定版本（也接受 2022 / 17 / vs17）
  . ~/.vs.env.ps1 -p vs2022 -a x86      指定目标架构（x64 默认 / x86 / arm64）
  . ~/.vs.env.ps1 --list                列出已安装实例
  . ~/.vs.env.ps1 -p vs2022 --refresh   忽略缓存重新探测
  . ~/.vs.env.ps1 --no-cache            本次不写缓存
  . ~/.vs.env.ps1 -q                    不打印摘要

其他: --host-arch arm64 / --help
'@ -ForegroundColor Gray
}

# ---------------- 参数解析（支持 -p xxx / --p=xxx / --list / -List） ----------------

function __VsEnv_ParseArgs {
    param([object[]] $Argv)

    $o = @{
        Version  = ''
        Arch     = 'x64'
        HostArch = 'x64'
        List     = $false
        Refresh  = $false
        NoCache  = $false
        Quiet    = $false
        Help     = $false
    }

    $alias = @{
        'p' = 'version'; 'product' = 'version'; 'vs' = 'version'; 'version' = 'version'
        'a' = 'arch'; 'arch' = 'arch'; 'target-arch' = 'arch'; 'targetarch' = 'arch'
        'host-arch' = 'hostarch'; 'hostarch' = 'hostarch'; 'host' = 'hostarch'
        'l' = 'list'; 'list' = 'list'
        'r' = 'refresh'; 'refresh' = 'refresh'; 'force' = 'refresh'
        'no-cache' = 'nocache'; 'nocache' = 'nocache'
        'q' = 'quiet'; 'quiet' = 'quiet'
        'h' = 'help'; 'help' = 'help'; '?' = 'help'
    }

    $i = 0
    $n = @($Argv).Count

    while ($i -lt $n) {
        $tok = [string] $Argv[$i]
        $i++
        if ($tok -eq '') { continue }

        # 裸参数（不带横线）= 版本，兼容老写法 . ~/.vs.env.ps1 2022
        if ($tok[0] -ne '-') {
            if ($o.Version) { throw "多余的参数：'$tok'（用 --help 查看用法）" }
            $o.Version = $tok
            continue
        }

        $name = $tok.TrimStart('-').ToLowerInvariant()
        $inline = ''
        $eq = $name.IndexOf('=')
        if ($eq -ge 0) {
            $inline = $name.Substring($eq + 1)
            $name = $name.Substring(0, $eq)
        }

        if (-not $alias.ContainsKey($name)) {
            throw "未知参数：'$tok'（用 --help 查看用法）"
        }
        $key = $alias[$name]

        if ($key -eq 'version' -or $key -eq 'arch' -or $key -eq 'hostarch') {
            if ($inline) {
                $val = $inline
            }
            elseif ($i -lt $n -and -not ([string] $Argv[$i]).StartsWith('-')) {
                $val = [string] $Argv[$i]
                $i++
            }
            else {
                throw "参数 '$tok' 缺少取值"
            }
            switch ($key) {
                'version' { $o.Version = $val }
                'arch' { $o.Arch = $val.ToLowerInvariant() }
                'hostarch' { $o.HostArch = $val.ToLowerInvariant() }
            }
        }
        else {
            $o[$key] = $true
        }
    }

    if (@('x64', 'x86', 'arm64') -notcontains $o.Arch) {
        throw "不支持的架构：'$($o.Arch)'（可选 x64 / x86 / arm64）"
    }
    if (@('x64', 'arm64') -notcontains $o.HostArch) {
        throw "不支持的宿主架构：'$($o.HostArch)'（可选 x64 / arm64）"
    }

    return $o
}

# ---------------- 主逻辑 ----------------

function __VsEnv_Main {
    [CmdletBinding()]
    param(
        [string] $Version,
        [string] $Arch = 'x64',
        [string] $HostArch = 'x64',
        [switch] $Refresh,
        [switch] $NoCache,
        [switch] $List,
        [switch] $Quiet
    )

    $ErrorActionPreference = 'Stop'

    $cacheRoot = Join-Path -Path $env:LOCALAPPDATA -ChildPath 'vsdev-env'
    $pathLikeNames = @('path', 'psmodulepath')
    $skipNames = @('PROMPT', '__VSCMD_PREINIT_PATH', '__VSCMD_DEBUG')

    # ---------------- 小工具 ----------------

    function ConvertTo-VsPathKey([string] $p) {
        if ([string]::IsNullOrWhiteSpace($p)) { return '' }
        $p.Trim().TrimEnd('\').ToLowerInvariant()
    }

    # 注意：热路径（缓存命中）尽量只用 .NET IO，不用 Get-ChildItem / Get-Content。
    # PowerShell 的 FileSystem provider 首次调用要初始化约 110ms，而 [IO.*] 只要 2ms。

    function Get-VsEnvSnapshot {
        $h = @{}
        $raw = [System.Environment]::GetEnvironmentVariables('Process')
        foreach ($k in $raw.Keys) { $h[[string] $k] = [string] $raw[$k] }
        return $h
    }

    # 把 @(...) / $null / 单元素 / ArrayList 统一成干净字符串数组
    function Expand-VsValue($v) {
        return @(@($v) | Where-Object { $null -ne $_ -and "$_" -ne '' })
    }

    # ---------------- 发现已安装实例 ----------------

    function Get-VsInstances {
        $list = New-Object System.Collections.ArrayList
        $seen = @{}

        foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
            if (-not $base) { continue }
            $root = Join-Path $base 'Microsoft Visual Studio'
            if (-not [System.IO.Directory]::Exists($root)) { continue }

            foreach ($yearDir in [System.IO.Directory]::GetDirectories($root)) {
                foreach ($edDir in [System.IO.Directory]::GetDirectories($yearDir)) {
                    $devenv = Join-Path $edDir 'Common7\IDE\devenv.exe'
                    if (-not [System.IO.File]::Exists($devenv)) { continue }

                    $key = $edDir.ToLowerInvariant()
                    if ($seen.ContainsKey($key)) { continue }

                    $ver = ''
                    try { $ver = [string] [System.Diagnostics.FileVersionInfo]::GetVersionInfo($devenv).ProductVersion } catch { }
                    if (-not $ver) { continue }

                    $major = 0
                    [void] [int]::TryParse(($ver -split '\.')[0], [ref] $major)
                    if ($major -le 0) { continue }

                    $year = switch ($major) {
                        15 { '2017' }
                        16 { '2019' }
                        17 { '2022' }
                        18 { '2026' }
                        default { "$major" }
                    }

                    $seen[$key] = $true
                    [void] $list.Add([pscustomobject] @{
                            Major       = $major
                            Year        = $year
                            Edition     = Split-Path -Path $edDir -Leaf
                            InstallPath = $edDir
                            DevEnv      = $devenv
                            Version     = $ver
                        })
                }
            }
        }

        return @($list | Sort-Object -Property Major, Edition)
    }

    # ---------------- 激活（真正干活的两种方式） ----------------

    function Invoke-VsDevShell([object] $inst) {
        $dll = Join-Path $inst.InstallPath 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll'
        if ([System.IO.File]::Exists($dll)) {
            # 同一会话里切换版本时，先卸掉旧版本加载的模块
            $mod = Get-Module -Name 'Microsoft.VisualStudio.DevShell' -ErrorAction SilentlyContinue
            if ($mod -and $mod.Path -and ($mod.Path -ne $dll)) {
                Remove-Module -Name $mod.Name -Force -ErrorAction SilentlyContinue
                $mod = $null
            }
            if (-not $mod) {
                Import-Module -Name $dll -ErrorAction Stop -WarningAction SilentlyContinue
            }
            if (Get-Command -Name 'Enter-VsDevShell' -ErrorAction SilentlyContinue) {
                Enter-VsDevShell -VsInstallPath $inst.InstallPath `
                    -SkipAutomaticLocation `
                    -DevCmdArguments "-arch=$Arch -host_arch=$HostArch -no_logo" `
                    -ErrorAction Stop | Out-Null
                return
            }
        }

        # 退回 vcvarsall.bat（没有 DevShell 的安装）
        $bat = Join-Path $inst.InstallPath 'VC\Auxiliary\Build\vcvarsall.bat'
        if (-not [System.IO.File]::Exists($bat)) {
            throw "该安装既没有 DevShell 也没有 vcvarsall.bat：$($inst.InstallPath)"
        }
        Write-Verbose "使用 vcvarsall 回退：$bat $Arch"
        $lines = & cmd.exe /c "`"$bat`" $Arch -no_logo >nul 2>&1 && set"
        foreach ($line in @($lines)) {
            $i = $line.IndexOf('=')
            if ($i -gt 0) {
                Set-Item -Path ('env:' + $line.Substring(0, $i)) -Value $line.Substring($i + 1) -Force
            }
        }
    }

    # ---------------- 缓存：生成 / 读写 ----------------
    # 纯文本格式，避免 JSON 反序列化首次调用时加载程序集（省 ~200ms）
    #   schema=1 / version=.. / arch=.. / ...
    #   [vars]
    #   NAME=VALUE
    #   [path Path]
    #   F <前插条目>
    #   T <尾部追加条目>

    function New-VsCacheData([object] $inst, [hashtable] $before, [hashtable] $after) {
        $vars = @{}
        $pathLike = New-Object System.Collections.ArrayList

        foreach ($name in @($after.Keys)) {
            if ($before.ContainsKey($name) -and ($before[$name] -eq $after[$name])) { continue }
            if ($skipNames -contains $name) { continue }

            if ($pathLikeNames -contains $name.ToLowerInvariant()) {
                $b = @($before[$name] -split ';' | Where-Object { $_ -ne '' })
                $a = @($after[$name] -split ';' | Where-Object { $_ -ne '' })

                $bset = @{}
                foreach ($x in $b) { $bset[(ConvertTo-VsPathKey $x)] = $true }

                $front = New-Object System.Collections.ArrayList
                $tail = New-Object System.Collections.ArrayList
                $seenBase = $false
                foreach ($x in $a) {
                    if ($bset.ContainsKey((ConvertTo-VsPathKey $x))) { $seenBase = $true; continue }
                    if ($seenBase) { [void] $tail.Add($x) } else { [void] $front.Add($x) }
                }

                [void] $pathLike.Add([pscustomobject] @{
                        Name  = $name
                        Front = @($front)
                        Tail  = @($tail)
                    })
            }
            else {
                $vars[$name] = [string] $after[$name]
            }
        }

        return [pscustomobject] @{
            Schema      = 1
            InstallPath = $inst.InstallPath
            Version     = $inst.Version
            Major       = $inst.Major
            Year        = $inst.Year
            Arch        = $Arch
            HostArch    = $HostArch
            Created     = (Get-Date).ToString('s')
            Vars        = $vars
            PathLike    = @($pathLike)
        }
    }

    function Write-VsCacheFile([object] $data, [string] $file) {
        $lines = New-Object System.Collections.ArrayList
        [void] $lines.Add('schema=1')
        [void] $lines.Add("installPath=$($data.InstallPath)")
        [void] $lines.Add("version=$($data.Version)")
        [void] $lines.Add("major=$($data.Major)")
        [void] $lines.Add("year=$($data.Year)")
        [void] $lines.Add("arch=$($data.Arch)")
        [void] $lines.Add("hostArch=$($data.HostArch)")
        [void] $lines.Add("created=$($data.Created)")
        [void] $lines.Add('[vars]')
        foreach ($k in @($data.Vars.Keys)) { [void] $lines.Add("$k=$($data.Vars[$k])") }
        foreach ($pl in @($data.PathLike)) {
            [void] $lines.Add("[path $($pl.Name)]")
            foreach ($x in @(Expand-VsValue $pl.Front)) { [void] $lines.Add("F $x") }
            foreach ($x in @(Expand-VsValue $pl.Tail)) { [void] $lines.Add("T $x") }
        }

        if (-not [System.IO.Directory]::Exists($cacheRoot)) {
            [void] [System.IO.Directory]::CreateDirectory($cacheRoot)
        }
        [System.IO.File]::WriteAllLines($file, [string[]] $lines, (New-Object System.Text.UTF8Encoding($true)))
    }

    function Read-VsCacheFile([string] $file) {
        $hdr = @{}
        $vars = @{}
        $paths = New-Object System.Collections.ArrayList
        $section = 'hdr'
        $cur = $null

        foreach ($line in [System.IO.File]::ReadAllLines($file)) {
            if ($line -eq '') { continue }
            if ($line.StartsWith('[')) {
                if ($line.StartsWith('[path ')) {
                    $cur = [pscustomobject] @{
                        Name  = $line.Substring(6).TrimEnd(']')
                        Front = (New-Object System.Collections.ArrayList)
                        Tail  = (New-Object System.Collections.ArrayList)
                    }
                    [void] $paths.Add($cur)
                    $section = 'path'
                }
                else {
                    $section = 'vars'
                    $cur = $null
                }
                continue
            }

            if ($section -eq 'vars') {
                $i = $line.IndexOf('=')
                if ($i -gt 0) { $vars[$line.Substring(0, $i)] = $line.Substring($i + 1) }
            }
            elseif ($section -eq 'path') {
                if ($line.StartsWith('F ')) { [void] $cur.Front.Add($line.Substring(2)) }
                elseif ($line.StartsWith('T ')) { [void] $cur.Tail.Add($line.Substring(2)) }
            }
            else {
                $i = $line.IndexOf('=')
                if ($i -gt 0) { $hdr[$line.Substring(0, $i)] = $line.Substring($i + 1) }
            }
        }

        return [pscustomobject] @{
            Schema      = [int] $hdr['schema']
            InstallPath = [string] $hdr['installPath']
            Version     = [string] $hdr['version']
            Major       = [int] $hdr['major']
            Year        = [string] $hdr['year']
            Arch        = [string] $hdr['arch']
            HostArch    = [string] $hdr['hostArch']
            Created     = [string] $hdr['created']
            Vars        = $vars
            PathLike    = @($paths)
        }
    }

    function Set-VsEnvFromCache([object] $c) {
        foreach ($k in @($c.Vars.Keys)) {
            Set-Item -Path ('env:' + $k) -Value ([string] $c.Vars[$k]) -Force
        }

        foreach ($pl in @($c.PathLike)) {
            if (-not $pl) { continue }
            $cur = ''
            $item = Get-Item -Path ('env:' + $pl.Name) -ErrorAction SilentlyContinue
            if ($item) { $cur = [string] $item.Value }

            $ours = @{}
            foreach ($x in @(@(Expand-VsValue $pl.Front) + @(Expand-VsValue $pl.Tail))) {
                if ($x) { $ours[(ConvertTo-VsPathKey $x)] = $true }
            }

            $kept = New-Object System.Collections.ArrayList
            foreach ($seg in @($cur -split ';')) {
                if ($seg -eq '') { continue }
                if ($ours.ContainsKey((ConvertTo-VsPathKey $seg))) { continue }
                [void] $kept.Add($seg)
            }

            $newValue = (@(@(Expand-VsValue $pl.Front) + @($kept) + @(Expand-VsValue $pl.Tail))) -join ';'
            Set-Item -Path ('env:' + $pl.Name) -Value $newValue -Force
        }
    }

    # ---------------- 主流程 ----------------

    $instances = @(Get-VsInstances)
    if ($instances.Count -eq 0) {
        throw '没有找到任何 Visual Studio 安装（%ProgramFiles%\Microsoft Visual Studio 下没有 devenv.exe）。'
    }

    if ($List) {
        foreach ($i in $instances) {
            Write-Host ("[{0,2}] VS {1} {2}  {3}  ({4})" -f $i.Major, $i.Year, $i.Edition, $i.InstallPath, $i.Version) -ForegroundColor Cyan
        }
        return
    }

    $want = "$Version".Trim().ToLowerInvariant()
    if ($want.StartsWith('vs')) { $want = $want.Substring(2).Trim() }

    if (-not $want -or $want -eq 'latest' -or $want -eq 'auto') {
        $target = $instances | Sort-Object -Property Major | Select-Object -Last 1
    }
    else {
        $target = $instances |
            Where-Object { $_.Year -eq $want -or "$($_.Major)" -eq $want } |
            Sort-Object -Property Major | Select-Object -Last 1
    }

    if (-not $target) {
        $avail = ($instances | ForEach-Object { "VS $($_.Year) ($($_.Major))" }) -join ', '
        throw "没有找到版本 '$Version'。已安装：$avail"
    }

    $cacheName = ('{0}_{1}_{2}_{3}.txt' -f $target.Major, $target.Edition, $Arch, $HostArch) -replace '[^A-Za-z0-9._-]', '_'
    $cacheFile = Join-Path -Path $cacheRoot -ChildPath $cacheName

    $cache = $null
    if (-not $Refresh -and [System.IO.File]::Exists($cacheFile)) {
        try {
            $c = Read-VsCacheFile $cacheFile
            if ($c.Schema -eq 1 -and $c.Version -eq $target.Version -and $c.Arch -eq $Arch -and $c.HostArch -eq $HostArch) {
                $cache = $c
            }
        }
        catch {
            $cache = $null
        }
    }

    # 记录激活前的 VS 安装目录，用来提示“会话里已经加载了另一个版本”
    $prevVsDir = $env:VSINSTALLDIR

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if ($cache) {
        $source = 'cache'
        Set-VsEnvFromCache $cache
    }
    else {
        $source = 'probe'
        $before = Get-VsEnvSnapshot
        Invoke-VsDevShell $target
        if (-not $NoCache) {
            try {
                Write-VsCacheFile (New-VsCacheData $target $before (Get-VsEnvSnapshot)) $cacheFile
            }
            catch {
                Write-Verbose "写入缓存失败（不影响使用）：$($_.Exception.Message)"
            }
        }
    }
    $sw.Stop()

    if (-not $Quiet) {
        $mode = if ($source -eq 'cache') { '缓存' } else { '重新探测' }
        Write-Host ("VS {0} 开发者环境已就绪  [{1}/{2}  {3} ms  {4}]" -f `
                $target.Year, $Arch, $HostArch, $sw.ElapsedMilliseconds, $mode) -ForegroundColor Green
        if ($env:VCToolsVersion) {
            # 不调用 Get-Command（首次会触发命令发现，约 100ms），直接按目录规则拼路径
            $clPath = Join-Path -Path $env:VCToolsInstallDir -ChildPath "bin\Host$HostArch\$Arch\cl.exe"
            if (-not [System.IO.File]::Exists($clPath)) { $clPath = '(未安装 C++ 工具集)' }
            Write-Host ("  MSVC {0} | Windows SDK {1} | cl -> {2}" -f `
                    $env:VCToolsVersion.TrimEnd('\'), $env:WindowsSDKVersion, $clPath) -ForegroundColor DarkGray
        }
    }

    if ($prevVsDir -and ($prevVsDir.TrimEnd('\') -ne $target.InstallPath.TrimEnd('\'))) {
        Write-Warning ("本会话此前加载的是 $prevVsDir，两个版本的 PATH/INCLUDE 已混在一起；建议新开一个窗口再激活。")
    }
}

# ---------------- 入口 ----------------

if ($MyInvocation.InvocationName -ne '.') {
    Write-Warning '请用点号加载：. ~/.vs.env.ps1   （用 & 或 -File 调用时，环境变量只在本次执行的子作用域里生效）'
}

$opts = $null
try {
    $opts = __VsEnv_ParseArgs $args
    if ($opts.Help) {
        __VsEnv_ShowHelp
        return
    }
    __VsEnv_Main -Version $opts.Version -Arch $opts.Arch -HostArch $opts.HostArch `
        -Refresh:$opts.Refresh -NoCache:$opts.NoCache -List:$opts.List -Quiet:$opts.Quiet
}
finally {
    foreach ($fn in '__VsEnv_Main', '__VsEnv_ParseArgs', '__VsEnv_ShowHelp') {
        Remove-Item -Path ("Function:\$fn") -Force -ErrorAction SilentlyContinue
    }
    Remove-Variable -Name 'opts' -ErrorAction SilentlyContinue
}