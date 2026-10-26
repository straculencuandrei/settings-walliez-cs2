import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/TestPccPlugin.cs
using System;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;

public class TestPccPlugin : BasePlugin
{
    public override string ModuleName => "TestPCC";
    public override string ModuleVersion => "1.0";

    [ConsoleCommand("css_testpcc", "Test point_clientcommand")]
    public void OnTestPcc(CCSPlayerController? caller, CommandInfo info)
    {
        Console.WriteLine("[TEST_PCC] css_testpcc called!");
        try
        {
            var pcc = Utilities.CreateEntityByName<CPointClientCommand>("point_clientcommand");
            if (pcc == null)
            {
                Console.WriteLine("[TEST_PCC] pcc is null!");
                return;
            }
            pcc.DispatchSpawn();
            Console.WriteLine("[TEST_PCC] pcc spawned!");

            var target = caller ?? Utilities.GetPlayers().Find(p => p != null && p.IsValid);
            if (target != null)
            {
                Console.WriteLine($"[TEST_PCC] Issuing command to {target.PlayerName}...");
                pcc.AcceptInput("Command", target, target, "echo TEST_PCC_SUCCESS");
                Console.WriteLine("[TEST_PCC] AcceptInput succeeded!");
            }
            pcc.Remove();
            Console.WriteLine("[TEST_PCC] pcc removed cleanly!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[TEST_PCC] Exception: {ex}");
        }
    }
}
EOF

cat << 'EOF' > /tmp/TestPccPlugin.csproj
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="CounterStrikeSharp.API" Version="1.0.368" />
  </ItemGroup>
</Project>
EOF

cd /tmp && dotnet build TestPccPlugin.csproj -c Release
mkdir -p /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/TestPCC
cp /tmp/bin/Release/net8.0/TestPccPlugin.* /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/TestPCC/
chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/TestPCC
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
