import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/reflect_mvp.cs
using System;
using System.Reflection;

class Program {
    static void Main() {
        var asm = Assembly.LoadFrom("/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll");
        var type = asm.GetType("MVPSoundsGoldKingZ") ?? System.Linq.Enumerable.First(asm.GetTypes(), t => t.Name == "MVPSoundsGoldKingZ");
        foreach (var m in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance)) {
            if (m.Name.Contains("PlaySound")) {
                Console.WriteLine($"Found method: {m.Name}");
                var bytes = m.GetMethodBody()?.GetILAsByteArray();
                if (bytes == null) continue;
                for (int i = 0; i < bytes.Length - 4; i++) {
                    if (bytes[i] == 0x28 || bytes[i] == 0x6F) {
                        int token = BitConverter.ToInt32(bytes, i + 1);
                        try {
                            var called = asm.ManifestModule.ResolveMethod(token);
                            Console.WriteLine($"   Calls: {called.DeclaringType.FullName}.{called.Name}");
                        } catch {}
                    }
                }
            }
        }
    }
}
EOF

cd /tmp/reflect_proj && cp /tmp/reflect_mvp.cs Program.cs && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
