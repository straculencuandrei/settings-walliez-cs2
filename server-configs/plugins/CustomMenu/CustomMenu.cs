#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Core.Translations;
using CounterStrikeSharp.API.Modules.Admin;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

namespace CustomMenu;

public class Config_Command
{
    public List<string> Command { get; set; } = new();
    public List<string> Permission { get; set; } = new();
    public string Team { get; set; } = string.Empty;
    public string SoundEvent { get; set; } = string.Empty;
    public bool CloseMenu { get; set; }
    public bool Confirm { get; set; }
    public bool Message { get; set; }
    public bool Disabled { get; set; }
    public int Cooldown { get; set; }
}

public class Config_Menu
{
    public string Title { get; set; } = string.Empty;
    public string Type { get; set; } = "WasdMenu";
    public List<string> Command { get; set; } = new();
    public List<string> Permission { get; set; } = new();
    public string Team { get; set; } = string.Empty;
    public bool ExitButton { get; set; } = true;
    public int DisplayTime { get; set; }
    public Dictionary<string, Config_Command> Options { get; set; } = new();
}

public class CustomMenuConfig : BasePluginConfig
{
    public string Prefix { get; set; } = "{green}[wlzmenu]{default} ";
    public Dictionary<string, Config_Menu> Menus { get; set; } = new();
}

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
    public bool ExitButton { get; set; } = true;
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
    public DateTime OpenedAtUtc { get; set; } = DateTime.MinValue;
    public PlayerButtons PreviousButtons { get; set; }
    public DateTime NextScrollRepeatUtc { get; set; } = DateTime.MinValue;
}

public class CustomMenuPlugin : BasePlugin, IPluginConfig<CustomMenuConfig>
{
    public override string ModuleName => "Custom Menu";
    public override string ModuleVersion => "1.1.0";
    public override string ModuleAuthor => "exkludera / modernized by Antigravity";

    public static CustomMenuPlugin Instance { get; private set; } = null!;
    public CustomMenuConfig Config { get; set; } = new();

    public static readonly Dictionary<string, string> CommandMenuId = new(StringComparer.OrdinalIgnoreCase);
    private static readonly Dictionary<int, CMenuState> MenuStates = new();
    private static readonly Dictionary<int, float> SavedSpeed = new();
    private static readonly HashSet<int> FrozenSlots = new();
    private static readonly Dictionary<int, Dictionary<Config_Command, DateTime>> Cooldowns = new();

    private static readonly Dictionary<string, PlayerButtons> ButtonMap = new(StringComparer.OrdinalIgnoreCase)
    {
        ["W"] = PlayerButtons.Forward,
        ["S"] = PlayerButtons.Back,
        ["E"] = PlayerButtons.Use,
        ["A"] = PlayerButtons.Moveleft,
        ["D"] = PlayerButtons.Moveright,
        ["R"] = PlayerButtons.Reload
    };

    public override void Load(bool hotReload)
    {
        Instance = this;
        RegisterCommands();
        RegisterListener<Listeners.OnTick>(OnInternalMenuTick);
        RegisterListener<Listeners.OnClientDisconnect>(OnClientDisconnect);
    }

    public override void Unload(bool hotReload)
    {
        RemoveListener<Listeners.OnTick>(OnInternalMenuTick);
        RemoveListener<Listeners.OnClientDisconnect>(OnClientDisconnect);
        foreach (var cmd in CommandMenuId.Keys.ToList())
        {
            RemoveCommand(cmd, OnCommandOpen);
        }
        CommandMenuId.Clear();
        MenuStates.Clear();
        FrozenSlots.Clear();
        SavedSpeed.Clear();
        Cooldowns.Clear();
    }

    private static void OnClientDisconnect(int slot)
    {
        MenuStates.Remove(slot);
        FrozenSlots.Remove(slot);
        SavedSpeed.Remove(slot);
        Cooldowns.Remove(slot);
    }

    public void OnConfigParsed(CustomMenuConfig config)
    {
        Config = config;
        Config.Prefix = Config.Prefix.ReplaceColorTags();
        RegisterCommands();
    }

    private void RegisterCommands()
    {
        CommandMenuId.Clear();
        foreach (var kvp in Config.Menus)
        {
            foreach (var cmd in kvp.Value.Command)
            {
                string cleanCmd = cmd.Trim();
                if (cleanCmd.Length == 0) continue;
                CommandMenuId[cleanCmd] = kvp.Key;
                AddCommand(cleanCmd, kvp.Key, OnCommandOpen);
            }
        }
    }

    [CommandHelper(0, "", CommandUsage.CLIENT_ONLY)]
    public static void OnCommandOpen(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        string cmd = info.GetCommandString.Trim();
        if (cmd.StartsWith("css_"))
            cmd = cmd[4..];

        // Also check with css_ prefix or exact
        if (!CommandMenuId.TryGetValue(info.GetCommandString, out var menuKey) &&
            !CommandMenuId.TryGetValue(cmd, out menuKey) &&
            !CommandMenuId.TryGetValue("css_" + cmd, out menuKey))
        {
            // Default to first menu (e.g. wlzmenu)
            menuKey = Instance.Config.Menus.Keys.FirstOrDefault() ?? "wlzmenu";
        }

        if (Instance.Config.Menus.TryGetValue(menuKey, out var menuConfig))
        {
            if (!Utils.HasPermission(player, menuConfig.Permission, menuConfig.Team))
            {
                player.PrintToChat(Instance.Config.Prefix + Instance.Localizer["NoPermission"]);
                return;
            }
            OpenCustomMenu(player, menuKey, menuConfig);
        }
    }

    internal static void OpenCustomMenu(CCSPlayerController player, string menuKey, Config_Menu menuConfig, CMenu? parentMenu = null)
    {
        if (!player.IsValid) return;

        string title = !string.IsNullOrWhiteSpace(menuConfig.Title) ? menuConfig.Title : menuKey;
        // Clean title if needed
        if (title.Equals("wlzmenu", StringComparison.OrdinalIgnoreCase))
            title = "SERVER MENU";

        var menu = new CMenu(menuKey, title);
        if (parentMenu != null)
        {
            menu.CustomBackAction = p => OpenMenu(p, parentMenu, suppressHistoryPush: true);
        }

        foreach (var optKvp in menuConfig.Options)
        {
            string optionName = optKvp.Key;
            var option = optKvp.Value;

            if (!Utils.HasPermission(player, option.Permission, option.Team))
                continue;

            menu.AddOption(optionName, p =>
            {
                if (option.Confirm)
                {
                    OpenConfirmMenu(p, optionName, option, menu);
                }
                else
                {
                    ExecuteOption(p, optionName, option, menu);
                }
            }, disabled: option.Disabled);
        }

        OpenMenu(player, menu);
    }

    private static void OpenConfirmMenu(CCSPlayerController player, string optionName, Config_Command option, CMenu parentMenu)
    {
        string confirmTitle = Instance.Localizer["ConfirmTitle"] ?? "Are you sure?";
        var confirmMenu = new CMenu("confirm", confirmTitle)
        {
            CustomBackAction = p => OpenMenu(p, parentMenu, suppressHistoryPush: true)
        };

        string yesText = Instance.Localizer["ConfirmAccept"] ?? "Yes";
        string noText = Instance.Localizer["ConfirmDecline"] ?? "No";

        confirmMenu.AddOption(yesText, p => ExecuteOption(p, optionName, option, parentMenu));
        confirmMenu.AddOption(noText, p => OpenMenu(p, parentMenu, suppressHistoryPush: true));

        OpenMenu(player, confirmMenu);
    }

    private static void ExecuteOption(CCSPlayerController player, string optionName, Config_Command option, CMenu currentMenu)
    {
        if (CommandCooldown(player, option))
        {
            player.PrintToChat(Instance.Config.Prefix + Instance.Localizer["Cooldown"]);
            return;
        }

        if (option.Message)
        {
            player.PrintToChat(Instance.Config.Prefix + Instance.Localizer["Selected", optionName]);
        }

        if (!string.IsNullOrEmpty(option.SoundEvent))
        {
            var recipients = new RecipientFilter { player };
            player.EmitSound(option.SoundEvent, recipients);
        }

        // Check first if this triggers a sub-menu navigation
        foreach (string rawCmd in option.Command)
        {
            if (string.IsNullOrWhiteSpace(rawCmd)) continue;
            string text = rawCmd.Trim();

            if (CommandMenuId.TryGetValue(text, out string targetMenuKey) &&
                Instance.Config.Menus.TryGetValue(targetMenuKey, out var targetMenuConfig) &&
                Utils.HasPermission(player, targetMenuConfig.Permission, targetMenuConfig.Team))
            {
                OpenCustomMenu(player, targetMenuKey, targetMenuConfig, parentMenu: currentMenu);
                return;
            }
        }

        if (option.CloseMenu)
        {
            CloseMenu(player);
        }

        foreach (string rawCmd in option.Command)
        {
            if (string.IsNullOrWhiteSpace(rawCmd)) continue;
            string text = rawCmd.Trim();

            if (text.StartsWith("give ", StringComparison.OrdinalIgnoreCase))
            {
                string item = text[5..].Trim();
                player.GiveNamedItem(item);
                player.PrintToChat(Instance.Config.Prefix + "Given " + item);
            }
            else if (text.StartsWith("server:", StringComparison.OrdinalIgnoreCase))
            {
                Server.ExecuteCommand(text[7..].Trim());
            }
            else if (text.StartsWith("client:", StringComparison.OrdinalIgnoreCase))
            {
                player.ExecuteClientCommandFromServer(text[7..].Trim());
            }
            else if (text.StartsWith("map ", StringComparison.OrdinalIgnoreCase) ||
                     text.StartsWith("changelevel ", StringComparison.OrdinalIgnoreCase) ||
                     text.StartsWith("mp_", StringComparison.OrdinalIgnoreCase) ||
                     text.StartsWith("bot_", StringComparison.OrdinalIgnoreCase) ||
                     text.StartsWith("sv_", StringComparison.OrdinalIgnoreCase) ||
                     text.StartsWith("exec ", StringComparison.OrdinalIgnoreCase) ||
                     text.Equals("quit", StringComparison.OrdinalIgnoreCase))
            {
                Server.ExecuteCommand(text);
            }
            else
            {
                player.ExecuteClientCommandFromServer(text);
            }
        }

        if (option.Cooldown > 0)
        {
            if (!Cooldowns.ContainsKey(player.Slot))
                Cooldowns[player.Slot] = new Dictionary<Config_Command, DateTime>();

            Cooldowns[player.Slot][option] = DateTime.UtcNow.AddSeconds(option.Cooldown);
            Instance.AddTimer(option.Cooldown, () =>
            {
                if (Cooldowns.TryGetValue(player.Slot, out var dict))
                {
                    dict.Remove(option);
                    if (dict.Count == 0)
                        Cooldowns.Remove(player.Slot);
                }
            }, TimerFlags.STOP_ON_MAPCHANGE);
        }

        // If not closing menu and not navigating to submenu, re-render
        if (!option.CloseMenu && MenuStates.TryGetValue(player.Slot, out var state) && state.ActiveMenu != null)
        {
            RenderMenu(player, state);
        }
    }

    private static bool CommandCooldown(CCSPlayerController player, Config_Command option)
    {
        if (Cooldowns.TryGetValue(player.Slot, out var dict) && dict.TryGetValue(option, out var expires))
        {
            return DateTime.UtcNow < expires;
        }
        return false;
    }

    // ==========================================
    // INTERNAL MENU ENGINE (Identical to AdminPlus)
    // ==========================================

    internal static CMenuState GetOrCreateMenuState(CCSPlayerController player)
    {
        if (!MenuStates.TryGetValue(player.Slot, out var state))
        {
            state = new CMenuState();
            MenuStates[player.Slot] = state;
        }
        return state;
    }

    internal static void OpenMenu(CCSPlayerController player, CMenu menu, bool suppressHistoryPush = false)
    {
        if (!player.IsValid) return;
        var state = GetOrCreateMenuState(player);
        var current = state.ActiveMenu;

        if (current != null && !suppressHistoryPush && current != menu)
            state.History.Push(current);

        state.ActiveMenu = menu;
        state.SelectedIndex = ClampToSelectableIndex(state, 0);
        state.ScrollOffset = 0;
        state.PreviousButtons = player.Buttons;
        state.NextScrollRepeatUtc = DateTime.MinValue;
        state.OpenedAtUtc = DateTime.UtcNow;

        SetFrozen(player, true);
        RenderMenu(player, state);
    }

    internal static void CloseMenu(CCSPlayerController player)
    {
        if (!player.IsValid) return;
        if (MenuStates.TryGetValue(player.Slot, out var state))
        {
            state.ActiveMenu = null;
            state.History.Clear();
            state.SelectedIndex = 0;
            state.ScrollOffset = 0;
            state.PreviousButtons = 0;
            player.PrintToCenterHtml(" ");
        }
        SetFrozen(player, false);
    }

    private static void OnInternalMenuTick()
    {
        foreach (var pl in Utilities.GetPlayers())
        {
            if (!pl.IsValid) continue;
            if (MenuStates.TryGetValue(pl.Slot, out var state) && state.ActiveMenu != null)
            {
                ProcessMenuInput(pl, state, pl.Buttons);
                RenderMenu(pl, state);
            }
            if (FrozenSlots.Contains(pl.Slot) && pl.PlayerPawn?.Value != null)
            {
                pl.PlayerPawn.Value.VelocityModifier = 0f;
            }
        }
    }

    private static void ProcessMenuInput(CCSPlayerController player, CMenuState state, PlayerButtons buttons)
    {
        if (!player.IsValid || state.ActiveMenu == null) return;

        var menu = state.ActiveMenu;
        var now = DateTime.UtcNow;

        if (now - state.OpenedAtUtc < TimeSpan.FromMilliseconds(150))
        {
            state.PreviousButtons = buttons;
            return;
        }

        var prev = state.PreviousButtons;

        // Exit button (R)
        if (menu.ExitButton && HasButtonJustPressed(PlayerButtons.Reload, buttons, prev))
        {
            state.PreviousButtons = buttons;
            CloseMenu(player);
            return;
        }

        // Back button (A)
        if (HasButtonJustPressed(PlayerButtons.Moveleft, buttons, prev))
        {
            state.PreviousButtons = buttons;
            NavigateBack(player, state);
            return;
        }

        // Select button (E)
        if (HasButtonJustPressed(PlayerButtons.Use, buttons, prev))
        {
            state.PreviousButtons = buttons;
            SelectCurrentOption(player, state);
            return;
        }

        // Scroll Up / Down with immediate response AND auto-repeat
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
                state.SelectedIndex = idx;
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

        option.Callback(player);
    }

    private static void NavigateBack(CCSPlayerController player, CMenuState state)
    {
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
        state.SelectedIndex = ClampToSelectableIndex(state, state.SelectedIndex);
        state.ScrollOffset = 0;
    }

    private static int ClampToSelectableIndex(CMenuState state, int fallback)
    {
        var menu = state.ActiveMenu;
        if (menu == null || menu.Options.Count == 0) return 0;
        int idx = Math.Clamp(fallback, 0, menu.Options.Count - 1);
        if (!menu.Options[idx].Disabled) return idx;
        int first = menu.Options.FindIndex(x => !x.Disabled);
        return first >= 0 ? first : 0;
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
        sb.Append($"<b><font color='#4ade80' class='fontSize-m'>{menu.Title}</font></b> <font color='#9ca3af' class='fontSize-s'>[{selected + 1}/{total}]</font><br>");

        for (int i = start; i < end; i++)
        {
            var opt = menu.Options[i];
            string text = opt.Text;
            bool isSelected = i == selected;
            if (opt.Disabled)
            {
                sb.Append($"<font color='#6b7280' class='fontSize-s'>  {text}</font><br>");
            }
            else if (isSelected)
            {
                sb.Append($"<b><font color='#facc15' class='fontSize-s'>&gt; </font><font color='#ffffff' class='fontSize-s'>{text}</font></b><br>");
            }
            else
            {
                sb.Append($"<font color='#d1d5db' class='fontSize-s'>  {text}</font><br>");
            }
        }

        bool canGoBack = state.History.Count > 0 || menu.CustomBackAction != null;
        if (canGoBack)
        {
            sb.Append($"<font color='#9ca3af' class='fontSize-xs'><font color='#38bdf8'>[W/S]</font> Move | <font color='#38bdf8'>[E]</font> Select | <font color='#38bdf8'>[A]</font> Back | <font color='#38bdf8'>[R]</font> Exit</font>");
        }
        else
        {
            sb.Append($"<font color='#9ca3af' class='fontSize-xs'><font color='#38bdf8'>[W/S]</font> Move | <font color='#38bdf8'>[E]</font> Select | <font color='#38bdf8'>[R]</font> Exit</font>");
        }

        player.PrintToCenterHtml(sb.ToString());
    }

    private static void SetFrozen(CCSPlayerController player, bool frozen)
    {
        if (player.PlayerPawn?.Value == null) return;
        if (frozen)
        {
            if (!SavedSpeed.ContainsKey(player.Slot))
                SavedSpeed[player.Slot] = player.PlayerPawn.Value.VelocityModifier;
            FrozenSlots.Add(player.Slot);
            return;
        }

        FrozenSlots.Remove(player.Slot);
        if (SavedSpeed.TryGetValue(player.Slot, out var speed))
        {
            Server.NextFrame(() =>
            {
                if (player.PlayerPawn?.Value != null)
                    player.PlayerPawn.Value.VelocityModifier = speed;
                SavedSpeed.Remove(player.Slot);
            });
        }
    }
}

internal static class Utils
{
    public static bool HasPermission(CCSPlayerController player, List<string> permissions, string team)
    {
        if (PermissionCheck(player, permissions))
        {
            return AllowedTeam(player, team);
        }
        return false;
    }

    public static bool PermissionCheck(CCSPlayerController player, List<string> permissions)
    {
        if (permissions.Count == 0) return true;
        foreach (string perm in permissions)
        {
            if (perm.StartsWith("@") && AdminManager.PlayerHasPermissions(player, perm))
                return true;
            if (perm.StartsWith("#") && AdminManager.PlayerInGroup(player, perm))
                return true;
        }
        return false;
    }

    public static bool AllowedTeam(CCSPlayerController player, string team)
    {
        string t = team.ToLower();
        if ((t != "t" && t != "terrorist") || player.Team == CsTeam.Terrorist)
        {
            if ((t != "ct" && t != "counterterrorist") || player.Team == CsTeam.CounterTerrorist)
            {
                if (t != "" && t != "both")
                    return t == "all";
                return true;
            }
        }
        return false;
    }
}
