# crop-diagnosis · 病虫害检测与多模态融合诊断

从「田头农技台」抽出的一个技能包。输入作物照片、方言语音或文字症状，输出病害候选、虫害检测框、
融合诊断报告与防治方案，三种输入可以任意组合。

`SKILL.md` 是给 AI Agent 读的技能说明，`handler.py` 是可执行实现，两者描述同一套契约。

## 文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 技能说明：能力范围、输入输出字段、HTTP 与 CLI 用法、降级语义 |
| `handler.py` | 入口 `run(payload, *, allow_paths=True) -> dict` |
| `schemas.py` | `CropDiagnosisInput`，pydantic 模型，真正参与校验 |
| `errors.py` | 技能层异常，由 HTTP 层映射成 400 / 413 / 503 |

## 装配到宿主

本技能不是独立服务：推理链路在宿主项目的 `src/` 下，`handler.py` 只做参数收敛与编排，
不复制任何推理逻辑。装配路径与上游一致：

```
<repo>/
├── skills/
│   ├── errors.py            # 复制本仓库 errors.py
│   ├── schemas.py           # 把本仓库 schemas.py 的输入模型并进去
│   └── crop_diagnosis/
│       ├── __init__.py      # from . import handler
│       ├── handler.py       # 本仓库 handler.py
│       └── SKILL.md
```

`handler.py` 里的导入按 `skills.errors`、`skills.schemas` 书写，对应的就是上面这套目录结构。
推理侧由它按需导入 `src.llm.fusion.get_fusion()`，宿主需要提供该入口。

## 调用

HTTP（宿主暴露的路由名）：

```bash
curl -X POST http://127.0.0.1:8000/api/skills/crop-diagnosis \
  -H "Content-Type: application/json" \
  -d '{"text":"水稻叶片有褐色斑点，最近多雨"}'
```

图片要先转 base64，HTTP 不接受本地路径，避免任意文件读取：

```bash
python - <<'PY'
import base64, json, pathlib
p = pathlib.Path("leaf.jpg")
print(json.dumps({"image_base64": base64.b64encode(p.read_bytes()).decode(),
                  "text": "看看这是什么病"}, ensure_ascii=False))
PY
```

CLI（宿主提供 `python -m skills`）：

```bash
python -m skills run crop-diagnosis --input payload.json --pretty
python -m skills run crop-diagnosis --input - --pretty     # 从 stdin 读
```

直接调用 handler：

```python
from skills.crop_diagnosis.handler import run

result = run({"text": "玉米叶片边缘发黄，叶背有灰霉"})
print(result["report"]["summary"])
```

## 依赖

- Python 3.10+
- pydantic ≥ 2.6（输入校验）
- 运行期由宿主提供：ONNX Runtime、病害分类模型（PDD271，271 类）、虫害检测模型（IP102，102 类）、
  大模型与 RAG 检索、语音服务

缺其中任何一项都不会让整个调用失败，按 `SKILL.md` 的降级语义在 `degraded` 里如实标注。

## 边界

- 单文件解码后不超过 20 MB；HTTP 只收 base64。
- 病害名限定在图像识别给出的闭集候选内，不接受模型自创病名。
- 虫害没有闭集，只保留检测器实际框出的类别。
- 诊断结果与防治建议仅供参考，不构成用药指令；用药以当地植保部门指导和农药登记标签为准。
