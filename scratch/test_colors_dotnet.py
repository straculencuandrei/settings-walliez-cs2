import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/CheckColors.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Modules.Utils;

class Program
{
    static void Main()
    {
        Type chatColorsType = typeof(ChatColors);
        Console.WriteLine("ChatColors fields:");
        foreach (var field in chatColorsType.GetFields(BindingFlags.Public | BindingFlags.Static))
        {
            Console.WriteLine($"  {field.Name} = {((int)(char)field.GetValue(null)):X2}");
        }

        string test = "{gold}[MVP] {grey}| {white}Previewing: {gold}Test{white}...";
        try
        {
            string replaced = test.ReplaceColorTags();
            Console.WriteLine("Original: " + test);
            Console.WriteLine("Replaced: " + replaced);
            foreach (char c in replaced)
            {
                if (c < 32)
                    Console.Write($"[0x{(int)c:X2}]");
                else
                    Console.Write(c);
            }
            Console.WriteLine();
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error: " + ex);
        }
    }
}
EOF

cd /home/csgoserver/cs2-custom-mvp && dotnet run /tmp/CheckColors.cs || true
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
