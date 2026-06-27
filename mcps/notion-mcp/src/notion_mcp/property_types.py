"""Property type handlers for all 24 Notion property types."""

from typing import Any


def build_title(value: str) -> dict:
    """Build title property value."""
    return {"title": [{"text": {"content": value}}]}


def build_rich_text(value: str) -> dict:
    """Build rich_text property value."""
    return {"rich_text": [{"text": {"content": value}}]}


def build_number(value: int | float) -> dict:
    """Build number property value."""
    return {"number": value}


def build_select(value: str) -> dict:
    """Build select property value."""
    return {"select": {"name": value}}


def build_multi_select(values: list[str]) -> dict:
    """Build multi_select property value."""
    return {"multi_select": [{"name": v} for v in values]}


def build_date(start: str, end: str | None = None) -> dict:
    """Build date property value. Dates should be ISO 8601 format."""
    date_obj = {"start": start}
    if end:
        date_obj["end"] = end
    return {"date": date_obj}


def build_checkbox(value: bool) -> dict:
    """Build checkbox property value."""
    return {"checkbox": value}


def build_url(value: str) -> dict:
    """Build url property value."""
    return {"url": value}


def build_email(value: str) -> dict:
    """Build email property value."""
    return {"email": value}


def build_phone_number(value: str) -> dict:
    """Build phone_number property value."""
    return {"phone_number": value}


def build_status(value: str) -> dict:
    """Build status property value."""
    return {"status": {"name": value}}


def build_files(urls: list[str]) -> dict:
    """Build files property value from external URLs."""
    return {"files": [{"type": "external", "name": url.split("/")[-1], "external": {"url": url}} for url in urls]}


def build_relation(page_ids: list[str]) -> dict:
    """Build relation property value."""
    return {"relation": [{"id": pid} for pid in page_ids]}


def build_people(user_ids: list[str]) -> dict:
    """Build people property value."""
    return {"people": [{"id": uid} for uid in user_ids]}


# Read-only properties (cannot be set via API)
READ_ONLY_PROPERTIES = {
    "formula",
    "rollup",
    "created_time",
    "created_by",
    "last_edited_time",
    "last_edited_by",
    "unique_id",
}


# Property type to builder mapping
PROPERTY_BUILDERS = {
    "title": build_title,
    "rich_text": build_rich_text,
    "number": build_number,
    "select": build_select,
    "multi_select": build_multi_select,
    "date": build_date,
    "checkbox": build_checkbox,
    "url": build_url,
    "email": build_email,
    "phone_number": build_phone_number,
    "status": build_status,
    "files": build_files,
    "relation": build_relation,
    "people": build_people,
}


def build_properties_from_schema(schema: dict, values: dict[str, Any]) -> dict:
    """
    Build Notion properties object from schema and values.

    Handles date values as either ISO 8601 strings or {"start": str, "end": str} dicts.

    Args:
        schema: Database schema with property definitions
        values: Dict of property_name -> value to set

    Returns:
        Notion-formatted properties object
    """
    properties = {}

    for prop_name, value in values.items():
        if prop_name not in schema:
            continue

        prop_type = schema[prop_name].get("type")

        if prop_type in READ_ONLY_PROPERTIES:
            continue

        builder = PROPERTY_BUILDERS.get(prop_type)
        if builder:
            if prop_type == "date" and isinstance(value, str):
                properties[prop_name] = builder(value)
            elif prop_type == "date" and isinstance(value, dict):
                properties[prop_name] = builder(value.get("start", ""), value.get("end"))
            else:
                properties[prop_name] = builder(value)

    return properties


def parse_property_value(prop: dict) -> Any:
    """
    Parse a Notion property value to a simple Python value.

    Args:
        prop: Notion property object

    Returns:
        Simplified Python value
    """
    prop_type = prop.get("type")

    if prop_type == "title":
        texts = prop.get("title", [])
        return "".join(t.get("plain_text", "") for t in texts)

    elif prop_type == "rich_text":
        texts = prop.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in texts)

    elif prop_type == "number":
        return prop.get("number")

    elif prop_type == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None

    elif prop_type == "multi_select":
        return [s.get("name") for s in prop.get("multi_select", [])]

    elif prop_type == "date":
        date = prop.get("date")
        if date:
            return {"start": date.get("start"), "end": date.get("end")}
        return None

    elif prop_type == "checkbox":
        return prop.get("checkbox")

    elif prop_type == "url":
        return prop.get("url")

    elif prop_type == "email":
        return prop.get("email")

    elif prop_type == "phone_number":
        return prop.get("phone_number")

    elif prop_type == "status":
        status = prop.get("status")
        return status.get("name") if status else None

    elif prop_type == "files":
        files = prop.get("files", [])
        result = []
        for f in files:
            if f.get("type") == "external":
                result.append(f.get("external", {}).get("url"))
            elif f.get("type") == "file":
                result.append(f.get("file", {}).get("url"))
        return result

    elif prop_type == "relation":
        return [r.get("id") for r in prop.get("relation", [])]

    elif prop_type == "people":
        return [p.get("id") for p in prop.get("people", [])]

    elif prop_type == "formula":
        formula = prop.get("formula", {})
        return formula.get(formula.get("type"))

    elif prop_type == "rollup":
        rollup = prop.get("rollup", {})
        return rollup.get(rollup.get("type"))

    elif prop_type in ("created_time", "last_edited_time"):
        return prop.get(prop_type)

    elif prop_type in ("created_by", "last_edited_by"):
        user = prop.get(prop_type)
        return user.get("id") if user else None

    elif prop_type == "unique_id":
        uid = prop.get("unique_id", {})
        prefix = uid.get("prefix", "")
        number = uid.get("number", 0)
        return f"{prefix}{number}" if prefix else str(number)

    return None


def parse_all_properties(properties: dict) -> dict[str, Any]:
    """
    Parse all properties from a Notion page.

    Args:
        properties: Notion properties object

    Returns:
        Dict of property_name -> parsed value
    """
    return {name: parse_property_value(prop) for name, prop in properties.items()}
