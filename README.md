# Book Search Engine with Crawling, PageRank and Ranking Models

![Python 3](https://img.shields.io/badge/Python-3-blue?style=flat-square)
![Course · IR](https://img.shields.io/badge/Course%20%C2%B7%20IR-blue?style=flat-square)

This project builds a book search engine over data crawled from the Books to Scrape website. The goal is a complete pipeline that crawls the data, builds an index, computes PageRank, combines keyword search with PageRank, and evaluates the resulting system. The system does not rely on text matching alone: it also uses the link structure between pages to improve ranking quality. This is a typical approach in modern information retrieval, where the usefulness of a document depends not only on its content but also on its importance within the link network.

---

## Objectives

- Collect book data from a web source with a clear structure.
- Build a dataset that is larger, more diverse, and more practical than the initial version.
- Build a link graph between book pages.
- Compute PageRank to determine the importance of each document.
- Build an inverted index to support keyword search.
- Combine lexical and PageRank scores to improve ranking quality.
- Evaluate results using standard IR metrics: P@10, Recall@100, and NDCG@10.
- Improve and complete the pipeline, from an early prototype to a nearly complete version.

---

## Method

### 1. Crawling

Crawling starts from a set of seed URLs and then collects the relevant content pages. During the improvement phase, the system:

- increased the number of seed URLs,
- removed unnecessary navigation links,
- excluded login, basket, search, duplicate, and self-links,
- restricted crawling to the website's domain to avoid noise.

These changes make the collected data more relevant and less noisy.

### 2. Link Graph Construction

After crawling, each document is represented as a node. If document A links to document B, a directed edge A → B is added. In addition:

- self-loops are removed,
- invalid links are removed,
- edges that do not reflect actual content are filtered out.

This step is important for PageRank to work well.

### 3. PageRank Computation

PageRank is applied to the constructed link graph. It determines which documents are more important based on the number and quality of links pointing to them.

Key improvements include:

- raising the damping factor to the standard value of 0.85,
- increasing the maximum number of iterations for convergence,
- improving the reliability of the input graph.

### 4. Inverted Index

After the documents are collected, the system tokenizes the text, counts term frequencies, and computes IDF values. These are used to build an inverted index, which enables fast and efficient retrieval of documents containing the query keywords.

### 5. Combined Search

The system combines two signals:

- **Lexical score**: relevance based on keyword matching.
- **PageRank score**: importance of a document within the link network.

This combination prevents results from being skewed by keywords alone, while preserving the importance of documents in the link graph.

### 6. Learning to Rank (LTR)

In addition to the basic methods, the project implements a Learning to Rank model using features such as:

- lexical score,
- PageRank,
- document length,
- number of matched terms,
- other statistical indicators.

The goal is to re-rank search results more effectively based on experimental data.

---

## Results

After improving the pipeline, the system runs successfully on the new data. Measured results:

- Documents in the graph: 567
- Edges: 4121
- The crawl, indexing, PageRank, and retrieval pipeline runs stably.
- Evaluation metrics for each method were collected.

Comparison of methods:

| Method | P@10 | Recall@100 | NDCG@10 |
|---|---:|---:|---:|
| ltr | 0.0600 | 0.3310 | 0.1890 |
| w0.0 | 0.1200 | 0.4821 | 0.4591 |
| w1.0 | 0.0900 | 0.4012 | 0.2845 |
| w5.0 | 0.1100 | 0.4321 | 0.2659 |

Observations:

- The system runs stably and produces real, measured results.
- The best-performing method so far is w0.0, which does not depend entirely on PageRank.
- LTR has not yet reached its optimal performance because the query/qrels set is limited.
- Overall, the system has progressed far beyond the first version.

---

## Improvements over the Initial Version

Compared with the prototype, the project addressed several key issues:

- increased the crawled data and document set,
- removed noisy navigation links,
- improved graph quality,
- improved PageRank,
- rebuilt the score combination method,
- improved pipeline stability,
- prepared a stronger foundation for LTR.

These changes were necessary to move the project from a system that was too small and too simple to a practical information retrieval pipeline.

---

## Limitations

Despite this progress, several limitations remain:

- the query set is small,
- the qrels are not yet sufficiently comprehensive,
- the number of crawled documents has not reached the target of 1000 pages,
- LTR cannot reach its full potential because the evaluation data is not strong enough.

Future work should therefore focus on:

- expanding the query set,
- improving qrels quality,
- improving the crawling strategy with detail pages,
- further optimizing features for the LTR model.

---

## Conclusion

The project delivers a basic yet fairly rigorous book search system, covering crawling, graph construction, PageRank, inverted index, retrieval, and experimental evaluation. These improvements significantly increased the quality of the input data and the stability of the system compared with the initial version.

The current performance is not yet optimal, but it provides a solid foundation for future improvements. With more queries, better qrels, and an optimized crawling strategy, the system has strong potential to achieve significantly better search quality.

---

> Course project — Information Retrieval (IR)
