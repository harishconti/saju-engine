import {
  DeleteObjectCommand,
  DeleteObjectsCommand,
  GetObjectCommand,
  HeadObjectCommand,
  ListObjectsV2Command,
  PutObjectCommand,
  S3Client,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { prisma } from "./prisma";

/**
 * Cloudflare R2 — private buckets, presigned access only.
 *
 * Everything here is lazily constructed: `next build` runs without runtime secrets, so nothing may
 * throw at module load. Contract and key scheme: docs/webapp/05-report-pipeline.md §3
 */

function config() {
  const accountId = process.env.R2_ACCOUNT_ID;
  const endpoint =
    process.env.R2_ENDPOINT ?? (accountId ? `https://${accountId}.r2.cloudflarestorage.com` : undefined);
  return {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    bucket: process.env.R2_BUCKET,
    endpoint,
  };
}

export function isR2Configured(): boolean {
  const c = config();
  return Boolean(c.accessKeyId && c.secretAccessKey && c.bucket && c.endpoint);
}

let client: S3Client | null = null;

function s3(): S3Client {
  if (!isR2Configured()) {
    throw new Error("R2 is not configured (missing R2_* environment variables)");
  }
  if (!client) {
    const c = config();
    client = new S3Client({
      region: process.env.R2_REGION ?? "auto",
      endpoint: c.endpoint,
      credentials: {
        accessKeyId: c.accessKeyId as string,
        secretAccessKey: c.secretAccessKey as string,
      },
    });
  }
  return client;
}

/**
 * Key scheme leads with userId so a deletion request is one list + one batch delete.
 *   reports/anonymous/{uuid}/sample.{html,pdf} — unclaimed free snapshots (swept after 3 days by the
 *                                                cleanup cron; see lib/retention.ts — nothing else
 *                                                deletes them)
 *   reports/{userId}/{orderId}/{reportId}.pdf
 *   reports/{userId}/{orderId}/{reportId}.md
 */
export function buildReportKey(
  userId: string,
  orderId: string,
  reportId: string,
  // `html` is the web document: the reading the client opens, downloadable as one file.
  ext: "pdf" | "md" | "mp3" | "html",
): string {
  return `reports/${userId}/${orderId}/${reportId}.${ext}`;
}

export function buildAnonymousKey(uuid: string, ext: "pdf" | "md" | "html" = "pdf"): string {
  return `reports/anonymous/${uuid}/sample.${ext}`;
}

/**
 * A sample a signed-in user has kept.
 *
 * Deliberately NOT under `reports/anonymous/`: that prefix is swept by age, and a saved sample
 * belongs to its owner until they delete it.
 */
export function buildSampleKey(userId: string, uuid: string, ext: "pdf" | "md" | "html" = "pdf"): string {
  return `reports/${userId}/samples/${uuid}.${ext}`;
}

/** Every object under a prefix, with its last-modified time. Paginates. */
export async function listObjectsByPrefix(
  prefix: string,
  max = 1000,
): Promise<{ key: string; lastModified: Date | null }[]> {
  const c = config();
  const out: { key: string; lastModified: Date | null }[] = [];
  let token: string | undefined;
  do {
    const res = await s3().send(
      new ListObjectsV2Command({ Bucket: c.bucket as string, Prefix: prefix, ContinuationToken: token }),
    );
    for (const obj of res.Contents ?? []) {
      if (obj.Key) out.push({ key: obj.Key, lastModified: obj.LastModified ?? null });
      if (out.length >= max) return out;
    }
    token = res.IsTruncated ? res.NextContinuationToken : undefined;
  } while (token);
  return out;
}

export function objectKeyFromPdfKey(pdfKey: string): string {
  return pdfKey;
}

export async function presignPutUrl(key: string, contentType = "application/pdf", expiresIn = 600): Promise<string> {
  const c = config();
  return getSignedUrl(
    s3(),
    new PutObjectCommand({ Bucket: c.bucket as string, Key: key, ContentType: contentType }),
    { expiresIn },
  );
}

/**
 * Direct PUT from the webapp.
 *
 * The engine uploads the PDF and the source markdown via presigned URLs, but the MP3 is
 * produced *here* (the voice call is ours), so it has to be written here too.
 */
export async function putObject(key: string, body: Buffer | Uint8Array, contentType: string): Promise<void> {
  const c = config();
  await s3().send(
    new PutObjectCommand({
      Bucket: c.bucket as string,
      Key: key,
      Body: body,
      ContentType: contentType,
      ContentLength: body.byteLength,
    }),
  );
}

/** Read a small text artefact (the source markdown) back out of R2. */
export async function getObjectText(key: string): Promise<string | null> {
  try {
    const c = config();
    const res = await s3().send(new GetObjectCommand({ Bucket: c.bucket as string, Key: key }));
    if (!res.Body) return null;
    return Buffer.from(await res.Body.transformToByteArray()).toString("utf-8");
  } catch (err) {
    console.error("r2 read failed", err instanceof Error ? err.name : "unknown");
    return null;
  }
}

/** Short-lived signed GET. Buckets are private; there is no public URL. */
export async function presignGetUrl(key: string, expiresIn = 3600): Promise<string> {
  const c = config();
  return getSignedUrl(s3(), new GetObjectCommand({ Bucket: c.bucket as string, Key: key }), { expiresIn });
}

export async function headObject(key: string): Promise<{ size: number } | null> {
  try {
    const c = config();
    const res = await s3().send(new HeadObjectCommand({ Bucket: c.bucket as string, Key: key }));
    return { size: Number(res.ContentLength ?? 0) };
  } catch {
    return null;
  }
}

export async function deleteObject(key: string): Promise<void> {
  const c = config();
  await s3().send(new DeleteObjectCommand({ Bucket: c.bucket as string, Key: key }));
}

/** Batch delete, up to 1000 keys per call. */
export async function deleteObjects(keys: string[]): Promise<{ deleted: string[]; failed: string[] }> {
  if (keys.length === 0) return { deleted: [], failed: [] };
  const c = config();
  const res = await s3().send(
    new DeleteObjectsCommand({
      Bucket: c.bucket as string,
      Delete: { Objects: keys.map((Key) => ({ Key })), Quiet: false },
    }),
  );
  const deleted = (res.Deleted ?? []).map((d) => d.Key!).filter(Boolean);
  const failed = (res.Errors ?? []).map((e) => e.Key!).filter(Boolean);
  return { deleted, failed };
}

/**
 * Queue a failed delete. "The delete failed" must never mean "the file stays forever" —
 * the daily cleanup cron drains this table.
 */
export async function queueObjectDeletion(fileKey: string, lastError: string): Promise<void> {
  await prisma.objectDeletion.create({ data: { fileKey, lastError } });
}

/** Best-effort delete: succeed quietly, otherwise enqueue for retry. */
export async function deleteObjectOrQueue(fileKey: string): Promise<void> {
  if (!isR2Configured()) {
    await queueObjectDeletion(fileKey, "R2 not configured");
    return;
  }
  try {
    await deleteObject(fileKey);
  } catch (err) {
    await queueObjectDeletion(fileKey, err instanceof Error ? err.name : "unknown");
  }
}

/** Drain the deletion queue in batches. Attempt cap prevents an infinite retry loop. */
export async function drainObjectDeletions(limit = 200): Promise<{ deleted: number; failed: number; abandoned: number }> {
  const rows = await prisma.objectDeletion.findMany({ orderBy: { createdAt: "asc" }, take: limit });
  if (rows.length === 0) return { deleted: 0, failed: 0, abandoned: 0 };

  const retryable = rows.filter((r) => r.attempts < 10);
  const abandoned = rows.length - retryable.length;
  if (abandoned > 0) {
    await prisma.objectDeletion.deleteMany({
      where: { id: { in: rows.filter((r) => r.attempts >= 10).map((r) => r.id) } },
    });
  }
  if (retryable.length === 0) return { deleted: 0, failed: 0, abandoned };

  const { deleted, failed } = await deleteObjects(retryable.map((r) => r.fileKey));
  await prisma.objectDeletion.deleteMany({
    where: { fileKey: { in: deleted } },
  });
  await prisma.objectDeletion.updateMany({
    where: { fileKey: { in: failed } },
    data: { attempts: { increment: 1 }, lastError: "batch delete failed" },
  });
  return { deleted: deleted.length, failed: failed.length, abandoned };
}
