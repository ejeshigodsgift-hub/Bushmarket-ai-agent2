# search_query.py

class SearchQuery(Base):

    __tablename__ = "search_queries"

    id
    user_id

    query_text

    normalized_query

    total_results

    created_at