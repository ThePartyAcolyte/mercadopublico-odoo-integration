"""
Field mapping and data extraction utilities for Mercado Público API payloads.

Converts raw JSON responses from API v1 (Licitaciones Públicas) and v2
(Compra Ágil) into Odoo-compatible field dictionaries. All functions are pure
Python with no ORM dependencies and are safe to call without an Odoo environment.
"""
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

# Mapping from API v1 integer status codes to internal selection key strings.
_V1_STATUS_MAP: dict[str, str] = {
    "5": "publicada",
    "6": "cerrada",
    "7": "desierta",
    "8": "adjudicada",
    "18": "revocada",
    "19": "suspendida",
}


def map_tender_status_v1(status_code) -> str:
    """
    Converts a v1 API status code to the internal selection key.

    Args:
        status_code: Raw status code from the API response (int or str).

    Returns:
        str: Internal status key. Defaults to 'publicada' for unknown codes.
    """
    return _V1_STATUS_MAP.get(str(status_code), "publicada")


def map_tender_fields_v1(data: dict) -> dict:
    """
    Maps a full v1 tender API response to Odoo field values.

    Args:
        data (dict): Tender detail dict from API v1, typically 'Listado[0]'.

    Returns:
        dict: Odoo-compatible field dictionary for mercadopublico.tender.
    """
    dates = data.get("Fechas", {})
    buyer = data.get("Comprador", {})
    return {
        "name": data.get("Nombre", "Sin nombre"),
        "descripcion": data.get("Descripcion", ""),
        "buyer_code": buyer.get("CodigoOrganismo", ""),
        "buyer_name": buyer.get("NombreOrganismo", ""),
        "buyer_commune": buyer.get("ComunaUnidad", ""),
        "buyer_region": buyer.get("RegionUnidad", ""),
        "fecha_publicacion": parse_api_datetime(dates.get("FechaPublicacion")),
        "fecha_cierre": parse_api_datetime(dates.get("FechaCierre")),
        "moneda": data.get("Moneda", ""),
        "estimated_amount": float(data.get("MontoEstimado", 0) or 0),
        "tipo_licitacion": data.get("Tipo", ""),
    }


def map_quick_buy_fields_v2(data: dict) -> dict:
    """
    Maps a full v2 quick buy API payload to Odoo field values.

    Args:
        data (dict): Quick buy payload from API v2 detail endpoint.

    Returns:
        dict: Odoo-compatible field dictionary for mercadopublico.tender.
    """
    institution = data.get("institucion", {})
    dates = data.get("fechas", {})
    budget = data.get("presupuesto", {})
    return {
        "name": data.get("nombre", "Sin nombre"),
        "descripcion": data.get("descripcion", ""),
        "buyer_code": institution.get("rut", ""),
        "buyer_name": institution.get("organismo_comprador", ""),
        "buyer_region": institution.get("nombre_region", ""),
        "fecha_publicacion": parse_api_datetime(dates.get("fecha_publicacion")),
        "fecha_cierre": parse_api_datetime(dates.get("fecha_cierre")),
        "moneda": budget.get("moneda", ""),
        "estimated_amount": float(budget.get("monto_disponible_clp", 0) or 0),
    }


def parse_api_datetime(date_str) -> datetime | bool:
    """
    Parses an ISO 8601 datetime string from the API into a naive UTC datetime.

    Handles both 'Z' suffix and fractional seconds (e.g. '.000Z').

    Args:
        date_str (str | None): Raw datetime string from the API.

    Returns:
        datetime | bool: Parsed naive datetime object, or False if unparseable.
    """
    if not date_str:
        return False
    try:
        return datetime.fromisoformat(date_str.split(".")[0].replace("Z", ""))
    except (ValueError, AttributeError, TypeError):
        return False


def extract_v1_items(full_data: dict) -> tuple[list, list]:
    """
    Extracts item line data and category codes from a v1 tender detail.

    Args:
        full_data (dict): Full v1 tender detail from the API.

    Returns:
        tuple[list, list]:
            - List of Odoo ORM command tuples (0, 0, vals) for item_ids field.
            - List of UNSPSC category code strings found in the items.
    """
    items_to_create = []
    category_codes = []
    raw_items = full_data.get("Items", {})
    item_list = raw_items.get("Listado", []) if isinstance(raw_items, dict) else []
    for item in item_list:
        if not isinstance(item, dict):
            continue
        if item.get("CodigoCategoria"):
            category_codes.append(str(item["CodigoCategoria"]))
        items_to_create.append((0, 0, {
            "product_code": str(item.get("CodigoProducto", "")),
            "category_code": str(item.get("CodigoCategoria", "")),
            "name": item.get("NombreProducto", ""),
            "description": item.get("Descripcion", ""),
            "quantity": float(item.get("Cantidad", 0) or 0),
            "unit_of_measure": item.get("UnidadMedida", ""),
        }))
    return items_to_create, category_codes


def extract_v2_items(full_data: dict) -> tuple[list, list]:
    """
    Extracts item line data and category codes from a v2 quick buy payload.

    In v2, an 8-digit all-numeric product code is a UNSPSC category identifier.

    Args:
        full_data (dict): Full v2 quick buy payload from the API.

    Returns:
        tuple[list, list]:
            - List of Odoo ORM command tuples (0, 0, vals) for item_ids field.
            - List of UNSPSC category code strings found in the items.
    """
    items_to_create = []
    category_codes = []
    for product in full_data.get("productos_solicitados", []):
        code = str(product.get("codigo_producto", ""))
        # In v2, 8-digit numeric product codes are UNSPSC category identifiers.
        is_unspsc = len(code) == 8 and code.isdigit()
        if is_unspsc:
            category_codes.append(code)
        items_to_create.append((0, 0, {
            "product_code": code,
            "category_code": code if is_unspsc else "",
            "name": product.get("nombre", ""),
            "description": product.get("descripcion", ""),
            "quantity": float(product.get("cantidad", 0) or 0),
            "unit_of_measure": product.get("unidad_medida", ""),
        }))
    return items_to_create, category_codes
