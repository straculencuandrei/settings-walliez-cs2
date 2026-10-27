using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security;
using System.Security.Permissions;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Core.Capabilities;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Entities;
using CounterStrikeSharp.API.Modules.Entities.Constants;
using CounterStrikeSharp.API.Modules.Memory;
using CounterStrikeSharp.API.Modules.Memory.DynamicFunctions;
using CounterStrikeSharp.API.Modules.Menu;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;
using Dapper;
using MenuManager;
using Microsoft.Extensions.Localization;
using Microsoft.Extensions.Logging;
using MySqlConnector;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace WeaponPaints;

[MinimumApiVersion(338)]
public class WeaponPaints : BasePlugin, IPluginConfig<WeaponPaintsConfig>
{
	private bool _mvpPlayed;

	private bool _giveNamedItemHooked;

	private static readonly Dictionary<string, string> WeaponList = new Dictionary<string, string>
	{
		{ "weapon_deagle", "Desert Eagle" },
		{ "weapon_elite", "Dual Berettas" },
		{ "weapon_fiveseven", "Five-SeveN" },
		{ "weapon_glock", "Glock-18" },
		{ "weapon_ak47", "AK-47" },
		{ "weapon_aug", "AUG" },
		{ "weapon_awp", "AWP" },
		{ "weapon_famas", "FAMAS" },
		{ "weapon_g3sg1", "G3SG1" },
		{ "weapon_galilar", "Galil AR" },
		{ "weapon_m249", "M249" },
		{ "weapon_m4a1", "M4A4" },
		{ "weapon_mac10", "MAC-10" },
		{ "weapon_p90", "P90" },
		{ "weapon_mp5sd", "MP5-SD" },
		{ "weapon_ump45", "UMP-45" },
		{ "weapon_xm1014", "XM1014" },
		{ "weapon_bizon", "PP-Bizon" },
		{ "weapon_mag7", "MAG-7" },
		{ "weapon_negev", "Negev" },
		{ "weapon_sawedoff", "Sawed-Off" },
		{ "weapon_tec9", "Tec-9" },
		{ "weapon_taser", "Zeus x27" },
		{ "weapon_hkp2000", "P2000" },
		{ "weapon_mp7", "MP7" },
		{ "weapon_mp9", "MP9" },
		{ "weapon_nova", "Nova" },
		{ "weapon_p250", "P250" },
		{ "weapon_scar20", "SCAR-20" },
		{ "weapon_sg556", "SG 553" },
		{ "weapon_ssg08", "SSG 08" },
		{ "weapon_m4a1_silencer", "M4A1-S" },
		{ "weapon_usp_silencer", "USP-S" },
		{ "weapon_cz75a", "CZ75-Auto" },
		{ "weapon_revolver", "R8 Revolver" },
		{ "weapon_knife", "Default Knife" },
		{ "weapon_knife_m9_bayonet", "M9 Bayonet" },
		{ "weapon_knife_karambit", "Karambit" },
		{ "weapon_bayonet", "Bayonet" },
		{ "weapon_knife_survival_bowie", "Bowie Knife" },
		{ "weapon_knife_butterfly", "Butterfly Knife" },
		{ "weapon_knife_falchion", "Falchion Knife" },
		{ "weapon_knife_flip", "Flip Knife" },
		{ "weapon_knife_gut", "Gut Knife" },
		{ "weapon_knife_tactical", "Huntsman Knife" },
		{ "weapon_knife_push", "Shadow Daggers" },
		{ "weapon_knife_gypsy_jackknife", "Navaja Knife" },
		{ "weapon_knife_stiletto", "Stiletto Knife" },
		{ "weapon_knife_widowmaker", "Talon Knife" },
		{ "weapon_knife_ursus", "Ursus Knife" },
		{ "weapon_knife_css", "Classic Knife" },
		{ "weapon_knife_cord", "Paracord Knife" },
		{ "weapon_knife_canis", "Survival Knife" },
		{ "weapon_knife_outdoor", "Nomad Knife" },
		{ "weapon_knife_skeleton", "Skeleton Knife" },
		{ "weapon_knife_kukri", "Kukri Knife" }
	};

	public static IStringLocalizer? _localizer;

	internal static readonly ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, string>> GPlayersKnife = new ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, string>>();

	internal static readonly ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>> GPlayersGlove = new ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>>();

	internal static readonly ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>> GPlayersMusic = new ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>>();

	internal static readonly ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>> GPlayersPin = new ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ushort>>();

	internal static readonly ConcurrentDictionary<int, (string? CT, string? T)> GPlayersAgent = new ConcurrentDictionary<int, (string, string)>();

	internal static readonly ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>>> GPlayerWeaponsInfo = new ConcurrentDictionary<int, ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>>>();

	internal static List<JObject> SkinsList = new List<JObject>();

	internal static List<JObject> PinsList = new List<JObject>();

	internal static List<JObject> GlovesList = new List<JObject>();

	internal static List<JObject> AgentsList = new List<JObject>();

	internal static List<JObject> MusicList = new List<JObject>();

	internal static WeaponSynchronization? WeaponSync;

	private static bool _gBCommandsAllowed = true;

	private readonly Dictionary<int, string> _playerWeaponImage = new Dictionary<int, string>();

	private static readonly Dictionary<int, DateTime> CommandsCooldown = new Dictionary<int, DateTime>();

	internal static Database? Database;

	private static readonly MemoryFunctionVoid<nint, string, float> CAttributeListSetOrAddAttributeValueByName = new MemoryFunctionVoid<nint, string, float>(GameData.GetSignature("CAttributeList_SetOrAddAttributeValueByName"));

	private const ulong MinimumCustomItemId = 65578uL;

	private ulong _nextItemId = 65578uL;

	private static readonly bool IsWindows = RuntimeInformation.IsOSPlatform(OSPlatform.Windows);

	private readonly ConcurrentDictionary<int, ConcurrentDictionary<int, float>> _temporaryPlayerWeaponWear = new ConcurrentDictionary<int, ConcurrentDictionary<int, float>>();

	internal static IMenuApi? MenuApi;

	private static readonly PluginCapability<IMenuApi> MenuCapability = new PluginCapability<IMenuApi>("menu:nfcore");

	private int _fadeSeed;

	internal List<CCSPlayerController> Players = new List<CCSPlayerController>();

	private static Dictionary<int, string> WeaponDefindex { get; } = new Dictionary<int, string>
	{
		{ 1, "weapon_deagle" },
		{ 2, "weapon_elite" },
		{ 3, "weapon_fiveseven" },
		{ 4, "weapon_glock" },
		{ 7, "weapon_ak47" },
		{ 8, "weapon_aug" },
		{ 9, "weapon_awp" },
		{ 10, "weapon_famas" },
		{ 11, "weapon_g3sg1" },
		{ 13, "weapon_galilar" },
		{ 14, "weapon_m249" },
		{ 16, "weapon_m4a1" },
		{ 17, "weapon_mac10" },
		{ 19, "weapon_p90" },
		{ 23, "weapon_mp5sd" },
		{ 24, "weapon_ump45" },
		{ 25, "weapon_xm1014" },
		{ 26, "weapon_bizon" },
		{ 27, "weapon_mag7" },
		{ 28, "weapon_negev" },
		{ 29, "weapon_sawedoff" },
		{ 30, "weapon_tec9" },
		{ 31, "weapon_taser" },
		{ 32, "weapon_hkp2000" },
		{ 33, "weapon_mp7" },
		{ 34, "weapon_mp9" },
		{ 35, "weapon_nova" },
		{ 36, "weapon_p250" },
		{ 38, "weapon_scar20" },
		{ 39, "weapon_sg556" },
		{ 40, "weapon_ssg08" },
		{ 60, "weapon_m4a1_silencer" },
		{ 61, "weapon_usp_silencer" },
		{ 63, "weapon_cz75a" },
		{ 64, "weapon_revolver" },
		{ 500, "weapon_bayonet" },
		{ 503, "weapon_knife_css" },
		{ 505, "weapon_knife_flip" },
		{ 506, "weapon_knife_gut" },
		{ 507, "weapon_knife_karambit" },
		{ 508, "weapon_knife_m9_bayonet" },
		{ 509, "weapon_knife_tactical" },
		{ 512, "weapon_knife_falchion" },
		{ 514, "weapon_knife_survival_bowie" },
		{ 515, "weapon_knife_butterfly" },
		{ 516, "weapon_knife_push" },
		{ 517, "weapon_knife_cord" },
		{ 518, "weapon_knife_canis" },
		{ 519, "weapon_knife_ursus" },
		{ 520, "weapon_knife_gypsy_jackknife" },
		{ 521, "weapon_knife_outdoor" },
		{ 522, "weapon_knife_stiletto" },
		{ 523, "weapon_knife_widowmaker" },
		{ 525, "weapon_knife_skeleton" },
		{ 526, "weapon_knife_kukri" }
	};

	internal static WeaponPaints Instance { get; private set; } = new WeaponPaints();

	public WeaponPaintsConfig Config { get; set; } = new WeaponPaintsConfig();

	private static WeaponPaintsConfig _config { get; set; } = new WeaponPaintsConfig();

	public override string ModuleAuthor => "Nereziel & daffyy";

	public override string ModuleDescription => "Skin, gloves, agents and knife selector, standalone and web-based";

	public override string ModuleName => "WeaponPaints";

	public override string ModuleVersion => "3.3a";

	private void OnCommandRefresh(CCSPlayerController? player, CommandInfo command)
	{
		if (!Config.Additional.CommandWpEnabled || !Config.Additional.SkinEnabled || !_gBCommandsAllowed || !Utility.IsPlayerValid(player) || player == null || !player.IsValid || !player.UserId.HasValue || player.IsBot)
		{
			return;
		}
		PlayerInfo playerInfo = new PlayerInfo
		{
			UserId = player.UserId,
			Slot = player.Slot,
			Index = (int)player.Index,
			SteamId = player?.SteamID.ToString(),
			Name = player?.PlayerName
		};
		CCSPlayerController? cCSPlayerController = player;
		object ipAddress;
		if ((object)cCSPlayerController == null)
		{
			ipAddress = null;
		}
		else
		{
			string? ipAddress2 = cCSPlayerController.IpAddress;
			ipAddress = ((ipAddress2 != null) ? ipAddress2.Split(":")[0] : null);
		}
		playerInfo.IpAddress = (string?)ipAddress;
		PlayerInfo playerInfo2 = playerInfo;
		try
		{
			if ((player != null && !CommandsCooldown.TryGetValue(player.Slot, out var value)) || (player != null && DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow)))
			{
				CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
				if (WeaponSync != null)
				{
					Task.Run(async () =>
					{
						try
						{
							await WeaponSync.GetPlayerData(playerInfo2);
						}
						catch (Exception ex)
						{
							Logger.LogWarning("[WeaponPaints] Error loading player data: " + ex.Message);
						}
						Server.NextFrame(() =>
						{
							if (player == null || !player.IsValid || !player.PawnIsAlive) return;
							GivePlayerGloves(player);
							RefreshWeapons(player);
							GivePlayerAgent(player);
							GivePlayerMusicKit(player);
							GivePlayerPin(player);
						});
					});
				}
				else
				{
					GivePlayerGloves(player);
					RefreshWeapons(player);
					GivePlayerAgent(player);
					GivePlayerMusicKit(player);
					GivePlayerPin(player);
				}
				if (!string.IsNullOrEmpty(Localizer["wp_command_refresh_done"]))
				{
					player.Print(Localizer["wp_command_refresh_done"]);
				}
			}
			else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
			{
				player.Print(Localizer["wp_command_cooldown"]);
			}
		}
		catch (Exception)
		{
		}
	}

	private void OnCommandWS(CCSPlayerController? player, CommandInfo command)
	{
		if (Config.Additional.SkinEnabled && Utility.IsPlayerValid(player))
		{
			if (!string.IsNullOrEmpty(Localizer["wp_info_website"]))
			{
				player.Print(Localizer["wp_info_website", new object[1] { Config.Website }]);
			}
			if (!string.IsNullOrEmpty(Localizer["wp_info_refresh"]))
			{
				player.Print(Localizer["wp_info_refresh"]);
			}
			if (Config.Additional.GloveEnabled && !string.IsNullOrEmpty(Localizer["wp_info_glove"]))
			{
				player.Print(Localizer["wp_info_glove"]);
			}
			if (Config.Additional.AgentEnabled && !string.IsNullOrEmpty(Localizer["wp_info_agent"]))
			{
				player.Print(Localizer["wp_info_agent"]);
			}
			if (Config.Additional.MusicEnabled && !string.IsNullOrEmpty(Localizer["wp_info_music"]))
			{
				player.Print(Localizer["wp_info_music"]);
			}
			if (Config.Additional.PinsEnabled && !string.IsNullOrEmpty(Localizer["wp_info_pin"]))
			{
				player.Print(Localizer["wp_info_pin"]);
			}
			if (Config.Additional.KnifeEnabled && !string.IsNullOrEmpty(Localizer["wp_info_knife"]))
			{
				player.Print(Localizer["wp_info_knife"]);
			}
		}
	}

	private void RegisterCommands()
	{
		_config.Additional.CommandStattrak.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Stattrak toggle", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player))
				{
					OnCommandStattrak(player, info);
				}
			});
		});
		_config.Additional.CommandSkin.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Skins info", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player))
				{
					OnCommandWS(player, info);
				}
			});
		});
		_config.Additional.CommandRefresh.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Skins refresh", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player))
				{
					OnCommandRefresh(player, info);
				}
			});
		});
		if (Config.Additional.CommandKillEnabled)
		{
			_config.Additional.CommandKill.ForEach((string c) =>
			{
				AddCommand("css_" + c, "kill yourself", (CCSPlayerController? player, CommandInfo _) =>
				{
					if (!(player == null) && Utility.IsPlayerValid(player) && !(player.PlayerPawn.Value == null) && player.PlayerPawn.IsValid)
					{
						player.PlayerPawn.Value.CommitSuicide(explode: true, force: false);
					}
				});
			});
		}
		AddCommand("wp_refresh", "Admin refresh player skins", (CCSPlayerController? player, CommandInfo info) =>
		{
			OnCommandSkinRefresh(player, info);
		});
	}

	private void OnCommandSkinRefresh(CCSPlayerController? player, CommandInfo command)
	{
		if (!Config.Additional.CommandWpEnabled || !Config.Additional.SkinEnabled || !_gBCommandsAllowed || player != null)
		{
			return;
		}
		string args = command.GetArg(1);
		if (string.IsNullOrEmpty(args))
		{
			Console.WriteLine("[WeaponPaints] Usage: wp_refresh <steamid64|all>");
			Console.WriteLine("[WeaponPaints] Examples:");
			Console.WriteLine("[WeaponPaints]   wp_refresh all - Refresh skins for all players");
			Console.WriteLine("[WeaponPaints]   wp_refresh 76561198012345678 - Refresh skins by SteamID64");
			return;
		}
		List<CCSPlayerController> list = new List<CCSPlayerController>();
		if (args.Equals("all", StringComparison.OrdinalIgnoreCase))
		{
			list = (from p in Utilities.GetPlayers()
				where p != null && p.IsValid && !p.IsBot && p.UserId.HasValue
				select p).ToList();
			if (list.Count == 0)
			{
				Console.WriteLine("[WeaponPaints] No players connected to refresh.");
				return;
			}
			Console.WriteLine($"[WeaponPaints] Refreshing skins for {list.Count} players...");
		}
		else
		{
			CCSPlayerController cCSPlayerController = Utilities.GetPlayers().FirstOrDefault((CCSPlayerController p) => p != null && p.IsValid && !p.IsBot && p.UserId.HasValue && p.SteamID.ToString() == args);
			if (cCSPlayerController == null)
			{
				Console.WriteLine("[WeaponPaints] Player with SteamID64 '" + args + "' not found.");
				return;
			}
			list.Add(cCSPlayerController);
			Console.WriteLine("[WeaponPaints] Refreshing skins for " + cCSPlayerController.PlayerName + "...");
		}
		foreach (CCSPlayerController targetPlayer in list)
		{
			try
			{
				PlayerInfo playerInfo = new PlayerInfo
				{
					UserId = targetPlayer.UserId,
					Slot = targetPlayer.Slot,
					Index = (int)targetPlayer.Index,
					SteamId = targetPlayer.SteamID.ToString(),
					Name = targetPlayer.PlayerName
				};
				string? ipAddress = targetPlayer.IpAddress;
				playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
				PlayerInfo playerInfo2 = playerInfo;
				if (WeaponSync != null)
				{
					Task.Run(async () =>
					{
						try
						{
							await WeaponSync.GetPlayerData(playerInfo2);
						}
						catch (Exception ex)
						{
							Logger.LogWarning("[WeaponPaints] Error loading player data: " + ex.Message);
						}
						Server.NextFrame(() =>
						{
							if (targetPlayer == null || !targetPlayer.IsValid || !targetPlayer.PawnIsAlive) return;
							GivePlayerGloves(targetPlayer);
							RefreshWeapons(targetPlayer);
							GivePlayerAgent(targetPlayer);
							GivePlayerMusicKit(targetPlayer);
							GivePlayerPin(targetPlayer);
						});
					});
				}
				else
				{
					GivePlayerGloves(targetPlayer);
					RefreshWeapons(targetPlayer);
					GivePlayerAgent(targetPlayer);
					GivePlayerMusicKit(targetPlayer);
					GivePlayerPin(targetPlayer);
				}
				if (!string.IsNullOrEmpty(Localizer["wp_command_refresh_done"]))
				{
					targetPlayer.Print(Localizer["wp_command_refresh_done"]);
				}
				Console.WriteLine("[WeaponPaints] Skins refreshed for " + targetPlayer.PlayerName);
			}
			catch (Exception ex)
			{
				Console.WriteLine("[WeaponPaints] Error refreshing skins for " + targetPlayer.PlayerName + ": " + ex.Message);
			}
		}
		Console.WriteLine("[WeaponPaints] Refresh process completed.");
	}

	private void OnCommandStattrak(CCSPlayerController? player, CommandInfo commandInfo)
	{
		if (player == null || !player.IsValid)
		{
			return;
		}
		CBasePlayerWeapon cBasePlayerWeapon = player.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value;
		if (!(cBasePlayerWeapon == null) && cBasePlayerWeapon.IsValid && HasChangedPaint(player, cBasePlayerWeapon.AttributeManager.Item.ItemDefinitionIndex, out WeaponInfo weaponInfo) && weaponInfo != null)
		{
			weaponInfo.StatTrak = !weaponInfo.StatTrak;
			RefreshWeapons(player);
			if (!string.IsNullOrEmpty(Localizer["wp_stattrak_action"]))
			{
				player.Print(Localizer["wp_stattrak_action"]);
			}
		}
	}

	private void SetupKnifeMenu()
	{
		if (!Config.Additional.KnifeEnabled || !_gBCommandsAllowed)
		{
			return;
		}
		Dictionary<string, string> knivesOnly = WeaponList.Where((KeyValuePair<string, string> pair) => pair.Key.StartsWith("weapon_knife") || pair.Key.StartsWith("weapon_bayonet")).ToDictionary((KeyValuePair<string, string> pair) => pair.Key, (KeyValuePair<string, string> pair) => pair.Value);
		IMenu giveItemMenu = Utility.CreateMenu(Localizer["wp_knife_menu_title"]);
		Action<CCSPlayerController, ChatMenuOption> onSelect = (CCSPlayerController player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player))
			{
				ConcurrentDictionary<CsTeam, string> orAdd = GPlayersKnife.GetOrAdd(player.Slot, new ConcurrentDictionary<CsTeam, string>());
				CsTeam[] teamsToCheck = ((player.TeamNum >= 2) ? new CsTeam[1] { player.Team } : new CsTeam[2]
				{
					CsTeam.Terrorist,
					CsTeam.CounterTerrorist
				});
				string knifeName = option.Text;
				string knifeKey = knivesOnly.FirstOrDefault((KeyValuePair<string, string> x) => x.Value == knifeName).Key;
				if (!string.IsNullOrEmpty(knifeKey))
				{
					if (!string.IsNullOrEmpty(Localizer["wp_knife_menu_select"]))
					{
						player.Print(Localizer["wp_knife_menu_select", new object[1] { knifeName }]);
					}
					if (!string.IsNullOrEmpty(Localizer["wp_knife_menu_kill"]) && Config.Additional.CommandKillEnabled)
					{
						player.Print(Localizer["wp_knife_menu_kill"]);
					}
					PlayerInfo playerInfo = new PlayerInfo
					{
						UserId = player.UserId,
						Slot = player.Slot,
						Index = (int)player.Index,
						SteamId = player.SteamID.ToString(),
						Name = player.PlayerName
					};
					string? ipAddress = player.IpAddress;
					playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
					PlayerInfo playerInfo2 = playerInfo;
					CsTeam[] array = teamsToCheck;
					foreach (CsTeam key in array)
					{
						orAdd[key] = knifeKey;
					}
					if (_gBCommandsAllowed && player.LifeState == 0)
					{
						RefreshWeapons(player);
					}
					if (WeaponSync != null)
					{
						Task.Run(async () =>
						{
							await WeaponSync.SyncKnifeToDatabase(playerInfo2, knifeKey, teamsToCheck);
						});
					}
				}
			}
		};
		foreach (KeyValuePair<string, string> item in knivesOnly)
		{
			giveItemMenu?.AddMenuOption(item.Value, onSelect);
		}
		_config.Additional.CommandKnife.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Knife Menu", (CCSPlayerController? player, CommandInfo _) =>
			{
				if (giveItemMenu != null && Utility.IsPlayerValid(player) && _gBCommandsAllowed && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
						giveItemMenu.PostSelectAction = PostSelectAction.Close;
						giveItemMenu.Open(player);
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	private void SetupSkinsMenu()
	{
		Dictionary<string, string> classNamesByWeapon = WeaponList.Except(new[] { new KeyValuePair<string, string>("weapon_knife", "Default Knife") }).ToDictionary((KeyValuePair<string, string> kvp) => kvp.Value, (KeyValuePair<string, string> kvp) => kvp.Key);
		IMenu weaponSelectionMenu = Utility.CreateMenu(Localizer["wp_skin_menu_weapon_title"]);
		Action<CCSPlayerController, ChatMenuOption> onSelect = (CCSPlayerController? player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player))
			{
				string text = option.Text;
				if (classNamesByWeapon.TryGetValue(text, out var selectedWeaponClassname))
				{
					List<JObject> list = SkinsList.Where((JObject skin) => skin.TryGetValue("weapon_name", out JToken value3) && value3?.ToString() == selectedWeaponClassname)?.ToList();
					IMenu menu = Utility.CreateMenu(Localizer["wp_skin_menu_skin_title", new object[1] { text }]);
					Action<CCSPlayerController, ChatMenuOption> onSelect2 = (CCSPlayerController p, ChatMenuOption opt) =>
					{
						if (Utility.IsPlayerValid(p))
						{
							JObject jObject = SkinsList.FirstOrDefault((JObject skin) => skin.TryGetValue("weapon_name", out JToken value5) && value5?.ToString() == selectedWeaponClassname);
							string text4 = opt.Text;
							string s = text4.Substring(text4.LastIndexOf('(') + 1).Trim(')');
							if (jObject != null && jObject.TryGetValue("weapon_defindex", out JToken value3) && int.TryParse(value3.ToString(), out var weaponDefIndex) && int.TryParse(s, out var paintId))
							{
								if (Config.Additional.ShowSkinImage)
								{
									string value4 = SkinsList.FirstOrDefault((JObject skin) => ((int?)skin["weapon_defindex"]).GetValueOrDefault() == weaponDefIndex && ((int?)skin["paint"]).GetValueOrDefault() == paintId && skin["image"] != null)?["image"]?.ToString() ?? "";
									_playerWeaponImage[p.Slot] = value4;
									AddTimer(2f, () =>
									{
										_playerWeaponImage.Remove(p.Slot);
									}, TimerFlags.STOP_ON_MAPCHANGE);
								}
								p.Print(Localizer["wp_skin_menu_select", new object[1] { text4 }]);
								ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> orAdd = GPlayerWeaponsInfo.GetOrAdd(p.Slot, new ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>>());
								CsTeam[] array = ((p.TeamNum >= 2) ? new CsTeam[1] { p.Team } : new CsTeam[2]
								{
									CsTeam.Terrorist,
									CsTeam.CounterTerrorist
								});
								CsTeam[] array2 = array;
								foreach (CsTeam key in array2)
								{
									ConcurrentDictionary<int, WeaponInfo> orAdd2 = orAdd.GetOrAdd(key, (CsTeam _) => new ConcurrentDictionary<int, WeaponInfo>());
									WeaponInfo orAdd3 = orAdd2.GetOrAdd(weaponDefIndex, (int _) => new WeaponInfo());
									orAdd3.Paint = paintId;
									orAdd3.Wear = 0.01f;
									orAdd3.Seed = 0;
								}
								PlayerInfo playerInfo = new PlayerInfo
								{
									UserId = p.UserId,
									Slot = p.Slot,
									Index = (int)p.Index,
									SteamId = p.SteamID.ToString(),
									Name = p.PlayerName
								};
								string? ipAddress = p.IpAddress;
								playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
								PlayerInfo playerInfo2 = playerInfo;
								if (_gBCommandsAllowed && p.LifeState == 0 && WeaponSync != null)
								{
									RefreshWeapons(player);
									try
									{
										Task.Run(async () =>
										{
											await WeaponSync.SyncWeaponPaintsToDatabase(playerInfo2);
										});
									}
									catch (Exception ex)
									{
										Utility.Log("Error syncing weapon paints: " + ex.Message);
									}
								}
							}
						}
					};
					if (list != null)
					{
						foreach (JObject item in list)
						{
							if (item.TryGetValue("paint_name", out JToken value) && item.TryGetValue("paint", out JToken value2))
							{
								string text2 = value?.ToString();
								string text3 = value2?.ToString();
								if (!string.IsNullOrEmpty(text2) && !string.IsNullOrEmpty(text3))
								{
									menu?.AddMenuOption(text2 + " (" + text3 + ")", onSelect2);
								}
							}
						}
					}
					if (player != null && Utility.IsPlayerValid(player))
					{
						menu?.Open(player);
					}
				}
			}
		};
		foreach (string item2 in from kvp in WeaponList
			where kvp.Key != "weapon_knife"
			select kvp.Value)
		{
			weaponSelectionMenu?.AddMenuOption(item2, onSelect);
		}
		_config.Additional.CommandSkinSelection.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Skins selection menu", (CCSPlayerController? player, CommandInfo _) =>
			{
				if (Utility.IsPlayerValid(player) && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
						weaponSelectionMenu?.Open(player);
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	private void SetupGlovesMenu()
	{
		IMenu glovesSelectionMenu = Utility.CreateMenu(Localizer["wp_glove_menu_title"]);
		if (glovesSelectionMenu == null)
		{
			return;
		}
		glovesSelectionMenu.PostSelectAction = PostSelectAction.Close;
		Action<CCSPlayerController, ChatMenuOption> onSelect = (CCSPlayerController? player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player) && (object)player != null)
			{
				string selectedPaintName = option.Text;
				ConcurrentDictionary<CsTeam, ushort> orAdd = GPlayersGlove.GetOrAdd(player.Slot, new ConcurrentDictionary<CsTeam, ushort>());
				CsTeam[] teamsToCheck = ((player.TeamNum >= 2) ? new CsTeam[1] { player.Team } : new CsTeam[2]
				{
					CsTeam.Terrorist,
					CsTeam.CounterTerrorist
				});
				JObject jObject = GlovesList.FirstOrDefault((JObject g) => g.ContainsKey("paint_name") && g["paint_name"]?.ToString() == selectedPaintName);
				string value = jObject?["image"]?.ToString() ?? "";
				if (jObject != null && jObject.ContainsKey("weapon_defindex") && jObject.ContainsKey("paint") && int.TryParse(jObject["weapon_defindex"]?.ToString(), out var weaponDefindex) && int.TryParse(jObject["paint"]?.ToString(), out var paint))
				{
					if (Config.Additional.ShowSkinImage)
					{
						_playerWeaponImage[player.Slot] = value;
						AddTimer(2f, () =>
						{
							_playerWeaponImage.Remove(player.Slot);
						}, TimerFlags.STOP_ON_MAPCHANGE);
					}
					if (!string.IsNullOrEmpty(Localizer["wp_glove_menu_select"]))
					{
						player.Print(Localizer["wp_glove_menu_select", new object[1] { selectedPaintName }]);
					}
					PlayerInfo playerInfo = new PlayerInfo
					{
						UserId = player.UserId,
						Slot = player.Slot,
						Index = (int)player.Index,
						SteamId = player.SteamID.ToString(),
						Name = player.PlayerName
					};
					string? ipAddress = player.IpAddress;
					playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
					PlayerInfo playerInfo2 = playerInfo;
					if (paint != 0)
					{
						if (!GPlayerWeaponsInfo.ContainsKey(player.Slot))
						{
							GPlayerWeaponsInfo[player.Slot] = new ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>>();
						}
						CsTeam[] array = teamsToCheck;
						foreach (CsTeam key in array)
						{
							if (!GPlayerWeaponsInfo[player.Slot].ContainsKey(key))
							{
								GPlayerWeaponsInfo[player.Slot][key] = new ConcurrentDictionary<int, WeaponInfo>();
							}
							orAdd[key] = (ushort)weaponDefindex;
							if (!GPlayerWeaponsInfo[player.Slot][key].ContainsKey(weaponDefindex))
							{
								WeaponInfo value2 = new WeaponInfo
								{
									Paint = paint
								};
								GPlayerWeaponsInfo[player.Slot][key][weaponDefindex] = value2;
							}
						}
					}
					else
					{
						GPlayersGlove.TryRemove(player.Slot, out ConcurrentDictionary<CsTeam, ushort> _);
					}
					if (WeaponSync != null)
					{
						Task.Run(async () =>
						{
							CsTeam[] array2 = teamsToCheck;
							foreach (CsTeam team in array2)
							{
								await WeaponSync.SyncGloveToDatabase(playerInfo2, (ushort)weaponDefindex, teamsToCheck);
								if (!GPlayerWeaponsInfo[playerInfo2.Slot][team].TryGetValue(weaponDefindex, out WeaponInfo value4))
								{
									value4 = new WeaponInfo();
									GPlayerWeaponsInfo[playerInfo2.Slot][team][weaponDefindex] = value4;
								}
								value4.Paint = paint;
								value4.Wear = 0f;
								value4.Seed = 0;
								await WeaponSync.SyncWeaponPaintsToDatabase(playerInfo2);
								value4 = null;
							}
						});
						AddTimer(0.1f, () =>
						{
							GivePlayerGloves(player);
						});
						AddTimer(0.25f, () =>
						{
							GivePlayerGloves(player);
						});
					}
				}
			}
		};
		foreach (string item in from gloveObject in GlovesList
			select gloveObject["paint_name"]?.ToString() ?? "" into paintName
			where paintName.Length > 0
			select paintName)
		{
			glovesSelectionMenu.AddMenuOption(item, onSelect);
		}
		_config.Additional.CommandGlove.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Gloves selection menu", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player) && _gBCommandsAllowed && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
						glovesSelectionMenu?.Open(player);
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	private void SetupAgentsMenu()
	{
		Action<CCSPlayerController?, ChatMenuOption> handleAgentSelection = (CCSPlayerController? player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player) && (object)player != null)
			{
				string selectedPaintName = option.Text;
				JObject selectedAgent = AgentsList.FirstOrDefault((JObject g) => g.ContainsKey("agent_name") && g["agent_name"] != null && g["agent_name"].ToString() == selectedPaintName && g["team"] != null && (int)g["team"] == player.TeamNum);
				if (selectedAgent != null && selectedAgent.ContainsKey("model"))
				{
					PlayerInfo playerInfo = new PlayerInfo
					{
						UserId = player.UserId,
						Slot = player.Slot,
						Index = (int)player.Index,
						SteamId = player.SteamID.ToString(),
						Name = player.PlayerName
					};
					string? ipAddress = player.IpAddress;
					playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
					PlayerInfo playerInfo2 = playerInfo;
					if (Config.Additional.ShowSkinImage)
					{
						string value = selectedAgent["image"]?.ToString() ?? "";
						_playerWeaponImage[player.Slot] = value;
						AddTimer(2f, () =>
						{
							_playerWeaponImage.Remove(player.Slot);
						}, TimerFlags.STOP_ON_MAPCHANGE);
					}
					if (!string.IsNullOrEmpty(Localizer["wp_agent_menu_select"]))
					{
						player.Print(Localizer["wp_agent_menu_select", new object[1] { selectedPaintName }]);
					}
					if (player.TeamNum == 3)
					{
						GPlayersAgent.AddOrUpdate(player.Slot, (int key) => ((string? CT, string? T))(CT: selectedAgent["model"].ToString().Equals("null") ? null : selectedAgent["model"].ToString(), T: null), (int key, (string? CT, string? T) oldValue) => (CT: selectedAgent["model"].ToString().Equals("null") ? null : selectedAgent["model"].ToString(), T: oldValue.T));
					}
					else
					{
						GPlayersAgent.AddOrUpdate(player.Slot, (int key) => ((string? CT, string? T))(CT: null, T: selectedAgent["model"].ToString().Equals("null") ? null : selectedAgent["model"].ToString()), (int key, (string? CT, string? T) oldValue) => (CT: oldValue.CT, T: selectedAgent["model"].ToString().Equals("null") ? null : selectedAgent["model"].ToString()));
					}
					if (WeaponSync != null)
					{
						Task.Run(async () =>
						{
							await WeaponSync.SyncAgentToDatabase(playerInfo2);
						});
					}
				}
			}
		};
		_config.Additional.CommandAgent.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Agents selection menu", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player) && _gBCommandsAllowed && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						IMenu menu = Utility.CreateMenu(Localizer["wp_agent_menu_title"]);
						if (menu != null)
						{
							menu.PostSelectAction = PostSelectAction.Close;
							IEnumerable<JObject> enumerable = AgentsList.Where((JObject agentObject) =>
							{
								int? num = agentObject["team"]?.Value<int>();
								if (num.HasValue)
								{
									int valueOrDefault = num.GetValueOrDefault();
									if (true)
									{
										return valueOrDefault == player.TeamNum;
									}
								}
								return false;
							});
							foreach (JObject item in enumerable)
							{
								string text = item["agent_name"]?.ToString() ?? "";
								if (text.Length > 0)
								{
									menu.AddMenuOption(text, handleAgentSelection);
								}
							}
							CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
							menu.Open(player);
						}
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	private void SetupMusicMenu()
	{
		IMenu musicSelectionMenu = Utility.CreateMenu(Localizer["wp_music_menu_title"]);
		if (musicSelectionMenu == null)
		{
			return;
		}
		musicSelectionMenu.PostSelectAction = PostSelectAction.Close;
		Action<CCSPlayerController, ChatMenuOption> onSelect = (CCSPlayerController? player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player) && (object)player != null)
			{
				string selectedPaintName = option.Text;
				ConcurrentDictionary<CsTeam, ushort> orAdd = GPlayersMusic.GetOrAdd(player.Slot, new ConcurrentDictionary<CsTeam, ushort>());
				CsTeam[] teamsToCheck = ((player.TeamNum >= 2) ? new CsTeam[1] { player.Team } : new CsTeam[2]
				{
					CsTeam.Terrorist,
					CsTeam.CounterTerrorist
				});
				JObject jObject = MusicList.FirstOrDefault((JObject g) => g.ContainsKey("name") && g["name"]?.ToString() == selectedPaintName);
				if (jObject != null)
				{
					if (jObject.ContainsKey("id") && jObject.ContainsKey("name") && int.TryParse(jObject["id"]?.ToString(), out var paint))
					{
						string value = jObject["image"]?.ToString() ?? "";
						if (Config.Additional.ShowSkinImage)
						{
							_playerWeaponImage[player.Slot] = value;
							AddTimer(2f, () =>
							{
								_playerWeaponImage.Remove(player.Slot);
							}, TimerFlags.STOP_ON_MAPCHANGE);
						}
						PlayerInfo playerInfo = new PlayerInfo
						{
							UserId = player.UserId,
							Slot = player.Slot,
							Index = (int)player.Index,
							SteamId = player.SteamID.ToString(),
							Name = player.PlayerName
						};
						string? ipAddress = player.IpAddress;
						playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
						PlayerInfo playerInfo2 = playerInfo;
						if (paint != 0)
						{
							CsTeam[] array = teamsToCheck;
							foreach (CsTeam key in array)
							{
								orAdd[key] = (ushort)paint;
							}
						}
						else
						{
							CsTeam[] array2 = teamsToCheck;
							foreach (CsTeam key2 in array2)
							{
								orAdd[key2] = 0;
							}
						}
						GivePlayerMusicKit(player);
						if (!string.IsNullOrEmpty(Localizer["wp_music_menu_select"]))
						{
							player.Print(Localizer["wp_music_menu_select", new object[1] { selectedPaintName }]);
						}
						if (WeaponSync != null)
						{
							Task.Run(async () =>
							{
								await WeaponSync.SyncMusicToDatabase(playerInfo2, (ushort)paint, teamsToCheck);
							});
						}
					}
				}
				else
				{
					PlayerInfo playerInfo3 = new PlayerInfo
					{
						UserId = player.UserId,
						Slot = player.Slot,
						Index = (int)player.Index,
						SteamId = player.SteamID.ToString(),
						Name = player.PlayerName
					};
					string? ipAddress2 = player.IpAddress;
					playerInfo3.IpAddress = ((ipAddress2 != null) ? ipAddress2.Split(":")[0] : null);
					PlayerInfo playerInfo4 = playerInfo3;
					CsTeam[] array3 = teamsToCheck;
					foreach (CsTeam key3 in array3)
					{
						orAdd[key3] = 0;
					}
					GivePlayerMusicKit(player);
					if (!string.IsNullOrEmpty(Localizer["wp_music_menu_select"]))
					{
						player.Print(Localizer["wp_music_menu_select", new object[1] { Localizer["None"] }]);
					}
					if (WeaponSync != null)
					{
						Task.Run(async () =>
						{
							await WeaponSync.SyncMusicToDatabase(playerInfo4, 0, teamsToCheck);
						});
					}
				}
			}
		};
		musicSelectionMenu.AddMenuOption(Localizer["None"], onSelect);
		foreach (string item in from musicObject in MusicList
			select musicObject["name"]?.ToString() ?? "" into paintName
			where paintName.Length > 0
			select paintName)
		{
			musicSelectionMenu.AddMenuOption(item, onSelect);
		}
		_config.Additional.CommandMusic.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Music selection menu", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player) && _gBCommandsAllowed && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
						musicSelectionMenu.Open(player);
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	private void SetupPinsMenu()
	{
		IMenu pinsSelectionMenu = Utility.CreateMenu(Localizer["wp_pins_menu_title"]);
		if (pinsSelectionMenu == null)
		{
			return;
		}
		pinsSelectionMenu.PostSelectAction = PostSelectAction.Close;
		Action<CCSPlayerController, ChatMenuOption> onSelect = (CCSPlayerController? player, ChatMenuOption option) =>
		{
			if (Utility.IsPlayerValid(player) && (object)player != null)
			{
				string selectedPaintName = option.Text;
				ConcurrentDictionary<CsTeam, ushort> orAdd = GPlayersPin.GetOrAdd(player.Slot, new ConcurrentDictionary<CsTeam, ushort>());
				CsTeam[] teamsToCheck = ((player.TeamNum >= 2) ? new CsTeam[1] { player.Team } : new CsTeam[2]
				{
					CsTeam.Terrorist,
					CsTeam.CounterTerrorist
				});
				JObject jObject = PinsList.FirstOrDefault((JObject g) => g.ContainsKey("name") && g["name"]?.ToString() == selectedPaintName);
				if (jObject != null)
				{
					if (jObject.ContainsKey("id") && jObject.ContainsKey("name") && int.TryParse(jObject["id"]?.ToString(), out var paint))
					{
						string value = jObject["image"]?.ToString() ?? "";
						if (Config.Additional.ShowSkinImage)
						{
							_playerWeaponImage[player.Slot] = value;
							AddTimer(2f, () =>
							{
								_playerWeaponImage.Remove(player.Slot);
							}, TimerFlags.STOP_ON_MAPCHANGE);
						}
						PlayerInfo playerInfo = new PlayerInfo
						{
							UserId = player.UserId,
							Slot = player.Slot,
							Index = (int)player.Index,
							SteamId = player.SteamID.ToString(),
							Name = player.PlayerName
						};
						string? ipAddress = player.IpAddress;
						playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
						PlayerInfo playerInfo2 = playerInfo;
						if (paint != 0)
						{
							CsTeam[] array = teamsToCheck;
							foreach (CsTeam key in array)
							{
								orAdd[key] = (ushort)paint;
							}
						}
						else
						{
							CsTeam[] array2 = teamsToCheck;
							foreach (CsTeam key2 in array2)
							{
								orAdd[key2] = 0;
							}
						}
						if (!string.IsNullOrEmpty(Localizer["wp_pins_menu_select"]))
						{
							player.Print(Localizer["wp_pins_menu_select", new object[1] { selectedPaintName }]);
						}
						GivePlayerPin(player);
						if (WeaponSync != null)
						{
							Task.Run(async () =>
							{
								await WeaponSync.SyncPinToDatabase(playerInfo2, (ushort)paint, teamsToCheck);
							});
						}
					}
				}
				else
				{
					PlayerInfo playerInfo3 = new PlayerInfo
					{
						UserId = player.UserId,
						Slot = player.Slot,
						Index = (int)player.Index,
						SteamId = player.SteamID.ToString(),
						Name = player.PlayerName
					};
					string? ipAddress2 = player.IpAddress;
					playerInfo3.IpAddress = ((ipAddress2 != null) ? ipAddress2.Split(":")[0] : null);
					PlayerInfo playerInfo4 = playerInfo3;
					CsTeam[] array3 = teamsToCheck;
					foreach (CsTeam key3 in array3)
					{
						orAdd[key3] = 0;
					}
					if (!string.IsNullOrEmpty(Localizer["wp_pins_menu_select"]))
					{
						player.Print(Localizer["wp_pins_menu_select", new object[1] { Localizer["None"] }]);
					}
					GivePlayerPin(player);
					if (WeaponSync != null)
					{
						Task.Run(async () =>
						{
							await WeaponSync.SyncPinToDatabase(playerInfo4, 0, teamsToCheck);
						});
					}
				}
			}
		};
		pinsSelectionMenu.AddMenuOption(Localizer["None"], onSelect);
		foreach (string item in from musicObject in PinsList
			select musicObject["name"]?.ToString() ?? "" into paintName
			where paintName.Length > 0
			select paintName)
		{
			pinsSelectionMenu.AddMenuOption(item, onSelect);
		}
		_config.Additional.CommandPin.ForEach((string c) =>
		{
			AddCommand("css_" + c, "Pin selection menu", (CCSPlayerController? player, CommandInfo info) =>
			{
				if (Utility.IsPlayerValid(player) && _gBCommandsAllowed && !(player == null) && player.UserId.HasValue)
				{
					if (!CommandsCooldown.TryGetValue(player.Slot, out var value) || DateTime.UtcNow >= (CommandsCooldown.TryGetValue(player.Slot, out value) ? value : DateTime.UtcNow))
					{
						CommandsCooldown[player.Slot] = DateTime.UtcNow.AddSeconds(Config.CmdRefreshCooldownSeconds);
						pinsSelectionMenu.Open(player);
					}
					else if (!string.IsNullOrEmpty(Localizer["wp_command_cooldown"]))
					{
						player.Print(Localizer["wp_command_cooldown"]);
					}
				}
			});
		});
	}

	[GameEventHandler(HookMode.Post)]
	public HookResult OnClientFullConnect(EventPlayerConnectFull @event, GameEventInfo info)
	{
		CCSPlayerController userid = @event.Userid;
		if ((object)userid == null || !userid.IsValid || userid.IsBot || WeaponSync == null || Database == null)
		{
			return HookResult.Continue;
		}
		PlayerInfo playerInfo = new PlayerInfo
		{
			UserId = userid.UserId,
			Slot = userid.Slot,
			Index = (int)userid.Index,
			SteamId = userid.SteamID.ToString(),
			Name = userid.PlayerName
		};
		string? ipAddress = userid.IpAddress;
		playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
		PlayerInfo playerInfo2 = playerInfo;
		try
		{
			Task.Run(async () =>
			{
				await WeaponSync.GetPlayerData(playerInfo2);
				Server.NextFrame(() =>
				{
					var p = Utilities.GetPlayerFromSlot(playerInfo2.Slot);
					if (p != null && p.IsValid && p.PawnIsAlive)
					{
						RefreshWeapons(p, force: true);
					}
				});
			});
		}
		catch
		{
		}
		Players.Add(userid);
		return HookResult.Continue;
	}

	[GameEventHandler(HookMode.Post)]
	public HookResult OnPlayerDisconnect(EventPlayerDisconnect @event, GameEventInfo info)
	{
		CCSPlayerController player = @event.Userid;
		if ((object)player == null || !player.IsValid || player.IsBot)
		{
			return HookResult.Continue;
		}
		PlayerInfo playerInfo = new PlayerInfo
		{
			UserId = player.UserId,
			Slot = player.Slot,
			Index = (int)player.Index,
			SteamId = player.SteamID.ToString(),
			Name = player.PlayerName
		};
		string? ipAddress = player.IpAddress;
		playerInfo.IpAddress = ((ipAddress != null) ? ipAddress.Split(":")[0] : null);
		PlayerInfo playerInfo2 = playerInfo;
		Task.Run(async () =>
		{
			if (WeaponSync != null)
			{
				await WeaponSync.SyncStatTrakToDatabase(playerInfo2);
			}
			if (Config.Additional.SkinEnabled)
			{
				GPlayerWeaponsInfo.TryRemove(player.Slot, out ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> _);
			}
		});
		if (Config.Additional.KnifeEnabled)
		{
			GPlayersKnife.TryRemove(player.Slot, out ConcurrentDictionary<CsTeam, string> _);
		}
		ConcurrentDictionary<CsTeam, ushort> value2;
		if (Config.Additional.GloveEnabled)
		{
			GPlayersGlove.TryRemove(player.Slot, out value2);
		}
		if (Config.Additional.AgentEnabled)
		{
			GPlayersAgent.TryRemove(player.Slot, out (string, string) _);
		}
		if (Config.Additional.MusicEnabled)
		{
			GPlayersMusic.TryRemove(player.Slot, out value2);
		}
		if (Config.Additional.PinsEnabled)
		{
			GPlayersPin.TryRemove(player.Slot, out value2);
		}
		_temporaryPlayerWeaponWear.TryRemove(player.Slot, out ConcurrentDictionary<int, float> _);
		CommandsCooldown.Remove(player.Slot);
		Players.Remove(player);
		return HookResult.Continue;
	}

	private void OnMapStart(string mapName)
	{
		_fadeSeed = 0;
		_nextItemId = 65578uL;
	}

	private HookResult OnPlayerSpawn(EventPlayerSpawn @event, GameEventInfo info)
	{
		CCSPlayerController player = @event.Userid;
		if ((object)player != null && player.IsValid && !player.IsBot)
		{
			Server.NextFrame(() =>
			{
				if (player != null && player.IsValid && player.PawnIsAlive)
				{
					RefreshWeapons(player, force: true);
				}
			});
		}
		return HookResult.Continue;
	}

	private HookResult OnRoundEnd(EventRoundEnd @event, GameEventInfo info)
	{
		_gBCommandsAllowed = false;
		return HookResult.Continue;
	}

	private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
	{
		_gBCommandsAllowed = true;
		_mvpPlayed = false;
		return HookResult.Continue;
	}

	private HookResult OnRoundMvp(EventRoundMvp @event, GameEventInfo info)
	{
		if (_mvpPlayed)
		{
			return HookResult.Continue;
		}
		CCSPlayerController userid = @event.Userid;
		if (userid == null || !userid.IsValid || userid.IsBot)
		{
			return HookResult.Continue;
		}
		if (!GPlayersMusic.TryGetValue(userid.Slot, out ConcurrentDictionary<CsTeam, ushort> value) || !value.TryGetValue(userid.Team, out var value2) || value2 == 0)
		{
			return HookResult.Continue;
		}
		@event.Musickitid = value2;
		@event.Nomusic = 0;
		info.DontBroadcast = true;
		EventRoundMvp eventRoundMvp = new EventRoundMvp(force: true)
		{
			Userid = userid,
			Musickitid = value2,
			Nomusic = 0
		};
		_mvpPlayed = true;
		eventRoundMvp.FireEvent(dontBroadcast: false);
		return HookResult.Continue;
	}

	private HookResult OnGiveNamedItemPost(DynamicHook hook)
	{
		try
		{
			CCSPlayer_ItemServices param = hook.GetParam<CCSPlayer_ItemServices>(0);
			CBasePlayerWeapon cBasePlayerWeapon = hook.GetReturn<CBasePlayerWeapon>();
			if (param == null || cBasePlayerWeapon == null || !cBasePlayerWeapon.IsValid)
			{
				goto IL_0046;
			}
			string designerName = cBasePlayerWeapon.DesignerName;
			if (designerName == null || !designerName.Contains("weapon"))
			{
				goto IL_0046;
			}
			CCSPlayerController playerFromItemServices = GetPlayerFromItemServices(param);
			if (playerFromItemServices != null)
			{
				GivePlayerWeaponSkin(playerFromItemServices, cBasePlayerWeapon);
			}
			goto end_IL_0001;
			IL_0046:
			return HookResult.Continue;
			end_IL_0001:;
		}
		catch
		{
		}
		return HookResult.Continue;
	}

	private void OnEntityCreated(CEntityInstance entity)
	{
		string designerName = entity.DesignerName;
		if (designerName == null || !designerName.Contains("weapon"))
		{
			return;
		}
		Server.NextWorldUpdate(() =>
		{
			CBasePlayerWeapon cBasePlayerWeapon = new CBasePlayerWeapon(entity.Handle);
			if (!cBasePlayerWeapon.IsValid)
			{
				return;
			}
			try
			{
				SteamID steamid = null;
				if (cBasePlayerWeapon.OriginalOwnerXuidLow != 0)
				{
					steamid = new SteamID(cBasePlayerWeapon.OriginalOwnerXuidLow);
				}
				CCSPlayerController cCSPlayerController;
				if (steamid != null && steamid.IsValid())
				{
					cCSPlayerController = Players.FirstOrDefault((CCSPlayerController p) => p.IsValid && p.SteamID == steamid.SteamId64);
					if (cCSPlayerController == null)
					{
						cCSPlayerController = Utilities.GetPlayerFromSteamId(cBasePlayerWeapon.OriginalOwnerXuidLow);
					}
				}
				else
				{
					CCSPlayerPawn cCSPlayerPawn = cBasePlayerWeapon.OwnerEntity.Value?.As<CCSPlayerPawn>();
					cCSPlayerController = (((object)cCSPlayerPawn == null || !cCSPlayerPawn.IsValid) ? null : cCSPlayerPawn.Controller.Value?.As<CCSPlayerController>());
				}
				if (!string.IsNullOrEmpty(cCSPlayerController?.PlayerName) && Utility.IsPlayerValid(cCSPlayerController))
				{
					GivePlayerWeaponSkin(cCSPlayerController, cBasePlayerWeapon);
				}
			}
			catch (Exception)
			{
			}
		});
	}

	private void OnTick()
	{
		if (!Config.Additional.ShowSkinImage)
		{
			return;
		}
		foreach (CCSPlayerController player in Players)
		{
			if (_playerWeaponImage.TryGetValue(player.Slot, out string value) && !string.IsNullOrEmpty(value))
			{
				player.PrintToCenterHtml("<img src='{PATH}'</img>".Replace("{PATH}", value));
			}
		}
	}

	[GameEventHandler(HookMode.Post)]
	public HookResult OnItemPickup(EventItemPickup @event, GameEventInfo _)
	{
		CCSPlayerController userid = @event.Userid;
		if (userid == null || !userid.IsValid || userid.IsBot)
		{
			return HookResult.Continue;
		}
		if (!@event.Item.Contains("knife"))
		{
			return HookResult.Continue;
		}
		int weaponDefIndex = (int)@event.Defindex;
		if (!HasChangedKnife(userid, out string _) || !HasChangedPaint(userid, weaponDefIndex, out WeaponInfo _))
		{
			return HookResult.Continue;
		}
		if ((object)userid != null && userid.Connected == PlayerConnectedState.Connected && userid.PawnIsAlive)
		{
			CHandle<CCSPlayerPawn> playerPawn = userid.PlayerPawn;
			if (playerPawn != null && playerPawn.IsValid)
			{
				GiveOnItemPickup(userid);
			}
		}
		return HookResult.Continue;
	}

	private HookResult OnPlayerDeath(EventPlayerDeath @event, GameEventInfo info)
	{
		CCSPlayerController attacker = @event.Attacker;
		CCSPlayerController userid = @event.Userid;
		if ((object)attacker == null || !attacker.IsValid)
		{
			return HookResult.Continue;
		}
		if (userid == null || !userid.IsValid || userid == attacker)
		{
			return HookResult.Continue;
		}
		CBasePlayerWeapon cBasePlayerWeapon = attacker.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value;
		if (cBasePlayerWeapon == null)
		{
			return HookResult.Continue;
		}
		int itemDefinitionIndex = cBasePlayerWeapon.AttributeManager.Item.ItemDefinitionIndex;
		if (!HasChangedPaint(attacker, itemDefinitionIndex, out WeaponInfo weaponInfo) || weaponInfo == null)
		{
			return HookResult.Continue;
		}
		if (!weaponInfo.StatTrak)
		{
			return HookResult.Continue;
		}
		weaponInfo.StatTrakCount++;
		CAttributeListSetOrAddAttributeValueByName.Invoke(cBasePlayerWeapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "kill eater", ViewAsFloat((uint)weaponInfo.StatTrakCount));
		CAttributeListSetOrAddAttributeValueByName.Invoke(cBasePlayerWeapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "kill eater score type", 0f);
		CAttributeListSetOrAddAttributeValueByName.Invoke(cBasePlayerWeapon.AttributeManager.Item.AttributeList.Handle, "kill eater", ViewAsFloat((uint)weaponInfo.StatTrakCount));
		CAttributeListSetOrAddAttributeValueByName.Invoke(cBasePlayerWeapon.AttributeManager.Item.AttributeList.Handle, "kill eater score type", 0f);
		return HookResult.Continue;
	}

	private void RegisterListeners()
	{
		RegisterListener<Listeners.OnMapStart>(OnMapStart);
		RegisterEventHandler<EventPlayerSpawn>(OnPlayerSpawn);
		RegisterEventHandler<EventRoundStart>(OnRoundStart);
		RegisterEventHandler<EventRoundEnd>(OnRoundEnd);
		RegisterEventHandler<EventRoundMvp>(OnRoundMvp);
		RegisterListener<Listeners.OnEntitySpawned>(OnEntityCreated);
		RegisterEventHandler<EventPlayerDeath>(OnPlayerDeath);
		if (Config.Additional.ShowSkinImage)
		{
			RegisterListener<Listeners.OnTick>(OnTick);
		}
		VirtualFunctions.GiveNamedItemFunc.Hook(OnGiveNamedItemPost, HookMode.Post);
		_giveNamedItemHooked = true;
	}

	private void GivePlayerWeaponSkin(CCSPlayerController player, CBasePlayerWeapon weapon)
	{
		if (!Config.Additional.SkinEnabled || !GPlayerWeaponsInfo.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> _))
		{
			return;
		}
		string text = weapon.DesignerName ?? "";
		if (text.Contains("knife") || text.Contains("bayonet"))
		{
			if (!HasChangedKnife(player, out string _))
			{
				return;
			}
			KeyValuePair<int, string> keyValuePair = WeaponDefindex.FirstOrDefault((KeyValuePair<int, string> x) => x.Value == GPlayersKnife[player.Slot][player.Team]);
			if (keyValuePair.Key == 0)
			{
				return;
			}
			if (weapon.AttributeManager.Item.ItemDefinitionIndex != keyValuePair.Key)
			{
				SubclassChange(weapon, (ushort)keyValuePair.Key);
			}
			weapon.AttributeManager.Item.ItemDefinitionIndex = (ushort)keyValuePair.Key;
			weapon.AttributeManager.Item.EntityQuality = 3;
			weapon.AttributeManager.Item.AttributeList.Attributes.RemoveAll();
			weapon.AttributeManager.Item.NetworkedDynamicAttributes.Attributes.RemoveAll();
		}
		else
		{
			weapon.AttributeManager.Item.EntityQuality = 0;
		}
		UpdatePlayerEconItemId(weapon.AttributeManager.Item);
		int weaponDefIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
		weapon.AttributeManager.Item.AccountID = (uint)player.SteamID;
		int fallbackPaintKit;
		if (_config.Additional.GiveRandomSkin && !HasChangedPaint(player, weaponDefIndex, out WeaponInfo _))
		{
			weapon.FallbackPaintKit = GetRandomPaint(weaponDefIndex);
			weapon.FallbackSeed = 0;
			weapon.FallbackWear = 0.01f;
			weapon.AttributeManager.Item.NetworkedDynamicAttributes.Attributes.RemoveAll();
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "set item texture prefab", GetRandomPaint(weaponDefIndex));
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "set item texture seed", 0f);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "set item texture wear", 0.01f);
			weapon.AttributeManager.Item.AttributeList.Attributes.RemoveAll();
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.AttributeList.Handle, "set item texture prefab", GetRandomPaint(weaponDefIndex));
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.AttributeList.Handle, "set item texture seed", 0f);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.AttributeList.Handle, "set item texture wear", 0.01f);
			fallbackPaintKit = weapon.FallbackPaintKit;
			if (fallbackPaintKit == 0)
			{
				return;
			}
			List<JObject> list = SkinsList.Where((JObject w) =>
			{
				JToken? jToken = w["weapon_defindex"];
				int result;
				if (jToken != null && jToken.ToObject<int>() == weaponDefIndex)
				{
					JToken? jToken2 = w["paint"];
					result = ((jToken2 != null && jToken2.ToObject<int>() == fallbackPaintKit) ? 1 : 0);
				}
				else
				{
					result = 0;
				}
				return (byte)result != 0;
			}).ToList();
			bool isLegacy = list.Count <= 0 || list[0].Value<bool>("legacy_model");
			UpdatePlayerWeaponMeshGroupMask(player, weapon, isLegacy);
		}
		else
		{
			if (!HasChangedPaint(player, weaponDefIndex, out WeaponInfo weaponInfo2) || weaponInfo2 == null)
			{
				return;
			}
			weapon.AttributeManager.Item.AttributeList.Attributes.RemoveAll();
			weapon.AttributeManager.Item.NetworkedDynamicAttributes.Attributes.RemoveAll();
			UpdatePlayerEconItemId(weapon.AttributeManager.Item);
			weapon.AttributeManager.Item.CustomName = weaponInfo2.Nametag;
			weapon.FallbackPaintKit = weaponInfo2.Paint;
			weapon.FallbackSeed = ((weaponInfo2 != null && weaponInfo2.Paint == 38 && weaponInfo2.Seed == 0) ? _fadeSeed++ : weaponInfo2.Seed);
			weapon.FallbackWear = weaponInfo2.Wear;
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "set item texture prefab", weapon.FallbackPaintKit);
			if (weaponInfo2.StatTrak)
			{
				weapon.AttributeManager.Item.EntityQuality = 9;
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "kill eater", ViewAsFloat((uint)weaponInfo2.StatTrakCount));
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "kill eater score type", 0f);
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.AttributeList.Handle, "kill eater", ViewAsFloat((uint)weaponInfo2.StatTrakCount));
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.AttributeList.Handle, "kill eater score type", 0f);
			}
			fallbackPaintKit = weapon.FallbackPaintKit;
			if (fallbackPaintKit == 0)
			{
				return;
			}
			if (weaponInfo2.KeyChain != null)
			{
				SetKeychain(player, weapon);
			}
			if (weaponInfo2.Stickers.Count > 0)
			{
				SetStickers(player, weapon);
			}
			List<JObject> list = SkinsList.Where((JObject w) =>
			{
				JToken? jToken = w["weapon_defindex"];
				int result;
				if (jToken != null && jToken.ToObject<int>() == weaponDefIndex)
				{
					JToken? jToken2 = w["paint"];
					result = ((jToken2 != null && jToken2.ToObject<int>() == fallbackPaintKit) ? 1 : 0);
				}
				else
				{
					result = 0;
				}
				return (byte)result != 0;
			}).ToList();
			bool isLegacy = list.Count <= 0 || list[0].Value<bool>("legacy_model");
			UpdatePlayerWeaponMeshGroupMask(player, weapon, isLegacy);
		}
	}

	private void IncrementWearForWeaponWithStickers(CCSPlayerController player, CBasePlayerWeapon weapon)
	{
		int itemDefinitionIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
		if (HasChangedPaint(player, itemDefinitionIndex, out WeaponInfo weaponInfo) && weaponInfo != null && weaponInfo.Stickers.Count > 0)
		{
			float wearIncrement = 0.001f;
			float wear = weaponInfo.Wear;
			ConcurrentDictionary<int, float> orAdd = _temporaryPlayerWeaponWear.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<int, float>());
			float num = orAdd.AddOrUpdate(itemDefinitionIndex, wear + wearIncrement, (int _, float oldWear) => Math.Min(oldWear + wearIncrement, 1f));
			weapon.FallbackWear = num;
		}
	}

	private void SetStickers(CCSPlayerController? player, CBasePlayerWeapon weapon)
	{
		if (player == null || !player.IsValid)
		{
			return;
		}
		int itemDefinitionIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
		if (!HasChangedPaint(player, itemDefinitionIndex, out WeaponInfo weaponInfo) || weaponInfo == null)
		{
			return;
		}
		foreach (StickerInfo sticker in weaponInfo.Stickers)
		{
			int value = weaponInfo.Stickers.IndexOf(sticker);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} id", ViewAsFloat(sticker.Id));
			if (sticker.OffsetX != 0f || sticker.OffsetY != 0f)
			{
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} schema", 0f);
			}
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} offset x", sticker.OffsetX);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} offset y", sticker.OffsetY);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} wear", sticker.Wear);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} scale", sticker.Scale);
			CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, $"sticker slot {value} rotation", sticker.Rotation);
		}
		if (_temporaryPlayerWeaponWear.TryGetValue(player.Slot, out ConcurrentDictionary<int, float> value2) && value2.TryGetValue(itemDefinitionIndex, out var value3))
		{
			weapon.FallbackWear = value3;
		}
	}

	private void SetKeychain(CCSPlayerController? player, CBasePlayerWeapon weapon)
	{
		if (!(player == null) && player.IsValid)
		{
			int itemDefinitionIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
			if (HasChangedPaint(player, itemDefinitionIndex, out WeaponInfo weaponInfo) && weaponInfo?.KeyChain != null)
			{
				KeyChainInfo keyChain = weaponInfo.KeyChain;
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "keychain slot 0 id", ViewAsFloat(keyChain.Id));
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "keychain slot 0 offset x", keyChain.OffsetX);
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "keychain slot 0 offset y", keyChain.OffsetY);
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "keychain slot 0 offset z", keyChain.OffsetZ);
				CAttributeListSetOrAddAttributeValueByName.Invoke(weapon.AttributeManager.Item.NetworkedDynamicAttributes.Handle, "keychain slot 0 seed", ViewAsFloat(keyChain.Seed));
			}
		}
	}

	private static void GiveKnifeToPlayer(CCSPlayerController? player)
	{
		if (_config.Additional.KnifeEnabled && !(player == null) && player.IsValid && !PlayerHasKnife(player))
		{
			player.GiveNamedItem(CsItem.DefaultKnifeCT);
			Utilities.SetStateChanged(player, "CCSPlayerController", "m_pInventoryServices");
		}
	}

	private static bool PlayerHasKnife(CCSPlayerController? player)
	{
		if (!_config.Additional.KnifeEnabled)
		{
			return false;
		}
		if (player == null || !player.IsValid || !player.PlayerPawn.IsValid)
		{
			return false;
		}
		if (player.PlayerPawn.Value == null || player.PlayerPawn.Value.WeaponServices == null || player.PlayerPawn.Value.ItemServices == null)
		{
			return false;
		}
		NetworkedVector<CHandle<CBasePlayerWeapon>> networkedVector = player.PlayerPawn.Value.WeaponServices?.MyWeapons;
		if (networkedVector == null)
		{
			return false;
		}
		foreach (CHandle<CBasePlayerWeapon> item in networkedVector)
		{
			if (!item.IsValid || item.Value == null || !item.Value.IsValid || (!item.Value.DesignerName.Contains("knife") && !item.Value.DesignerName.Contains("bayonet")))
			{
				continue;
			}
			return true;
		}
		return false;
	}

	private bool WeaponNeedsRefresh(CCSPlayerController player, CBasePlayerWeapon weapon, out int targetDefIndex, out int targetPaint)
	{
		targetDefIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
		targetPaint = weapon.FallbackPaintKit;

		string designerName = weapon.DesignerName ?? "";
		bool isKnife = designerName.Contains("knife") || designerName.Contains("bayonet");

		if (isKnife)
		{
			if (HasChangedKnife(player, out string _))
			{
				var targetKnife = WeaponDefindex.FirstOrDefault(x => x.Value == GPlayersKnife[player.Slot][player.Team]);
				if (targetKnife.Key != 0)
				{
					targetDefIndex = targetKnife.Key;
				}
			}
			else
			{
				targetDefIndex = (player.Team == CsTeam.Terrorist) ? 59 : 42;
			}

			if (HasChangedPaint(player, targetDefIndex, out WeaponInfo? weaponInfo) && weaponInfo != null)
			{
				targetPaint = weaponInfo.Paint;
			}
			else
			{
				targetPaint = 0;
			}

			if (weapon.AttributeManager.Item.ItemDefinitionIndex != targetDefIndex ||
			    weapon.FallbackPaintKit != targetPaint ||
			    (weaponInfo != null && Math.Abs(weapon.FallbackWear - weaponInfo.Wear) > 0.0001f))
			{
				return true;
			}

			return false;
		}
		else
		{
			int defIndex = weapon.AttributeManager.Item.ItemDefinitionIndex;
			if (HasChangedPaint(player, defIndex, out WeaponInfo? weaponInfo) && weaponInfo != null)
			{
				targetPaint = weaponInfo.Paint;
			}
			else
			{
				targetPaint = 0;
			}

			if (weapon.FallbackPaintKit != targetPaint ||
			    (weaponInfo != null && Math.Abs(weapon.FallbackWear - weaponInfo.Wear) > 0.0001f))
			{
				return true;
			}

			return false;
		}
	}

	private void RefreshWeapons(CCSPlayerController? player, bool force = false)
	{
		if ((!force && !_gBCommandsAllowed) || player == null || !player.IsValid || player.IsBot || player.PlayerPawn.Value == null || player.LifeState != 0 || player.PlayerPawn.Value.WeaponServices == null)
		{
			return;
		}

		GivePlayerMusicKit(player);
		GivePlayerAgent(player);
		GivePlayerGloves(player);
		GivePlayerPin(player);

		var pawn = player.PlayerPawn.Value;
		if (pawn == null || !pawn.IsValid || pawn.WeaponServices == null)
		{
			return;
		}

		NetworkedVector<CHandle<CBasePlayerWeapon>> myWeapons = pawn.WeaponServices.MyWeapons;
		if (myWeapons == null || myWeapons.Count == 0)
		{
			return;
		}
		CsTeam team = player.Team;
		if (team <= CsTeam.Spectator)
		{
			return;
		}

		int activeSlot = 3;
		try
		{
			var activeWeapon = pawn.WeaponServices?.ActiveWeapon.Value;
			if (activeWeapon != null && activeWeapon.IsValid)
			{
				string activeName = activeWeapon.DesignerName ?? "";
				if (activeName.Contains("knife") || activeName.Contains("bayonet"))
				{
					activeSlot = 3;
				}
				else if (activeName.Contains("c4"))
				{
					activeSlot = 5;
				}
				else if (activeName.Contains("grenade") || activeName.Contains("molotov") || activeName.Contains("flashbang") || activeName.Contains("decoy"))
				{
					activeSlot = 4;
				}
				else if (activeName.Contains("deagle") || activeName.Contains("glock") || activeName.Contains("usp") || activeName.Contains("p2000") || activeName.Contains("p250") || activeName.Contains("fiveseven") || activeName.Contains("cz75") || activeName.Contains("tec9") || activeName.Contains("revolver") || activeName.Contains("elite"))
				{
					activeSlot = 2;
				}
				else
				{
					activeSlot = 1;
				}
			}
		}
		catch { }

		bool hadKnife = false;
		bool refreshKnife = false;
		var weaponsToRefresh = new List<(string DesignerName, int Clip1, int ReserveAmmo)>();
		var weaponsToRemove = new List<CBasePlayerWeapon>();

		foreach (CHandle<CBasePlayerWeapon> item in myWeapons)
		{
			if (!item.IsValid || item.Value == null || !item.Value.IsValid)
			{
				continue;
			}
			CBasePlayerWeapon weapon = item.Value;
			string designerName = weapon.DesignerName ?? "";
			if (!designerName.Contains("weapon_"))
			{
				continue;
			}

			try
			{
				bool isKnife = designerName.Contains("knife") || designerName.Contains("bayonet");
				if (isKnife)
				{
					hadKnife = true;
					if (WeaponNeedsRefresh(player, weapon, out _, out _))
					{
						refreshKnife = true;
						weaponsToRemove.Add(weapon);
					}
				}
				else if (WeaponDefindex.ContainsKey(weapon.AttributeManager.Item.ItemDefinitionIndex))
				{
					if (WeaponNeedsRefresh(player, weapon, out _, out _))
					{
						weaponsToRefresh.Add((designerName, weapon.Clip1, weapon.ReserveAmmo[0]));
						weaponsToRemove.Add(weapon);
					}
				}
			}
			catch (Exception ex)
			{
				Logger.LogWarning("[WeaponPaints] Error checking weapon for refresh: " + ex.Message);
			}
		}

		if (!hadKnife && !PlayerHasKnife(player))
		{
			GiveKnifeToPlayer(player);
		}

		if (weaponsToRemove.Count == 0)
		{
			return;
		}

		// Cleanly remove from player inventory and delete entities
		foreach (var wep in weaponsToRemove)
		{
			try
			{
				if (wep.IsValid)
				{
					pawn.RemovePlayerItem(wep);
					wep.Remove();
				}
			}
			catch (Exception ex)
			{
				Logger.LogWarning("[WeaponPaints] Error removing weapon for refresh: " + ex.Message);
			}
		}

		AddTimer(0.15f, () =>
		{
			try
			{
				if (player == null || !player.IsValid || !player.PawnIsAlive || player.PlayerPawn.Value == null)
				{
					return;
				}

				var curPawn = player.PlayerPawn.Value;
				if (curPawn.WeaponServices == null)
				{
					return;
				}

				if (refreshKnife)
				{
					var knifeItem = (player.Team == CsTeam.Terrorist) ? CsItem.DefaultKnifeT : CsItem.DefaultKnifeCT;
					player.GiveNamedItem(knifeItem);
				}

				foreach (var gun in weaponsToRefresh)
				{
					var newGunHandle = player.GiveNamedItem(gun.DesignerName);
					if (newGunHandle != IntPtr.Zero)
					{
						var newGun = new CBasePlayerWeapon(newGunHandle);
						if (newGun.IsValid)
						{
							newGun.Clip1 = gun.Clip1;
							newGun.ReserveAmmo[0] = gun.ReserveAmmo;
							IncrementWearForWeaponWithStickers(player, newGun);
						}
					}
				}

				player.ExecuteClientCommand($"slot{activeSlot}");
			}
			catch (Exception ex)
			{
				Logger.LogWarning("[WeaponPaints] Error re-giving refreshed weapons: " + ex.Message);
			}
		}, TimerFlags.STOP_ON_MAPCHANGE);
	}

	private void GivePlayerGloves(CCSPlayerController player)
	{
		if (!Utility.IsPlayerValid(player) || player.LifeState != 0)
		{
			return;
		}
		CCSPlayerPawn pawn = player.PlayerPawn.Value;
		if (pawn == null || !pawn.IsValid)
		{
			return;
		}
		CEconItemView item = pawn.EconGloves;
		item.NetworkedDynamicAttributes.Attributes.RemoveAll();
		item.AttributeList.Attributes.RemoveAll();
		player.ExecuteClientCommand("lastinv");
		Instance.AddTimer(0.08f, () =>
		{
			try
			{
				if (player.IsValid && player.PawnIsAlive && pawn.IsValid && GPlayersGlove.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ushort> value) && value.TryGetValue(player.Team, out var value2) && value2 != 0 && HasChangedPaint(player, value2, out WeaponInfo weaponInfo) && weaponInfo != null)
				{
					item.ItemDefinitionIndex = value2;
					UpdatePlayerEconItemId(item);
					item.NetworkedDynamicAttributes.Attributes.RemoveAll();
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.NetworkedDynamicAttributes.Handle, "set item texture prefab", weaponInfo.Paint);
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.NetworkedDynamicAttributes.Handle, "set item texture seed", weaponInfo.Seed);
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.NetworkedDynamicAttributes.Handle, "set item texture wear", weaponInfo.Wear);
					item.AttributeList.Attributes.RemoveAll();
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.AttributeList.Handle, "set item texture prefab", weaponInfo.Paint);
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.AttributeList.Handle, "set item texture seed", weaponInfo.Seed);
					CAttributeListSetOrAddAttributeValueByName.Invoke(item.AttributeList.Handle, "set item texture wear", weaponInfo.Wear);
					item.Initialized = true;
					player.ExecuteClientCommand("lastinv");
					SetBodygroup(pawn, "first_or_third_person", 0);
					AddTimer(0.2f, () =>
					{
						if (pawn.IsValid)
						{
							SetBodygroup(pawn, "first_or_third_person", 1);
						}
					}, TimerFlags.STOP_ON_MAPCHANGE);
				}
			}
			catch (Exception)
			{
			}
		}, TimerFlags.STOP_ON_MAPCHANGE);
	}

	private static int GetRandomPaint(int defindex)
	{
		if (SkinsList.Count == 0)
		{
			return 0;
		}
		Random random = new Random();
		List<JObject> list = SkinsList.Where((JObject w) => w["weapon_defindex"]?.ToString() == defindex.ToString()).ToList();
		if (list.Count == 0)
		{
			return 0;
		}
		JObject jObject = list[random.Next(list.Count)];
		int result;
		return int.TryParse(jObject["paint"]?.ToString(), out result) ? result : 0;
	}

	public static void SubclassChange(CBasePlayerWeapon weapon, ushort itemD)
	{
		weapon.AcceptInput("ChangeSubclass", null, null, itemD.ToString());
	}

	public static void SetBodygroup(CCSPlayerPawn pawn, string group, int value)
	{
		pawn.AcceptInput("SetBodygroup", null, null, $"{group},{value}");
	}

	private void UpdateWeaponMeshGroupMask(CBaseEntity weapon, bool isLegacy = false)
	{
		if (weapon.CBodyComponent?.SceneNode != null)
		{
			weapon.AcceptInput("SetBodygroup", null, null, $"body,{(isLegacy ? 1 : 0)}");
		}
	}

	private void UpdatePlayerWeaponMeshGroupMask(CCSPlayerController player, CBasePlayerWeapon weapon, bool isLegacy)
	{
		UpdateWeaponMeshGroupMask(weapon, isLegacy);
	}

	private static void GivePlayerAgent(CCSPlayerController player)
	{
		if (!GPlayersAgent.TryGetValue(player.Slot, out (string, string) value))
		{
			return;
		}
		string text;
		if (player.TeamNum == 3)
		{
			(text, _) = value;
		}
		else
		{
			text = value.Item2;
		}
		string model = text;
		if (string.IsNullOrEmpty(model) || player.PlayerPawn.Value == null)
		{
			return;
		}
		try
		{
			Server.NextFrame(() =>
			{
				if (player.IsValid)
				{
					CCSPlayerPawn value2 = player.PlayerPawn.Value;
					if (!(value2 == null) && value2.IsValid)
					{
						value2.SetModel("agents/models/" + model + ".vmdl");
					}
				}
			});
		}
		catch (Exception)
		{
		}
	}

	private static void GivePlayerMusicKit(CCSPlayerController player)
	{
		if (!player.IsBot && GPlayersMusic.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ushort> value) && value.TryGetValue(player.Team, out var value2) && value2 != 0 && player.InventoryServices != null)
		{
			player.MusicKitID = value2;
			player.InventoryServices.MusicID = value2;
			Utilities.SetStateChanged(player, "CCSPlayerController", "m_iMusicKitID");
			Utilities.SetStateChanged(player, "CCSPlayerController", "m_pInventoryServices");
		}
	}

	private static void GivePlayerPin(CCSPlayerController player)
	{
		if (GPlayersPin.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ushort> value) && value.TryGetValue(player.Team, out var value2) && player.InventoryServices != null)
		{
			player.InventoryServices.Rank[5] = (MedalRank_t)((value2 > 0) ? value2 : 0);
			Utilities.SetStateChanged(player, "CCSPlayerController", "m_pInventoryServices");
		}
	}

	private void GiveOnItemPickup(CCSPlayerController player)
	{
		CCSPlayerPawn value = player.PlayerPawn.Value;
		if (value == null)
		{
			return;
		}
		NetworkedVector<CHandle<CBasePlayerWeapon>> networkedVector = value.WeaponServices?.MyWeapons;
		if (networkedVector == null)
		{
			return;
		}
		foreach (CHandle<CBasePlayerWeapon> item in networkedVector)
		{
			CBasePlayerWeapon value2 = item.Value;
			if (value2 != null && value2.IsValid)
			{
				GivePlayerWeaponSkin(player, value2);
			}
		}
	}

	private void UpdatePlayerEconItemId(CEconItemView econItemView)
	{
		ulong num = _nextItemId++;
		econItemView.ItemID = num;
		econItemView.ItemIDLow = (uint)((int)num & -1);
		econItemView.ItemIDHigh = (uint)num;
	}

	private static CCSPlayerController? GetPlayerFromItemServices(CCSPlayer_ItemServices itemServices)
	{
		CBasePlayerPawn value = itemServices.Pawn.Value;
		if (value == null || !value.IsValid || !value.Controller.IsValid || value.Controller.Value == null)
		{
			return null;
		}
		CCSPlayerController cCSPlayerController = new CCSPlayerController(value.Controller.Value.Handle);
		return (!Utility.IsPlayerValid(cCSPlayerController)) ? null : cCSPlayerController;
	}

	private static bool HasChangedKnife(CCSPlayerController player, out string? knifeValue)
	{
		knifeValue = null;
		if (!GPlayersKnife.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, string> value) || !value.TryGetValue(player.Team, out var value2) || value2 == "weapon_knife")
		{
			return false;
		}
		knifeValue = value2;
		return true;
	}

	private static bool HasChangedPaint(CCSPlayerController player, int weaponDefIndex, out WeaponInfo? weaponInfo)
	{
		weaponInfo = null;
		if (!GPlayerWeaponsInfo.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> value) || !value.TryGetValue(player.Team, out var value2))
		{
			return false;
		}
		if (!value2.TryGetValue(weaponDefIndex, out var value3) || value3.Paint <= 0)
		{
			return false;
		}
		weaponInfo = value3;
		return true;
	}

	private static float ViewAsFloat(uint value)
	{
		return BitConverter.Int32BitsToSingle((int)value);
	}

	public override void Load(bool hotReload)
	{
		Instance = this;
		if (hotReload)
		{
			OnMapStart(string.Empty);
			GPlayerWeaponsInfo.Clear();
			GPlayersKnife.Clear();
			GPlayersGlove.Clear();
			GPlayersAgent.Clear();
			GPlayersPin.Clear();
			GPlayersMusic.Clear();
			foreach (CCSPlayerController item in from player in Utilities.GetPlayers().TakeWhile((CCSPlayerController _) => WeaponSync != null).OfType<CCSPlayerController>()
				where player.IsValid && !string.IsNullOrEmpty(player.IpAddress) && (object)player != null && !player.IsBot && player.Connected == PlayerConnectedState.Connected
				select player)
			{
				PlayerInfo playerInfo = new PlayerInfo
				{
					UserId = item.UserId,
					Slot = item.Slot,
					Index = (int)item.Index,
					SteamId = item?.SteamID.ToString(),
					Name = item?.PlayerName
				};
				object ipAddress;
				if ((object)item == null)
				{
					ipAddress = null;
				}
				else
				{
					string? ipAddress2 = item.IpAddress;
					ipAddress = ((ipAddress2 != null) ? ipAddress2.Split(":")[0] : null);
				}
				playerInfo.IpAddress = (string?)ipAddress;
				PlayerInfo playerInfo2 = playerInfo;
				Task.Run(async () =>
				{
					if (WeaponSync != null)
					{
						await WeaponSync.GetPlayerData(playerInfo2);
					}
				});
			}
		}
		Utility.LoadSkinsFromFile(ModuleDirectory + "/data/skins_" + _config.SkinsLanguage + ".json", Logger);
		Utility.LoadGlovesFromFile(ModuleDirectory + "/data/gloves_" + _config.SkinsLanguage + ".json", Logger);
		Utility.LoadAgentsFromFile(ModuleDirectory + "/data/agents_" + _config.SkinsLanguage + ".json", Logger);
		Utility.LoadMusicFromFile(ModuleDirectory + "/data/music_" + _config.SkinsLanguage + ".json", Logger);
		Utility.LoadPinsFromFile(ModuleDirectory + "/data/collectibles_" + _config.SkinsLanguage + ".json", Logger);
		RegisterListeners();
	}

	public override void Unload(bool hotReload)
	{
		if (_giveNamedItemHooked)
		{
			VirtualFunctions.GiveNamedItemFunc.Unhook(OnGiveNamedItemPost, HookMode.Post);
			_giveNamedItemHooked = false;
		}
	}

	public void OnConfigParsed(WeaponPaintsConfig config)
	{
		Config = config;
		_config = config;
		if (config.DatabaseHost.Length < 1 || config.DatabaseName.Length < 1 || config.DatabaseUser.Length < 1)
		{
			throw new InvalidOperationException("You need to setup Database credentials in \"configs/plugins/WeaponPaints/WeaponPaints.json\"!");
		}
		if (!File.Exists(Path.GetDirectoryName(Path.GetDirectoryName(ModuleDirectory)) + "/gamedata/weaponpaints.json"))
		{
			throw new InvalidOperationException("You need to upload \"weaponpaints.json\" to \"gamedata directory\"!");
		}
		MySqlConnectionStringBuilder mySqlConnectionStringBuilder = new MySqlConnectionStringBuilder
		{
			Server = config.DatabaseHost,
			UserID = config.DatabaseUser,
			Password = config.DatabasePassword,
			Database = config.DatabaseName,
			Port = (uint)config.DatabasePort,
			Pooling = true,
			MaximumPoolSize = 640u
		};
		Database = new Database(mySqlConnectionStringBuilder.ConnectionString);
		WeaponSync = new WeaponSynchronization(Database, config);
		Utility.CheckDatabaseTables();
		_localizer = Localizer;
		Utility.Config = config;
		Utility.ShowAd(ModuleVersion);
		Task.Run(async () =>
		{
			await Utility.CheckVersion(ModuleVersion, Logger);
		});
	}

	public override void OnAllPluginsLoaded(bool hotReload)
	{
		try
		{
			MenuApi = MenuCapability.Get();
			if (Config.Additional.KnifeEnabled)
			{
				SetupKnifeMenu();
			}
			if (Config.Additional.SkinEnabled)
			{
				SetupSkinsMenu();
			}
			if (Config.Additional.GloveEnabled)
			{
				SetupGlovesMenu();
			}
			if (Config.Additional.AgentEnabled)
			{
				SetupAgentsMenu();
			}
			if (Config.Additional.MusicEnabled)
			{
				SetupMusicMenu();
			}
			if (Config.Additional.PinsEnabled)
			{
				SetupPinsMenu();
			}
			RegisterCommands();
		}
		catch (Exception)
		{
			MenuApi = null;
			Logger.LogError("Error while loading required plugins");
			throw;
		}
	}
}
public class Additional
{
	[JsonPropertyName("KnifeEnabled")]
	public bool KnifeEnabled { get; set; } = true;

	[JsonPropertyName("GloveEnabled")]
	public bool GloveEnabled { get; set; } = true;

	[JsonPropertyName("MusicEnabled")]
	public bool MusicEnabled { get; set; } = true;

	[JsonPropertyName("AgentEnabled")]
	public bool AgentEnabled { get; set; } = true;

	[JsonPropertyName("SkinEnabled")]
	public bool SkinEnabled { get; set; } = true;

	[JsonPropertyName("PinsEnabled")]
	public bool PinsEnabled { get; set; } = true;

	[JsonPropertyName("CommandWpEnabled")]
	public bool CommandWpEnabled { get; set; } = true;

	[JsonPropertyName("CommandKillEnabled")]
	public bool CommandKillEnabled { get; set; } = true;

	[JsonPropertyName("CommandKnife")]
	public List<string> CommandKnife { get; set; }

	[JsonPropertyName("CommandMusic")]
	public List<string> CommandMusic { get; set; }

	[JsonPropertyName("CommandPin")]
	public List<string> CommandPin { get; set; }

	[JsonPropertyName("CommandGlove")]
	public List<string> CommandGlove { get; set; }

	[JsonPropertyName("CommandAgent")]
	public List<string> CommandAgent { get; set; }

	[JsonPropertyName("CommandStattrak")]
	public List<string> CommandStattrak { get; set; }

	[JsonPropertyName("CommandSkin")]
	public List<string> CommandSkin { get; set; }

	[JsonPropertyName("CommandSkinSelection")]
	public List<string> CommandSkinSelection { get; set; }

	[JsonPropertyName("CommandRefresh")]
	public List<string> CommandRefresh { get; set; }

	[JsonPropertyName("CommandKill")]
	public List<string> CommandKill { get; set; }

	[JsonPropertyName("GiveRandomKnife")]
	public bool GiveRandomKnife { get; set; }

	[JsonPropertyName("GiveRandomSkin")]
	public bool GiveRandomSkin { get; set; }

	[JsonPropertyName("ShowSkinImage")]
	public bool ShowSkinImage { get; set; }

	public Additional()
	{
		int num = 1;
		List<string> list = new List<string>(num);
		CollectionsMarshal.SetCount(list, num);
		CollectionsMarshal.AsSpan(list)[0] = "knife";
		CommandKnife = list;
		num = 1;
		List<string> list2 = new List<string>(num);
		CollectionsMarshal.SetCount(list2, num);
		CollectionsMarshal.AsSpan(list2)[0] = "music";
		CommandMusic = list2;
		num = 4;
		List<string> list3 = new List<string>(num);
		CollectionsMarshal.SetCount(list3, num);
		Span<string> span = CollectionsMarshal.AsSpan(list3);
		span[0] = "pin";
		span[1] = "pins";
		span[2] = "coin";
		span[3] = "coins";
		CommandPin = list3;
		num = 1;
		List<string> list4 = new List<string>(num);
		CollectionsMarshal.SetCount(list4, num);
		CollectionsMarshal.AsSpan(list4)[0] = "gloves";
		CommandGlove = list4;
		num = 1;
		List<string> list5 = new List<string>(num);
		CollectionsMarshal.SetCount(list5, num);
		CollectionsMarshal.AsSpan(list5)[0] = "agents";
		CommandAgent = list5;
		num = 2;
		List<string> list6 = new List<string>(num);
		CollectionsMarshal.SetCount(list6, num);
		Span<string> span2 = CollectionsMarshal.AsSpan(list6);
		span2[0] = "stattrak";
		span2[1] = "st";
		CommandStattrak = list6;
		num = 1;
		List<string> list7 = new List<string>(num);
		CollectionsMarshal.SetCount(list7, num);
		CollectionsMarshal.AsSpan(list7)[0] = "ws";
		CommandSkin = list7;
		num = 1;
		List<string> list8 = new List<string>(num);
		CollectionsMarshal.SetCount(list8, num);
		CollectionsMarshal.AsSpan(list8)[0] = "skins";
		CommandSkinSelection = list8;
		num = 1;
		List<string> list9 = new List<string>(num);
		CollectionsMarshal.SetCount(list9, num);
		CollectionsMarshal.AsSpan(list9)[0] = "wp";
		CommandRefresh = list9;
		num = 1;
		List<string> list10 = new List<string>(num);
		CollectionsMarshal.SetCount(list10, num);
		CollectionsMarshal.AsSpan(list10)[0] = "kill";
		CommandKill = list10;
		GiveRandomKnife = false;
		GiveRandomSkin = false;
		ShowSkinImage = true;
		
	}
}
public class WeaponPaintsConfig : BasePluginConfig
{
	[JsonPropertyName("ConfigVersion")]
	public override int Version { get; set; } = 10;

	[JsonPropertyName("SkinsLanguage")]
	public string SkinsLanguage { get; set; } = "en";

	[JsonPropertyName("DatabaseHost")]
	public string DatabaseHost { get; set; } = "";

	[JsonPropertyName("DatabasePort")]
	public int DatabasePort { get; set; } = 3306;

	[JsonPropertyName("DatabaseUser")]
	public string DatabaseUser { get; set; } = "";

	[JsonPropertyName("DatabasePassword")]
	public string DatabasePassword { get; set; } = "";

	[JsonPropertyName("DatabaseName")]
	public string DatabaseName { get; set; } = "";

	[JsonPropertyName("CmdRefreshCooldownSeconds")]
	public int CmdRefreshCooldownSeconds { get; set; } = 3;

	[JsonPropertyName("Website")]
	public string Website { get; set; } = "example.com/skins";

	[JsonPropertyName("Additional")]
	public Additional Additional { get; set; } = new Additional();

	[JsonPropertyName("MenuType")]
	public string MenuType { get; set; } = "selectable";
}
public class Database(string dbConnectionString)
{
	public async Task<MySqlConnection> GetConnectionAsync()
	{
		try
		{
			MySqlConnection connection = new MySqlConnection(dbConnectionString);
			await connection.OpenAsync();
			return connection;
		}
		catch (Exception ex)
		{
			Exception ex2 = ex;
			WeaponPaints.Instance.Logger.LogError("Unable to connect to database: " + ex2.Message);
			throw;
		}
	}
}
public static class PlayerExtensions
{
	public static void Print(this CCSPlayerController controller, string message)
	{
		if (WeaponPaints._localizer != null)
		{
			StringBuilder stringBuilder = new StringBuilder(WeaponPaints._localizer["wp_prefix"]);
			stringBuilder.Append(message);
			controller.PrintToChat(stringBuilder.ToString());
		}
	}
}
public class PlayerInfo
{
	public int Index { get; set; }

	public int Slot { get; init; }

	public int? UserId { get; set; }

	public string? SteamId { get; init; }

	public string? Name { get; set; }

	public string? IpAddress { get; set; }
}
internal static class Utility
{
	internal static WeaponPaintsConfig? Config { get; set; }

	internal static async Task CheckDatabaseTables()
	{
		if (WeaponPaints.Database == null)
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await WeaponPaints.Database.GetConnectionAsync();
			await using MySqlTransaction transaction = await connection.BeginTransactionAsync();
			try
			{
				string[] createTableQueries = new string[6] { "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_skins` (\n\t\t\t\t\t        `steamid` varchar(18) NOT NULL,\n\t\t\t\t\t        `weapon_team` int(1) NOT NULL,\n\t\t\t\t\t        `weapon_defindex` int(6) NOT NULL,\n\t\t\t\t\t        `weapon_paint_id` int(6) NOT NULL,\n\t\t\t\t\t        `weapon_wear` float NOT NULL DEFAULT 0.000001,\n\t\t\t\t\t        `weapon_seed` int(16) NOT NULL DEFAULT 0,\n\t\t\t\t\t        `weapon_nametag` VARCHAR(128) DEFAULT NULL,\n\t\t\t\t\t        `weapon_stattrak` tinyint(1) NOT NULL DEFAULT 0,\n\t\t\t\t\t        `weapon_stattrak_count` int(10) NOT NULL DEFAULT 0,\n\t\t\t\t\t        `weapon_sticker_0` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0;0;0' COMMENT 'id;schema;x;y;wear;scale;rotation',\n\t\t\t\t\t        `weapon_sticker_1` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0;0;0' COMMENT 'id;schema;x;y;wear;scale;rotation',\n\t\t\t\t\t        `weapon_sticker_2` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0;0;0' COMMENT 'id;schema;x;y;wear;scale;rotation',\n\t\t\t\t\t        `weapon_sticker_3` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0;0;0' COMMENT 'id;schema;x;y;wear;scale;rotation',\n\t\t\t\t\t        `weapon_sticker_4` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0;0;0' COMMENT 'id;schema;x;y;wear;scale;rotation',\n\t\t\t\t\t        `weapon_keychain` VARCHAR(128) NOT NULL DEFAULT '0;0;0;0;0' COMMENT 'id;x;y;z;seed',\n\t\t\t\t\t        UNIQUE (`steamid`, `weapon_team`, `weapon_defindex`) -- Add unique constraint here\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;", "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_knife` (\n\t\t\t\t\t        `steamid` varchar(18) NOT NULL,\n\t\t\t\t\t        `weapon_team` int(1) NOT NULL,\n\t\t\t\t\t        `knife` varchar(64) NOT NULL,\n\t\t\t\t\t        UNIQUE (`steamid`, `weapon_team`) -- Unique constraint\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;", "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_gloves` (\n\t\t\t\t\t        `steamid` varchar(18) NOT NULL,\n\t\t\t\t\t        `weapon_team` int(1) NOT NULL,\n\t\t\t\t\t        `weapon_defindex` int(11) NOT NULL,\n\t\t\t\t\t        UNIQUE (`steamid`, `weapon_team`) -- Unique constraint\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;", "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_agents` (\n\t\t\t\t\t        `steamid` varchar(18) NOT NULL,\n\t\t\t\t\t        `agent_ct` varchar(64) DEFAULT NULL,\n\t\t\t\t\t        `agent_t` varchar(64) DEFAULT NULL,\n\t\t\t\t\t        UNIQUE (`steamid`) -- Unique constraint\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;", "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_music` (\n\t\t\t\t\t        `steamid` varchar(64) NOT NULL,\n\t\t\t\t\t        `weapon_team` int(1) NOT NULL,\n\t\t\t\t\t        `music_id` int(11) NOT NULL,\n\t\t\t\t\t        UNIQUE (`steamid`, `weapon_team`) -- Unique constraint\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;", "\n\t\t\t\t\t    CREATE TABLE IF NOT EXISTS `wp_player_pins` (\n\t\t\t\t\t        `steamid` varchar(64) NOT NULL,\n\t\t\t\t\t        `weapon_team` int(1) NOT NULL,\n\t\t\t\t\t        `id` int(11) NOT NULL,\n\t\t\t\t\t        UNIQUE (`steamid`, `weapon_team`) -- Unique constraint\n\t\t\t\t\t    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;" };
				string[] array = createTableQueries;
				foreach (string query in array)
				{
					await connection.ExecuteAsync(query, null, transaction);
				}
				await transaction.CommitAsync();
			}
			catch (Exception)
			{
				await transaction.RollbackAsync();
				throw new Exception("[WeaponPaints] Unable to create tables!");
			}
		}
		catch (Exception ex2)
		{
			throw new Exception("[WeaponPaints] Unknown MySQL exception! " + ex2.Message);
		}
	}

	internal static bool IsPlayerValid(CCSPlayerController? player)
	{
		if ((object)player == null || WeaponPaints.WeaponSync == null)
		{
			return false;
		}
		return (object)player != null && player.IsValid && !player.IsBot && !player.IsHLTV && player.UserId.HasValue;
	}

	internal static void LoadSkinsFromFile(string filePath, ILogger logger)
	{
		string value = File.ReadAllText(filePath);
		try
		{
			List<JObject> list = JsonConvert.DeserializeObject<List<JObject>>(value);
			WeaponPaints.SkinsList = list ?? new List<JObject>();
		}
		catch (FileNotFoundException)
		{
			logger?.LogError("Not found \"skins.json\" file");
		}
	}

	internal static void LoadPinsFromFile(string filePath, ILogger logger)
	{
		string value = File.ReadAllText(filePath);
		try
		{
			List<JObject> list = JsonConvert.DeserializeObject<List<JObject>>(value);
			WeaponPaints.PinsList = list ?? new List<JObject>();
		}
		catch (FileNotFoundException)
		{
			logger?.LogError("Not found \"pins.json\" file");
		}
	}

	internal static void LoadGlovesFromFile(string filePath, ILogger logger)
	{
		try
		{
			string value = File.ReadAllText(filePath);
			List<JObject> list = JsonConvert.DeserializeObject<List<JObject>>(value);
			WeaponPaints.GlovesList = list ?? new List<JObject>();
		}
		catch (FileNotFoundException)
		{
			logger?.LogError("Not found \"gloves.json\" file");
		}
	}

	internal static void LoadAgentsFromFile(string filePath, ILogger logger)
	{
		try
		{
			string value = File.ReadAllText(filePath);
			List<JObject> list = JsonConvert.DeserializeObject<List<JObject>>(value);
			WeaponPaints.AgentsList = list ?? new List<JObject>();
		}
		catch (FileNotFoundException)
		{
			logger?.LogError("Not found \"agents.json\" file");
		}
	}

	internal static void LoadMusicFromFile(string filePath, ILogger logger)
	{
		try
		{
			string value = File.ReadAllText(filePath);
			List<JObject> list = JsonConvert.DeserializeObject<List<JObject>>(value);
			WeaponPaints.MusicList = list ?? new List<JObject>();
		}
		catch (FileNotFoundException)
		{
			logger?.LogError("Not found \"music.json\" file");
		}
	}

	internal static void Log(string message)
	{
		Console.BackgroundColor = ConsoleColor.DarkGray;
		Console.ForegroundColor = ConsoleColor.Cyan;
		Console.WriteLine("[WeaponPaints] " + message);
		Console.ResetColor();
	}

	internal static IMenu? CreateMenu(string title)
	{
		string text = WeaponPaints.Instance.Config.MenuType.ToLower();
		string text2 = text;
		if (1 == 0)
		{
		}
		IMenu result;
		if (text.Equals("selectable", StringComparison.CurrentCultureIgnoreCase))
		{
			result = WeaponPaints.MenuApi?.GetMenu(title);
		}
		else if (text.Equals("dynamic", StringComparison.CurrentCultureIgnoreCase))
		{
			result = WeaponPaints.MenuApi?.GetMenuForcetype(title, MenuType.ButtonMenu);
		}
		else if (text.Equals("center", StringComparison.CurrentCultureIgnoreCase))
		{
			result = WeaponPaints.MenuApi?.GetMenuForcetype(title, MenuType.CenterMenu);
		}
		else if (text.Equals("chat", StringComparison.CurrentCultureIgnoreCase))
		{
			result = WeaponPaints.MenuApi?.GetMenuForcetype(title, MenuType.ChatMenu);
		}
		else
		{
			result = ((!text.Equals("console", StringComparison.CurrentCultureIgnoreCase)) ? WeaponPaints.MenuApi?.GetMenu(title) : WeaponPaints.MenuApi?.GetMenuForcetype(title, MenuType.ConsoleMenu));
		}
		if (1 == 0)
		{
		}
		return result;
	}

	internal static async Task CheckVersion(string version, ILogger logger)
	{
		using HttpClient client = new HttpClient();
		try
		{
			HttpResponseMessage response = await client.GetAsync("https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/VERSION").ConfigureAwait(continueOnCapturedContext: false);
			if (response.IsSuccessStatusCode)
			{
				string remoteVersion = (await response.Content.ReadAsStringAsync().ConfigureAwait(continueOnCapturedContext: false)).Trim();
				int comparisonResult = string.CompareOrdinal(version, remoteVersion);
				int num = comparisonResult;
				if (num >= 0)
				{
					if (num > 0)
					{
						logger.LogInformation("Probably dev version detected");
					}
					else
					{
						logger.LogInformation("Plugin is up to date");
					}
				}
				else
				{
					logger.LogWarning("Plugin is outdated! Check https://github.com/Nereziel/cs2-WeaponPaints");
				}
			}
			else
			{
				logger.LogWarning("Failed to check version");
			}
		}
		catch (HttpRequestException ex)
		{
			HttpRequestException ex2 = ex;
			logger.LogError(ex2, "Failed to connect to the version server.");
		}
		catch (Exception ex3)
		{
			Exception ex4 = ex3;
			logger.LogError(ex4, "An error occurred while checking version.");
		}
	}

	internal static void ShowAd(string moduleVersion)
	{
		Console.WriteLine(" ");
		Console.WriteLine(" _     _  _______  _______  _______  _______  __    _  _______  _______  ___   __    _  _______  _______ ");
		Console.WriteLine("| | _ | ||       ||   _   ||       ||       ||  |  | ||       ||   _   ||   | |  |  | ||       ||       |");
		Console.WriteLine("| || || ||    ___||  |_|  ||    _  ||   _   ||   |_| ||    _  ||  |_|  ||   | |   |_| ||_     _||  _____|");
		Console.WriteLine("|       ||   |___ |       ||   |_| ||  | |  ||       ||   |_| ||       ||   | |       |  |   |  | |_____ ");
		Console.WriteLine("|       ||    ___||       ||    ___||  |_|  ||  _    ||    ___||       ||   | |  _    |  |   |  |_____  |");
		Console.WriteLine("|   _   ||   |___ |   _   ||   |    |       || | |   ||   |    |   _   ||   | | | |   |  |   |   _____| |");
		Console.WriteLine("|__| |__||_______||__| |__||___|    |_______||_|  |__||___|    |__| |__||___| |_|  |__|  |___|  |_______|");
		Console.WriteLine("\t\t\t\t\t\t>> Version: " + moduleVersion);
		Console.WriteLine("\t\t\t>> GitHub: https://github.com/Nereziel/cs2-WeaponPaints");
		Console.WriteLine(" ");
	}
}
public class WeaponInfo
{
	public int Paint { get; set; }

	public int Seed { get; set; }

	public float Wear { get; set; }

	public string Nametag { get; set; } = "";

	public bool StatTrak { get; set; }

	public int StatTrakCount { get; set; }

	public KeyChainInfo? KeyChain { get; set; }

	public List<StickerInfo> Stickers { get; set; } = new List<StickerInfo>();
}
public class StickerInfo
{
	public uint Id { get; set; }

	public uint Schema { get; set; }

	public float OffsetX { get; set; }

	public float OffsetY { get; set; }

	public float Wear { get; set; }

	public float Scale { get; set; }

	public float Rotation { get; set; }
}
public class KeyChainInfo
{
	public uint Id { get; set; }

	public float OffsetX { get; set; }

	public float OffsetY { get; set; }

	public float OffsetZ { get; set; }

	public uint Seed { get; set; }
}
internal class WeaponSynchronization
{
	private readonly WeaponPaintsConfig _config;

	private readonly Database _database;

	internal WeaponSynchronization(Database database, WeaponPaintsConfig config)
	{
		_database = database;
		_config = config;
	}

	internal async Task GetPlayerData(PlayerInfo? player)
	{
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			if (_config.Additional.KnifeEnabled)
			{
				GetKnifeFromDatabase(player, connection);
			}
			if (_config.Additional.GloveEnabled)
			{
				GetGloveFromDatabase(player, connection);
			}
			if (_config.Additional.AgentEnabled)
			{
				GetAgentFromDatabase(player, connection);
			}
			if (_config.Additional.MusicEnabled)
			{
				GetMusicFromDatabase(player, connection);
			}
			if (_config.Additional.SkinEnabled)
			{
				GetWeaponPaintsFromDatabase(player, connection);
			}
			if (_config.Additional.PinsEnabled)
			{
				GetPinsFromDatabase(player, connection);
			}
		}
		catch (Exception ex)
		{
			Exception ex2 = ex;
			Console.WriteLine("An error occurred: " + ex2.Message);
		}
	}

	private void GetKnifeFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (!_config.Additional.KnifeEnabled || string.IsNullOrEmpty(player?.SteamId))
			{
				return;
			}
			IEnumerable<object> enumerable = connection.Query<object>("SELECT `knife`, `weapon_team` FROM `wp_player_knife` WHERE `steamid` = @steamid ORDER BY `weapon_team` ASC", new
			{
				steamid = player.SteamId
			});
			foreach (dynamic item in enumerable)
			{
				if (!(string.IsNullOrEmpty(item.knife) ? true : false))
				{
					int num = (int)item.weapon_team;
					if (1 == 0)
					{
					}
					CsTeam csTeam = num switch
					{
						2 => CsTeam.Terrorist, 
						3 => CsTeam.CounterTerrorist, 
						_ => CsTeam.None, 
					};
					if (1 == 0)
					{
					}
					CsTeam csTeam2 = csTeam;
					ConcurrentDictionary<CsTeam, string> orAdd = WeaponPaints.GPlayersKnife.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<CsTeam, string>());
					if (csTeam2 == CsTeam.None)
					{
						orAdd[CsTeam.Terrorist] = item.knife;
						orAdd[CsTeam.CounterTerrorist] = item.knife;
					}
					else
					{
						orAdd[csTeam2] = item.knife;
					}
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetKnifeFromDatabase: " + ex.Message);
		}
	}

	private void GetGloveFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (!_config.Additional.GloveEnabled || string.IsNullOrEmpty(player?.SteamId))
			{
				return;
			}
			IEnumerable<object> enumerable = connection.Query<object>("SELECT `weapon_defindex`, `weapon_team` FROM `wp_player_gloves` WHERE `steamid` = @steamid ORDER BY `weapon_team` ASC", new
			{
				steamid = player.SteamId
			});
			foreach (dynamic item in enumerable)
			{
				if (!((item.weapon_defindex == null) ? true : false))
				{
					ConcurrentDictionary<CsTeam, ushort> orAdd = WeaponPaints.GPlayersGlove.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<CsTeam, ushort>());
					int num = (int)item.weapon_team;
					if (1 == 0)
					{
					}
					CsTeam csTeam = num switch
					{
						2 => CsTeam.Terrorist, 
						3 => CsTeam.CounterTerrorist, 
						_ => CsTeam.None, 
					};
					if (1 == 0)
					{
					}
					CsTeam csTeam2 = csTeam;
					if (csTeam2 == CsTeam.None)
					{
						orAdd[CsTeam.Terrorist] = (ushort)item.weapon_defindex;
						orAdd[CsTeam.CounterTerrorist] = (ushort)item.weapon_defindex;
					}
					else
					{
						orAdd[csTeam2] = (ushort)item.weapon_defindex;
					}
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetGlovesFromDatabase: " + ex.Message);
		}
	}

	private void GetAgentFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (!_config.Additional.AgentEnabled || string.IsNullOrEmpty(player?.SteamId))
			{
				return;
			}
			(string, string) tuple = connection.QueryFirstOrDefault<(string, string)>("SELECT `agent_ct`, `agent_t` FROM `wp_player_agents` WHERE `steamid` = @steamid", new
			{
				steamid = player.SteamId
			});
			(string, string) tuple2 = tuple;
			if (!(tuple2.Item1 == null) || !(tuple2.Item2 == null))
			{
				var (text, text2) = tuple;
				if (!string.IsNullOrEmpty(text) || !string.IsNullOrEmpty(text2))
				{
					WeaponPaints.GPlayersAgent[player.Slot] = (text, text2);
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetAgentFromDatabase: " + ex.Message);
		}
	}

	private void GetWeaponPaintsFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (!_config.Additional.SkinEnabled || player == null || string.IsNullOrEmpty(player.SteamId))
			{
				return;
			}
			ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> orAdd = WeaponPaints.GPlayerWeaponsInfo.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>>());
			IEnumerable<object> enumerable = connection.Query<object>("SELECT * FROM `wp_player_skins` WHERE `steamid` = @steamid ORDER BY `weapon_team` ASC", new
			{
				steamid = player.SteamId
			});
			foreach (dynamic item2 in enumerable)
			{
				int key = item2.weapon_defindex ?? ((object)0);
				int paint = item2.weapon_paint_id ?? ((object)0);
				float wear = item2.weapon_wear ?? ((object)0f);
				int seed = item2.weapon_seed ?? ((object)0);
				string nametag = item2.weapon_nametag ?? "";
				bool statTrak = item2.weapon_stattrak ?? ((object)false);
				int statTrakCount = item2.weapon_stattrak_count ?? ((object)0);
				object obj = item2.weapon_team;
				if (1 == 0)
				{
				}
				if (!(obj is int num))
				{
					goto IL_0560;
				}
				CsTeam csTeam;
				if (num != 2)
				{
					if (num != 3)
					{
						goto IL_0560;
					}
					csTeam = CsTeam.CounterTerrorist;
				}
				else
				{
					csTeam = CsTeam.Terrorist;
				}
				goto IL_0565;
				IL_0565:
				if (1 == 0)
				{
				}
				CsTeam csTeam2 = csTeam;
				string[] array = item2.weapon_keychain?.ToString().Split(';');
				KeyChainInfo keyChainInfo = new KeyChainInfo();
				if (array.Length == 5 && uint.TryParse(array[0], out var result) && float.TryParse(array[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var result2) && float.TryParse(array[2], NumberStyles.Float, CultureInfo.InvariantCulture, out var result3) && float.TryParse(array[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var result4) && uint.TryParse(array[4], out var result5))
				{
					keyChainInfo.Id = result;
					keyChainInfo.OffsetX = result2;
					keyChainInfo.OffsetY = result3;
					keyChainInfo.OffsetZ = result4;
					keyChainInfo.Seed = result5;
				}
				else
				{
					keyChainInfo.Id = 0u;
					keyChainInfo.OffsetX = 0f;
					keyChainInfo.OffsetY = 0f;
					keyChainInfo.OffsetZ = 0f;
					keyChainInfo.Seed = 0u;
				}
				WeaponInfo weaponInfo = new WeaponInfo
				{
					Paint = paint,
					Seed = seed,
					Wear = wear,
					Nametag = nametag,
					KeyChain = keyChainInfo,
					StatTrak = statTrak,
					StatTrakCount = statTrakCount
				};
				for (int num2 = 0; num2 <= 4; num2++)
				{
					string key2 = $"weapon_sticker_{num2}";
					object obj2 = ((IDictionary<string, object>)item2)[key2];
					if (!string.IsNullOrEmpty(obj2.ToString()))
					{
						string[] array2 = obj2.ToString().Split(';');
						if (array2.Length == 7 && uint.TryParse(array2[0], out var result6) && uint.TryParse(array2[1], out var result7) && float.TryParse(array2[2], NumberStyles.Float, CultureInfo.InvariantCulture, out var result8) && float.TryParse(array2[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var result9) && float.TryParse(array2[4], NumberStyles.Float, CultureInfo.InvariantCulture, out var result10) && float.TryParse(array2[5], NumberStyles.Float, CultureInfo.InvariantCulture, out var result11) && float.TryParse(array2[6], NumberStyles.Float, CultureInfo.InvariantCulture, out var result12))
						{
							StickerInfo item = new StickerInfo
							{
								Id = result6,
								Schema = result7,
								OffsetX = result8,
								OffsetY = result9,
								Wear = result10,
								Scale = result11,
								Rotation = result12
							};
							weaponInfo.Stickers.Add(item);
						}
					}
				}
				if (csTeam2 == CsTeam.None)
				{
					ConcurrentDictionary<int, WeaponInfo> orAdd2 = orAdd.GetOrAdd(CsTeam.Terrorist, (CsTeam _) => new ConcurrentDictionary<int, WeaponInfo>());
					ConcurrentDictionary<int, WeaponInfo> orAdd3 = orAdd.GetOrAdd(CsTeam.CounterTerrorist, (CsTeam _) => new ConcurrentDictionary<int, WeaponInfo>());
					orAdd2[key] = weaponInfo;
					orAdd3[key] = weaponInfo;
				}
				else
				{
					ConcurrentDictionary<int, WeaponInfo> orAdd4 = orAdd.GetOrAdd(csTeam2, (CsTeam _) => new ConcurrentDictionary<int, WeaponInfo>());
					orAdd4[key] = weaponInfo;
				}
				continue;
				IL_0560:
				csTeam = CsTeam.None;
				goto IL_0565;
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetWeaponPaintsFromDatabase: " + ex.Message);
		}
	}

	private void GetMusicFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (!_config.Additional.MusicEnabled || string.IsNullOrEmpty(player?.SteamId))
			{
				return;
			}
			IEnumerable<object> enumerable = connection.Query<object>("SELECT `music_id`, `weapon_team` FROM `wp_player_music` WHERE `steamid` = @steamid ORDER BY `weapon_team` ASC", new
			{
				steamid = player.SteamId
			});
			foreach (dynamic item in enumerable)
			{
				if (!((item.music_id == null) ? true : false))
				{
					int num = (int)item.weapon_team;
					if (1 == 0)
					{
					}
					CsTeam csTeam = num switch
					{
						2 => CsTeam.Terrorist, 
						3 => CsTeam.CounterTerrorist, 
						_ => CsTeam.None, 
					};
					if (1 == 0)
					{
					}
					CsTeam csTeam2 = csTeam;
					ConcurrentDictionary<CsTeam, ushort> orAdd = WeaponPaints.GPlayersMusic.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<CsTeam, ushort>());
					if (csTeam2 == CsTeam.None)
					{
						orAdd[CsTeam.Terrorist] = (ushort)item.music_id;
						orAdd[CsTeam.CounterTerrorist] = (ushort)item.music_id;
					}
					else
					{
						orAdd[csTeam2] = (ushort)item.music_id;
					}
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetMusicFromDatabase: " + ex.Message);
		}
	}

	private void GetPinsFromDatabase(PlayerInfo? player, MySqlConnection connection)
	{
		try
		{
			if (string.IsNullOrEmpty(player?.SteamId))
			{
				return;
			}
			IEnumerable<object> enumerable = connection.Query<object>("SELECT `id`, `weapon_team` FROM `wp_player_pins` WHERE `steamid` = @steamid ORDER BY `weapon_team` ASC", new
			{
				steamid = player.SteamId
			});
			foreach (dynamic item in enumerable)
			{
				if (!((item.id == null) ? true : false))
				{
					int num = (int)item.weapon_team;
					if (1 == 0)
					{
					}
					CsTeam csTeam = num switch
					{
						2 => CsTeam.Terrorist, 
						3 => CsTeam.CounterTerrorist, 
						_ => CsTeam.None, 
					};
					if (1 == 0)
					{
					}
					CsTeam csTeam2 = csTeam;
					ConcurrentDictionary<CsTeam, ushort> orAdd = WeaponPaints.GPlayersPin.GetOrAdd(player.Slot, (int _) => new ConcurrentDictionary<CsTeam, ushort>());
					if (csTeam2 == CsTeam.None)
					{
						orAdd[CsTeam.Terrorist] = (ushort)item.id;
						orAdd[CsTeam.CounterTerrorist] = (ushort)item.id;
					}
					else
					{
						orAdd[csTeam2] = (ushort)item.id;
					}
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("An error occurred in GetPinsFromDatabase: " + ex.Message);
		}
	}

	internal async Task SyncKnifeToDatabase(PlayerInfo player, string knife, CsTeam[] teams)
	{
		if (!_config.Additional.KnifeEnabled || string.IsNullOrEmpty(player.SteamId) || string.IsNullOrEmpty(knife) || teams.Length == 0)
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			foreach (CsTeam team in teams)
			{
				await connection.ExecuteAsync("INSERT INTO `wp_player_knife` (`steamid`, `weapon_team`, `knife`) VALUES(@steamid, @team, @newKnife) ON DUPLICATE KEY UPDATE `knife` = @newKnife", new
				{
					steamid = player.SteamId,
					team = team,
					newKnife = knife
				});
			}
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing knife to database: " + ex.Message);
		}
	}

	internal async Task SyncGloveToDatabase(PlayerInfo player, ushort gloveDefIndex, CsTeam[] teams)
	{
		if (!_config.Additional.GloveEnabled || string.IsNullOrEmpty(player.SteamId) || teams.Length == 0)
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			foreach (CsTeam team in teams)
			{
				await connection.ExecuteAsync("\n        INSERT INTO `wp_player_gloves` (`steamid`, `weapon_team`, `weapon_defindex`) \n        VALUES(@steamid, @team, @gloveDefIndex) \n        ON DUPLICATE KEY UPDATE `weapon_defindex` = @gloveDefIndex", new
				{
					steamid = player.SteamId,
					team = (int)team,
					gloveDefIndex = gloveDefIndex
				});
			}
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing glove to database: " + ex.Message);
		}
	}

	internal async Task SyncAgentToDatabase(PlayerInfo player)
	{
		if (!_config.Additional.AgentEnabled || string.IsNullOrEmpty(player.SteamId))
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			await connection.ExecuteAsync("\t\t\t\t\tINSERT INTO `wp_player_agents` (`steamid`, `agent_ct`, `agent_t`)\n\t\t\t\t\tVALUES(@steamid, @agent_ct, @agent_t)\n\t\t\t\t\tON DUPLICATE KEY UPDATE\n\t\t\t\t\t\t`agent_ct` = @agent_ct,\n\t\t\t\t\t\t`agent_t` = @agent_t", new
			{
				steamid = player.SteamId,
				agent_ct = WeaponPaints.GPlayersAgent[player.Slot].CT,
				agent_t = WeaponPaints.GPlayersAgent[player.Slot].T
			});
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing agents to database: " + ex.Message);
		}
	}

	internal async Task SyncWeaponPaintsToDatabase(PlayerInfo player)
	{
		if (string.IsNullOrEmpty(player.SteamId) || !WeaponPaints.GPlayerWeaponsInfo.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> teamWeaponInfos))
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			foreach (var (teamId, weaponsInfo) in teamWeaponInfos)
			{
				foreach (var (weaponDefIndex, weaponInfo2) in weaponsInfo)
				{
					int paintId = weaponInfo2.Paint;
					float wear = weaponInfo2.Wear;
					int seed = weaponInfo2.Seed;
					string query;
					object parameters;
					if (await connection.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM `wp_player_skins` WHERE `steamid` = @steamid AND `weapon_defindex` = @weaponDefIndex AND `weapon_team` = @weaponTeam", new
					{
						steamid = player.SteamId,
						weaponDefIndex = weaponDefIndex,
						weaponTeam = teamId
					}) > 0)
					{
						query = "UPDATE `wp_player_skins` SET `weapon_paint_id` = @paintId, `weapon_wear` = @wear, `weapon_seed` = @seed WHERE `steamid` = @steamid AND `weapon_defindex` = @weaponDefIndex AND `weapon_team` = @weaponTeam";
						parameters = new
						{
							steamid = player.SteamId,
							weaponDefIndex = weaponDefIndex,
							weaponTeam = (int)teamId,
							paintId = paintId,
							wear = wear,
							seed = seed
						};
					}
					else
					{
						query = "INSERT INTO `wp_player_skins` (`steamid`, `weapon_defindex`, `weapon_team`, `weapon_paint_id`, `weapon_wear`, `weapon_seed`) VALUES (@steamid, @weaponDefIndex, @weaponTeam, @paintId, @wear, @seed)";
						parameters = new
						{
							steamid = player.SteamId,
							weaponDefIndex = weaponDefIndex,
							weaponTeam = (int)teamId,
							paintId = paintId,
							wear = wear,
							seed = seed
						};
					}
					await connection.ExecuteAsync(query, parameters);
				}
			}
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing weapon paints to database: " + ex.Message);
		}
	}

	internal async Task SyncMusicToDatabase(PlayerInfo player, ushort music, CsTeam[] teams)
	{
		if (!_config.Additional.MusicEnabled || string.IsNullOrEmpty(player.SteamId))
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			foreach (CsTeam team in teams)
			{
				await connection.ExecuteAsync("INSERT INTO `wp_player_music` (`steamid`, `weapon_team`, `music_id`) VALUES(@steamid, @team, @newMusic) ON DUPLICATE KEY UPDATE `music_id` = @newMusic", new
				{
					steamid = player.SteamId,
					team = team,
					newMusic = music
				});
			}
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing music kit to database: " + ex.Message);
		}
	}

	internal async Task SyncPinToDatabase(PlayerInfo player, ushort pin, CsTeam[] teams)
	{
		if (!_config.Additional.PinsEnabled || string.IsNullOrEmpty(player.SteamId))
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			foreach (CsTeam team in teams)
			{
				await connection.ExecuteAsync("INSERT INTO `wp_player_pins` (`steamid`, `weapon_team`, `id`) VALUES(@steamid, @team, @newPin) ON DUPLICATE KEY UPDATE `id` = @newPin", new
				{
					steamid = player.SteamId,
					team = team,
					newPin = pin
				});
			}
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing pin to database: " + ex.Message);
		}
	}

	internal async Task SyncStatTrakToDatabase(PlayerInfo player)
	{
		if (WeaponPaints.WeaponSync == null || WeaponPaints.GPlayerWeaponsInfo.IsEmpty || string.IsNullOrEmpty(player.SteamId))
		{
			return;
		}
		try
		{
			await using MySqlConnection connection = await _database.GetConnectionAsync();
			await using MySqlTransaction transaction = await connection.BeginTransactionAsync();
			if (!WeaponPaints.GPlayerWeaponsInfo.TryGetValue(player.Slot, out ConcurrentDictionary<CsTeam, ConcurrentDictionary<int, WeaponInfo>> teamWeaponsInfo))
			{
				return;
			}
			foreach (KeyValuePair<CsTeam, ConcurrentDictionary<int, WeaponInfo>> teamInfo in teamWeaponsInfo)
			{
				ConcurrentDictionary<int, WeaponInfo> weaponInfos = teamInfo.Value;
				Dictionary<int, (bool StatTrak, int StatTrakCount)> statTrakWeapons = weaponInfos.ToDictionary((KeyValuePair<int, WeaponInfo> w) => w.Key, (KeyValuePair<int, WeaponInfo> w) => (StatTrak: w.Value.StatTrak, StatTrakCount: w.Value.StatTrakCount));
				if (statTrakWeapons.Count == 0)
				{
					continue;
				}
				int weaponTeam = (int)teamInfo.Key;
				foreach (KeyValuePair<int, (bool, int)> item in statTrakWeapons)
				{
					item.Deconstruct(out var key, out var value);
					(bool, int) tuple = value;
					int defindex = key;
					bool statTrak = tuple.Item1;
					int statTrakCount = tuple.Item2;
					var parameters = new
					{
						steamid = player.SteamId,
						weaponDefIndex = defindex,
						StatTrak = statTrak,
						StatTrakCount = statTrakCount,
						weaponTeam = weaponTeam
					};
					await connection.ExecuteAsync("\n\t\t\t\t\t    UPDATE `wp_player_skins` \n\t\t\t\t\t    SET `weapon_stattrak` = @StatTrak, \n\t\t\t\t\t        `weapon_stattrak_count` = @StatTrakCount\n\t\t\t\t\t    WHERE `steamid` = @steamid \n\t\t\t\t\t      AND `weapon_defindex` = @weaponDefIndex\n\t\t\t\t\t      AND `weapon_team` = @weaponTeam", parameters, transaction);
				}
			}
			await transaction.CommitAsync();
		}
		catch (Exception ex)
		{
			Utility.Log("Error syncing stattrak to database: " + ex.Message);
		}
	}
}
