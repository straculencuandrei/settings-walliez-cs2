import os, sys

with open(r"C:\Users\buzunar\.gemini\antigravity-ide\brain\fcfbab7e-5aa1-4945-a84f-f8c3888faae9\scratch\Original_Helper.cs", "r", encoding="utf-8") as f:
    code = f.read()

# Add translation using
if "using CounterStrikeSharp.API.Core.Translations;" not in code:
    code = "using CounterStrikeSharp.API.Core.Translations;\n" + code

# Fix CSS v300+ PlayerConnectedState removal
code = code.replace("&& p.Connected == PlayerConnectedState.PlayerConnected", "")
code = code.replace("p.Connected == PlayerConnectedState.PlayerConnected &&", "")
code = code.replace("p.Connected == PlayerConnectedState.PlayerConnected", "p != null && p.IsValid")

# Fix Namespaces
code = code.replace("namespace MVP_Sounds_GoldKingZ;", "namespace Custom_MVP_Sounds;")
code = code.replace("using MVP_Sounds_GoldKingZ.Config;", "using Custom_MVP_Sounds.Config;")
code = code.replace("namespace MVP_Sounds_GoldKingZ.Config", "namespace Custom_MVP_Sounds.Config")

# Fix Cookie paths
code = code.replace('"../../plugins/MVP-Sounds-GoldKingZ/Cookies/"', '"Cookies/"')
code = code.replace('"../../plugins/MVP-Sounds-GoldKingZ/Cookies/MVP_Sounds_Cookies.json"', '"Cookies/MVP_Sounds_Cookies.json"')

# Replace AdvancedPrintToChat and AdvancedPrintToServer with color tags & space prefix
old_print = """    public static void AdvancedPrintToChat(CCSPlayerController player, string message, params object[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            message = message.Replace($"{{{i}}}", args[i].ToString());
        }
        if (Regex.IsMatch(message, "{nextline}", RegexOptions.IgnoreCase))
        {
            string[] parts = Regex.Split(message, "{nextline}", RegexOptions.IgnoreCase);
            foreach (string part in parts)
            {
                string messages = part.Trim();
                player.PrintToChat(" " + messages);
            }
        }else
        {
            player.PrintToChat(message);
        }
    }
    public static void AdvancedPrintToServer(string message, params object[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            message = message.Replace($"{{{i}}}", args[i].ToString());
        }
        if (Regex.IsMatch(message, "{nextline}", RegexOptions.IgnoreCase))
        {
            string[] parts = Regex.Split(message, "{nextline}", RegexOptions.IgnoreCase);
            foreach (string part in parts)
            {
                string messages = part.Trim();
                Server.PrintToChatAll(" " + messages);
            }
        }else
        {
            Server.PrintToChatAll(message);
        }
    }"""

new_print = """    public static void AdvancedPrintToChat(CCSPlayerController player, string message, params object[] args)
    {
        if (player == null || !player.IsValid) return;
        for (int i = 0; i < args.Length; i++)
        {
            message = message.Replace($"{{{i}}}", args[i]?.ToString() ?? string.Empty);
        }
        message = message.ReplaceColorTags();
        if (Regex.IsMatch(message, "{nextline}", RegexOptions.IgnoreCase))
        {
            string[] parts = Regex.Split(message, "{nextline}", RegexOptions.IgnoreCase);
            foreach (string part in parts)
            {
                string messages = part.Trim();
                player.PrintToChat(" " + messages);
            }
        }
        else
        {
            player.PrintToChat(" " + message);
        }
    }
    public static void AdvancedPrintToServer(string message, params object[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            message = message.Replace($"{{{i}}}", args[i]?.ToString() ?? string.Empty);
        }
        message = message.ReplaceColorTags();
        if (Regex.IsMatch(message, "{nextline}", RegexOptions.IgnoreCase))
        {
            string[] parts = Regex.Split(message, "{nextline}", RegexOptions.IgnoreCase);
            foreach (string part in parts)
            {
                string messages = part.Trim();
                Server.PrintToChatAll(" " + messages);
            }
        }
        else
        {
            Server.PrintToChatAll(" " + message);
        }
    }"""

assert old_print in code, "old_print not matched!"
code = code.replace(old_print, new_print)

os.makedirs("server-configs/plugins/Custom_MVP_Sounds/Config", exist_ok=True)
with open("server-configs/plugins/Custom_MVP_Sounds/Config/Helper.cs", "w", encoding="utf-8") as f:
    f.write(code)

print("[+] Successfully generated server-configs/plugins/Custom_MVP_Sounds/Config/Helper.cs")
