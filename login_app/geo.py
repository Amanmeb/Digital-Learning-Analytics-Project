# CDLAID Geo Admin Helpers
# Lets a school admin list existing woreda entries or insert a new one,
# then assign a school to that woreda. Runs entirely against the local
# school database -- no internet or central connectivity required.
import re
from sqlalchemy import text


def slugify(value):
    # Converts a woreda name into a safe geo_id fragment
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-")
    return slug.upper()


def get_zones(db):
    # Returns all zone-level (level 3) geo nodes with their region name
    rows = db.execute(
        text("""
            SELECT z.geo_id, z.node_name AS zone_name, r.node_name AS region_name
            FROM mart.dim_geo_node z
            JOIN mart.dim_geo_node r ON z.parent_geo_id = r.geo_id
            WHERE z.level_number = 3
            ORDER BY r.node_name, z.node_name
        """)
    ).mappings().all()
    return [dict(row) for row in rows]


def get_woredas(db, zone_geo_id):
    # Returns existing woreda-level (level 4) nodes under a given zone
    rows = db.execute(
        text("""
            SELECT geo_id, node_name
            FROM mart.dim_geo_node
            WHERE level_number = 4 AND parent_geo_id = :zone_geo_id
            ORDER BY node_name
        """),
        {"zone_geo_id": zone_geo_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def resolve_or_create_woreda(db, woreda_geo_id, zone_geo_id, woreda_name):
    # Returns (geo_id, error). If woreda_geo_id is given, validates it
    # exists at level 4. Otherwise creates a new woreda node under
    # zone_geo_id using woreda_name.
    if woreda_geo_id:
        row = db.execute(
            text("""
                SELECT geo_id FROM mart.dim_geo_node
                WHERE geo_id = :geo_id AND level_number = 4
            """),
            {"geo_id": woreda_geo_id},
        ).fetchone()
        if not row:
            return None, "woreda_geo_id not found at level 4"
        return woreda_geo_id, None

    if not zone_geo_id or not woreda_name:
        return None, "zone_geo_id and woreda_name are required to create a new woreda"

    zone_row = db.execute(
        text("""
            SELECT geo_id, country_code FROM mart.dim_geo_node
            WHERE geo_id = :zone_geo_id AND level_number = 3
        """),
        {"zone_geo_id": zone_geo_id},
    ).mappings().fetchone()
    if not zone_row:
        return None, "zone_geo_id not found at level 3"

    new_geo_id = zone_geo_id + "-" + slugify(woreda_name)

    db.execute(
        text("""
            INSERT INTO mart.dim_geo_node
                (geo_id, parent_geo_id, country_code, level_number, node_name, node_code)
            VALUES
                (:geo_id, :parent_geo_id, :country_code, 4, :node_name, :node_name)
            ON CONFLICT (geo_id) DO NOTHING
        """),
        {
            "geo_id": new_geo_id,
            "parent_geo_id": zone_geo_id,
            "country_code": zone_row["country_code"],
            "node_name": woreda_name,
        },
    )
    return new_geo_id, None


def assign_school_woreda(db, school_id, woreda_geo_id):
    # Updates dim_school.geo_id to point at the given woreda
    result = db.execute(
        text("""
            UPDATE mart.dim_school
            SET geo_id = :geo_id
            WHERE school_id = :school_id
        """),
        {"geo_id": woreda_geo_id, "school_id": school_id},
    )
    return result.rowcount > 0