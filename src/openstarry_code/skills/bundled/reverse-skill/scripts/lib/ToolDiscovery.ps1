Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ReverseUserProfilePath {
    [CmdletBinding()]
    param()

    $profilePath = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
    if (-not [string]::IsNullOrWhiteSpace($profilePath)) {
        return $profilePath
    }
    if (-not [string]::IsNullOrWhiteSpace($HOME)) {
        return $HOME
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        return $env:USERPROFILE
    }
    throw 'Unable to resolve the current user profile path.'
}

function Join-ReverseOptionalPath {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$ChildPath
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return ''
    }
    return Join-Path $Path $ChildPath
}

function Get-ReverseToolCatalog {
    [CmdletBinding()]
    param()

    $userProfile = Get-ReverseUserProfilePath
    $localAppData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
    $appData = [Environment]::GetEnvironmentVariable('APPDATA')
    $toolRoot = Join-Path $userProfile 'Tools'
    $reversePythonPaths = @(
        (Join-Path $toolRoot 'python-analysis\Scripts\python.exe'),
        (Join-Path $toolRoot 'python-re\Scripts\python.exe'),
        (Join-Path $toolRoot 'python-pe\Scripts\python.exe'),
        (Join-Path $userProfile '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
    )

    return @(
        [pscustomobject]@{
            Name = 'jadx'
            Skill = 'apk-reverse'
            Purpose = 'Java 反编译'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'jadx' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\jadx\bin\jadx.bat') }
            )
        }
        [pscustomobject]@{
            Name = 'apktool'
            Skill = 'apk-reverse'
            Purpose = 'APK 解包与重建'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'apktool' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\apktool\apktool.bat') },
                [pscustomobject]@{ Type = 'java-jar'; Value = (Join-Path $userProfile 'Tools\apktool\apktool.jar') }
            )
        }
        [pscustomobject]@{
            Name = 'adb'
            Skill = 'apk-reverse'
            Purpose = '设备连接与 logcat'
            VersionArgs = @('version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'adb' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-ReverseOptionalPath -Path $localAppData -ChildPath 'Android\Sdk\platform-tools\adb.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'java'
            Skill = 'apk-reverse'
            Purpose = '运行 jar 与 Java 工具链'
            VersionArgs = @('-version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'java' }
            )
        }
        [pscustomobject]@{
            Name = 'apksigner'
            Skill = 'apk-reverse'
            Purpose = 'APK 签名'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'apksigner' }
            )
        }
        [pscustomobject]@{
            Name = 'zipalign'
            Skill = 'apk-reverse'
            Purpose = 'APK 对齐'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'zipalign' }
            )
        }
        [pscustomobject]@{
            Name = 'frida'
            Skill = 'apk-reverse'
            Purpose = 'Frida 动态注入'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'frida' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-analysis\Scripts\frida.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-re\Scripts\frida.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-ReverseOptionalPath -Path $appData -ChildPath 'Python\Python3xx\Scripts\frida.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'frida-ps'
            Skill = 'apk-reverse'
            Purpose = 'Frida 进程枚举'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'frida-ps' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-analysis\Scripts\frida-ps.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-re\Scripts\frida-ps.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-ReverseOptionalPath -Path $appData -ChildPath 'Python\Python3xx\Scripts\frida-ps.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'r2'
            Skill = 'radare2'
            Purpose = 'radare2 主分析器'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'r2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\r2.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'radare2\bin\radare2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\r2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\r2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\r2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'rabin2'
            Skill = 'radare2'
            Purpose = '二进制侦察'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'rabin2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\rabin2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\rabin2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\rabin2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'rasm2'
            Skill = 'radare2'
            Purpose = '汇编/反汇编'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'rasm2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\rasm2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\rasm2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\rasm2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'radiff2'
            Skill = 'radare2'
            Purpose = '二进制差分'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'radiff2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\radiff2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\radiff2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\radiff2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'rahash2'
            Skill = 'radare2'
            Purpose = '哈希与校验'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'rahash2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\rahash2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\rahash2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\rahash2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'rax2'
            Skill = 'radare2'
            Purpose = '进制与位运算转换'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'rax2' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\bin\rax2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\radare2\rax2.exe') },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Tools\radare2\bin\rax2.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'python'
            Skill = 'reverse-engineering'
            Purpose = '辅助脚本执行'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\re-python.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-re\Scripts\python.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-pe\Scripts\python.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') },
                [pscustomobject]@{ Type = 'command'; Value = 'python' },
                [pscustomobject]@{ Type = 'command'; Value = 'python3' }
            )
        }
        [pscustomobject]@{
            Name = 'pip'
            Skill = 'reverse-engineering'
            Purpose = 'Python 包管理'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\re-pip.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-re\Scripts\pip.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-pe\Scripts\pip.exe') },
                [pscustomobject]@{ Type = 'command'; Value = 'pip' },
                [pscustomobject]@{ Type = 'command'; Value = 'pip3' }
            )
        }
        [pscustomobject]@{
            Name = 'node'
            Skill = 'js-reverse'
            Purpose = '运行 Node 侧 JS 复现与 MCP 客户端'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'node' }
            )
        }
        [pscustomobject]@{
            Name = 'npx'
            Skill = 'js-reverse'
            Purpose = '运行临时 npm 包与 MCP 入口'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'npx' }
            )
        }
        [pscustomobject]@{
            Name = 'jshookmcp'
            Skill = 'js-reverse'
            Purpose = '通过 npx 启动 @jshookmcp/jshook MCP（仍需先配置并启用 MCP server）'
            FixedVersion = '@jshookmcp/jshook@latest'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'npx' }
            )
        }
        [pscustomobject]@{
            Name = 'agent-browser'
            Skill = 'browser-automation'
            Purpose = '浏览器自动化（Playwright）：打开页面、点击、填表、爬取、截图'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'agent-browser' }
            )
        }
        [pscustomobject]@{
            Name = 'analyzeHeadless'
            Skill = 'reverse-engineering'
            Purpose = 'Ghidra 无头分析（免费 IDA 替代）'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'analyzeHeadless' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\analyzeHeadless.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = '&lt;工具根目录&gt;\ghidra\support\analyzeHeadless.bat' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\ghidra\support\analyzeHeadless.bat') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $userProfile 'Tools\ghidra\ghidra_11.3_PUBLIC\support\analyzeHeadless.bat') }
            )
        }
        [pscustomobject]@{
            Name = 'pyghidra'
            Skill = 'reverse-engineering'
            Purpose = 'Ghidra Python headless API'
            FixedVersion = '3.1.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\pyghidra.cmd') }
            )
        }
        [pscustomobject]@{
            Name = 'vineflower'
            Skill = 'reverse-engineering'
            Purpose = 'Modern Java bytecode decompiler'
            FixedVersion = '1.11.1'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\vineflower.cmd') }
            )
        }
        [pscustomobject]@{
            Name = 'cfr'
            Skill = 'reverse-engineering'
            Purpose = 'Java bytecode decompiler cross-check'
            FixedVersion = '0.152'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\cfr.cmd') }
            )
        }
        [pscustomobject]@{
            Name = 'procyon'
            Skill = 'reverse-engineering'
            Purpose = 'Java bytecode decompiler cross-check'
            FixedVersion = '0.6.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\procyon.cmd') }
            )
        }
        [pscustomobject]@{
            Name = 'javap'
            Skill = 'reverse-engineering'
            Purpose = 'JVM bytecode and class signature inspection'
            VersionArgs = @('-version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'javap' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'jdk21\bin\javap.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'jdeps'
            Skill = 'reverse-engineering'
            Purpose = 'Java module and dependency analysis'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'jdeps' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'jdk21\bin\jdeps.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'jar'
            Skill = 'reverse-engineering'
            Purpose = 'JAR archive listing and extraction'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'jar' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'jdk21\bin\jar.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'r2ghidra'
            Skill = 'radare2'
            Purpose = 'radare2 Ghidra decompiler plugin'
            FixedVersion = '6.1.8'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'file'; Value = (Join-Path $toolRoot 'radare2\lib\plugins\core_r2ghidra.dll') }
            )
        }
        [pscustomobject]@{
            Name = 'r2ghidra-sleigh'
            Skill = 'radare2'
            Purpose = 'r2ghidra processor language definitions'
            FixedVersion = '6.1.8'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'directory'; Value = (Join-Path $toolRoot 'r2ghidra-sleigh') }
            )
        }
        [pscustomobject]@{
            Name = 'diec'
            Skill = 'reverse-engineering'
            Purpose = 'Detect It Easy CLI packer/compiler triage'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'diec' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'die\diec.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'floss'
            Skill = 'reverse-engineering'
            Purpose = 'Decoded and stack string extraction'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'floss' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'floss\floss.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'capa'
            Skill = 'reverse-engineering'
            Purpose = 'Executable capability identification'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'capa' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'capa\capa.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'pe-bear'
            Skill = 'reverse-engineering'
            Purpose = 'PE structure inspection GUI'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'pe-bear\PE-bear.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'x64dbg'
            Skill = 'binary-re-dynamic-analysis'
            Purpose = 'Windows x64 native debugger'
            FixedVersion = '2026.05.27'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'x64dbg' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\x64dbg.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'x64dbg\release\x64\x64dbg.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'x32dbg'
            Skill = 'binary-re-dynamic-analysis'
            Purpose = 'Windows x86 native debugger'
            FixedVersion = '2026.05.27'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'x32dbg' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'bin\x32dbg.cmd') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'x64dbg\release\x32\x32dbg.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'objdump'
            Skill = 'reverse-engineering'
            Purpose = 'GNU disassembly and PE/ELF metadata'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'objdump' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'msys2\ucrt64\bin\objdump.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'nm'
            Skill = 'reverse-engineering'
            Purpose = 'GNU symbol table inspection'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'nm' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'msys2\ucrt64\bin\nm.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'gnu-strings'
            Skill = 'reverse-engineering'
            Purpose = 'GNU strings extraction'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'msys2\ucrt64\bin\strings.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'sigcheck'
            Skill = 'reverse-engineering'
            Purpose = 'PE signature and metadata verification'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'sysinternals\sigcheck64.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'sysinternals-strings'
            Skill = 'reverse-engineering'
            Purpose = 'Windows ASCII/Unicode string extraction'
            FixedVersion = '2.54'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'sysinternals\strings64.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'capstone-python'
            Skill = 'reverse-engineering'
            Purpose = 'Python disassembly engine'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'capstone'; Distribution = 'capstone'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'lief-python'
            Skill = 'reverse-engineering'
            Purpose = 'Python executable format parser/editor'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'lief'; Distribution = 'lief'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'pefile-python'
            Skill = 'reverse-engineering'
            Purpose = 'Python PE parser'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'pefile'; Distribution = 'pefile'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'r2pipe-python'
            Skill = 'radare2'
            Purpose = 'Python radare2 automation bindings'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'r2pipe'; Distribution = 'r2pipe'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'unicorn-python'
            Skill = 'reverse-engineering'
            Purpose = 'Python CPU emulation engine'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'unicorn'; Distribution = 'unicorn'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'yara-python'
            Skill = 'malware-analysis'
            Purpose = 'Python YARA bindings'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'yara'; Distribution = 'yara-python'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'angr-python'
            Skill = 'reverse-engineering'
            Purpose = 'Symbolic binary analysis and program exploration'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'angr'; Distribution = 'angr'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'z3-python'
            Skill = 'reverse-engineering'
            Purpose = 'SMT solving for symbolic analysis'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'z3'; Distribution = 'z3-solver'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'qiling-python'
            Skill = 'binary-re-dynamic-analysis'
            Purpose = 'Cross-platform binary emulation framework'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'qiling'; Distribution = 'qiling'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'frida-python'
            Skill = 'binary-re-dynamic-analysis'
            Purpose = 'Frida Python instrumentation bindings'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'python-module'; Value = 'frida'; Distribution = 'frida'; PythonPaths = $reversePythonPaths }
            )
        }
        [pscustomobject]@{
            Name = 'uncompyle6'
            Skill = 'reverse-engineering'
            Purpose = 'Python bytecode decompiler'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'uncompyle6' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-analysis\Scripts\uncompyle6.exe') },
                [pscustomobject]@{ Type = 'path'; Value = (Join-Path $toolRoot 'python-re\Scripts\uncompyle6.exe') }
            )
        }
        [pscustomobject]@{
            Name = 'playwright'
            Skill = 'browser-automation'
            Purpose = 'Playwright 浏览器引擎'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'playwright' },
                [pscustomobject]@{ Type = 'path'; Value = (Join-ReverseOptionalPath -Path $appData -ChildPath 'npm\playwright.ps1') }
            )
        }
        [pscustomobject]@{
            Name = 'proxycat'
            Skill = 'pentest-tools'
            Purpose = '代理池管理与轮换'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'proxycat' }
            )
        }
        [pscustomobject]@{
            Name = 'seclists'
            Skill = 'pentest-tools'
            Purpose = 'Security wordlists'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'directory'; Value = (Join-Path $userProfile 'Tools\SecLists') },
                [pscustomobject]@{ Type = 'directory'; Value = 'C:\Tools\SecLists' },
                [pscustomobject]@{ Type = 'directory'; Value = '/usr/share/seclists' }
            )
        }
        [pscustomobject]@{
            Name = 'pentestswarm'
            Skill = 'pentest-tools'
            Purpose = '群体智能自主渗透与 MCP 执行'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'pentestswarm' }
            )
        }
        [pscustomobject]@{
            Name = 'nmap'
            Skill = 'pentest-tools'
            Purpose = '端口扫描与服务识别'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'nmap' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Nmap\nmap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Nmap\nmap.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'wireshark'
            Skill = 'pentest-tools'
            Purpose = 'Wireshark GUI 抓包与 PCAP 分析'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'wireshark' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\Wireshark.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\Wireshark.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\Wireshark.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'tshark'
            Skill = 'pentest-tools'
            Purpose = 'Wireshark CLI 协议解析与 PCAP 字段提取'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'tshark' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\tshark.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\tshark.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\tshark.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'dumpcap'
            Skill = 'pentest-tools'
            Purpose = 'Wireshark CLI 抓包采集'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'dumpcap' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\dumpcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\dumpcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\dumpcap.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'capinfos'
            Skill = 'pentest-tools'
            Purpose = 'PCAP 元数据、时间范围与包计数统计'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'capinfos' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\capinfos.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\capinfos.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\capinfos.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'editcap'
            Skill = 'pentest-tools'
            Purpose = 'PCAP 裁剪、转换与去重'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'editcap' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\editcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\editcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\editcap.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'mergecap'
            Skill = 'pentest-tools'
            Purpose = '多个 PCAP/PCAPNG 文件合并'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'mergecap' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\mergecap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\mergecap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\mergecap.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'text2pcap'
            Skill = 'pentest-tools'
            Purpose = '文本/十六进制转 PCAP 用于协议复现检查'
            VersionArgs = @('-v')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'text2pcap' },
                [pscustomobject]@{ Type = 'path'; Value = 'E:\wireshark\text2pcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\Wireshark\text2pcap.exe' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files (x86)\Wireshark\text2pcap.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'binwalk'
            Skill = 'firmware-pentest'
            Purpose = '固件提取与分析'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'binwalk' }
            )
        }
        [pscustomobject]@{
            Name = 'yara'
            Skill = 'malware-analysis'
            Purpose = '恶意软件规则匹配引擎'
            VersionArgs = @('--version')
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'yara' },
                [pscustomobject]@{ Type = 'path'; Value = 'C:\Program Files\yara\yara.exe' }
            )
        }
        [pscustomobject]@{
            Name = 'pwntools'
            Skill = 'reverse-engineering'
            Purpose = 'CTF pwn 利用开发框架'
            FixedVersion = 'v0.5.0'
            VersionArgs = @()
            Fallbacks = @(
                [pscustomobject]@{ Type = 'command'; Value = 'pwntools' },
                [pscustomobject]@{ Type = 'command'; Value = 'pwn' }
            )
        }
    )
}

function Get-ReverseSkillRoot {
    [CmdletBinding()]
    param()

    return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
}

function Resolve-ReversePathTemplate {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Value
    }

    $resolved = $Value
    $replacements = @{
        '%USERPROFILE%' = (Get-ReverseUserProfilePath)
        '%LOCALAPPDATA%' = [string]([Environment]::GetEnvironmentVariable('LOCALAPPDATA'))
        '%APPDATA%' = [string]([Environment]::GetEnvironmentVariable('APPDATA'))
        '%TEMP%' = [string]([Environment]::GetEnvironmentVariable('TEMP'))
        '%SKILL_ROOT%' = Get-ReverseSkillRoot
    }

    foreach ($key in $replacements.Keys) {
        $resolved = $resolved.Replace($key, $replacements[$key])
    }

    return $resolved
}

function ConvertTo-ReverseHashtable {
    [CmdletBinding()]
    param(
        [AllowNull()]
        $InputObject
    )

    if ($null -eq $InputObject) {
        return $null
    }
    if ($InputObject -is [string] -or $InputObject.GetType().IsPrimitive -or $InputObject -is [decimal]) {
        return $InputObject
    }
    if ($InputObject -is [System.Collections.IDictionary]) {
        $map = [ordered]@{}
        foreach ($key in $InputObject.Keys) {
            $map[[string]$key] = ConvertTo-ReverseHashtable -InputObject $InputObject[$key]
        }
        return $map
    }
    if ($InputObject -is [System.Management.Automation.PSCustomObject]) {
        $map = [ordered]@{}
        foreach ($property in $InputObject.PSObject.Properties) {
            $map[$property.Name] = ConvertTo-ReverseHashtable -InputObject $property.Value
        }
        return $map
    }
    if ($InputObject -is [System.Collections.IEnumerable] -and -not ($InputObject -is [string])) {
        $items = @()
        foreach ($item in $InputObject) {
            $items += ,(ConvertTo-ReverseHashtable -InputObject $item)
        }
        return $items
    }

    return $InputObject
}

function Read-ReverseJsonAsHashtable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $json = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    return ConvertTo-ReverseHashtable -InputObject $json
}

function Get-ReverseBootstrapManifestPath {
    [CmdletBinding()]
    param()

    return Join-Path (Get-ReverseSkillRoot) 'scripts\bootstrap-manifest.json'
}

function Get-ReverseBootstrapCatalog {
    [CmdletBinding()]
    param()

    if ((Get-Variable -Name 'ReverseBootstrapCatalog' -Scope Script -ErrorAction SilentlyContinue) -and $script:ReverseBootstrapCatalog) {
        return $script:ReverseBootstrapCatalog
    }

    $path = Get-ReverseBootstrapManifestPath
    if (-not (Test-Path -LiteralPath $path)) {
        $script:ReverseBootstrapCatalog = @()
        return $script:ReverseBootstrapCatalog
    }

    $json = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    $catalog = @()
    foreach ($capability in @($json.capabilities)) {
        $clone = [pscustomobject]@{}
        foreach ($property in $capability.PSObject.Properties) {
            $value = $property.Value
            if ($value -is [string]) {
                $value = Resolve-ReversePathTemplate -Value $value
            }
            elseif ($value -is [System.Collections.IEnumerable] -and -not ($value -is [string])) {
                $items = @()
                foreach ($item in $value) {
                    if ($item -is [string]) {
                        $items += Resolve-ReversePathTemplate -Value $item
                    }
                    else {
                        $items += $item
                    }
                }
                $value = $items
            }
            elseif ($null -ne $value -and $value -is [System.Management.Automation.PSCustomObject]) {
                $propCount = @($value.PSObject.Properties).Count
                if ($propCount -gt 0) {
                    $map = [ordered]@{}
                    foreach ($subProperty in $value.PSObject.Properties) {
                        $subValue = $subProperty.Value
                        if ($subValue -is [string]) {
                            $subValue = Resolve-ReversePathTemplate -Value $subValue
                        }
                        $map[$subProperty.Name] = $subValue
                    }
                    $value = [pscustomobject]$map
                }
            }
            Add-Member -InputObject $clone -NotePropertyName $property.Name -NotePropertyValue $value
        }
        $catalog += $clone
    }

    $script:ReverseBootstrapCatalog = $catalog
    return $script:ReverseBootstrapCatalog
}

function Get-ReverseBootstrapDefinition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return Get-ReverseBootstrapCatalog | Where-Object { $_.name -eq $Name } | Select-Object -First 1
}

function Get-ClaudeMcpConfigPath {
    [CmdletBinding()]
    param()

    if (-not [string]::IsNullOrWhiteSpace($env:CLAUDE_MCP_CONFIG)) {
        return $env:CLAUDE_MCP_CONFIG
    }
    $profilePath = Get-ReverseUserProfilePath
    return Join-Path (Join-Path $profilePath '.claude') 'mcp.json'
}

function Get-CodexConfigPath {
    [CmdletBinding()]
    param()

    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_CONFIG_PATH)) {
        return $env:CODEX_CONFIG_PATH
    }
    $profilePath = Get-ReverseUserProfilePath
    return Join-Path (Join-Path $profilePath '.codex') 'config.toml'
}

function Get-ClaudeMcpServerNames {
    [CmdletBinding()]
    param()

    $configPath = Get-ClaudeMcpConfigPath
    if (-not (Test-Path -LiteralPath $configPath)) {
        return @()
    }

    try {
        $json = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -eq $json.mcpServers) {
            return @()
        }
        return @($json.mcpServers.PSObject.Properties.Name)
    }
    catch {
        return @()
    }
}

function Get-CodexMcpServerNames {
    [CmdletBinding()]
    param()

    $configPath = Get-CodexConfigPath
    if (-not (Test-Path -LiteralPath $configPath)) {
        return @()
    }

    $pattern = '^\[mcp_servers\.([^\].]+)\]\s*$'
    $names = @()
    foreach ($match in Select-String -LiteralPath $configPath -Pattern $pattern) {
        if ($match.Matches.Count -gt 0) {
            $names += $match.Matches[0].Groups[1].Value
        }
    }

    return @($names | Sort-Object -Unique)
}

function Get-ReverseMcpServerNames {
    [CmdletBinding()]
    param()

    $names = @()
    $names += @(Get-ClaudeMcpServerNames)
    $names += @(Get-CodexMcpServerNames)
    return @($names | Sort-Object -Unique)
}

function Test-ReverseTcpPort {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [string]$TargetHost = '127.0.0.1'
    )

    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($TargetHost, $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(1000, $false)
        if (-not $connected) {
            $client.Close()
            return $false
        }
        $client.EndConnect($async)
        $client.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Test-ReverseMcpHttp {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [string]$TargetHost = '127.0.0.1',

        [int]$TimeoutMs = 3000
    )

    try {
        $body = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
        $uri = "http://${TargetHost}:$Port/mcp"
        $req = [System.Net.HttpWebRequest]::Create($uri)
        $req.Method = 'POST'
        $req.ContentType = 'application/json'
        $req.Timeout = $TimeoutMs
        $req.ReadWriteTimeout = $TimeoutMs
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $req.ContentLength = $bytes.Length
        $reqStream = $req.GetRequestStream()
        $reqStream.Write($bytes, 0, $bytes.Length)
        $reqStream.Close()
        $resp = $req.GetResponse()
        $statusCode = [int]$resp.StatusCode
        $resp.Close()
        return $statusCode -eq 200
    }
    catch {
        return $false
    }
}

function Add-ReverseProcessPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Container)) {
        return
    }

    $separator = [System.IO.Path]::PathSeparator
    $entries = @($env:PATH -split [regex]::Escape([string]$separator)) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    if ($entries -contains $Path) {
        return
    }

    if ([string]::IsNullOrWhiteSpace($env:PATH)) {
        $env:PATH = $Path
    }
    else {
        $env:PATH = "$Path$separator$env:PATH"
    }
}

function Resolve-ReverseCommandCandidate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $commands = @(Get-Command -Name $Name -All -ErrorAction SilentlyContinue)
    if ($commands.Count -eq 0) {
        return $null
    }

    if ($Name -in @('python', 'python3')) {
        foreach ($candidate in ($commands | Where-Object { $_.CommandType -eq 'Application' })) {
            & $candidate.Source --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        return $null
    }

    if ($Name -in @('npm', 'npx', 'pnpm', 'yarn', 'corepack')) {
        $cmdShim = $commands | Where-Object { $_.CommandType -eq 'Application' -and $_.Source -match '\.cmd$' } | Select-Object -First 1
        if ($cmdShim) {
            return $cmdShim
        }

        $application = $commands | Where-Object { $_.CommandType -eq 'Application' } | Select-Object -First 1
        if ($application) {
            return $application
        }
    }

    return ($commands | Select-Object -First 1)
}

function Get-ReverseCapabilityState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $definition = Get-ReverseBootstrapDefinition -Name $Name
    if ($null -eq $definition) {
        return $null
    }

    $registered = $false
    if ($definition.PSObject.Properties['mcpNames']) {
        $registeredNames = Get-ReverseMcpServerNames
        foreach ($candidate in @($definition.mcpNames)) {
            if ($registeredNames -contains $candidate) {
                $registered = $true
                break
            }
        }
    }

    $serviceOnline = $false
    $mcpHttpVerified = $false
    if ($definition.PSObject.Properties['servicePort'] -and $definition.servicePort) {
        $serviceOnline = Test-ReverseTcpPort -Port ([int]$definition.servicePort)
        # If TCP passes, attempt HTTP MCP protocol-level handshake for higher confidence
        if ($serviceOnline) {
            $mcpHttpVerified = Test-ReverseMcpHttp -Port ([int]$definition.servicePort)
        }
    }

    $toolReady = $false
    try {
        $toolSpec = Resolve-ReverseToolSpec -Name $Name
        $toolReady = [bool]$toolSpec.Available
    }
    catch {
        $toolReady = $false
    }

    $verificationMode = if ($definition.PSObject.Properties['verificationMode']) { [string]$definition.verificationMode } else { '' }
    $ready = $toolReady
    if ($definition.PSObject.Properties['mcpNames']) {
        switch ($verificationMode) {
            'service-and-registration' {
                $ready = $registered -and $serviceOnline
            }
            'service-or-registration' {
                $ready = $registered -or $serviceOnline
            }
            default {
                if ($definition.bootstrapKind -eq 'npm-mcp') {
                    $ready = $registered -and $toolReady
                }
                else {
                    $ready = $registered -or $toolReady
                }
            }
        }
    }

    return [pscustomobject]@{
        Name = $definition.name
        BootstrapKind = $definition.bootstrapKind
        CanAutoInstall = [bool]$definition.canAutoInstall
        DocsUrl = [string]$definition.docsUrl
        Ready = $ready
        Registered = $registered
        ServiceOnline = $serviceOnline
        McpHttpVerified = $mcpHttpVerified
    }
}

function Get-ReverseToolDefinition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $definition = Get-ReverseToolCatalog | Where-Object { $_.Name -eq $Name } | Select-Object -First 1
    if ($null -eq $definition) {
        throw "Unknown reverse tool: $Name"
    }

    $bootstrap = Get-ReverseBootstrapDefinition -Name $Name
    if ($null -ne $bootstrap) {
        foreach ($property in $bootstrap.PSObject.Properties) {
            if (-not $definition.PSObject.Properties[$property.Name]) {
                Add-Member -InputObject $definition -NotePropertyName $property.Name -NotePropertyValue $property.Value
            }
        }
    }

    return $definition
}

function Resolve-ReverseToolSpec {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $definition = Get-ReverseToolDefinition -Name $Name
    $fixedVersion = if ($definition.PSObject.Properties['FixedVersion']) { [string]$definition.FixedVersion } else { '' }

    foreach ($candidate in $definition.Fallbacks) {
        if (-not $candidate.PSObject.Properties['Value'] -or [string]::IsNullOrWhiteSpace([string]$candidate.Value)) {
            continue
        }

        switch ($candidate.Type) {
            'command' {
                $cmd = Resolve-ReverseCommandCandidate -Name $candidate.Value
                if ($null -ne $cmd) {
                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $true
                        IsDirectory = $false
                        Source = 'Get-Command'
                        ResolvedPath = $cmd.Source
                        Command = $cmd.Source
                        PrefixArgs = @()
                        VersionArgs = $definition.VersionArgs
                        FixedVersion = $fixedVersion
                    }
                }
            }
            'path' {
                if (Test-Path -LiteralPath $candidate.Value) {
                    Add-ReverseProcessPath -Path (Split-Path -Path $candidate.Value -Parent)
                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $true
                        IsDirectory = $false
                        Source = 'FallbackPath'
                        ResolvedPath = $candidate.Value
                        Command = $candidate.Value
                        PrefixArgs = @()
                        VersionArgs = $definition.VersionArgs
                        FixedVersion = $fixedVersion
                    }
                }
            }
            'directory' {
                if (Test-Path -LiteralPath $candidate.Value -PathType Container) {
                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $false
                        IsDirectory = $true
                        Source = 'FallbackDirectory'
                        ResolvedPath = $candidate.Value
                        Command = ''
                        PrefixArgs = @()
                        VersionArgs = @()
                        FixedVersion = $fixedVersion
                    }
                }
            }
            'file' {
                if (Test-Path -LiteralPath $candidate.Value -PathType Leaf) {
                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $false
                        IsDirectory = $false
                        Source = 'FallbackFile'
                        ResolvedPath = $candidate.Value
                        Command = ''
                        PrefixArgs = @()
                        VersionArgs = @()
                        FixedVersion = $fixedVersion
                    }
                }
            }
            'python-module' {
                $moduleName = [string]$candidate.Value
                $distributionName = if ($candidate.PSObject.Properties['Distribution']) { [string]$candidate.Distribution } else { $moduleName }
                foreach ($pythonPath in @($candidate.PythonPaths)) {
                    if ([string]::IsNullOrWhiteSpace([string]$pythonPath) -or -not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
                        continue
                    }

                    & $pythonPath -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$moduleName') else 1)" *> $null
                    if ($LASTEXITCODE -ne 0) {
                        continue
                    }

                    $moduleVersion = ''
                    try {
                        $moduleVersion = [string](& $pythonPath -c "import importlib.metadata as m; print(m.version('$distributionName'))" 2>$null | Select-Object -First 1)
                    }
                    catch {
                        $moduleVersion = ''
                    }

                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $false
                        IsDirectory = $false
                        Source = 'PythonModule'
                        ResolvedPath = "$pythonPath :: $moduleName"
                        Command = ''
                        PrefixArgs = @()
                        VersionArgs = @()
                        FixedVersion = $moduleVersion
                    }
                }
            }
            'java-jar' {
                if (Test-Path -LiteralPath $candidate.Value) {
                    $java = Resolve-ReverseToolSpec -Name 'java'
                    if (-not $java.Available -or [string]::IsNullOrWhiteSpace([string]$java.Command)) {
                        continue
                    }
                    return [pscustomobject]@{
                        Name = $definition.Name
                        Skill = $definition.Skill
                        Purpose = $definition.Purpose
                        Available = $true
                        IsExecutable = $true
                        IsDirectory = $false
                        Source = 'FallbackJavaJar'
                        ResolvedPath = $candidate.Value
                        Command = $java.Command
                        PrefixArgs = @('-jar', $candidate.Value)
                        VersionArgs = @('-jar', $candidate.Value, '--version')
                        FixedVersion = $fixedVersion
                    }
                }
            }
        }
    }

    return [pscustomobject]@{
        Name = $definition.Name
        Skill = $definition.Skill
        Purpose = $definition.Purpose
        Available = $false
        IsExecutable = $false
        IsDirectory = $false
        Source = 'Missing'
        ResolvedPath = ''
        Command = ''
        PrefixArgs = @()
        VersionArgs = $definition.VersionArgs
        FixedVersion = $fixedVersion
    }
}

function Get-ReverseToolVersion {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Spec
    )

    if (-not $Spec.Available) {
        return ''
    }
    if ($Spec.PSObject.Properties['FixedVersion'] -and -not [string]::IsNullOrWhiteSpace([string]$Spec.FixedVersion)) {
        return [string]$Spec.FixedVersion
    }
    if ([string]::IsNullOrWhiteSpace([string]$Spec.Command) -or @($Spec.VersionArgs).Count -eq 0) {
        return ''
    }

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $rawLines = & $Spec.Command @($Spec.VersionArgs) 2>&1 | Select-Object -First 20
        $cleanLines = New-Object System.Collections.Generic.List[string]
        foreach ($line in $rawLines) {
            $text = ([string]$line).Trim()
            if (-not $text -or $text -match '^Module manifest file error' -or $text -match '^\s*->\s*Invalid line' -or $text -match '^INFO:') {
                continue
            }
            $cleanLines.Add($text)
        }

        $versionLine = $cleanLines | Where-Object { $_ -match '(?i)(?:^|[\s,])v?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?' } | Select-Object -First 1
        if ($versionLine) {
            return $versionLine
        }
        if ($cleanLines.Count -gt 0) {
            return $cleanLines[0]
        }
        return ''
    }
    catch {
        return ''
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Invoke-ReverseTool {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter()]
        [string[]]$Arguments = @()
    )

    $spec = Resolve-ReverseToolSpec -Name $Name
    if (-not $spec.Available) {
        throw "Missing required CLI tool: $Name"
    }
    if ($spec.PSObject.Properties['IsExecutable'] -and -not [bool]$spec.IsExecutable) {
        throw "Tool '$Name' is available at '$($spec.ResolvedPath)' but is not an executable command."
    }
    if ([string]::IsNullOrWhiteSpace([string]$spec.Command)) {
        throw "Tool '$Name' is available but does not expose an executable command."
    }

    & $spec.Command @($spec.PrefixArgs + $Arguments)
    return $LASTEXITCODE
}

function Get-ReverseToolReport {
    [CmdletBinding()]
    param(
        [string[]]$Names
    )

    $selectedNames = if ($null -ne $Names -and @($Names).Count -gt 0) { $Names } else { (Get-ReverseToolCatalog).Name }

    foreach ($name in $selectedNames) {
        $spec = Resolve-ReverseToolSpec -Name $name
        $capabilityState = Get-ReverseCapabilityState -Name $name
        [pscustomobject]@{
            Name = $spec.Name
            Skill = $spec.Skill
            Purpose = $spec.Purpose
            Available = $spec.Available
            IsExecutable = if ($spec.PSObject.Properties['IsExecutable']) { $spec.IsExecutable } else { -not [string]::IsNullOrWhiteSpace([string]$spec.Command) }
            IsDirectory = if ($spec.PSObject.Properties['IsDirectory']) { $spec.IsDirectory } else { $false }
            ResolvedPath = $spec.ResolvedPath
            Source = $spec.Source
            Version = Get-ReverseToolVersion -Spec $spec
            BootstrapKind = if ($capabilityState) { $capabilityState.BootstrapKind } else { '' }
            CanAutoInstall = if ($capabilityState) { $capabilityState.CanAutoInstall } else { $false }
            DocsUrl = if ($capabilityState) { $capabilityState.DocsUrl } else { '' }
            Ready = if ($capabilityState) { $capabilityState.Ready } else { $spec.Available }
            McpRegistered = if ($capabilityState) { $capabilityState.Registered } else { $false }
            ServiceOnline = if ($capabilityState) { $capabilityState.ServiceOnline } else { $false }
            McpHttpVerified = if ($capabilityState) { $capabilityState.McpHttpVerified } else { $false }
        }
    }
}
