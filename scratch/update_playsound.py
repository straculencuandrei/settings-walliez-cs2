import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

sftp = ssh.open_sftp()
with sftp.file('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs', 'r') as f:
    lines = f.readlines()

new_lines = []
in_play_sound = False
skip_until_brace = False

new_play_sound_code = """    private static void PlaySoundToPlayer(CCSPlayerController player, string soundEvent, string soundPath)
    {
        try
        {
            if (player == null || !player.IsValid || player.IsBot || player.IsHLTV)
                return;

            // 1. Emit native Source 2 sound event (safe, non-blocking, matches workshop VPK)
            string ev = !string.IsNullOrEmpty(soundEvent) ? soundEvent : ExtractSoundEvent(new Dictionary<string, object>(), soundPath);
            if (!string.IsNullOrEmpty(ev))
            {
                player.EmitSound(ev);
                return;
            }

            // 2. Fallback to client command
            if (!string.IsNullOrEmpty(soundPath))
            {
                string soundToPlay = soundPath.Trim().Replace("\\"", "").Replace(";", "");
                if (soundToPlay.EndsWith(".vsnd", StringComparison.OrdinalIgnoreCase))
                    soundToPlay += "_c";
                player.ExecuteClientCommand($"play {soundToPlay}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MVP Sound Error] Failed to play sound: {ex.Message}");
        }
    }
"""

i = 0
replaced = False
while i < len(lines):
    line = lines[i]
    if "private static void PlaySoundToPlayer" in line:
        # replace entire method until end of method
        new_lines.append(new_play_sound_code)
        # advance until the closing brace of PlaySoundToPlayer
        brace_count = 0
        found_open = False
        while i < len(lines):
            if "{" in lines[i]:
                brace_count += lines[i].count("{")
                found_open = True
            if "}" in lines[i]:
                brace_count -= lines[i].count("}")
            if found_open and brace_count == 0:
                i += 1
                break
            i += 1
        replaced = True
        continue
    new_lines.append(line)
    i += 1

print(f"Replaced PlaySoundToPlayer: {replaced}")

with sftp.file('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs', 'w') as f:
    f.writelines(new_lines)
sftp.close()

# Rebuild and redeploy
print(run("cd /home/csgoserver/cs2-custom-mvp && dotnet build -c Release"))
print(run("cp /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll"))
print(run("systemctl restart cs2.service"))
print("Deployed and restarted!")

ssh.close()
