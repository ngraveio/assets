from __future__ import annotations

import argparse
import io
import json
import posixpath
import struct
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
import zlib

from PIL import Image


TRUSTWALLET_TREE_URL = (
    "https://api.github.com/repos/trustwallet/assets/git/trees/master?recursive=1"
)
TRUSTWALLET_RAW_BASE_URL = "https://raw.githubusercontent.com/trustwallet/assets/master"
COINGECKO_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&category=binance-smart-chain&order=market_cap_desc"
    "&per_page=100&page=1&sparkline=false"
    "&price_change_percentage=1h,24h,7d"
)
COINGECKO_LIST_URL = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"

BSC_DEST_ROOT = Path("blockchains/binancesmartchain/assets")
REPORT_PATH = Path("reports/LIQ-1061-bsc-token-logo-audit.xlsx")
POPULAR_REPORT_PATH = Path("reports/LIQ-1061-bsc-popular-token-selection.xlsx")
USER_AGENT = "ngrave-assets-liq-1061"


@dataclass(frozen=True)
class TrustWalletLogo:
    contract: str
    lower_contract: str
    source_path: str
    destination_dir: Path

    @property
    def destination_logo(self) -> Path:
        return self.destination_dir / "logo.png"

    @property
    def destination_logo64(self) -> Path:
        return self.destination_dir / "logo64.png"

    @property
    def raw_url(self) -> str:
        quoted_path = urllib.parse.quote(self.source_path, safe="/")
        return f"{TRUSTWALLET_RAW_BASE_URL}/{quoted_path}"


@dataclass(frozen=True)
class SheetSpec:
    name: str
    rows: list[list[object]]
    widths: list[float]
    table_name: str


def request_bytes(url: str, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network failure path
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def request_json(url: str) -> object:
    return json.loads(request_bytes(url).decode("utf-8"))


def fetch_trustwallet_logos() -> list[TrustWalletLogo]:
    data = request_json(TRUSTWALLET_TREE_URL)
    if not isinstance(data, dict) or not isinstance(data.get("tree"), list):
        raise RuntimeError("Unexpected Trust Wallet tree response")
    if data.get("truncated"):
        raise RuntimeError("Trust Wallet tree response is truncated")

    logos: list[TrustWalletLogo] = []
    seen: set[str] = set()
    for item in data["tree"]:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if not isinstance(path, str):
            continue
        if not path.startswith("blockchains/smartchain/assets/"):
            continue
        if not path.endswith("/logo.png"):
            continue

        parts = path.split("/")
        if len(parts) != 5:
            continue
        contract = parts[3]
        lower_contract = contract.lower()
        if lower_contract in seen:
            raise RuntimeError(f"Duplicate Trust Wallet contract after lowercasing: {contract}")
        seen.add(lower_contract)
        logos.append(
            TrustWalletLogo(
                contract=contract,
                lower_contract=lower_contract,
                source_path=path,
                destination_dir=BSC_DEST_ROOT / lower_contract,
            )
        )
    return sorted(logos, key=lambda logo: logo.lower_contract)


def resize_to_64(source_png: bytes) -> bytes:
    try:
        image = Image.open(io.BytesIO(source_png))
    except Exception:
        image = Image.open(io.BytesIO(strip_bad_png_ancillary_chunks(source_png)))

    with image:
        resized = image.resize((64, 64), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        resized.save(output, format="PNG")
        return output.getvalue()


def strip_bad_png_ancillary_chunks(source_png: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    if not source_png.startswith(signature):
        raise ValueError("source file is not a PNG")

    output = bytearray(signature)
    offset = len(signature)
    while offset + 12 <= len(source_png):
        length = struct.unpack(">I", source_png[offset : offset + 4])[0]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if crc_end > len(source_png):
            raise ValueError("source PNG is truncated")

        chunk_type = source_png[offset + 4 : offset + 8]
        chunk_data = source_png[chunk_start:chunk_end]
        expected_crc = struct.unpack(">I", source_png[chunk_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        is_critical = 65 <= chunk_type[0] <= 90

        if expected_crc == actual_crc or is_critical:
            if expected_crc != actual_crc:
                raise ValueError(f"critical PNG chunk has a bad CRC: {chunk_type.decode('ascii')}")
            output.extend(source_png[offset:crc_end])

        offset = crc_end
        if chunk_type == b"IEND":
            return bytes(output)

    raise ValueError("source PNG is missing IEND")


def image_is_64(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            return image.size == (64, 64)
    except Exception:
        return False


def import_logo(
    logo: TrustWalletLogo,
    dry_run: bool,
    tracked_paths: set[str],
    changed_paths: set[str],
) -> dict[str, str]:
    try:
        source_png = request_bytes(logo.raw_url)
        logo64 = resize_to_64(source_png)

        destination_exists = logo.destination_logo.exists()
        logo_same = destination_exists and logo.destination_logo.read_bytes() == source_png
        logo64_same = logo.destination_logo64.exists() and logo.destination_logo64.read_bytes() == logo64
        logo64_valid = logo.destination_logo64.exists() and image_is_64(logo.destination_logo64)

        destination_logo_path = posix_path(logo.destination_logo)
        destination_logo64_path = posix_path(logo.destination_logo64)
        tracked = destination_logo_path in tracked_paths
        changed = (
            destination_logo_path in changed_paths
            or destination_logo64_path in changed_paths
        )

        if not tracked:
            status = "imported"
        elif changed:
            status = "updated"
        elif logo_same and logo64_same and logo64_valid:
            status = "already present"
        else:
            status = "updated" if destination_exists else "imported"

        if not (logo_same and logo64_same and logo64_valid):
            if not dry_run:
                logo.destination_dir.mkdir(parents=True, exist_ok=True)
                logo.destination_logo.write_bytes(source_png)
                logo.destination_logo64.write_bytes(logo64)

        return {
            "Trust Wallet contract": logo.contract,
            "lowercase destination contract": logo.lower_contract,
            "status": status,
            "source path": logo.source_path,
            "destination path": destination_logo_path,
        }
    except Exception as exc:  # pragma: no cover - network/image failure path
        return {
            "Trust Wallet contract": logo.contract,
            "lowercase destination contract": logo.lower_contract,
            "status": f"failed: {exc}",
            "source path": logo.source_path,
            "destination path": posix_path(logo.destination_logo),
        }


def git_path_set(*args: str) -> set[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
        )
    except Exception:
        return set()
    return {
        path.decode("utf-8")
        for path in result.stdout.split(b"\0")
        if path
    }


def build_import_summary(logos: list[TrustWalletLogo], dry_run: bool, workers: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tracked_paths = git_path_set("ls-files", "-z", posix_path(BSC_DEST_ROOT))
    changed_paths = git_path_set("diff", "--name-only", "-z", "--", posix_path(BSC_DEST_ROOT))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_logo = {
            executor.submit(import_logo, logo, dry_run, tracked_paths, changed_paths): logo
            for logo in logos
        }
        for future in as_completed(future_to_logo):
            rows.append(future.result())
    return sorted(rows, key=lambda row: row["lowercase destination contract"])


def fetch_coingecko_top_100(
    imported_contracts: set[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    markets = request_json(COINGECKO_MARKETS_URL)
    coin_list = request_json(COINGECKO_LIST_URL)
    if not isinstance(markets, list):
        raise RuntimeError("Unexpected CoinGecko markets response")
    if not isinstance(coin_list, list):
        raise RuntimeError("Unexpected CoinGecko coin list response")

    def rounded(value: object, digits: int = 2) -> object:
        return round(value, digits) if isinstance(value, (int, float)) else ""

    platforms_by_id: dict[str, dict[str, str]] = {}
    for coin in coin_list:
        if not isinstance(coin, dict):
            continue
        coin_id = coin.get("id")
        platforms = coin.get("platforms")
        if isinstance(coin_id, str) and isinstance(platforms, dict):
            platforms_by_id[coin_id] = {
                str(key): str(value)
                for key, value in platforms.items()
                if isinstance(value, str) and value
            }

    rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    for rank, token in enumerate(markets[:100], start=1):
        if not isinstance(token, dict):
            continue
        coin_id = str(token.get("id", ""))
        symbol = str(token.get("symbol", ""))
        name = str(token.get("name", ""))
        market_cap = token.get("market_cap")
        contract = platforms_by_id.get(coin_id, {}).get("binance-smart-chain", "")
        lower_contract = contract.lower()

        imported = bool(lower_contract and lower_contract in imported_contracts)
        local_path = posix_path(BSC_DEST_ROOT / lower_contract) if imported else ""
        notes = ""
        if coin_id == "binancecoin" and symbol.lower() == "bnb":
            notes = "excluded_native_bnb"
        elif not contract:
            notes = "missing_contract"
        elif not imported:
            notes = "not_in_trustwallet"

        if notes == "excluded_native_bnb":
            selection_priority = "native coin - not token folder"
            logo_status = "native"
        elif imported:
            selection_priority = "candidate"
            logo_status = "Trust Wallet logo imported"
        elif not contract:
            selection_priority = "review manually"
            logo_status = "no BSC contract resolved"
        else:
            selection_priority = "missing Trust Wallet logo"
            logo_status = "not imported"

        rows.append(
            {
                "rank": rank,
                "CoinGecko ID": coin_id,
                "symbol": symbol,
                "name": name,
                "market cap": market_cap if isinstance(market_cap, (int, float)) else "",
                "resolved BSC contract": lower_contract,
                "imported from Trust Wallet": "yes" if imported else "no",
                "local path": local_path,
                "notes": notes,
            }
        )
        candidate_rows.append(
            {
                "selection rank": rank,
                "CoinGecko ID": coin_id,
                "symbol": symbol.upper(),
                "name": name,
                "price": rounded(token.get("current_price"), 8),
                "1h %": rounded(token.get("price_change_percentage_1h_in_currency")),
                "24h %": rounded(token.get("price_change_percentage_24h_in_currency")),
                "7d %": rounded(token.get("price_change_percentage_7d_in_currency")),
                "24h volume": rounded(token.get("total_volume"), 0),
                "market cap": market_cap if isinstance(market_cap, (int, float)) else "",
                "resolved BSC contract": lower_contract,
                "logo status": logo_status,
                "local path": local_path,
                "selection priority": selection_priority,
                "notes": notes,
            }
        )
    return rows, candidate_rows


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def range_ref(rows: list[list[object]]) -> str:
    row_count = max(len(rows), 1)
    col_count = max((len(row) for row in rows), default=1)
    return f"A1:{column_name(col_count)}{row_count}"


def style_for_cell(header: str, value: object, row_index: int) -> int:
    if row_index == 1:
        return 1
    text = str(value)
    if header == "status":
        if text == "imported":
            return 2
        if text == "updated":
            return 3
        if text.startswith("failed"):
            return 4
    if header in {"imported from Trust Wallet", "logo status"}:
        if text in {"yes", "Trust Wallet logo imported"}:
            return 2
        if text in {"no", "not imported", "no BSC contract resolved"}:
            return 4
        if text == "native":
            return 5
    if header == "selection priority":
        if text == "candidate":
            return 2
        if text == "native coin - not token folder":
            return 5
        if text in {"review manually", "missing Trust Wallet logo"}:
            return 3
    if header == "notes" and text:
        return 6
    return 0


def worksheet_xml(spec: SheetSpec, table_id: int) -> str:
    rows = spec.rows
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        headers = rows[0] if rows else []
        for col_index, value in enumerate(row, start=1):
            ref = f"{column_name(col_index)}{row_index}"
            header = str(headers[col_index - 1]) if col_index - 1 < len(headers) else ""
            style = style_for_cell(header, value, row_index)
            style_attr = f' s="{style}"' if style else ""
            if value is None or value == "":
                cells.append(f'<c r="{ref}"{style_attr}/>')
            elif isinstance(value, bool):
                cells.append(f'<c r="{ref}"{style_attr} t="b"><v>{1 if value else 0}</v></c>')
            elif isinstance(value, (int, float)):
                cells.append(f'<c r="{ref}"{style_attr}><v>{value}</v></c>')
            else:
                text = escape(str(value), {'"': "&quot;"})
                cells.append(
                    f'<c r="{ref}"{style_attr} t="inlineStr"><is><t>{text}</t></is></c>'
                )
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    cols = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(spec.widths, start=1)
    )
    ref = range_ref(rows)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheetViews><sheetView workbookViewId=\"0\"><pane ySplit=\"1\" topLeftCell=\"A2\" "
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f"<cols>{cols}</cols>"
        f"<sheetData>{''.join(xml_rows)}</sheetData>"
        '<tableParts count="1"><tablePart r:id="rId1"/></tableParts>'
        "</worksheet>"
    )


def sheet_rows(headers: list[str], dict_rows: Iterable[dict[str, object]]) -> list[list[object]]:
    rows: list[list[object]] = [headers]
    for row in dict_rows:
        rows.append([row.get(header, "") for header in headers])
    return rows


def table_xml(table_id: int, spec: SheetSpec) -> str:
    headers = spec.rows[0]
    columns = "".join(
        f'<tableColumn id="{index}" name="{escape(str(header), {chr(34): "&quot;"})}"/>'
        for index, header in enumerate(headers, start=1)
    )
    ref = range_ref(spec.rows)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'id="{table_id}" name="{spec.table_name}" displayName="{spec.table_name}" '
        f'ref="{ref}" totalsRowShown="0">'
        f'<autoFilter ref="{ref}"/>'
        f'<tableColumns count="{len(headers)}">{columns}</tableColumns>'
        '<tableStyleInfo name="TableStyleMedium2" showFirstColumn="0" showLastColumn="0" '
        'showRowStripes="1" showColumnStripes="0"/>'
        "</table>"
    )


def worksheet_rels_xml(table_id: int) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" '
        f'Target="../tables/table{table_id}.xml"/>'
        "</Relationships>"
    )


def styles_xml() -> str:
    fills = [
        '<fill><patternFill patternType="none"/></fill>',
        '<fill><patternFill patternType="gray125"/></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFE2F0D9"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFF4CCCC"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFCE4D6"/><bgColor indexed="64"/></patternFill></fill>',
    ]
    cell_xfs = [
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>',
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFill="1" applyFont="1" applyBorder="1"/>',
        '<xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>',
        '<xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>',
        '<xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>',
        '<xf numFmtId="0" fontId="0" fillId="6" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>',
        '<xf numFmtId="0" fontId="0" fillId="7" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>',
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>'
        "</fonts>"
        f'<fills count="{len(fills)}">{"".join(fills)}</fills>'
        '<borders count="2"><border/><border><left style="thin"><color rgb="FFD9E2F3"/></left>'
        '<right style="thin"><color rgb="FFD9E2F3"/></right><top style="thin"><color rgb="FFD9E2F3"/></top>'
        '<bottom style="thin"><color rgb="FFD9E2F3"/></bottom></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        f'<cellXfs count="{len(cell_xfs)}">{"".join(cell_xfs)}</cellXfs>'
        "</styleSheet>"
    )


def write_xlsx(path: Path, sheets: list[SheetSpec]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for index in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        content_types.append(
            f'<Override PartName="/xl/tables/table{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/>'
        )
    content_types.append("</Types>")

    workbook_sheets = []
    workbook_rels = []
    for index, spec in enumerate(sheets, start=1):
        workbook_sheets.append(
            f'<sheet name="{escape(spec.name)}" sheetId="{index}" r:id="rId{index}"/>'
        )
        workbook_rels.append(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
    styles_rid = len(sheets) + 1
    workbook_rels.append(
        f'<Relationship Id="rId{styles_rid}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{''.join(workbook_sheets)}</sheets></workbook>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(workbook_rels)}</Relationships>"
    )
    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
        'Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
        'Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>LIQ-1061 importer</dc:creator>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        "</cp:coreProperties>"
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Python</Application></Properties>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/styles.xml", styles_xml())
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        for index, spec in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(spec, index))
            archive.writestr(f"xl/worksheets/_rels/sheet{index}.xml.rels", worksheet_rels_xml(index))
            archive.writestr(f"xl/tables/table{index}.xml", table_xml(index, spec))


def posix_path(path: Path) -> str:
    return path.as_posix()


def count_bsc_folders() -> int:
    if not BSC_DEST_ROOT.exists():
        return 0
    return sum(1 for path in BSC_DEST_ROOT.iterdir() if path.is_dir())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import all Trust Wallet BSC token PNG logos and write the LIQ-1061 audit workbook."
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch and report without writing assets.")
    parser.add_argument("--workers", type=int, default=16, help="Concurrent Trust Wallet downloads.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="Output .xlsx report path.")
    parser.add_argument(
        "--popular-report",
        type=Path,
        default=POPULAR_REPORT_PATH,
        help="Output .xlsx report path for the focused popular-token selection workbook.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    before_count = count_bsc_folders()
    logos = fetch_trustwallet_logos()
    import_rows = build_import_summary(logos, dry_run=args.dry_run, workers=args.workers)
    successful_contracts = {
        str(row["lowercase destination contract"])
        for row in import_rows
        if not str(row["status"]).startswith("failed")
    }
    top_100_rows, candidate_rows = fetch_coingecko_top_100(successful_contracts)

    import_headers = [
        "Trust Wallet contract",
        "lowercase destination contract",
        "status",
        "source path",
        "destination path",
    ]
    coingecko_headers = [
        "rank",
        "CoinGecko ID",
        "symbol",
        "name",
        "market cap",
        "resolved BSC contract",
        "imported from Trust Wallet",
        "local path",
        "notes",
    ]
    candidate_headers = [
        "selection rank",
        "CoinGecko ID",
        "symbol",
        "name",
        "price",
        "1h %",
        "24h %",
        "7d %",
        "24h volume",
        "market cap",
        "resolved BSC contract",
        "logo status",
        "local path",
        "selection priority",
        "notes",
    ]
    candidate_sheet = SheetSpec(
        name="Popular Candidates",
        rows=sheet_rows(candidate_headers, candidate_rows),
        widths=[14, 34, 12, 36, 14, 10, 10, 10, 18, 18, 44, 28, 72, 28, 24],
        table_name="PopularCandidates",
    )
    write_xlsx(
        args.report,
        [
            SheetSpec(
                name="Import Summary",
                rows=sheet_rows(import_headers, import_rows),
                widths=[44, 44, 18, 72, 92],
                table_name="ImportSummary",
            ),
            SheetSpec(
                name="CoinGecko Top 100",
                rows=sheet_rows(coingecko_headers, top_100_rows),
                widths=[8, 34, 12, 36, 18, 44, 24, 72, 24],
                table_name="CoinGeckoTop100",
            ),
            candidate_sheet,
        ],
    )
    write_xlsx(args.popular_report, [candidate_sheet])

    after_count = count_bsc_folders()
    status_counts: dict[str, int] = {}
    for row in import_rows:
        status = str(row["status"]).split(":", 1)[0]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"Trust Wallet smartchain logos: {len(logos)}")
    print(f"BSC asset folders before: {before_count}")
    print(f"BSC asset folders after: {after_count}")
    print(f"Report: {args.report}")
    print(f"Popular token report: {args.popular_report}")
    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
