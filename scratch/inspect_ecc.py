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
        var method = typeof(CCSPlayerController).GetMethod("ExecuteClientCommand");
        if (method != null)
        {
            Console.WriteLine("ExecuteClientCommand: " + method);
            var body = method.GetMethodBody();
            if (body != null)
            {
                var il = body.GetILAsByteArray();
                Console.WriteLine("IL bytes: " + BitConverter.ToString(il));
            }
        }
        else
        {
            Console.WriteLine("ExecuteClientCommand not found on CCSPlayerController!");
            foreach (var m in typeof(CCSPlayerController).GetMethods())
            {
                if (m.Name.Contains("Command"))
                    Console.WriteLine("Found: " + m.Name);
            }
        }
    }
}
EOF
cd /tmp/test_color_proj && dotnet run
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
