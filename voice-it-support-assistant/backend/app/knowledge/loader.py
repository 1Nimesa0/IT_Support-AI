"""
Knowledge Base Loader for SOP Documents.
Parses Markdown files with YAML FrontMatter metadata.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import yaml


class SOPStep(BaseModel):
    step_id: int
    action: str
    instruction_spoken: str
    expected_confirmation: List[str] = Field(default_factory=list)
    fallback_instruction: str = ""
    shortcut: Optional[str] = None


class SOPDocument(BaseModel):
    sop_id: str
    title: str
    category: str
    symptoms: List[str] = Field(default_factory=list)
    prerequisites: Dict[str, Any] = Field(default_factory=dict)
    steps: List[SOPStep] = Field(default_factory=list)
    raw_markdown: str = ""
    body_text: str = ""

    def get_step(self, step_id: int) -> Optional[SOPStep]:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_step_count(self) -> int:
        return len(self.steps)

    def to_chunk_text(self) -> str:
        """Render a concise text representation for semantic embedding and LLM prompt grounding."""
        step_lines = []
        for s in self.steps:
            shortcuts = f" [Phím tắt: {s.shortcut}]" if s.shortcut else ""
            step_lines.append(
                f"- Bước {s.step_id}: {s.action}. Lời thoại: \"{s.instruction_spoken}\"{shortcuts}. "
                f"Xác nhận mong đợi: {', '.join(s.expected_confirmation)}. Dự phòng: \"{s.fallback_instruction}\""
            )

        symptoms_str = ", ".join(self.symptoms)
        prereqs_str = ", ".join([f"{k}: {v}" for k, v in self.prerequisites.items()])

        return (
            f"Mã SOP: {self.sop_id}\n"
            f"Tiêu đề: {self.title}\n"
            f"Phân loại: {self.category}\n"
            f"Triệu chứng: {symptoms_str}\n"
            f"Điều kiện tiên quyết: {prereqs_str}\n"
            f"Các bước xử lý:\n" + "\n".join(step_lines)
        )


class SOPLoader:
    def __init__(self, sops_dir: Optional[Path | str] = None):
        if sops_dir is None:
            self.sops_dir = Path(__file__).parent / "sops"
        else:
            self.sops_dir = Path(sops_dir)
        self.documents: Dict[str, SOPDocument] = {}
        self.load_all()

    def load_all(self) -> Dict[str, SOPDocument]:
        """Loads and parses all Markdown SOP files in the sops directory."""
        if not self.sops_dir.exists():
            return {}

        docs: Dict[str, SOPDocument] = {}
        for file_path in sorted(self.sops_dir.glob("*.md")):
            doc = self.parse_sop_file(file_path)
            if doc:
                docs[doc.sop_id] = doc

        self.documents = docs
        return self.documents

    @staticmethod
    def parse_sop_file(file_path: Path) -> Optional[SOPDocument]:
        """Parses a single Markdown file containing YAML frontmatter."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Extract YAML Frontmatter between --- delimiters
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not frontmatter_match:
            return None

        yaml_str = frontmatter_match.group(1)
        body_text = frontmatter_match.group(2).strip()

        try:
            meta = yaml.safe_load(yaml_str) or {}
        except Exception:
            return None

        sop_id = meta.get("sop_id", "")
        if not sop_id:
            return None

        raw_steps = meta.get("steps", [])
        parsed_steps: List[SOPStep] = []
        for step in raw_steps:
            parsed_steps.append(
                SOPStep(
                    step_id=int(step.get("step_id", len(parsed_steps) + 1)),
                    action=str(step.get("action", "")),
                    instruction_spoken=str(step.get("instruction_spoken", "")),
                    expected_confirmation=step.get("expected_confirmation", []) or [],
                    fallback_instruction=str(step.get("fallback_instruction", "")),
                    shortcut=step.get("shortcut"),
                )
            )

        return SOPDocument(
            sop_id=sop_id,
            title=meta.get("title", file_path.stem),
            category=meta.get("category", "General"),
            symptoms=meta.get("symptoms", []) or [],
            prerequisites=meta.get("prerequisites", {}) or {},
            steps=parsed_steps,
            raw_markdown=content,
            body_text=body_text,
        )

    def get(self, sop_id: str) -> Optional[SOPDocument]:
        return self.documents.get(sop_id)

    def all(self) -> List[SOPDocument]:
        return list(self.documents.values())


# Global singleton instance for easy import
sop_loader = SOPLoader()
