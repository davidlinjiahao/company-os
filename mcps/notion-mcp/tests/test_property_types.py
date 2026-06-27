"""Tests for property type builders and parsers."""

from notion_mcp.property_types import (
    build_title,
    build_rich_text,
    build_number,
    build_select,
    build_multi_select,
    build_date,
    build_checkbox,
    build_url,
    build_email,
    build_phone_number,
    build_status,
    build_files,
    build_relation,
    build_people,
    build_properties_from_schema,
    parse_property_value,
    parse_all_properties,
    READ_ONLY_PROPERTIES,
)


# --- Builder tests ---


class TestBuildTitle:
    def test_basic(self):
        result = build_title("Hello")
        assert result == {"title": [{"text": {"content": "Hello"}}]}

    def test_empty(self):
        result = build_title("")
        assert result == {"title": [{"text": {"content": ""}}]}


class TestBuildRichText:
    def test_basic(self):
        result = build_rich_text("Some text")
        assert result == {"rich_text": [{"text": {"content": "Some text"}}]}


class TestBuildNumber:
    def test_integer(self):
        assert build_number(42) == {"number": 42}

    def test_float(self):
        assert build_number(3.14) == {"number": 3.14}

    def test_zero(self):
        assert build_number(0) == {"number": 0}


class TestBuildSelect:
    def test_basic(self):
        assert build_select("High") == {"select": {"name": "High"}}


class TestBuildMultiSelect:
    def test_multiple(self):
        result = build_multi_select(["A", "B", "C"])
        assert result == {"multi_select": [{"name": "A"}, {"name": "B"}, {"name": "C"}]}

    def test_empty(self):
        assert build_multi_select([]) == {"multi_select": []}

    def test_single(self):
        assert build_multi_select(["X"]) == {"multi_select": [{"name": "X"}]}


class TestBuildDate:
    def test_start_only(self):
        result = build_date("2026-01-15")
        assert result == {"date": {"start": "2026-01-15"}}

    def test_start_and_end(self):
        result = build_date("2026-01-15", "2026-01-20")
        assert result == {"date": {"start": "2026-01-15", "end": "2026-01-20"}}

    def test_end_none(self):
        result = build_date("2026-01-15", None)
        assert result == {"date": {"start": "2026-01-15"}}


class TestBuildCheckbox:
    def test_true(self):
        assert build_checkbox(True) == {"checkbox": True}

    def test_false(self):
        assert build_checkbox(False) == {"checkbox": False}


class TestBuildUrl:
    def test_basic(self):
        assert build_url("https://example.com") == {"url": "https://example.com"}


class TestBuildEmail:
    def test_basic(self):
        assert build_email("test@example.com") == {"email": "test@example.com"}


class TestBuildPhoneNumber:
    def test_basic(self):
        assert build_phone_number("+1234567890") == {"phone_number": "+1234567890"}


class TestBuildStatus:
    def test_basic(self):
        assert build_status("In Progress") == {"status": {"name": "In Progress"}}


class TestBuildFiles:
    def test_single(self):
        result = build_files(["https://example.com/file.pdf"])
        assert len(result["files"]) == 1
        assert result["files"][0]["type"] == "external"
        assert result["files"][0]["external"]["url"] == "https://example.com/file.pdf"
        assert result["files"][0]["name"] == "file.pdf"

    def test_multiple(self):
        result = build_files(["https://a.com/1.pdf", "https://b.com/2.png"])
        assert len(result["files"]) == 2

    def test_empty(self):
        assert build_files([]) == {"files": []}


class TestBuildRelation:
    def test_basic(self):
        result = build_relation(["id1", "id2"])
        assert result == {"relation": [{"id": "id1"}, {"id": "id2"}]}

    def test_empty(self):
        assert build_relation([]) == {"relation": []}


class TestBuildPeople:
    def test_basic(self):
        result = build_people(["user1", "user2"])
        assert result == {"people": [{"id": "user1"}, {"id": "user2"}]}


# --- build_properties_from_schema tests ---


class TestBuildPropertiesFromSchema:
    def test_basic_types(self):
        schema = {
            "Name": {"type": "title"},
            "Notes": {"type": "rich_text"},
            "Score": {"type": "number"},
        }
        values = {"Name": "Test", "Notes": "Hello", "Score": 42}
        result = build_properties_from_schema(schema, values)
        assert result["Name"] == {"title": [{"text": {"content": "Test"}}]}
        assert result["Notes"] == {"rich_text": [{"text": {"content": "Hello"}}]}
        assert result["Score"] == {"number": 42}

    def test_skips_unknown_properties(self):
        schema = {"Name": {"type": "title"}}
        values = {"Name": "Test", "Unknown": "skip me"}
        result = build_properties_from_schema(schema, values)
        assert "Unknown" not in result
        assert "Name" in result

    def test_skips_read_only_properties(self):
        schema = {
            "Name": {"type": "title"},
            "Created": {"type": "created_time"},
            "Formula": {"type": "formula"},
        }
        values = {"Name": "Test", "Created": "2026-01-01", "Formula": "x"}
        result = build_properties_from_schema(schema, values)
        assert "Name" in result
        assert "Created" not in result
        assert "Formula" not in result

    def test_date_as_string(self):
        schema = {"Due": {"type": "date"}}
        values = {"Due": "2026-01-15"}
        result = build_properties_from_schema(schema, values)
        assert result["Due"] == {"date": {"start": "2026-01-15"}}

    def test_date_as_dict(self):
        schema = {"Due": {"type": "date"}}
        values = {"Due": {"start": "2026-01-15", "end": "2026-01-20"}}
        result = build_properties_from_schema(schema, values)
        assert result["Due"] == {"date": {"start": "2026-01-15", "end": "2026-01-20"}}

    def test_date_dict_missing_start(self):
        schema = {"Due": {"type": "date"}}
        values = {"Due": {"end": "2026-01-20"}}
        result = build_properties_from_schema(schema, values)
        assert result["Due"] == {"date": {"start": "", "end": "2026-01-20"}}

    def test_empty_values(self):
        schema = {"Name": {"type": "title"}}
        result = build_properties_from_schema(schema, {})
        assert result == {}


# --- Parser tests ---


class TestParsePropertyValue:
    def test_title(self):
        prop = {"type": "title", "title": [{"plain_text": "Hello"}, {"plain_text": " World"}]}
        assert parse_property_value(prop) == "Hello World"

    def test_title_empty(self):
        prop = {"type": "title", "title": []}
        assert parse_property_value(prop) == ""

    def test_rich_text(self):
        prop = {"type": "rich_text", "rich_text": [{"plain_text": "content"}]}
        assert parse_property_value(prop) == "content"

    def test_number(self):
        assert parse_property_value({"type": "number", "number": 42}) == 42

    def test_number_none(self):
        assert parse_property_value({"type": "number", "number": None}) is None

    def test_select(self):
        prop = {"type": "select", "select": {"name": "High"}}
        assert parse_property_value(prop) == "High"

    def test_select_none(self):
        prop = {"type": "select", "select": None}
        assert parse_property_value(prop) is None

    def test_multi_select(self):
        prop = {"type": "multi_select", "multi_select": [{"name": "A"}, {"name": "B"}]}
        assert parse_property_value(prop) == ["A", "B"]

    def test_date(self):
        prop = {"type": "date", "date": {"start": "2026-01-15", "end": None}}
        assert parse_property_value(prop) == {"start": "2026-01-15", "end": None}

    def test_date_none(self):
        prop = {"type": "date", "date": None}
        assert parse_property_value(prop) is None

    def test_checkbox_true(self):
        assert parse_property_value({"type": "checkbox", "checkbox": True}) is True

    def test_checkbox_false(self):
        assert parse_property_value({"type": "checkbox", "checkbox": False}) is False

    def test_url(self):
        prop = {"type": "url", "url": "https://example.com"}
        assert parse_property_value(prop) == "https://example.com"

    def test_email(self):
        prop = {"type": "email", "email": "test@example.com"}
        assert parse_property_value(prop) == "test@example.com"

    def test_phone_number(self):
        prop = {"type": "phone_number", "phone_number": "+1234"}
        assert parse_property_value(prop) == "+1234"

    def test_status(self):
        prop = {"type": "status", "status": {"name": "Done"}}
        assert parse_property_value(prop) == "Done"

    def test_status_none(self):
        prop = {"type": "status", "status": None}
        assert parse_property_value(prop) is None

    def test_files_external(self):
        prop = {"type": "files", "files": [{"type": "external", "external": {"url": "https://a.com/f.pdf"}}]}
        assert parse_property_value(prop) == ["https://a.com/f.pdf"]

    def test_files_internal(self):
        prop = {"type": "files", "files": [{"type": "file", "file": {"url": "https://notion.so/f.pdf"}}]}
        assert parse_property_value(prop) == ["https://notion.so/f.pdf"]

    def test_relation(self):
        prop = {"type": "relation", "relation": [{"id": "abc"}, {"id": "def"}]}
        assert parse_property_value(prop) == ["abc", "def"]

    def test_people(self):
        prop = {"type": "people", "people": [{"id": "user1"}]}
        assert parse_property_value(prop) == ["user1"]

    def test_formula_number(self):
        prop = {"type": "formula", "formula": {"type": "number", "number": 100}}
        assert parse_property_value(prop) == 100

    def test_formula_string(self):
        prop = {"type": "formula", "formula": {"type": "string", "string": "hello"}}
        assert parse_property_value(prop) == "hello"

    def test_created_time(self):
        prop = {"type": "created_time", "created_time": "2026-01-15T00:00:00Z"}
        assert parse_property_value(prop) == "2026-01-15T00:00:00Z"

    def test_created_by(self):
        prop = {"type": "created_by", "created_by": {"id": "user1"}}
        assert parse_property_value(prop) == "user1"

    def test_unique_id_with_prefix(self):
        prop = {"type": "unique_id", "unique_id": {"prefix": "TASK-", "number": 42}}
        assert parse_property_value(prop) == "TASK-42"

    def test_unique_id_without_prefix(self):
        prop = {"type": "unique_id", "unique_id": {"prefix": "", "number": 7}}
        assert parse_property_value(prop) == "7"

    def test_unknown_type(self):
        prop = {"type": "new_fancy_type"}
        assert parse_property_value(prop) is None


class TestParseAllProperties:
    def test_multiple(self):
        props = {
            "Name": {"type": "title", "title": [{"plain_text": "Test"}]},
            "Score": {"type": "number", "number": 42},
        }
        result = parse_all_properties(props)
        assert result == {"Name": "Test", "Score": 42}

    def test_empty(self):
        assert parse_all_properties({}) == {}


# --- Read-only properties constant ---


class TestReadOnlyProperties:
    def test_contains_expected(self):
        expected = {"formula", "rollup", "created_time", "created_by", "last_edited_time", "last_edited_by", "unique_id"}
        assert READ_ONLY_PROPERTIES == expected
