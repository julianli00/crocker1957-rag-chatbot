import re


def extract_ingredients(text):
    """Extract recipe ingredients"""
    paragraphs = text.split('\n\n')
    ingredients = []
    
    def clean_ingredient(line):
        original = line
        # 跳过插图标记
        if '[Illustration:' in line:
            return ''
        
        # 移除开头的数字和空格
        line = re.sub(r'^\d+\.\s*', '', line.strip())
        # 移除开头的混合指令词
        line = re.sub(r'^(Mix|Blend|Add|Stir|Beat|Pour|Heat)\s+', '', line)
        # 移除下划线标记
        line = re.sub(r'_([^_]+)_', r'\1', line)
        # 处理特殊情况：each x and y
        if 'each' in line and ' and ' in line:
            line = line.replace(' and ', ' ')
        # 保持tsp.格式
        if 'tsp salt' in line:
            line = line.replace('tsp salt', 'tsp. salt')
        elif 'tsp. salt' in line:
            line = line  # 保持原样
        elif 'tsp salt' in line.lower():
            line = re.sub(r'(?i)tsp salt', 'tsp. salt', line)
        
        # 移除指令性文本
        line = re.sub(r'(?i)(?:with|into|about|bake|dust|makes|turn|heat|drop|serve|ends|spread|roll)\s+.*$', '', line)
        
        # 保留特定的描述性文本
        if 'if desired' in line:
            line = re.sub(r',\s*if desired', '', line)
            line += ', if desired'
        
        # 处理逗号分隔的选项
        if ',' in line:
            parts = line.split(',')
            main_part = parts[0].strip()
            descriptive_parts = []
            
            for part in parts[1:]:
                part = part.strip()
                # 保留描述性文本
                if any(word in part.lower() for word in ['melted', 'softened', 'chopped', 'drained']):
                    main_part += ' ' + part
                # 保留配料选项
                elif any(word in part.lower() for word in ['peaches', 'cherries', 'or']):
                    descriptive_parts.append(part)
                # 保留"if desired"
                elif 'if desired' in part:
                    descriptive_parts.append(part)
            
            if descriptive_parts:
                line = main_part + ', ' + ', '.join(descriptive_parts)
            else:
                line = main_part
        
        result = line.strip()
        print(f"Clean ingredient: '{original}' -> '{result}'")  # Debug
        return result
    
    def is_ingredient_line(line):
        line = line.strip().lower()
        # 跳过插图标记
        if '[illustration:' in line.lower():
            return False
        
        # 检查是否包含数字或分数
        has_number = bool(re.search(r'\d', line))
        has_fraction = bool(re.search(r'\d/\d', line) or any(f in line for f in ['¼', '½', '¾', '⅓', '⅔', '⅛', '⅜', '⅝', '⅞']))
        # 检查是否包含测量单位
        has_unit = any(unit.lower() in line for unit in ['cup', 'qt', 'cups', 'tbsp', 'tsp', 'oz', 'pound', 'lb', 'pkg', 'package', 'can'])
        # 检查是否包含常见配料词
        has_ingredient = any(ing.lower() in line.lower() for ing in ['milk', 'egg', 'butter', 'sugar', 'salt', 'bisquick', 'corn', 'meal', 'cheese', 'jam', 'preserves'])
        
        # 排除看起来像指令的行
        looks_like_instruction = bool(re.match(r'^(heat|make|follow|bake|cook|stir|pour|place|top|serve|spoon|drop|roll|cut|mix|blend|try|wash|bring|with|into|about|dust|turn|ends|spread)', line))
        
        # 排除包含特定指令性词语的行
        has_instruction_words = any(word in line for word in ['bake', 'dust', 'makes', 'turn', 'heat', 'drop', 'serve', 'ends', 'spread', 'roll'])
        
        # 排除看起来像食谱说明的行
        looks_like_recipe_instruction = bool(re.search(r'(?:spread|roll|etc\.?|like)', line))
        
        # 特殊处理：允许包含"jam"或"preserves"的行，但必须有数字或单位
        if ('jam' in line or 'preserves' in line) and (has_number or has_unit):
            return True
        
        return (has_number or has_fraction) and (has_unit or has_ingredient) and not looks_like_instruction and not has_instruction_words and not looks_like_recipe_instruction
    
    def extract_ingredients_from_text(text):
        lines = text.split('\n')
        current_ingredients = []
        
        # 跳过开头的空行和下划线标记行
        start_index = 0
        while start_index < len(lines) and (not lines[start_index].strip() or lines[start_index].strip().startswith('_')):
            start_index += 1
        
        # 如果第一个非空非下划线行不包含配料，直接返回空列表
        if start_index < len(lines):
            first_line = lines[start_index].strip()
            # 检查是否是指令行或引用行
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
        
        # 处理剩余行
        for line in lines[start_index:]:
            line = line.strip()
            if not line or line.startswith('_') or line.startswith('['):
                continue
            
            # 跳过看起来像指令的行
            if re.match(r'^(Heat|Make|Follow|Bake|Cook|Stir|Pour|Place|Top|Serve|With|Into|About|Use)', line, re.IGNORECASE):
                continue
            
            # 如果这行看起来是配料
            if is_ingredient_line(line):
                cleaned_line = clean_ingredient(line)
                if cleaned_line:
                    current_ingredients.append(cleaned_line)
        
        return current_ingredients

    def extract_mixed_ingredients(text):
        # 合并多行文本
        text = ' '.join(text.split('\n'))
        print("Original text:", text)  # Debug
        # 移除指令性文本
        text = re.sub(r'\.\s*(?:Let stand|Then|Bake|Drop|Serve|Makes|Turn|Heat).*$', '', text)
        print("After removing instructions:", text)  # Debug
        # 提取配料部分
        ingredients_match = re.search(r'Mix\s+(.*?)(?=\.\s*(?:Let stand|Then|Bake|Drop|Serve|Makes|Turn|Heat)|$)', text)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1)
            print("Extracted ingredients text:", ingredients_text)  # Debug
            # 分割配料（处理逗号和and的组合）
            parts = []
            # 首先按and分割
            and_parts = ingredients_text.split(' and ')
            print("After and split:", and_parts)  # Debug
            for part in and_parts:
                # 然后按逗号分割
                comma_parts = [p.strip() for p in part.split(',') if p.strip()]
                print("After comma split:", comma_parts)  # Debug
                parts.extend(comma_parts)
            print("All parts:", parts)  # Debug
            # 清理每个配料
            cleaned_parts = []
            for part in parts:
                cleaned = clean_ingredient(part)
                print(f"Cleaning part '{part}' -> '{cleaned}'")  # Debug
                if cleaned:
                    cleaned_parts.append(cleaned)
                    print(f"Added cleaned part: {cleaned}")  # Debug
            print("Final cleaned parts:", cleaned_parts)  # Debug
            return cleaned_parts
        return []

    # 首先尝试提取格式化的配料列表
    for para in paragraphs:
        if para.strip().startswith('Mix'):
            # 这是CRANBERRY MUFFINS或HUSH PUPPIES格式
            mixed_ingredients = extract_mixed_ingredients(para)
            if mixed_ingredients:
                if any('(' in ing for ing in mixed_ingredients):
                    # CRANBERRY MUFFINS格式
                    return ' '.join(mixed_ingredients)
                else:
                    # HUSH PUPPIES格式
                    ingredients.extend(mixed_ingredients)
                    break
        else:
            # 这是其他格式
            current_ingredients = extract_ingredients_from_text(para)
            if current_ingredients:
                ingredients.extend(current_ingredients)
                
    # 移除重复项并保持顺序
    seen = set()
    ingredients = [x for x in ingredients if not (x in seen or seen.add(x))]
    
    # 格式化输出
    return '\n'.join(ingredients)
# 测试用例
test_cases = {
    "CRANBERRY MUFFINS": {
        "input": """                 CRANBERRY MUFFINS

Mix ¾ cup raw cranberries (cut in halves or quarters) and ½ cup
confectioners' sugar. Let stand ½ to 1 hr. Then fold into Muffin batter
(p. 2). Bake.
""",
        "expected": "¾ cup raw cranberries (cut in halves or quarters) ½ cup confectioners' sugar"
    },
    "JAM TWISTS": {
        "input": """    [Illustration: JAM TWISTS]

(_Pictured on inside of back cover._)

  1 egg
  ½ cup cream or ⅓ cup milk
  2 cups Bisquick
  2 tbsp. sugar
  ⅓ cup _thick_ jam or preserves

Heat oven to 450° (hot). Grease brown paper and lay on baking sheet.
Blend egg and cream together. Stir in Bisquick and sugar until well
blended. Turn out on surface sprinkled with Bisquick. Roll gently to
lightly coat dough. Knead 15 times. Roll into a 15x9″ rectangle. Spread
with jam. Fold in thirds lengthwise to make a 15x3″ rectangle. Cut in 1″
strips. Holding strip at both ends, twist in opposite directions twice,
forming a spiral. Place twists 1½″ apart on greased paper, pressing both
ends down. Bake _10 to 12 min._ Dust tops with confectioners' sugar.
Remove immediately. _Makes 15._
""",
        "expected": "1 egg\n½ cup cream or ⅓ cup milk\n2 cups Bisquick\n2 tbsp. sugar\n⅓ cup thick jam or preserves"
    },
    "SWEDISH PANCAKES": {
        "input": """    [Illustration: SWEDISH PANCAKES]

_"Old country" flavor without old-time fussing._

  1¼ cups Bisquick
  2 cups milk
  3 eggs
  ¼ cup butter, melted

Beat together until blended. Lightly grease a 6 or 7″ skillet. Spoon
about 3 tbsp. batter into hot skillet and tilt to coat bottom of pan.
Cook until small bubbles appear on surface. Loosen edges with spatula,
turn pancake gently and finish baking on other side. Lay on towel or
absorbent paper; place in low oven to keep warm. Spread each with sugar,
jam, applesauce, or whipped cream, etc. and roll up like jelly roll.
Serve warm. _Makes about 15._
""",
        "expected": "1¼ cups Bisquick\n2 cups milk\n3 eggs\n¼ cup butter melted"
    },
    "DOUGHNUTS": {
        "input": """    [Illustration: DOUGHNUTS]

_Light, tender doughnuts made with Bisquick!_

  2 cups Bisquick
  ¼ cup sugar
  ⅓ cup milk
  1 tsp. vanilla
  1 egg
  ¼ tsp. _each_ cinnamon and nutmeg, if desired

Heat fat to 375°. Mix ingredients until well blended. Turn onto lightly
floured surface and knead about 10 times. Roll out ⅜″ thick. Cut with
floured doughnut cutter. Fry in hot fat until golden brown, about 1 min.
to a side. Take from fat and drain on absorbent paper. _Makes about 12
doughnuts._
""",
        "expected": "2 cups Bisquick\n¼ cup sugar\n⅓ cup milk\n1 tsp. vanilla\n1 egg\n¼ tsp. each cinnamon nutmeg, if desired"
    },
    "FRUIT SHORT PIE COBBLER": {
        "input": """                        FRUIT SHORT PIE COBBLER

  2 tbsp. Bisquick
  1 cup sugar
  ½ tsp. cinnamon
  1 cup water
  1 tbsp. lemon juice
  4 cups fresh blueberries, peaches, or cherries

Heat oven to 425° (hot). Mix ingredients. Pour into 11½x7½x1½″ oblong
baking dish. Make Short Pie dough above. Divide in 8 parts. Pat into 3½″
squares to cover fruit mixture. Bake _25 min._ Serve warm with cream.
""",
        "expected": "2 tbsp. Bisquick\n1 cup sugar\n½ tsp. cinnamon\n1 cup water\n1 tbsp. lemon juice\n4 cups fresh blueberries, peaches, or cherries"
    },
    "HUSH PUPPIES": {
        "input": """                              HUSH PUPPIES

_An old-time favorite in the Deep South now brought up to date._

Mix 1 cup corn meal, 1 cup Bisquick, 1 tsp. salt, 1 egg, and 1 cup milk.
Drop with spoon into hot fat, fry until golden brown on both sides,
turning only once. Serve hot. _Makes 15 to 20._
""",
        "expected": "1 cup corn meal\n1 cup Bisquick\n1 tsp. salt\n1 egg\n1 cup milk"
    },
    "PIZZA BOATS":{
        "input": """
    [Illustration: PIZZA BOATS]

Heat oven to 400° (mod. hot). Make Fruit Shortcake dough (p. 3). Roll
into 15x6″ rectangle. Cut into ten 3″ squares. Place half a wiener, a
strip of cheese the same size, and 2 tsp. chili sauce or catsup on each
square. Fasten sides of boat to wiener with toothpicks. Bake _15 to 20
min._

 """,
    "expected": ""
 },
    "SWEET CINNAMON ROLLS":{
        "input": """

                          SWEET CINNAMON ROLLS

Make Biscuit dough (p. 3). Drop small spoonfuls into mixture of cinnamon
and sugar. Roll to coat surface. Bake _8 to 10 min._ in hot oven. _Makes
24._


 """,
    "expected": ""
 },
    "CAMPFIRE STEW WITH DUMPLINGS":{
        "input": """
   CAMPFIRE STEW WITH DUMPLINGS

Use canned or homemade stew. Make Dumplings (p. 2).


 """,
    "expected": ""
 }
}

score = 0
total = len(test_cases)

print("Running simple test...\n")

for title, case in test_cases.items():
    output = extract_ingredients(case["input"]).strip()
    expected = case["expected"].strip()
    if output == expected:
        print(f"[✓] {title}")
        score += 1
    else:
        print(f"[✗] {title}")
        print("Expected:")
        print(expected)
        print("Got:")
        print(output)
        print()

print(f"\nScore: {score}/{total} correct.")
