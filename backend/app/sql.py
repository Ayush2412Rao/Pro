import re

from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_openai import AzureChatOpenAI

from .config import Settings


DISALLOWED_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|PRAGMA|ATTACH|DETACH|REPLACE)\b",
    re.IGNORECASE,
)


def is_safe_select(sql: str, allowed_tables: list[str]) -> bool:
    if not sql:
        return False
    normalized = sql.strip().strip(";")
    if not normalized.upper().startswith("SELECT"):
        return False
    if DISALLOWED_SQL.search(normalized):
        return False
    if ";" in normalized:
        return False
    table_ok = any(f" {table} " in f" {normalized} " for table in allowed_tables)
    return table_ok


def run_text_to_sql(question: str, settings: Settings) -> str | None:
    db = SQLDatabase.from_uri(f"sqlite:///{settings.db_path}")
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_endpoint,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
        azure_deployment=settings.azure_deployment,
        temperature=0,
    )
    chain = create_sql_query_chain(llm, db)
    sql = chain.invoke({"question": question})
    if isinstance(sql, dict):
        sql = sql.get("result", "")
    sql = str(sql).replace("SQLQuery:", "").strip()
    if not is_safe_select(sql, ["orders", "complaints", "policies"]):
        return None
    return db.run(sql)
