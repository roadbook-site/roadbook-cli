import time
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config import get_books_dir, get_roadbook_dir, CORE_DIR

class RuntimeManager:
    @staticmethod
    def _resolve_book_dir(rb_id: str, book_dir: Optional[Path] = None) -> Path:
        if book_dir is not None:
            return Path(book_dir)

        from .roadbook import RoadbookManager

        book = RoadbookManager.get_roadbook(rb_id)
        if not book:
            return get_books_dir() / rb_id
        return book.path.parent

    @staticmethod
    def get_runtime_dir(rb_id: str, book_dir: Optional[Path] = None) -> Path:
        return RuntimeManager._resolve_book_dir(rb_id, book_dir) / "runtime"

    @staticmethod
    def get_active_session_file() -> Path:
        """Returns the path to the file storing the active session info."""
        # Use new core location first
        new_path = CORE_DIR / "active_session.json"
        
        # Migration check
        legacy_path = get_roadbook_dir() / "active_session.json"
        if legacy_path.exists() and not new_path.exists():
            try:
                legacy_path.rename(new_path)
            except Exception:
                pass
                
        return new_path

    @staticmethod
    def save_active_session(rb_id: str, run_id: str, current_step: int = 0, roadbook_dir: Optional[Path] = None):
        """Saves the current active session state."""
        data = {
            "roadbook_id": rb_id,
            "run_id": run_id,
            "current_step": current_step,
            "timestamp": time.time()
        }
        if roadbook_dir is not None:
            data["roadbook_dir"] = str(roadbook_dir)
        with open(RuntimeManager.get_active_session_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_active_session() -> Optional[Dict[str, Any]]:
        """Loads the current active session state."""
        path = RuntimeManager.get_active_session_file()
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def clear_active_session():
        """Clears the active session."""
        path = RuntimeManager.get_active_session_file()
        if path.exists():
            path.unlink()

    @staticmethod
    def get_scripts_dir(rb_id: str, book_dir: Optional[Path] = None) -> Path:
        path = RuntimeManager._resolve_book_dir(rb_id, book_dir) / "scripts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_runs_dir(rb_id: str, book_dir: Optional[Path] = None) -> Path:
        path = RuntimeManager.get_runtime_dir(rb_id, book_dir) / "runs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def find_script(rb_id: str, lang: str = None, book_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Finds a script for the given roadbook ID.
        If lang is provided, looks for that specific language extension.
        If lang is None, looks for any supported script type (priority: .py > .js > .ts).
        """
        cwd = Path.cwd()
        
        # Define search extensions
        extensions = []
        if lang:
            if lang.lower() == "python": extensions = [".py"]
            elif lang.lower() in ["node", "nodejs", "javascript"]: extensions = [".js"]
            elif lang.lower() in ["typescript", "ts"]: extensions = [".ts"]
        else:
            extensions = [".py", ".js", ".ts"]

        for ext in extensions:
            # 1. Check workspace .roadbook (New Standard)
            workspace_roadbook_script = cwd / ".roadbook" / rb_id / "scripts" / f"script{ext}"
            if workspace_roadbook_script.exists():
                return workspace_roadbook_script
            
            # 2. Check current workspace (Legacy High priority)
            # Check ./scripts/script<ext>
            workspace_script = cwd / "scripts" / f"script{ext}"
            if workspace_script.exists():
                return workspace_script

            # Check ./<rb_id><ext>
            workspace_script_direct = cwd / f"{rb_id}{ext}"
            if workspace_script_direct.exists():
                return workspace_script_direct

            # 3. Check roadbook directory (Standard location)
            scripts_dir = RuntimeManager.get_scripts_dir(rb_id, book_dir)
            script_path = scripts_dir / f"script{ext}"
            
            if script_path.exists():
                return script_path
                
        return None

    @staticmethod
    def list_scripts(rb_id: str, book_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        scripts_dir = RuntimeManager.get_scripts_dir(rb_id, book_dir)
        results = []
        if scripts_dir.exists():
            for item in scripts_dir.iterdir():
                if item.is_file() and item.suffix in ['.py', '.js', '.ts']:
                    lang_map = {".py": "Python", ".js": "NodeJS", ".ts": "TypeScript"}
                    stats = item.stat()
                    results.append({
                        "name": item.name,
                        "lang": lang_map.get(item.suffix, "Unknown"),
                        "size": stats.st_size,
                        "mtime": stats.st_mtime,
                        "path": str(item)
                    })
        return results

    @staticmethod
    def clean_scripts(rb_id: str, book_dir: Optional[Path] = None):
        scripts_dir = RuntimeManager.get_scripts_dir(rb_id, book_dir)
        for item in scripts_dir.iterdir():
            if item.is_file():
                item.unlink()

    @staticmethod
    def create_run(rb_id: str, book_dir: Optional[Path] = None) -> str:
        run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        runs_dir = RuntimeManager.get_runs_dir(rb_id, book_dir)
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_id

    @staticmethod
    def log_run_result(rb_id: str, run_id: str, status: str, details: Dict[str, Any], book_dir: Optional[Path] = None):
        runs_dir = RuntimeManager.get_runs_dir(rb_id, book_dir)
        run_dir = runs_dir / run_id
        
        result = {
            "id": run_id,
            "roadbook_id": rb_id,
            "status": status,
            "timestamp": time.time(),
            "details": details
        }
        
        with open(run_dir / "run_meta.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        # Update 'last' symlink or copy
        last_link = runs_dir.parent / "last_run.json"
        with open(last_link, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    @staticmethod
    def list_runs(rb_id: str, book_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        runs_dir = RuntimeManager.get_runs_dir(rb_id, book_dir)
        results = []
        for item in runs_dir.iterdir():
            if item.is_dir() and (item / "run_meta.json").exists():
                try:
                    with open(item / "run_meta.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append(data)
                except Exception:
                    continue
        # Sort by timestamp desc
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return results

    @staticmethod
    def get_last_run(rb_id: str, book_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        # Check last_run.json first
        last_link = RuntimeManager.get_runtime_dir(rb_id, book_dir) / "last_run.json"
        if last_link.exists():
            try:
                with open(last_link, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Fallback to list
        runs = RuntimeManager.list_runs(rb_id, book_dir)
        if runs:
            return runs[0]
        return None
    
    @staticmethod
    def get_run(rb_id: str, run_id: str, book_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        run_file = RuntimeManager.get_runs_dir(rb_id, book_dir) / run_id / "run_meta.json"
        if run_file.exists():
            try:
                with open(run_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None
