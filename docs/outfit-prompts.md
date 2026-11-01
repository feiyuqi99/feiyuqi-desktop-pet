# 小橘 10 套新装扮生图提示词

每套两张：`<id>_idle.png` 和 `<id>_happy.png`，1024×1024，纯绿幕。

## 生成约定（实测有效）

- **idle 帧**：图生图。Image 1 = `assets/raw/casual_idle.png`（姿势取景参考），Image 2 = `assets/raw/casual_happy.png`。提示词用下方各套 idle 段落。
- **happy 帧**：图生图。Image 1 = **本套已清洗的 idle 成品图**（`tools/clean_raw.py` 处理过），Image 2 = `assets/raw/casual_happy.png`（姿势表情参考）。
- happy 帧姿势硬性要求：**画面左侧**（角色右手）举起在头侧挥手，画面右侧手臂自然下垂，与 casual_happy 同姿势。必须显式写 `Do not mirror the pose`，否则模型经常举反边。表情为张嘴笑（与 casual_happy 一致，非闭眼）。
- happy 提示词模板（`[OUTFIT]` 换成本套服装描述）：

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = current character in her [OUTFIT] (keep this exact outfit and character); Image 2 = happy pose and expression reference
Primary request: Redraw the exact same character from Image 1 in a happy greeting pose, keeping her exact [OUTFIT] unchanged: [DESC].
Character (must stay identical to Image 1): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: the raised waving arm must be on the SAME side as in Image 2 - on the viewer's LEFT side of the image (the character's right hand) raised in a gentle open-hand wave beside her head; the character's left arm on the viewer's RIGHT side stays relaxed at her side; feet together, same scale and framing as Image 2. Do not mirror the pose.
Expression: happy open-mouth smile, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the pose and expression. Keep the face, eyes, hair, sunflower hair ornament, skin tone and all clothing exactly as in Image 1. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

- 生成后 `tools/clean_raw.py --gen "<id>_<frame>=<生成文件>"` 归档到 `assets/raw/`；再 `build_sprites.py <id>`、`port_blink.py <id>`、`build_rig.py <id>`。
- 并行生成时输出文件名可能撞时间戳互相覆盖（实测发生过一次），生成后立即归档再继续下一批。

## 通用负面提示词

```text
text, watermark, signature, logo, background gradient, drop shadow, floor, cropped feet, extra limbs, extra fingers, deformed hands, different face, different hairstyle, missing sunflower hair ornament, green clothing, green background spill, blurry edges, photorealistic, 3D render, multiple characters, bag, umbrella, weapon, held object
```

## 1. jk｜JK 水手服

### idle → `jk_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a Japanese JK sailor school uniform: white short-sleeve blouse with a navy sailor collar with two white stripes, a red neckerchief, a navy pleated skirt, white ankle socks and brown loafers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `jk_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a Japanese JK sailor school uniform: white short-sleeve blouse with a navy sailor collar with two white stripes, a red neckerchief, a navy pleated skirt, white ankle socks and brown loafers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 2. pajama｜居家睡衣

### idle → `pajama_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a cozy two-piece pajama set in soft peach and cream: long-sleeve button-up pajama top with a tiny star print, matching loose pajama pants, and fluffy cream slippers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `pajama_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a cozy two-piece pajama set in soft peach and cream: long-sleeve button-up pajama top with a tiny star print, matching loose pajama pants, and fluffy cream slippers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 3. sport｜运动服

### idle → `sport_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a sporty navy and white tracksuit: zip-up navy track jacket with white sleeve stripes and a small orange chest emblem, matching navy track pants with white side stripes, and white sneakers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `sport_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a sporty navy and white tracksuit: zip-up navy track jacket with white sleeve stripes and a small orange chest emblem, matching navy track pants with white side stripes, and white sneakers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 4. sweater｜宽松毛衣

### idle → `sweater_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing an oversized oatmeal cable-knit sweater with ribbed cuffs and hem, sleeves covering half of her hands, paired with a dark brown pleated mini skirt, cream thigh-high socks and brown loafers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `sweater_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing an oversized oatmeal cable-knit sweater with ribbed cuffs and hem, sleeves covering half of her hands, paired with a dark brown pleated mini skirt, cream thigh-high socks and brown loafers.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 5. yukata｜浴衣

### idle → `yukata_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a light indigo cotton yukata with a small white floral pattern, wide sleeves, a coral-orange obi sash tied in a bow, and wooden geta sandals.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `yukata_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a light indigo cotton yukata with a small white floral pattern, wide sleeves, a coral-orange obi sash tied in a bow, and wooden geta sandals.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 6. qipao｜旗袍

### idle → `qipao_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a deep burgundy fitted cheongsam with gold floral embroidery, mandarin collar, short sleeves, a modest side slit, and black low-heeled shoes.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `qipao_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a deep burgundy fitted cheongsam with gold floral embroidery, mandarin collar, short sleeves, a modest side slit, and black low-heeled shoes.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 7. santa｜圣诞装

### idle → `santa_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a red velvet Santa-style mini dress with white fur trim at the hem and cuffs, a black belt with a gold buckle, red-and-white striped thigh-high stockings, brown boots, and a small red Santa hat with white fur trim and pom-pom tilted to one side while keeping the sunflower hair ornament visible.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing and the small Santa hat. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `santa_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a red velvet Santa-style mini dress with white fur trim at the hem and cuffs, a black belt with a gold buckle, red-and-white striped thigh-high stockings, brown boots, and a small red Santa hat with white fur trim and pom-pom tilted to one side while keeping the sunflower hair ornament visible.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing and the small Santa hat. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 8. raincoat｜雨衣

### idle → `raincoat_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a butter-yellow hooded raincoat with the hood down, white drawstrings, front pockets and buttons, matching yellow rain boots; no umbrella.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `raincoat_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a butter-yellow hooded raincoat with the hood down, white drawstrings, front pockets and buttons, matching yellow rain boots; no umbrella.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 9. trench｜风衣围巾

### idle → `trench_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a camel double-breasted trench coat with lapels, storm flaps and a belted waist, a cream knit scarf around her neck, and dark brown boots.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `trench_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a camel double-breasted trench coat with lapels, storm flaps and a belted waist, a cream knit scarf around her neck, and dark brown boots.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 10. witch｜魔女

### idle → `witch_idle.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a black witch outfit: a small pointed black witch hat with a purple band, a black short dress with purple trim and a tiny capelet, black-and-purple striped tights, and black ankle boots; no broom.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: calm neutral expression, lips gently closed, eyes open, identical to Image 1
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing and the small witch hat. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

### happy → `witch_happy.png`

```text
Use case: consistent-character outfit replacement for a game sprite
Input images: Image 1 = idle pose and framing reference; Image 2 = happy expression reference
Primary request: Redraw the exact same character wearing a black witch outfit: a small pointed black witch hat with a purple band, a black short dress with purple trim and a tiny capelet, black-and-purple striped tights, and black ankle boots; no broom.
Character (must stay identical): petite chibi anime girl, very long wavy orange hair with side bangs, large warm amber eyes, fair skin, small sunflower hair ornament with black-and-white ribbon on the viewer's right side, same face shape, same hairstyle, same body proportions.
Pose: full body standing, facing the viewer, arms relaxed at her sides, feet together, identical pose, scale and framing to the reference.
Expression: happy open-mouth smile with softly closed crescent eyes, identical to Image 2
Background: perfectly flat pure chroma-key green #00FF00. No shadow, no gradient, no floor, no background objects, no text.
Style: clean cel-shaded anime game sprite, soft shading, crisp clean edges with no green fringe.
Constraints: change ONLY the clothing and the small witch hat. Keep the face, eyes, hair, sunflower hair ornament, skin tone, pose, scale and framing unchanged. Do not add bags, umbrellas, weapons or held objects. No watermark, no text, no extra characters.
```

## 参数与排错

- 尺寸 1024×1024；图生图重绘强度 0.55–0.75。
- 工具支持多参考图（image1/image2/image3）：idle 用便服双帧参考，happy 用本套 idle + 便服 happy。
- happy 手臂举反边：在 Pose 句里显式写 `the raised waving arm must be on the SAME side as in Image 2` 和 `Do not mirror the pose`。
- 脸/发饰跑偏：降低强度到 0.45–0.55，或提高参考图权重。
- 衣服没换成功：提高到 0.8 左右，并强调 `change ONLY the clothing`。
- 出现绿边：把背景改成纯蓝 `#0000FF` 或纯品红 `#FF00FF` 后告诉我，我加对应抠色。
- 出现多余道具：把负面提示词里的 `bag, umbrella, weapon, held object` 保留，并在正向句末重复 `no held objects`。