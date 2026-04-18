# doc-based-coding 瀹夎鎸囧崡

鏈枃妗ｉ潰鍚?AI 缂栫▼鍔╂墜锛圕opilot銆丆odex 绛夛級锛屾彁渚涗粠闆跺畨瑁呮湰骞冲彴鐨勭簿纭楠ゃ€?

## 姒傝堪

鏈彂琛屽寘鍖呭惈涓や釜 Python wheel锛?

| 鏂囦欢 | 鍖呭悕 | 鑱岃矗 |
|------|------|------|
| `doc_based_coding_runtime-0.9.3-py3-none-any.whl` | doc-based-coding-runtime | 骞冲彴 runtime / CLI / MCP server |
| `doc_loop_vibe_coding-0.9.3-py3-none-any.whl` | doc-loop-vibe-coding | 瀹樻柟瀹炰緥 pack锛堟枃妗ｉ┍鍔ㄥ伐浣滄祦妯℃澘涓庤祫浜э級 |

渚濊禆鍏崇郴锛氬疄渚嬪寘渚濊禆 runtime 鍖咃紙`doc-based-coding-runtime>=0.9.3,<1.0.0`锛夈€?

## 鍓嶇疆瑕佹眰

- Python >= 3.10
- pip >= 22.0

## 瀹夎姝ラ

### 1. 鍒涘缓铏氭嫙鐜锛堟帹鑽愶級

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. 瀹夎 runtime 鍖?

```bash
pip install doc_based_coding_runtime-0.9.3-py3-none-any.whl
```

杩欏皢鍚屾椂瀹夎鎵€鏈変緷璧栵紙jsonschema銆乵cp 绛夛級銆?

### 3. 瀹夎瀹樻柟瀹炰緥鍖?

```bash
pip install doc_loop_vibe_coding-0.9.3-py3-none-any.whl
```

鐢变簬 runtime 宸插畨瑁咃紝姝ゆ楠や笉浼氶噸澶嶆媺鍙栦緷璧栥€?

> **鏈湴绂荤嚎瀹夎鎻愮ず**锛氬鏋滀綘鍦ㄧ绾跨幆澧冧腑浠庢湰鍦?wheel 瀹夎锛宲ip 鍙兘鏃犳硶鑷姩瑙ｆ瀽鍚岀洰褰曚腑鐨勪緷璧栥€傛帹鑽愪互涓嬫柟寮忎箣涓€锛?
>
> ```bash
> # 鏂瑰紡 A锛氭寜椤哄簭閫愪釜瀹夎锛堟帹鑽愶級
> pip install --force-reinstall doc_based_coding_runtime-0.9.3-py3-none-any.whl
> pip install --force-reinstall --no-deps doc_loop_vibe_coding-0.9.3-py3-none-any.whl
>
> # 鏂瑰紡 B锛氫娇鐢?--find-links 璁?pip 浠庡綋鍓嶇洰褰曟煡鎵句緷璧?
> pip install --force-reinstall --no-index --find-links . doc_loop_vibe_coding-0.9.3-py3-none-any.whl
> ```
>
> 濡傛灉涔嬪墠宸插畨瑁呮棫鐗堟湰锛屽缓璁厛 `pip uninstall` 鍐嶅畨瑁咃紝閬垮厤鐗堟湰鍐茬獊銆?

### 4. 楠岃瘉瀹夎

```bash
# 楠岃瘉 runtime CLI
doc-based-coding --help

# 楠岃瘉 runtime 鑳藉彂鐜?pack锛堝寘鎷?pip 瀹夎鐨勫畼鏂瑰疄渚?pack锛?
doc-based-coding info

# 楠岃瘉绾︽潫妫€鏌?
doc-based-coding validate

# 楠岃瘉瀹炰緥鍖?CLI
doc-loop-bootstrap --help
doc-loop-validate-instance --help
```

> **Pack 鑷姩鍙戠幇**锛歳untime 浼氳嚜鍔ㄥ彂鐜颁互涓嬩綅缃殑 pack锛?
> 1. `.codex/packs/` 鐩綍涓嬬殑 `*.pack.json` 鏂囦欢锛堥」鐩湰鍦?pack锛?
> 2. 椤圭洰鏍圭洰褰曠殑涓€绾у瓙鐩綍涓殑 `pack-manifest.json`
> 3. 閫氳繃 pip 瀹夎鍒?Python 鐜涓殑 pack锛堝 `doc-loop-vibe-coding`锛?
>
> 鍥犳锛屾墽琛?`pip install` 鍚庢棤闇€棰濆閰嶇疆锛宍doc-based-coding info` 鍗冲彲鐪嬪埌宸插畨瑁呯殑瀹樻柟 pack銆?
> 濡傞渶瑕嗙洊鑷姩鍙戠幇锛屽彲鍒涘缓 `.codex/platform.json` 骞舵寚瀹?`pack_dirs`銆?

#### 鐞嗚В validate 杈撳嚭

`validate` 鍛戒护鐨?JSON 杈撳嚭鍖呭惈浠ヤ笅鍏抽敭瀛楁锛?

| 瀛楁 | 鍚箟 |
|------|------|
| `command_status` | 鍛戒护鏄惁姝ｅ父杩愯锛堝缁堜负 `"ok"`锛屽鏋滆緭鍑轰簡 JSON 灏辫鏄庡钩鍙版甯革級 |
| `governance_status` | 娌荤悊鍐崇瓥鐘舵€侊細`"passed"` 鎴?`"blocked"` |
| `blocking_constraints` | 琚樆濉炵殑绾︽潫 ID 鍒楄〃锛堝 `["C5"]`锛?|

**閫€鍑虹爜璇箟锛?*

| 閫€鍑虹爜 | 鍚箟 |
|--------|------|
| 0 | 鍛戒护鎴愬姛锛屾不鐞嗘棤闃诲 |
| 1 | 鍛戒护杩愯寮傚父锛坮untime error锛?|
| 2 | 鍛戒护鎴愬姛锛屼絾娌荤悊绾︽潫闃诲 |

> **閲嶈**锛氬湪鍒?bootstrap 鐨勯」鐩腑锛宍validate` 鍙兘浼氭姤鍛?C5 绾︽潫锛堢己灏?planning-gate 鏂囨。锛夛紝姝ゆ椂 `command_status` 浠嶄负 `"ok"`锛宻everity 涓?`"warn"`銆傝繖鏄甯哥殑娌荤悊鎻愮ず锛屼笉鏄畨瑁呭け璐ャ€傚垱寤?planning-gate 鏂囨。鍚庣害鏉熷嵆瑙ｉ櫎銆?

## 鍦ㄩ」鐩腑鍚敤鏂囨。椹卞姩宸ヤ綔娴?

### 鏂瑰紡 A锛欱ootstrap 鏂伴」鐩?

鍦ㄧ洰鏍囬」鐩牴鐩綍涓繍琛岋細

```bash
doc-loop-bootstrap --target /path/to/your/project --project-name "Your Project Name"
```

杩欏皢鍦ㄧ洰鏍囩洰褰曚腑鐢熸垚锛?
- `AGENTS.md` 鈥?agent 宸ヤ綔鎸囦护
- `design_docs/` 鈥?鐘舵€佹澘銆侀樁娈垫枃妗ｃ€佸伐鍏锋爣鍑?
- `.codex/` 鈥?pack 閰嶇疆銆佸悎鍚屾ā鏉裤€佹彁绀鸿瘝銆乭andoff

### 鏂瑰紡 B锛氭墜鍔ㄩ厤缃?MCP Server

鍦ㄤ綘鐨?VS Code 椤圭洰涓垱寤烘垨缂栬緫 `.vscode/mcp.json`锛?

```json
{
  "servers": {
    "doc-based-coding-governance": {
      "type": "stdio",
      "command": "doc-based-coding-mcp",
      "args": ["--project", "${workspaceFolder}"]
    }
  }
}
```

MCP server 鍚姩鍚庯紝鍦?Copilot Chat 涓彲浠ヨ皟鐢ㄤ互涓嬫不鐞嗗伐鍏凤細
- `check_constraints` 鈥?妫€鏌ラ」鐩害鏉熺姸鎬?
- `governance_decide` 鈥?瀵圭敤鎴疯緭鍏ユ墽琛屽畬鏁存不鐞嗛摼
- `get_next_action` 鈥?鑾峰彇涓嬩竴姝ュ缓璁鍔?
- `get_pack_info` 鈥?鏌ョ湅宸插姞杞界殑 pack 淇℃伅
- `writeback_notify` 鈥?safe-stop 鏃惰幏鍙栧繀瑕佸啓鍥炴竻鍗?

## 鍙敤 CLI 鍛戒护涓€瑙?

### Runtime锛坉oc-based-coding锛?

| 鍛戒护 | 璇存槑 |
|------|------|
| `doc-based-coding process <text>` | 瀵硅緭鍏ユ墽琛屽畬鏁存不鐞嗛摼锛坉ry-run锛?|
| `doc-based-coding info` | 鏄剧ず宸插姞杞界殑 pack 淇℃伅 |
| `doc-based-coding validate` | 妫€鏌ラ」鐩害鏉熺姸鎬?|
| `doc-based-coding check [text]` | 浠呮墽琛岀害鏉?鐘舵€佹鏌?|
| `doc-based-coding generate-instructions` | 鐢熸垚 copilot-instructions 鐗囨 |

### 瀹炰緥鍖咃紙doc-loop-vibe-coding锛?

| 鍛戒护 | 璇存槑 |
|------|------|
| `doc-loop-bootstrap` | 灏嗘枃妗ｉ┍鍔ㄥ伐浣滄祦鑴氭墜鏋跺鍒跺埌鐩爣浠撳簱 |
| `doc-loop-validate-doc` | 楠岃瘉鏂囨。缁撴瀯绗﹀悎宸ヤ綔娴佹爣鍑?|
| `doc-loop-validate-instance` | 楠岃瘉瀹炰緥 pack manifest 涓庤祫浜т竴鑷存€?|

## 鏁呴殰鎺掓煡

| 闂 | 鍘熷洜 | 瑙ｅ喅 |
|------|------|------|
| `doc-based-coding` 鍛戒护涓嶅彲鐢?| 铏氭嫙鐜鏈縺娲?| 杩愯 `activate` 鑴氭湰 |
| `doc-based-coding info` 鏃?pack 杈撳嚭 | 鏈畨瑁呭疄渚嬪寘锛屾垨椤圭洰涓己灏?`.codex/packs/` | 瀹夎瀹炰緥鍖呮垨杩愯 `doc-loop-bootstrap` |
| MCP server 鏃犳硶鍚姩 | `doc-based-coding-mcp` 涓嶅湪 PATH 涓?| 浣跨敤缁濆璺緞鎴栫‘淇?venv 宸叉縺娲?|
| `pip install` 鎶?"already installed" | 椤圭洰鏍圭洰褰曟湁娈嬬暀鐨?`*.egg-info` | 鍒犻櫎 `*.egg-info` 鐩綍鍚庨噸璇?|
