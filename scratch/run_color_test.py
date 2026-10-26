import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
rm -rf /tmp/test_color_proj
mkdir -p /tmp/test_color_proj
cat << 'EOF' > /tmp/test_color_proj/Program.cs
using System;
using CounterStrikeSharp.API.Core.Translations;

class Program
{
    static void Main()
    {
        string raw = "{gold}[MVP] {grey}| {white}Previewing: {gold}Stiu feat WALLI3Z{white}...";
        string formatted = raw.ReplaceColorTags();
        Console.WriteLine("Formatted: " + formatted);
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

cat << 'EOF' > /tmp/test_color_proj/test_color_proj.csproj
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

cd /tmp/test_color_proj && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== RUN OUTPUT ===")
print(stdout.read().decode('utf-8', errors='ignore'))
print("=== RUN ERR ===")
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
