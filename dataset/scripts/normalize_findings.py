#!/usr/bin/env python3
"""Gộp các file JSON output thô của Opengrep (reports/week1/) thành 1 dataset
nháp chưa gán nhãn (dataset/findings_draft.json).

Việc script làm:
  - Đọc từng file kết quả Opengrep, gắn source_app + base_path tương ứng
  - Chuẩn hoá field theo schema trong docs/ke-hoach-6-tuan.md
  - Map mỗi rule_id về 1 trong 4 nhóm taxonomy (rule custom đã tự khai trong
    metadata.taxonomy; rule registry dùng bảng ánh xạ tường minh RULE_GROUP_MAP
    bên dưới - PHẢI review bằng tay khi thêm rule mới, không đoán tự động)
  - Khử trùng lặp theo (source_app, file, start_line, end_line, rule_id)
  - Gán id ổn định: JS-0001..., CRAPI-0001...

Chạy lại: python3 dataset/scripts/normalize_findings.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports" / "week1"
OUT_PATH = REPO_ROOT / "dataset" / "findings_draft.json"

# (file_name, source_app, base_path để tính rel path)
INPUT_FILES = [
    ("findings_raw.json", "juice-shop", "/home/hoanglh98/projects/targets/juice-shop"),
    ("findings_raw_auto.json", "juice-shop", "/home/hoanglh98/projects/targets/juice-shop"),
    ("findings_raw_custom.json", "juice-shop", "/home/hoanglh98/projects/targets/juice-shop"),
    ("findings_raw_crapi_workshop.json", "crapi", "/home/hoanglh98/projects/targets/crapi"),
    ("findings_raw_crapi_identity.json", "crapi", "/home/hoanglh98/projects/targets/crapi"),
    ("findings_raw_crapi_broken_invariant.json", "crapi", "/home/hoanglh98/projects/targets/crapi"),
]

ID_PREFIX = {"juice-shop": "JS", "crapi": "CRAPI"}

# Rule registry -> taxonomy. Chỉ áp dụng cho rule KHÔNG có metadata.taxonomy
# (tức rule custom của mình). Nguyên tắc phân loại: xem docs/taxonomy.md
# (sẽ viết ở T1.7). Mọi check_id mới xuất hiện mà không có trong bảng này sẽ
# bị đánh dấu group="UNCLASSIFIED" để bắt buộc review thủ công, không đoán.
RULE_GROUP_MAP = {
    # --- JavaScript/TypeScript (Juice Shop) ---
    "javascript.browser.security.eval-detected.eval-detected": "taint_flow",
    "javascript.express.security.audit.express-check-directory-listing.express-check-directory-listing": "insecure_property",
    "javascript.express.security.audit.express-detect-notevil-usage.express-detect-notevil-usage": "taint_flow",
    "javascript.express.security.audit.express-open-redirect.express-open-redirect": "taint_flow",
    "javascript.express.security.audit.express-res-sendfile.express-res-sendfile": "taint_flow",
    "javascript.express.security.audit.remote-property-injection.remote-property-injection": "taint_flow",
    "javascript.express.security.audit.possible-user-input-redirect.unknown-value-in-redirect": "taint_flow",
    "javascript.express.security.injection.tainted-sql-string.tainted-sql-string": "taint_flow",
    "javascript.jsonwebtoken.security.jwt-hardcode.hardcoded-jwt-secret": "insecure_property",
    "javascript.lang.security.audit.code-string-concat.code-string-concat": "taint_flow",
    "javascript.lang.security.audit.detect-non-literal-regexp.detect-non-literal-regexp": "taint_flow",
    "javascript.lang.security.audit.hardcoded-hmac-key.hardcoded-hmac-key": "insecure_property",
    "javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal": "taint_flow",
    "javascript.lang.security.audit.unknown-value-with-script-tag.unknown-value-with-script-tag": "taint_flow",
    "javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring": "taint_flow",
    "javascript.sequelize.security.audit.sequelize-injection-express.express-sequelize-injection": "taint_flow",
    # --- Python/Django (crAPI workshop) ---
    "python.django.security.audit.csrf-exempt.no-csrf-exempt": "insecure_property",
    "python.django.security.audit.django-rest-framework.missing-throttle-config.missing-throttle-config": "missing_control",
    "python.django.security.injection.tainted-sql-string.tainted-sql-string": "taint_flow",
    "python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2": "taint_flow",
    "python.requests.security.disabled-cert-validation.disabled-cert-validation": "insecure_property",
    "python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query": "taint_flow",
    # --- Java (crAPI identity) ---
    "generic.secrets.security.detected-private-key.detected-private-key": "insecure_property",
    "java.lang.security.audit.crypto.ssl.insecure-hostname-verifier.insecure-hostname-verifier": "insecure_property",
    "java.spring.security.audit.spring-csrf-disabled.spring-csrf-disabled": "insecure_property",
    "problem-based-packs.insecure-transport.java-stdlib.disallow-old-tls-versions1.disallow-old-tls-versions1": "insecure_property",
}


def classify(check_id: str, metadata: dict) -> tuple[str, str]:
    """Trả về (group, rule_source)."""
    if "taxonomy" in metadata:
        return metadata["taxonomy"], "custom"
    return RULE_GROUP_MAP.get(check_id, "UNCLASSIFIED"), "registry"


def load_results(fname: str, source_app: str, base_path: str):
    fpath = REPORTS_DIR / fname
    data = json.loads(fpath.read_text())
    base = Path(base_path)
    out = []
    for r in data.get("results", []):
        extra = r.get("extra", {})
        metadata = extra.get("metadata", {})
        group, rule_source = classify(r["check_id"], metadata)
        try:
            rel_path = str(Path(r["path"]).relative_to(base))
        except ValueError:
            rel_path = r["path"]
        out.append({
            "source_app": source_app,
            "tool": "opengrep-1.30.0",
            "rule_id": r["check_id"],
            "rule_source": rule_source,
            "severity": extra.get("severity"),
            "cwe": metadata.get("cwe", []),
            "group": group,
            "file": rel_path,
            "start_line": r["start"]["line"],
            "end_line": r["end"]["line"],
            "code_snippet": extra.get("lines", "").strip(),
            "tool_message": extra.get("message", "").strip(),
            # Điền ở bước gán nhãn (T1.6):
            "label": None,
            "reason": None,
            "context_needed": None,
            "confidence": None,
            "labeled_by": None,
            "labeled_at": None,
        })
    return out


def dedupe(findings):
    seen = {}
    for f in findings:
        key = (f["source_app"], f["file"], f["start_line"], f["end_line"], f["rule_id"])
        seen[key] = f  # file sau đè file trước nhưng nội dung giống hệt nên không mất gì
    return list(seen.values())


def content_key(f):
    return (f["source_app"], f["file"], f["start_line"], f["end_line"], f["rule_id"])


def load_existing_ids():
    """Đọc findings_draft.json hiện có (nếu có) để TÁI SỬ DỤNG id cũ.

    Bắt buộc phải làm vậy: dataset/labels/*.json tham chiếu finding theo id
    (vd "JS-0007"). Nếu chạy lại script mà đánh số lại từ đầu, id có thể trỏ
    sang finding khác, âm thầm làm sai toàn bộ nhãn đã gán trước đó.
    """
    if not OUT_PATH.exists():
        return {}
    existing = json.loads(OUT_PATH.read_text())
    return {content_key(f): f["id"] for f in existing}


def assign_ids(findings):
    existing_ids = load_existing_ids()
    counters = {}
    # Số đã dùng cho mỗi prefix, để id mới không trùng id cũ đã tồn tại.
    for eid in existing_ids.values():
        prefix, num = eid.rsplit("-", 1)
        counters[prefix] = max(counters.get(prefix, 0), int(num))

    # Finding đã có id giữ nguyên thứ tự/id cũ; finding mới nối vào cuối
    # theo prefix, không sắp xếp lại toàn bộ (tránh xáo trộn id đã gán nhãn).
    findings.sort(key=lambda f: (f["source_app"], f["file"], f["start_line"]))
    reused, new = [], []
    for f in findings:
        key = content_key(f)
        if key in existing_ids:
            f["id"] = existing_ids[key]
            reused.append(f)
        else:
            new.append(f)

    for f in new:
        prefix = ID_PREFIX[f["source_app"]]
        counters[prefix] = counters.get(prefix, 0) + 1
        f["id"] = f"{prefix}-{counters[prefix]:04d}"

    print(f"ID giữ nguyên: {len(reused)}  |  ID mới cấp: {len(new)}")
    all_final = sorted(reused + new, key=lambda f: f["id"])
    return [{"id": f["id"], **{k: v for k, v in f.items() if k != "id"}} for f in all_final]


def main():
    all_findings = []
    for fname, source_app, base_path in INPUT_FILES:
        all_findings.extend(load_results(fname, source_app, base_path))

    print(f"Tổng finding thô (chưa dedupe): {len(all_findings)}")
    deduped = dedupe(all_findings)
    print(f"Sau khi dedupe: {len(deduped)}")

    unclassified = [f for f in deduped if f["group"] == "UNCLASSIFIED"]
    if unclassified:
        print(f"\n⚠️  {len(unclassified)} finding chưa map được nhóm — cần bổ sung RULE_GROUP_MAP:")
        for f in unclassified:
            print(f"   {f['rule_id']}  ({f['file']}:{f['start_line']})")

    final = assign_ids(deduped)
    OUT_PATH.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n")
    print(f"\nĐã ghi {len(final)} finding vào {OUT_PATH.relative_to(REPO_ROOT)}")

    from collections import Counter
    print("\nPhân bố theo nhóm:")
    for g, c in sorted(Counter(f["group"] for f in final).items()):
        print(f"  {g:20s} {c}")
    print("\nPhân bố theo app:")
    for a, c in sorted(Counter(f["source_app"] for f in final).items()):
        print(f"  {a:20s} {c}")
    print("\nPhân bố theo rule_source:")
    for s, c in sorted(Counter(f["rule_source"] for f in final).items()):
        print(f"  {s:20s} {c}")


if __name__ == "__main__":
    main()
