import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', port=22, username='root', password=')(e092e8EjTUiV')

local_mp3 = r'C:\Users\buzunar\Documents\cs2server\wlzMVP\sounds\mvp\stiufeatWALLI3Zmastered.mp3'
remote_tmp_in = '/tmp/stiu_full.mp3'
remote_tmp_wav = '/tmp/stiu_10s.wav'

sftp = ssh.open_sftp()
sftp.put(local_mp3, remote_tmp_in)

# Trim starting at 0:00 for 10 seconds, fading out smoothly from 9.0s to 10.0s
cmd = "/usr/local/bin/ffmpeg -y -ss 00:00:00 -i /tmp/stiu_full.mp3 -t 10 -af 'afade=t=out:st=9:d=1' -c:a pcm_s16le -ar 44100 /tmp/stiu_10s.wav"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()

# Check duration
stdin, stdout, stderr = ssh.exec_command("/usr/local/bin/ffmpeg -i /tmp/stiu_10s.wav 2>&1 | grep -i duration")
print("Duration info:", stdout.read().decode().strip())

local_wav = r'C:\Users\buzunar\Documents\cs2server\wlzMVP\sounds\mvp\stiufeatWALLI3Zmastered.wav'
sftp.get(remote_tmp_wav, local_wav)
sftp.close()
ssh.close()
print("Local WAV size:", os.path.getsize(local_wav))
