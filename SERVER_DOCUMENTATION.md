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

### 6. `Custom_MVP_Sounds` Architecture & Dedicated Server Crash Diagnostics
Source: `/home/csgoserver/cs2-custom-mvp`
Binary: `/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll`
Active Workshop Addon: `3827657422` (Item Name: `wlzMVP`) mounted via `multiaddonmanager.cfg`

#### A. Dedicated Server Audio Architecture & The "play" Command Deadlock Crash
- **Bug Symptoms**:
  - Whenever a player pressed "Preview Track (10s)" in the `/mvp` menu or when an MVP won a round, the server would immediately freeze tick processing.
  - No chat or commands could be sent; client packet queues filled up (`recv queue overflow 100 messages already queued`).
  - Exactly 30 seconds after the freeze, the server process crashed with:
    ```text
    WatchDog! Server took too long to process (probably infinite loop)
    FATAL ERROR: Watchdog timeout exceeded, exiting
    ```
    or in systemd logs: `Main process exited, code=dumped, status=6/ABRT` / `status=11/SEGV` in `libtier0.so`.
- **Root Cause Analysis**:
  1. A Linux dedicated server runs headless (`-dedicated`) with no audio hardware or sound driver loaded. Its internal sound system interface (`libsoundsystem.so`) does not initialize hardware audio stream playback buffers.
  2. Developers often assume that `player.ExecuteClientCommand($"play {sound}")` runs *only* on the client's local game console.
  3. **The Engine Reality**: In CounterStrikeSharp, `ExecuteClientCommand` dispatches to `IVEngineServer2::ClientCommand(clientIndex, command)`. The dedicated server's internal engine command parser receives `"play ..."` and dispatches it into `libsoundsystem.so`'s sound mixer worker thread.
  4. Because the server is headless, the sound mixer blocks on an uninitialized audio hardware mutex. This deadlocks the server's main tick loop.
  5. The tick loop stops advancing entirely. After 30 seconds of no tick updates, Valve's watchdog thread (`EngineWatchdogThread`) triggers a fatal assertion crash to abort what it assumes is an infinite loop.
  6. Conversely, executing `ExecuteClientCommandFromServer("play ...")` routes through server ConVar lookups and dereferences a null sound output device pointer (`0x801540` in `libsoundsystem.so`), crashing instantly with a segmentation fault (`status 11/SEGV` at offset `+0x88`).
- **The Native Source 2 Solution (`EmitSound` with `RecipientFilter`)**:
  - **NEVER** use `ExecuteClientCommand("play ...")` or `ExecuteClientCommandFromServer("play ...")` for sound playback on a dedicated server.
  - Use Source 2's native networked sound emission API:
    ```csharp
    var recipients = new RecipientFilter { player };
    player.EmitSound(soundEvent, recipients);
    ```
  - **Why this never crashes**: `player.EmitSound` serializes a `CSVCMsg_Sounds` Protobuf network message and transmits it directly over the UDP socket to the client. The dedicated server process never touches audio mixing buffers, never accesses hardware drivers, and never blocks the tick loop.
  - For round MVP broadcasts (to all non-muted players):
    ```csharp
    foreach (var target in Helper.GetAllController())
    {
        if (target == null || !target.IsValid || target.IsBot || target.IsHLTV) continue;
        if (!Globals.client_mute.ContainsKey(target.SteamID))
        {
            var recipients = new RecipientFilter { target };
            target.EmitSound(soundEvent, recipients);
        }
    }
    ```
  - In `Custom_MVP_Sounds`, `PlaySoundToPlayer(player, soundEvent, soundPath)` resolves the sound event key (`CustomMVP.{track_id}`) and broadcasts via `player.EmitSound` safely.

#### B. WASD Menu HUD Persistence & The 200ms Fade-Out Rule
- **Bug Symptoms**:
  - The `/mvp` menu was continuously popping in and out, blinking on screen, or disappearing when navigating between options.
- **Root Cause**:
  - In CounterStrikeSharp / CS2, `player.PrintToCenterHtml` messages are ephemeral HUD elements rendered by Panorama.
  - By default, Panorama begins fading out center HTML messages after ~200-250ms unless a new message refreshes the container.
  - When the menu was throttled (e.g. updated only on 500ms intervals or on key-down events), the HUD element faded out between inputs, creating an annoying flickering / popping effect.
- **Resolution**:
  - In `OnTick()`, when a player has an active menu in `_playerMenuStates`, re-render `RenderMenu(player, state)` every tick while `!Globals.Show_Center`:
    ```csharp
    if (!Globals.Show_Center)
    {
        RenderMenu(player, state);
        state.IsDirty = false;
        state.LastRenderTimeUtc = now;
    }
    ```
  - Continuous per-tick rendering keeps the Panorama center HTML container stably illuminated and 100% flicker-free.
  - The menu automatically yields when round MVP banners (`Globals.Show_Center`) are displayed.

#### C. Audio Trimming, Normalization & 10-Second Fade-Out Standard
- **The Problem**:
  - Songs would play indefinitely after round end, continuing into the freeze time and early combat of the next round.
- **The Specification**:
  - **Duration**: Exactly 10.0 seconds total duration.
  - **Fade-Out**: Smooth 1.0-second volume fadeout starting at second 9.0 and ending at second 10.0 (`afade=t=out:st=9:d=1`).
  - **Encoding**: Clean 44.1 kHz CBR MP3 (libmp3lame, 320 kbps, stereo), strictly stripped of ID3v2/APIC tags that can confuse Valve's `resourcecompiler.exe`.
  - **Automation**: Implemented in `export_clean_mp3.py` and `wlz_mvp_studio.py`, replicating the exact output profile of onlineaudioconverter without requiring web browser interaction.

#### D. Steam Workshop Pipeline & MultiAddonManager Mounting
- **Addon Details**:
  - Workshop Item ID: `3827657422` (Name: `wlzMVP`)
  - Server Mount Configuration: `/home/csgoserver/server-cs2/game/csgo/cfg/multiaddonmanager.cfg`:
    ```cfg
    mm_extra_addons "3827657422"
    ```
- **Asset Compilation Architecture**:
  - Source files reside in `C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP\`.
  - Soundevents KV3 file: `soundevents/soundevents_addon.vsndevts`.
  - Valve's `resourcecompiler.exe` compiles assets into `game\csgo_addons\wlzMVP\soundevents\soundevents_addon.vsndevts_c` and `game\csgo_addons\wlzMVP\sounds\mvp\*.vsnd_c`.
  - CS2 Workshop Tools packages and uploads the final VPK to Steam Workshop. Connecting clients automatically download and mount the VPK before map spawn.

---

### 7. MVP Anthem Studio & Automation Tools

To ensure anthems can be added quickly and reliably with zero risk of crashing the server, use the included tooling:

#### Option A: All-in-One MVP Studio (`wlzMVP_Studio.bat` / `wlz_mvp_studio.py`)
Double-click `wlzMVP_Studio.bat` (or drag and drop audio files onto it):
1. **Interactive Metadata Prompt**: Prompts for Anthem Display Name and optional start time offset (e.g., `00:45` or `32`).
2. **Automated Clean Audio Export**: Converts the source track to 44.1 kHz CBR MP3, trims to exactly 10.0 seconds, and applies a smooth 1-second volume fadeout (`9.0s -> 10.0s`).
3. **KV3 Soundevents Registration**: Updates `soundevents/soundevents_addon.vsndevts` with the new track key (`CustomMVP.{track_id}`).
4. **Valve Resource Compilation**: Invokes `resourcecompiler.exe` to compile the `.mp3` and `.vsndevts` into binary `.vsnd_c` and `.vsndevts_c` assets.
5. **Dedicated Server Config Synchronization**: Updates `MVP_Settings.json` and syncs with the remote server via SFTP.
6. **Workshop Tools Launcher**: Launches the CS2 Workshop Manager to submit the update directly to Workshop Item `3827657422`.

#### Option B: Clean 44.1 kHz Audio Exporter (`Convert_To_Clean_44k_MP3.bat` / `export_clean_mp3.py`)
Drag and drop any audio file onto `Convert_To_Clean_44k_MP3.bat`:
- Implements the exact onlineaudioconverter algorithm: 44.1 kHz CBR, 320 kbps, stereo, stripped ID3 tags.
- Trims to 10.0 seconds with a 1-second smooth volume fadeout from 9.0s to 10.0s.

---

### 8. Troubleshooting & Gotchas Cheat Sheet

| Symptom | Root Cause | Fix / Prevention |
|---|---|---|
| **Server hangs for 30s then crashes on preview/round end** | `ExecuteClientCommand("play ...")` was used on dedicated server; engine sound streamer deadlocks on headless audio device | Use `player.EmitSound(soundEvent, new RecipientFilter { player })`. Never execute `play` via engine console commands. |
| **Server crashes instantly (`status 11/SEGV`) on sound** | `ExecuteClientCommandFromServer("play ...")` was used; dereferences null sound device pointer (`+0x88`) | Use native `EmitSound`. |
| **`/mvp` menu blinks / pops in and out continuously** | CS2 Panorama HUD fades center HTML messages in ~200ms; menu was throttled or event-driven | Call `RenderMenu(player, state)` every tick in `OnTick()` while active and `!Globals.Show_Center`. |
| **Song plays forever past round end** | Audio was not trimmed to round-end duration | Audio tracks must be trimmed to 10.0s with 1.0s fadeout using `export_clean_mp3.py`. |
| **Resource compiler fails with "extraneous tokens"** | Syntax error in `soundevents_addon.vsndevts` KV3 format (missing braces or unquoted keys) | Use `wlz_mvp_studio.py` which formats KV3 soundevents blocks validly. |
| **Players can't hear custom workshop anthem** | Workshop addon not mounted or item ID mismatch | Ensure `mm_extra_addons "3827657422"` is in `multiaddonmanager.cfg` and soundevent name matches `CustomMVP.{track_id}`. |
| **Player weapon switch locked after choosing skin** | `AddEntityIOEvent("Kill")` left dangling handles in `CCSPlayer_WeaponServices.m_hMyWeapons` | Never call `Kill` on player weapon entities; use `AcceptInput("ChangeSubclass")` and dynamic attribute updates. |



