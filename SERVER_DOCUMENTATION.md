# CS2 Dedicated Server Documentation & Session Backup

## Server Details & SSH Credentials
- **Host / IP**: `81.181.113.120`
- **SSH Port**: `22`
- **Username**: `root`
- **Server User**: `csgoserver` (UID 1000)
- **CS2 Root Directory**: `/home/csgoserver/server-cs2`
- **CS2 Binary**: `/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/cs2`
- **CounterStrikeSharp Directory**: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp`
- **Source Code Repositories on Server**:
  - `AdminPlus` (`wlzadmin`): `/home/csgoserver/cs2-adminplus`
  - `MenuManagerCore` (`/menu` WASD menu engine): `/home/csgoserver/cs2-menumanager`
  - `WeaponPaints` (Skins, Knives, Gloves): `/home/csgoserver/cs2-weaponpaints`
- **Systemd Service**: `cs2.service` (`systemctl restart cs2`, `systemctl status cs2`)

---

## What Was Fixed In This Session

### 1. Panel Scrolling Issues Resolved (`wlzadmin` / `AdminPlus`)
- **Root Cause**:
  1. `ProcessMenuInput` in `AdminPlus.InternalMenu.cs` recorded input snapshot transitions before running the debounce check. Rapid presses or presses during the grace window were swallowed, and held keys were discarded as duplicates, completely blocking scrolling down.
  2. The sliding window tried to display 5 items per view at `fontSize-m`. In CS2 Panorama's center HTML container (~140px), 5 items plus header and footer clipped out of the screen on 4:3 stretched resolutions.
- **Fix**:
  1. Implemented reliable edge-triggered button detection (`justPressed`) using bitwise operations (`PlayerButtons`).
  2. Added smooth auto-repeat scrolling when holding `W` or `S` (250ms initial delay, 90ms repeat cadence).
  3. Window size set to 4 visible items with `fontSize-s`, keeping all lines and control shortcuts (`Move`, `Select`, `Back`, `Exit`) fully visible without vertical clipping on any aspect ratio.
  4. Smooth edge-pinned scrolling offset with wraparound navigation at boundaries.

### 2. Alt Slots and Template Placeholders Removed
- **Removed Entries**:
  - `Server_Owner_Alt`
  - `Server_Owner_Alt2`
  - `EXAMPLE_STAFF_ADMIN_REPLACE_STEAMID`
  - `EXAMPLE_STAFF_MOD_REPLACE_STEAMID`
- **Preserved Existing Admins** (Strictly Preserved):
  - `Server_Owner` (SteamID: `76561199135800683`, Immunity: 100, Flags: `@css/root`, Groups: `#wlz/owner`, `#css/admin`)
  - `Fiora` (SteamID: `76561198855173662`, Immunity: 90, Groups: `#wlz/admin`)
  - `Piskeletto_pablo` (SteamID: `76561199209803186`, Immunity: 90, Groups: `#wlz/admin`)
  - `远征契约` (SteamID: `76561199489270994`, Immunity: 90, Groups: `#wlz/admin`)
  - `Andreea3` (SteamID: `76561199144991900`, Immunity: 50, Groups: `#wlz/mod`)

### 3. Visuals & Emojis Cleaned Up (`wlzadmin`)
- Stripped emojis (`✅`, `❌`, `◄`, `💡`, `•`) across all language files (`lang/en.json`, `de.json`, `fr.json`, `tr.json`, `ru.json`, `pt-BR.json`, `pl.json`).
- Removed CS2 console/chat color tags (`{green}`, `{red}`, `{yellow}`, `{default}`) from center HTML strings.
- Replaced noisy selector markers (`►[ • ... ]◄`) with a clean highlighted cursor (`> Option` in `#ffffff` with `#facc15` indicator).
- Styled the header in `#4ade80` (green) with muted index indicators (`#9ca3af`), and controls in cyan (`#38bdf8`).
- Fixed a translation format exception bug in `ShowAddAdminConfirmMenu` (`Admin.Added` parameter mismatch).

### 4. `/menu` WASD Panel Fixed & Modernized (`MenuManagerCore` & `CustomMenu`)
- **Root Cause**:
  1. `MenuManagerCore` used `player.Buttons.ToString()` comparison every tick inside `OnPluginTick()`. If holding W or S, `IsEqualButtons` returned true and ignored all held inputs. Tapping quickly caused dropped frames and stuck navigation.
  2. `MenuLinesCount` defaulted to 6. Combined with `fontSize-sm`, title, and footer, 8 lines vertically overflowed the Panorama center HUD bounds on 4:3 stretched resolutions, cutting off the bottom items and controls.
  3. Language files used clunky brackets and arrow characters (`► [MENUITEM] ◄`) which shifted text alignment and looked cluttered.
- **Fix**:
  1. Replaced string-based button checking with bitwise edge detection (`justPressed`) and smooth auto-repeat (280ms initial delay, 120ms repeat) when holding W or S.
  2. Added boundary wraparound (pressing Down on last item loops to top; pressing Up on top item loops to bottom).
  3. Updated `MenuLinesCount` from 6 to 4 in config and code, using `fontSize-s` for a compact, clean layout that never clips on 4:3 stretched or standard resolutions.
  4. Added dynamic item position indicator `(selected/total)` next to the menu title.
  5. Cleaned selection indicator to gold `> ` with white text, and indented unselected items with `&nbsp;&nbsp;` so lines never jump or shake when moving cursor.
  6. Modernized footer across `en.json`, `ru.json`, `tr.json`, and `zh-Hans.json` to `[W/S] Move  [E] Select  [R] Exit`.
  7. Built and deployed to `plugins/MenuManagerCore/MenuManagerCore.dll`, with persistent source saved in `/home/csgoserver/cs2-menumanager`.

### 5. Weapon Switching Lockup Bug Fixed (`WeaponPaints`)
- **Bug Description**:
  When choosing a skin or knife from the website or in-game command, or running `/wp`, the player was permanently unable to switch weapons (1, 2, 3 or scroll wheel). The player would be locked into the current weapon/knife and forced back to it until dying.
- **Root Cause**:
  1. In `RefreshWeapons` (lines 1961-2095 in original code) and `GiveOnItemPickup`, the plugin called `item.Value?.AddEntityIOEvent("Kill", ...)` directly on carried weapons.
  2. In CS2 Source 2, calling the engine entity I/O `"Kill"` destroys the CBasePlayerWeapon entity but does **NOT** remove the handle from `CCSPlayer_WeaponServices.m_hMyWeapons`.
  3. The plugin additionally gave dummy items (`CsItem.USPS`, `CsItem.DefaultKnifeCT`) into `m_hMyWeapons` and immediately executed `"Kill"` on them.
  4. As a result, `m_hMyWeapons` was polluted with multiple dead, dangling handles. When the player tried to switch weapons, `Weapon_Switch` failed on the invalid handles, aborted the weapon switch, and forced the player back to the active weapon. The player was trapped until death cleared the pawn.
  5. Additionally, in `OnCommandRefresh` (`/wp`), `GetPlayerData` was dispatched via `Task.Run` in the background without awaiting, calling `RefreshWeapons` before the database had even returned the new skins.
- **Fix**:
  1. Completely removed all calls to `AddEntityIOEvent("Kill")` and dummy weapon spawns.
  2. Implemented safe in-place weapon updating: loops through existing `myWeapons` and calls `GivePlayerWeaponSkin(player, weapon)` directly.
  3. For knives, `GivePlayerWeaponSkin` natively invokes Valve's Source 2 engine input `ChangeSubclass` (`weapon.AcceptInput("ChangeSubclass", null, null, itemD.ToString())`), which morphs the knife model in-place without destroying entities or corrupting inventory handles.
  4. For guns, `FallbackPaintKit`, `FallbackSeed`, `FallbackWear`, dynamic attributes, nametags, and stickers update in-place with `Utilities.SetStateChanged`.
  5. In `GiveOnItemPickup`, removed the `networkedVector.Count == 1` block that was spawning and killing dummy weapons on pickup.
  6. In `OnCommandRefresh` (`/wp`) and `OnCommandSkinRefresh`, properly queued `RefreshWeapons` onto `Server.NextFrame` after `await WeaponSync.GetPlayerData(playerInfo2)` finishes, guaranteeing the latest website/database skins load seamlessly without delaying or breaking gameplay.
  7. Built and deployed to `plugins/WeaponPaints/WeaponPaints.dll`, with persistent source saved in `/home/csgoserver/cs2-weaponpaints`.

---

## Active Configuration Files

### `admins.json`
Location: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/admins.json`
```json
{
  "Server_Owner": {
    "identity": "76561199135800683",
    "immunity": 100,
    "flags": [
      "@css/root"
    ],
    "groups": [
      "#wlz/owner",
      "#css/admin"
    ]
  },
  "76561198855173662": {
    "identity": "76561198855173662",
    "name": "Fiora",
    "immunity": 90,
    "groups": [
      "#wlz/admin"
    ]
  },
  "76561199209803186": {
    "identity": "76561199209803186",
    "name": "Piskeletto_pablo",
    "immunity": 90,
    "groups": [
      "#wlz/admin"
    ]
  },
  "76561199489270994": {
    "identity": "76561199489270994",
    "name": "远征契约",
    "immunity": 90,
    "groups": [
      "#wlz/admin"
    ]
  },
  "76561199144991900": {
    "identity": "76561199144991900",
    "name": "Andreea3",
    "immunity": 50,
    "groups": [
      "#wlz/mod"
    ]
  }
}
```

### `admin_groups.json`
Location: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/admin_groups.json`
- `#wlz/owner`: Immunity 100, flags `@css/root`
- `#wlz/admin`: Immunity 75
- `#wlz/mod`: Immunity 50
- `#css/admin`: Immunity 75
- `#css/mod`: Immunity 50

---

## Plugin Building & Deployment Workflow

### 1. `AdminPlus` (`/admin`, `wlzadmin`)
Source: `/home/csgoserver/cs2-adminplus`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/AdminPlus/AdminPlus.dll`
```bash
cd /home/csgoserver/cs2-adminplus
dotnet build
cp /home/csgoserver/cs2-adminplus/BuildOutput/plugins/AdminPlus/AdminPlus.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/AdminPlus/AdminPlus.dll
systemctl restart cs2
```

### 2. `CustomMenu` (`/menu`, `/wlzmenu`)
Source: `/home/csgoserver/cs2-custommenu`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu/CustomMenu.dll`
Config: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/CustomMenu/CustomMenu.json`
- Modern internal menu engine matching `/admin` (4-line viewport, edge-triggered input, holding auto-repeat, wraparound).
- Clean, compact option titles without redundant command tags (e.g., `Skins`, `Knives`, `Gloves`, `Agents`).
```bash
cd /home/csgoserver/cs2-custommenu
dotnet build -c Release
cp /home/csgoserver/cs2-custommenu/bin/Release/net8.0/CustomMenu.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu/CustomMenu.dll
systemctl restart cs2
```

### 3. `Custom_MVP_Sounds` (`!mvp`, `/mvp`, `!mvps`, `!anthem`, `!mvpsound`)
Source: `/home/csgoserver/cs2-custom-mvp`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll`
Config: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/config.json`
MVP Settings: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json`
Addon Manager: `MultiAddonManager` (`cfg/multiaddonmanager/multiaddonmanager.cfg`)
- Modern WASD Menu System: Integrated custom WASD navigation matching `/menu` and `/admin` (4-line viewport, smooth auto-repeat scrolling, edge-triggered button detection, wraparound, gold `> ` cursor).
- Commands: `!mvp`, `/mvp`, `!mvps`, `!anthem`, `!mvpsound`, `css_mvp`, or via `/menu`.
- Features: Track preview, per-player selection cookies, MySQL persistence, and automatic client downloading of compiled `.vsnd_c` workshop music assets.
- Audio Standard: Automatically trimmed to 10.0 seconds with a smooth 1-second fadeout from 9.0s to 10.0s (`afade=t=out:st=9:d=1`) at 44.1 kHz 16-bit PCM WAV.
- Round Transition: Sends `stopsound` to all players on `EventRoundStart` to cleanly cut off any ongoing previews or audio.
- Workshop Audio: Mounted via `MultiAddonManager` (`mm_extra_addons "3827657422"` in `cfg/multiaddonmanager/multiaddonmanager.cfg`), ensuring all connecting players automatically download and hear the compiled `.vsnd_c` tracks (`wlzMVP`).
- High-Speed Importer: `Add_MVP.bat` (and `add_mvp_cli.py`) allows 1-click drag-and-drop importing of any audio file, automatic 10s fadeout trimming, resource compilation, server config updates, and VPK cache sync in ~3 seconds.
```bash
cd /home/csgoserver/cs2-custom-mvp
dotnet publish -c Release -o /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/
systemctl restart cs2
```

### 4. `WeaponPaints` (`/wp`, Skins, Knives)
Source: `/home/csgoserver/cs2-weaponpaints`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/WeaponPaints/WeaponPaints.dll`
- Weapon switching bug completely fixed (removed entity kill/USP dummy loop, safe in-place `GivePlayerWeaponSkin` / native subclass update).
```bash
cd /home/csgoserver/cs2-weaponpaints
dotnet build
cp /home/csgoserver/cs2-weaponpaints/bin/Debug/net8.0/WeaponPaints.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/WeaponPaints/WeaponPaints.dll
systemctl restart cs2
```

### 5. `MenuManagerCore` (Menu Backend)
Source: `/home/csgoserver/cs2-menumanager`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/MenuManagerCore/MenuManagerCore.dll`
```bash
cd /home/csgoserver/cs2-menumanager
dotnet build
cp /home/csgoserver/cs2-menumanager/bin/Debug/net8.0/MenuManagerCore.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/MenuManagerCore/MenuManagerCore.dll
systemctl restart cs2
```

---

### 6. `MVPAnthem` Audio Architecture & Dedicated Server Crash Diagnostics
Source: `/home/csgoserver/cs2-mvpanthem`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/MVPAnthem/MVPAnthem.dll`

#### A. Dedicated Server Audio Architecture & Client Command Dispatch
- **Root Cause of Server Crash**:
  1. A Linux CS2 dedicated server runs headless (`-dedicated`) without audio output hardware; its internal sound output device pointer (`0x801540` in `libsoundsystem.so`) is `NULL`.
  2. Executing `player.ExecuteClientCommandFromServer("play ...")` or `Server.ExecuteCommand("play ...")` executes the `play` command **locally on the dedicated server**, not the client.
  3. When the dedicated server attempts to process local audio playback in `libsoundsystem.so`, instruction `cmp 0x88(%rbx), %rax` dereferences offset `0x88` on the `NULL` device pointer, immediately terminating the server with a segmentation fault (`status 11/SEGV`).
  4. Additionally, mutating networked entity properties (`mvpPlayer.MVPs = 0`, `mvpPlayer.MusicKitMVPs = 0`, `@event.Nomusic = 1`) inside `EventRoundMvp` (HookMode.Pre) corrupts the engine's internal music-kit resolver, which also causes null-pointer crashes.
- **Audio Playback Rules & Solutions**:
  1. **Execute on Client, NEVER on Server**: Always use `player.ExecuteClientCommand($"play {sound}")`. This transmits the command over the network to execute on the player's game console, where audio hardware exists. It never executes on the headless server.
  2. **44.1 kHz MP3 Standard with Original Quality**: Any incoming audio file is converted to MP3 at **44.1 kHz** (`-codec:a libmp3lame -q:a 0 -ar 44100`), preserving the full original bitrate, channels, and dynamics without artificial downsampling.
  3. **FastDL Delivery**: CS2 clients require HTTP FastDL to download custom sounds. Nginx on port 80 now mirrors `/var/www/fastdl/` -> `/home/csgoserver/server-cs2/game/csgo/`, and `server.cfg` has `sv_downloadurl "http://81.181.113.120/fastdl/"` and `sv_allowdownload 1`. Connecting clients automatically download the tracks over HTTP upon connecting.
  4. **Native Sound Events**: For native CS2 audio (e.g. `Music.Valve_MVP`, `Weapon_AWP.Single`), dispatch via `player.EmitSound(soundEvent, recipients)`.
  5. **NEVER mutate entity MVP or music properties in round event hooks**: Leave `@event.Nomusic`, `mvpPlayer.MVPs`, and `mvpPlayer.MusicKitMVPs` intact.
  6. **Always defer round MVP actions to `Server.NextFrame`**: Wrapping audio playback, chat broadcast, and center HTML banner generation inside `Server.NextFrame(() => { try { ... } catch (Exception ex) { ... } })` guarantees the Source 2 engine finishes its internal round-end event chain before plugin actions occur.

#### B. First-Spawn Weapon Skins Resolution (`WeaponPaints`)
- **Root Cause**:
  1. When a player connects to the server, `EventPlayerConnectFull` triggers an asynchronous MySQL query (`GetPlayerData`).
  2. The player frequently spawns into the game (`OnPlayerSpawn`) *before* the asynchronous database query returns.
  3. Originally, when `GetPlayerData` completed, it only populated memory dictionaries and never pushed skin/knife updates to the player's active pawn.
  4. As a result, the player was stuck with default weapons until they died and respawned next round.
- **Resolution**:
  1. In `OnClientFullConnect`: As soon as `await WeaponSync.GetPlayerData(playerInfo2)` finishes, it schedules `Server.NextFrame(() => RefreshWeapons(p, force: true))` to immediately apply custom knife, weapon skins, gloves, agent, and music kit.
  2. In `OnPlayerSpawn`: Calls `Server.NextFrame(() => RefreshWeapons(player, force: true))`, ensuring that whenever a player spawns, all their held weapons and knife are immediately transformed in-place without needing to die.

#### C. Permissions Hierarchy & Menu Visibility
- Custom permission checks in `HasAccess()` must always include a root administrator override:
  `if (AdminManager.PlayerHasPermissions(player, "@css/root")) return true;`
- Implement group inheritance: `#wlz/owner` automatically inherits `#wlz/admin` and `#wlz/mod` permissions, and `#wlz/admin` inherits `#wlz/mod`.

#### C. Client Console Output Analysis (Round Transition Diagnostics)
When a round concludes and resets, the CS2 game engine outputs several client-side diagnostics:
- **`[Client] CL: Forcing ExecuteQueuedOperations due to entity slot re-use (176 basemodelentity)`**:
  - *Status*: Completely normal engine operation.
  - *Explanation*: At round end, ragdolls, dropped weapons, and bot pawns are recycled into entity pool slots for the next round. The client flushes its queued interpolation and rendering operations before slot re-allocation.
- **`Annotation: Cleared 0 annotations` / `Annotation: Error loading file : Missing file ''`**:
  - *Status*: Harmless engine cleanup.
  - *Explanation*: Source 2 cleans up map annotation vectors (used for tutorials/bomb site markers) when a round terminates.
- **`[SoundSystemLowLevel] Audio device starved 244 samples`**:
  - *Status*: Transient client-side buffer underrun (~5.5ms at 44.1 kHz).
  - *Explanation*: Occurs during the frame where the round concludes and the MVP banner / scoreboard renders, causing a microsecond client CPU spike. Inaudible and normal in CS2.
- **`[CL CommandQueue] CQ: Server set re-sync at cmd 6561`**:
  - *Status*: Standard sub-tick network synchronization.
  - *Explanation*: The server sets a re-synchronization baseline for client sub-tick user commands at round freeze time.
- **`[SteamNetSockets] Waited 2.8ms for SteamNetworkingSockets lock`**:
  - *Status*: Minor thread lock contention.
  - *Explanation*: Multiple game threads (render, net, physics) accessed Steam networking state concurrently during round state transition. A 2.8ms wait is negligible and within normal tolerances.

---

### 7. MVP Anthem Studio & Safe Deployment Tooling

To ensure you can add anthems at any time with zero risk of crashing the server, use the included tooling:

#### Option A: Visual Web Studio (Recommended)
Double-click `Launch_MVP_Studio.bat` (or execute `python add_mvp_ui.py`):
1. **Interactive Audio Scrubber**: Drag and drop any audio file (`.mp3`, `.wav`, etc.). Scrub the waveform, listen with the live volume slider, and click **"Set Start Here"** to pick the exact drop.
2. **Crash-Safe CS2 Sound Event Pairing**: Select from verified sound events (e.g. `Ubersoft.roundmvpanthem_01`, `Music.Valve_MVP`, `Survival.WinnerFanfare`).
3. **Live Deployment Log Console**: The real-time log window displays every phase of deployment as it streams from the server:
   - SSH & SFTP connection status
   - Staging upload & server-side FFmpeg trimming
   - Automated JSON configuration backup (`.bak`)
   - Enforcement of `RemovePlayerInGameMvp: false`
   - Linux ownership validation (`chown csgoserver:csgoserver`)
   - Instant in-memory hot-reload confirmation

#### Option B: High-Speed CLI Script
Execute `add_mvp.py` with custom arguments:
```powershell
# Trim starting at 0:45 for 8 seconds:
python add_mvp.py "C:\path\to\song.mp3" --name "Drop Beat" --start 00:45 --duration 8

# Add to specific category and permission:
python add_mvp.py "C:\path\to\song.mp3" --name "VIP Banger" --category "VIP Anthems" --permission "@css/vip"
```
#### Option C: 1-Click Client Sync Tool (`Sync_MVP_Anthems.bat`)
Double-click `Sync_MVP_Anthems.bat` on any player's Windows PC:
- Auto-detects the local CS2 game installation across all Steam drives (C:, D:, E:).
- Syncs all custom MP3 anthems from the FastDL HTTP endpoint (`http://81.181.113.120/fastdl/sounds/mvp/`) directly into `game/csgo/sounds/mvp/`.
- Players can also type `/mvp` in-game and choose "FastDL Sound Pack Info" to view the download link and instructions.


