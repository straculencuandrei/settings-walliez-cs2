import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

remote_script = """
cat << 'EOF' > /tmp/decompile.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Core;

class Program {
    static void Main() {
        var asm = typeof(BaseEntity).Assembly;
        foreach (var type in asm.GetTypes()) {
            foreach (var m in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance)) {
                if (m.Name == "EmitSound") {
                    Console.WriteLine($"Type: {type.FullName}, Method: {m}");
                    var body = m.GetMethodBody();
                    if (body != null) {
                        Console.WriteLine($"  IL length: {body.GetILAsByteArray()?.Length}");
                    }
                }
            }
        }
    }
}
EOF
dotnet run --project /home/csgoserver/cs2-custom-mvp /tmp/decompile.cs 2>/dev/null || true
"""

# Let's inspect where EmitSound native implementation is
stdin, stdout, stderr = ssh.exec_command("grep -rn 'EmitSound' /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/")
print(stdout.read().decode('utf-8', errors='ignore')[:2000])

stdin, stdout, stderr = ssh.exec_command("nm -D /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so | grep -i sound")
print("CSS symbols:\n", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
