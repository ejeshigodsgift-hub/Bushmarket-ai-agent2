# search_result_cache.py

class SearchResultCache(Base):

    __tablename__ = "search_result_cache"

    id

    query_hash

    query_text

    result_json

    expires_at

    created_at