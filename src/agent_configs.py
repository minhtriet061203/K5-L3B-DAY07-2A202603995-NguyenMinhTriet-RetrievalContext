"""Agent configurations compared on dev. Change only one thing at a time.

method       retrieval method behind the `search` tool
top_k        passages returned per search call
budget       max characters of passages shown to the model over the whole run
max_searches stop condition: search calls allowed per question
filter_mode  "given" = use the filter supplied with the question (user input, Day 6 C);
             "none"  = never filter
"""
CONFIGS = {
    # Step 4/5: same agent, three retrieval methods (baseline = Day 6 dense).
    "dense_k3_b800": {"method": "dense", "top_k": 3, "budget": 800, "max_searches": 3, "filter_mode": "given"},
    "bm25_k3_b800": {"method": "bm25", "top_k": 3, "budget": 800, "max_searches": 3, "filter_mode": "given"},
    "hybrid_k3_b800": {"method": "hybrid_rrf", "top_k": 3, "budget": 800, "max_searches": 3, "filter_mode": "given"},
    # Step 6a / improvement #1: only the context budget changes (800 -> 4000 chars).
    # Hypothesis: 800 chars holds ~1 chunk of index B (mean 632, max 1060 chars), so results of
    # the 2nd/3rd search (and sometimes the 1st, e.g. q02/bm25) are dropped. 4000 chars fits about
    # 3 searches x top-3 of new chunks (~6 chunks), so Context Evidence Rate should approach
    # retrieval Hit@3 and false refusals should drop, at the cost of more prompt tokens.
    "dense_k3_b4000": {"method": "dense", "top_k": 3, "budget": 4000, "max_searches": 3, "filter_mode": "given"},
    "bm25_k3_b4000": {"method": "bm25", "top_k": 3, "budget": 4000, "max_searches": 3, "filter_mode": "given"},
    "hybrid_k3_b4000": {"method": "hybrid_rrf", "top_k": 3, "budget": 4000, "max_searches": 3, "filter_mode": "given"},
    # Step 6b / improvement #2: vs bm25_k3_b4000 only the method changes: BM25 top-20 candidates ->
    # cross-encoder/ms-marco-MiniLM-L-6-v2 -> keep top-3. Hypothesis: remaining dev errors are ranking
    # errors (gold in top-20 but not top-3, e.g. q07 gold p028:c01 at BM25 rank 5), which a cross-encoder
    # reading query+passage can fix; risk: MS MARCO model may demote AML-specific passages.
    "bm25_rerank_k3_b4000": {"method": "bm25_rerank", "top_k": 3, "budget": 4000, "max_searches": 3,
                             "filter_mode": "given"},
}