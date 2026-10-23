# Coding agent + RAG: pages and interview guide

- Open [index.html](index.html) for the public project landing page.
- Open [guide.html](guide.html) for the personal study guide, with 25 interview questions, worked explanations and exercises.
- [guide.md](guide.md) is the authored guide source.

Both HTML files are self-contained and can be opened directly in a browser. Keep them together when sharing. Each page links to the source and saved evidence on the CV closure branch. Interactive examples display saved outputs; they do not call a model or rerun training. Practice checkboxes are saved only in the current browser. Use the guide's print button to save a PDF.

The pages describe the verified results and their limitations. They are local static artifacts, not a deployed website. No CV file was edited.

## Rebuild from a single repository

`build.py` reads this repository's saved results, current status and guide source. It needs Python 3, Node and marked 17.0.5 only at build time. It does not need sibling project checkouts, model inference, cluster access or remote data. The generated HTML remains self-contained.

```sh
python3 showcase/build.py --node /path/to/node --marked /path/to/marked/lib/marked.esm.js
```

The Node/marked paths can also be supplied as `NODE_BINARY` and `MARKED_MODULE`. Install that exact marked version in a separate build environment if it is not already available. No package installation happens in the build script. Re-run `verify_project.py` after rebuilding.
