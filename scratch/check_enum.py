import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

script = """
cat << 'EOF' > /tmp/enum_test.cs
using System;
using CounterStrikeSharp.API.Core;

class Program {
    static void Main() {
        foreach (var val in Enum.GetNames(typeof(PlayerConnectedState))) {
            Console.WriteLine("PlayerConnectedState: " + val);
        }
    }
}
EOF

cat << 'EOF' > /tmp/enum_test.csproj
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="CounterStrikeSharp.API">
      <HintPath>/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll</HintPath>
    </Reference>
  </ItemGroup>
</Project>
EOF

cd /tmp && /usr/bin/dotnet build -c Release enum_test.csproj
sed -i 's/"version": "8.0.0"/"version": "10.0.0"/' /tmp/bin/Release/net8.0/enum_test.runtimeconfig.json
/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/dotnet/dotnet /tmp/bin/Release/net8.0/enum_test.dll
"""
print(run(script))

ssh.close()
