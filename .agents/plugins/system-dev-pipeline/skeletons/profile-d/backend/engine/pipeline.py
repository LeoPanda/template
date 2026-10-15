import os
from concurrent.futures import ProcessPoolExecutor
from typing import List, Callable, TypeVar, Any

T = TypeVar("T")
R = TypeVar("R")

class ChunkPipeline:
    """
    大容量データ解析・メディア処理用 multiprocessing チャンク並列処理基盤
    (Python GIL を回避し、マルチコア CPU をフル活用)
    """
    def __init__(self, chunk_size: int = 1000, max_workers: int = None):
        self.chunk_size = chunk_size
        self.max_workers = max_workers or max(1, (os.cpu_count() or 2) - 1)

    def split_chunks(self, items: List[T]) -> List[List[T]]:
        """リストを chunk_size ごとのサブリストに分割"""
        return [items[i:i + self.chunk_size] for i in range(0, len(items), self.chunk_size)]

    def process_parallel(self, items: List[T], worker_fn: Callable[[List[T]], List[R]]) -> List[R]:
        """チャンク並列実行と順序保持結合"""
        chunks = self.split_chunks(items)
        results: List[R] = []

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            chunk_results = list(executor.map(worker_fn, chunks))

        for cr in chunk_results:
            results.extend(cr)
        return results
