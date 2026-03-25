"""Tests for the file_utils module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from zipfile import ZipFile

from jammy.file_utils import (
    FileCompressor,
    get_files,
    load_jsonl,
    timeit,
    write_to_file,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestWriteToFile:
    """Tests for write_to_file."""

    def test_write_to_file_string(self, tmp_path: Path) -> None:
        """Test writing a plain string to a file."""
        path = tmp_path / "test.txt"
        write_to_file(path, "hello world")
        assert path.read_text() == "hello world"

    def test_write_to_file_dict_json(self, tmp_path: Path) -> None:
        """Test writing a dict as JSON."""
        path = tmp_path / "test.json"
        write_to_file(path, {"key": "value"})
        assert json.loads(path.read_text()) == {"key": "value"}

    def test_write_to_file_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created automatically."""
        path = tmp_path / "a" / "b" / "c" / "test.txt"
        write_to_file(path, "nested")
        assert path.read_text() == "nested"

    def test_write_to_file_non_string_converted(self, tmp_path: Path) -> None:
        """Test that non-string content is converted to string."""
        path = tmp_path / "test.txt"
        write_to_file(path, 42)
        assert path.read_text() == "42"


class TestGetFiles:
    """Tests for get_files."""

    def test_get_files_matches_extension(self, tmp_path: Path) -> None:
        """Test that only files with the specified extension are returned."""
        (tmp_path / "a.txt").touch()
        (tmp_path / "b.txt").touch()
        (tmp_path / "c.py").touch()
        result = get_files(tmp_path, "txt")
        assert len(result) == 2
        assert all(f.suffix == ".txt" for f in result)

    def test_get_files_recursive(self, tmp_path: Path) -> None:
        """Test recursive file search in subdirectories."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "top.txt").touch()
        (sub / "nested.txt").touch()
        result = get_files(tmp_path, "txt", recursive=True)
        assert len(result) == 2

    def test_get_files_no_matches(self, tmp_path: Path) -> None:
        """Test that an empty list is returned when no files match."""
        (tmp_path / "a.py").touch()
        result = get_files(tmp_path, "txt")
        assert result == []


class TestLoadJsonl:
    """Tests for load_jsonl."""

    def test_load_jsonl_reads_lines(self, tmp_path: Path) -> None:
        """Test reading a JSONL file with multiple lines."""
        path = tmp_path / "data.jsonl"
        lines = [{"a": 1}, {"b": 2}, {"c": 3}]
        path.write_text("\n".join(json.dumps(line) for line in lines))
        result = load_jsonl(path)
        assert len(result) == 3
        assert result[0] == {"a": 1}

    def test_load_jsonl_empty_file(self, tmp_path: Path) -> None:
        """Test reading an empty JSONL file."""
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        result = load_jsonl(path)
        assert result == []


class TestTimeit:
    """Tests for timeit decorator."""

    def test_timeit_preserves_return_value(self) -> None:
        """Test that the decorator does not alter the function's return value."""

        @timeit
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert add(2, 3) == 5

    def test_timeit_preserves_function_name(self) -> None:
        """Test that @functools.wraps preserves the original function name."""

        @timeit
        def my_function() -> None:
            """Do nothing."""

        assert my_function.__name__ == "my_function"


class TestFileCompressor:
    """Tests for FileCompressor."""

    def test_zip_file_creates_zip(self, tmp_path: Path) -> None:
        """Test compressing a single file to zip."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        txt_file = input_dir / "test.txt"
        txt_file.write_text("content")

        compressor = FileCompressor(input_dir, output_dir)
        compressor.zip_file(txt_file)

        zip_path = output_dir / "test.zip"
        assert zip_path.exists()
        assert not txt_file.exists()  # original deleted

    def test_unzip_file_extracts(self, tmp_path: Path) -> None:
        """Test extracting a single zip file."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create a zip
        zip_path = input_dir / "test.zip"
        with ZipFile(zip_path, "w") as zf:
            zf.writestr("hello.txt", "world")

        compressor = FileCompressor(input_dir, output_dir)
        compressor.unzip_file(zip_path)

        assert (output_dir / "hello.txt").read_text() == "world"
