import subprocess
from typing import List

class StreamPipeManager:
    """
    外部プロセス (FFmpeg 等) とのインメモリ双方向パイプ制御基盤
    (ディスク書き込み I/O ボトルネックを排除し、ダイレクトメモリ転送)
    """
    def __init__(self, command: List[str]):
        self.command = command
        self.process: subprocess.Popen = None

    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return self

    def write_chunk(self, data: bytes):
        if self.process and self.process.stdin:
            self.process.stdin.write(data)

    def finish(self) -> tuple[bytes, bytes]:
        if not self.process:
            return b"", b""
        stdout, stderr = self.process.communicate()
        return stdout, stderr
