import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/test_color_proj/Program.cs
using System;
using System.Reflection;
using CounterStrikeSharp.API.Core;

class Program
{
    static void Main()
    {
        var mod = typeof(CCSPlayerController).Module;
        foreach (int token in new int[] { 0x0600000C, 0x06000797, 0x0600109E })
        {
            var mb = mod.ResolveMethod(token);
            Console.WriteLine($"Token 0x{token:X8} => {mb.DeclaringType?.FullName}.{mb.Name}");
        }
    }
}
EOF
cd /tmp/test_color_proj && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
