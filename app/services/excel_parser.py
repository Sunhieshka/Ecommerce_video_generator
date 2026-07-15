from __future__ import annotations

import posixpath
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pandas as pd

from app.schemas import ParsedWorkbook, ProductRow


COLUMN_ALIASES = {
    "sku": {"sku", "product_id", "id", "item_id"},
    "product_name": {"product_name", "name", "title", "product_title"},
    "product_description": {"product_description", "description", "product_desc", "details"},
    "video_style": {"video_style", "style", "video_type", "video_style_name"},
    "duration_seconds": {"duration", "duration_seconds", "video_duration", "video_duration_seconds"},
    "product_image_refs": {
        "product_image_refs",
        "product_images",
        "product_image",
        "reference_image",
        "reference_images",
        "product_image_urls",
    },
    "human_model_image_refs": {
        "human_model_image_refs",
        "human_model_images",
        "human_model_reference",
        "human_model_references",
        "human_model",
        "model_image",
        "model_images",
        "human_model_image",
    },
}

REQUIRED_FIELDS = {"product_description"}


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _split_refs(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    items = re.split(r"[,\n;|]+", str(value))
    return [item.strip() for item in items if item and item.strip()]


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _image_sort_key(column_name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", column_name)
    if match:
        return (int(match.group(1)), column_name)
    return (0, column_name)


def _find_product_image_columns(normalized_columns: dict[str, str]) -> list[str]:
    matches: list[tuple[str, str]] = []
    for normalized_name, original_name in normalized_columns.items():
        if re.fullmatch(r"product_reference_image(_\d+)?", normalized_name):
            matches.append((normalized_name, original_name))
    matches.sort(key=lambda item: _image_sort_key(item[0]))
    return [original_name for _, original_name in matches]


def _find_human_model_columns(normalized_columns: dict[str, str]) -> list[str]:
    matches: list[tuple[str, str]] = []
    for normalized_name, original_name in normalized_columns.items():
        if normalized_name in COLUMN_ALIASES["human_model_image_refs"] or re.fullmatch(
            r"human_model(_image)?(_\d+)?", normalized_name
        ):
            matches.append((normalized_name, original_name))
    matches.sort(key=lambda item: _image_sort_key(item[0]))
    return [original_name for _, original_name in matches]


def _extract_embedded_images_by_cell(file_path: Path) -> dict[tuple[int, int], list[str]]:
    namespace = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
        "office_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    }

    cell_map: dict[tuple[int, int], list[str]] = {}
    extract_dir = file_path.parent / f"{file_path.stem}_embedded"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(file_path) as archive:
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        workbook_rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        workbook_rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in workbook_rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        }

        first_sheet = workbook_root.find("main:sheets/main:sheet", namespace)
        if first_sheet is None:
            return cell_map

        sheet_rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        if not sheet_rel_id:
            return cell_map

        worksheet_target = workbook_rel_map.get(sheet_rel_id)
        if not worksheet_target:
            return cell_map

        worksheet_path = posixpath.normpath(posixpath.join("xl", worksheet_target))
        worksheet_rels_path = posixpath.join(
            posixpath.dirname(worksheet_path),
            "_rels",
            f"{Path(worksheet_path).name}.rels",
        )
        if worksheet_rels_path not in archive.namelist():
            return cell_map

        worksheet_rels = ET.fromstring(archive.read(worksheet_rels_path))
        drawing_target = None
        for rel in worksheet_rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            if rel.attrib.get("Type", "").endswith("/drawing"):
                drawing_target = posixpath.normpath(
                    posixpath.join(posixpath.dirname(worksheet_path), rel.attrib["Target"])
                )
                break

        if not drawing_target or drawing_target not in archive.namelist():
            return cell_map

        drawing_rels_path = posixpath.join(
            posixpath.dirname(drawing_target),
            "_rels",
            f"{Path(drawing_target).name}.rels",
        )
        if drawing_rels_path not in archive.namelist():
            return cell_map

        drawing_root = ET.fromstring(archive.read(drawing_target))
        drawing_rels = ET.fromstring(archive.read(drawing_rels_path))
        drawing_rel_map = {
            rel.attrib["Id"]: posixpath.normpath(posixpath.join(posixpath.dirname(drawing_target), rel.attrib["Target"]))
            for rel in drawing_rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        }

        for anchor in drawing_root:
            from_node = anchor.find("xdr:from", namespace)
            if from_node is None:
                continue

            col_node = from_node.find("xdr:col", namespace)
            row_node = from_node.find("xdr:row", namespace)
            picture_node = anchor.find("xdr:pic", namespace)
            if col_node is None or row_node is None or picture_node is None:
                continue

            blip_node = picture_node.find(".//a:blip", namespace)
            if blip_node is None:
                continue

            rel_id = blip_node.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            media_path = drawing_rel_map.get(rel_id or "")
            if not media_path or media_path not in archive.namelist():
                continue

            image_bytes = archive.read(media_path)
            extension = Path(media_path).suffix or ".img"
            row_number = int(row_node.text) + 1
            column_number = int(col_node.text) + 1
            output_path = extract_dir / f"r{row_number}_c{column_number}_{Path(media_path).stem}{extension}"
            output_path.write_bytes(image_bytes)
            cell_map.setdefault((row_number, column_number), []).append(str(output_path))

    return cell_map


def parse_excel(file_path: Path) -> ParsedWorkbook:
    dataframe = pd.read_excel(file_path)
    normalized_columns = {_normalize_name(column): column for column in dataframe.columns}
    resolved_columns: dict[str, str] = {}
    multi_image_columns = _find_product_image_columns(normalized_columns)
    human_model_columns = _find_human_model_columns(normalized_columns)
    embedded_images_by_cell = _extract_embedded_images_by_cell(file_path)
    column_positions = {str(column): position for position, column in enumerate(dataframe.columns, start=1)}

    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_columns:
                resolved_columns[target] = normalized_columns[alias]
                break

    missing = sorted(REQUIRED_FIELDS - set(resolved_columns))
    if "product_image_refs" not in resolved_columns and not multi_image_columns:
        missing.append("product_image_refs")
    if missing:
        readable = ", ".join(missing)
        raise ValueError(f"Missing required columns: {readable}")

    warnings: list[str] = []
    rows: list[ProductRow] = []

    for index, row in dataframe.iterrows():
        row_number = index + 2
        product_name = _clean_text(row.get(resolved_columns["product_name"], "")) if "product_name" in resolved_columns else ""
        description = _clean_text(row.get(resolved_columns["product_description"], ""))
        video_style = _clean_text(row.get(resolved_columns["video_style"], "")) if "video_style" in resolved_columns else ""
        duration_seconds = _parse_duration_seconds(row.get(resolved_columns["duration_seconds"])) if "duration_seconds" in resolved_columns else None
        product_images: list[str] = []
        if "product_image_refs" in resolved_columns:
            product_images.extend(_split_refs(row.get(resolved_columns["product_image_refs"])))
        for column_name in multi_image_columns:
            value = _clean_text(row.get(column_name, ""))
            if value:
                product_images.append(value)
            product_images.extend(embedded_images_by_cell.get((row_number, column_positions[column_name]), []))

        # Preserve order but avoid duplicate references when a sheet mixes cell text and embedded media.
        product_images = list(dict.fromkeys(product_images))

        model_images: list[str] = []
        if "human_model_image_refs" in resolved_columns:
            model_images.extend(_split_refs(row.get(resolved_columns["human_model_image_refs"])))
        for column_name in human_model_columns:
            value = _clean_text(row.get(column_name, ""))
            if value:
                model_images.extend(_split_refs(value))
            if column_name in column_positions:
                model_images.extend(embedded_images_by_cell.get((row_number, column_positions[column_name]), []))
        model_images = list(dict.fromkeys(model_images))

        sku_column = resolved_columns.get("sku")
        sku_value = _clean_text(row.get(sku_column, "")) if sku_column else ""
        sku = sku_value or f"ROW-{row_number}"
        product_name = product_name or sku

        if not description or not product_images:
            warnings.append(f"Row {row_number} was skipped because one or more required values were empty.")
            continue

        rows.append(
            ProductRow(
                row_number=row_number,
                sku=sku,
                product_name=product_name,
                product_description=description,
                product_image_refs=product_images,
                human_model_image_refs=model_images,
                video_style=video_style or None,
                duration_seconds=duration_seconds,
            )
        )

    if not rows:
        raise ValueError("The workbook did not contain any valid product rows.")

    return ParsedWorkbook(rows=rows, warnings=warnings, columns=[str(column) for column in dataframe.columns])


def _parse_duration_seconds(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    seconds = round(float(match.group(1)))
    if 3 <= seconds <= 30:
        return seconds
    return None
