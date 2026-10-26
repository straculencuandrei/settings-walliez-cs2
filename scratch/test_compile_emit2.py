import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

test_cs = """
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

public static class TestEmit {
    public static void Test(CCSPlayerController player, string soundEvent) {
        var recipients = new RecipientFilter { player };
        if (player.PlayerPawn.Value != null && player.PlayerPawn.Value.IsValid) {
            player.PlayerPawn.Value.EmitSound(soundEvent, recipients);
        } else {
            player.EmitSound(soundEvent, recipients);
        }
    }
}
"""

sftp = ssh.open_sftp()
with sftp.file("/home/csgoserver/cs2-custom-mvp/TestEmit.cs", "w") as f:
    f.write(test_cs)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("cd /home/csgoserver/cs2-custom-mvp && dotnet build")
out = stdout.read().decode('utf-8')
print("Compile output:\n", out)

ssh.exec_command("rm -f /home/csgoserver/cs2-custom-mvp/TestEmit.cs")
ssh.close()
