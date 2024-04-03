import argparse
import dataclasses
import pathlib
import re
import typing

import ruamel.yaml


def remove_set_commands(content: str) -> str:
    return re.sub(r"^\s*(set -[eux])\n\s*", "", content, flags=re.MULTILINE)


def remove_shebang(content: str) -> str:
    return re.sub(r"^\s*#!.*\n\s*", "", content)


class ScriptContentProcessor:
    def __init__(self, *transformers: typing.Callable[[str], str]):
        self.transformers = transformers

    def process(self, content: str) -> str:
        for transformer in self.transformers:
            content = transformer(content)
        return ruamel.yaml.scalarstring.PreservedScalarString(content)


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


@dataclasses.dataclass
class ScriptData:
    app_name: str
    install_method: str
    script_type: str
    script_content: str


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
    ) -> ScriptData:
        script_name_parts = script_path.stem.split("-", 1)
        app_name = (
            script_name_parts[1] if len(script_name_parts) > 1 else script_path.stem
        )
        install_method = grouping_fn(script_path)
        script_content = script_path.read_text()
        script_content = self.content_processor.process(script_content)
        script_type = self.script_type_detector(script_path)
        return ScriptData(app_name, install_method, script_type, script_content)


class ScriptProcessor:
    def __init__(
        self,
        outfile: str,
        script_data_extractor: ScriptDataExtractor,
        content_processor: ScriptContentProcessor,
    ):
        self.outfile = pathlib.Path(outfile)
        self.script_data_extractor = script_data_extractor
        self.content_processor = content_processor
        self.errors_and_warnings: typing.List[str] = []
        self.processed_script_count: int = 0

    def process_script(
        self,
        script_path: pathlib.Path,
        grouping_fn: typing.Callable[[pathlib.Path], str],
        apps_data: typing.Dict[str, typing.Dict[str, typing.Any]],
    ) -> None:
        script_data = self.script_data_extractor.extract(script_path, grouping_fn)
        if script_data.app_name in apps_data:
            self.errors_and_warnings.append(
                f"Warning: Duplicate app name found - {script_data.app_name}\n"
                f"Skipping script: {script_path}"
            )
            return

        apps_data[script_data.app_name] = {
            "name": script_data.app_name,
            "install_methods": [
                {
                    "type": script_data.install_method,
                    "script_type": script_data.script_type,
                    "script": script_data.script_content,
                }
            ],
        }
        self.processed_script_count += 1

    def process_scripts(
        self,
        script_paths: typing.List[pathlib.Path],
        grouping_fn: typing.Callable[[pathlib.Path], str],
    ) -> None:
        apps_data = {}
        for script_path in script_paths:
            self.process_script(script_path, grouping_fn, apps_data)

        apps = list(apps_data.values())
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        with open(self.outfile, "w") as f:
            yaml.dump(
                {
                    "apps": apps,
                },
                f,
            )

        if self.errors_and_warnings:
            print("Errors and Warnings:")
            for message in self.errors_and_warnings:
                print(message)

    def get_processed_script_count(self) -> int:
        return self.processed_script_count


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

    if re.search(r"\bon-linux\b", script_path.name):
        return "any"
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
    content_processor = ScriptContentProcessor(remove_shebang, remove_set_commands)
    script_data_extractor = ScriptDataExtractor(content_processor, detect_script_type)
    script_processor = ScriptProcessor(
        "scripts.yaml", script_data_extractor, content_processor
    )

    script_processor.process_scripts(
        script_paths=script_paths,
        grouping_fn=group_by_install_method,
    )

    script_count = script_processor.get_processed_script_count()
    print(f"Processed {script_count} script(s) to {script_processor.outfile.resolve()}")


if __name__ == "__main__":
    main()
