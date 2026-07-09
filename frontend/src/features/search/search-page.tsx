import { Loader2, Search } from "lucide-react";
import { FormEvent, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { searchKnowledge } from "@/lib/search-api";
import type { SearchMode, SearchResultItem } from "@/types/search";

const modes: SearchMode[] = ["semantic", "keyword", "hybrid"];

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [hasContext, setHasContext] = useState<boolean | null>(null);
  const [totalCandidates, setTotalCandidates] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      const response = await searchKnowledge({ query: trimmed, mode });
      setResults(response.results);
      setHasContext(response.has_sufficient_context);
      setTotalCandidates(response.total_candidates);
    } catch {
      setError("Search failed. Check that the API is running and you are signed in.");
      setResults([]);
      setHasContext(null);
      setTotalCandidates(0);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Search</h1>
        <p className="text-sm text-muted-foreground">
          Semantic, keyword, and hybrid search across your knowledge base.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search knowledge
          </CardTitle>
          <CardDescription>Hybrid retrieval with MMR ranking and citation metadata.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSearch}>
            <div className="space-y-2">
              <Label htmlFor="search-query">Query</Label>
              <Input
                id="search-query"
                placeholder="Search documents, chunks, and metadata…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {modes.map((item) => (
                <Button
                  key={item}
                  type="button"
                  size="sm"
                  variant={mode === item ? "default" : "outline"}
                  onClick={() => setMode(item)}
                >
                  {item}
                </Button>
              ))}
            </div>
            <Button type="submit" disabled={loading || !query.trim()}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching…
                </>
              ) : (
                "Search"
              )}
            </Button>
          </form>

          {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}

          {hasContext !== null ? (
            <div className="mt-6 space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                <span>
                  {results.length} result{results.length === 1 ? "" : "s"} from {totalCandidates}{" "}
                  candidates
                </span>
                <Badge variant={hasContext ? "secondary" : "outline"}>
                  {hasContext ? "Sufficient context" : "Below threshold"}
                </Badge>
              </div>

              {results.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No chunks matched your query above the similarity threshold.
                </p>
              ) : (
                <div className="space-y-3">
                  {results.map((item) => (
                    <Card key={item.chunk_id}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">{item.title}</CardTitle>
                        <CardDescription>{item.citation}</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <p className="text-sm leading-relaxed">{item.content}</p>
                        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <Badge variant="muted">score {item.score.toFixed(3)}</Badge>
                          <Badge variant="outline">semantic {item.semantic_score.toFixed(3)}</Badge>
                          <Badge variant="outline">keyword {item.keyword_score.toFixed(3)}</Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
