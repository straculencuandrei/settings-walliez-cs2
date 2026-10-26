#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Admin;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;
using Microsoft.Extensions.Localization;
using MySqlConnector;
using Newtonsoft.Json;
using Custom_MVP_Sounds.Config;

namespace Custom_MVP_Sounds;

internal sealed class CMenuOption
{
    public string Text { get; set; } = string.Empty;
    public bool Disabled { get; set; }
    public Action<CCSPlayerController> Callback { get; set; } = _ => { };
}

internal sealed class CMenu
{
    public string Id { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public Action<CCSPlayerController>? CustomBackAction { get; set; }
    public List<CMenuOption> Options { get; } = new();

    public CMenu(string id, string title)
    {
        Id = id;
        Title = title;
    }

    public void AddOption(string text, Action<CCSPlayerController> callback, bool disabled = false)
    {
        Options.Add(new CMenuOption
        {
            Text = text,
            Callback = callback,
            Disabled = disabled
        });
    }
}

internal sealed class CMenuState
{
    public CMenu? ActiveMenu { get; set; }
    public Stack<CMenu> History { get; } = new();
    public int SelectedIndex { get; set; }
    public int ScrollOffset { get; set; }
    public PlayerButtons PreviousButtons { get; set; }
    public DateTime OpenedAtUtc { get; set; } = DateTime.MinValue;
    public DateTime NextScrollRepeatUtc { get; set; } = DateTime.MinValue;
    public bool IsDirty { get; set; } = true;
    public DateTime LastRenderTimeUtc { get; set; } = DateTime.MinValue;
}

public class MVPSoundsGoldKingZ : BasePlugin
{
    public override string ModuleName => "Custom MVP Sounds";
    public override string ModuleVersion => "2.0.0";
    public override string ModuleAuthor => "Walliez / modernized by Antigravity";
    public override string ModuleDescription => "Custom Server MVP Music Pack with WASD Menu";

    internal static IStringLocalizer? Stringlocalizer;
    private CounterStrikeSharp.API.Modules.Timers.Timer? HUDTimer_Center;
    private CounterStrikeSharp.API.Modules.Timers.Timer? HUDTimer_Center_Bottom;

    private readonly Dictionary<int, CMenuState> _playerMenuStates = new();
    private readonly Dictionary<int, DateTime> _previewCooldowns = new();

    public override void Load(bool hotReload)
    {
        Configs.Load(ModuleDirectory);
        Stringlocalizer = Localizer;
        Configs.Shared.CookiesModule = ModuleDirectory;
        Configs.Shared.StringLocalizer = Localizer;

        RegisterEventHandler<EventRoundMvp>(OnEventRoundMvp, HookMode.Pre);
        RegisterEventHandler<EventPlayerConnectFull>(OnEventPlayerConnectFull);
        RegisterEventHandler<EventPlayerDisconnect>(OnPlayerDisconnect);
        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        RegisterListener<Listeners.OnTick>(OnTick);
        RegisterListener<Listeners.OnMapEnd>(OnMapEnd);

        AddCommandListener("say", OnCommandSay);
        AddCommandListener("say_team", OnCommandSay);
        AddCommand("css_mvp", "Open MVP Menu", OnCommandMvp);
        AddCommand("mvp", "Open MVP Menu", OnCommandMvp);
        AddCommand("mvpsound", "Open MVP Menu", OnCommandMvp);
        AddCommand("anthem", "Open MVP Menu", OnCommandMvp);
    }

    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;

        HUDTimer_Center?.Kill();
        HUDTimer_Center = null;
        HUDTimer_Center_Bottom?.Kill();
        HUDTimer_Center_Bottom = null;

        Globals.Show_Center = false;
        Globals.Show_Center_Bottom = false;

        return HookResult.Continue;
    }

    public HookResult OnEventPlayerConnectFull(EventPlayerConnectFull @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;
        var player = @event.Userid;
        if (player == null || !player.IsValid || player.IsBot || player.IsHLTV) return HookResult.Continue;

        var playerid = player.SteamID;
        foreach (var kvp in Configs.GetConfigData().MVP_DefaultMusicKitPerSteam)
        {
            if (kvp.Key.ToString() == playerid.ToString())
            {
                Globals.Choosed_MVP[player.SteamID] = kvp.Value;
                break;
            }
        }

        if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP) &&
            Helper.IsPlayerInGroupPermission(player, Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP))
        {
            Globals.allow_groups[playerid] = true;
        }

        if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP) &&
            Helper.IsPlayerInGroupPermission(player, Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP))
        {
            Globals.client_cantoggle[playerid] = true;
        }

        Helper.PersonData personData = Helper.RetrievePersonDataById(playerid);
        if (!string.IsNullOrEmpty(personData.MusicKit))
        {
            Globals.Choosed_MVP[player.SteamID] = personData.MusicKit;
        }

        if (personData.Client_Mute_MVP)
        {
            Globals.client_mute[player.SteamID] = true;
        }

        if (Configs.GetConfigData().MVP_UseMySql)
        {
            Task.Run(async () =>
            {
                try
                {
                    string mysqlPath = Path.Combine(ModuleDirectory, "config/MySql_Settings.json");
                    if (!File.Exists(mysqlPath)) return;
                    var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(mysqlPath));
                    if (connectionSettings == null) return;

                    var connectionString = new MySqlConnectionStringBuilder
                    {
                        Server = connectionSettings.MySqlHost,
                        Port = (uint)connectionSettings.MySqlPort,
                        Database = connectionSettings.MySqlDatabase,
                        UserID = connectionSettings.MySqlUsername,
                        Password = connectionSettings.MySqlPassword
                    }.ConnectionString;

                    using var connection = new MySqlConnection(connectionString);
                    await connection.OpenAsync();
                    await MySqlDataManager.CreatePersonDataTableIfNotExistsAsync(connection);

                    var result = await MySqlDataManager.RetrievePersonDataByIdAsync(playerid, connection);
                    if (result != null)
                    {
                        if (!string.IsNullOrEmpty(result.MusicKit))
                        {
                            Globals.Choosed_MVP[player.SteamID] = result.MusicKit;
                        }
                        if (result.Client_Mute_MVP)
                        {
                            Globals.client_mute[player.SteamID] = true;
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[MVP MySql] Error connecting: {ex.Message}");
                }
            });
        }

        return HookResult.Continue;
    }

    [CommandHelper(minArgs: 0, usage: "", whoCanExecute: CommandUsage.CLIENT_ONLY)]
    public void OnCommandMvp(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;
        OpenMVPMenu(player);
    }

    public HookResult OnCommandSay(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return HookResult.Continue;
        var eventmessage = info.GetArg(1);
        if (string.IsNullOrWhiteSpace(eventmessage)) return HookResult.Continue;
        string message = eventmessage.Trim();
        string[] MVPInGameMenu = Configs.GetConfigData().MVP_InGameMenu.Split(',');
        if (MVPInGameMenu.Any(cmd => cmd.Equals(message, StringComparison.OrdinalIgnoreCase)))
        {
            OpenMVPMenu(player);
            return HookResult.Handled;
        }
        return HookResult.Continue;
    }

    public void OpenMVPMenu(CCSPlayerController player)
    {
        if (player == null || !player.IsValid) return;
        var playerSteamId = player.SteamID;

        if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP) && !Globals.allow_groups.ContainsKey(playerSteamId))
        {
            string notAllowed = Localizer["player.not.allowed"];
            if (!string.IsNullOrEmpty(notAllowed))
            {
                Helper.AdvancedPrintToChat(player, notAllowed);
            }
            return;
        }

        Dictionary<string, Dictionary<string, object>>? mvpData = LoadMvpSettings();
        if (mvpData == null || mvpData.Count == 0)
        {
            Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}No MVP anthems are currently configured.");
            return;
        }

        var mainMenu = BuildMainMenu(player, mvpData);
        var state = new CMenuState
        {
            ActiveMenu = mainMenu,
            SelectedIndex = 0,
            ScrollOffset = 0,
            OpenedAtUtc = DateTime.UtcNow,
            IsDirty = true
        };
        _playerMenuStates[player.Slot] = state;
    }

    private Dictionary<string, Dictionary<string, object>>? LoadMvpSettings()
    {
        string[] possiblePaths = {
            Path.Combine(ModuleDirectory, "config/MVP_Settings.json"),
            Path.Combine(ModuleDirectory, "../../plugins/MVP-Sounds-GoldKingZ/config/MVP_Settings.json"),
            Path.Combine(ModuleDirectory, "MVP_Settings.json")
        };

        foreach (var p in possiblePaths)
        {
            if (File.Exists(p))
            {
                try
                {
                    string json = File.ReadAllText(p);
                    return JsonConvert.DeserializeObject<Dictionary<string, Dictionary<string, object>>>(json);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[MVP] Error reading {p}: {ex.Message}");
                }
            }
        }
        return null;
    }

    private CMenu BuildMainMenu(CCSPlayerController player, Dictionary<string, Dictionary<string, object>> data)
    {
        var menu = new CMenu("main", "MVP Anthems");
        var personData = Helper.RetrievePersonDataById(player.SteamID);
        bool isMuted = Globals.client_mute.ContainsKey(player.SteamID) || personData.Client_Mute_MVP;

        string currentEquippedKey = string.Empty;
        if (Globals.Choosed_MVP.TryGetValue(player.SteamID, out var key))
        {
            currentEquippedKey = key;
        }
        else if (!string.IsNullOrEmpty(personData.MusicKit))
        {
            currentEquippedKey = personData.MusicKit;
        }

        // Toggle Mute option
        string muteText = isMuted ? "Sound: [MUTED]" : "Sound: [ACTIVE]";
        menu.AddOption(muteText, p =>
        {
            ToggleMute(p);
            // Refresh menu
            var updatedData = LoadMvpSettings() ?? data;
            if (_playerMenuStates.TryGetValue(p.Slot, out var st))
            {
                st.ActiveMenu = BuildMainMenu(p, updatedData);
                st.IsDirty = true;
            }
        });

        // Remove Anthem option
        menu.AddOption("Remove Equipped MVP", p =>
        {
            RemoveEquippedAnthem(p);
            var updatedData = LoadMvpSettings() ?? data;
            if (_playerMenuStates.TryGetValue(p.Slot, out var st))
            {
                st.ActiveMenu = BuildMainMenu(p, updatedData);
                st.IsDirty = true;
            }
        });

        // List each configured anthem
        foreach (var kvp in data)
        {
            string kitKey = kvp.Key;
            var kitDict = kvp.Value;
            string kitName = kitDict.ContainsKey("MVP_Kit_Name") ? kitDict["MVP_Kit_Name"]?.ToString() ?? kitKey : kitKey;
            string hasFlag = kitDict.ContainsKey("FLAGS") ? kitDict["FLAGS"]?.ToString() ?? string.Empty : string.Empty;
            bool isHidden = kitDict.ContainsKey("HIDDEN") && bool.TryParse(kitDict["HIDDEN"]?.ToString(), out bool hVal) && hVal;

            if (isHidden && !string.IsNullOrEmpty(hasFlag) && !Helper.IsPlayerInGroupPermission(player, hasFlag))
                continue;

            bool isEquipped = !string.IsNullOrEmpty(currentEquippedKey) && currentEquippedKey.Equals(kitKey, StringComparison.OrdinalIgnoreCase);
            string optionText = isEquipped ? $"● {kitName} [Equipped]" : kitName;

            menu.AddOption(optionText, p =>
            {
                OpenTrackSubMenu(p, kitKey, kitName, kitDict, hasFlag);
            });
        }

        // Exit
        menu.AddOption("Exit Menu", p => CloseMenu(p));

        return menu;
    }

    private void OpenTrackSubMenu(CCSPlayerController player, string kitKey, string kitName, Dictionary<string, object> kitDict, string hasFlag)
    {
        if (!_playerMenuStates.TryGetValue(player.Slot, out var state)) return;

        bool hasAccess = string.IsNullOrEmpty(hasFlag) || Helper.IsPlayerInGroupPermission(player, hasFlag);
        var subMenu = new CMenu($"track_{kitKey}", kitName);

        // Option 1: Equip
        if (hasAccess)
        {
            subMenu.AddOption("Equip Anthem", p =>
            {
                EquipAnthem(p, kitKey, kitName);
                // Return to main menu
                var data = LoadMvpSettings();
                if (data != null && _playerMenuStates.TryGetValue(p.Slot, out var st))
                {
                    st.History.Clear();
                    st.ActiveMenu = BuildMainMenu(p, data);
                    st.SelectedIndex = 0;
                    st.ScrollOffset = 0;
                }
            });
        }
        else
        {
            subMenu.AddOption("Equip Anthem (VIP Only)", p =>
            {
                Helper.AdvancedPrintToChat(p, "{gold}[MVP] {grey}| {darkred}You need VIP status to equip this anthem.");
            }, disabled: true);
        }

        // Option 2: Preview
        bool canPreview = kitDict.ContainsKey("CanBePreview") && bool.TryParse(kitDict["CanBePreview"]?.ToString(), out bool pVal) && pVal;
        if (canPreview)
        {
            string soundPath = ExtractSoundPath(kitDict);
            string soundEvent = ExtractSoundEvent(kitDict, soundPath);
            if (!string.IsNullOrEmpty(soundPath) || !string.IsNullOrEmpty(soundEvent))
            {
                subMenu.AddOption("Preview Track (10s)", p =>
                {
                    try
                    {
                        if (p == null || !p.IsValid || p.IsBot) return;

                        if (_previewCooldowns.TryGetValue(p.Slot, out var cd) && DateTime.UtcNow < cd)
                        {
                            Helper.AdvancedPrintToChat(p, "{gold}[MVP] {grey}| {white}Please wait before previewing again.");
                            return;
                        }
                        _previewCooldowns[p.Slot] = DateTime.UtcNow.AddSeconds(2);

                        Helper.AdvancedPrintToChat(p, "{gold}[MVP] {grey}| {white}Previewing: {gold}{0}{white}...", kitName);
                        PlaySoundToPlayer(p, soundEvent, soundPath);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[MVP Preview Error] {ex.Message}");
                    }
                });
            }
        }

        // Option 3: Back
        subMenu.AddOption("Back", p =>
        {
            if (_playerMenuStates.TryGetValue(p.Slot, out var st))
            {
                NavigateBack(p, st);
            }
        });

        subMenu.CustomBackAction = p =>
        {
            if (_playerMenuStates.TryGetValue(p.Slot, out var st))
            {
                NavigateBack(p, st);
            }
        };

        if (state.ActiveMenu != null)
        {
            state.History.Push(state.ActiveMenu);
        }
        state.ActiveMenu = subMenu;
        state.SelectedIndex = 0;
        state.ScrollOffset = 0;
        state.IsDirty = true;
    }

    private static string ExtractSoundPath(Dictionary<string, object> kitDict)
    {
        if (kitDict.ContainsKey("Sound_Path_1") && kitDict["Sound_Path_1"] != null)
            return kitDict["Sound_Path_1"].ToString() ?? string.Empty;
        if (kitDict.ContainsKey("Sound_Path") && kitDict["Sound_Path"] != null)
            return kitDict["Sound_Path"].ToString() ?? string.Empty;
        return string.Empty;
    }

    private static string ExtractSoundEvent(Dictionary<string, object> kitDict, string soundPath)
    {
        if (kitDict.ContainsKey("Sound_Event") && kitDict["Sound_Event"] != null)
        {
            string ev = kitDict["Sound_Event"].ToString() ?? string.Empty;
            if (!string.IsNullOrEmpty(ev)) return ev;
        }

        if (!string.IsNullOrEmpty(soundPath))
        {
            string fileName = Path.GetFileName(soundPath);
            if (fileName.EndsWith(".vsnd_c", StringComparison.OrdinalIgnoreCase))
                fileName = fileName[..^7];
            else if (fileName.EndsWith(".vsnd", StringComparison.OrdinalIgnoreCase))
                fileName = fileName[..^5];
            return $"CustomMVP.{fileName}";
        }

        return string.Empty;
    }

    private static void PlaySoundToPlayer(CCSPlayerController player, string soundEvent, string soundPath)
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
    }

    private void EquipAnthem(CCSPlayerController player, string kitKey, string kitName)
    {
        Globals.Choosed_MVP[player.SteamID] = kitKey;
        var personData = Helper.RetrievePersonDataById(player.SteamID);
        Helper.SaveToJsonFile(player.SteamID, kitKey, personData.Client_Mute_MVP, DateTime.Now);

        if (Configs.GetConfigData().MVP_UseMySql)
        {
            SaveToMySqlAsync(player.SteamID, kitKey, personData.Client_Mute_MVP);
        }

        Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}Equipped anthem: {gold}{0}", kitName);
    }

    private void RemoveEquippedAnthem(CCSPlayerController player)
    {
        Globals.Choosed_MVP.Remove(player.SteamID);
        var personData = Helper.RetrievePersonDataById(player.SteamID);
        Helper.SaveToJsonFile(player.SteamID, string.Empty, personData.Client_Mute_MVP, DateTime.Now);

        if (Configs.GetConfigData().MVP_UseMySql)
        {
            SaveToMySqlAsync(player.SteamID, string.Empty, personData.Client_Mute_MVP);
        }

        Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}Removed your equipped MVP anthem.");
    }

    private void ToggleMute(CCSPlayerController player)
    {
        var personData = Helper.RetrievePersonDataById(player.SteamID);
        bool currentlyMuted = Globals.client_mute.ContainsKey(player.SteamID) || personData.Client_Mute_MVP;

        if (currentlyMuted)
        {
            Globals.client_mute.Remove(player.SteamID);
            personData.Client_Mute_MVP = false;
            Helper.SaveToJsonFile(player.SteamID, personData.MusicKit ?? string.Empty, false, DateTime.Now);
            if (Configs.GetConfigData().MVP_UseMySql)
            {
                SaveToMySqlAsync(player.SteamID, personData.MusicKit ?? string.Empty, false);
            }
            Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}MVP sounds {green}ENABLED{white}.");
        }
        else
        {
            if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP) && !Globals.client_cantoggle.ContainsKey(player.SteamID))
            {
                Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {darkred}You do not have permission to mute MVP sounds.");
                return;
            }

            Globals.client_mute[player.SteamID] = true;
            personData.Client_Mute_MVP = true;
            Helper.SaveToJsonFile(player.SteamID, personData.MusicKit ?? string.Empty, true, DateTime.Now);
            if (Configs.GetConfigData().MVP_UseMySql)
            {
                SaveToMySqlAsync(player.SteamID, personData.MusicKit ?? string.Empty, true);
            }
            Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}MVP sounds {red}MUTED{white}.");
        }
    }

    private void SaveToMySqlAsync(ulong steamId, string kitKey, bool isMuted)
    {
        Task.Run(async () =>
        {
            try
            {
                string mysqlPath = Path.Combine(ModuleDirectory, "config/MySql_Settings.json");
                if (!File.Exists(mysqlPath)) return;
                var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(mysqlPath));
                if (connectionSettings == null) return;

                var connectionString = new MySqlConnectionStringBuilder
                {
                    Server = connectionSettings.MySqlHost,
                    Port = (uint)connectionSettings.MySqlPort,
                    Database = connectionSettings.MySqlDatabase,
                    UserID = connectionSettings.MySqlUsername,
                    Password = connectionSettings.MySqlPassword
                }.ConnectionString;

                using var connection = new MySqlConnection(connectionString);
                await connection.OpenAsync();
                await MySqlDataManager.SaveToMySqlAsync(steamId, kitKey, isMuted, DateTime.Now, connection, connectionSettings);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[MVP MySql] Error saving: {ex.Message}");
            }
        });
    }

    public void OnTick()
    {
        // 1. Render MVP banners if active
        if (Globals.Show_Center || Globals.Show_Center_Bottom)
        {
            foreach (var player in Helper.GetAllController())
            {
                if (player == null || !player.IsValid || player.IsBot || player.IsHLTV || Globals.client_mute.ContainsKey(player.SteamID))
                    continue;

                if (Globals.Show_Center)
                {
                    var sb = new StringBuilder();
                    sb.AppendLine(Globals.MVP_Locaraize_Center);
                    sb.AppendLine("</div>");
                    player.PrintToCenterHtml(sb.ToString());
                }
                if (Globals.Show_Center_Bottom)
                {
                    player.PrintToCenter(Globals.MVP_Locaraize_Center_Bottom);
                }
            }
        }

        // 2. Process WASD menu navigation & rendering
        if (_playerMenuStates.Count == 0) return;
        var now = DateTime.UtcNow;

        var slotsToRemove = new List<int>();
        foreach (var (slot, state) in _playerMenuStates)
        {
            var player = Utilities.GetPlayerFromSlot(slot);
            if (player == null || !player.IsValid || player.IsBot)
            {
                slotsToRemove.Add(slot);
                continue;
            }

            if (state.ActiveMenu == null)
            {
                slotsToRemove.Add(slot);
                continue;
            }

            // Read player buttons
            var buttons = player.Buttons;
            var prev = state.PreviousButtons;

            // Exit button (A / Moveleft or R / Reload)
            if (HasButtonJustPressed(PlayerButtons.Moveleft, buttons, prev) || HasButtonJustPressed(PlayerButtons.Reload, buttons, prev))
            {
                state.PreviousButtons = buttons;
                NavigateBack(player, state);
                continue;
            }

            // Select button (E / Use)
            if (HasButtonJustPressed(PlayerButtons.Use, buttons, prev))
            {
                state.PreviousButtons = buttons;
                SelectCurrentOption(player, state);
                continue;
            }

            // Scroll Up (W / Forward) / Down (S / Back)
            bool upActive = buttons.HasFlag(PlayerButtons.Forward);
            bool upJustPressed = upActive && !prev.HasFlag(PlayerButtons.Forward);

            bool downActive = buttons.HasFlag(PlayerButtons.Back);
            bool downJustPressed = downActive && !prev.HasFlag(PlayerButtons.Back);

            if (upJustPressed)
            {
                MoveSelection(state, -1);
                state.NextScrollRepeatUtc = now.AddMilliseconds(250);
            }
            else if (downJustPressed)
            {
                MoveSelection(state, 1);
                state.NextScrollRepeatUtc = now.AddMilliseconds(250);
            }
            else if (upActive && now >= state.NextScrollRepeatUtc)
            {
                MoveSelection(state, -1);
                state.NextScrollRepeatUtc = now.AddMilliseconds(90);
            }
            else if (downActive && now >= state.NextScrollRepeatUtc)
            {
                MoveSelection(state, 1);
                state.NextScrollRepeatUtc = now.AddMilliseconds(90);
            }

            state.PreviousButtons = buttons;

            // Render menu smoothly on every tick without throttling delay,
            // which prevents Panorama from re-triggering the entrance/pop-in animation repeatedly.
            if (!Globals.Show_Center)
            {
                RenderMenu(player, state);
                state.IsDirty = false;
            }
        }

        foreach (var s in slotsToRemove)
        {
            _playerMenuStates.Remove(s);
        }
    }

    private static bool HasButtonJustPressed(PlayerButtons btn, PlayerButtons current, PlayerButtons previous)
    {
        return current.HasFlag(btn) && !previous.HasFlag(btn);
    }

    private static void MoveSelection(CMenuState state, int direction)
    {
        var menu = state.ActiveMenu;
        if (menu == null || menu.Options.Count == 0) return;
        int count = menu.Options.Count;
        int idx = state.SelectedIndex;
        for (int i = 0; i < count; i++)
        {
            idx = (idx + direction + count) % count;
            if (!menu.Options[idx].Disabled)
            {
                if (state.SelectedIndex != idx)
                {
                    state.SelectedIndex = idx;
                    state.IsDirty = true;
                }
                return;
            }
        }
    }

    private static void SelectCurrentOption(CCSPlayerController player, CMenuState state)
    {
        var menu = state.ActiveMenu;
        if (menu == null || menu.Options.Count == 0) return;
        var option = menu.Options[Math.Clamp(state.SelectedIndex, 0, menu.Options.Count - 1)];
        if (option.Disabled) return;
        state.IsDirty = true;
        option.Callback(player);
    }

    private void NavigateBack(CCSPlayerController player, CMenuState state)
    {
        state.IsDirty = true;
        var current = state.ActiveMenu;
        if (current?.CustomBackAction != null)
        {
            current.CustomBackAction.Invoke(player);
            return;
        }

        if (state.History.Count == 0)
        {
            CloseMenu(player);
            return;
        }

        state.ActiveMenu = state.History.Pop();
        state.SelectedIndex = Math.Clamp(state.SelectedIndex, 0, Math.Max(0, (state.ActiveMenu?.Options.Count ?? 1) - 1));
        state.ScrollOffset = 0;
    }

    public void CloseMenu(CCSPlayerController player)
    {
        _playerMenuStates.Remove(player.Slot);
        player.PrintToCenterHtml(" ");
    }

    private static void RenderMenu(CCSPlayerController player, CMenuState state)
    {
        var menu = state.ActiveMenu;
        if (menu == null) return;

        const int visible = 4;
        int total = menu.Options.Count;
        int selected = Math.Clamp(state.SelectedIndex, 0, Math.Max(0, total - 1));

        if (selected < state.ScrollOffset)
            state.ScrollOffset = selected;
        else if (selected >= state.ScrollOffset + visible)
            state.ScrollOffset = selected - visible + 1;

        state.ScrollOffset = Math.Clamp(state.ScrollOffset, 0, Math.Max(0, total - visible));
        int start = state.ScrollOffset;
        int end = Math.Min(total, start + visible);

        var sb = new StringBuilder();
        sb.Append($"<b><font color='#facc15' class='fontSize-m'>{menu.Title}</font></b> <font color='#9ca3af' class='fontSize-s'>[{selected + 1}/{total}]</font><br>");

        for (int i = start; i < end; i++)
        {
            var opt = menu.Options[i];
            string text = opt.Text;
            bool isSelected = i == selected;
            if (opt.Disabled)
            {
                sb.Append($"<font color='#6b7280' class='fontSize-s'>&nbsp;&nbsp;{text}</font><br>");
            }
            else if (isSelected)
            {
                sb.Append($"<b><font color='#facc15' class='fontSize-s'>&gt; </font><font color='#ffffff' class='fontSize-s'>{text}</font></b><br>");
            }
            else
            {
                sb.Append($"<font color='#d1d5db' class='fontSize-s'>&nbsp;&nbsp;{text}</font><br>");
            }
        }

        bool canGoBack = state.History.Count > 0 || menu.CustomBackAction != null;
        string footer = canGoBack
            ? "<font color='#9ca3af' class='fontSize-s'>[W/S] Move &nbsp;[E] Select &nbsp;[A] Back</font>"
            : "<font color='#9ca3af' class='fontSize-s'>[W/S] Move &nbsp;[E] Select &nbsp;[A/R] Exit</font>";

        sb.Append(footer);
        player.PrintToCenterHtml(sb.ToString());
    }

    public HookResult OnPlayerDisconnect(EventPlayerDisconnect @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;
        var player = @event.Userid;
        if (player == null || !player.IsValid) return HookResult.Continue;

        _playerMenuStates.Remove(player.Slot);
        _previewCooldowns.Remove(player.Slot);
        Globals.Choosed_MVP.Remove(player.SteamID);
        Globals.client_mute.Remove(player.SteamID);
        Globals.allow_groups.Remove(player.SteamID);
        Globals.client_cantoggle.Remove(player.SteamID);

        return HookResult.Continue;
    }

    private void OnMapEnd()
    {
        _playerMenuStates.Clear();
        _previewCooldowns.Clear();
        Globals.playedPaths.Clear();
        Globals.Choosed_MVP.Clear();
        Globals.client_mute.Clear();
        Globals.allow_groups.Clear();
        Globals.client_cantoggle.Clear();
    }

    private HookResult OnEventRoundMvp(EventRoundMvp @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;
        var player = @event.Userid;
        if (player == null || !player.IsValid || player.IsBot) return HookResult.Continue;

        Server.NextFrame(() =>
        {
            try
            {
                var mvpData = LoadMvpSettings();
                if (mvpData == null || mvpData.Count == 0) return;

                string? chosenKitKey = null;
                if (Globals.Choosed_MVP.TryGetValue(player.SteamID, out var key) && mvpData.ContainsKey(key))
                {
                    chosenKitKey = key;
                }
                else
                {
                    var personData = Helper.RetrievePersonDataById(player.SteamID);
                    if (!string.IsNullOrEmpty(personData.MusicKit) && mvpData.ContainsKey(personData.MusicKit))
                    {
                        chosenKitKey = personData.MusicKit;
                    }
                }

                // If player has no kit chosen, check default
                if (string.IsNullOrEmpty(chosenKitKey) && mvpData.Count > 0)
                {
                    // Check default steam kit or take first available
                    if (Configs.GetConfigData().MVP_DefaultMusicKitPerSteam.TryGetValue(player.SteamID.ToString(), out var defKit) && mvpData.ContainsKey(defKit))
                    {
                        chosenKitKey = defKit;
                    }
                }

                if (string.IsNullOrEmpty(chosenKitKey) || !mvpData.ContainsKey(chosenKitKey))
                    return;

                var chosenKit = mvpData[chosenKitKey];
                string kitName = chosenKit.ContainsKey("MVP_Kit_Name") ? chosenKit["MVP_Kit_Name"]?.ToString() ?? chosenKitKey : chosenKitKey;
                string soundPath = ExtractSoundPath(chosenKit);
                string soundEvent = ExtractSoundEvent(chosenKit, soundPath);

                if (string.IsNullOrEmpty(soundPath) && string.IsNullOrEmpty(soundEvent)) return;

                // Broadcast chat
                string chatMsg = $" {{gold}}[MVP] {{grey}}| {{gold}}{player.PlayerName} {{grey}}is the MVP! Playing: {{gold}}{kitName}";

                // Play sound and display for all non-muted players
                foreach (var target in Helper.GetAllController())
                {
                    if (target == null || !target.IsValid || target.IsBot || target.IsHLTV)
                        continue;

                    Helper.AdvancedPrintToChat(target, chatMsg);

                    if (!Globals.client_mute.ContainsKey(target.SteamID))
                    {
                        PlaySoundToPlayer(target, soundEvent, soundPath);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[MVP] Error in EventRoundMvp: {ex.Message}");
            }
        });

        return HookResult.Continue;
    }
}
