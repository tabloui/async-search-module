import asyncio
import os
import time
import functools
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional

@functools.lru_cache(maxsize=128)
def cached_fuzzy_match(word: str, target: str, cutoff: float = 0.6) -> bool:
    """Comprueba si una palabra coincide de forma difusa con el objetivo."""
    if not word or not target:
        return False
    matches = difflib.get_close_matches(word.lower(), [target.lower()], n=1, cutoff=cutoff)
    return len(matches) > 0

class AsyncAdvancedSearch:
    def __init__(self, root_dir: str = ".", excluded_dirs: Optional[List[str]] = None):
        self.root_dir = Path(root_dir)
        self.excluded_dirs = set(excluded_dirs or ['.git', '__pycache__', 'node_modules', '.venv', 'venv'])
        self._cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
        self.ttl = 60

    async def search_files(self, query: str, extension: Optional[str] = None, fuzzy: bool = True) -> List[Dict[str, Any]]:
        """Realiza una búsqueda asíncrona de archivos aplicando filtros avanzados y caché."""
        cache_key = f"{query}_{extension}_{fuzzy}"
        now = time.time()

        if cache_key in self._cache:
            timestamp, results = self._cache[cache_key]
            if now - timestamp < self.ttl:
                return results

        results = await asyncio.to_thread(self._sync_search, query, extension, fuzzy)
        self._cache[cache_key] = (now, results)
        return results

    def _sync_search(self, query: str, extension: Optional[str], fuzzy: bool) -> List[Dict[str, Any]]:
        found = []
        for path in self.root_dir.rglob("*"):
            if any(exc in path.parts for exc in self.excluded_dirs):
                continue
            if not path.is_file():
                continue

            if extension and path.suffix.lower() != extension.lower():
                continue

            filename = path.name
            match = False

            if query.lower() in filename.lower():
                match = True
            elif fuzzy and cached_fuzzy_match(query, filename):
                match = True

            if match:
                found.append({
                    "path": str(path),
                    "name": filename,
                    "size": path.stat().st_size
                })
        return found

default_searcher = AsyncAdvancedSearch()
