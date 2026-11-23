# A short Lumen demo

Use **Start Demo.cmd**, or `python run.py --demo-only`. This mode blocks real scans at the server and keeps saved live reports out of the demo. The data, applications, hashes, and sizes shown are fictional.

## A three-minute walkthrough

1. **Overview:** show the storage categories and review queue. Explain the distinction between logical size, bytes under review, and actual reclaimable space. Lumen does not claim they are equivalent.
2. **Storage explorer:** click a large folder to narrow the inventory, then clear the filter and search for `package.json`. Open its details and select **Explain this file**. The answer links back to that exact file. Human last-opened time is explicitly unknown.
3. **Duplicates:** open a group and inspect its evidence and locations. The demo illustrates the result format; its hashes are fictional. Real scans use full SHA-256 checks, reject changing files, and avoid counting hard links twice.
4. **Review queue:** open a finding, read what removal could affect, and mark it to keep. This changes only a browser annotation for that snapshot. There is no delete button or generated command executor.
5. **Snapshots:** compare the two demo snapshots. New, missing, and changed paths are shown separately; missing does not prove deletion.
6. **Export:** download the readable HTML report or the complete CSV inventory. The HTML opens offline and can be printed to PDF. JSON preserves the complete structured snapshot.

Press `/` to focus file search and `Escape` to close a dialog. In the question box, `Enter` sends and `Shift+Enter` inserts a line break.

## Explain the AI honestly

The default evidence guide uses deterministic rules and retrieval. It does not pretend to be a language model. The optional Ollama adapter adds local LLM inference: bounded metadata context, selected-root masking, structured responses, checked citation IDs, and request deadlines. It has no file contents, shell tools, or deletion capability.

The development environment exercised this integration with simulated model responses. Before demonstrating actual local AI, follow the [optional AI setup](../README.md#optional-ai-on-your-own-laptop) on your own laptop and try the model with several file questions. Model output quality was not benchmarked here.

## Discuss engineering evidence

Use the [verification record](verification.md) for the actual test counts and measured results. Keep the distinctions clear: the 100,000-record benchmark measures in-memory analysis and persistence; the 10,000-file fixture benchmark performs real filesystem reads; the sustained test exercises repeated scans, SQLite saves, and concurrent HTTP requests.

Useful implementation topics to discuss include asynchronous jobs, cancellation versus commit, stale browser responses, SQLite read-only connections, local HTTP request protections, CSV formula guards, and fixture-based testing. These are implemented parts of the project, not proposed features.
