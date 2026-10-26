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
    private void TestPointRoundStart()
    {
        Console.WriteLine("[TEST_POINT] Running test on round start...");
        try
        {
            var pcc = Utilities.CreateEntityByName<CPointClientCommand>("point_clientcommand");
            if (pcc == null)
            {
                Console.WriteLine("[TEST_POINT] Failed to create point_clientcommand entity!");
                return;
            }
            pcc.DispatchSpawn();
            Console.WriteLine("[TEST_POINT] Spawned point_clientcommand entity successfully!");
            
            var bot = Utilities.GetPlayers().Find(p => p != null && p.IsValid);
            if (bot != null)
            {
                Console.WriteLine($"[TEST_POINT] Sending command to {bot.PlayerName}...");
                pcc.AcceptInput("Command", bot, bot, "echo HELLO_FROM_TEST");
                Console.WriteLine("[TEST_POINT] AcceptInput finished successfully!");
            }
            pcc.Remove();
            Console.WriteLine("[TEST_POINT] Removed entity successfully!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[TEST_POINT] Exception: {ex}");
        }
    }
}
EOF
"""
stdin, stdout, stderr = ssh.exec_command(script)
ssh.close()
