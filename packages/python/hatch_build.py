"""Ship the one LICENSE and NOTICE at the repository root in every build, without copies in git."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        here = Path(self.root)
        for name in ("LICENSE", "NOTICE"):
            # Inside an sdist the files sit next to pyproject.toml; in the repository, two levels up.
            src = here / name if (here / name).is_file() else here.parent.parent / name
            if not src.is_file():
                raise FileNotFoundError(
                    f"{name} not found next to pyproject.toml or at the repository root"
                )
            target = name if self.target_name == "sdist" else f"one_xops/{name}"
            build_data["force_include"][str(src)] = target
        # The settings templates: next to pyproject.toml inside an sdist, at the repository root otherwise.
        tpl = here / "templates" / "settings"
        if not tpl.is_dir():
            tpl = here.parent.parent / "templates" / "settings"
        for f in sorted(tpl.glob("*.json")):
            target = f"templates/settings/{f.name}" if self.target_name == "sdist" else f"one_xops/templates/settings/{f.name}"
            build_data["force_include"][str(f)] = target
