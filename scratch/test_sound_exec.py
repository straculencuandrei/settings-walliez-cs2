import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /home/csgoserver/cs2-custom-mvp/TestPoint.cs
using System;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;

public partial class MVPSoundsGoldKingZ
{
    private void TestSoundPlayback(CCSPlayerController player, string soundPath)
    {
        Console.WriteLine($"[TEST_SOUND] Testing playback for {player.PlayerName}: {soundPath}");
        try
        {
            // Test Method 1: ExecuteClientCommand
            Console.WriteLine("[TEST_SOUND] Calling ExecuteClientCommand...");
            player.ExecuteClientCommand($"play {soundPath}");
            Console.WriteLine("[TEST_SOUND] ExecuteClientCommand returned successfully!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[TEST_SOUND] Exception in ExecuteClientCommand: {ex}");
        }
    }
}
EOF
cd /home/csgoserver/cs2-custom-mvp && dotnet build -c Release
cp /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.* /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/
chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/
systemctl restart cs2
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
print("Restarting CS2, waiting 15s...")
time.sleep(15)

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 25 --no-pager")
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
