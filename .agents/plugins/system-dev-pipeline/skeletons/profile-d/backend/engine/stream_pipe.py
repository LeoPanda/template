import subprocess
from typing import List, Optional, Tuple


class StreamPipeManager:
    """
    外部プロセス (FFmpeg 等) とのインメモリ双方向パイプ制御基盤
    (ディスク書き込み I/O ボトルネックを排除し、ダイレクトメモリ転送)
    """
    def __init__(self, command: List[str]):
        self.command = command
        self.process: Optional[subprocess.Popen] = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return self

    def write_chunk(self, data: bytes) -> None:
        if self.process and self.process.stdin:
            self.process.stdin.write(data)

    def finish(self) -> Tuple[bytes, bytes]:
        if not self.process:
            return b"", b""
        stdout, stderr = self.process.communicate()
        return stdout, stderr

    def close(self) -> None:
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            if self.process.stdin:
                try:
                    self.process.stdin.close()
                except OSError:
                    pass
            self.process = None
