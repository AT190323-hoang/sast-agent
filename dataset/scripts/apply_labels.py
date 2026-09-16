#!/usr/bin/env python3
"""Gộp các file nhãn trong dataset/labels/*.json vào dataset/findings_draft.json,
ghi kết quả ra dataset/findings_labeled.json.

Mỗi file trong dataset/labels/ là 1 lô gán nhãn (theo nhóm taxonomy hoặc theo
phiên làm việc), dạng {finding_id: {label, reason, context_needed, confidence}}.
Tách file theo lô để dễ review từng lô qua git diff, không phải sửa tay 1 file
JSON khổng lồ.

findings_draft.json KHÔNG bị sửa (giữ nguyên làm nguồn thô). File
findings_labeled.json là bản build ra, chạy lại script này bất cứ lúc nào sau
khi thêm/sửa file trong dataset/labels/.

Khi mọi nhóm đã gán nhãn xong và được review (T1.8), copy
findings_labeled.json thành findings_v1.json để "freeze" — từ đó không sửa
findings_v1.json nữa, chỉ tạo v2 kèm CHANGELOG nếu cần đổi nhãn sau này.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DRAFT_PATH = REPO_ROOT / "dataset" / "findings_draft.json"
LABELS_DIR = REPO_ROOT / "dataset" / "labels"
OUT_PATH = REPO_ROOT / "dataset" / "findings_labeled.json"

LABEL_FIELDS = ["label", "reason", "context_needed", "confidence"]


def main():
    findings = json.loads(DRAFT_PATH.read_text())
    by_id = {f["id"]: f for f in findings}

    all_labels = {}
    for label_file in sorted(LABELS_DIR.glob("*.json")):
        batch = json.loads(label_file.read_text())
        for fid, fields in batch.items():
            if fid in all_labels:
                raise ValueError(f"ID {fid} bị gán nhãn 2 lần (trong {label_file.name} và lô trước) — kiểm tra trùng lặp giữa các file labels/")
            if fid not in by_id:
                raise ValueError(f"ID {fid} trong {label_file.name} không tồn tại trong findings_draft.json")
            all_labels[fid] = (fields, label_file.name)

    for fid, (fields, fname) in all_labels.items():
        for k in LABEL_FIELDS:
            by_id[fid][k] = fields.get(k)
        by_id[fid]["labeled_by"] = "claude"
        by_id[fid]["labeled_at"] = "2026-09-16"
        by_id[fid]["labeled_from"] = fname

    OUT_PATH.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n")

    labeled = [f for f in findings if f["label"] is not None]
    unlabeled = [f for f in findings if f["label"] is None]
    print(f"Đã gán nhãn: {len(labeled)}/{len(findings)}")
    print(f"Còn thiếu: {len(unlabeled)}")

    from collections import Counter, defaultdict
    per_group = defaultdict(Counter)
    for f in labeled:
        per_group[f["group"]][f["label"]] += 1
    print("\nTP/FP theo nhóm (đã gán):")
    for g in sorted(per_group):
        c = per_group[g]
        total_group = sum(1 for f in findings if f["group"] == g)
        status = "OK" if c["TP"] >= 1 and c["FP"] >= 1 and (c["TP"] + c["FP"]) >= 10 else "⚠️  CHƯA ĐỦ"
        print(f"  {g:20s} TP={c['TP']:2d}  FP={c['FP']:2d}  (tổng nhóm: {total_group})  {status}")

    if unlabeled:
        print("\nCòn lại chưa gán nhãn:")
        per_group_todo = Counter(f["group"] for f in unlabeled)
        for g, c in sorted(per_group_todo.items()):
            print(f"  {g:20s} {c}")


if __name__ == "__main__":
    main()
