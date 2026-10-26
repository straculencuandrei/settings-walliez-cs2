import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_cmds.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Core;

class Program {
    static void Main() {
        var t = typeof(CCSPlayerController);
        foreach (var m in t.GetMethods()) {
            if (m.Name.Contains("Command", StringComparison.OrdinalIgnoreCase)) {
                Console.WriteLine($"Method: {m.Name}");
                foreach (var p in m.GetParameters()) {
                    Console.WriteLine($"   {p.ParameterType.Name} {p.Name}");
                }
            }
        }
    }
}
EOF
dotnet run --project /home/csgoserver/cs2-custom-mvp /tmp/check_cmds.cs 2>/dev/null || true
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
