# (C) Copyright 2024 Hewlett Packard Enterprise Development LP
# Author: Jean Snyman <jean.snyman@hpe.com>
# Author: Supreshna Gurung <supreshna.gurung@hpe.com>
# SPDX-License-Identifier: Apache-2.0

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import subprocess
import platform

from importlib.metadata import version


class OutputHelpers:
    @staticmethod
    def print_dependency_info():
        curl_conf_proc = subprocess.run(["curl-config", "--version"], capture_output=True)
        libcurl_version = curl_conf_proc.stdout.decode("utf-8").strip().split()[1]

        dep_versions = {
            "python": platform.python_version(),
            "tornado": version("tornado"),
            "pycurl": version("pycurl"),
            "libcurl": libcurl_version,
            "sqlalchemy": version("sqlalchemy")
        }

        optional_deps = ["psycopg2", "psycopg", "mysqlclient", "pymysql"]

        for dep in optional_deps:
            try:
                dep_versions[dep] = version(dep)
            except Exception:
                continue

        output = "Using dependencies: "
        output += ", ".join([ f"{dep} v{ver}" for dep, ver in dep_versions.items() ])
        print(output)

    @staticmethod
    def format_duration(seconds):
        if seconds < 0.000001:
            return f"{round(seconds*1000000000, None)}ns"
        elif seconds < 0.001:
            return f"{round(seconds*1000000, None)}μs"
        elif seconds < 1:
            return f"{round(seconds*1000, None)}ms"
        elif seconds < 60:
            return f"{round(seconds, 1)}s"
        elif seconds < 3600:
            return f"{round(seconds/60, 1)}m"
        else:
            return f"{round(seconds/3600, 1)}h"

    @staticmethod
    def format_count(number, singular, plural):
        return f"{number} {singular}" if number == 1 else f"{number} {plural}"

    @staticmethod
    def center(content, width):
        line_template = "{:^" + str(width) + "}"
        return "\n".join([line_template.format(line) for line in content.splitlines()])


class Table:
    def __init__(self, *col_templates):
        self._col_templates = col_templates
        self._output = ""

        self._row_template = "  ".join(["{:" + col_template + "}" for col_template in self.col_templates])

    def _append_row(self, *cells):
        if self._output:
            self._output += "\n"

        cells = [str(cell) for cell in cells]

        self._output += self.row_template.format(*cells)

    def head(self, *col_labels):
        col_labels = list(col_labels)
        borders = []

        if len(col_labels) > self.col_count:
            raise ValueError("number of column labels exceeds the number of columns in the table")

        for i in range(self.col_count - len(col_labels)):
            col_labels.append("")
        
        for col_index, col_label in enumerate(col_labels):
            if col_label:
                borders.append("-" * self.col_sizes[col_index])
            else:
                borders.append("")

        self._append_row(*col_labels)
        self._append_row(*borders)
        
        return self

    def row(self, *rows):
        rows = list(rows)

        if len(rows) > self.col_count:
            raise ValueError("number of cells exceeds the number of columns in the table")

        for i in range(self.col_count - len(rows)):
            rows.append("")

        self._append_row(*rows)

        return self

    def percents(self, *cells):
        formatted_cells = []

        for cell in cells:
            if isinstance(cell, (float, int)):
                percent = round(cell * 100, 1)
                formatted_cells.append(f"{percent}%")
            elif cell is None:
                formatted_cells.append("--")
            else:
                formatted_cells.append(cell)

        return self.row(*formatted_cells)

    def times(self, *cells):
        formatted_cells = []

        for cell in cells:
            if isinstance(cell, (float, int)):
                duration = OutputHelpers.format_duration(cell)
                formatted_cells.append(duration)
            elif cell is None:
                formatted_cells.append("--")
            else:
                formatted_cells.append(cell)

        return self.row(*formatted_cells)

    def decimals(self, *cells):
        formatted_cells = []

        for cell in cells:
            if isinstance(cell, (float, int)):
                num = round(cell, 1)
                formatted_cells.append(f"{num}")
            elif cell is None:
                formatted_cells.append("--")
            else:
                formatted_cells.append(cell)

        return self.row(*formatted_cells)

    def integers(self, *cells):
        formatted_cells = []

        for cell in cells:
            if isinstance(cell, (float, int)):
                num = int(round(cell, 0))
                formatted_cells.append(f"{num}")
            elif cell is None:
                formatted_cells.append("--")
            else:
                formatted_cells.append(cell)

        return self.row(*formatted_cells)

    def print(self):
        print(self.output)

    @property
    def col_templates(self):
        return self._col_templates

    @property
    def col_sizes(self):
        return [int(col_template[1:]) for col_template in self.col_templates]

    @property
    def col_count(self):
        return len(self.col_templates)

    @property
    def row_template(self):
        return self._row_template

    @property
    def output(self):
        return self._output


class ColumnGroup:
    def __init__(self, border=True):
        self._title = None
        self._title_alignment = "<"
        self._border = border

        self._columns = []

    def set_title(self, title, alignment="<"):
        self._title = title
        self._title_alignment = alignment
        
        return self

    def add(self, column):
        if isinstance(column, Table):
            column = column.output

        if isinstance(column, ColumnGroup):
            column = column.get_embed()

        self._columns.append(column)

        return self

    def _horizontal(self, lines):
        first_line = lines[0]
        border = ["─" * len(part) for part in first_line]
        return border

    def _make_header(self, lines):
        if not self.title or not self.title_alignment:
            return

        if not self.border:
            lines.insert(0, [title])
            return

        border = self._horizontal(lines)

        first_line = lines[0]
        title_length = sum([len(part) for part in first_line])
        title_template = "{:" + self.title_alignment + str(title_length) + "}"
        title = title_template.format(self.title)

        lines.insert(0, border)
        lines.insert(1, [title])

    def _make_outer_horizontals(self, lines):
        if not self.border:
            return

        border = self._horizontal(lines)
        lines.insert(0, border)
        lines.append(border)

    def _make_inner_verticals(self, lines):
        for line_i, line in enumerate(lines.copy()):
            updated_line = []

            for part_i, part in enumerate(line[:-1]):
                if part[-1] == "─":
                    if line_i == 0:
                        separator = "─┬─"
                    elif line_i == len(lines) - 1:
                        separator = "─┴─"
                    elif line[part_i + 1][0] == "─":
                        separator = "─┼─"
                    else:
                        separator = "─┤ "
                else:
                    separator = " │ " if self.border else "   "
                
                updated_line.append(part)
                updated_line.append(separator)

            updated_line.append(line[-1])
            lines[line_i] = updated_line

    def _make_outer_verticals(self, lines):
        for line_i, line in enumerate(lines.copy()):
            first_part = line[0]
            last_part = line[-1]

            if first_part[0] == "─":
                if line_i == 0:
                    left_edge = "  ┌─"
                elif line_i == len(lines) - 1:
                    left_edge = "  └─"
                else:
                    left_edge = "  ├─"
            else:
                left_edge = "  │ " if self.border else "  "

            if last_part[-1] == "─":
                if line_i == 0:
                    right_edge = "─┐"
                elif line_i == len(lines) - 1:
                    right_edge = "─┘"
                else:
                    right_edge = "─┤"
            else:
                right_edge = " │" if self.border else ""

            lines[line_i] = [left_edge, *line, right_edge]

    def get_output(self):
        columns = [column.splitlines() for column in self.columns]
        lines = [list(line) for line in zip(*columns)]
        self._make_outer_horizontals(lines)
        self._make_inner_verticals(lines)
        self._make_header(lines)
        self._make_outer_verticals(lines)
        
        joined_lines = ["".join(line) for line in lines]
        return "\n".join(joined_lines)

    def get_embed(self):
        columns = [column.splitlines() for column in self.columns]
        lines = [list(line) for line in zip(*columns)]
        self._make_outer_horizontals(lines)
        self._make_header(lines)
        lines = lines[1:-1]
        
        joined_lines = ["".join(line) for line in lines]
        return "\n".join(joined_lines)

    def print(self):
        print(self.get_output())

    @property
    def title(self):
        return self._title

    @property
    def title_alignment(self):
        return self._title_alignment

    @property
    def border(self):
        return self._border

    @property
    def columns(self):
        return self._columns.copy()