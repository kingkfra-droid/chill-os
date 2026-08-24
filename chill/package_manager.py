from __future__ import annotations

import os
import platform
import shutil
import subprocess
import importlib.util
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class System:
    os_name: str
    architecture: str
    package_manager: str | None


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def detect_system() -> System:
    # ChillOS Debian RootFS runs as root. Never use Termux pkg there.
    if os.geteuid() == 0 and command_exists("apt-get"):
        return System("debian", platform.machine(), "apt-get")

    if os.environ.get("CHILLOS_ROOTFS") == "1" and command_exists("apt-get"):
        return System("debian", platform.machine(), "apt-get")

    if command_exists("apk"):
        return System("alpine", platform.machine(), "apk")

    if command_exists("pkg") and os.geteuid() != 0:
        return System("termux", platform.machine(), "pkg")

    if command_exists("apt-get"):
        return System("debian", platform.machine(), "apt-get")

    return System("unknown", platform.machine(), None)



class PackageManager:
    def __init__(self):
        self.system = detect_system()

        # Repository recipes take priority.
        self.recipe_dir = (
            Path(__file__).resolve().parent / "recipes"
        )

        # Optional user recipes.
        self.user_recipe_dir = Path(
            os.environ.get(
                "CHILL_HOME",
                str(Path.home() / ".chillos")
            )
        ) / "recipes"


        # GitHub fallback tools.
        self.tools_dir = (
            Path(os.environ.get(
                "CHILL_HOME",
                str(Path.home() / ".chillos")
            )) / "tools"
        )
        self.tools_dir.mkdir(parents=True, exist_ok=True)


    def run(self, *args: str) -> None:
        print("[Chill] $", " ".join(args))
        subprocess.run(args, check=True)

    def install_native(self, *packages: str) -> None:
        pm = self.system.package_manager

        if pm == "apk":
            self.run("apk", "add", *packages)

        elif pm == "pkg":
            self.run("pkg", "install", "-y", *packages)

        elif pm == "apt-get":
            self.run("apt-get", "update")
            self.run("apt-get", "install", "-y", *packages)

        else:
            raise RuntimeError(
                "No supported package manager detected."
            )

    def recipe_path(self, name: str) -> Path | None:
        repo_recipe = self.recipe_dir / f"{name}.py"

        if repo_recipe.is_file():
            return repo_recipe

        user_recipe = self.user_recipe_dir / f"{name}.py"

        if user_recipe.is_file():
            return user_recipe

        return None

    def recipe_exists(self, name: str) -> bool:
        return self.recipe_path(name) is not None

    def native_package_available(self, name: str) -> bool:
        """Check whether the native package manager knows this package."""
        pm = self.system.package_manager

        try:
            if pm == "apt-get":
                result = subprocess.run(
                    ["apt-cache", "show", name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                return result.returncode == 0

            if pm == "apk":
                result = subprocess.run(
                    ["apk", "search", "-e", name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                return result.returncode == 0

            if pm == "pkg":
                result = subprocess.run(
                    ["pkg", "search", f"^{name}$"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                return result.returncode == 0

        except OSError:
            pass

        return False

    def github_search(self, query: str, limit: int = 8) -> list[dict]:
        """Search GitHub and rank repositories by relevance to the tool name."""

        encoded = urllib.parse.quote(query)

        url = (
            "https://api.github.com/search/repositories"
            f"?q={encoded}&sort=stars&order=desc&per_page={limit}"
        )

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "ChillOS-package-manager",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

        except Exception as exc:
            print(f"[Chill] GitHub search failed: {exc}")
            return []

        wanted = query.strip().lower()
        results = []

        for repo in data.get("items", []):
            if repo.get("fork"):
                continue

            full_name = repo.get("full_name", "")
            repo_name = repo.get("name", "")
            description = repo.get("description") or ""
            language = repo.get("language") or "Unknown"

            name_lower = repo_name.lower()
            full_lower = full_name.lower()
            desc_lower = description.lower()

            score = 0

            # Exact repository-name match.
            if name_lower == wanted:
                score += 100

            # Repository name starts with requested tool.
            elif name_lower.startswith(wanted):
                score += 70

            # Requested name appears in repository name.
            elif wanted in name_lower:
                score += 50

            # Full repository path match.
            if wanted in full_lower:
                score += 20

            # Description relevance.
            if wanted in desc_lower:
                score += 15

            # Prefer active repositories.
            if not repo.get("archived", False):
                score += 5

            # Stars are useful, but deliberately secondary.
            stars = repo.get("stargazers_count", 0) or 0
            score += min(stars // 100, 20)

            results.append({
                "name": full_name,
                "description": (
                    description
                    or "No description provided."
                ),
                "language": language,
                "stars": stars,
                "clone_url": repo.get("clone_url", ""),
                "html_url": repo.get("html_url", ""),
                "archived": repo.get("archived", False),
                "score": score,
            })

        results.sort(
            key=lambda repo: (
                repo["score"],
                repo["stars"],
            ),
            reverse=True,
        )

        return results[:limit]

    def select_github_repository(
        self,
        package: str,
        candidates: list[dict],
    ) -> dict | None:
        """Display GitHub candidates and let the user choose one."""

        if not candidates:
            print(f"[Chill] No GitHub repositories found for '{package}'.")
            return None

        print()
        print(f"[Chill] GitHub results for '{package}':")
        print()

        for index, repo in enumerate(candidates, 1):
            print(f"[{index}] {repo['name']}")
            print(f"    Description: {repo['description']}")
            print(f"    Language   : {repo['language']}")
            print(f"    Stars      : {repo['stars']}")
            print()

        print("[0] Cancel")

        while True:
            try:
                choice = input(
                    f"Select a tool [0-{len(candidates)}]: "
                ).strip()

                number = int(choice)

                if number == 0:
                    print("[Chill] Cancelled.")
                    return None

                if 1 <= number <= len(candidates):
                    selected = candidates[number - 1]

                    print()
                    print(f"[Chill] Selected: {selected['name']}")
                    print(
                        f"[Chill] Description: "
                        f"{selected['description']}"
                    )

                    confirm = input(
                        "Install this tool? [Y/n]: "
                    ).strip().lower()

                    if confirm in ("", "y", "yes"):
                        return selected

                    print("[Chill] Installation cancelled.")
                    return None

            except (ValueError, EOFError, KeyboardInterrupt):
                print("[Chill] Please enter a valid selection.")

    def _create_python_venv(self, target: Path) -> Path | None:
        """Create a private virtual environment for a GitHub Python tool."""

        if not command_exists("python3"):
            print("[Chill] Python 3 is required for this project.")
            return None

        venv = target / ".venv"

        if venv.exists():
            return venv

        print("[Chill] Creating Python virtual environment...")

        try:
            subprocess.run(
                ["python3", "-m", "venv", str(venv)],
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"[Chill] Failed to create virtual environment: {exc}")
            return None

        return venv


    def _install_python_project(self, target: Path) -> bool:
        """Install a Python GitHub project into its private venv."""

        venv = self._create_python_venv(target)

        if venv is None:
            return False

        pip = venv / "bin" / "pip"

        if not pip.exists():
            print("[Chill] Virtual environment pip was not created.")
            return False

        try:
            requirements = target / "requirements.txt"
            pyproject = target / "pyproject.toml"
            setup = target / "setup.py"

            if requirements.is_file():
                print("[Chill] Python project detected: requirements.txt")

                subprocess.run(
                    [
                        str(pip),
                        "install",
                        "-r",
                        str(requirements),
                    ],
                    check=True,
                )

            if pyproject.is_file():
                print("[Chill] Python project detected: pyproject.toml")

                subprocess.run(
                    [
                        str(pip),
                        "install",
                        str(target),
                    ],
                    check=True,
                )

            elif setup.is_file():
                print("[Chill] Python project detected: setup.py")

                subprocess.run(
                    [
                        str(pip),
                        "install",
                        str(target),
                    ],
                    check=True,
                )

        except subprocess.CalledProcessError as exc:
            print(f"[Chill] Python installation failed: {exc}")
            return False

        return True


    def _inspect_project(self, target: Path) -> None:
        """Show potentially relevant installation files without executing them."""

        detected = []

        checks = {
            "requirements.txt": "Python dependencies",
            "pyproject.toml": "Python project",
            "setup.py": "Python setup script",
            "Makefile": "Make build instructions",
            "install.sh": "Shell installation script",
            "INSTALL": "Installation instructions",
            "README.md": "Documentation",
        }

        for filename, description in checks.items():
            if (target / filename).is_file():
                detected.append((filename, description))

        if detected:
            print()
            print("[Chill] Project files detected:")

            for filename, description in detected:
                print(f"  - {filename}: {description}")


    def _register_executable(self, executable: Path, name: str) -> bool:
        """Register an executable in ~/.chillos/bin."""

        chill_home = Path(
            os.environ.get(
                "CHILL_HOME",
                str(Path.home() / ".chillos")
            )
        )

        bin_dir = chill_home / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        destination = bin_dir / name

        try:
            if destination.exists() or destination.is_symlink():
                destination.unlink()

            destination.symlink_to(executable)
            print(f"[✓] Registered command: {name}")
            print(f"[✓] Launcher: {destination}")
            return True

        except OSError as exc:
            print(f"[Chill] Could not register {name}: {exc}")
            return False


    def _install_go_project(
        self,
        target: Path,
        command_name: str,
    ) -> bool:
        """Automatically build a Go project."""

        if not command_exists("go"):
            print("[Chill] Go is required. Installing Go...")

            try:
                if self.system.package_manager == "apt-get":
                    self.install_native("golang-go")
                elif self.system.package_manager == "apk":
                    self.install_native("go")
                elif self.system.package_manager == "pkg":
                    self.install_native("golang")
                else:
                    raise RuntimeError(
                        "Cannot determine how to install Go."
                    )
            except Exception as exc:
                print(f"[Chill] Unable to install Go: {exc}")
                return False

        output = target / command_name

        print(f"[Chill] Building Go tool: {command_name}")

        try:
            subprocess.run(
                [
                    "go",
                    "build",
                    "-o",
                    str(output),
                    ".",
                ],
                cwd=str(target),
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"[Chill] Go build failed: {exc}")
            return False

        if not output.is_file():
            print("[Chill] Go build completed but binary was not found.")
            return False

        try:
            output.chmod(output.stat().st_mode | 0o111)
        except OSError:
            pass

        return self._register_executable(
            output,
            command_name,
        )


    def _automatic_github_install(
        self,
        target: Path,
        command_name: str,
    ) -> bool:
        """Automatically detect and install supported GitHub projects."""

        # Go project
        if (target / "go.mod").is_file():
            print("[Chill] Go project detected.")
            return self._install_go_project(
                target,
                command_name,
            )

        # Python project
        if (
            (target / "requirements.txt").is_file()
            or (target / "pyproject.toml").is_file()
            or (target / "setup.py").is_file()
        ):
            print("[Chill] Python project detected.")

            try:
                if not self._install_python_project(target):
                    return False
            except AttributeError:
                print(
                    "[Chill] Python installer is not available "
                    "in this PackageManager version."
                )
                return False

            return True

        # Rust project
        if (target / "Cargo.toml").is_file():
            if not command_exists("cargo"):
                print("[Chill] Cargo is required for this project.")
                return False

            try:
                subprocess.run(
                    ["cargo", "build", "--release"],
                    cwd=str(target),
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                print(f"[Chill] Rust build failed: {exc}")
                return False

            release = target / "target" / "release"
            binary = release / command_name

            if not binary.is_file():
                print("[Chill] Rust binary was not found.")
                return False

            return self._register_executable(
                binary,
                command_name,
            )

        # Node project
        if (target / "package.json").is_file():
            if not command_exists("npm"):
                print("[Chill] npm is required for this project.")
                return False

            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(target),
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                print(f"[Chill] npm installation failed: {exc}")
                return False

            print("[Chill] Node.js dependencies installed.")
            return True

        print(
            "[Chill] No supported automatic build system "
            "detected."
        )
        return False


    def _bundle_metadata(
        self,
        bundle: Path,
        repo: dict,
        tool_type: str,
        executable: str,
    ) -> None:
        """Write ChillOS metadata for a managed tool bundle."""

        metadata = {
            "name": bundle.name,
            "source": "github",
            "repository": repo.get("name", ""),
            "url": repo.get("html_url", ""),
            "clone_url": repo.get("clone_url", ""),
            "type": tool_type,
            "executable": f"bin/{executable}",
            "installed": True,
        }

        (bundle / "chill.json").write_text(
            json.dumps(metadata, indent=2) + "\n"
        )


    def _bundle_register(
        self,
        bundle: Path,
        executable: Path,
        command_name: str,
    ) -> bool:
        """Register a bundle executable in ~/.chillos/bin."""

        chill_home = Path(
            os.environ.get(
                "CHILL_HOME",
                str(Path.home() / ".chillos"),
            )
        )

        bin_dir = chill_home / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        launcher = bin_dir / command_name

        try:
            if launcher.exists() or launcher.is_symlink():
                launcher.unlink()

            launcher.symlink_to(executable)

            print(f"[✓] Registered: {launcher}")
            return True

        except OSError as exc:
            print(f"[Chill] Could not register launcher: {exc}")
            return False


    def _bundle_python(
        self,
        source: Path,
        deps: Path,
        bin_dir: Path,
    ) -> tuple[bool, str | None]:
        """Install a Python project into its private bundle venv."""

        if not command_exists("python3"):
            print("[Chill] Python 3 is required.")
            return False, None

        venv = deps / "venv"

        try:
            subprocess.run(
                ["python3", "-m", "venv", str(venv)],
                check=True,
            )

            pip = venv / "bin" / "pip"

            requirements = source / "requirements.txt"
            pyproject = source / "pyproject.toml"
            setup = source / "setup.py"

            if requirements.is_file():
                subprocess.run(
                    [
                        str(pip),
                        "install",
                        "-r",
                        str(requirements),
                    ],
                    check=True,
                )

            if pyproject.is_file() or setup.is_file():
                subprocess.run(
                    [
                        str(pip),
                        "install",
                        str(source),
                    ],
                    check=True,
                )

            # Copy useful venv entry points into the bundle.
            venv_bin = venv / "bin"

            if venv_bin.is_dir():
                for item in venv_bin.iterdir():
                    if (
                        item.is_file()
                        and os.access(item, os.X_OK)
                        and item.name not in {
                            "python",
                            "python3",
                            "pip",
                            "pip3",
                        }
                    ):
                        destination = bin_dir / item.name

                        if destination.exists():
                            destination.unlink()

                        destination.symlink_to(item)

            return True, None

        except (subprocess.CalledProcessError, OSError) as exc:
            print(f"[Chill] Python bundle installation failed: {exc}")
            return False, None


    def _bundle_go(
        self,
        source: Path,
        bin_dir: Path,
        command_name: str,
    ) -> tuple[bool, str | None]:
        """Build a Go project from its actual main package."""

        if not command_exists("go"):
            print("[Chill] Go is required. Installing Go...")

            try:
                if self.system.package_manager == "apt-get":
                    self.install_native("golang")
                elif self.system.package_manager == "apk":
                    self.install_native("go")
                elif self.system.package_manager == "pkg":
                    self.install_native("golang")
                else:
                    raise RuntimeError(
                        "Unsupported package manager for Go."
                    )
            except Exception as exc:
                print(f"[Chill] Unable to install Go: {exc}")
                return False, None

        main_dir = None

        # Prefer conventional cmd/<tool> layouts.
        candidates = [
            source / "cmd" / command_name,
            source / "cmd" / command_name.lower(),
        ]

        for candidate in candidates:
            if candidate.is_dir() and any(candidate.glob("*.go")):
                main_dir = candidate
                break

        # Find package main elsewhere.
        if main_dir is None:
            try:
                for go_file in source.rglob("*.go"):
                    if any(
                        part in {
                            ".git",
                            "vendor",
                            "testdata",
                        }
                        for part in go_file.parts
                    ):
                        continue

                    text = go_file.read_text(errors="ignore")

                    if (
                        "package main" in text
                        and "func main(" in text
                    ):
                        main_dir = go_file.parent
                        break

            except OSError:
                pass

        if main_dir is None:
            print("[Chill] No Go main package found.")
            return False, None

        output = bin_dir / command_name

        print(
            "[Chill] Go main package:",
            main_dir.relative_to(source),
        )

        try:
            subprocess.run(
                [
                    "go",
                    "build",
                    "-o",
                    str(output),
                    ".",
                ],
                cwd=str(main_dir),
                check=True,
            )

            output.chmod(output.stat().st_mode | 0o111)

            return True, command_name

        except subprocess.CalledProcessError as exc:
            print(f"[Chill] Go build failed: {exc}")
            return False, None


    def _bundle_rust(
        self,
        source: Path,
        bin_dir: Path,
        command_name: str,
    ) -> tuple[bool, str | None]:
        """Build a Rust project into the bundle."""

        if not command_exists("cargo"):
            print("[Chill] Cargo is required.")
            return False, None

        try:
            subprocess.run(
                ["cargo", "build", "--release"],
                cwd=str(source),
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"[Chill] Rust build failed: {exc}")
            return False, None

        binary = (
            source
            / "target"
            / "release"
            / command_name
        )

        if not binary.is_file():
            print("[Chill] Rust executable not found.")
            return False, None

        destination = bin_dir / command_name

        try:
            shutil.copy2(binary, destination)
            destination.chmod(
                destination.stat().st_mode | 0o111
            )
        except OSError as exc:
            print(f"[Chill] Could not copy Rust binary: {exc}")
            return False, None

        return True, command_name


    def _bundle_node(
        self,
        source: Path,
        bin_dir: Path,
        command_name: str,
    ) -> tuple[bool, str | None]:
        """Install Node dependencies inside the bundle."""

        if not command_exists("npm"):
            print("[Chill] npm is required.")
            return False, None

        try:
            subprocess.run(
                ["npm", "install"],
                cwd=str(source),
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"[Chill] npm installation failed: {exc}")
            return False, None

        package_file = source / "package.json"

        try:
            package = json.loads(
                package_file.read_text()
            )

            bins = package.get("bin", {})

            if isinstance(bins, str):
                bins = {command_name: bins}

            registered = False

            for name, relative in bins.items():
                executable = source / relative

                if executable.is_file():
                    destination = bin_dir / name

                    if destination.exists():
                        destination.unlink()

                    destination.symlink_to(executable)
                    registered = True

            return registered, command_name if registered else None

        except (OSError, json.JSONDecodeError) as exc:
            print(f"[Chill] Node metadata error: {exc}")
            return False, None


    def _install_github_bundle(
        self,
        repo: dict,
    ) -> bool:
        """Clone, build, isolate and register a GitHub tool bundle."""

        full_name = repo.get("name", "")
        clone_url = repo.get("clone_url", "")

        if not full_name or not clone_url:
            print("[Chill] Invalid GitHub repository.")
            return False

        command_name = (
            full_name.split("/", 1)[-1]
            .strip()
            .lower()
            .replace("_", "-")
        )

        bundle = self.tools_dir / command_name
        source = bundle / "source"
        bin_dir = bundle / "bin"
        deps = bundle / "deps"

        # Existing bundle: never clone again.
        if (bundle / "chill.json").is_file():
            print(f"[Chill] Existing ChillOS bundle: {bundle}")

            metadata = json.loads(
                (bundle / "chill.json").read_text()
            )

            executable = (
                bundle
                / metadata.get(
                    "executable",
                    f"bin/{command_name}",
                )
            )

            if executable.exists():
                self._bundle_register(
                    bundle,
                    executable,
                    command_name,
                )
                print(f"[✓] Tool ready: {command_name}")
                return True

        bundle.mkdir(parents=True, exist_ok=True)
        bin_dir.mkdir(parents=True, exist_ok=True)
        deps.mkdir(parents=True, exist_ok=True)

        # Migrate an existing flat GitHub repository into source/.
        # Never rename the bundle into a directory inside itself.
        if not source.exists() and (bundle / ".git").exists():
            print("[Chill] Migrating existing repository into source/")

            try:
                source.mkdir(parents=True, exist_ok=True)

                protected = {
                    "bin",
                    "deps",
                    "source",
                    "chill.json",
                }

                for item in list(bundle.iterdir()):
                    if item.name in protected:
                        continue

                    shutil.move(
                        str(item),
                        str(source / item.name),
                    )

                print("[✓] Existing repository migrated.")

            except OSError as exc:
                print(f"[Chill] Migration failed: {exc}")
                return False

        if not (source / ".git").exists():
            if not command_exists("git"):
                print("[Chill] Git is required.")

                try:
                    self.install_native("git")
                except Exception as exc:
                    print(f"[Chill] Unable to install git: {exc}")
                    return False

            print(f"[Chill] Downloading {full_name}...")

            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        "--single-branch",
                        clone_url,
                        str(source),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                print(f"[Chill] Git clone failed: {exc}")
                shutil.rmtree(bundle, ignore_errors=True)
                return False

        print(f"[Chill] Source: {source}")

        # Detect project type.
        if (source / "go.mod").is_file():
            tool_type = "go"

            print("[Chill] Go project detected.")

            ok, executable_name = self._bundle_go(
                source,
                bin_dir,
                command_name,
            )

        elif (
            (source / "requirements.txt").is_file()
            or (source / "pyproject.toml").is_file()
            or (source / "setup.py").is_file()
        ):
            tool_type = "python"

            print("[Chill] Python project detected.")

            ok, executable_name = self._bundle_python(
                source,
                deps,
                bin_dir,
            )

            if ok:
                # Prefer a command matching the repository name.
                candidate = bin_dir / command_name

                if candidate.exists():
                    executable_name = command_name

        elif (source / "Cargo.toml").is_file():
            tool_type = "rust"

            print("[Chill] Rust project detected.")

            ok, executable_name = self._bundle_rust(
                source,
                bin_dir,
                command_name,
            )

        elif (source / "package.json").is_file():
            tool_type = "node"

            print("[Chill] Node.js project detected.")

            ok, executable_name = self._bundle_node(
                source,
                bin_dir,
                command_name,
            )

        else:
            print("[Chill] Unsupported project type.")
            print(
                "[Chill] Repository was downloaded but "
                "not marked as installed."
            )
            return False

        if not ok:
            return False

        if not executable_name:
            print("[Chill] No executable was produced.")
            return False

        executable = bin_dir / executable_name

        if not executable.exists():
            print(
                f"[Chill] Expected executable missing: "
                f"{executable}"
            )
            return False

        if not self._bundle_register(
            bundle,
            executable,
            command_name,
        ):
            return False

        self._bundle_metadata(
            bundle,
            repo,
            tool_type,
            executable_name,
        )

        print()
        print(f"[✓] Installed: {full_name}")
        print(f"[✓] Bundle   : {bundle}")
        print(f"[✓] Command  : {command_name}")
        print(f"[✓] Executable: {executable}")

        return True


    def install_github_repository(self, repo: dict) -> bool:
        """Install a GitHub repository as a self-contained ChillOS bundle."""
        return self._install_github_bundle(repo)


    def github_fallback(self, package: str) -> bool:
        """Search GitHub and interactively install a selected tool."""

        print()
        print(f"[Chill] '{package}' was not found as a native package.")
        print(f"[Chill] Searching GitHub for '{package}'...")

        candidates = self.github_search(package)

        selected = self.select_github_repository(
            package,
            candidates,
        )

        if selected is None:
            return False

        return self.install_github_repository(selected)


    def install(self, name: str) -> bool:
        """Install a package using recipe, native package, or GitHub fallback."""

        print(f"[Chill] Installing: {name}")
        print(
            f"[Chill] Platform: {self.system.os_name} "
            f"{self.system.architecture}"
        )

        # 1. ChillOS recipe.
        if self.recipe_exists(name):
            print(
                f"[Chill] Recipe: "
                f"{self.recipe_dir / (name + '.py')}"
            )

            try:
                recipe = self.recipe_path(name)
                if recipe is None:
                    raise RuntimeError(
                        f"Recipe disappeared before installation: {name}"
                    )

                self.run_recipe(name, recipe)
                return True
            except Exception as exc:
                print(f"[Chill] Recipe failed: {exc}")
                return False

        # 2. Native package.
        if self.native_package_available(name):
            print("[Chill] Native package found.")

            try:
                self.install_native(name)
                return True
            except Exception as exc:
                print(f"[Chill] Native installation failed: {exc}")

        # 3. GitHub fallback.
        return self.github_fallback(name)


    def run_recipe(self, name: str, path: Path) -> None:
        spec = importlib.util.spec_from_file_location(
            f"chill_recipe_{name}",
            path,
        )

        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"Cannot load recipe: {name}"
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        install = getattr(module, "install", None)

        if not callable(install):
            raise RuntimeError(
                f"Recipe '{name}' has no install(manager) function."
            )

        install(self)
