import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
rm -rf /tmp/reflect_proj
mkdir -p /tmp/reflect_proj
cat << 'EOF' > /tmp/reflect_proj/Program.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Core;

class Program {
    static void Main() {
        var t2 = typeof(CCSPlayerController);
        var m1 = t2.GetMethod("ExecuteClientCommand");
        var m = typeof(NativeAPI).GetMethod("IssueClientCommand");
        Console.WriteLine($"IssueClientCommand parameters: {string.Join(", ", System.Linq.Enumerable.Select(m.GetParameters(), p => p.ParameterType.Name + " " + p.Name))}");
        
        // Also print what ExecuteClientCommand passes
        var mExec = typeof(CCSPlayerController).GetMethod("ExecuteClientCommand");
        var mSlot = typeof(CCSPlayerController).GetProperty("Slot");
        Console.WriteLine($"Player.Slot type: {mSlot?.PropertyType.Name}");
    }
}
EOF

cat << 'EOF' > /tmp/reflect_proj/reflect.csproj
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="CounterStrikeSharp.API" Version="1.0.368" />
  </ItemGroup>
</Project>
EOF

cd /tmp/reflect_proj && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
