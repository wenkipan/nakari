from __future__ import annotations


def test_persona_yaml_parsing_smoke(tmp_path) -> None:
    from memory.personality import load_persona_config

    p = tmp_path / "persona.yaml"
    p.write_text(
        (
            """
emotions:
  init_range: [0.3, 0.7]
  types: [happy]
preferences:
  concepts:
    - content: "cyberpunk"
      emotions:
        love: 0.8
""".lstrip()
        ),
        encoding="utf-8",
    )

    cfg = load_persona_config(str(p))
    assert cfg["emotions"]["types"] == ["happy"]
