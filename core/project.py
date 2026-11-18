#!/usr/bin/env python3
"""
project.py - MyOS project detection and configuration handling.
Handles .MyOS/Project.md and project hierarchy detection.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import sys
import logging

from core.config.parser import MarkdownConfigParser
from core.brand import META_DIR, NAME, getenv, project_heading

logger = logging.getLogger(__name__)

# System-wide version constant
APP_VERSION = getenv("VERSION", f"{NAME} v0.1")


def _coerce_search_dir(start_path: Union[str, Path]) -> Path:
    target = Path(start_path).expanduser().resolve()
    return target.parent if target.is_file() else target


def _read_inherit_value_from_config_file(config_path: Path) -> Optional[str]:
    """
    Read inherit value from a <Section>.md config file.
    Returns normalized inherit value or None when missing/unreadable.
    """
    try:
        data = MarkdownConfigParser.parse_file(config_path)
    except Exception:
        return None
    section_name = config_path.stem
    section_data = None
    if isinstance(data, dict):
        section_data = data.get(section_name, data)
    else:
        section_data = data
    inherit_values = MarkdownConfigParser.find_inherit(section_data)
    if inherit_values is None:
        return None
    if isinstance(inherit_values, list):
        if not inherit_values:
            return None
        value = str(inherit_values[0]).strip().lower()
    else:
        value = str(inherit_values).strip().lower()
    if value in {"fix", "dynamic", "not"}:
        return value
    return None


def find_config_in_parents(
    start_path: Union[str, Path],
    config_name: str,
    *,
    require_project_marker: bool = True,
    honor_inherit_not: bool = True,
) -> Optional[Path]:
    """
    Find nearest `.MyOS/<config_name>` by walking up from start_path.
    """
    search_dir = _coerce_search_dir(start_path)
    for candidate in [search_dir, *search_dir.parents]:
        if require_project_marker and not (candidate / META_DIR / "Project.md").exists():
            continue
        config_path = candidate / META_DIR / str(config_name)
        if not (config_path.exists() and config_path.is_file()):
            continue
        if honor_inherit_not:
            inherit_value = _read_inherit_value_from_config_file(config_path)
            if inherit_value == "not":
                return None
        return config_path
    return None


def find_next_parent_config(
    current_project: Union[str, Path],
    config_name: str,
    *,
    require_project_marker: bool = True,
    honor_inherit_not: bool = True,
) -> Optional[Path]:
    """
    Find nearest parent config above the current project directory.
    """
    project_dir = _coerce_search_dir(current_project)
    parent = project_dir.parent
    if parent == project_dir:
        return None
    return find_config_in_parents(
        parent,
        config_name,
        require_project_marker=require_project_marker,
        honor_inherit_not=honor_inherit_not,
    )




class ProjectConfig:
    """Load, write, and manage project configuration stored in .MyOS/."""

    def __init__(self, path: Path):
        """Initialize a ProjectConfig for the given path."""
        self.path = Path(path)
        self.settings_dir = self.path / META_DIR
        
        # Marker file that defines a project root
        self.project_md = self.settings_dir / "Project.md"
        
        self.templates = []
        self.version = None
        self.metadata = {}
        self.config_data = {}
        
        # Load config if this is a valid project
        if self.is_valid():
            self.load()
            logger.debug("ProjectConfig created at %s", self.path)
    
    def _is_project(self) -> bool:
        """Return True when the project marker file exists."""
        return self.project_md.exists()
    
    def load(self):
        """Load configuration from local .MyOS/ files."""
        if self.settings_dir.exists():
            self._load_from_settings_dir()
    
    def _load_from_settings_dir(self):
        """Load Templates.md, Manifest.md, and Config.md from .MyOS/."""
        # Templates.md -> self.templates
        templates_md = self.settings_dir / "Templates.md"
        if templates_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(templates_md)
                logger.debug("Parsed Templates.md: %s", data)
                
                if data:
                    # Case 1: list under "Templates"
                    if "Templates" in data:
                        templates_data = data["Templates"]
                        if isinstance(templates_data, list):
                            self.templates = templates_data
                        elif isinstance(templates_data, dict):
                            # Look for "items" in a section dict
                            if "items" in templates_data:
                                items = templates_data["items"]
                                if isinstance(items, list):
                                    self.templates = items
                                elif isinstance(items, str):
                                    self.templates = [items]
                    
                    # Case 2: root list
                    elif isinstance(data, list):
                        self.templates = data
                    
                logger.debug("Loaded templates = %s", self.templates)
            except Exception as e:
                logger.exception("Error parsing Templates.md: %s", e)
        
        # Manifest.md -> self.metadata, self.version
        manifest_md = self.settings_dir / "Manifest.md"
        if manifest_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(manifest_md)
                logger.debug("Parsed Manifest.md: %s", data)
                
                if data and "Project" in data:
                    manifest_data = data["Project"]
                    if isinstance(manifest_data, dict):
                        # Normalize keys for consistent access
                        self.metadata = {}
                        for key, value in manifest_data.items():
                            # Store values as strings for easier use
                            if isinstance(value, list):
                                self.metadata[key.lower()] = ", ".join(value)
                            else:
                                self.metadata[key.lower()] = str(value)
                        
                        # Extract version separately if present
                        if "version" in self.metadata:
                            self.version = self.metadata.pop("version")
                        
                logger.debug("Loaded metadata = %s, version = %s", self.metadata, self.version)
            except Exception as e:
                logger.exception("Error parsing Manifest.md: %s", e)
        
        # Config.md -> self.config_data
        self._load_config_data()
    
    def _load_config_data(self):
        """Load Config.md into self.config_data."""
        config_md = self.settings_dir / "Config.md"
        if config_md.exists():
            try:
                self.config_data = MarkdownConfigParser.parse_file(config_md)
                logger.debug("Loaded config_data from Config.md")
            except Exception as e:
                logger.exception("Error parsing Config.md: %s", e)
                self.config_data = {}
        else:
            self.config_data = {}
            logger.debug("Config.md does not exist at %s", config_md)
    
    def get_inherit_status(self, section_name: str) -> str:
        """
        Read the inherit status for a section.
        
        Args:
            section_name: Section name (e.g., "Templates")
                
        Returns:
            "fix" | "dynamic" | "not"; missing/invalid -> "dynamic"
        """
        if not self.config_data:
            self._load_config_data()
        if section_name not in self.config_data:
            logger.debug("Section '%s' not found in config data, default dynamic", section_name)
            return "dynamic"
        section_data = self.config_data[section_name]
        inherit_values = MarkdownConfigParser.find_inherit(section_data)
        if inherit_values is None:
            return "dynamic"
        if isinstance(inherit_values, list):
            if not inherit_values:
                return "dynamic"
            inherit_value = inherit_values[0].lower()
        else:
            inherit_value = str(inherit_values).lower()
        if inherit_value in ("fix", "dynamic", "not"):
            return inherit_value
        logger.warning("Invalid inherit value '%s' in section '%s', defaulting to dynamic", inherit_value, section_name)
        return "dynamic"

    def _get_local_section_data(self, section_name: str) -> Tuple[Any, bool]:
        """
        Return local section data from <Section>.md first, then Config.md.
        """
        section = str(section_name or "").strip()
        if not section:
            return None, False

        section_file = self.settings_dir / f"{section}.md"
        if section_file.exists():
            try:
                parsed = MarkdownConfigParser.parse_file(section_file)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                if section in parsed:
                    return parsed.get(section), True
                return parsed, True
            if parsed is not None:
                return parsed, True

        if not self.config_data:
            self._load_config_data()
        if section in self.config_data:
            return self.config_data.get(section), True
        return None, False

    @staticmethod
    def _inherit_from_section_data(section_data: Any) -> str:
        inherit_values = MarkdownConfigParser.find_inherit(section_data)
        if inherit_values is None:
            return "dynamic"
        if isinstance(inherit_values, list):
            if not inherit_values:
                return "dynamic"
            inherit_value = str(inherit_values[0]).strip().lower()
        else:
            inherit_value = str(inherit_values).strip().lower()
        if inherit_value in ("fix", "dynamic", "not"):
            return inherit_value
        return "dynamic"

    def resolve_effective_section(self, section_name: str) -> Any:
        """
        Resolve a section by walking project ancestors.
        Nearest local section wins. Missing inherit defaults to dynamic.
        """
        section = str(section_name or "").strip()
        if not section:
            return None

        current = self.path
        while True:
            marker = current / META_DIR / "Project.md"
            if marker.exists():
                settings_dir = current / META_DIR
                local_data = None
                found = False

                section_file = settings_dir / f"{section}.md"
                if section_file.exists():
                    try:
                        parsed = MarkdownConfigParser.parse_file(section_file)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, dict):
                        if section in parsed:
                            local_data = parsed.get(section)
                        else:
                            local_data = parsed
                        found = True
                    elif parsed is not None:
                        local_data = parsed
                        found = True

                if not found:
                    config_md = settings_dir / "Config.md"
                    if config_md.exists():
                        try:
                            parsed_config = MarkdownConfigParser.parse_file(config_md)
                        except Exception:
                            parsed_config = {}
                        if isinstance(parsed_config, dict) and section in parsed_config:
                            local_data = parsed_config.get(section)
                            found = True

                if found:
                    inherit_state = self._inherit_from_section_data(local_data)
                    if inherit_state == "not":
                        return None
                    return local_data
            if current == current.parent:
                break
            current = current.parent
        return None

    @staticmethod
    def _extract_templates_from_section(section_data: Any) -> List[str]:
        if section_data is None:
            return []
        values: List[str] = []
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict):
                    items = item.get("items")
                    if isinstance(items, list):
                        values.extend(str(v).strip() for v in items if str(v).strip())
                    elif isinstance(items, str) and items.strip():
                        values.append(items.strip())
                else:
                    text = str(item).strip()
                    if text:
                        values.append(text)
        elif isinstance(section_data, dict):
            items = section_data.get("items")
            if isinstance(items, list):
                values.extend(str(v).strip() for v in items if str(v).strip())
            elif isinstance(items, str) and items.strip():
                values.append(items.strip())
            elif "Templates" in section_data:
                inner = section_data.get("Templates")
                if isinstance(inner, list):
                    values.extend(str(v).strip() for v in inner if str(v).strip())
                elif isinstance(inner, str) and inner.strip():
                    values.append(inner.strip())
        elif isinstance(section_data, str):
            text = section_data.strip()
            if text:
                values.append(text)
        # Keep insertion order while removing duplicates.
        unique: List[str] = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
        return unique

    def get_effective_templates(self) -> List[str]:
        """
        Resolve effective Templates section from nearest project ancestor.
        """
        section_data = self.resolve_effective_section("Templates")
        return self._extract_templates_from_section(section_data)

    def get_parent_project(self) -> Optional['ProjectConfig']:
        """Find the nearest parent project (one directory above)."""
        parent_dir = self.path.parent
        if parent_dir == self.path:
            return None
        parent_config = ProjectConfig(parent_dir)
        if parent_config.is_valid():
            return parent_config
        return None

    def get_child_projects(self) -> List['ProjectConfig']:
        """Return direct child projects under this path."""
        children = []
        try:
            for item in self.path.iterdir():
                if item.is_dir():
                    child_config = ProjectConfig(item)
                    if child_config.is_valid():
                        children.append(child_config)
        except (PermissionError, OSError) as e:
            logger.debug("Error accessing directory %s: %s", self.path, e)
        return children

    def is_valid(self) -> bool:
        """Return True when this path is a valid MyOS project."""
        return self._is_project()

    
    @classmethod
    def create(cls, dir_path: Union[str, Path]) -> 'ProjectConfig':
        """
        Create a new project marker. The parent's config files are not copied (they are
        inherited); the templates' root .MyOS files are (core.template_seed).
        """
        dir_path = Path(dir_path)
        
        # Find nearest parent with .MyOS
        parent_settings = cls._find_parent_settings_dir(dir_path)
        if not parent_settings:
            raise ValueError(f"No parent {META_DIR} directory found for {dir_path}")
        # Ensure target directory exists and initialize minimal .MyOS marker.
        dir_path.mkdir(parents=True, exist_ok=True)
        target_settings = dir_path / META_DIR
        from core.project_unmake import record_created, settings_before  # late: imports this module
        before = settings_before(dir_path)  # the folder's own settings (tags, a sort rule)
        target_settings.mkdir(parents=True, exist_ok=True)
        project_marker = target_settings / "Project.md"
        if not project_marker.exists():
            project_marker.write_text(project_heading() + "\n")
            cls._first_gets_standard(dir_path)
            # A new project gets what its templates' root .MyOS holds (ACLs.md, Desk.md, ...).
            from core.template_seed import seed_from_templates  # late: template_seed imports this module
            try:
                seed_from_templates(dir_path)
            except Exception:  # the project exists; a template problem must not undo that
                logger.exception("could not copy the template settings into %s", dir_path)
            # What creating wrote: turning the project back removes it without asking.
            record_created(dir_path, before)

        # Return fresh ProjectConfig.
        project = cls(dir_path)
        project._load_config_data()
        return project

    @staticmethod
    def _first_gets_standard(dir_path: Path) -> None:
        """The top project (none above it) names the template "Standard" when it is there and
        nothing names one yet: else the first project of a new user had no suggested folders,
        an empty lens, and the clock found no 0_Admin/Zeitaufwand (review 2026-11-18, E1).
        A subproject inherits its parent's templates."""
        if any((parent / META_DIR / "Project.md").is_file() for parent in dir_path.parents):
            return
        own = dir_path / META_DIR / "Templates.md"
        if own.exists():
            return
        from core.template_place import find_templates_dir  # late: light, but keeps imports as they are
        templates = find_templates_dir(dir_path)
        if templates is None or not (templates / "Standard").is_dir():
            return
        own.write_text("# Templates\nStandard\n", encoding="utf-8")

    @staticmethod
    def _find_parent_settings_dir(dir_path: Path) -> Optional[Path]:
        """Find parent .MyOS directory by walking up the directory tree."""
        current = dir_path.parent
        while current and current != current.parent:  # Stop at filesystem root
            settings_dir = current / META_DIR
            if settings_dir.exists():
                return settings_dir
            current = current.parent
        return None

    @staticmethod
    def make_project(dir_path: Union[str, Path], template: str = "standard") -> bool:
        """
        Turns an ordinary folder into a project.
        
        Args:
            dir_path: Path to directory
            template: Template name
        
        Returns:
            True if successful, False on error
        """
        try:
            path = Path(dir_path)
            
            # Check if parent directory exists
            if not path.parent.exists():
                print(f"Error: Parent directory does not exist: {path.parent}")
                return False
            
            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
            
            # Create project config (with the templates' .MyOS files)
            config = ProjectConfig.create(path)
            return config.is_valid()
            
        except (OSError, PermissionError) as e:
            # Catch actual filesystem errors
            logger.error("Error creating project at %s: %s", dir_path, e)
            return False
        except Exception as e:
            # Catch any other errors
            logger.exception("Unexpected error creating project at %s: %s", dir_path, e)
            return False


class ProjectFinder:
    """
    Finds MyOS projects in the directory hierarchy.
    
    Walks up from a starting directory to find the nearest project.
    """
    
    @staticmethod
    def find_nearest(start_path: Union[str, Path]) -> Optional[Path]:
        """
        Find nearest project root from starting path.
        
        Args:
            start_path: Starting directory path
            
        Returns:
            Path to project root directory, or None if not found
        """
        current = Path(start_path).expanduser().absolute()
        
        while current != current.parent:  # Stop at filesystem root
            # Check for .MyOS/Project.md marker
            if (current / META_DIR / "Project.md").exists():
                return current
            
            current = current.parent
        
        return None

    @staticmethod
    def is_project(path: Union[str, Path]) -> bool:
        """Check if directory contains a MyOS project."""
        path = Path(path)
        
        # Check for .MyOS/Project.md marker
        if (path / META_DIR / "Project.md").exists():
            return True
        
        return False


def find_projects(start_path: Union[str, Path]) -> List[ProjectConfig]:
    """
    Find project configs from the given path upwards.
    Order is most specific first.
    """
    start_path = Path(start_path).expanduser().resolve()
    if start_path.is_file():
        start_path = start_path.parent

    results: List[ProjectConfig] = []
    current = start_path
    while True:
        candidate = ProjectConfig(current)
        if candidate.is_valid():
            results.append(candidate)
        if current == current.parent:
            break
        current = current.parent
    return results


def resolve_cwp(start_path: Union[str, Path]) -> Optional[ProjectConfig]:
    """Resolve current working project for a given path."""
    found = ProjectFinder.find_nearest(start_path)
    if not found:
        return None
    return ProjectConfig(found)



if __name__ == "__main__":
    # Smoke test. Run from repo root: python3 -m core.project
    # Full tests: python3 -m pytest core/tests/unit/test_project_config.py -v
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        parent_settings = test_dir.parent / META_DIR
        parent_settings.mkdir(exist_ok=True)
        (parent_settings / "Project.md").write_text(project_heading() + "\n")
        result = ProjectConfig.make_project(test_dir, template="standard")
        assert result, "make_project should succeed"
        config = ProjectConfig(test_dir)
        assert config.is_valid(), "Project should be valid"
        found = ProjectFinder.find_nearest(test_dir / "subdir")
        assert found == test_dir, f"Should find {test_dir}, got {found}"
        print("✓ Smoke test passed")
