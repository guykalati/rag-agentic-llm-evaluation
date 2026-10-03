# Corpus and model credits

Eight Python 3.12 standard-library documentation pages are frozen with original HTML, URLs and SHA256 hashes in corpus/manifest.json. Python documentation is copyright the Python Software Foundation and contributors; the documentation license is at https://docs.python.org/3.12/license.html. Retain the HTML attribution and source URLs when redistributing the corpus.

Dense embeddings use sentence-transformers/all-MiniLM-L6-v2 under Apache-2.0, pinned to revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41. Local cache file hashes are in embedding_files_manifest.json; model weights are excluded from Git. Model card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2.

Answer and judge use the existing local Gemma4 12B QAT artifact. Its exact digest and Ollama version are in runtime_manifest.json. No requests are sent to cloud model endpoints.
