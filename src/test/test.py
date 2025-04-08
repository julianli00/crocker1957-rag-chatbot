import re
# import regex as re  # 替代标准库 re
import json
PATTERN = r'(?:\[Illustration:\s*)?["“”‘’]?([\dA-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ][A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ, \-]+)(?:["“”‘\]’]?)\n'
# 定义测量单位和常见配料
measurement_units = [
    'cup', 'cups', 'tbsp', 'tsp', 'oz', 
    'pound', 'lb', 'pkg', 'package', 'can'
]

common_ingredients = [
    'egg', 'milk', 'butter', 'sugar', 'salt', 
    'Bisquick', 'cream', 'jam', 'corn meal', 
    'preserves', 'wiener', 'cheese', 'vanilla',
    'water', 'oil', 'shortening', 'nuts'
]

def parse_serving_size(text):
    """Parse recipe serving size"""
    # First check for dozen patterns
    dozen_patterns = [
        r'makes\s+(\d+(?:\s*[½¾])?)\s*to\s*(\d+(?:\s*[½¾])?)\s*doz',
        r'_makes\s+(\d+(?:\s*[½¾])?)\s*to\s*(\d+(?:\s*[½¾])?)\s*doz',
        r'Makes\s+(\d+(?:\s*[½¾])?)\s*to\s*(\d+(?:\s*[½¾])?)\s*doz',
        r'_Makes\s+(\d+(?:\s*[½¾])?)\s*to\s*(\d+(?:\s*[½¾])?)\s*doz',
        r'makes\s+(\d+(?:\s*[½¾])?)\s*doz',
        r'_makes\s+(\d+(?:\s*[½¾])?)\s*doz',
        r'Makes\s+(\d+(?:\s*[½¾])?)\s*doz',
        r'_Makes\s+(\d+(?:\s*[½¾])?)\s*doz'
    ]
    
    for pattern in dozen_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                # Convert fractions to decimals
                num1 = match.group(1).replace('½', '.5').replace('¾', '.75')
                num2 = match.group(2).replace('½', '.5').replace('¾', '.75')
                # Convert to actual numbers (multiply by 12)
                return [int(float(num1) * 12), int(float(num2) * 12)]
            else:
                num = match.group(1).replace('½', '.5').replace('¾', '.75')
                val = int(float(num) * 12)
                return [val, val]
    
    # Regular serving size patterns
    patterns = [
        r'makes\s+(\d+)\s+to\s+(\d+)\s+servings',
        r'_makes\s+(\d+)\s+to\s+(\d+)_',
        r'_Makes\s+(\d+)\s+to\s+(\d+)_',
        r'(\d+)\s+to\s+(\d+)\s+servings',
        r'_Makes\s+(\d+)_',
        r'_makes\s+(\d+)_',
        r'Makes\s+(\d+)',
        r'makes\s+(\d+)',
        r'makes about\s+(\d+)',
        r'_Makes about\s+(\d+)_',
        r'about\s+(\d+)\s+servings',
        r'_Makes (\d+)_',
        r'_Makes (\d+) to (\d+)_',
        r'_makes (\d+)_',
        r'_makes about (\d+)_',
        r'Makes about (\d+)',
        r'makes (\d+) to (\d+)',
        r'_Makes about (\d+) to (\d+)_',
        r'_makes about (\d+) to (\d+)_',
        r'Makes (\d+) to (\d+)',
        r'(\d+)\s+servings'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return [int(match.group(1)), int(match.group(2))]
            else:
                num = int(match.group(1))
                return [num, num]
    
    # Look for numbers followed by "servings" at the end of lines
    lines = text.split('\n')
    for line in lines:
        if line.strip().endswith('servings.'):
            match = re.search(r'(\d+)', line)
            if match:
                num = int(match.group(1))
                return [num, num]
    
    return [0, 0]

def extract_notes(text):
    """Extract recipe notes"""
    notes = []
    seen_notes = set()  # For deduplication
    
    # Extract content between underscores that's on its own line
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('_') and line.endswith('_'):
            note = line[1:-1].strip()
            # Exclude serving size related notes
            if not (re.search(r'makes|servings|about', note, re.IGNORECASE) or
                   note.lower().startswith('makes') or 
                   note.lower().startswith('about') or 
                   note.lower().endswith('min.') or
                   note.lower().endswith('min') or
                   note.lower().startswith('servings')):
                if note not in seen_notes:
                    notes.append(note)
                    seen_notes.add(note)
        break
    
    return '\n'.join(notes) if notes else ""

import re

def extract_first_sentence(text):
    """提取 Mix 开头段落的第一句话"""
    match = re.search(r'(?i)^mix\s+.*?[.!?](?=\s+[A-Z]|\n|$)', text, re.DOTALL)
    return match.group(0).strip() if match else ''

def is_probable_ingredient_sentence(sentence):
    """判断句子是否可能是配料结构"""
    units = ['cup', 'cups', 'tbsp', 'tsp', 'oz', 'pound', 'lb', 'pkg', 'package', 'can']
    ingredients = ['milk', 'egg', 'butter', 'sugar', 'salt', 'bisquick', 'corn meal',
                   'cheese', 'jam', 'preserves', 'shortening', 'water', 'oil']
    sentence_lower = sentence.lower()
    return any(unit in sentence_lower for unit in units) and any(ing in sentence_lower for ing in ingredients)

def extract_ingredients(text):
    """Extract recipe ingredients"""
    paragraphs = text.split('\n\n')
    ingredients = []

    def clean_ingredient(line):
        if '[Illustration:' in line:
            return ''
        line = re.sub(r'^\d+\.\s*', '', line.strip())
        line = re.sub(r'^(Mix|Blend|Add|Stir|Beat|Pour|Heat)\s+', '', line)
        line = re.sub(r'_([^_]+)_', r'\1', line)
        if 'each' in line and ' and ' in line:
            line = line.replace(' and ', ' ')
        if 'tsp salt' in line:
            line = line.replace('tsp salt', 'tsp. salt')
        elif 'tsp. salt' in line:
            line = line
        elif 'tsp salt' in line.lower():
            line = re.sub(r'(?i)tsp salt', 'tsp. salt', line)
        line = re.sub(r'(?i)(?:\s|^)(?:with|into|about|bake|dust|makes|turn|heat|drop|serve|ends|spread|roll)\s+.*$', '', line)
        if 'if desired' in line:
            line = re.sub(r',\s*if desired', '', line)
            line += ', if desired'
        if ',' in line:
            parts = line.split(',')
            main_part = parts[0].strip()
            descriptive_parts = []
            for part in parts[1:]:
                part = part.strip()
                if any(word in part.lower() for word in ['melted', 'softened', 'chopped', 'drained']):
                    main_part += ' ' + part
                elif any(word in part.lower() for word in ['peaches', 'cherries', 'or']):
                    descriptive_parts.append(part)
                elif 'if desired' in part:
                    descriptive_parts.append(part)
            if descriptive_parts:
                line = main_part + ', ' + ', '.join(descriptive_parts)
            else:
                line = main_part
        return line.strip()

    def is_ingredient_line(line):
        line = line.strip().lower()
        if '[illustration:' in line:
            return False
        has_number = bool(re.search(r'\d', line))
        has_fraction = bool(re.search(r'\d/\d', line) or any(f in line for f in ['¼', '½', '¾', '⅓', '⅔', '⅛', '⅜', '⅝', '⅞']))
        has_unit = any(unit in line for unit in ['cup', 'qt', 'cups', 'tbsp', 'tsp', 'oz', 'pound', 'lb', 'pkg', 'package', 'can'])
        has_ingredient = any(ing in line for ing in ['milk', 'egg', 'butter', 'sugar', 'salt', 'bisquick', 'corn', 'meal', 'cheese', 'jam', 'preserves','maple','cream'])
        looks_like_instruction = bool(re.match(r'^(heat|make|follow|bake|cook|stir|pour|place|top|serve|spoon|drop|roll|cut|mix|blend|try|wash|bring|with|into|about|dust|turn|ends|spread)', line))
        has_instruction_words = any(word in line for word in ['bake', 'dust', 'makes', 'turn', 'heat', 'drop', 'serve', 'ends', 'spread', 'roll'])
        looks_like_recipe_instruction = bool(re.search(r'(?:spread|roll|etc\.?|like)', line))
        if ('jam' in line or 'preserves' in line) and (has_number or has_unit):
            return True
        return (has_number or has_fraction) and (has_unit or has_ingredient) and not looks_like_instruction and not has_instruction_words and not looks_like_recipe_instruction

    def extract_ingredients_from_text(text):
        lines = text.split('\n')
        current_ingredients = []
        start_index = 0
        while start_index < len(lines) and (not lines[start_index].strip() or lines[start_index].strip().startswith('_')):
            start_index += 1
        if start_index < len(lines):
            first_line = lines[start_index].strip()
            instruction_patterns = [
                r'^(Heat|Make|Follow|Bake|Cook|Stir|Pour|Place|Top|Serve|With|Into|About|Use)',
                r'dough \(p\. \d+\)',
                r'batter \(p\. \d+\)',
                r'\(p\. \d+\)'
            ]
            if any(re.search(pattern, first_line, re.IGNORECASE) for pattern in instruction_patterns):
                return []
            if not is_ingredient_line(first_line) and not first_line.startswith('['):
                return []
        for line in lines[start_index:]:
            line = line.strip()
            if not line or line.startswith('_') or line.startswith('['):
                continue
            if re.match(r'^(Heat|Make|Follow|Bake|Cook|Stir|Pour|Place|Top|Serve|With|Into|About|Use)', line, re.IGNORECASE):
                continue
            if is_ingredient_line(line):
                cleaned_line = clean_ingredient(line)
                if cleaned_line:
                    current_ingredients.append(cleaned_line)
        return current_ingredients

    def extract_mixed_ingredients(text):
        unit_abbreviations = {'tsp.', 'tbsp.', 'oz.', 'qt.', 'pt.', 'lb.', 'gal.', 'pkg.', 'min.', 'c.'}
        lines = text.split('\n')
        mix_started = False
        mix_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("mix"):
                mix_started = True
            if mix_started:
                mix_lines.append(stripped)
                if '.' in line:
                    period_matches = list(re.finditer(r'\.', line))
                    for m in period_matches:
                        end_pos = m.end()
                        snippet = line[:end_pos]
                        last_words = re.findall(r'\b\w+\.\b', snippet)
                        if not last_words or last_words[-1] not in unit_abbreviations:
                            break
                    else:
                        continue
                    break  # found good end

        if mix_lines:
            mix_text = ' '.join(mix_lines)
            match = re.search(r'Mix\s+(.+)', mix_text)
            if match:
                ingredients_text = match.group(1)
                parts = re.split(r'\.\s*(?=Let stand|Then|Bake|Drop|Serve|Makes|Turn|Heat|$)', ingredients_text)
                ingredients_text = parts[0]
                all_parts = []
                and_parts = ingredients_text.split(' and ')
                for part in and_parts:
                    comma_parts = [p.strip() for p in part.split(',') if p.strip()]
                    all_parts.extend(comma_parts)
                return [clean_ingredient(p) for p in all_parts if p.strip()]
        return []

    for para in paragraphs:
        if para.lower().startswith("mix"):
            mixed_ingredients = extract_mixed_ingredients(para)
            if mixed_ingredients:
                ingredients.extend(mixed_ingredients)
        else:
            current_ingredients = extract_ingredients_from_text(para)
            if current_ingredients:
                ingredients.extend(current_ingredients)

    seen = set()
    ingredients = [x for x in ingredients if not (x in seen or seen.add(x))]

    # ⬇️ fallback：尝试用 instructions 的第一句做配料
    if not ingredients:
        first_sentence = extract_first_sentence(text)
        if is_probable_ingredient_sentence(first_sentence):
            ingredients = [first_sentence.strip()]

    return '\n'.join(ingredients)



# def extract_instructions(text):
#     """Extract recipe instructions"""
#     # Remove title line and illustration
#     text = re.sub(r'^\[Illustration:[A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ][A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ\s\-,"“”‘’]*?\]\n', '', text)
#     text = re.sub(r'^[A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ][A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒ\s\-,"“”‘’]+\n', '', text)
    
#     # Split by paragraph
#     paragraphs = text.split('\n\n')
    
#     # Skip notes in underscores
#     i = 0
#     while i < len(paragraphs):
#         if paragraphs[i].strip().startswith('_') and paragraphs[i].strip().endswith('_'):
#             if paragraphs[i][1:-1].strip().endswith('min.') or paragraphs[i][1:-1].strip().endswith('min'):
#                 break
#             i += 1
#         else:
#             break


#     # Find instruction paragraphs
#     verbs = ['mix', 'stir', 'beat', 'add', 'heat', 'lay', 'make', 'pour', 'blend', 'bake', 'try', 'wash', 'bring']
#     for para in paragraphs[i:]:
#         para = para.strip()
#         if not para:
#             continue
        
#         # Skip ingredient paragraphs
#         lines = para.split('\n')
#         if all(line.strip() and (
#             re.match(r'^\s*\d', line.strip()) or
#             re.match(r'^\s*[A-ZÉÈÊËÀÂÄÇÎÏÔÖÙÛÜŸÆŒa-zéèêëàâäçîïôöùûüÿæœ]+\s+\d', line.strip())
#         ) for line in lines if line.strip()):
#             continue

#         if re.match(r'^_[^_]+_:', para):
#             break
#         # 🟡 保留时间段落，例如 "_20 to 25 min._"
#         if para.startswith('_') and para.endswith('_'):
#             content = para[1:-1].strip().lower()
#             if re.match(r'^\d+\s+to\s+\d+\s+min\.?$', content):
#                 para = content  # 替换为纯文本内容
#             else:
#                 continue  # 否则跳过其他 notes
#         # If it's an instruction paragraph
#         if any(para.lower().startswith(verb) for verb in verbs) or re.match(r'^\d+\s+to\s+\d+\s+min\.?$', para.lower()):
#             # First remove serving size information
#             para = re.sub(r'\s*_\d+(?:\s*to\s*\d+)?\s*(?:servings|min)\._\s*$', '', para)
#             # Then replace underscored text with its content
#             para = re.sub(r'_([^_]+)_', r'\1', para)
#             # Fix dash without duplicating 'except'
#             para = re.sub(r'—\s*(?:except\s+)?', '—except ', para)
#             # Join lines and normalize spaces
#             para = ' '.join(line.strip() for line in para.split('\n'))
#             # Remove extra spaces
#             para = re.sub(r'\s+', ' ', para)
#             return para.strip()
    
#     return ""

def extract_instructions(text):
    text = re.sub(r'^\[Illustration:[^\]]+\]\n', '', text)
    text = re.sub(r'^[A-Z][A-Z\s\-,"“”‘’]+\n', '', text)

    paragraphs = text.split('\n\n')
    
    # Skip intro underscores
    i = 0
    while i < len(paragraphs):
        para = paragraphs[i].strip()
        if para.startswith('_') and para.endswith('_'):
            note_content = para[1:-1].strip().lower()
            if any(kw in note_content for kw in ['makes', 'servings', 'about']) \
            or note_content.startswith('makes') \
            or note_content.startswith('about') \
            or note_content.startswith('servings') \
            or note_content.endswith('min.') \
            or note_content.endswith('min'):
                break
            i += 1
        else:
            break

    verbs = ['mix', 'stir', 'beat', 'add', 'heat', 'lay', 'make', 'pour',
             'blend', 'bake', 'try', 'wash', 'bring', 'form', 'use', 'follow',
             'drop', 'spoon']
    instruction_parts = []
    extra_parts = []

    for para in paragraphs[i:]:
        para = para.strip()
        if not para:
            continue

        # ✅ Handle _Ham Filling:_ pattern → convert to "Ham Filling: ..."
        # ✅ KEEP THIS — handles all "_Something:_ content" formats
        if re.match(r'^_.*?:_', para):
            # 合并整段为一行，防止中途断句
            para_single_line = ' '.join(line.strip() for line in para.split('\n'))
            title_match = re.match(r'^_(.*?):_', para_single_line)
            if title_match:
                title = title_match.group(1).strip()
                rest = para_single_line.split(':_', 1)[1].strip()
                full_line = f"{title}: {rest}"
                full_line = re.sub(r'\s+', ' ', full_line).strip()
                extra_parts.append(full_line)
                continue


        # ✅ Handle plain "Ham Filling: ..." or "Streusel Topping: ..."
        if re.match(r'^[A-Z][A-Za-z\s]+\s*(Filling|Topping|Syrup|Trick|Filling|Topping|Syrup|Trick):.*', para):
            para = ' '.join(line.strip() for line in para.split('\n'))
            extra_parts.append(para.strip())
            continue

        # ✅ Keep cooking time lines like "_8 to 10 min._"
        if para.startswith('_') and para.endswith('_'):
            content = para[1:-1].strip().lower()
            if re.match(r'^\d+\s+to\s+\d+\s+min\.?$', content):
                instruction_parts.append(content)
            continue

        # ❌ Skip ingredient blocks
        lines = para.split('\n')
        if all(line.strip() and (
            re.match(r'^\s*\d', line.strip()) or
            re.match(r'^\s*[A-Za-z]+\s+\d', line.strip())
        ) for line in lines if line.strip()):
            continue

        # ✅ Instruction paragraphs
        if any(para.lower().startswith(verb) for verb in verbs):
            para = re.sub(r'\s*_\d+(?:\s*to\s*\d+)?\s*(?:servings)\._\s*$', '', para)
            para = re.sub(r'\b(?:makes|serves|servings?)\s+\d+[½¾⅓⅔⅛⅜⅝⅞]?\.*$', '', para.strip(), flags=re.IGNORECASE)
            para = re.sub(r'_([^_]+)_', r'\1', para)
            para = re.sub(r'—\s*(?:except\s+)?', '—except ', para)
            para = ' '.join(line.strip() for line in para.split('\n'))
            para = re.sub(r'\s+', ' ', para)
            instruction_parts.append(para)

    # ✅ Return full instructions, with extra recipe components at the end
    return ' '.join(instruction_parts + extra_parts).strip()

def parse_recipe(text):
    """Parse a single recipe"""
# 跳过像 "\n\n   DESSERTS   \n\n" 这种大写分类标题
    # 步骤 1：预清理类似 "\n\n   DESSERTS   \n\n" 的分类标题块
    text = re.sub(r'\n\s{0,20}DESSERTS\n{2,}', '\n', text)

    # Extract title with extended capital letters (including accented characters)
    title_match = re.match(PATTERN, text)
    if not title_match:
        return None


    title = title_match.group(1).strip().strip('"').strip('”').strip('“')
    text = text[title_match.end():].strip()

    # Parse recipe other parts
    serving_size = parse_serving_size(text)
    notes = extract_notes(text)
    ingredients = extract_ingredients(text)
    instructions = extract_instructions(text)

    # Debug information
    if not ingredients:
        print(f"Debug: No ingredients found for {title}")
        print(f"Text after title: {text[:200]}...")  # Print first 200 chars for debugging
    if not instructions:
        print(f"Debug: No instructions found for {title}")

    return {
        "title": title,
        "serving_size": serving_size,
        "notes": notes,
        "ingredients": ingredients,
        "instructions": instructions
    }

# Read file
with open('data/recipes.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Split text by line
lines = text.split('\n')
# Extract text from line 46 to line 1826
text = '\n'.join(lines[46:1826])

# Use regular expression to find all matches
recipe_pattern = re.compile(PATTERN)
matches = []
pos = 0

while True:
    match = recipe_pattern.search(text, pos)
    if not match:
        break
    # Verify this is actually a recipe title by checking surrounding context
    title = match.group(1).strip().strip('"').strip('”').strip('“')
    if not any(title.startswith(skip) for skip in ['Step ', 'INDEX']):
        matches.append(match)
    pos = match.end()

# Define titles to skip
skip_titles = {
    'BREADS', 'CAKES', 'COOKIES', 'DESSERTS', 'MAIN DISHES',
    'SAUCES AND GRAVIES', 'MENUS', 'INDEX', 'Betty Crocker','FAVORITE LUNCH'
    'Step 1', 'Step 2', 'Step 3', 'Step 4', 'HOW TO MAKE GOOD BISCUITS','SUNDAY BRUNCH'
}

# Parse all recipes
all_recipes = []
recipe_dict = {}  # For quick lookup of recipes

for i, match in enumerate(matches):
    title = match.group(1).strip().strip('"').strip('”').strip('“')  # Remove all types of quotes
    
    # Skip non-recipe titles
    if title in skip_titles:
        continue
    
    # Get text between current recipe and next recipe
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    recipe_text = match.group(0) + text[start:end]
    
    # Parse recipe
    recipe = parse_recipe(recipe_text)
    if recipe:
        all_recipes.append(recipe)
        recipe_dict[recipe['title']] = recipe

print(f"Successfully parsed {len(all_recipes)} recipes")

# Save results to JSON file
with open('data/recipes.json', 'w', encoding='utf-8') as f:
    json.dump(all_recipes, f, indent=2)
print("Results saved to recipes.json")

# Test case
class Cookbook:
    def __init__(self, recipes):
        self.recipes = {}
        for recipe in recipes:
            # Store both with and without quotes for matching
            title = recipe['title']
            self.recipes[title] = recipe
            self.recipes[f'"{title}"'] = recipe  # Also store with quotes
            self.recipes[title.strip('"').strip('”').strip('“')] = recipe  # Also store without quotes

    def __getitem__(self, name):
        # Try different variations of the title
        if name in self.recipes:
            return self.recipes[name]
        quoted_name = f'"{name}"'
        if quoted_name in self.recipes:
            return self.recipes[quoted_name]
        unquoted_name = name.strip('"')
        if unquoted_name in self.recipes:
            return self.recipes[unquoted_name]
        raise KeyError(name)

book = Cookbook(all_recipes)
test_cases = [
    ('CHEESE SAUCE', 'instructions', 'Stir in 2 cups grated sharp cheese.'),
    ('HUSH PUPPIES', 'ingredients', '1 cup corn meal\n1 cup Bisquick\n1 tsp. salt\n1 egg\n1 cup milk'),
    ('CELERY CRESCENTS', 'serving_size', [16, 16]),
    ('BUTTONS AND BOWKNOTS', 'serving_size', [10, 10]),
    ('SWEDISH PANCAKES', 'ingredients', '1¼ cups Bisquick\n2 cups milk\n3 eggs\n¼ cup butter melted'),
    ('APPLE PANCAKES', 'instructions', 'Add 2 cups grated unpeeled apple, 1 tbsp. lemon juice, and 2 tbsp. sugar to Pancake batter (p. 2). Bake. Serve with syrup.'),
    ('PIZZA BOATS', 'ingredients', ''),
    ('CHOCOLATE PUDDING', 'instructions', 'Mix Bisquick, sugar, cocoa. Gradually stir in water and milk. Bring to boil over medium heat; boil 1 min. Add vanilla. Pour into sherbet glasses. Sprinkle with sugar. Cool. Top with whipped cream.'),
    ('BACON WAFFLES', 'instructions', 'Lay short strips of bacon over grids of heated waffle iron. Close and bake about 1 min. Make Waffle batter (p. 2)—except omit shortening. Spoon batter over bacon. Bake.'),
    ('STICK BISCUITS', 'notes', 'An age-old way to make hot biscuits.'),
    ('WAFFLES WITH PINEAPPLE', 'notes', 'Perfect match for smoked ham.'),
    ('PUDDING COOKIES', 'serving_size', [30, 36]),
    ('WHUFFINS', 'instructions', 'Make richer Muffins (p. 2)—except fold 1½ cups Wheaties carefully into batter.'),
    ('FRUIT SHORT PIE COBBLER', 'instructions', 'Heat oven to 425° (hot). Mix ingredients. Pour into 11½x7½x1½″ oblong baking dish. Make Short Pie dough above. Divide in 8 parts. Pat into 3½″ squares to cover fruit mixture. Bake 25 min. Serve warm with cream.'),
    ('JAM TWISTS', 'ingredients', '1 egg\n½ cup cream or ⅓ cup milk\n2 cups Bisquick\n2 tbsp. sugar\n⅓ cup thick jam or preserves'),
    ('SALMON, TUNA, OR CHICKEN SOUFFLÉ', 'instructions', 'Try 1 cup salmon or tuna, or 1½ cups cut-up cooked chicken, in place of cheese. Add 1 tbsp. lemon juice, 1 tsp. grated onion.')]

score = 0
for name, attribute, value in test_cases:
    if book[name][attribute] == value:
        score += 1
    else:
        print(f'{name} test case failed! {attribute} incorrect')
        print('Reference: ', value)
        print('Hypothesis: ', book[name][attribute])
        print('---')

print(f'Score: {score}/{len(test_cases)}')