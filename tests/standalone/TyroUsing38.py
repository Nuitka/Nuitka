#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-skip-unless-imports: tyro

# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=source-inclusion
# nuitka-project: --source-inclusion-args="small --help"
# nuitka-project: --source-inclusion-args="large --help"

# spell-checker: disable

import sys
from dataclasses import dataclass, field

import tyro
from tyro import _docstrings


@dataclass
class BaseTrainerConfig(object):
    """Base trainer settings."""

    name: str = "base"
    """Base trainer name."""


@dataclass
class MachineConfig(object):
    """Machine settings."""

    workers: int = 4
    """Number of workers."""


@dataclass
class LoggingConfig(object):
    """Logging settings."""

    output_dir: str = "logs"
    """Output directory for logs."""


@dataclass
class SmallTrainerConfig(BaseTrainerConfig):
    """Small trainer settings."""

    machine: MachineConfig = field(default_factory=MachineConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    steps: int = 100
    """Number of training steps."""


@dataclass
class LargeTrainerConfig(BaseTrainerConfig):
    """Large trainer settings."""

    machine: MachineConfig = field(default_factory=MachineConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    precision: str = "fp16"
    """Numeric precision for the large trainer."""


AnnotatedBaseConfigUnion = tyro.conf.SuppressFixed[
    tyro.conf.FlagConversionOff[
        tyro.extras.subcommand_type_from_defaults(
            {
                "small": SmallTrainerConfig(name="small", steps=25),
                "large": LargeTrainerConfig(name="large", precision="bf16"),
            },
            prefix_names=False,
        )
    ]
]


def main():
    args = sys.argv[1:]

    if not args:
        args = ["small"]

    config = tyro.cli(AnnotatedBaseConfigUnion, args=args)

    steps_doc = _docstrings.get_field_docstring(SmallTrainerConfig, "steps", ())
    precision_doc = _docstrings.get_field_docstring(LargeTrainerConfig, "precision", ())
    workers_doc = _docstrings.get_field_docstring(MachineConfig, "workers", ())

    assert steps_doc == "Number of training steps.", steps_doc
    assert precision_doc == "Numeric precision for the large trainer.", precision_doc
    assert workers_doc == "Number of workers.", workers_doc

    print("Trainer:", config.name, type(config).__name__)
    print("Steps doc:", steps_doc)
    print("Precision doc:", precision_doc)
    print("Workers doc:", workers_doc)
    print("OK.")


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
