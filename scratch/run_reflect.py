import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/reflect.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Core;

class Program {
    static void Main() {
        var t = typeof(BaseEntityExtensions);
        foreach (var m in t.GetMethods()) {
            if (m.Name.Contains("EmitSound")) {
                Console.WriteLine($"{m.Name}(");
                foreach (var p in m.GetParameters()) {
                    Console.WriteLine($"   {p.ParameterType.Name} {p.Name},");
                }
                Console.WriteLine(")");
            }
        }
        var t2 = typeof(CCSPlayerController);
        foreach (var m in t2.GetMethods()) {
            if (m.Name.Contains("EmitSound")) {
                Console.WriteLine($"Player: {m.Name}");
            }
        }
    }
}
EOF
cd /home/csgoserver/cs2-custom-mvp && dotnet run --property:StartupObject=Program 2>/dev/null || true
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
