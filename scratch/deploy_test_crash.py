import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
rm -rf /tmp/test_crash
mkdir -p /tmp/test_crash
cat << 'EOF' > /tmp/test_crash/TestCrash.cs
using System;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;

public class TestCrash : BasePlugin
{
    public override string ModuleName => "TestCrash";
    public override string ModuleVersion => "1.0";

    private bool _tested = false;
    private int _tickCount = 0;

    public override void Load(bool hotReload)
    {
        Server.PrintToConsole("[TEST_CRASH] TestCrash Loaded successfully!");
        Server.ExecuteCommand("sv_hibernate_when_empty 0");
        RegisterListener<Listeners.OnTick>(OnTick);
    }

    private void OnTick()
    {
        _tickCount++;
        if (_tickCount % 50 == 0)
        {
            Server.PrintToConsole($"[TEST_CRASH] OnTick count: {_tickCount}");
        }
        if (_tested || _tickCount < 100) return;
        _tested = true;
        Server.PrintToConsole("[TEST_CRASH] Triggering RunAllTests!");
        RunAllTests();
    }

    private void RunAllTests()
    {
        var players = Utilities.GetPlayers();
        Server.PrintToConsole($"[TEST_CRASH] Found {players.Count} players in Utilities.GetPlayers()");
        foreach (var p in players)
        {
            if (p == null || !p.IsValid) continue;
            Server.PrintToConsole($"[TEST_CRASH] Testing on: {p.PlayerName} (Slot {p.Slot}, Bot: {p.IsBot})");

            // Test 1: point_clientcommand echo
            try
            {
                var pcc = Utilities.CreateEntityByName<CPointClientCommand>("point_clientcommand");
                if (pcc != null)
                {
                    pcc.DispatchSpawn();
                    pcc.AcceptInput("Command", p, p, "echo PCC_WORKS");
                    pcc.Remove();
                    Server.PrintToConsole("[TEST_CRASH] point_clientcommand echo SUCCEEDED!");

                    pcc = Utilities.CreateEntityByName<CPointClientCommand>("point_clientcommand");
                    pcc.DispatchSpawn();
                    pcc.AcceptInput("Command", p, p, "play sounds/mvp/stiufeatwalli3zmastered.vsnd");
                    pcc.Remove();
                    Server.PrintToConsole("[TEST_CRASH] point_clientcommand play SUCCEEDED!");
                }
            }
            catch (Exception ex)
            {
                Server.PrintToConsole("[TEST_CRASH] point_clientcommand EXCEPTION: " + ex);
            }

            // Test 2: ExecuteClientCommand
            try
            {
                Server.PrintToConsole("[TEST_CRASH] Testing ExecuteClientCommand on " + p.PlayerName);
                p.ExecuteClientCommand("echo ECC_WORKS");
                Server.PrintToConsole("[TEST_CRASH] ExecuteClientCommand echo SUCCEEDED!");

                p.ExecuteClientCommand("play sounds/mvp/stiufeatwalli3zmastered.vsnd");
                Server.PrintToConsole("[TEST_CRASH] ExecuteClientCommand play SUCCEEDED!");
            }
            catch (Exception ex)
            {
                Server.PrintToConsole("[TEST_CRASH] ExecuteClientCommand EXCEPTION: " + ex);
            }
        }
    }
}
EOF

cat << 'EOF' > /tmp/test_crash/TestCrash.csproj
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="CounterStrikeSharp.API" Version="1.0.368" />
  </ItemGroup>
</Project>
EOF

cd /tmp/test_crash && dotnet build -c Release
cp /tmp/test_crash/bin/Release/net8.0/TestCrash.* /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/TestCrash/
chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/TestCrash/
systemctl restart cs2
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
