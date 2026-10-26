import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

test_cs = """using System;
using CounterStrikeSharp.API.Core;

public class TestEmitSound
{
    public void Test(CCSPlayerController player)
    {
        // Check if EmitSound exists on player or player.PlayerPawn.Value
        player.EmitSound("test");
    }
}
"""

run("echo '" + test_cs.replace("'", "'\\''") + "' > /home/csgoserver/cs2-custom-mvp/TestEmit.cs")
print(run("cd /home/csgoserver/cs2-custom-mvp && dotnet build"))
run("rm -f /home/csgoserver/cs2-custom-mvp/TestEmit.cs")

ssh.close()
