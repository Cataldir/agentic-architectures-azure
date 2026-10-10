"""Hybrid retrieval with a trusted tenant filter before candidate retrieval."""
import os
from .cloud_guard import require_effects, endpoint


def retrieve(query: str, vector: list[float] | None, tenant: str) -> list[dict[str, str]]:
    require_effects()
    if tenant != os.environ["COURSE_TENANT"] or not tenant.isalnum():
        raise PermissionError("untrusted tenant")
    if not 0 < len(query) <= 1024 or (vector is not None and len(vector) != int(os.environ["EMBEDDING_DIMENSIONS"])):
        raise ValueError("bounded query and matching embedding dimensions required")
    from azure.identity import ManagedIdentityCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    client = SearchClient(endpoint("SEARCH_ENDPOINT", ".search.windows.net"),
                          os.environ["SEARCH_INDEX"], credential)
    vector_options = {} if vector is None else {
        "vector_queries": [VectorizedQuery(vector=vector, k_nearest_neighbors=10,
                                           fields="content_vector")],
        "vector_filter_mode": "preFilter",
    }
    rows = client.search(search_text=query, filter=f"tenant eq '{tenant}'",
                         top=5, **vector_options,
                         select=["id", "content", "tenant", "source_revision"])
    return [{k: str(row[k]) for k in ("id", "content", "tenant", "source_revision")}
            for row in rows]
