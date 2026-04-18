# One-time script: replace conversation rules section
import pathlib

base = pathlib.Path(r"e:\workspace\tool develop\vibe coding facilities\doc based coding")
target = base / ".github" / "copilot-instructions.md"
replacement_src = base / "scripts" / "_new_conversation_section.md"

content = target.read_text(encoding="utf-8")
new_section = replacement_src.read_text(encoding="utf-8").rstrip("\n")

lines = content.split("\n")

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if start_idx is None and "\u5bf9\u8bdd\u884c\u4e3a\u7ea6\u675f" in line:
        start_idx = i
    if "\u5f53\u524d Phase \u5b9e\u65bd\u8fc7\u7a0b\u4e2d\u53d1\u73b0\u7684\u65b0\u9700\u6c42" in line:
        end_idx = i

assert start_idx is not None, "start marker not found"
assert end_idx is not None, "end marker not found"

print(f"Replacing lines {start_idx+1}-{end_idx+1}")

new_lines = lines[:start_idx] + new_section.split("\n") + lines[end_idx + 1:]
target.write_text("\n".join(new_lines), encoding="utf-8")
print("Done")
