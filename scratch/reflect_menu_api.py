import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

# Create a small reflection program using dotnet
cs_code = """using System;
using System.Reflection;

class Program
{
    static void Main()
    {
        try
        {
            var asm = Assembly.LoadFrom("/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll");
            Console.WriteLine("Loaded: " + asm.FullName);
            foreach (var t in asm.GetTypes())
            {
                if (t.Name.Contains("Menu"))
                {
                    Console.WriteLine("TYPE: " + t.FullName);
                    foreach (var m in t.GetMembers(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
                    {
                        if (m.MemberType == MemberTypes.Method || m.MemberType == MemberTypes.Constructor)
                            Console.WriteLine("  " + m.ToString());
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERROR: " + ex);
        }
    }
}
"""

run("mkdir -p /tmp/reflect && cd /tmp/reflect && dotnet new console --force >/dev/null 2>&1")
sftp = ssh.open_sftp()
with sftp.file('/tmp/reflect/Program.cs', 'w') as f:
    f.write(cs_code)
sftp.close()

print('=== REFLECTION OUTPUT ===')
print(run("cd /tmp/reflect && dotnet run"))

ssh.close()
