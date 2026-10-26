import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /home/csgoserver/cs2-custom-mvp/TestColorOutput.cs
using System;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Translations;

public class TestColorOutput
{
    public static void Run()
    {
        string raw = "{gold}[MVP] {grey}| {white}Previewing: {gold}Stiu feat WALLI3Z{white}...";
        string formatted = raw.ReplaceColorTags();
        Console.WriteLine("Formatted: " + formatted);
        foreach (char c in formatted)
        {
            if (c < 32)
                Console.Write($"[0x{(int)c:X2}]");
            else
                Console.Write(c);
        }
        Console.WriteLine();
    }
}
EOF
"""
stdin, stdout, stderr = ssh.exec_command(script)
ssh.close()
