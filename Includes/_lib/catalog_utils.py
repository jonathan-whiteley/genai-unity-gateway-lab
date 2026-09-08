import re
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()


def _safe_uc_name(value: str) -> str:
    """Make a string safe for UC identifiers."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "user"


def _current_user_email() -> str:
    """Get the current user's email address."""
    return spark.sql("SELECT current_user()").first()[0]


def _vocareum_schema_name(user_email: str) -> str:
    """Return the schema name for a Vocareum user (username without domain)."""
    return _safe_uc_name(user_email.split("@")[0])


def _get_workspace_catalogs() -> list:
    """Return a list of catalogs visible to the current user."""
    return [
        row["catalog"].strip().lower()
        for row in spark.sql("SHOW CATALOGS").collect()
    ]



def _catalog_exists(name: str, catalogs: list) -> bool:
    """Check if a catalog already exists."""
    return name.lower() in catalogs


def _looks_like_missing_storage_root(err: Exception) -> bool:
    """Heuristic: does this CREATE CATALOG failure mean the metastore has no
    storage root (the Default Storage / no-managed-location case)?"""
    msg = str(err).lower()
    return (
        "storage root" in msg
        or "default storage" in msg
        or "managed location" in msg
        or "storage location" in msg
    )


def build_user_catalog(
    prefix: str = "labuser",
    catalog_forced: str = None,
    managed_location: str = None,
) -> str:
    """
    Return a UC catalog name for the current user, creating it if needed.

    Parameters
    ----------
    prefix : str
        Prefix for the catalog name. Default is 'labuser'.
    catalog_forced : str
        Use this catalog name exactly (must already exist).
    managed_location : str, optional
        External-location URL to use as the new catalog's MANAGED LOCATION
        (e.g. 's3://my-bucket/uc/'). Required on accounts whose metastore has
        no storage root (UC Default Storage), where a bare CREATE CATALOG is
        rejected. Ignored when the catalog already exists or is forced. Set it
        via ``catalog.managed_location`` in the course config.
    """
    user_email = _current_user_email()
    safe_user_name = _safe_uc_name(user_email.split("@")[0])

    # Vocareum: shared 'dbacademy' catalog, pre-provisioned by the platform
    if user_email.lower().endswith("@vocareum.com"):
        print("Vocareum workspace detected.")
        vocareum_catalog = safe_user_name
        if _catalog_exists(vocareum_catalog, _get_workspace_catalogs()):
            print(f"  Catalog '{vocareum_catalog}' found. Using it.")
            return vocareum_catalog
        else:
            raise ValueError(
                f"Catalog '{vocareum_catalog}' does not exist in this Vocareum workspace."
            )

    # Non-Vocareum: use prefix_username or a forced catalog name
    catalog_name = catalog_forced if catalog_forced else f"{prefix}_{safe_user_name[:19]}"

    if catalog_forced and not _catalog_exists(catalog_name, _get_workspace_catalogs()):
        raise RuntimeError(
            f"Forced catalog '{catalog_name}' does not exist. "
            "Create it first, then re-run."
        )

    if _catalog_exists(catalog_name, _get_workspace_catalogs()):
        print(f"  Catalog '{catalog_name}' already exists. Using it.")
        return catalog_name

    print(f"  Creating catalog '{catalog_name}'...")
    ddl = f"CREATE CATALOG IF NOT EXISTS {catalog_name}"
    if managed_location:
        ddl += f" MANAGED LOCATION '{managed_location}'"
    try:
        spark.sql(ddl)
    except Exception as e:
        # The most common clone-and-deploy failure: the account uses UC Default
        # Storage (or the metastore has no storage root), so a bare CREATE CATALOG
        # is rejected. Re-raise with the three concrete fixes instead of the raw
        # "Metastore storage root URL does not exist" stack trace.
        if _looks_like_missing_storage_root(e) and not managed_location:
            raise RuntimeError(
                f"Could not create catalog '{catalog_name}': this account has no "
                f"metastore storage root (UC Default Storage), so a catalog needs an "
                f"explicit MANAGED LOCATION. Pick ONE of:\n"
                f"  1. Point the lab at a catalog you can already write to, by adding "
                f"$catalog_override=\"<existing_catalog>\" after the "
                f"%run ./Includes/Classroom-Setup-1 line (you need CREATE SCHEMA on it).\n"
                f"  2. Set 'catalog.managed_location' in Includes/config/config-1.yaml to an "
                f"external-location URL you own (e.g. 's3://<bucket>/uc/'), then re-run.\n"
                f"  3. Ask an account admin to configure a metastore storage root.\n"
                f"Original error: {e}"
            ) from e
        raise
    print(f"  Catalog '{catalog_name}' created.")
    return catalog_name


def setup_catalog_and_schema(schema_name: str, catalog_prefix: str = "labuser") -> tuple[str, str]:
    """
    Build the user catalog, create the schema, and set both as active.

    Parameters
    ----------
    schema_name : str
        Name of the schema to create and use.
    catalog_prefix : str
        Prefix used when auto-creating a catalog. Default is 'labuser'.

    Returns
    -------
    tuple[str, str]
        (catalog_name, schema_name)
    """
    catalog_name = build_user_catalog(prefix=catalog_prefix)

    spark.sql(f"USE CATALOG {catalog_name}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    spark.sql(f"USE SCHEMA {schema_name}")

    print(f"  Catalog : {catalog_name}")
    print(f"  Schema  : {schema_name}")

    return catalog_name, schema_name

def _drop_catalog(catalog_name: str):
    spark.sql(f"DROP CATALOG IF EXISTS {catalog_name} CASCADE")
    print(f"Successfully dropped catalog {catalog_name}.")