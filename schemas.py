"""技能输入契约（本仓库只保留该技能的输入模型）。

裁剪自田头农技台的 `skills/schemas.py`：输出模型仅用于生成文档、
不参与校验，独立发布时不需要，因此整段删去。
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator


def _check_iso_date(value: str) -> str:
    """校验 YYYY-MM-DD，返回原字符串。"""
    text = str(value or "").strip()
    try:
        date.fromisoformat(text)
    except ValueError as e:
        raise ValueError("日期格式应为 YYYY-MM-DD") from e
    return text


class CropDiagnosisInput(BaseModel):
    """病虫害检测与多模态诊断的输入。

    图片/音频各支持 base64 与本地路径二选一：HTTP 只允许 base64，CLI 两种都行。
    至少提供图片、语音、文字中的一项。
    """

    image_base64: str | None = Field(None, description="图片 base64；允许 data:image/...;base64, 前缀")
    image_path: str | None = Field(None, description="本地图片路径，仅 CLI 可用")
    audio_base64: str | None = Field(None, description="音频 base64；允许 data:audio/...;base64, 前缀")
    audio_path: str | None = Field(None, description="本地音频路径，仅 CLI 可用")
    audio_format: str = Field("auto", description="auto / wav / pcm / amr / mp3")
    text: str = Field("", max_length=4000, description="文字症状描述")
    dialect: str | None = Field(None, description="方言 key；留空用默认方言")
    topk: int = Field(5, ge=1, le=10, description="病害候选数量")

    @model_validator(mode="after")
    def _validate_inputs(self) -> "CropDiagnosisInput":
        if self.image_base64 and self.image_path:
            raise ValueError("image_base64 与 image_path 只能二选一")
        if self.audio_base64 and self.audio_path:
            raise ValueError("audio_base64 与 audio_path 只能二选一")
        if not any((
            self.image_base64, self.image_path,
            self.audio_base64, self.audio_path,
            (self.text or "").strip(),
        )):
            raise ValueError("请至少提供图片、语音或文字中的一项")
        return self
