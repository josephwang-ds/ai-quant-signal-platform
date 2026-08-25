# Storage and Retrieval Deployment

The local portfolio build remains file-backed. A database becomes useful when Company
Lens accepts user documents, refreshes headlines, persists rules, or exposes retrieval
history through an API. Those dynamic features should use a storage adapter rather than
change the deterministic snapshot contract.

## Recommended deployed shape

```text
Vercel
  static/read UI; never receives provider or database service keys
       |
       v
Vultr worker/API
  SEC + headline refresh, parsing, embeddings, bounded retrieval, LLM validation
       |
       v
Supabase
  Postgres: metadata, chunks, rulesets, retrieval/LLM run provenance
  Storage: original user uploads
  pgvector + full-text search: filtered hybrid retrieval
```

Supabase is a convenience choice, not a domain dependency. The same schema can run on
Postgres with pgvector on Vultr. The initial local retriever uses deterministic TF-IDF,
so development and the static demo do not require a cloud database or embedding bill.

## Prepared boundary

`company_lens.storage.EvidenceStorage` defines the small persistence seam for
documents, chunks, headline metadata, rulesets, retrieval runs, and LLM-run
provenance. `LocalJsonStorage` is the default offline implementation and writes
atomic, versioned JSON collections. The opt-in grounded CLI path now records imported
evidence, selected chunks, safe reader rules, enforced retrieval scope, and validated
or fallback LLM provenance under `data/build/company_lens_storage/` by default.
`--storage-dir` can redirect that local cache for tests or operations. Persistence
failures are reported as a bounded status and do not remove the deterministic page.

`SupabaseStorage` is an optional `requests`/PostgREST adapter using bounded network
timeouts and primary-key upserts. It is created only when
`--storage-backend supabase` or `--storage-backend dual` is explicit. `dual` writes
local JSON first and then makes a best-effort remote write; a remote failure marks
provenance as degraded while preserving the complete local record set. This is not a
distributed transaction, queue, or synchronization service.

```bash
company-lens AAPL --llm --storage-backend local
company-lens AAPL --llm --storage-backend dual
```

Remote modes require `SUPABASE_URL` plus a backend key in the worker environment.
Prefer the current `SUPABASE_SECRET_KEY` (`sb_secret_...`); the legacy
`SUPABASE_SERVICE_ROLE_KEY` JWT remains a compatibility fallback. Secret keys are sent
only as the PostgREST `apikey` header, while legacy JWTs also use Bearer authorization.
Publishable keys are rejected. Backend keys must never appear in Vercel frontend
configuration, browser JavaScript, or a public artifact. Local mode reads none of these
variables.

The reviewed, unapplied migration at
`ops/supabase/0001_evidence_storage.sql` mirrors those records, enables row-level
security, and adds deterministic full-text indexes. It intentionally defines no
embedding column or vector dimension. Its table/index creation and policy replacement
are safe to rerun during reviewed setup. Public policies expose approved SEC/news
metadata, while document chunks inherit access through their parent document and
uploaded evidence plus provenance remain owner-only. No Supabase project, credentials,
network connection, authentication UI, or migration deployment is configured here.

## Logical tables

| Table | Grain | Important fields |
|---|---|---|
| `companies` | ticker | CIK, name, active scope |
| `documents` | immutable source document | owner, ticker, type, title, URL/storage path, content hash, published/fetched times |
| `document_chunks` | stable chunk | document ID, chunk index, text, citation, metadata, search vector, optional embedding |
| `headlines` | source-linked headline | publisher, URL, published/fetched times, ticker/entity, topic, legal snippet |
| `rulesets` | versioned user/system rule set | owner, name, allowed emphasis rules, immutable trust-policy version |
| `retrieval_runs` | one query | query, enforced scope, selected citations/scores, index version, latency |
| `llm_runs` | one generation attempt | provider/model, prompt version, evidence hash, validator result, usage/cost |
| `snapshots` | published company version | ticker, as-of, artifact URL/hash, freshness/status |

Original uploads belong in object storage; normalized text and chunks belong in
Postgres. Do not store API keys in either table or browser configuration.

## Access rules

- Published SEC/headline metadata and approved snapshots may be publicly readable.
- A user's uploaded documents, rulesets, retrieval runs, and unpublished output are
  owner-only through row-level security.
- Only the Vultr worker holds the recommended Supabase Secret key (or a legacy
  service-role JWT) and LLM provider keys.
- Uploaded document text is always treated as untrusted evidence, never instructions.
- Deletes first mark records inactive; a background job removes object-storage files and
  derived chunks so the operation is auditable.

## Migration order

1. Keep current file-backed static build and validate retrieval quality.
2. Review and apply the prepared Postgres tables/RLS, then exercise the optional
   dual-write adapter against a non-production project.
3. Select an embedding model with a frozen retrieval evaluation before fixing vector
   dimensions or creating an HNSW index.
4. Add Storage/RLS for authenticated uploads.
5. Move only dynamic API reads to Supabase; keep Vercel's published pages cache-first.
