import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
rm -rf /tmp/test_color_dir
mkdir -p /tmp/test_color_dir
cat << 'EOF' > /tmp/test_color_dir/TestColor.cs
using System;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Translations;
using CounterStrikeSharp.API.Modules.Utils;

public class TestColor
{
    public static void Main()
    {
        string msg = "{gold}[MVP] {grey}| {white}Previewing: {gold}Stiu feat WALLI3Z{white}...";
        string formatted = msg.ReplaceColorTags();
        Console.WriteLine("RESULT: " + formatted);
        foreach (char c in formatted)
        {
            if (c < 32)
                Console.Write($"[0x{(int)c:X2}]");
            else
                Console.Write(c);
        }
        Console.WriteLine();
    }
}
EOF

cat << 'EOF' > /tmp/test_color_dir/TestColor.csproj
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

cd /tmp/test_color_dir && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
