using System.Text;
using MySqlConnector;
using Newtonsoft.Json;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using Microsoft.Extensions.Localization;
using CounterStrikeSharp.API.Modules.Menu;
using CounterStrikeSharp.API.Modules.Timers;

namespace Custom_MVP_Sounds;
using Custom_MVP_Sounds.Config;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;
using System.IO;

public class CustomMVPSounds : BasePlugin
{
    private readonly Dictionary<ulong, DateTime> _refreshCooldowns = new();

    private string GetMvpSettingsPath()
    {
        string p1 = Path.Combine(ModuleDirectory, "config/MVP_Settings.json");
        if (File.Exists(p1)) return p1;
        string p2 = Path.Combine(ModuleDirectory, "../../plugins/Custom_MVP_Sounds/config/MVP_Settings.json");
        if (File.Exists(p2)) return p2;
        string p3 = Path.Combine(ModuleDirectory, "../../plugins/MVP-Sounds-GoldKingZ/config/MVP_Settings.json");
        if (File.Exists(p3)) return p3;
        return p1;
    }

    public void OnCommandSoundRefresh(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid || player.IsBot || player.IsHLTV) return;

        var steamId = player.SteamID;
        if (_refreshCooldowns.TryGetValue(steamId, out var nextAllowed) && DateTime.UtcNow < nextAllowed)
        {
            var remaining = Math.Ceiling((nextAllowed - DateTime.UtcNow).TotalSeconds);
            Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {darkred}Please wait {0}s before refreshing again.", remaining);
            return;
        }

        _refreshCooldowns[steamId] = DateTime.UtcNow.AddSeconds(3);

        Task.Run(async () =>
        {
            string chosenKit = string.Empty;
            bool isMuted = false;
            bool foundData = false;

            // 1. Try reading from MySQL PersonData table (same db used by mvpz.walliez.xyz)
            try
            {
                string mysqlPath = Path.Combine(ModuleDirectory, "config/MySql_Settings.json");
                if (File.Exists(mysqlPath))
                {
                    var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(mysqlPath));
                    if (connectionSettings != null && !string.IsNullOrEmpty(connectionSettings.MySqlHost) && connectionSettings.MySqlHost != "your_mysql_host")
                    {
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
                        var dbData = await MySqlDataManager.RetrievePersonDataByIdAsync(steamId, connection);
                        if (dbData != null && dbData.PlayerSteamID != 0)
                        {
                            chosenKit = dbData.MusicKit ?? string.Empty;
                            isMuted = dbData.Client_Mute_MVP;
                            foundData = true;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[MVP Refresh] MySQL note: {ex.Message}");
            }

            // 2. If not found in MySQL, check Cookies/MVP_Sounds_Cookies.json
            if (!foundData)
            {
                try
                {
                    var cookieData = Helper.RetrievePersonDataById(steamId);
                    if (cookieData != null && cookieData.PlayerSteamID != 0)
                    {
                        chosenKit = cookieData.MusicKit ?? string.Empty;
                        isMuted = cookieData.Client_Mute_MVP;
                        foundData = true;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[MVP Refresh] Cookie note: {ex.Message}");
                }
            }

            // 3. Queue update on main game thread
            Server.NextFrame(() =>
            {
                if (player == null || !player.IsValid) return;

                // Update mute status in RAM
                if (isMuted)
                {
                    Globals.client_mute[steamId] = true;
                }
                else
                {
                    Globals.client_mute.Remove(steamId);
                }

                // Clean kit string
                if (chosenKit == "Unequip MVP Sound" || chosenKit == "Disable All MVP Sounds")
                {
                    chosenKit = string.Empty;
                }

                // Update chosen MVP in RAM
                if (!string.IsNullOrEmpty(chosenKit))
                {
                    Globals.Choosed_MVP[steamId] = chosenKit;

                    // Sync local cookie file
                    Helper.SaveToJsonFile(steamId, chosenKit, isMuted, DateTime.Now);

                    // Resolve display name from MVP_Settings.json
                    string displayName = chosenKit;
                    try
                    {
                        string jsonFilePath = GetMvpSettingsPath();
                        if (File.Exists(jsonFilePath))
                        {
                            var settings = JsonConvert.DeserializeObject<Dictionary<string, Dictionary<string, string>>>(File.ReadAllText(jsonFilePath));
                            if (settings != null && settings.TryGetValue(chosenKit, out var kitDict) && kitDict.TryGetValue("MVP_Kit_Name", out var name))
                            {
                                displayName = name;
                            }
                        }
                    }
                    catch { }

                    Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}Anthem Refreshed from site: {gold}{0}", displayName);
                }
                else
                {
                    Globals.Choosed_MVP.Remove(steamId);
                    Helper.SaveToJsonFile(steamId, string.Empty, isMuted, DateTime.Now);
                    Helper.AdvancedPrintToChat(player, "{gold}[MVP] {grey}| {white}MVP Anthem is currently {darkred}unequipped{white}.");
                }
            });
        });
    }

    public void OpenMvpMenu(CCSPlayerController Player)
    {
        if (Player == null || !Player.IsValid || Player.IsBot || Player.IsHLTV) return;
        var PlayerSteamID = Player.SteamID;
        Helper.PersonData personData = Helper.RetrievePersonDataById(PlayerSteamID);

        if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP) && !Globals.allow_groups.ContainsKey(PlayerSteamID))
        {
            if (!string.IsNullOrEmpty(Localizer["player.not.allowed"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.not.allowed"]);
            }
            return;
        }

        try
        {
            string jsonFilePath = GetMvpSettingsPath();
            string jsonData = File.ReadAllText(jsonFilePath);
            var data = JsonConvert.DeserializeObject<Dictionary<string, Dictionary<string, string>>>(jsonData);
            if (data == null) return;

            IMenu VoteGameModeMenu;
            if (Configs.GetConfigData().MVP_ChangeMVPMenuFromChatToCentre)
            {
                VoteGameModeMenu = new CenterHtmlMenu(Localizer["menu.music"], this);
            }
            else
            {
                VoteGameModeMenu = new ChatMenu(Localizer["menu.music"]);
            }

            if (personData.Client_Mute_MVP)
            {
                VoteGameModeMenu.AddMenuOption(Localizer["menu.enabled"], (p, option) => HandleMenu(p, option, string.Empty, null!, false));
            }
            else
            {
                VoteGameModeMenu.AddMenuOption(Localizer["menu.disabled"], (p, option) => HandleMenu(p, option, string.Empty, null!, false));
            }

            VoteGameModeMenu.AddMenuOption(Localizer["menu.remove"], (p, option) => HandleMenu(p, option, string.Empty, null!, false));

            foreach (var key in data.Keys)
            {
                string ChoosenKitKey = data[key]["MVP_Kit_Name"];
                bool isPreviewAble = data[key].ContainsKey("CanBePreview") && bool.TryParse(data[key]["CanBePreview"].ToString(), out bool PreviewValue) ? PreviewValue : false;
                bool isHiddenItem = data[key].ContainsKey("HIDDEN") && bool.TryParse(data[key]["HIDDEN"].ToString(), out bool isHiddenItemValue) ? isHiddenItemValue : false;
                string HasFlag = data[key].ContainsKey("FLAGS") ? data[key]["FLAGS"] : null!;

                if (isHiddenItem && !string.IsNullOrEmpty(HasFlag) && !Helper.IsPlayerInGroupPermission(Player, HasFlag)) continue;
                VoteGameModeMenu.AddMenuOption(ChoosenKitKey, (p, option) => HandleMenu(p, option, key, HasFlag, isPreviewAble));
            }

            if (Configs.GetConfigData().MVP_ChangeMVPMenuFromChatToCentre)
            {
                if (VoteGameModeMenu is CenterHtmlMenu centerHtmlMenu)
                {
                    MenuManager.OpenCenterHtmlMenu(this, Player, centerHtmlMenu);
                }
            }
            else
            {
                if (VoteGameModeMenu is ChatMenu chatMenu)
                {
                    MenuManager.OpenChatMenu(Player, chatMenu);
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Custom_MVP_Sounds] Error opening menu: {ex.Message}");
        }
    }

    public override string ModuleName => "Custom MVP Sounds";
    public override string ModuleVersion => "1.0.5";
    public override string ModuleAuthor => "Walliez";
    public override string ModuleDescription => "Custom Server MVP Music Pack";
    internal static IStringLocalizer? Stringlocalizer;
    private CounterStrikeSharp.API.Modules.Timers.Timer? HUDTimer_Center;
    private CounterStrikeSharp.API.Modules.Timers.Timer? HUDTimer_Center_Bottom;
	

    public override void Load(bool hotReload)
    {
        Configs.Load(ModuleDirectory);
        Stringlocalizer = Localizer;
        Configs.Shared.CookiesModule = ModuleDirectory;
        Configs.Shared.StringLocalizer = Localizer;
        RegisterEventHandler<EventRoundMvp>(OnEventRoundMvp,HookMode.Pre);
        RegisterEventHandler<EventPlayerConnectFull>(OnEventPlayerConnectFull);
        RegisterListener<Listeners.OnTick>(OnTick);
        RegisterEventHandler<EventPlayerDisconnect>(OnPlayerDisconnect);
        RegisterListener<Listeners.OnMapEnd>(OnMapEnd);
        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        AddCommandListener("say", OnCommandSay);
        AddCommandListener("say_team", OnCommandSay);
        AddCommand("css_mvp", "Open MVP Menu", (p, info) => { if (p != null && p.IsValid) OpenMvpMenu(p); });
        AddCommand("mvp", "Open MVP Menu", (p, info) => { if (p != null && p.IsValid) OpenMvpMenu(p); });
        AddCommand("anthem", "Open MVP Menu", (p, info) => { if (p != null && p.IsValid) OpenMvpMenu(p); });
        AddCommand("css_sr", "Refresh MVP anthem from website", (p, info) => { if (p != null && p.IsValid) OnCommandSoundRefresh(p, info); });
        AddCommand("sr", "Refresh MVP anthem from website", (p, info) => { if (p != null && p.IsValid) OnCommandSoundRefresh(p, info); });

    }
    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        if(@event == null)return HookResult.Continue;

        HUDTimer_Center?.Kill();
        HUDTimer_Center = null;
        HUDTimer_Center_Bottom?.Kill();
        HUDTimer_Center_Bottom = null;
        
        Globals.Show_Center = false;
        Globals.Show_Center_Bottom = false;

        if (Configs.GetConfigData().MVP_ForceDisableDefaultMVP_ToAll)
        {
            var all = Helper.GetAllController();
            all.ForEach(p =>
            {
                if (p != null && p.IsValid && !p.IsBot)
                {
                    try
                    {
                        p.MusicKitID = 0;
                        if (p.InventoryServices != null)
                        {
                            p.InventoryServices.MusicID = 0;
                        }
                    }
                    catch { }
                }
            });
        }

        return HookResult.Continue;
    }

    public HookResult OnEventPlayerConnectFull(EventPlayerConnectFull @event, GameEventInfo info)
    {
        if (@event == null)return HookResult.Continue;
        var player = @event.Userid;

        if (player == null || !player.IsValid || player.IsBot || player.IsHLTV) return HookResult.Continue;

        if (Configs.GetConfigData().MVP_ForceDisableDefaultMVP_ToAll)
        {
            try
            {
                player.MusicKitID = 0;
                if (player.InventoryServices != null)
                {
                    player.InventoryServices.MusicID = 0;
                }
            }
            catch { }
        }

        var playerid = player.SteamID;
        foreach (var kvp in Configs.GetConfigData().MVP_DefaultMusicKitPerSteam)
        {
            if (kvp.Key.ToString() == playerid.ToString())
            {
                string defaultmusickit = kvp.Value;
                if (!Globals.Choosed_MVP.ContainsKey(player.SteamID))
                {
                    Globals.Choosed_MVP.Add(player.SteamID, defaultmusickit);
                }
                if (Globals.Choosed_MVP.ContainsKey(player.SteamID))
                {
                    Globals.Choosed_MVP[player.SteamID] = defaultmusickit;
                }
                break;
            }
        }
        
        if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP) && Helper.IsPlayerInGroupPermission(player, Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanMVP))
        {
            if (!Globals.allow_groups.ContainsKey(playerid))
            {
                Globals.allow_groups.Add(playerid, true);
            }
        }

        if(!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP) && Helper.IsPlayerInGroupPermission(player, Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP))
        {
            if (!Globals.client_cantoggle.ContainsKey(playerid))
            {
                Globals.client_cantoggle.Add(playerid, true);
            }
        }


        Helper.PersonData personData = Helper.RetrievePersonDataById(playerid);

        if(!string.IsNullOrEmpty(personData.MusicKit))
        {
            if (!Globals.Choosed_MVP.ContainsKey(player.SteamID))
            {
                Globals.Choosed_MVP.Add(player.SteamID, personData.MusicKit);
            }
            if (Globals.Choosed_MVP.ContainsKey(player.SteamID))
            {
                Globals.Choosed_MVP[player.SteamID] = personData.MusicKit;
            }
        }

        if(personData.Client_Mute_MVP)
        {
            if (!Globals.client_mute.ContainsKey(player.SteamID))
            {
                Globals.client_mute.Add(player.SteamID, true);
            }
            if (Globals.client_mute.ContainsKey(player.SteamID))
            {
                Globals.client_mute[player.SteamID] = true;
            }
        }


        if(Configs.GetConfigData().MVP_UseMySql)
        {
            async Task PerformDatabaseOperationAsync()
            {
                try
                {
                    var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(Path.Combine(Path.Combine(ModuleDirectory, "config"), "MySql_Settings.json")));
                    var connectionString = new MySqlConnectionStringBuilder
                    {
                        Server = connectionSettings!.MySqlHost,
                        Port = (uint)connectionSettings.MySqlPort,
                        Database = connectionSettings.MySqlDatabase,
                        UserID = connectionSettings.MySqlUsername,
                        Password = connectionSettings.MySqlPassword
                    }.ConnectionString;

                    using (var connection = new MySqlConnection(connectionString))
                    {
                        await connection.OpenAsync();
                        var personDataz = await MySqlDataManager.RetrievePersonDataByIdAsync(playerid, connection);
                        if (personDataz.PlayerSteamID != 0)
                        {
                            DateTime personDate = DateTime.Now;
                            if(!string.IsNullOrEmpty(personDataz.MusicKit))
                            {
                                if (!Globals.Choosed_MVP.ContainsKey(player.SteamID))
                                {
                                    Globals.Choosed_MVP.Add(player.SteamID, personDataz.MusicKit);
                                }
                                if (Globals.Choosed_MVP.ContainsKey(player.SteamID))
                                {
                                    Globals.Choosed_MVP[player.SteamID] = personDataz.MusicKit;
                                }
                            }
                            if(personDataz.Client_Mute_MVP)
                            {
                                if (!Globals.client_mute.ContainsKey(player.SteamID))
                                {
                                    Globals.client_mute.Add(player.SteamID, true);
                                }
                                if (Globals.client_mute.ContainsKey(player.SteamID))
                                {
                                    Globals.client_mute[player.SteamID] = true;
                                }
                            }
                            Helper.SaveToJsonFile(player.SteamID, personDataz.MusicKit!, personDataz.Client_Mute_MVP, DateTime.Now);
                        }
                        
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"======================== ERROR =============================");
                    Console.WriteLine($"An error occurred: {ex.Message}");
                    Console.WriteLine($"======================== ERROR =============================");
                }
            }

            Task.Run(PerformDatabaseOperationAsync);
        }

        
        
        return HookResult.Continue;
    }
    public HookResult OnCommandSay(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid || player.IsBot || player.IsHLTV) return HookResult.Continue;
        var message = info.GetArg(1);
        if (string.IsNullOrWhiteSpace(message)) return HookResult.Continue;

        string trimmedMessage = message.Trim();

        // /sr command (same behavior as /wp for skins)
        if (trimmedMessage.Equals("!sr", StringComparison.OrdinalIgnoreCase) ||
            trimmedMessage.Equals("/sr", StringComparison.OrdinalIgnoreCase) ||
            trimmedMessage.Equals("!refreshmvp", StringComparison.OrdinalIgnoreCase) ||
            trimmedMessage.Equals("/refreshmvp", StringComparison.OrdinalIgnoreCase) ||
            trimmedMessage.Equals("!mvprefresh", StringComparison.OrdinalIgnoreCase) ||
            trimmedMessage.Equals("/mvprefresh", StringComparison.OrdinalIgnoreCase))
        {
            OnCommandSoundRefresh(player, info);
            return HookResult.Continue;
        }

        string[] MVPInGameMenu = Configs.GetConfigData().MVP_InGameMenu.Split(',');
        if (MVPInGameMenu.Any(cmd => cmd.Equals(trimmedMessage, StringComparison.OrdinalIgnoreCase)))
        {
            OpenMvpMenu(player);
        }
        return HookResult.Continue;
    }

    private void HandleMenu(CCSPlayerController Player, ChatMenuOption option, string ChoosenKitKey, string HasFlag, bool isPreviewAble)
    {
        Helper.PersonData personData = Helper.RetrievePersonDataById(Player.SteamID);
        var disabled = option.Text;
        if(disabled == Localizer["menu.enabled"])
        {
            Globals.client_mute.Remove(Player.SteamID);
            personData.Client_Mute_MVP = !personData.Client_Mute_MVP;
            if(personData.Client_Mute_MVP)
            {

            }else
            {
                Helper.SaveToJsonFile(Player.SteamID, personData.MusicKit!, personData.Client_Mute_MVP, DateTime.Now);
            }
            
            if(Configs.GetConfigData().MVP_UseMySql)
            {
                Task.Run(async () =>
                {
                    try
                    {
                        var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(Path.Combine(Path.Combine(ModuleDirectory, "config"), "MySql_Settings.json")));
                        var connectionString = new MySqlConnectionStringBuilder
                        {
                            Server = connectionSettings!.MySqlHost,
                            Port = (uint)connectionSettings.MySqlPort,
                            Database = connectionSettings.MySqlDatabase,
                            UserID = connectionSettings.MySqlUsername,
                            Password = connectionSettings.MySqlPassword
                        }.ConnectionString;
                        
                        using (var connection = new MySqlConnection(connectionString))
                        {
                            await connection.OpenAsync();
                            await MySqlDataManager.CreatePersonDataTableIfNotExistsAsync(connection);

                            DateTime personDate = DateTime.Now;
                            var personData = Helper.RetrievePersonDataById(Player.SteamID);
                            if (personData.PlayerSteamID != 0)
                            {
                                await MySqlDataManager.SaveToMySqlAsync(Player.SteamID, personData.MusicKit!, false, personDate, connection, connectionSettings);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"======================== ERROR =============================");
                        Console.WriteLine($"An error occurred: {ex.Message}");
                        Console.WriteLine($"======================== ERROR =============================");
                    }
                });
            }
            if (!string.IsNullOrEmpty(Localizer["player.musickit.enabled"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.musickit.enabled"], option.Text);
            }
            MenuManager.CloseActiveMenu(Player);
            return;
        }
        if(disabled == Localizer["menu.disabled"])
        {
            if (!string.IsNullOrEmpty(Configs.GetConfigData().MVP_OnlyAllowTheseGroupsCanToggleOffMVP) && !Globals.client_cantoggle.ContainsKey(Player.SteamID))
            {
                if (!string.IsNullOrEmpty(Localizer["player.disabled.not.allowed"]))
                {
                    Helper.AdvancedPrintToChat(Player, Localizer["player.disabled.not.allowed"]);
                }
                MenuManager.CloseActiveMenu(Player);
                return;
            }
            if (!Globals.client_mute.ContainsKey(Player.SteamID))
            {
                Globals.client_mute.Add(Player.SteamID, true);
            }
            if (Globals.client_mute.ContainsKey(Player.SteamID))
            {
                Globals.client_mute[Player.SteamID] = true;
            }
            
            personData.Client_Mute_MVP = !personData.Client_Mute_MVP;
            if(personData.Client_Mute_MVP)
            {
                Helper.SaveToJsonFile(Player.SteamID, personData.MusicKit!, personData.Client_Mute_MVP, DateTime.Now);
            }else
            {
                
            }
            if(Configs.GetConfigData().MVP_UseMySql)
            {
                Task.Run(async () =>
                {
                    try
                    {
                        var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(Path.Combine(Path.Combine(ModuleDirectory, "config"), "MySql_Settings.json")));
                        var connectionString = new MySqlConnectionStringBuilder
                        {
                            Server = connectionSettings!.MySqlHost,
                            Port = (uint)connectionSettings.MySqlPort,
                            Database = connectionSettings.MySqlDatabase,
                            UserID = connectionSettings.MySqlUsername,
                            Password = connectionSettings.MySqlPassword
                        }.ConnectionString;
                        
                        using (var connection = new MySqlConnection(connectionString))
                        {
                            await connection.OpenAsync();
                            await MySqlDataManager.CreatePersonDataTableIfNotExistsAsync(connection);

                            DateTime personDate = DateTime.Now;
                            var personData = Helper.RetrievePersonDataById(Player.SteamID);
                            if (personData.PlayerSteamID != 0)
                            {
                                await MySqlDataManager.SaveToMySqlAsync(Player.SteamID, personData.MusicKit!, true, personDate, connection, connectionSettings);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"======================== ERROR =============================");
                        Console.WriteLine($"An error occurred: {ex.Message}");
                        Console.WriteLine($"======================== ERROR =============================");
                    }
                });
            }
            if (!string.IsNullOrEmpty(Localizer["player.musickit.disabled"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.musickit.disabled"], option.Text);
            }
            MenuManager.CloseActiveMenu(Player);
            return;
        }

        if(disabled == Localizer["menu.remove"])
        {
            Globals.Choosed_MVP.Remove(Player.SteamID);
            
            Helper.SaveToJsonFile(Player.SteamID, disabled, personData.Client_Mute_MVP, DateTime.Now);
            if(Configs.GetConfigData().MVP_UseMySql)
            {
                Task.Run(async () =>
                {
                    try
                    {
                        var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(Path.Combine(Path.Combine(ModuleDirectory, "config"), "MySql_Settings.json")));
                        var connectionString = new MySqlConnectionStringBuilder
                        {
                            Server = connectionSettings!.MySqlHost,
                            Port = (uint)connectionSettings.MySqlPort,
                            Database = connectionSettings.MySqlDatabase,
                            UserID = connectionSettings.MySqlUsername,
                            Password = connectionSettings.MySqlPassword
                        }.ConnectionString;
                        
                        using (var connection = new MySqlConnection(connectionString))
                        {
                            await MySqlDataManager.RemoveFromMySqlAsync(Player.SteamID, connection, connectionSettings);
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"An error occurred while removing data from MySQL: {ex.Message}");
                    }
                });
            }
            if (!string.IsNullOrEmpty(Localizer["player.musickit.remove"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.musickit.remove"], option.Text);
            }
            MenuManager.CloseActiveMenu(Player);
            return;
        }
        
        if(!string.IsNullOrEmpty(HasFlag) && !Helper.IsPlayerInGroupPermission(Player, HasFlag) && !isPreviewAble)
        {
            if (!string.IsNullOrEmpty(Localizer["player.not.allowed.musickit.flag"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.not.allowed.musickit.flag"]);
            }
            MenuManager.CloseActiveMenu(Player);
            return;
        }
        
        if(isPreviewAble)
        {
            var choosedkit =  option.Text;
            
            IMenu VoteGameModeMenu;
            if (Configs.GetConfigData().MVP_ChangeMVPMenuFromChatToCentre)
            {
                VoteGameModeMenu = new CenterHtmlMenu(Localizer["menu.are.you.sure", choosedkit], this);
            }
            else
            {
                VoteGameModeMenu = new ChatMenu(Localizer["menu.are.you.sure", choosedkit]);
            }

            string[] answers = { Localizer["menu.answer.yes"], Localizer["menu.answer.no"]};

            foreach (string answer in answers)
            {
                VoteGameModeMenu.AddMenuOption(answer, (Player, option) => HandleMenu2(Player, option, ChoosenKitKey, HasFlag, isPreviewAble, choosedkit));
            }
            VoteGameModeMenu.AddMenuOption(Localizer["menu.back"], (Player, option) => HandleMenu2(Player, option, ChoosenKitKey, HasFlag, isPreviewAble, choosedkit));
            if (Configs.GetConfigData().MVP_ChangeMVPMenuFromChatToCentre)
            {
                if (VoteGameModeMenu is CenterHtmlMenu centerHtmlMenu)
                {
                    MenuManager.OpenCenterHtmlMenu(this, Player, centerHtmlMenu);
                }
            }
            else
            {
                if (VoteGameModeMenu is ChatMenu chatMenu)
                {
                    MenuManager.OpenChatMenu(Player, chatMenu);
                }
            }
            return;
        }
        if (!Globals.Choosed_MVP.ContainsKey(Player.SteamID))
        {
            Globals.Choosed_MVP.Add(Player.SteamID, ChoosenKitKey);
        }
        if (Globals.Choosed_MVP.ContainsKey(Player.SteamID))
        {
            Globals.Choosed_MVP[Player.SteamID] = ChoosenKitKey;
        }
        if (!string.IsNullOrEmpty(Localizer["player.musickit.selected"]))
        {
            Helper.AdvancedPrintToChat(Player, Localizer["player.musickit.selected"], option.Text);
        }

        Helper.SaveToJsonFile(Player.SteamID, ChoosenKitKey, personData.Client_Mute_MVP, DateTime.Now);
        MenuManager.CloseActiveMenu(Player);
    }
    private void HandleMenu2(CCSPlayerController Player, ChatMenuOption option, string ChoosenKitKey, string HasFlag, bool isPreviewAble, string choosedkit)
    {
        Helper.PersonData personData = Helper.RetrievePersonDataById(Player.SteamID);
        if(option.Text == Localizer["menu.answer.yes"])
        {
            if(!string.IsNullOrEmpty(HasFlag) && !Helper.IsPlayerInGroupPermission(Player, HasFlag))
            {
                if (!string.IsNullOrEmpty(Localizer["player.not.allowed.musickit.flag"]))
                {
                    Helper.AdvancedPrintToChat(Player, Localizer["player.not.allowed.musickit.flag"]);
                }
                MenuManager.CloseActiveMenu(Player);
                return;
            }
            if (!Globals.Choosed_MVP.ContainsKey(Player.SteamID))
            {
                Globals.Choosed_MVP.Add(Player.SteamID, ChoosenKitKey);
            }
            if (Globals.Choosed_MVP.ContainsKey(Player.SteamID))
            {
                Globals.Choosed_MVP[Player.SteamID] = ChoosenKitKey;
            }
            if (!string.IsNullOrEmpty(Localizer["player.musickit.selected"]))
            {
                Helper.AdvancedPrintToChat(Player, Localizer["player.musickit.selected"], choosedkit);
            }
            Helper.SaveToJsonFile(Player.SteamID, ChoosenKitKey, personData.Client_Mute_MVP, DateTime.Now);
            MenuManager.CloseActiveMenu(Player);
        }else if(option.Text == Localizer["menu.answer.no"])
        {
            string MVPKitChoosen = ChoosenKitKey;
            try
            {
                string jsonPath = GetMvpSettingsPath();
                string jsonContent = File.ReadAllText(jsonPath);
                dynamic mvpSettings = JsonConvert.DeserializeObject(jsonContent)!;
                var chosenKit = mvpSettings[MVPKitChoosen];
                string kitName = chosenKit["MVP_Kit_Name"];

                List<string> soundPaths = new List<string>();
                int soundPathCount = 0;
                while (chosenKit[$"Sound_Path_{soundPathCount + 1}"] != null)
                {
                    soundPathCount++;
                }

                for (int i = 1; i <= soundPathCount; i++)
                {
                    string soundPathKey = $"Sound_Path_{i}";
                    if (chosenKit[soundPathKey] != null)
                    {
                        string soundPathValue = chosenKit[soundPathKey];
                        soundPaths.Add(soundPathValue);
                    }
                }

                Random rng = new Random();
                string soundPath = soundPaths.FirstOrDefault(path => !Globals.playedPaths.Contains(path))!;
                
                if (Globals.playedPaths.Count == soundPaths.Count)
                {
                    Globals.playedPaths.Clear();
                }
                if (Globals.playedPaths.Count == 0)
                {
                    soundPaths = soundPaths.OrderBy(x => rng.Next()).ToList();
                }
                if (soundPath == null || Globals.playedPaths.Count == 0)
                {
                    soundPath = soundPaths.FirstOrDefault(path => !Globals.playedPaths.Contains(path))!;
                }

                if (soundPath != null)
                {
                    if (!string.IsNullOrEmpty(Localizer["player.preview"]))
                    {
                        Helper.AdvancedPrintToChat(Player, Localizer["player.preview"], choosedkit);
                    }
                    string pSound = soundPath.EndsWith(".vsnd_c", StringComparison.OrdinalIgnoreCase) ? soundPath[..^2] : soundPath;
                    Player.ExecuteClientCommand("play " + pSound);
                    Globals.playedPaths.Add(soundPath);
                }
            }
            catch { }
        }else if(option.Text == Localizer["menu.back"])
        {
            OpenMvpMenu(Player);
        }
    }

    private HookResult OnEventRoundMvp(EventRoundMvp @event, GameEventInfo info)
    {
        if(@event == null)return HookResult.Continue;
        var Player = @event.Userid;
        if (Player == null || !Player.IsValid)return HookResult.Continue;
        var PlayerSteamID = Player.SteamID;

        // Force disable Valve's default MVP sound for all players (we play custom ones)
        @event.Musickitid = 0;
        @event.Nomusic = 1;

        if (Player != null && Player.IsValid)
        {
            try
            {
                Player.MusicKitID = 0;
                if (Player.InventoryServices != null)
                {
                    Player.InventoryServices.MusicID = 0;
                }
            }
            catch { }
        }

        if(Configs.GetConfigData().MVP_ForceDisableDefaultMVP_ToAll)
        {   
            var allplayerz = Helper.GetAllController();
            allplayerz.ForEach(playerz =>
            {
                if (playerz != null && playerz.IsValid && !playerz.IsBot)
                {
                    try
                    {
                        playerz.MusicKitID = 0;
                        if (playerz.InventoryServices != null)
                        {
                            playerz.InventoryServices.MusicID = 0;
                        }
                    }
                    catch { }
                }
            });
        }

        if (Globals.Choosed_MVP.ContainsKey(PlayerSteamID))
        {
            string MVPKitChoosen = Globals.Choosed_MVP[PlayerSteamID];

            try
            {
                string jsonPath = GetMvpSettingsPath();
                string jsonContent = File.ReadAllText(jsonPath);
                dynamic mvpSettings = JsonConvert.DeserializeObject(jsonContent)!;
                var chosenKit = mvpSettings[MVPKitChoosen];
                string kitName = chosenKit["MVP_Kit_Name"];
                Globals.MVP_PlayerName = Player.PlayerName;
                Globals.MVP_KitName = kitName;
                bool custommessage = chosenKit["Custom_Message"] != null ? (bool)chosenKit["Custom_Message"] : false;
                bool messageChatEnabled = chosenKit["Message_Chat"] != null ? (bool)chosenKit["Message_Chat"] : false;

                bool messageCenterEnabled = chosenKit["Message_Center"] != null ? (bool)chosenKit["Message_Center"] : false;
                float messageCenterInSecs = chosenKit["Message_Center_InSecs"] != null ? (float)chosenKit["Message_Center_InSecs"] : 10;

                bool messageCenterBottomEnabled = chosenKit["Message_Center_Bottom"] != null ? (bool)chosenKit["Message_Center_Bottom"] : false;
                float messageCenterBottomInSecs = chosenKit["Message_Center_Bottom_InSecs"] != null ? (float)chosenKit["Message_Center_Bottom_InSecs"] : 10;

                List<string> soundPaths = new List<string>();
                int soundPathCount = 0;
                while (chosenKit[$"Sound_Path_{soundPathCount + 1}"] != null)
                {
                    soundPathCount++;
                }

                for (int i = 1; i <= soundPathCount; i++)
                {
                    string soundPathKey = $"Sound_Path_{i}";
                    if (chosenKit[soundPathKey] != null)
                    {
                        string soundPathValue = chosenKit[soundPathKey];
                        soundPaths.Add(soundPathValue);
                    }
                }

                Random rng = new Random();
                string soundPath = soundPaths.FirstOrDefault(path => !Globals.playedPaths.Contains(path))!;
                
                if (Globals.playedPaths.Count == soundPaths.Count)
                {
                    Globals.playedPaths.Clear();
                }
                if (Globals.playedPaths.Count == 0)
                {
                    soundPaths = soundPaths.OrderBy(x => rng.Next()).ToList();
                }
                if (soundPath == null || Globals.playedPaths.Count == 0)
                {
                    soundPath = soundPaths.FirstOrDefault(path => !Globals.playedPaths.Contains(path))!;
                }
                
                var allplayers = Helper.GetAllController();
                allplayers.ForEach(players =>
                {
                    if (players != null && players.IsValid && !players.IsBot && !Globals.client_mute.ContainsKey(players.SteamID))
                    {
                        if (soundPath != null)
                        {
                            
                            if(custommessage)
                            {
                                if(messageChatEnabled)
                                {
                                    if (!string.IsNullOrEmpty(Localizer[MVPKitChoosen + ".now.playing.chat"]))
                                    {
                                        Helper.AdvancedPrintToChat(players, Localizer[MVPKitChoosen + ".now.playing.chat"], Player.PlayerName, kitName);
                                    }
                                }
                                

                                if(messageCenterEnabled)
                                {
                                    Globals.Show_Center = true;
                                    Globals.MVP_Locaraize_Center = Localizer[MVPKitChoosen + ".now.playing.centre", Globals.MVP_PlayerName, Globals.MVP_KitName];
                                    HUDTimer_Center?.Kill();
                                    HUDTimer_Center = null;
                                    HUDTimer_Center = AddTimer(messageCenterInSecs, HUDTimer_Center_Callback, TimerFlags.STOP_ON_MAPCHANGE);
                                }

                                if(messageCenterBottomEnabled)
                                {
                                    Globals.Show_Center_Bottom = true;
                                    Globals.MVP_Locaraize_Center_Bottom = Localizer[MVPKitChoosen + ".now.playing.centre.bottom", Globals.MVP_PlayerName, Globals.MVP_KitName];
                                    HUDTimer_Center_Bottom?.Kill();
                                    HUDTimer_Center_Bottom = null;
                                    HUDTimer_Center_Bottom = AddTimer(messageCenterBottomInSecs, HUDTimer_Center_Bottom_Callback, TimerFlags.STOP_ON_MAPCHANGE);
                                }
                            }else
                            {
                                if(messageChatEnabled)
                                {
                                    if (!string.IsNullOrEmpty(Localizer["now.playing.chat"]))
                                    {
                                        Helper.AdvancedPrintToChat(players, Localizer["now.playing.chat"], Player.PlayerName, kitName);
                                    }
                                }
                                

                                if(messageCenterEnabled)
                                {
                                    Globals.Show_Center = true;
                                    Globals.MVP_Locaraize_Center = Localizer["now.playing.centre", Globals.MVP_PlayerName, Globals.MVP_KitName];
                                    HUDTimer_Center?.Kill();
                                    HUDTimer_Center = null;
                                    HUDTimer_Center = AddTimer(messageCenterInSecs, HUDTimer_Center_Callback, TimerFlags.STOP_ON_MAPCHANGE);
                                }

                                if(messageCenterBottomEnabled)
                                {
                                    Globals.Show_Center_Bottom = true;
                                    Globals.MVP_Locaraize_Center_Bottom = Localizer["now.playing.centre.bottom", Globals.MVP_PlayerName, Globals.MVP_KitName];
                                    HUDTimer_Center_Bottom?.Kill();
                                    HUDTimer_Center_Bottom = null;
                                    HUDTimer_Center_Bottom = AddTimer(messageCenterBottomInSecs, HUDTimer_Center_Bottom_Callback, TimerFlags.STOP_ON_MAPCHANGE);
                                }
                            }
                            string pSound = soundPath.EndsWith(".vsnd_c", StringComparison.OrdinalIgnoreCase) ? soundPath[..^2] : soundPath;
                            players.ExecuteClientCommand("play " + pSound);
                            Globals.playedPaths.Add(soundPath);
                        }
                    }
                });
                
            }
            catch { }
        }
        return HookResult.Continue;
    }
    private void HUDTimer_Center_Callback()
    {
        Globals.Show_Center = false;
    }
    private void HUDTimer_Center_Bottom_Callback()
    {
        Globals.Show_Center_Bottom = false;
    }
    public void OnTick()
    {
        if(Globals.Show_Center || Globals.Show_Center_Bottom)
        {
            foreach (var player in Helper.GetAllController())
            {
                if (player == null || !player.IsValid || player.IsBot || player.IsHLTV || Globals.client_mute.ContainsKey(player.SteamID)) continue;
                if(Globals.Show_Center)
                {
                    StringBuilder builder = new StringBuilder();
                    string Show_Center = Globals.MVP_Locaraize_Center;
                    builder.AppendLine(Show_Center);
                    builder.AppendLine("</div>");
                    var centerhtml = builder.ToString();
                    player.PrintToCenterHtml(centerhtml);
                }
                if(Globals.Show_Center_Bottom)
                {
                    StringBuilder builder = new StringBuilder();
                    string Show_Center_bottom = Globals.MVP_Locaraize_Center_Bottom;
                    builder.Append(Show_Center_bottom);
                    var centerhtml = builder.ToString();
                    player.PrintToCenter(centerhtml);
                }
            }
        }
    }


    public HookResult OnPlayerDisconnect(EventPlayerDisconnect @event, GameEventInfo info)
    {
        if (@event == null) return HookResult.Continue;
        var player = @event.Userid;
        
        if (player == null || !player.IsValid || player.IsBot || player.IsHLTV) return HookResult.Continue;
        var playerid = player.SteamID;
        Helper.PersonData personData = Helper.RetrievePersonDataById(playerid);
        DateTime personDate = DateTime.Now;

        Globals.allow_groups.Remove(playerid);
        Globals.Choosed_MVP.Remove(playerid);
        Globals.client_mute.Remove(playerid);
        Globals.client_cantoggle.Remove(playerid);

        if(Configs.GetConfigData().MVP_UseMySql)
        {
            Task.Run(async () =>
            {
                try
                {
                    var connectionSettings = JsonConvert.DeserializeObject<MySqlDataManager.MySqlConnectionSettings>(await File.ReadAllTextAsync(Path.Combine(Path.Combine(ModuleDirectory, "config"), "MySql_Settings.json")));
                    var connectionString = new MySqlConnectionStringBuilder
                    {
                        Server = connectionSettings!.MySqlHost,
                        Port = (uint)connectionSettings.MySqlPort,
                        Database = connectionSettings.MySqlDatabase,
                        UserID = connectionSettings.MySqlUsername,
                        Password = connectionSettings.MySqlPassword
                    }.ConnectionString;
                    
                    using (var connection = new MySqlConnection(connectionString))
                    {
                        await connection.OpenAsync();
                        await MySqlDataManager.CreatePersonDataTableIfNotExistsAsync(connection);

                        DateTime personDate = DateTime.Now;
                        var personData = Helper.RetrievePersonDataById(playerid);
                        if (personData.PlayerSteamID != 0)
                        {
                            await MySqlDataManager.SaveToMySqlAsync(playerid, personData.MusicKit!, personData.Client_Mute_MVP, personDate, connection, connectionSettings);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"======================== ERROR =============================");
                    Console.WriteLine($"An error occurred: {ex.Message}");
                    Console.WriteLine($"======================== ERROR =============================");
                }
            });
        }

        return HookResult.Continue;
    }
    public void OnMapEnd()
    {
        Helper.ClearVariables();
    }
    public override void Unload(bool hotReload)
    {
        Helper.ClearVariables();
    }
}