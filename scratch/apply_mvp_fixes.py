import paramiko
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

# 1. Update MVP_Settings.json
mvp_settings = {
  "mvp_stiufeatwalli3zmastered": {
    "CanBePreview": True,
    "Message_Chat": True,
    "Message_Center_Bottom": True,
    "Message_Center_Bottom_InSecs": 10,
    "MVP_Kit_Name": "Stiu feat WALLI3Z",
    "Sound_Path_1": "sounds/mvp/stiufeatwalli3zmastered.vsnd",
    "Sound_Event": "CustomMVP.stiufeatwalli3zmastered"
  },
  "mvp_gta_iii_full_theme_hq": {
    "CanBePreview": True,
    "Message_Chat": True,
    "Message_Center_Bottom": True,
    "Message_Center_Bottom_InSecs": 10,
    "MVP_Kit_Name": "GTA III Theme",
    "Sound_Path_1": "sounds/mvp/gta_iii_full_theme_hq.vsnd",
    "Sound_Event": "CustomMVP.gta_iii_full_theme_hq"
  }
}

sftp = ssh.open_sftp()
with sftp.file('/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json', 'w') as f:
    f.write(json.dumps(mvp_settings, indent=2))
run("mkdir -p /home/csgoserver/cs2-custom-mvp/config /home/csgoserver/cs2-custom-mvp/Config")
try:
    with sftp.file('/home/csgoserver/cs2-custom-mvp/config/MVP_Settings.json', 'w') as f:
        f.write(json.dumps(mvp_settings, indent=2))
except:
    pass
print("Updated MVP_Settings.json")

# 2. Modify Custom_MVP_Sounds.cs
with sftp.file('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs', 'r') as f:
    code = f.read().decode('utf-8')

# Fix 1: Remove stopsound in OnRoundStart
old_round_start = """    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;

        HUDTimer_Center?.Kill();
        HUDTimer_Center = null;
        HUDTimer_Center_Bottom?.Kill();
        HUDTimer_Center_Bottom = null;

        Globals.Show_Center = false;
        Globals.Show_Center_Bottom = false;

        foreach (var player in Helper.GetAllController())
        {
            if (player != null && player.IsValid && !player.IsBot && !player.IsHLTV)
            {
                try
                {
                    player.ExecuteClientCommand("stopsound");
                }
                catch { }
            }
        }

        return HookResult.Continue;
    }"""

new_round_start = """    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;

        HUDTimer_Center?.Kill();
        HUDTimer_Center = null;
        HUDTimer_Center_Bottom?.Kill();
        HUDTimer_Center_Bottom = null;

        Globals.Show_Center = false;
        Globals.Show_Center_Bottom = false;

        return HookResult.Continue;
    }"""

if old_round_start in code:
    code = code.replace(old_round_start, new_round_start)
    print("Fix 1 applied: Cleaned OnRoundStart (removed illegal stopsound loop)")
else:
    print("Fix 1 warning: old_round_start not matched exactly, checking lines...")

# Fix 2: PlaySoundToPlayer use player.EmitSound
old_play_sound = """    private static void PlaySoundToPlayer(CCSPlayerController player, string soundEvent, string soundPath)
    {
        try
        {
            if (player == null || !player.IsValid || player.IsBot || player.IsHLTV)
                return;

            string soundToPlay = !string.IsNullOrEmpty(soundPath) ? soundPath : soundEvent;
            if (string.IsNullOrEmpty(soundToPlay)) return;

            if (soundToPlay.EndsWith(".vsnd_c", StringComparison.OrdinalIgnoreCase))
                soundToPlay = soundToPlay[..^2];

            soundToPlay = soundToPlay.Trim().Replace("\"", "").Replace(";", "");

            player.ExecuteClientCommand($"play {soundToPlay}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MVP Sound Error] Failed to play sound: {ex.Message}");
        }
    }"""

new_play_sound = """    private static void PlaySoundToPlayer(CCSPlayerController player, string soundEvent, string soundPath)
    {
        try
        {
            if (player == null || !player.IsValid || player.IsBot || player.IsHLTV)
                return;

            // 1. First priority: Emit native Source 2 sound event (safe, non-blocking, supports workshop VPKs)
            string ev = !string.IsNullOrEmpty(soundEvent) ? soundEvent : ExtractSoundEvent(new Dictionary<string, object>(), soundPath);
            if (!string.IsNullOrEmpty(ev))
            {
                player.EmitSound(ev);
                return;
            }

            // 2. Fallback to client command if no sound event is registered
            if (!string.IsNullOrEmpty(soundPath))
            {
                string soundToPlay = soundPath.Trim().Replace("\"", "").Replace(";", "");
                if (soundToPlay.EndsWith(".vsnd", StringComparison.OrdinalIgnoreCase))
                    soundToPlay += "_c";
                player.ExecuteClientCommand($"play {soundToPlay}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MVP Sound Error] Failed to play sound: {ex.Message}");
        }
    }"""

if old_play_sound in code:
    code = code.replace(old_play_sound, new_play_sound)
    print("Fix 2 applied: PlaySoundToPlayer now uses player.EmitSound(ev)")
else:
    print("Fix 2 warning: old_play_sound not matched exactly")

# Fix 3: Remove 180ms throttle so menu renders continuously on tick without pop-in / flicker
old_render_throttle = """            // Throttle rendering to only when state is dirty OR every 180ms to refresh the display,
            // preventing network send queue starvation / buffer overflow (64Hz unthrottled flooding).
            if (!Globals.Show_Center)
            {
                if (state.IsDirty || (now - state.LastRenderTimeUtc).TotalMilliseconds >= 180)
                {
                    RenderMenu(player, state);
                    state.IsDirty = false;
                    state.LastRenderTimeUtc = now;
                }
            }"""

new_render_tick = """            // Render menu smoothly on every tick without throttling delay,
            // which prevents Panorama from re-triggering the entrance/pop-in animation repeatedly.
            if (!Globals.Show_Center)
            {
                RenderMenu(player, state);
                state.IsDirty = false;
            }"""

if old_render_throttle in code:
    code = code.replace(old_render_throttle, new_render_tick)
    print("Fix 3 applied: RenderMenu now updates smoothly on tick (no pop-in flicker)")
else:
    print("Fix 3 warning: old_render_throttle not matched exactly")

sftp = ssh.open_sftp()
with sftp.file('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs', 'w') as f:
    f.write(code)
sftp.close()
print("Saved modified Custom_MVP_Sounds.cs")

# 3. Build Release
print("Building Custom_MVP_Sounds (Release)...")
build_out = run("cd /home/csgoserver/cs2-custom-mvp && dotnet build -c Release")
print(build_out)

if "Build succeeded" in build_out:
    print("Deploying DLL to plugins directory...")
    run("cp /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll")
    print("Restarting CS2 service...")
    run("systemctl restart cs2.service")
    print("Done! CS2 service restarted.")

ssh.close()
