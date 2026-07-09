import { FileUp, FolderOpen, Globe, Upload } from "lucide-react";
import { FormEvent, useRef, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useIngestUrl, useUploadDocuments } from "@/hooks/use-documents";

type UploadZoneProps = {
  onUploaded?: () => void;
  organizationId?: string;
};

export function UploadZone({ onUploaded, organizationId }: UploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const uploadDocuments = useUploadDocuments(organizationId);
  const ingestUrl = useIngestUrl(organizationId);

  async function handleFiles(files: FileList | File[]) {
    const list = Array.from(files);
    if (!list.length) return;
    setError(null);
    setUploadProgress(0);
    try {
      await uploadDocuments.mutateAsync({
        files: list,
        onProgress: setUploadProgress,
      });
      setUploadProgress(100);
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setUploadProgress(null);
    }
  }

  async function onUrlSubmit(event: FormEvent) {
    event.preventDefault();
    if (!url.trim()) return;
    setError(null);
    try {
      await ingestUrl.mutateAsync({ url: url.trim() });
      setUrl("");
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "URL ingest failed.");
    }
  }

  return (
    <Card
      className={`border-dashed transition-colors ${dragOver ? "border-primary bg-primary/5" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragOver(false);
        if (event.dataTransfer.files?.length) {
          void handleFiles(event.dataTransfer.files);
        }
      }}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Upload documents
        </CardTitle>
        <CardDescription>
          PDF, DOCX, TXT, CSV, Markdown, Office, JSON, HTML, images, and ZIP archives.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error ? <Alert variant="destructive">{error}</Alert> : null}
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(event) => event.target.files && void handleFiles(event.target.files)}
          />
          <input
            ref={folderInputRef}
            type="file"
            multiple
            className="hidden"
            // @ts-expect-error webkitdirectory is supported in Chromium browsers
            webkitdirectory=""
            onChange={(event) => event.target.files && void handleFiles(event.target.files)}
          />
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadDocuments.isPending}
          >
            <FileUp className="h-4 w-4" />
            Choose files
          </Button>
          <Button
            variant="outline"
            onClick={() => folderInputRef.current?.click()}
            disabled={uploadDocuments.isPending}
          >
            <FolderOpen className="h-4 w-4" />
            Upload folder
          </Button>
        </div>
        {uploadProgress !== null ? (
          <Progress value={uploadProgress} label="Uploading files" />
        ) : null}
        <form onSubmit={onUrlSubmit} className="grid gap-2 md:grid-cols-[1fr_auto]">
          <div className="space-y-2">
            <Label htmlFor="source-url">Website URL</Label>
            <Input
              id="source-url"
              placeholder="https://example.com/policy"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button type="submit" disabled={ingestUrl.isPending}>
              <Globe className="h-4 w-4" />
              Add URL
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
