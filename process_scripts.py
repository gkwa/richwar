import argparse
import pathlib
import re
import typing

import ruamel.yaml


class ShebangRemover:
    def __init__(self, remove_enabled: bool = True):
        self.remove_enabled = remove_enabled

    def remove_shebang(self, content: str) -> str:
        if self.remove_enabled:
            return re.sub(r"^\s*#!.*\n\s*", "", content)
        else:
            return content


class ScriptContentProcessor:
    def __init__(self, shebang_remover: ShebangRemover):
        self.shebang_remover = shebang_remover

    def process(self, content: str) -> str:
        processed_content = self.shebang_remover.remove_shebang(content)
        return ruamel.yaml.scalarstring.PreservedScalarString(processed_content)


class ScriptPathCollector:
    def collect(
        self, basedir: pathlib.Path, *extensions: str
    ) -> typing.List[pathlib.Path]:
        files = []
        for ext in extensions:
            files.extend(basedir.glob(f"*{ext}"))
        return files


def detect_script_type(script_path: pathlib.Path) -> str:
    if script_path.suffix == ".sh":
        return "bash"
    elif script_path.suffix == ".ps1":
        return "powershell"
    else:
        # If neither .sh nor .ps1, we need to parse the script content to determine the type
        # Here, you can implement your logic to parse the script content and determine the type
        # For now, let's assume it's bash if neither .sh nor .ps1
        return "bash"


class ScriptDataExtractor:
    def __init__(
        self,
        content_processor: ScriptContentProcessor,
        script_type_detector: typing.Callable[[pathlib.Path], str],
    ):
        self.content_processor = content_processor
        self.script_type_detector = script_type_detector

    def extract(
        self,
        script_path: pathlib.Path,
        grouping_fn: typing.Callable[[pathlib.Path], str],
    ) -> typing.Tuple[str, str, str]:
        script_name_parts = script_path.stem.split("-", 1)
        app_name = (
            script_name_parts[1] if len(script_name_parts) > 1 else script_path.stem
        )
        install_method = grouping_fn(script_path)
        script_content = script_path.read_text()
        script_content = self.content_processor.process(script_content)
        script_type = self.script_type_detector(script_path)
        return app_name, install_method, script_type, script_content


class ScriptProcessor:
    def __init__(
        self,
        script_data_extractor: ScriptDataExtractor,
        content_processor: ScriptContentProcessor,
    ):
        self.script_data_extractor = script_data_extractor
        self.content_processor = content_processor

    def process_scripts(
        self,
        script_paths: typing.List[pathlib.Path],
        grouping_fn: typing.Callable[[pathlib.Path], str],
    ) -> None:
        apps_data = {}
        for script_path in script_paths:
            (
                app_name,
                install_method,
                script_type,
                script_content,
            ) = self.script_data_extractor.extract(script_path, grouping_fn)
            if app_name not in apps_data:
                apps_data[app_name] = {
                    "name": app_name,
                    "install_methods": [],
                }
            apps_data[app_name]["install_methods"].append(
                {
                    "type": install_method,
                    "script_type": script_type,
                    "script": script_content,
                }
            )

        apps = list(apps_data.values())
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open("scripts.yaml", "w") as f:
            yaml.dump(
                {
                    "apps": apps,
                },
                f,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--basedir",
        type=pathlib.Path,
        required=True,
        help="Base directory containing script files",
    )
    return parser.parse_args()


def group_by_install_method(script_path: pathlib.Path) -> str:
    content = script_path.read_text()
    if re.search(r"\bapt\b", content):
        return "apt"
    elif re.search(r"\bpip3?\b", content):
        return "pip"
    elif re.search(r"\byum\b", content):
        return "yum"
    elif re.search(r"\bbrew\b", content):
        return "homebrew"
    elif re.search(r"\bcurl\b", content):
        return "curl"
    else:
        return "other"


def main() -> None:
    args = parse_args()
    script_path_collector = ScriptPathCollector()
    script_paths = script_path_collector.collect(args.basedir, ".sh", ".ps1")
    shebang_remover = ShebangRemover()
    content_processor = ScriptContentProcessor(shebang_remover)
    script_data_extractor = ScriptDataExtractor(content_processor, detect_script_type)
    script_processor = ScriptProcessor(script_data_extractor, content_processor)

    script_processor.process_scripts(
        script_paths=script_paths,
        grouping_fn=group_by_install_method,
    )


if __name__ == "__main__":
    main()
